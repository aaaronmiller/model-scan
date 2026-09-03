# Alignment Report — Phase 2 Routing Registry (model-scan)

**Date:** 2026-09-02
**Phase:** 2 — Routing Registry (model-scan)
**Contract version:** T0 v3.1 + A2 v2.1
**Author:** Phase 2 coordinator (codex primary)
**Gate:** Must land before any new code is written. Informs integration pass what changed and why.

---

## 1. Readiness gate (WA.RE.01)

| Check | Result | Evidence |
|-------|--------|----------|
| Tooling on PATH | **PASS with caveat** | `cass`  (0.41s), `ld` (living-documents shim), `qm` (quartermaster) all resolve via `which`. `ld validate` → 33 pages valid. `cass triage` → **stale** — fingerprint mismatch, lexical checkpoint `completed:false`, `partial:true`. Incremental `cass index` defers repair at this DB size (`checkpoint_incomplete`). Full rebuild required (`cass index --full`) but not blocking lexical search (degraded, still covers 752 conversations). |
| Intent record exists | **PASS** | `/home/cheta/LIVING_DOCUMENTS/projects/model-scan/` — 33 pages, `start-here.md` updated 2026-08-15, `requirements.md`/`design.md` canonical, `tasks.md` all lanes complete, `decisions.md` current. |
| Dossier sections complete | **PASS** | Every required type present: project, requirements, design, plan, tasks, decisions, history, resources, plus 5 tranches + 2 audit updates. `ld validate` passes. |
| Session index not stale | **FAIL (recoverable)** | Stale per above. Strategy: search remains usable; no punchlist item depends on a missing recent session that a full rebuild would surface, verified by `cass search` error path still returning bounded verdict. Recommend `cass index --full` before council evidence pack, not before alignment. |
| Providers outside index audited directly | **PASS** | No provider outside the project pool is invoked by current model-scan code without inspection. Provider sources inspected directly: `source_adapter.py`, `quota_meter.py`, `gateway.py:build_routing_snapshot`, plus live probe of `~/.config/model-scan/model_scan.db` and `routing_snapshot.json`. |

**Verdict:** Loop may proceed. The stale index is the only degradation and does not manufacture false blockers for this phase — it is documented, its workaround is explicit, and its repair is queued.

---

## 2. Punchlist triage against the intent record

The "stalled since mid-August behind a punchlist" refers to `TODO.md` (Phase 3, 6 tasks remaining as of 2026-06-19, now superseded) plus the nine open questions raised in `intent-archaeology-update-2026-08-16.md` and resolved/left-open in `blocking-questions-resolved-2026-08-20.md`.

### 2.1 Prior claim verified: 6 of 9 already answered

An independent read of `blocking-questions-resolved-2026-08-20.md` confirms:

| Q | Topic | Prior disposition | Classification per WA.DS intake ledger |
|---|-------|-------------------|----------------------------------------|
| Q1 | Tier boundary rule | **ANSWERED** — price-based boundary at $0.30/task, not gap detection. Implemented as `TIERS` in `model_roles_api.py`. | **Incorporated** — durable decision, code already reflects it. |
| Q2 | Substitutability tolerance | **ANSWERED** — same price band = interchangeable; capability tie broken by functional property. | **Incorporated** |
| Q3 | Task fixture set | **STILL OPEN** — no tasks, judge, or count decision. Blocks REQ-3a.2, REQ-5a, gate 9. | **Genuinely blocked** |
| Q4 | Canonical model identities | **ANSWERED** — 6 of 7 tested against live registry capture 2026-08-20 (`available-models.json`, 791 models/14 providers). | **Incorporated** |
| Q5 | Opus High vs XL | **ANSWERED empirically** — xhigh dominates max on price at equal capability. | **Incorporated** |
| Q6 | Quota vs cheapest-adequate | **ANSWERED** — marginal cost resolves conflict; cheapest-adequate governs, allowance exhaustion is observation. | **Incorporated** |
| Q7 | Local tool-caller hardware budget | **STILL OPEN, possibly moot** — "never assign to llama" + local models "unsuitable for almost all work." Needs withdrawal vs exception decision. | **Genuinely blocked (low severity)** |
| Q8 | AA authorization | **STILL OPEN** — scrape vs API, terms. AA data already in use via ARDF import, so formally inconsistent. | **Genuinely blocked** |
| Q9 | Which ARDF package to freeze | **ANSWERED BY ACTION** — `ardf/ardf` canonical via commit `81079f8`, 2,839-row ledger pinned. | **Incorporated** |

