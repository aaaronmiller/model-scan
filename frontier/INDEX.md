# ARDF Consolidated Working-Set Index (v7.5.0)

This is the **current canonical working package** (`/home/cheta/code/model-scan/frontier`, version **7.5.0**, updated **2026-11-09**; folded into model-scan from `/home/cheta/code/ardf/ardf` on 2026-11-19, where the old repository stays as an archive). Its immutable authoritative core contains nine required files plus the tracked presentation template (`dashboard-template.html`), the primary AA/Priors refresh utility (`current_frontier.py`), the AA vs. Priors verification ledger (`docs/current-frontier.md`), and the errata/judicial audit log (`ERRATA-and-findings.md`). All superseded historical folders, August backups, and duplicate drafts have been staged in `/home/cheta/code/ardf/ardf-archive/ready-for-deletion/`.

The governing rule for the authoritative export is one file per irreducible responsibility. An exported file exists only if merging it would blur an important boundary between evidence, executable method, machine-editable policy, visualization, operational decision output, accumulated user intent, research documentation, or package navigation.

## Current canonical files

| File | Status | Purpose | Why it deserves its own file |
|---|---|---|---|
| `data/unified-model-evidence.csv` | **AUTHORITATIVE DATA** | Single canonical evidence ledger: catalog rows (`1,418`), atomic benchmark/cost observations (`6,312`), provenance, model identity, models.dev metadata, raw values, and calibrated columns (`7,775` total rows). | Data must remain inspectable and separable from code/presentation. There is no second model/evidence ledger. |
| `project-config.json` | **AUTHORITATIVE POLICY** | Calibration algorithms, reference scales, manual anchors, 4-tier/Pareto/pinch-point analysis policy, dashboard policy, source-acquisition manifest, and source ledger (`v7.5.0`). | Machine-readable policy/source definitions should be editable without changing Python and should not be fragmented across sidecars. |
| `calibrate.py` | **AUTHORITATIVE EXECUTABLE** | Regenerates standardized task-cost fallback rows, calibrates the ledger, applies the 6-MAD scale sanity filter, computes Pareto/tier/pinch-point/executor analyses, regenerates the two decision documents, embeds dashboard payloads, and validates the nine-file architecture. | Calibration/derived-data math belongs outside HTML. All deterministic build logic is consolidated here. |
| `dashboard-template.html` / `dashboard.html` | **CURRENT VISUALIZATION & INTEGRATED SITE** | Self-contained offline all-model explorer with embedded calibrated evidence/analysis payloads, dim effort-lineage trajectories, smart Pareto + contender labels, interactive filtering, and full integrated research/routing/tiers/audit tabs. | `dashboard-template.html` is the tracked presentation source; `calibrate.py` embeds the generated payloads to produce `dashboard.html`. |
| `pareto-frontier-cheatsheet.md` | **CURRENT DECISION REFERENCE** | 21-point strict Pareto frontier, unrestricted and T3+ role-gated executor shortlists, named/algorithmic near-frontier misses, Muse/Luna economics, top-end routing cuts, and external frontier cross-checks. | Pareto/economic selection is distinct from capability tiers and deserves its own concise operational reference. |
| `model-tiers-and-contenders.md` | **CURRENT CAPABILITY REFERENCE** | 4-tier operational policy (`T1` to `T4`), current scored configurations by tier, top contested region (`>= 50`), pinch-point contested pairs (`delta cap <= 2.0`, `delta cost <= 25%`), bottom contested region, and Bottom-4 (`T4`) interchangeability matrix by use case. | Capability stratification and boundary contests are conceptually different from economic Pareto dominance. |
| `user-prompt-aggregation.md` | **AUTHORITATIVE INTENT / RESTART CONTRACT** | Accumulated user requirements, artifact contract, architectural corrections, failure modes, and restart instructions for future sessions/agents. | User intent must not be reconstructed from research prose or inferred from code. |
| `ardf-research-paper.md` | **CURRENT RESEARCH DOCUMENT** | Overall project paper containing rationale, evidence model, calibration methodology, dispersion/6-MAD outlier handling, cost model, operational routing matrix, provisional free candidates, source acquisition manual, and release history. | Human-facing methodology/provenance belongs in a research document, not in config or code comments. |
| `INDEX.md` | **CURRENT PACKAGE MAP** | This file. Defines the nine-file contract and maps every former v7.3 and archived artifact to its surviving responsibility. | A compact package still needs an explicit authority/status map so it does not re-fragment later. |

### Supporting tracked files in `/home/cheta/code/model-scan/frontier`

| File | Role |
|---|---|
| `current_frontier.py` | Recomputes the November 2026 primary Artificial Analysis v4.2 10-benchmark composite and Priors API cross-check from `sources/current/aa-primary.json.gz` and `sources/current/priors-api.json`. |
| `docs/current-frontier.md` | Exact 116-model AA v4.2 vs. Priors API and subscription frontier verification ledger generated by `current_frontier.py`. |
| `ERRATA-and-findings.md` | Judicial audit report (`v7.5.0`) and historical errata record. |
| `docs/routing-rules.md`, `docs/full-frontier.md`, `docs/free-routes.md`, `docs/priors-deltas.md` | Generated by `calibrate.py` from the primary AA block and `sources/current/`: at most 12 routing rules of thumb each citing its data; the frontier of all models and of each provider; the free-route evaluation (zero-price Kilo, OpenRouter and OpenCode Zen entries matched to scored configurations); and the exact ARDF-versus-Priors deltas. Never edit by hand. |
| `tests/verify_dashboard.py` | Verification of the rebuilt dashboard: runs the in-page self-test in headless Chromium (filters, zero and unknown costs, offline tier weighting, no network) and cross-checks the page against `current_frontier.py`. Run after `python3 calibrate.py`. |

