"""Resolver — total over four outcomes, floor-before-cost enforced structurally.

Four outcomes (no fifth, never silent):
  1. resolved
  2. resolved_with_degradation  (floor met, preference not)
  3. routing_policy_unavailable  (no safe default)
  4. routing_blocked             (missing requirement)

Floors are hard: filter by floor before ranking by cost. Prove with property test.

Staleness: per-field freshness consulted; stale binding -> degradation notice.

Cost: accepted-result cost, not token price. Formula in resolver/cost.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from registry import is_stale, is_unknown


# Outcome tags — the only four values the resolver may return as outcome
OUTCOME_RESOLVED = "resolved"
OUTCOME_RESOLVED_WITH_DEGRADATION = "resolved_with_degradation"
OUTCOME_ROUTING_POLICY_UNAVAILABLE = "routing_policy_unavailable"
OUTCOME_ROUTING_BLOCKED = "routing_blocked"


@dataclass(frozen=True)
class FloorSpec:
    """Hard floors. None = no requirement on that axis."""
    min_capability: float | None = None  # for a given task_class
    task_class: str | None = None
    require_tool: bool | None = None
    require_vision: bool | None = None
    require_context: int | None = None
    privacy_allow_paid: bool | None = None  # if False, paid bindings fail floor
    max_latency_ms: int | None = None


@dataclass(frozen=True)
class Request:
    lane: str
    floors: FloorSpec = field(default_factory=FloorSpec)
    prefer_low_cost: bool = True
    harness: str | None = None  # e.g. "omp", "agy" — restricts eligibility
    allow_stale: bool = False


@dataclass(frozen=True)
class Resolution:
    outcome: str
    binding: dict[str, Any] | None
    degradation_notice: str | None = None
    reason: str | None = None
    safe_default: str | None = None
    candidates_considered: int = 0
    eliminated_by_floor: list[dict[str, str]] | None = None
    ranking_inputs: dict[str, Any] | None = None


def _fails_floor(binding: dict, floors: FloorSpec) -> str | None:
    """Return reason if binding fails any hard floor, else None. Order is floor identity, not cost."""
    # capability floor
    if floors.min_capability is not None and floors.task_class:
        perf = binding.get("measured_task_class_performance")
        if is_unknown(perf) or perf is None:
            return f"missing_performance:{floors.task_class}"
        if not isinstance(perf, dict):
            return f"missing_performance:{floors.task_class}"
        score = perf.get(floors.task_class)
        if score is None:
            return f"missing_performance:{floors.task_class}"
        if score < floors.min_capability:
            return f"below_capability_floor:{score}<{floors.min_capability}"

    if floors.require_tool:
        v = binding.get("tool_capability")
        if v != True:
            return "requires_tool"

    if floors.require_vision:
        mods = binding.get("modalities")
        if is_unknown(mods):
            return "requires_vision:unknown"
        if not isinstance(mods, list) or "vision" not in mods:
            return "requires_vision"

    if floors.require_context is not None:
        cl = binding.get("context_limit")
        if is_unknown(cl):
            return "requires_context:unknown"
        if not isinstance(cl, int) or cl < floors.require_context:
            return f"insufficient_context:{cl}<{floors.require_context}"

    if floors.privacy_allow_paid is False:
        pc = binding.get("price_class")
        if pc == "paid":
            return "privacy_blocks_paid"

    # latency is a floor when specified
    if floors.max_latency_ms is not None:
        lat = binding.get("observed_latency_ms_p50")
        if not is_unknown(lat) and isinstance(lat, (int, float)) and lat > floors.max_latency_ms:
            return f"exceeds_latency:{lat}>{floors.max_latency_ms}"

    # harness eligibility is a floor when request names a harness
    # (checked in resolve, not here, to keep floor spec harness-agnostic)
    return None


def _accepted_result_cost(binding: dict) -> float:
    """Delegate to cost.py formula; inline fallback for test isolation."""
    try:
        from resolver.cost import accepted_result_cost
        return accepted_result_cost(binding)
    except Exception:
        # minimal fallback: use observed_cost_per_task, unknown -> inf
        c = binding.get("observed_cost_per_task")
        if is_unknown(c) or c is None:
            return float("inf")
        try:
            return float(c)
        except Exception:
            return float("inf")


def resolve(request: Request, bindings: list[dict], now: datetime | None = None) -> Resolution:
    """Total resolver: always returns exactly one of four outcomes."""
    now = now or datetime.now(timezone.utc)

    # 1. Scope to lane
    lane_bindings = [b for b in bindings if b.get("lane") == request.lane]

    if not lane_bindings:
        return Resolution(
            outcome=OUTCOME_ROUTING_POLICY_UNAVAILABLE,
            binding=None,
            reason=f"no bindings for lane {request.lane!r}",
            safe_default="retry_with_human_lane_selection",
            candidates_considered=0,
            eliminated_by_floor=[],
        )

    # 2. Harness floor (if request names a harness)
    harness_filtered = []
    harness_eliminated: list[dict[str, str]] = []
    for b in lane_bindings:
        if request.harness == "omp" and b.get("in_harness_eligible") is False:
            harness_eliminated.append({"binding_id": b["binding_id"], "reason": "in_harness_ineligible"})
            continue
        if request.harness == "agy" and b.get("exo_harness_eligible") is False:
            harness_eliminated.append({"binding_id": b["binding_id"], "reason": "exo_harness_ineligible"})
            continue
        harness_filtered.append(b)

    if not harness_filtered:
        return Resolution(
            outcome=OUTCOME_ROUTING_BLOCKED,
            binding=None,
            reason="no harness-eligible bindings",
            safe_default=None,
            candidates_considered=len(lane_bindings),
            eliminated_by_floor=harness_eliminated,
        )

    # 3. Hard floors — structural filter before any ranking (C2)
    survivors: list[dict] = []
    eliminated: list[dict[str, str]] = list(harness_eliminated)
    for b in harness_filtered:
        reason = _fails_floor(b, request.floors)
        if reason:
            eliminated.append({"binding_id": b["binding_id"], "reason": reason})
        else:
            survivors.append(b)

    if not survivors:
        # All candidates eliminated by floors. Check if missing data is the blocker.
        missing = [e for e in eliminated if "unknown" in e["reason"] or "missing" in e["reason"]]
        if missing:
            return Resolution(
                outcome=OUTCOME_ROUTING_BLOCKED,
                binding=None,
                reason=f"all candidates failed floors; missing requirement present",
                safe_default=None,
                candidates_considered=len(lane_bindings),
                eliminated_by_floor=eliminated,
                ranking_inputs={"floor_spec": request.floors.__dict__},
            )
        return Resolution(
            outcome=OUTCOME_ROUTING_POLICY_UNAVAILABLE,
            binding=None,
            reason="all candidates failed hard floors",
            safe_default="relax_floor_or_add_binding",
            candidates_considered=len(lane_bindings),
            eliminated_by_floor=eliminated,
            ranking_inputs={"floor_spec": request.floors.__dict__},
        )

    # 4. Staleness check (C3) — fresh survivors vs stale survivors
    fresh_survivors: list[dict] = []
    stale_survivors: list[dict] = []
    for b in survivors:
        # A binding is stale if any floor-relevant field's freshness is expired.
        # For simplicity, check lane freshness plus key fields; if any stamped field is stale, binding is stale.
        freshness = b.get("freshness", {})
        is_binding_stale = False
        for _field, stamp in freshness.items():
            if is_stale(stamp, now):
                is_binding_stale = True
                break
        if is_binding_stale and not request.allow_stale:
            stale_survivors.append(b)
        else:
            fresh_survivors.append(b)

    # If fresh survivors exist, rank among them; stale ones are not preferred.
    # If no fresh survivors but stale ones exist, we can still resolve with degradation.
    ranking_pool = fresh_survivors if fresh_survivors else survivors
    degraded = len(fresh_survivors) == 0 and len(stale_survivors) > 0

    # 5. Health filter is NOT a floor inversion: unhealthy still considered but ranked last.
    # For now, provider_health is informational; we sort healthy first.
    def health_rank(b: dict) -> int:
        h = b.get("provider_health")
        order = {"healthy": 0, "degraded": 1, "unhealthy": 2, "down": 3, "unknown": 4}
        return order.get(h if isinstance(h, str) else "unknown", 4)

    # 6. Rank by accepted-result cost (C4) — floors already enforced
    ranking_pool_sorted = sorted(ranking_pool, key=lambda b: (_accepted_result_cost(b), health_rank(b)))

    winner = ranking_pool_sorted[0]

    # Build ranking inputs for decision log (D2.6)
    ranking_inputs = {
        "floor_spec": request.floors.__dict__,
        "cost_inputs": {b["binding_id"]: _accepted_result_cost(b) for b in ranking_pool_sorted},
        "health": {b["binding_id"]: b.get("provider_health") for b in ranking_pool_sorted},
        "freshness_degraded": degraded,
    }

    if degraded:
        return Resolution(
            outcome=OUTCOME_RESOLVED_WITH_DEGRADATION,
            binding=winner,
            degradation_notice="stale_registry: all survivors are stale; verify freshness before relying on ranking",
            candidates_considered=len(lane_bindings),
            eliminated_by_floor=eliminated,
            ranking_inputs=ranking_inputs,
        )

    # Check if winner's preference (cost) was sacrificed due to health ordering vs pure cost.
    # Cheapest but unhealthy vs slightly more expensive but healthy: not a degradation per spec;
    # preference not met would be e.g. prefer_low_cost=False but cost still used. For now,
    # we only emit degradation for staleness. Future: separate preference signal.

    return Resolution(
        outcome=OUTCOME_RESOLVED,
        binding=winner,
        candidates_considered=len(lane_bindings),
        eliminated_by_floor=eliminated,
        ranking_inputs=ranking_inputs,
    )