**Nothing to escalate beyond the three already named.** Each of the six incorporated items already has a durable record and a code footprint; re-escalating them would reproduce the stall. The three open items each propose a safe default in §2.2.

### 2.2 The three genuinely remaining blockers — with proposed defaults

| Blocker | Impact on Phase 2 | Proposed safe default (WA.RE.03) | What Phase 2 will do without an answer |
|---------|-------------------|-----------------------------------|----------------------------------------|
| **Q3 — task fixture set** | Blocks per-task cost observation (REQ-3a.2) and role→tier mapping grounding. Phase 2 deliverable C4 (accepted-result cost) needs `task_class` and `modality` examples. | Treat ARDF's `standard-task-price-proxy-v7` as the **interim task cost proxy**. Document that capability calibration remains AA-derived until fixtures land. No new judgement of success invented. | Ship C4 formula with `task_class` left as an explicit `unknown` dimension; ranking degrades to frontier-with-price-proxy, not a fabricated fixture run. |
| **Q8 — AA authorization** | Blocks adding a new AA frontier-table scraper as a first-class source adapter. | **Do not scrape.** Continue via the versioned AA cache already on disk (`aa_cache.json`, 540 models) and the ARDF ledger import. No new AA HTTP surface until authorization with terms. | AA adapter stays in `unknown`/stale state in the registry; health reflects the cache file's age, not a live probe. |
| **Q7 — local hardware budget** | Blocks REQ-11.5 local tool-caller capacity modeling in D2.1 (`local RAM/VRAM`). | **Assume REQ-11.5 is deferred, not withdrawn.** Record `unknown` for local RAM/VRAM, add a note referencing the 2026-08-20 "almost all work" direction, and do not size a local concurrency lane. | No local lane published; resolver abstains on local-only queries with `routing-blocked: insufficient capacity evidence`. |

### 2.3 TODO.md and other historical punchlist items

`TODO.md`'s six "remaining" Phase 3 tasks (gold standard, CPMR, optimization loop, audit, supplemental benchmarks, refinement cron) were superseded by `implementation-completion-2026-08-15.md`, which closed MS-003/MS-005/MC-002 with a different decomposition (evidence contract + role evaluation + source adapter + API gate). Those TODO entries are **superseded**, not open. The canonical task list is now `tasks.md` + `what-to-do.md`, both marked complete with "wait for a named live evidence-collection or integration target."

No additional punchlist item manufactures a Phase 2 blocker.

---

## 3. Inventory against Phase 2 deliverables (D2.1–D2.7)

Every file listed was inspected (`read` + `grep` + `glob`). Disposition follows the contract's vocabulary.

### D2.1 — Registry schema and data

| Existing artifact | Disposition | Reason / work required |
|-------------------|-------------|------------------------|
| `contracts/routing_snapshot.schema.json` | **ADAPT** | Covers the *output* snapshot (15 S* slots, rank map, provider health/ quota excerpt). Does not model the *registry itself* (per-model lane binding, harness restriction, context/modality limits, price class, freshness stamp per field, `adapter_id`, `unknown` semantics). Adapt by extracting the snapshot line and promoting a new `registry.schema.json` (and `registry.json` data) that snapshots can be derived from. Fulfills C1 (stable lane names) and C3 (per-field freshness). |
| `tiers.yaml` | **KEEP** | Satisfies the tier-band input to D2.1 price-class derivation. Already consumed by `model_roles_api.py:TIERS`. Keep as data dependency, not part of registry schema. |
| `blocklist.yaml` | **KEEP** | Satisfies the blocklist dimension of provider/model eligibility. |
| `slot_grid.py` + `slot_grid` tests | **ADAPT** | Implements provider-slot geometry but against the legacy slot namespace (now S*). Adapt to emit lane bindings, not slot rows. Logic for capability/latency/tool gates is reusable. |
| `evidence_contract.py` / `capability_evidence.py` + schemas | **KEEP** | Satisfy REQ-2/REQ-5 provenance; they feed the registry but are not the registry. No change. |
| `~/code/agent-contracts/lanes.yaml` (5 lanes) | **KEEP** | Canonical lane vocabulary (adjudication/durable/review/routine/specialist). D2.1 lane bindings must key off this file, not duplicate it. |
| *Missing:* `registry.schema.json` + `registry.json` + per-field `freshness` + `unknown` sentinel | **REPLACE** (greenfield) | Justification: no current artifact models harness-bound restrictions, in-harness vs exo-harness eligibility, tool-compatibility, RAM/VRAM, quota state provenance, or per-field staleness. Cannot be retrofitted onto the snapshot schema without breaking its Gateway contract. |

