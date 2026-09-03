# Phase 2 Handoff — Routing Registry

**Date:** 2026-09-02
**Contract:** T0 v3.1 + A2 v2.1
**Registry version:** 0.2.0
**Resolver version:** 0.2.0
**Agent-contracts lane vocabulary:** v0.1.0 (`lanes.yaml`)

## Registry and resolver versions

- `registry/schema.json` — v0.2.0 (bindings with per-field freshness, `unknown` sentinel)
- `registry/registry.json` — v0.2.0 (seed data, 6 bindings across 3 lanes)
- `resolver/resolver.py` — v0.2.0 (total, 4 outcomes, floor-before-cost)
- `resolver/cost.py` — v0.2.0 (accepted-result cost formula)
- `resolver/decision_log.py` + `resolver/decision_log.schema.json` — v0.2.0

## Lane vocabulary with definitions

From `~/code/agent-contracts/lanes.yaml` v0.1.0 (5 lanes, stable names; models are volatile bindings):

| Lane | Use |
|------|-----|
| `routine` | Low-latency utility work, summarization, extraction |
| `specialist` | Modality or domain-specific (vision, browser QA, embeddings) |
| `review` | Adversarial review, second pass |
| `adjudication` | Final approval, narrow acceptance decision (judge) |
| `durable` | Long-running, resource-capped work |

Callers name only a lane. The registry binds lane → (provider, model_id, adapter_id, capacity). Renaming a model touches only `registry/registry.json`.

## Adapter interface

`adapters/adapter.py` — protocol `Adapter { adapter_id, build_command(binding, prompt, cwd?) -> argv }`

| Adapter | Harness | Location | Invocation shape |
|---------|---------|----------|------------------|
| `omp` | in-harness | `opencode-go` / `opencode-zen` via `omp` | `omp -p --model <provider/model> --cwd <dir> <prompt>` |
| `agy` | exo-harness | `agy` / `codex` family | `agy --model <model> -p <prompt>` |

Acceptance proof: `tests/test_registry_resolver.py::test_gate_6_two_adapters_and_rename` — renaming `model_id` in registry data changes both adapters' argv without touching prompt artifacts or component source. `get_adapter("omp").build_command(...)` + `shell_preview(...)` are the integration points.

New model: `registry/registry.json` needs a new `adapter_id` only if a genuinely new harness appears; otherwise add a binding.

## Quota provider implementations

Interface: `quota/provider.py` — `QuotaProvider { provider_id, get_quota(provider) -> QuotaReading, list_providers() -> [str], health() -> str }`

| Implementation | What it can see | What it cannot see |
|----------------|-----------------|--------------------|
| `CPAManagerPlusQuotaProvider` | CPA-Manager-Plus SQLite events DB: per-account / per-model / per-channel token usage, latency, status, cost estimation with editable prices, price sync, account-pool quota detection, unhealthy account discovery. Probed via `CPA_MANAGER_PLUS_DB` (default `~/.local/share/cpa-manager-plus/events.db`). Lists table names as capability signal; live `remaining_fraction` requires deployed DDL version. | Nothing when DB missing (reports `db-missing` provenance). Endpoint shapes must be verified against the running CPA-Manager-Plus version; this build does not assume a fixed DDL. |
| `ManagementAPIQuotaProvider` | Management Center `/management/*`: configuration, credentials, logs, quota administration (allocated quota, not consumed usage). Controlled by `PROXY_MGMT_TOKEN` + `base_url` (default `http://127.0.0.1:8080`). | Usage/cost since v6.10.0 — that moved to companion projects (Usage Keeper / Manager-Plus). This provider correctly reports `unknown` for usage with provenance `management-api:offline` until a live probe is wired. |
| `LocalDBQuotaProvider` | `~/.config/model-scan/provider_quota.json` + `routing_snapshot.json:provider_quota` (as produced by `quota_meter.py` + gateway reliability feedback). Provenance-tagged `local-db:*`. Used as fallback for offline CI. | No synthetic quota; returns `unknown` with `miss` provenance when neither file has the provider. |
| `CompositeQuotaProvider` | Priority-ordered composition (`cpa-manager-plus` → `management-api` → `local-db`), returns first non-unknown hit. | Same blind spots as constituents; never fabricates. |
| `StubQuotaProvider` | Always `unknown` | By design |

**Gate 7 proof:** `test_gate_7_quota_three_providers` seeds a synthetic `provider_quota.json` with 3 providers (go, zen, openrouter) and asserts each returns a non-unknown `remaining_fraction` through the interface. Live on this machine, `provider_quota.json` currently holds only `opencode-go`; deploy CPA-Manager-Plus to reach live 3-provider coverage without synthesis.