## Authority order

When artifacts disagree, use this order:

1. **Raw/provenance facts:** `data/unified-model-evidence.csv` and `sources/current/`.
2. **Policy/algorithm/source definitions:** `project-config.json`.
3. **Derived calculation behavior:** `calibrate.py` and `current_frontier.py`.
4. **Generated decision state:** `pareto-frontier-cheatsheet.md`, `model-tiers-and-contenders.md`, `docs/current-frontier.md`, and the embedded payload in `dashboard.html` after running `python3 calibrate.py`.
5. **Methodology and acquisition guidance:** `ardf-research-paper.md` and `ERRATA-and-findings.md`.
6. **Accumulated user requirements:** `user-prompt-aggregation.md` governs intended behavior and triggers corrections to lower-level artifacts when they conflict with explicit requirements.

## Normal workflow

Run `python3 calibrate.py` from `/home/cheta/code/model-scan/frontier` after changing evidence, prices, calibration policy, or analysis policy. It updates the standardized cost fallback, calibrated columns, Pareto/tier documents, dashboard embedded payloads, and performs structural validation. `python3 calibrate.py --no-docs` recalibrates the CSV without rebuilding the human/dashboard outputs. The script is standard-library-only.

The rendered `dashboard.html` is rebuilt on every `python3 calibrate.py` run from `dashboard-template.html`. Presentation and integrated content edits belong in `dashboard-template.html`, never in `dashboard.html` directly.

## Disposition of the former 40-file v7.3 tree and 21 archive snapshots

All historical material from `/home/cheta/code/ardf/` and `/home/cheta/code/ardf/ardf/docs/` (before the fold) was audited against the canonical v7.5.0 files and staged in `/home/cheta/code/ardf/ardf-archive/ready-for-deletion/` (documented in `/home/cheta/code/ardf/ardf-archive/README.md`).

| Former v7.3 / Archive file | Disposition in v7.5.0 canonical package | Rationale |
|---|---|---|
| `INDEX.md` | -> `INDEX.md` | Rewritten around the v7.5.0 authority model. |
| `README.md` | -> `INDEX.md` + `ardf-research-paper.md` Appendix B | Quick-start/package semantics moved to the index; substantive project notes preserved in the paper. |
| `calibration-audit.md` (`ardf-archive/useful/`) | -> `calibrate.py` (`ana_dispersion`, `ana_scale_filter`) + `ardf-research-paper.md` Section 9.4 | Dispersion metrics (`std_err`, `spread`, `provisional`) and the 6-MAD scale outlier filter are active in code and documented in the paper. |
| `ardf-ux-linear` (`ardf-archive/old/`) | -> `model-tiers-and-contenders.md` + `dashboard-template.html` | Rescued the 4-tier operational policy (`T1` to `T4`), Pinch-Point Contested Matrix, and Bottom-4 (`T4`) Interchangeability Matrix. |
| `model-routing-2026-11-04.md` (`~/LIVING_DOCUMENTS/projects/ardf/`) | -> `ardf-research-paper.md` Appendix D + `dashboard-template.html` | Rescued the Operational Routing Matrix by workload, Subscription vs API cost basis, and Provisional Top-10 Free Candidates. |
| `calibration-studio.html` | -> `project-config.json` + `calibrate.py` + dashboard calibration selectors | Editable calibration policy and inspectable algorithms live in config and the main dashboard. |
| `config/*.json` | -> `project-config.json` | Consolidated machine-readable policy. |
| `docs/context-restart-meta-prompt.md` | -> `user-prompt-aggregation.md` | Expanded into the canonical accumulated-intent/restart artifact. |
| `docs/methodology.md` | -> `ardf-research-paper.md` | Methodology is the main body of the overall project paper. |
| `docs/pareto-executor-cheatsheet.md` | -> `pareto-frontier-cheatsheet.md` | Retained, renamed, and generated by the single build script. |
| `docs/source-acquisition-cheatsheet.md` | -> `ardf-research-paper.md` Appendix A + `project-config.json` | Human playbooks live in the paper; machine source definitions live in config. |
| `generated/*.js`, `generated/*.json` | -> embedded `window.ARDF_DATA` + `window.ARDF_ANALYSIS` inside `dashboard.html` | Eliminates external file dependencies for offline viewing. |
| `reports/*.md` | -> `calibrate.py` validation + `ERRATA-and-findings.md` | Build-integrity assertions are executable; judicial audit findings live in `ERRATA-and-findings.md`. |
| `scripts/*.py` | -> `calibrate.py` + `current_frontier.py` | Consolidated into standard-library executables. |
| `source-methodology.html` / `views/*.html` | -> integrated tabs in `dashboard-template.html` (`dashboard.html`) | All written resources are now styled and integrated directly into the single visualization application. |

## Deliberately not separate files

The following are **not** allowed to reappear as independent working artifacts unless a future requirement demonstrates a real responsibility boundary: generated JS/JSON payloads, rendered copies of Markdown documents, dated validation reports, one-source synchronization scripts, one-off migrations, duplicate scoped dashboards, duplicate config files, duplicate source ledgers, or an internal archive directory.