### D2.2 — Resolver, total over four outcomes

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `slot_resolver.py` | **ADAPT** | Closest to a resolver: given a request, returns a ranked lane. Not total — it throws/returns `None` on missing lanes and has no `routing-policy-unavailable` / `routing-blocked` terminal states, no floor-before-cost proof, and no degradation notice. Adapt into `resolver.py` that is total over exactly four outcomes per spec. |
| `adaptive_limiter.py` | **KEEP** | Concurrency limiter logic useful to the resolver's capacity check, but not the resolver itself. |
| `scoring/` pipeline | **KEEP** | Feeds scoring inputs; does not decide routing. |

**New:** `resolver.py` + property test proving floor-before-cost (C2), plus on-disk `routing_decision` log writer (D2.6 is the log; D2.2 is the decision).

### D2.3 — Adapters, `adapter_id`

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `source_adapter.py` | **ADAPT** | Implements Gap G3's predecessor: discovery/callable/probe/policy states with provenance, quarantine, last-good. However it names *source providers*, not *harness invocation lines*. It lacks `adapter_id`, the in-harness vs exo-harness split, and the "model rename touches only registry data" invariant. Adapt by introducing `adapters/` interface (`adapter.py` protocol + two implementations: e.g. `omp_adapter.py` and `exo_adapter.py`/`agy_adapter.py`) and having `source_adapter.py` become one data supplier behind the registry, not the adapter itself. |
| *Missing:* adapter interface + two implementations | **REPLACE** | Justification: no existing file owns the command-line that invokes a binding, nor proves the lane→invocation separation. The acceptance clause "rename model in registry data requires no prompt or component source change" has no current artifact to test against. |

### D2.4 — Quota provider interface, with CLI Proxy API implementation

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `quota_meter.py` + `spend_ledger.py` + `gateway_bridge.py` | **ADAPT** | Implements local spend/quota-metering against `model_scan.db` and the CLI Proxy API telemetry path (Gateway `POST /reliability` → `reliability_feedback.jsonl`). Provides per-provider accounting, but not a `QuotaProvider` interface with pluggable `Management Center` vs `CPA-Manager-Plus` vs `CPA Usage Keeper` vs SQLite fallback. Needs a `quota/` interface (e.g. `quota/provider.py` protocol + `cpa_manager_plus.py` + `management_api.py` + `local_db.py`) where `quota_meter.py` becomes one backend. |
| `gateway.py` (`GET /quota/ledger`, etc.) | **KEEP** | Serves quota as data; consumed by dashboard. Not the provider interface itself. |
| *Missing:* provider admin vs usage distinction (Mgmnt vs Usage Keeper/Plus) | **REPLACE** | Justification: current code conflates admin (credentials/config) with usage (tokens/cost) — precisely the v6.10.0 split the spec calls out. No existing code probes the documented "usage moved to companion projects" endpoints. Building that behind a uniform interface is new. |

Coverage note: the spec's acceptance gate 7 requires live quota readable for ≥3 providers through the interface. Local DB + reliability feedback + one Proxy API adapter can satisfy it without reaching into private credential stores; document which providers are readable on this machine and which are `unknown` with reason.