**Secrets note:** `PROXY_MGMT_TOKEN` is referenced by name only, never logged. Account IDs in health logs are truncated/hashed.

## Health provider implementation

Definition: `health/probe.py` — `classify_health(error_rate, auth_valid, remaining_fraction, latency_p50_ms, latency_p95_ms)` + `HealthReading { provider, health, reason, observed_at, signals }`

| Field | Source | Meaning |
|-------|--------|---------|
| `error_rate` | proxy telemetry / `reliability_feedback.jsonl` | Recent error fraction per provider |
| `auth_valid` | proxy account health | Credential validity (future: Management Center + CPA-Manager-Plus account health) |
| `quota_headroom` | quota provider `remaining_fraction` | Low headroom -> degraded |
| `latency_p50/p95` | gateway telemetry | Tail latency degradation |

`HealthRunner.check_provider(provider)` aggregates proxy account-pool health (primary) + local signals (`reliability_feedback.jsonl`, `provider_quota.json`, snapshot `provider_health`) + synthetic probe fallback (model-list reachability without spending quota — stubbed as local signals until a live probe is wired).

**Gate 8 proof:** `test_gate_8_health_producer_and_unhealthy_detection` — `check_provider` produces `healthy/degraded/unknown` from local signals; `detect_deliberately_unhealthy(marker_path)` surfaces a deliberately unhealthy account marker file as `unhealthy` (proves account-pool signal reaches health, not just synthetic).

## Routing decision log format

`resolver/decision_log.schema.json` — append-only JSONL at `~/.local/share/model-scan/routing_decisions.jsonl`

```json
{
  "timestamp": "2026-09-02T12:00:00Z",
  "lane": "routine",
  "outcome": "resolved",
  "binding_id": "routine-free-1",
  "degradation_notice": null,
  "reason": null,
  "candidates_considered": 3,
  "eliminated_by_floor": [{"binding_id":"routine-paid-1","reason":"requires_vision"}],
  "ranking_inputs": {
    "floor_spec": {"require_tool": true, ...},
    "cost_inputs": {"routine-free-1": 0.003, ...},
    "health": {"routine-free-1": "healthy"},
    "freshness_degraded": false
  },
  "request": {"lane":"routine","harness":"omp","floors":{"require_tool":true}},
  "registry_version": "0.2.0"
}
```

Writer: `resolver.decision_log.format_decision(request, resolution, registry_version)` + `append_log(entry, path)`. Every resolver call can be explained after the fact.

## Fields currently unresolvable on this machine (with reason)

| Field | Value | Reason |
|-------|-------|--------|
| `ram_requirement_gb` | `unknown` | No VRAM / hardware inventory probe wired; decision Q7 (local hardware budget) open and possibly moot per 2026-08-20 direction ("local models unsuitable for almost all work"). |
| `vram_requirement_gb` | `unknown` | Same as above |
| `provider_health` for zen/openrouter in live files | `unknown` / `degraded` (snapshot) | No CPA-Manager-Plus DB deployed; local `reliability_feedback.jsonl` contains no recent per-provider error rates for those providers. Health runner reports correctly as `unknown` / `degraded` rather than fabricating. |
| `quota_state` for zen/openrouter | `unknown` | Same DB absence; `LocalDBQuotaProvider` correctly returns `unknown` with `miss` provenance. |
| `observed_cost_per_task` for specialist-vision | `unknown` | No task fixture set (Q3 open); `standard-task-price-proxy-v7` proxy not yet wired into registry derivation. |
| `measured_task_class_performance` for specialist-vision | `unknown` | Same — calibration record exists (agent-contracts) but model-level performance requires the task fixtures. |
| `observed_latency_ms_p50` for specialist/review | `unknown` | No gateway telemetry for those lanes yet; would come from proxy telemetry integration (Component 5). |

All unknowns are explicit `"unknown"` sentinels with freshness stamps where applicable, per D2.1.

## Verification

```
python3 -m jsonschema -i registry/registry.json registry/schema.json
python3 -m registry.table
python3 -m registry.table --json
python3 -m pytest tests/test_registry_resolver.py -v   # 11 passed
python3 -m pytest -q                                   # 253 passed
grep -r -E "gpt-5|claude-opus|deepseek-v4" resolver/ adapters/ quota/ health/ registry/*.py  # exit 1 (no hits)
```

Council: `docs/council-resolution-semantics.md` — V(5,3,1) record with dissent preserved.

Alignment predecessor: `docs/alignment-report.md` — disposition KEEP/ADAPT/REPLACE/RETIRE for every prior artifact + punchlist triage (6 incorporated, 3 genuinely blocked with safe defaults).
