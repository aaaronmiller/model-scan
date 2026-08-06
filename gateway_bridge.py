"""Bridge between a running gateway and the quota pipeline.

Two directions:

**Inbound.** A gateway reports what a request actually cost and what the
provider said about remaining capacity. Those become a spend event and a quota
reading. This is what turns seeded estimates into measured facts.

**Outbound.** The resolved slot grid becomes configuration a gateway can load:
a model-alias table for a LiteLLM-style proxy, or a plain redirect map for an
interception layer.

Substrate-neutral by design. The core functions take plain mappings, and the
LiteLLM-shaped adapters are thin wrappers over them, so choosing a different
substrate later does not require rewriting the pipeline. That matches the
recorded requirement to keep one shared resolver rather than embedding routing
logic in one harness path.

No network access. Nothing here starts, configures, or authenticates a gateway.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import quota_meter as qm
import slot_grid as sg
import slot_resolver as sr
import spend_ledger as sl

# Response header names a provider may use to report cost directly. Checked
# before falling back to a caller-supplied figure.
COST_HEADERS = ("x-cost-usd", "x-request-cost", "openrouter-cost")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# The leading segment of a model id is a **protocol adapter**, not necessarily
# the provider. `openai/qwen/qwen3-next` served from integrate.api.nvidia.com is
# an NVIDIA model spoken to over the OpenAI wire format. Treating the prefix as
# the provider files its spend and quota under "openai", which is wrong.
#
# Recorded user correction, 2026-06-02, made twice: "for openrouter the whole
# thing, 'google/gemma...' is the model name; even though it says google at the
# start, the provider is NOT google, its openrouter, who then sends it to
# google."
ADAPTER_PREFIXES = frozenset({"openai", "anthropic", "azure", "custom", "hosted_vllm"})

# api_base host to provider identity. The host is authoritative because it is
# who the request actually goes to.
HOST_PROVIDERS: dict[str, str] = {
    "integrate.api.nvidia.com": "nvidia",
    "api.groq.com": "groq",
    "openrouter.ai": "openrouter",
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
    "api.deepseek.com": "deepseek",
    "opencode.ai": "opencode",
}


def _host_of(api_base: str | None) -> str:
    text = str(api_base or "").strip().lower()
    if not text:
        return ""
    text = text.split("://", 1)[-1]
    return text.split("/", 1)[0].split(":", 1)[0]


def resolve_provider(model: str, api_base: str | None = None) -> str:
    """Determine the real provider for a model id.

    Precedence, strongest first:

    1. ``api_base`` host, because that is who actually receives the request.
    2. A leading segment that is a known routing provider rather than a protocol
       adapter, such as ``openrouter/...``.
    3. The leading segment as a last resort.

    A bare id with no separator and no api_base returns itself, which keeps
    behaviour sane for locally named models.
    """

    host = _host_of(api_base)
    if host:
        if host in HOST_PROVIDERS:
            return HOST_PROVIDERS[host]
        # Unknown host: use its registrable-looking label rather than guessing
        # from the model id, since the host is still the more truthful signal.
        parts = [p for p in host.split(".") if p not in ("api", "www")]
        if parts:
            return parts[0]

    text = str(model or "").strip().lower()
    if "/" not in text:
        return text

    head = text.split("/", 1)[0]
    if head in ADAPTER_PREFIXES:
        # The prefix is a wire format, not a provider, and we have no api_base
        # to resolve against. Reporting it as the provider would be a confident
        # wrong answer, so report unknown instead.
        return ""
    return head


def _provider_of(model: str) -> str:
    """Backwards-compatible shim. Prefer :func:`resolve_provider`."""

    return resolve_provider(model)


def _coerce_cost(value: Any) -> float | None:
    if value is None:
        return None
    try:
        cost = float(value)
    except (TypeError, ValueError):
        return None
    if cost != cost or cost < 0:
        return None
    return cost


@dataclass(frozen=True)
class RequestOutcome:
    """What a gateway observed for one completed request."""

    model: str
    started_at: datetime
    cost: float | None = None
    unit: str = "usd"
    headers: Mapping[str, Any] | None = None
    slot_id: str = ""
    request_id: str = ""
    provider: str = ""
    api_base: str = ""

    def resolved_provider(self) -> str:
        """Real provider, resolved from api_base first and the id only after.

        Returns an empty string when the provider genuinely cannot be
        determined, so a caller can decline to record rather than file the
        event under a protocol adapter name.
        """

        if self.provider:
            return self.provider.lower()
        return resolve_provider(self.model, self.api_base).lower()


def spend_event_from_outcome(outcome: RequestOutcome) -> sl.SpendEvent | None:
    """Derive a spend event, preferring a provider-reported cost.

    Returns ``None`` when no cost is available. Recording nothing is correct
    here: inferring spend from token counts is explicitly excluded, because that
    source documents severe undercount and would produce a confident wrong
    number.
    """

    cost = None
    headers = {str(k).lower(): v for k, v in (outcome.headers or {}).items()}
    for name in COST_HEADERS:
        cost = _coerce_cost(headers.get(name))
        if cost is not None:
            break
    if cost is None:
        cost = _coerce_cost(outcome.cost)
    if cost is None:
        return None

    provider = outcome.resolved_provider()
    if not provider:
        # Attributing spend to a protocol adapter would corrupt every per
        # provider total. Recording nothing is the honest outcome.
        return None

    return sl.SpendEvent(
        provider=provider,
        amount=cost,
        unit=outcome.unit,
        at=outcome.started_at,
        model=str(outcome.model or ""),
        slot_id=outcome.slot_id,
        request_id=outcome.request_id,
    )


def quota_reading_from_outcome(
    outcome: RequestOutcome, *, now: datetime | None = None
) -> qm.QuotaReading | None:
    """Derive a live quota reading from the response headers, if present."""

    if not outcome.headers:
        return None
    provider = outcome.resolved_provider()
    if not provider:
        return None
    reading = qm.reading_from_headers(provider, outcome.headers, now=now or _utcnow())
    return reading if reading.is_known() else None


def observe(
    outcome: RequestOutcome,
    *,
    spend_path: str | os.PathLike[str] | None = None,
    ledger_path: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Record one request outcome into both ledgers.

    Never raises on a malformed outcome. A gateway callback must not be able to
    break request handling, so a bad record is dropped and reported rather than
    propagated.
    """

    result: dict[str, Any] = {"spend_recorded": False, "quota_recorded": False}
    try:
        event = spend_event_from_outcome(outcome)
        if event is not None:
            _, recorded = sl.record_spend_once(event, spend_path)
            result["spend_recorded"] = recorded
            if recorded:
                result["amount"] = event.amount
            else:
                result["spend_duplicate"] = True
    except (OSError, ValueError) as exc:
        result["spend_error"] = f"{type(exc).__name__}: {exc}"

    try:
        reading = quota_reading_from_outcome(outcome, now=now)
        if reading is not None:
            qm.append_observation(reading, ledger_path)
            result["quota_recorded"] = True
            result["remaining_fraction"] = reading.remaining_fraction
    except OSError as exc:
        result["quota_error"] = f"{type(exc).__name__}: {exc}"

    return result