### D2.5 — Health probe definition and runner

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `routing_snapshot.py: provider_health` + `gateway.py: check_provider_health()` | **ADAPT** | Produces a `healthy/degraded/down/unknown` field fed by reliability feedback and `check_provider_health()` against the local `models` table. No definition of what health *means* (error rate window, auth validity, quota headroom, latency percentile), no synthetic probe, and no account-pool health from the proxy layer. Adapt by adding `health/` (definition document + `probe.py` + `runner.py`) and having current snapshot code consume the runner's output rather than compute health inline. |
| *Missing:* health schema, probe runner, degraded-account detection | **REPLACE** | Justification: the field exists but has no producer contract; gate 8 ("deliberately unhealthy account is detected") cannot be satisfied by current code. |

### D2.6 — Routing decision log

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `gateway_dashboard.html` + `~/.config/model-scan/config_changelog.jsonl` | **RETIRE (as D2.6)** | Changelog is about config application, not routing decisions. Dashboard renders decisions but does not log them. Neither satisfies "which candidates were considered, which floor eliminated each, which ranking inputs used." |
| `dink.py` scan log | **KEEP** | Useful context, not a routing decision log. |
| *Missing:* `routing_decision.log.jsonl` schema + writer | **REPLACE** | Greenfield; no existing file is the routing decision log. Must be append-only, correlated to resolver calls, and owned by the resolver. |

### D2.7 — Human table output

| Existing artifact | Disposition | Reason |
|-------------------|-------------|--------|
| `tui.py` | **KEEP** | Already satisfies an interactive human table. Keep; add a D2.7-compatible `--registry` view rather than replacing. |
| `gateway_dashboard.html` | **KEEP** | Satisfies a web human table. Keep; add registry health row. |
| `cli_overall.py` | **KEEP** | `model-scan overall` is the existing human SKU summary. Keep; do not conflate with lane table. |
| *Missing:* `--json` for agents + compact one-screen lane table (`model-scan registry` / `registry table`) | **ADAPT** | Add a `registry table` command and `--json` projection to existing `dink.py`/`gateway_cli.py` surface; do not replace existing CLI. Must show healthy/throttled/unknown in one screen per spec. |

### Cross-cutting constraints (C1–C8) mapping

| Constraint | Existing coverage | New artifact bearing the proof |
|------------|-------------------|--------------------------------|
| C1 lanes stable, models volatile | `lanes.yaml` exists (good) | `registry.json` keys lanes; prompt never mentions model name |
| C2 floors hard, before cost | no proof | property test over random registries/requests |
| C3 staleness declared | no per-field freshness | `freshness` object per field + "when to refresh" doc |
| C4 accepted-result cost | partially in `scoring/` | explicit formula + missing-input behavior doc |
| C5 separate frontiers | REQ-5a tiers exist | lane × task-class ranking separation |
| C6 telemetry contradicts policy | unhandled | incident record: preserve evidence, route conservative, flag recalibration |
| C7 calibration record schema not owned | `~/code/agent-contracts/calibration-record.json` exists — Component 1 owns it | consume it, do not redefine |
| C8 multi-account fan-out | partially in `session_manager.py` slot allocation | model as `capacity: { slots: N }` in registry |

---

## 4. Existing consumers — compatibility promise

| Consumer | What it calls today | Compatibility guarantee |
|----------|---------------------|-------------------------|
| **claude-code-proxy (Gateway)** | `~/.config/model-scan/routing_snapshot.json` via `GET /routing-snapshot`; `POST /reliability` feedback; rank map `gateway-rank-evidence-*.json` | **Preserved.** Registry is upstream; snapshot shape unchanged. New registry emits snapshots through existing `routing_snapshot.py` path. No break without a shim + deprecation note. |
| **Harness / `~/.config/hermes/config.yaml`** via `model_roles_api.py` | `TIERS`, role→tier mapping, `cli_overall` | **Preserved.** Role tables continue to resolve from `tiers.yaml`. Registry adds lane bindings; does not replace tier bands. |
| **Operator — CLI/TUI** | `dink.py` flags (`--emit-snapshot`, `--analyze`, `--tui`, etc.), `gateway_cli.py rank-map` | **Preserved.** Flags kept; new `registry` subcommands added alongside, not replacing. |
| **Operator — Web/Dashboard** | `gateway_dashboard.html` served by `gateway.py` | **Preserved.** Dashboard gains a registry section; existing routes untouched. |
| **Cron / `cron_manager.py`** | `dink.py --mode daily --emit-snapshot` | **Preserved.** Cron continues to emit snapshots; registry refresh can be cron-driven behind the same lock/checkpoint discipline. |
| **Living Documents `ld` analytics** | reads `model-scan` commits/metrics via `cass` + git | **Preserved.** No LD schema change required. |
| **Quartermaster `qm`** | lists skills; no current coupling | No guarantee needed. |

