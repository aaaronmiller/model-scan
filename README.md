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

## Frontier (ARDF, folded in 2026-11-19)

`frontier/` is the cost-capability frontier, formerly the separate ARDF repository at
`/home/cheta/code/ardf/ardf`. It came in with its git history (`git log -- frontier/`); the old
repository stays in place as an archive and nothing reads it any more. Build, dashboard and
readers are in `frontier/README.md`:

```bash
cd /home/cheta/code/model-scan/frontier && python3 calibrate.py && python3 current_frontier.py
python3 -m http.server 8789 --bind 127.0.0.1 --directory /home/cheta/code/model-scan/frontier
# then open http://127.0.0.1:8789/dashboard.html
```

`ardf_roles.py` and `ardf_export.py` read it; so does the capacity-watch skill
(`frontier/data/current-comparison.csv`). `ardf_roles.py` matches frontier names to registry
ids with `free_rank.matcher` (no name map); its exclusions live in `role_policy.json` and its
quota multipliers come from the registry's own "(Nx usage)" labels.

## Free model ranking

`free_rank/` ranks the free models on OpenCode Zen, OpenCode Go, Kilo and OpenRouter purely
by formula from benchmark data. One command fetches a dated snapshot and writes the ranking:

```bash
cd /home/cheta/code/model-scan
python3 -m free_rank --refresh          # fetch catalogues and benchmark pages, then rank
python3 -m free_rank                    # rank from the latest snapshot, no network
python3 -m free_rank --compare /home/cheta/LIVING_DOCUMENTS/projects/masterplan/sources/free-model-tiers-2026-11-19/tiers.md \
  --change "what changed in config.json"   # also measure agreement and log the iteration
```

How it works, with every constant in `free_rank/config.json`:

1. **Discovery.** Each catalogue's own pricing fields decide "free": Zen and Go price every
   `cost` field at zero; Kilo sets `isFree` and zero prompt and completion prices; OpenRouter
   (all modalities) prices every `pricing` field at zero. Non-chat routes (video, rerank,
   embeddings, decisions) and routers are inventoried but not ranked.
2. **Benchmarks.** Live adapters read Artificial Analysis (leaderboard and coding-agent index),
   Vals Terminal-Bench 4, the Terminal-Bench board and KiloBench. Raw fetches are cached gzip
   in `free_rank/snapshots/<date>/` with URL, time, status and sha256. Publisher tables that
   exist only as images come from the transcribed evidence file
   `free_rank/evidence/l1-free-models-2026-11-19.json` (benchmark records only; its tiers are
   never read). A source host already read live for a model is not counted twice.
3. **Matching.** `free_rank/matcher.py` matches catalogue ids, canonical ids, weights repos and
   names after one normalisation; version numbers are kept, so different versions never match.
4. **Score.** Independent results win over publisher results; publisher-only values are
   discounted and count less as evidence. Each benchmark is normalised across the ranked pool,
   each family (agentic coding, repository repair, general agent) is a weighted mean shrunk
   toward a prior, so a missing benchmark lowers confidence instead of scoring zero, and the
   families are mixed by fixed weights plus a small log-scaled context bonus. Tiers are shares
   of the top score with minimum evidence and tool support. Limit tags (limited, sharing,
   region, expiry, zero retention) are reported, never scored.

Outputs in `free_rank/out/`: `ranking.json` and `ranking.md` (tiers, order, per-model score
breakdown with sources), `routes-l6.json` and `routes-l6.md` (omp, OpenCode and Kilo selectors
per route), and with `--compare`, `agreement.md` plus the iteration log
`agreement-iterations.jsonl` / `.md`. `tests/test_free_rank.py` fails if any module in
`free_rank/` or `ardf_roles.py` contains a model name from the evidence inventory or a
version-like literal.

Every earlier version of this project (model-scan-new, ARDF and its archive, model-scraper,
MODEL-DASHOARD, the classifier papers, the v4/v5 docs) was audited on 2026-11-19: each file has
a disposition and each idea a category in
`/home/cheta/LIVING_DOCUMENTS/projects/model-scan/version-ledger.md`.

## Migration Note

Older v5 scoring, web UI (SvelteKit), gateway, and 33-command CLI remain in checkout as **migration evidence** but are not authority to apply a route. The new registry is the authority. Do not add model names/prices/quotas to prompts — add them to `registry.json`.

## Use When

- Picking a harness/model for a task class — ask the registry, not the prompt
- Debugging a bad route — read `routing_decisions.jsonl`
- Calibrating — feed `observability/store/calibration-record.jsonl` into `registry.json` rankings (round-trip changes ranking in asserted direction, gate 9)

**Handoff:** `docs/handoff-phase2.md` + `registry/table` output + `calibration-record.json` shape (owned by Component 1, lives in `agent-contracts`, Component 2 consumes it).