def litellm_success_callback(
    kwargs: Mapping[str, Any],
    response_obj: Any = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    *,
    spend_path: str | os.PathLike[str] | None = None,
    ledger_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Adapter shaped like a LiteLLM success callback.

    Reads the response cost and any rate-limit headers LiteLLM surfaces, then
    delegates to :func:`observe`. Written defensively because callback payload
    shapes vary between versions.
    """

    model = str(kwargs.get("model") or "")
    litellm_params = kwargs.get("litellm_params") or {}
    metadata = litellm_params.get("metadata") if isinstance(litellm_params, Mapping) else {}
    metadata = metadata if isinstance(metadata, Mapping) else {}

    standard_logging_object = kwargs.get("standard_logging_object")
    cost = kwargs.get("response_cost")
    if cost is None and isinstance(standard_logging_object, Mapping):
        cost = standard_logging_object.get("response_cost")

    headers: dict[str, Any] = {}
    for source in (
        getattr(response_obj, "_hidden_params", None),
        kwargs.get("additional_headers"),
    ):
        if isinstance(source, Mapping):
            raw = source.get("additional_headers") or source
            if isinstance(raw, Mapping):
                headers.update({str(k): v for k, v in raw.items()})

    api_base = ""
    if isinstance(litellm_params, Mapping):
        api_base = str(litellm_params.get("api_base") or "")

    request_id = str(
        metadata.get("request_id")
        or kwargs.get("litellm_call_id")
        or (standard_logging_object.get("id") if isinstance(standard_logging_object, Mapping) else "")
        or ""
    )
    missing_spend_id = cost is not None and not request_id

    outcome = RequestOutcome(
        model=model,
        started_at=start_time or _utcnow(),
        # Cost without a stable identity is not safe under at-least-once
        # callback delivery. Preserve quota headers but decline the spend row.
        cost=None if missing_spend_id else cost,
        headers=headers or None,
        api_base=api_base,
        slot_id=str(metadata.get("slot_id") or ""),
        request_id=request_id,
    )
    result = observe(outcome, spend_path=spend_path, ledger_path=ledger_path)
    if missing_spend_id:
        result["spend_error"] = "missing stable request_id; spend not recorded"
    return result


def refresh_quota(
    *,
    windows: Iterable[qm.BudgetWindow] | None = None,
    spend_path: str | os.PathLike[str] | None = None,
    ledger_path: str | os.PathLike[str] | None = None,
    quota_path: str | os.PathLike[str] | None = None,
    epoch: datetime | None = None,
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Recompute and publish ``provider_quota.json`` from recorded observations.

    Budget windows come from recorded spend. Live header readings come from the
    meter's own ledger, most recent per provider. The meter's precedence rules
    then decide which wins.
    """

    now = now or _utcnow()
    selected = list(windows) if windows is not None else [
        window for group in qm.BUDGET_WINDOWS.values() for window in group
    ]

    readings: list[qm.QuotaReading] = list(
        sl.measured_readings(selected, now=now, epoch=epoch, path=spend_path)
    )
    readings.extend(_recent_live_readings(ledger_path, now=now))

    payload = qm.build_provider_quota(readings)
    qm.write_provider_quota(payload, quota_path)
    return payload


def _recent_live_readings(
    ledger_path: str | os.PathLike[str] | None, *, now: datetime
) -> list[qm.QuotaReading]:
    """Most recent live header reading per provider from the meter ledger."""

    target = Path(ledger_path).expanduser() if ledger_path else qm.LEDGER_PATH
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()[-5_000:]
    except OSError:
        return []

    latest: dict[str, qm.QuotaReading] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping) or row.get("source") != qm.SOURCE_LIVE:
            continue
        fraction = row.get("remaining_fraction")
        provider = row.get("provider")
        if fraction is None or not isinstance(provider, str):
            continue
        try:
            value = float(fraction)
        except (TypeError, ValueError):
            continue
        observed = row.get("observed_at")
        try:
            at = datetime.fromisoformat(str(observed).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        existing = latest.get(provider.lower())
        if existing is None or at > existing.observed_at:
            latest[provider.lower()] = qm.QuotaReading(
                provider=provider.lower(),
                remaining_fraction=max(0.0, min(1.0, value)),
                confidence=qm.CONFIDENCE_MEASURED,
                source=qm.SOURCE_LIVE,
                observed_at=at,
                unit=str(row.get("unit") or "requests"),
                provenance="ledger-replay",
            )
    return list(latest.values())


def build_redirect_table(
    snapshot: Mapping[str, Any],
    pairs: Sequence[tuple[str, str | None]],
    *,
    candidate_ranks: Mapping[str, int] | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, str], dict[str, sr.Resolution]]:
    """Resolve the grid and return ``(redirect_table, resolutions)``."""

    resolutions = sr.resolve_snapshot(
        snapshot,
        requirements=sg.requirements_for_slots(),
        candidate_ranks=candidate_ranks,
        now=now,
    )
    aliases = sg.alias_table(pairs)
    return sr.redirect_map(resolutions, aliases), resolutions


