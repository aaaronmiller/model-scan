"""Resolve routing slots to concrete candidates using published quota state.

The routing snapshot publishes ``slots`` (keyed by role id such as
``R1_primary``) each holding a ranked candidate list, plus optional
``provider_quota``. Nothing consumed the quota when choosing, so a slot kept its
statically ranked winner until a request actually failed.

This module closes that loop. It re-ranks a slot's candidates against current
quota state so a provider that is exhausted, or nearly so, is passed over at
resolution time rather than after a rejection.

Design constraints carried from the plan and the quota adjudication:

- Deterministic. The same inputs always produce the same ordering.
- Explainable. Every excluded candidate carries a reason.
- Availability fallback is kept separate from validation-driven escalation.
  This module produces an ordered fallback chain; it never escalates on
  quality.
- Quota input is optional. Missing or unusable quota degrades to static
  ranking rather than failing.
- Remaining quota is not the objective. Quota only prices and excludes; the
  selection rule stays cheapest-adequate.

No network access. Pure functions over snapshot data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from quota_meter import (
    CONFIDENCE_MEASURED,
    QuotaReading,
    depletion_penalty,
    opportunity_cost,
)

# Exclusion reasons. Stable strings so they can be asserted on and displayed.
EXCLUDED_QUOTA_EXHAUSTED = "quota_exhausted"
EXCLUDED_BLOCKLISTED = "blocklisted"
EXCLUDED_NO_TOOLS = "requires_tools"
EXCLUDED_NO_VISION = "requires_vision"
EXCLUDED_UNKNOWN_PRICE = "price_unknown_under_budget_policy"
EXCLUDED_UNRESOLVED_IDENTITY = "unresolved_identity"
EXCLUDED_PROVIDER_UNHEALTHY = "provider_unhealthy"
EXCLUDED_BELOW_CAPABILITY_FLOOR = "below_capability_floor"
EXCLUDED_NOT_FREE = "not_free_under_free_eval_mode"

# How a slot was resolved.
MODE_QUOTA_AWARE = "quota_aware"
MODE_STATIC = "static"
MODE_EMPTY = "empty"


@dataclass(frozen=True)
class Exclusion:
    """One candidate rejected, with the reason it was rejected."""

    api_model: str
    provider: str
    reason: str
    detail: str = ""


@dataclass
class Resolution:
    """The outcome of resolving one slot.

    ``fallback_chain`` is the ordered list of survivors, best first. The first
    entry is ``chosen``. Availability fallback walks this chain; it is not an
    escalation ladder.
    """

    slot_id: str
    label: str
    chosen: dict[str, Any] | None
    fallback_chain: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[Exclusion] = field(default_factory=list)
    mode: str = MODE_STATIC
    notes: list[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.chosen is not None

    def explain(self) -> str:
        """A one-line human-readable account of why this slot resolved as it did."""
        if not self.resolved:
            reasons = ", ".join(sorted({e.reason for e in self.excluded})) or "no candidates"
            return f"{self.slot_id}: UNRESOLVED ({reasons})"
        chosen = self.chosen or {}
        tail = f", {len(self.fallback_chain) - 1} fallback(s)" if len(self.fallback_chain) > 1 else ""
        skipped = f", {len(self.excluded)} excluded" if self.excluded else ""
        return f"{self.slot_id}: {chosen.get('api_model')} via {self.mode}{tail}{skipped}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def quota_reading_from_state(
    provider: str,
    state: Mapping[str, Any] | None,
    *,
    now: datetime | None = None,
) -> QuotaReading | None:
    """Rehydrate a published ``quotaState`` back into a reading for pricing.

    The published contract cannot carry confidence, so a published figure is
    treated as measured. That is sound because the meter omits unknown readings
    entirely rather than publishing a guess.
    """

    if not isinstance(state, Mapping):
        return None
    raw = state.get("remaining_fraction")
    try:
        fraction = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if fraction != fraction:  # NaN
        return None
    fraction = max(0.0, min(1.0, fraction))

    reset_at = None
    reset_raw = state.get("reset_at")
    if isinstance(reset_raw, str) and reset_raw:
        try:
            parsed = datetime.fromisoformat(reset_raw.replace("Z", "+00:00"))
            reset_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            reset_at = None

    return QuotaReading(
        provider=provider,
        remaining_fraction=fraction,
        confidence=CONFIDENCE_MEASURED,
        source=str(state.get("source") or "model-scan"),
        observed_at=now or _utcnow(),
        unit=str(state.get("unit") or "requests"),
        reset_at=reset_at,
        provenance="published-snapshot",
    )


def _identity_ok(candidate: Mapping[str, Any]) -> bool:
    return bool(str(candidate.get("api_model") or "").strip()) and bool(
        str(candidate.get("provider") or "").strip()
    )


def score_candidate(
    candidate: Mapping[str, Any],
    reading: QuotaReading | None,
    *,
    now: datetime,
    reserve_fraction: float,
    rank: int | None = None,
) -> tuple[float, float, float]:
    """Return ``(effective_cost, rank_key, fitness_key)`` for deterministic ordering.

    ``rank_key`` implements cheapest-adequate. Every candidate reaching this
    point already meets the slot's capability floor, so among them the *weakest
    qualifying* one is preferred, meaning the largest ladder rank number. Taking
    the strongest instead would spend scarce high-capability quota on work that
    did not need it, which is the "strong models used for trivial tasks" failure
    the problem statement names.

    When rank is unknown the key is neutral and fitness decides, so behaviour is
    unchanged for candidates carrying no ladder evidence.

    Effective cost is the candidate's blended price repriced against its
    provider's quota window. A free candidate has nominal cost zero, so among
    free candidates the rank key decides, and fitness only breaks a remaining
    tie.
    """

    price = candidate.get("price_blended")
    nominal = 0.0
    if isinstance(price, (int, float)) and price == price:
        nominal = max(0.0, float(price))

    if reading is None:
        effective = nominal
    else:
        # Two terms, because one alone is not enough. The multiplicative term
        # prices a real budget; it collapses to zero for a free candidate. The
        # additive term survives a zero price, so a nearly-exhausted free
        # provider is still ranked below a healthy one instead of winning on
        # fitness and failing mid-request.
        priced = opportunity_cost(
            reading, nominal_cost=nominal, now=now, reserve_fraction=reserve_fraction
        )
        if priced == float("inf"):
            return float("inf"), 0.0, 0.0
        effective = priced + depletion_penalty(reading, now=now)

    fitness = candidate.get("fitness")
    fitness_value = float(fitness) if isinstance(fitness, (int, float)) else 0.0

    # Sorted ascending, so negate to express "prefer larger rank number".
    rank_key = -float(rank) if isinstance(rank, int) else 0.0
    return effective, rank_key, fitness_value


def resolve_slot(
    slot_id: str,
    selection: Mapping[str, Any],
    provider_quota: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    blocklist: Iterable[str] = (),
    provider_health: Mapping[str, Any] | None = None,
    require_tools: bool = False,
    require_vision: bool = False,
    require_known_price: bool = False,
    reserve_fraction: float = 0.0,
    min_rank: int | None = None,
    candidate_ranks: Mapping[str, int] | None = None,
    eval_mode: str | None = None,
    now: datetime | None = None,
) -> Resolution:
    """Resolve one slot to a candidate, with exclusions recorded.

    ``min_rank`` is the slot's capability floor on the classifier ladder, where
    a lower number is more capable. A candidate is excluded when its known rank
    is numerically greater than the floor. A candidate whose rank is *unknown*
    is not excluded: refusing to route on missing evidence would strand slots,
    and the meter's principle is to fail to unknown rather than to fabricate.
    """

    now = now or _utcnow()
    provider_quota = provider_quota or {}
    blocked = {str(b).strip().lower() for b in blocklist if str(b).strip()}
    health = provider_health or {}

    label = str(selection.get("label") or slot_id)
    candidates: Sequence[Mapping[str, Any]] = selection.get("candidates") or []
    # An explicit requirement overrides what the snapshot published, so policy
    # can tighten a slot without republishing the snapshot.
    effective_eval_mode = str(eval_mode or selection.get("eval_mode") or "").strip().lower()

    resolution = Resolution(slot_id=slot_id, label=label, chosen=None)

    if not candidates:
        resolution.mode = MODE_EMPTY
        resolution.notes.append("slot published no candidates")
        return resolution

    quota_used = False
    scored: list[tuple[float, float, str, dict[str, Any]]] = []

    for candidate in candidates:
        api_model = str(candidate.get("api_model") or "")
        provider = str(candidate.get("provider") or "").lower()

        if not _identity_ok(candidate):
            resolution.excluded.append(
                Exclusion(api_model or "<missing>", provider or "<missing>", EXCLUDED_UNRESOLVED_IDENTITY)
            )
            continue

        if api_model.lower() in blocked or provider in blocked:
            resolution.excluded.append(Exclusion(api_model, provider, EXCLUDED_BLOCKLISTED))
            continue

        if require_tools and not candidate.get("has_tools"):
            resolution.excluded.append(Exclusion(api_model, provider, EXCLUDED_NO_TOOLS))
            continue

        if require_vision and not candidate.get("has_vision"):
            resolution.excluded.append(Exclusion(api_model, provider, EXCLUDED_NO_VISION))
            continue

        price = candidate.get("price_blended")
        if require_known_price and not isinstance(price, (int, float)):
            resolution.excluded.append(Exclusion(api_model, provider, EXCLUDED_UNKNOWN_PRICE))
            continue

        # Recovered directive, 2026-05-20: auxiliary selections use the free
        # option while primary, delegated, and primary fallbacks use a cost
        # basis. A free-mode slot therefore refuses a priced candidate outright
        # rather than merely ranking it lower. An unknown price is treated as
        # not-free here, because spending by accident is worse than declining.
        if effective_eval_mode == "free":
            if not isinstance(price, (int, float)) or float(price) > 0:
                resolution.excluded.append(
                    Exclusion(api_model, provider, EXCLUDED_NOT_FREE, detail=f"price={price}")
                )
                continue

        if health.get(provider) is False:
            resolution.excluded.append(Exclusion(api_model, provider, EXCLUDED_PROVIDER_UNHEALTHY))
            continue

        if min_rank is not None and candidate_ranks:
            rank = candidate_ranks.get(api_model)
            if isinstance(rank, int) and rank > min_rank:
                resolution.excluded.append(
                    Exclusion(
                        api_model,
                        provider,
                        EXCLUDED_BELOW_CAPABILITY_FLOOR,
                        detail=f"rank={rank} floor={min_rank}",
                    )
                )
                continue

        reading = quota_reading_from_state(provider, provider_quota.get(provider), now=now)
        if reading is not None:
            quota_used = True

        effective, rank_key, fitness = score_candidate(
            candidate,
            reading,
            now=now,
            reserve_fraction=reserve_fraction,
            rank=(candidate_ranks or {}).get(api_model),
        )

        if effective == float("inf"):
            resolution.excluded.append(
                Exclusion(
                    api_model,
                    provider,
                    EXCLUDED_QUOTA_EXHAUSTED,
                    detail=f"remaining_fraction={reading.remaining_fraction if reading else 'n/a'}",
                )
            )
            continue

        scored.append((effective, rank_key, -fitness, api_model, dict(candidate)))

    if not scored:
        resolution.mode = MODE_QUOTA_AWARE if quota_used else MODE_STATIC
        resolution.notes.append("all candidates excluded")
        return resolution

    # Deterministic: cost asc, then cheapest-adequate rank, then fitness desc,
    # then api_model as a stable final tie-break.
    scored.sort(key=lambda row: (row[0], row[1], row[2], row[3]))

    resolution.fallback_chain = [row[4] for row in scored]
    resolution.chosen = resolution.fallback_chain[0]
    resolution.mode = MODE_QUOTA_AWARE if quota_used else MODE_STATIC
    if not quota_used:
        resolution.notes.append("no quota state for these providers; static ranking used")
    return resolution


def resolve_snapshot(
    snapshot: Mapping[str, Any],
    *,
    requirements: Mapping[str, Mapping[str, Any]] | None = None,
    reserve_fraction: float = 0.0,
    candidate_ranks: Mapping[str, int] | None = None,
    now: datetime | None = None,
) -> dict[str, Resolution]:
    """Resolve every slot in a routing snapshot.

    ``requirements`` optionally carries per-slot constraints, for example
    ``{"R7_vision": {"require_vision": True}}`` or ``{"S15_fable_max":
    {"min_rank": 1}}``. ``candidate_ranks`` maps ``api_model`` to a classifier
    ladder rank and is required for any ``min_rank`` to take effect.
    """

    now = now or _utcnow()
    requirements = requirements or {}
    slots = snapshot.get("slots") or {}
    provider_quota = snapshot.get("provider_quota") or {}
    blocklist = snapshot.get("blocklist") or []
    health = _health_map(snapshot.get("provider_health"))

    results: dict[str, Resolution] = {}
    for slot_id, selection in slots.items():
        req = requirements.get(slot_id, {})
        results[slot_id] = resolve_slot(
            slot_id,
            selection or {},
            provider_quota,
            blocklist=blocklist,
            provider_health=health,
            require_tools=bool(req.get("require_tools")),
            require_vision=bool(req.get("require_vision")),
            require_known_price=bool(req.get("require_known_price")),
            reserve_fraction=float(req.get("reserve_fraction", reserve_fraction)),
            min_rank=req.get("min_rank"),
            candidate_ranks=candidate_ranks,
            eval_mode=req.get("eval_mode"),
            now=now,
        )
    return results


def _health_map(raw: Any) -> dict[str, Any]:
    """Normalize provider health into ``{provider: bool}``.

    Accepts either a plain boolean map or objects carrying an ``accessible``
    flag, since the snapshot has carried both shapes.
    """

    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, Any] = {}
    for provider, value in raw.items():
        key = str(provider).lower()
        if isinstance(value, bool):
            out[key] = value
        elif isinstance(value, Mapping):
            for flag in ("accessible", "healthy", "ok"):
                if flag in value:
                    out[key] = bool(value[flag])
                    break
    return out


def redirect_map(
    resolutions: Mapping[str, Resolution],
    slot_aliases: Mapping[str, str],
) -> dict[str, str]:
    """Build the vendor-model to actual-model substitution table.

    ``slot_aliases`` maps a harness-visible model identity to a slot id, for
    example ``{"claude-3-5-haiku-20241022": "R9_session_search"}``. The result
    is what an interception layer needs: what the harness asked for, mapped to
    what should actually be called.

    Slots that did not resolve are omitted, so the caller falls through to its
    existing static configuration rather than routing into nothing.
    """

    table: dict[str, str] = {}
    for requested, slot_id in slot_aliases.items():
        resolution = resolutions.get(slot_id)
        if resolution is None or not resolution.resolved:
            continue
        api_model = str((resolution.chosen or {}).get("api_model") or "")
        if api_model:
            table[requested] = api_model
    return table
