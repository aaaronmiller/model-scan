# Accepted-Result Cost Formula (C4)

Rank by **expected cost to a verified accepted result**, not token price.

## Formula

```
accepted_result_cost = base_generation_cost
                     + latency_cost
                     + quota_scarcity_penalty
                     + health_retry_penalty
                     + validation_cost
```

| Term | Input | Value |
|------|-------|-------|
| `base_generation_cost` | `observed_cost_per_task` (USD per task) | as observed, or `UNKNOWN_PENALTY = $0.10` if `unknown` (conservative) |
| `latency_cost` | `observed_latency_ms_p50` | `(p50_ms / 1000) * LATENCY_COST_PER_SECOND` where `LATENCY_COST_PER_SECOND = $0.0005` |
| `quota_scarcity_penalty` | `quota_state.remaining_fraction` | `+ $0.02` if < 0.15, doubled if < 0.05; `+ $0.005` if unknown |
| `health_retry_penalty` | `provider_health` | `degraded: +$0.01`, `unhealthy|down: +$0.05`, `unknown: +$0.005` |
| `validation_cost` | `lane` | `routine $0.001, specialist $0.002, review $0.005, adjudication $0.010, durable $0.003` |

Constants are explicit in `resolver/cost.py` for audit.

## Missing-input behavior

Every input may be `"unknown"`. An unknown is penalized (high cost), never treated as cheap. A cheap worker needing one retry usually still beats an expensive worker that never retries; an expensive judge is justified only on the narrow acceptance decision.

## Separate frontiers (C5)

Distinct rankings when `task_class`, `modality`, `context size`, `tool requirements`, `privacy class`, `latency requirement`, `reliability requirement`, or `specialisation` change the ordering. Floors filter first; then cost ranks survivors. One global leaderboard routes badly.

## Telemetry contradicts policy (C6)

Preserve the evidence, route conservatively (prefer the policy that was verified), flag recalibration. Do not silently overwrite either side.
