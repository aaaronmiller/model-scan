"""Accepted-result cost: expected cost to a verified accepted result.

Rank by expected cost to verified accepted result, not token price.

Inputs (all may be unknown):
  generation cost (observed_cost_per_task)
  latency (observed_latency_ms_p50) — time is cost when it blocks
  retry probability (derived from provider_health / quota headroom)
  validation cost (fixed per lane)
  quota consumption (opportunity cost when allowance is scarce)

When inputs are missing: route conservatively (unknown -> high cost), never
fabricate a low figure. A cheap worker needing one retry usually still wins
over a dear worker that never retries; an expensive judge is justified only
on the acceptance decision.

This is the formula the resolver ranks by after floors are enforced.
"""
from __future__ import annotations

from registry import is_unknown

# Calibration: keep constants explicit and testable.
RETRY_COST_MULTIPLIER = 1.0  # one retry doubles effective cost at 50% success
LATENCY_COST_PER_SECOND = 0.0005  # USD-equivalent per second of p50 latency
QUOTA_SCARCITY_PENALTY = 0.02  # added when remaining_fraction < 0.15
UNHEALTHY_PENALTY = 0.05
DEGRADED_PENALTY = 0.01
UNKNOWN_PENALTY = 0.10  # unknown cost treated as expensive, not cheap


# Validation cost per lane (opaque to model, but real in the pipeline)
LANE_VALIDATION_COST = {
    "routine": 0.001,
    "specialist": 0.002,
    "review": 0.005,
    "adjudication": 0.010,
    "durable": 0.003,
}


def accepted_result_cost(binding: dict) -> float:
    """Compute expected cost to accepted result. Unknown inputs penalize, not hide."""
    # Base generation cost
    base = binding.get("observed_cost_per_task")
    if is_unknown(base) or base is None:
        cost = UNKNOWN_PENALTY
    else:
        try:
            cost = float(base)
        except Exception:
            cost = UNKNOWN_PENALTY

    # Latency cost
    lat = binding.get("observed_latency_ms_p50")
    if not is_unknown(lat) and isinstance(lat, (int, float)):
        cost += (lat / 1000.0) * LATENCY_COST_PER_SECOND

    # Quota scarcity
    quota = binding.get("quota_state")
    if isinstance(quota, dict):
        rf = quota.get("remaining_fraction")
        if isinstance(rf, (int, float)) and rf < 0.15:
            cost += QUOTA_SCARCITY_PENALTY
        if isinstance(rf, (int, float)) and rf < 0.05:
            cost += QUOTA_SCARCITY_PENALTY  # double penalty for near-exhaustion
    elif is_unknown(quota):
        cost += 0.005  # small unknown-quota penalty

    # Provider health penalty (retry expectation)
    health = binding.get("provider_health")
    if health == "degraded":
        cost += DEGRADED_PENALTY
    elif health in ("unhealthy", "down"):
        cost += UNHEALTHY_PENALTY
    elif is_unknown(health):
        cost += 0.005

    # Validation cost per lane
    lane = binding.get("lane")
    cost += LANE_VALIDATION_COST.get(lane, 0.002)

    # Capacity is not a cost but could affect retry probability; omitted for now
    # to keep formula auditable. Future: factor capacity_slots into retry estimate.

    return cost


def cost_inputs_for_log(binding: dict) -> dict:
    """Explain cost breakdown for D2.6 routing decision log."""
    return {
        "observed_cost_per_task": binding.get("observed_cost_per_task"),
        "observed_latency_ms_p50": binding.get("observed_latency_ms_p50"),
        "quota_state": binding.get("quota_state"),
        "provider_health": binding.get("provider_health"),
        "lane": binding.get("lane"),
        "computed": accepted_result_cost(binding),
    }