def litellm_model_aliases(redirect_table: Mapping[str, str]) -> list[dict[str, Any]]:
    """Render a redirect table as LiteLLM ``model_list`` entries.

    Each entry maps a vendor-visible model name to the resolved target, which is
    exactly the substitution the existing configuration already performs by hand
    for the haiku slot.

    Credentials are never emitted. ``api_key`` is left to the gateway's own
    provider registry.
    """

    entries: list[dict[str, Any]] = []
    for requested, target in sorted(redirect_table.items()):
        entries.append(
            {
                "model_name": requested,
                "litellm_params": {"model": target},
                "model_info": {"managed_by": "model-scan", "redirect_of": requested},
            }
        )
    return entries


def write_litellm_overrides(
    redirect_table: Mapping[str, str],
    path: str | os.PathLike[str],
) -> Path:
    """Write the alias entries as JSON for a gateway to merge.

    JSON rather than YAML so no serializer dependency is added. A gateway or an
    operator merges this into its own configuration; nothing here edits a live
    gateway config, which would be a configuration change requiring approval.
    """

    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_by": "model-scan.gateway_bridge",
        "model_list": litellm_model_aliases(redirect_table),
    }
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def utilization_report(
    *,
    windows: Iterable[qm.BudgetWindow] | None = None,
    spend_path: str | os.PathLike[str] | None = None,
    epoch: datetime | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Per-window utilization, sorted by how much capacity is on track to be wasted."""

    now = now or _utcnow()
    selected = list(windows) if windows is not None else [
        window for group in qm.BUDGET_WINDOWS.values() for window in group
    ]
    rows = [
        sl.utilization(window, now=now, epoch=epoch, path=spend_path) for window in selected
    ]
    rows.sort(key=lambda row: row["projected_waste"], reverse=True)
    return rows
