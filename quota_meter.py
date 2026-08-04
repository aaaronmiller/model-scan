"""Quota metering: produce the ``provider_quota.json`` that routing snapshots consume.

``routing_snapshot.load_provider_quota`` already reads this file and publishes it
as ``provider_quota`` in the routing snapshot. Nothing produced it, so the
gateway had no knowledge of quotas. This module is that producer.

Design constraints, from the adjudicated quota monitoring specification:

- Provider response headers are the highest-precedence source (Pattern A).
- A meter must fail to ``unknown`` rather than invent remaining capacity.
- Estimates must never be presented as provider truth; provenance and
  observation time are carried on every reading.
- Local token accounting (ccusage-style) is telemetry, never authoritative
  quota when a provider source exists.
- Remaining quota is not the routing objective. This module reports state and
  prices it; it does not select models.

Nothing here performs network access. Header readings are supplied by the
caller, so the module is testable entirely from redacted fixtures.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

CONFIG_DIR = Path(os.environ.get("MODEL_SCAN_CONFIG_DIR", Path.home() / ".config" / "model-scan"))
PROVIDER_QUOTA_PATH = CONFIG_DIR / "provider_quota.json"
LEDGER_PATH = CONFIG_DIR / "quota_ledger.jsonl"

# Confidence is richer than the shared contract's quotaState allows. The
# contract is `additionalProperties: false`, so confidence and observation time
# live in the meter's own store and are not emitted into the snapshot.
CONFIDENCE_MEASURED = "measured"
CONFIDENCE_ESTIMATED = "estimated"
CONFIDENCE_UNKNOWN = "unknown"

# Contract-legal values for quotaState.source.
SOURCE_MODEL_SCAN = "model-scan"  # seeded/derived locally
SOURCE_LIVE = "live"  # observed from a provider response
SOURCE_MERGED = "merged"  # live reading refined by local accounting


@dataclass(frozen=True)
class BudgetWindow:
    """A quota window denominated in a spendable unit that refills on a period.

    ``budget`` is expressed in whatever ``unit`` names. For budget-denominated
    free tiers the unit is currency even though the user is not billed, because
    the provider meters against it.
    """

    provider: str
    unit: str
    budget: float
    period: timedelta
    label: str = ""


@dataclass(frozen=True)
class CreditBalance:
    """A pre-paid balance that depletes and does **not** refill.

    Structurally different from :class:`BudgetWindow` and deliberately a
    separate type. A window resets on a period, so remaining capacity is a
    function of spend *within the current window*. A pre-paid balance has no
    reset, so remaining capacity is a function of *all spend ever* against it.
    Modelling one as the other would report a balance as full again every five
    hours, which is exactly the kind of confident wrong number the meter exists
    to avoid.

    ``expires_at`` is optional because most pre-paid credit does not expire.
    When it is set, the balance regains use-it-or-lose-it urgency; when it is
    not, there is no deadline and no expiry discount applies.
    """

    provider: str
    unit: str
    initial: float
    expires_at: datetime | None = None
    label: str = "prepaid"


# Pre-paid balances. Recorded user answer, 2026-07-30: the objective is to use
# up the author's pre-paid credit. Amounts are the stated tiers and are
# **unverified** against any provider account page.
CREDIT_BALANCES: dict[str, CreditBalance] = {
    "google": CreditBalance("google", "usd", 20.0),
    "openai": CreditBalance("openai", "usd", 20.0),
    "anthropic": CreditBalance("anthropic", "usd", 20.0),
}


# Tier 1: budget-denominated windows. Transcribed from supplied provider
# documentation and therefore seeded at CONFIDENCE_ESTIMATED until local
# accounting or a provider reading supersedes them.
BUDGET_WINDOWS: dict[str, tuple[BudgetWindow, ...]] = {
    "opencode-go": (
        BudgetWindow("opencode-go", "usd", 12.0, timedelta(hours=5), "5h"),
        BudgetWindow("opencode-go", "usd", 30.0, timedelta(days=7), "week"),
        BudgetWindow("opencode-go", "usd", 60.0, timedelta(days=30), "month"),
    ),
}

# Published per-window request estimates, used only to seed a prior. These are
# provider estimates based on an assumed token mix and will diverge from local
# usage, which is why they never carry CONFIDENCE_MEASURED.
SEED_REQUESTS_PER_5H: dict[str, int] = {
    "deepseek-v4-flash": 31_650,
    "mimo-v2.5": 30_100,
    "qwen3.7-plus": 4_300,
    "deepseek-v4-pro": 3_450,
    "mimo-v2.5-pro": 3_250,
    "minimax-m3": 3_200,
    "kimi-k2.7-code": 1_350,
    "glm-5.2": 880,
    "grok-4.5": 120,
    "kimi-k3": 110,
}

# Pattern A: provider rate-limit header names, most specific first. Values are
# (remaining_header, limit_header, reset_header).
HEADER_SCHEMES: dict[str, tuple[str, str, str]] = {
    "groq": (
        "x-ratelimit-remaining-requests",
        "x-ratelimit-limit-requests",
        "x-ratelimit-reset-requests",
    ),
    "openrouter": (
        "x-ratelimit-remaining",
        "x-ratelimit-limit",
        "x-ratelimit-reset",
    ),
    "generic": (
        "x-ratelimit-remaining",
        "x-ratelimit-limit",
        "x-ratelimit-reset",
    ),
}


@dataclass
class QuotaReading:
    """One observation of a provider's remaining capacity.

    ``remaining_fraction`` is ``None`` when the source did not supply enough to
    compute it. That is a deliberate representable state: the meter reports
    unknown rather than inventing a number.
    """

    provider: str
    remaining_fraction: float | None
    confidence: str
    source: str
    observed_at: datetime
    unit: str = "requests"
    reset_at: datetime | None = None
    limit: float | None = None
    remaining: float | None = None
    provenance: str = ""
    window_label: str = ""
    # One provider can meter several independent pools. The author holds a
    # pre-paid balance and a free tier at the same providers, and the stated
    # plan is to accommodate other users on other plans later. Without a scope
    # these collapse into one figure and a depleted balance would appear to be
    # refilled by an unrelated free allowance.
    account_scope: str = "default"
    # What is being metered: requests, tokens, credits, messages. Distinct from
    # `unit`, which is the measure. A provider can cap requests per minute and
    # tokens per day at the same time, and those are different resources.
    resource: str = "requests"

    def is_known(self) -> bool:
        return self.remaining_fraction is not None and self.confidence != CONFIDENCE_UNKNOWN


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp_fraction(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return result if result == result else None  # reject NaN


def _parse_reset(value: Any, now: datetime) -> datetime | None:
    """Interpret a reset header as either a duration or an absolute timestamp.

    Providers disagree here. Groq emits durations like ``2m59.56s``; others emit
    epoch seconds or ISO timestamps. An unparseable value yields ``None`` rather
    than a guess.
    """

    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    # Duration forms: 1h2m3.5s, 45s, 500ms
    if raw and raw[-1].isalpha():
        total = 0.0
        number = ""
        unit = ""
        matched = False
        for ch in raw:
            if ch.isdigit() or ch == ".":
                if unit:
                    total += _duration_part(number, unit)
                    number, unit = "", ""
                number += ch
            else:
                unit += ch
        if number and unit:
            total += _duration_part(number, unit)
            matched = True
        if matched and total > 0:
            return now + timedelta(seconds=total)

    numeric = _coerce_float(raw)
    if numeric is not None:
        # Heuristic: values large enough to be an epoch are absolute.
        if numeric > 1_000_000_000:
            return datetime.fromtimestamp(numeric, tz=timezone.utc)
        return now + timedelta(seconds=numeric)

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _duration_part(number: str, unit: str) -> float:
    try:
        value = float(number)
    except ValueError:
        return 0.0
    scale = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}
    return value * scale.get(unit.strip().lower(), 0.0)


def reading_from_headers(
    provider: str,
    headers: Mapping[str, Any],
    *,
    scheme: str | None = None,
    now: datetime | None = None,
) -> QuotaReading:
    """Pattern A: derive a reading from provider response headers.

    Returns an ``unknown`` reading when the headers do not carry enough to
    compute a fraction. Header names are matched case-insensitively.
    """

    now = now or _utcnow()
    lowered = {str(k).lower(): v for k, v in headers.items()}

    # A named scheme is a preference, not an exclusive filter. Providers vary in
    # which header set they emit, and several emit the generic names even when a
    # provider-specific scheme exists. Trying only the named scheme would return
    # unknown for a response that plainly carried the numbers.
    if scheme:
        order = [scheme]
    else:
        order = [provider] if provider in HEADER_SCHEMES else []
        order.append("generic")

    key = order[-1]
    remaining = limit = None
    reset_at = None
    for name in order:
        remaining_h, limit_h, reset_h = HEADER_SCHEMES[name]
        candidate_remaining = _coerce_float(lowered.get(remaining_h))
        candidate_limit = _coerce_float(lowered.get(limit_h))
        if candidate_remaining is not None and candidate_limit is not None:
            key = name
            remaining, limit = candidate_remaining, candidate_limit
            reset_at = _parse_reset(lowered.get(reset_h), now)
            break
        if reset_at is None:
            reset_at = _parse_reset(lowered.get(reset_h), now)

    if remaining is None or limit is None or limit <= 0:
        return QuotaReading(
            provider=provider,
            remaining_fraction=None,
            confidence=CONFIDENCE_UNKNOWN,
            source=SOURCE_LIVE,
            observed_at=now,
            reset_at=reset_at,
            limit=limit,
            remaining=remaining,
            provenance=f"headers:{key}:insufficient",
        )

    return QuotaReading(
        provider=provider,
        remaining_fraction=_clamp_fraction(remaining / limit),
        confidence=CONFIDENCE_MEASURED,
        source=SOURCE_LIVE,
        observed_at=now,
        reset_at=reset_at,
        limit=limit,
        remaining=remaining,
        provenance=f"headers:{key}",
    )


def reading_from_budget(
    window: BudgetWindow,
    spent: float,
    window_started_at: datetime,
    *,
    now: datetime | None = None,
) -> QuotaReading:
    """Compute remaining capacity for a budget-denominated window.

    This is the only tier where remaining capacity is computable without any
    provider introspection, because the provider publishes the ceiling.
    """

    now = now or _utcnow()
    elapsed = now - window_started_at
    if elapsed >= window.period:
        # The window rolled over; capacity is full again.
        spent = 0.0
        window_started_at = now
        elapsed = timedelta(0)

    remaining_budget = max(0.0, window.budget - max(0.0, spent))
    fraction = _clamp_fraction(remaining_budget / window.budget) if window.budget > 0 else 0.0

    return QuotaReading(
        provider=window.provider,
        remaining_fraction=fraction,
        # Locally accounted spend is measured; it is our own observation of our
        # own usage, not a provider assertion.
        confidence=CONFIDENCE_MEASURED if spent > 0 else CONFIDENCE_ESTIMATED,
        source=SOURCE_MODEL_SCAN,
        observed_at=now,
        unit=window.unit,
        reset_at=window_started_at + window.period,
        limit=window.budget,
        remaining=remaining_budget,
        provenance=f"budget:{window.label or window.period}",
        window_label=window.label,
    )


def reading_from_credit_balance(
    balance: CreditBalance,
    total_spent: float,
    *,
    now: datetime | None = None,
) -> QuotaReading:
    """Remaining fraction of a pre-paid balance, from lifetime spend.

    ``total_spent`` is cumulative and never resets. Passing windowed spend here
    would overstate the balance, so callers must supply an all-time figure.
    """

    now = now or _utcnow()
    remaining_credit = max(0.0, balance.initial - max(0.0, total_spent))
    fraction = _clamp_fraction(remaining_credit / balance.initial) if balance.initial > 0 else 0.0

    return QuotaReading(
        provider=balance.provider,
        remaining_fraction=fraction,
        confidence=CONFIDENCE_MEASURED if total_spent > 0 else CONFIDENCE_ESTIMATED,
        source=SOURCE_MODEL_SCAN,
        observed_at=now,
        unit=balance.unit,
        # Only a balance that actually expires carries a reset time. Inventing
        # one would fabricate expiry urgency that does not exist.
        reset_at=balance.expires_at,
        limit=balance.initial,
        remaining=remaining_credit,
        provenance=f"prepaid-balance:{balance.label}",
        window_label=balance.label,
        account_scope=f"{balance.provider}:prepaid",
        resource="credits",
    )


def unknown_reading(provider: str, *, now: datetime | None = None, reason: str = "") -> QuotaReading:
    """An explicit 'we do not know' reading, which is a valid meter output."""

    return QuotaReading(
        provider=provider,
        remaining_fraction=None,
        confidence=CONFIDENCE_UNKNOWN,
        source=SOURCE_MODEL_SCAN,
        observed_at=now or _utcnow(),
        provenance=reason or "no-source",
    )


def merge_readings(readings: Iterable[QuotaReading]) -> QuotaReading | None:
    """Collapse readings for one provider using documented source precedence.

    Precedence: a measured provider reading beats local accounting, which beats
    an estimate, which beats unknown. Among equals the most recent wins. When
    several windows are known the tightest binding constraint is chosen, since
    the smallest remaining fraction is what will actually stop work.
    """

    readings = [r for r in readings if r is not None]
    if not readings:
        return None

    scopes = {r.account_scope for r in readings}
    if len(scopes) > 1:
        raise ValueError(
            "merge_readings received mixed account_scope values %s; "
            "blending separate pools would report a depleted balance as refilled"
            % sorted(scopes)
        )

    rank = {
        (SOURCE_LIVE, CONFIDENCE_MEASURED): 4,
        (SOURCE_MERGED, CONFIDENCE_MEASURED): 4,
        (SOURCE_MODEL_SCAN, CONFIDENCE_MEASURED): 3,
        (SOURCE_LIVE, CONFIDENCE_ESTIMATED): 2,
        (SOURCE_MODEL_SCAN, CONFIDENCE_ESTIMATED): 2,
    }

    def score(r: QuotaReading) -> int:
        if not r.is_known():
            return 0
        return rank.get((r.source, r.confidence), 1)

    best_score = max(score(r) for r in readings)
    if best_score == 0:
        # Nothing is known. Preserve that honestly.
        newest = max(readings, key=lambda r: r.observed_at)
        return newest

    tier = [r for r in readings if score(r) == best_score]
    # Tightest binding window first, then most recent.
    tier.sort(key=lambda r: (r.remaining_fraction if r.remaining_fraction is not None else 1.0, -r.observed_at.timestamp()))
    chosen = tier[0]

    if len({r.source for r in tier}) > 1:
        chosen = QuotaReading(**{**chosen.__dict__, "source": SOURCE_MERGED})
    return chosen


def opportunity_cost(
    reading: QuotaReading,
    *,
    nominal_cost: float,
    now: datetime | None = None,
    reserve_fraction: float = 0.0,
) -> float:
    """Price a request against a use-it-or-lose-it window.

    Capacity that expires unused has no salvage value, so as reset approaches
    with capacity still free the effective cost falls toward zero. Cost rises
    only while a reserve is being protected for work expected before reset.

    This is what lets a cheapest-adequate selector maximize utilization without
    being told to. It does not select anything itself.

    ``nominal_cost`` is the price the caller would otherwise use. An unknown
    reading returns it unchanged, so ignorance never makes something look cheap.
    """

    if not reading.is_known():
        return nominal_cost

    remaining = reading.remaining_fraction or 0.0
    if remaining <= 0.0:
        return float("inf")  # exhausted: not a candidate

    if reading.reset_at is None:
        return nominal_cost * (1.0 if remaining >= reserve_fraction else 4.0)

    now = now or _utcnow()
    seconds_left = (reading.reset_at - now).total_seconds()
    if seconds_left <= 0:
        return nominal_cost

    # Expiry pressure: how close to reset, relative to how much is left.
    # Plenty of capacity and little time means the capacity is about to be lost.
    horizon = max(seconds_left, 1.0)
    urgency = remaining / (remaining + (horizon / 3600.0))
    discounted = nominal_cost * (1.0 - urgency)

    if remaining < reserve_fraction:
        # Protecting a reserve is the only reason to make usage look expensive.
        scarcity = (reserve_fraction - remaining) / max(reserve_fraction, 1e-9)
        return nominal_cost * (1.0 + 4.0 * scarcity)

    return max(discounted, 0.0)


def depletion_penalty(
    reading: QuotaReading,
    *,
    now: datetime | None = None,
    risk_weight: float = 1.0,
    expiry_weight: float = 0.1,
    headroom: float = 0.25,
) -> float:
    """An additive quota term that works even when nominal price is zero.

    ``opportunity_cost`` scales the nominal price, so for a free candidate it
    returns zero no matter how depleted the window is. Quota state then has no
    influence on ranking at all, which is the degenerate case that lets a
    nearly-exhausted provider win on fitness and fail mid-request.

    This term is additive so it survives a zero price. It has two parts:

    - **Rejection risk**, zero until a window falls below ``headroom`` and
      rising steeply after that. This is an *availability* concern, not thrift.
      A window at two percent remaining will reject the request; declining to
      route there is not conservation. A window at half full carries no
      meaningful rejection risk and must not be penalised, otherwise a provider
      with no quota data at all would outrank a healthy measured one, and
      ignorance would look like an advantage.
    - **Expiry bonus**, a small credit for capacity that is about to reset
      unused, which keeps use-it-or-lose-it working in free-price space.

    Returns 0.0 for an unknown reading, so ignorance neither helps nor harms.
    """

    if not reading.is_known():
        return 0.0

    remaining = reading.remaining_fraction or 0.0
    if remaining <= 0.0:
        return float("inf")

    if remaining >= headroom or headroom <= 0.0:
        risk = 0.0
    else:
        shortfall = (headroom - remaining) / headroom
        risk = risk_weight * shortfall**2

    bonus = 0.0
    if reading.reset_at is not None:
        now = now or _utcnow()
        hours_left = max((reading.reset_at - now).total_seconds() / 3600.0, 0.0)
        urgency = 1.0 / (1.0 + hours_left)
        bonus = expiry_weight * urgency * remaining

    return risk - bonus


def to_quota_state(reading: QuotaReading, *, best_tier_available: str | None = None) -> dict[str, Any] | None:
    """Render a reading in the shared ``quotaState`` contract shape.

    Returns ``None`` for an unknown reading. The contract requires
    ``remaining_fraction`` and forbids extra properties, so an unknown reading
    cannot be represented and must be omitted rather than fabricated.
    """

    if not reading.is_known():
        return None

    state: dict[str, Any] = {"remaining_fraction": round(float(reading.remaining_fraction or 0.0), 6)}
    if reading.reset_at is not None:
        state["reset_at"] = reading.reset_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if reading.unit:
        state["unit"] = reading.unit
    if best_tier_available:
        state["best_tier_available"] = best_tier_available
    state["source"] = reading.source
    return state


def build_provider_quota(
    readings: Iterable[QuotaReading],
    *,
    best_tiers: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Group readings by provider and emit the contract-legal mapping."""

    best_tiers = best_tiers or {}
    grouped: dict[str, list[QuotaReading]] = {}
    for reading in readings:
        grouped.setdefault(reading.provider.lower(), []).append(reading)

    result: dict[str, dict[str, Any]] = {}
    for provider, items in grouped.items():
        merged = merge_readings(items)
        if merged is None:
            continue
        state = to_quota_state(merged, best_tier_available=best_tiers.get(provider))
        if state is not None:
            result[provider] = state
    return result


