# Model-Scan — Routing Registry (Component 2)

> **what is routable right now** — lanes stable, bindings volatile, `T0` rots unless this exists

**Spec:** `A2` Component 2 + `P2 v2.1` **Commit** `11f849b` **Tests** `11 passed` (C1-C10) **Policy** `f42df720`

Model-Scan is now **Component 2** of the five-component system. Its shift: from a local evidence scanner with 33 CLI commands and a web dashboard to the **registry that holds every volatile fact about models, providers, quotas, health, cost, and invocation** — so the prompt never does.

```
prompt:  "route this task"
   ↓ names only a lane (routine / review / specialist ...)
registry:  lane → bindings (model + provider + adapter_id + capacity_slots + quota + health + freshness + price + cost)
resolver:  floors first, then cost — never returns nothing, never inverts a floor
```

## Why This Exists

The previous prompt carried model names, prices, and quota numbers. Those rot between sessions and the prompt has no way to know it. Separation: **prompt = policy (which lane for which task class), registry = reality (what that lane can currently do and what it costs).** Renaming a model now touches only `registry.json` — no prompt or source change (C1, proven by `grep` gate).

## Quick Start (new path)

```bash
cd ~/code/model-scan

# Human: one screen, healthy / throttled / unknown at a glance
python3 -m registry.table
# LANE     BINDING          PROVIDER     MODEL               ADAPTER CAP PRICE  COST  STATUS
# routine  routine-free-1   opencode-zen example-flash-free  omp     4   free   0.002 ✓ healthy
# healthy=2 throttled=2 unknown=2

# Machine
python3 -m registry.table --json | jq .

# Validate registry against schema (every field present or explicitly unknown)
python3 -c "import json,jsonschema; jsonschema.validate(json.load(open('registry/registry.json')), json.load(open('registry/schema.json'))); print('OK')"

# Resolver — total over exactly 4 outcomes, floor-before-cost structurally impossible to invert (property test)
python3 -m pytest tests/test_registry_resolver.py -q  # 11 passed
# Covers: totality (every lane → one of 4), floor violation unproducible, staleness → degradation, 3-provider quota, unhealthy detection, calibration round-trip, source grep

# Decision log — why this lane was picked
cat ~/.local/share/model-scan/routing_decisions.jsonl | jq .
# {candidates_considered: [...], eliminated_by_floor: {...}, ranking_inputs: {cost, latency, quota...}}

# Cost ranking (accepted-result cost, not token price)
cat docs/cost-formula.md   # generation + reasoning + latency + retries + validation + review + quota + recovery
cat docs/registry-freshness.md  # per-field freshness, when to refresh (start of orchestration, quota exhaustion, provider failure, sustained 429, resumption)
```

## Architecture (after P2)

```
registry/
  schema.json          # per-model/binding with freshness stamp on every field, unknown sentinel
  registry.json        # 6 bindings, 3 lanes, capacity_slots (C8: 4 concurrent slots on a lane, not "lane exists")
  table.py             # human + --json

resolver/
  resolver.py          # total over 4: resolved / resolved+degradation / routing-policy-unavailable / routing-blocked; floors hard, cost never overrides
  cost.py              # accepted_result_cost (formula, inputs, missing-input behavior)
  decision_log.py      # candidates, eliminated_by_floor, ranking_inputs (debuggable bad routes)
  decision_log.schema.json

adapters/
  adapter.py           # adapter_id → command line; callers name only a lane; 2 impls: omp in-harness, agy exo-harness

quota/
  provider.py          # QuotaProvider interface + 4 impls
                       # CPAManagerPlusQuotaProvider (recommended first target, per-account/model/channel SQLite)
                       # ManagementAPIQuotaProvider, LocalDBQuotaProvider, CompositeQuotaProvider
                       # v6.10.0 split: Management API = config/credentials/logs; Usage = companion (SQLite)

health/
  probe.py             # classify_health(recent error rate, auth validity, quota headroom, p50/p95) + HealthRunner
                       # proxy account-pool primary, synthetic probe fallback; deliberately-unhealthy account detected

docs/
  alignment-report.md       # Phase 0 brownfield: punchlist 6/9 already answered, disposition KEEP/ADAPT/REPLACE/RETIRE
  council-resolution-semantics.md  # V(5,3,1) on four-outcome totality + floor-before-cost, dissent: provider_health==down as hard floor (revisit 1 month)
  registry-freshness.md     # staleness declared not inferred, refresh triggers
  cost-formula.md           # accepted-result cost with missing-input behavior
  handoff-phase2.md         # registry version, lanes, adapter interface, quota/health impls + what they cannot see, unknown fields (ram/vram, zen quota) with reasons
```

## The Four Outcomes (D2.2)

```
Given a lane request, resolver returns exactly one of:
  1. resolved route
  2. resolved route + degradation notice (floor met, preference not)
  3. routing-policy-unavailable (reason + named safe default)
  4. routing-blocked (specific missing requirement)
No fifth state, no silent `None`. Predecessor deadlocked here.
```

## What Remains Unknown (honest, from handoff)

- `ram/vram` per binding — no local measurement yet
- `quota_state` / `provider_health` for zen/openrouter — no CPA DB wired for those providers
- Vision cost/performance — Q3 data not applied

These are `unknown` explicitly, never fabricated (D2.1).

## Migration Note

Older v5 scoring, web UI (SvelteKit), gateway, ARDF, and 33-command CLI remain in checkout as **migration evidence** but are not authority to apply a route. The new registry is the authority. Do not add model names/prices/quotas to prompts — add them to `registry.json`.

## Use When

- Picking a harness/model for a task class — ask the registry, not the prompt
- Debugging a bad route — read `routing_decisions.jsonl`
- Calibrating — feed `observability/store/calibration-record.jsonl` into `registry.json` rankings (round-trip changes ranking in asserted direction, gate 9)

**Handoff:** `docs/handoff-phase2.md` + `registry/table` output + `calibration-record.json` shape (owned by Component 1, lives in `agent-contracts`, Component 2 consumes it).