**Shim rule:** If any snapshot field must change for D2.1 reasons, ship a parser-compatible superset (new fields additive, old fields kept for one release window) plus a deprecation note in `CHANGELOG.md`.

---

## 5. Stale generated output

| Path | Finding | Action |
|------|---------|--------|
| `/tmp/ld-analytics-cron.log` | analytics generator computed 12-week slope but labeled it 4-week (audit §Upstream filing) | Not model-scan owned; file left in place, noted here for Component 5 awareness. No model-scan action. |
| `~/.config/model-scan/routing_snapshot.json` (scan_id 87) | `provider_health: {openrouter: down}` — current snapshot reflects a down provider, which is valid health data, not staleness. `generated_at` 2026-08-30 is 3 days old; freshness policy will mark it stale per D2.5 definition. | On registry bootstrap, recompute freshness against D2.5 thresholds; surface degradation notice rather than silent reuse. |
| `__pycache__/` | standard | ignore; `.gitignore` already covers. |

---

## 6. What remains to build (ordered)

1. **Council V(5,3,1)** on resolution semantics (four-outcome totality + floor-before-cost) — spec §Council requirement. Must run before implementing `resolver.py`. Record dissent and changes.
2. **D2.1** `registry.schema.json` + `registry.json` + freshness + `unknown` sentinel + `docs/registry-freshness.md`.
3. **D2.3** `adapters/` interface + two implementations (in-harness + exo-harness) + rename-model test.
4. **D2.2** `resolver.py` (total) + property test (C2) + degradation-notice logic + C3 stale-notice path.
5. **D2.4** `quota/` interface + Proxy API implementation (CPA-Manager-Plus recommended) + local-DB fallback; live probe for ≥3 providers.
6. **D2.5** `health/` definition + runner + account-pool vs synthetic probe.
7. **D2.6** routing decision log schema + writer, wired to resolver.
8. **D2.7** compact lane table (`--json` + human table).
9. **C4 formula doc** + separate-frontiers note + C6 contradiction handling.
10. Handoff note: versions, lane vocabulary, adapter interface, quota/health capabilities vs blind spots, log format, currently-unresolvable fields.

Each item lands with a freshness stamp or explicit `unknown`; no field defaults to fabricated data.

---

## 7. Decisions captured by this report

- **Decision 2026-09-02-01:** Treat `TODO.md`'s six Phase 3 leftovers as superseded by `implementation-completion-2026-08-15.md`. Canonical queue is `tasks.md` + `what-to-do.md`. Rationale: §2.3 — prior completion review with evidence gate 240+48 tests.
- **Decision 2026-09-02-02:** The three blocking questions (Q3, Q7, Q8) are the only genuine punchlist blockers; the other six are incorporated and will not be re-escalated. Rationale: §2.1 — each has a durable decision and a code footprint.
- **Decision 2026-09-02-03:** Interim cost axis remains `standard-task-price-proxy-v7`; AA live scrape not authorized; local hardware budget deferred. Rationale: §2.2 safe defaults, preserving privacy and credential boundaries (WA.EV.04 Yellow/Red).
- **Decision 2026-09-02-04:** No ARDF role in the routing registry runtime path; the frozen ARDF fixture remains a test input only per `design.md` and `decisions.md` 2026-08-16. Rationale: same — ARDF is prior art, not authority.

---

*End of report. Next step: run the Structured Review V(5,3,1) on resolution semantics, then proceed in §6 order. No new project code was written to produce this report.*