def write_provider_quota(
    payload: Mapping[str, Mapping[str, Any]],
    path: str | os.PathLike[str] | None = None,
) -> Path:
    """Write ``provider_quota.json`` atomically for the snapshot builder to read."""

    target = Path(path).expanduser() if path else PROVIDER_QUOTA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def append_observation(reading: QuotaReading, path: str | os.PathLike[str] | None = None) -> Path:
    """Append a reading to the local ledger, retaining confidence and provenance.

    The ledger keeps what the shared contract cannot carry, so an audit can
    always answer where a published figure came from and how sure it was.
    """

    target = Path(path).expanduser() if path else LEDGER_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "provider": reading.provider,
        "remaining_fraction": reading.remaining_fraction,
        "confidence": reading.confidence,
        "source": reading.source,
        "observed_at": reading.observed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "unit": reading.unit,
        "reset_at": reading.reset_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if reading.reset_at
        else None,
        "limit": reading.limit,
        "remaining": reading.remaining,
        "provenance": reading.provenance,
        "window_label": reading.window_label,
        "account_scope": reading.account_scope,
        "resource": reading.resource,
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return target


def seed_estimated_windows(now: datetime | None = None) -> list[QuotaReading]:
    """Produce day-one priors for budget-denominated tiers with no spend history.

    Without this the gateway starts with no quota knowledge at all, which is the
    current state. These are explicitly estimates and are superseded by the
    first measured observation.
    """

    now = now or _utcnow()
    readings: list[QuotaReading] = []
    for windows in BUDGET_WINDOWS.values():
        for window in windows:
            readings.append(reading_from_budget(window, spent=0.0, window_started_at=now, now=now))
    return readings
