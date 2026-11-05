# ARDF Consolidated Working-Set Index

This is the **current working package**. Its immutable authoritative export
contains exactly nine files. Supporting provenance and transition records may
remain beside that export, but they are non-authoritative and must not replace
or override any of the nine files below. The prior v7.3 ZIP remains the
archival record.

The governing rule for the authoritative export is one file per irreducible
responsibility. An exported file exists only if merging it would blur an
important boundary between evidence, executable method, machine-editable
policy, visualization, operational decision output, accumulated user intent,
research documentation, or package navigation.

## Current files

| File | Status | Purpose | Why it deserves its own file |
|---|---|---|---|
| `data/unified-model-evidence.csv` | **AUTHORITATIVE DATA** | Single canonical evidence ledger: catalog rows, atomic benchmark/cost observations, provenance, model identity, models.dev metadata, raw values, and calibrated columns. | Data must remain inspectable and separable from code/presentation. There is no second model/evidence ledger. |
| `project-config.json` | **AUTHORITATIVE POLICY** | Calibration algorithms, reference scales, manual anchors, analysis/tier/Pareto policy, dashboard policy, source-acquisition manifest, and source ledger. | Machine-readable policy/source definitions should be editable without changing Python and should not be fragmented across five sidecars. |
| `calibrate.py` | **AUTHORITATIVE EXECUTABLE** | Regenerates standardized task-cost fallback rows, calibrates the ledger, computes Pareto/tier/executor analyses, regenerates the two decision documents, embeds dashboard payloads, and validates the nine-file architecture. | Calibration/derived-data math belongs outside HTML. All deterministic build logic is consolidated here. |
| `dashboard.html` | **CURRENT VISUALIZATION** | Self-contained offline all-model explorer with embedded calibrated evidence/analysis payloads, filtering, evidence inspection, Pareto visualization, tables, and external-frontier panels. | Interactive visualization is a distinct user surface. Generated JS/JSON payloads are embedded here instead of shipped separately. |
| `pareto-frontier-cheatsheet.md` | **CURRENT DECISION REFERENCE** | Strict Pareto frontier, price/performance, executor shortlist, named/algorithmic near-frontier misses, Muse/Luna economics, top-end routing, and external frontier cross-checks. | Pareto/economic selection is not the same thing as capability tiers and deserves its own concise operational reference. |
| `model-tiers-and-contenders.md` | **CURRENT CAPABILITY REFERENCE** | Capability-tier definitions and membership, top contested region, bottom/low-cost contested region, closest Pareto competitors, and named high-interest competitors. | Capability stratification and boundary contests are conceptually different from economic Pareto dominance. |
| `user-prompt-aggregation.md` | **AUTHORITATIVE INTENT / RESTART CONTRACT** | Accumulated user requirements, artifact contract, architectural corrections, failure modes, and restart instructions for future sessions/agents. | User intent must not be reconstructed from research prose or inferred from code. |
| `ardf-research-paper.md` | **CURRENT RESEARCH DOCUMENT** | Overall project paper containing rationale, evidence model, calibration methodology, cost model, source acquisition/refresher manual, identity rules, validation, limitations, release history, and operational notes. | Human-facing methodology/provenance belongs in a research document, not in config or code comments. |
| `INDEX.md` | **CURRENT PACKAGE MAP** | This file. Defines the nine-file contract and maps every former v7.3 artifact to its surviving responsibility. | A tiny package still needs an explicit authority/status map so it does not re-fragment later. |

## Authority order

When artifacts disagree, use this order:

1. **Raw/provenance facts:** `data/unified-model-evidence.csv`.
2. **Policy/algorithm/source definitions:** `project-config.json`.
3. **Derived calculation behavior:** `calibrate.py`.
4. **Generated decision state:** `pareto-frontier-cheatsheet.md`, `model-tiers-and-contenders.md`, and the embedded payload in `dashboard.html` after running `python calibrate.py`.
5. **Methodology and acquisition guidance:** `ardf-research-paper.md`.
6. **Accumulated user requirements:** `user-prompt-aggregation.md` governs intended behavior and should trigger corrections to lower-level artifacts when they conflict with explicit requirements.

## Normal workflow

Run `python calibrate.py` from the package root after changing evidence, prices, calibration policy, or analysis policy. It updates the standardized cost fallback, calibrated columns, Pareto/tier documents, dashboard embedded payloads, and performs structural validation. `python calibrate.py --no-docs` recalibrates the CSV without rebuilding the human/dashboard outputs. The script is standard-library-only.

The rendered `dashboard.html` is ignored by Git. `dashboard-template.html` is the tracked presentation source for a clean checkout: `calibrate.py` always reads the template, embeds the canonical ledger, and writes the rendered dashboard; an existing `dashboard.html` is overwritten and is never a build input, so presentation edits belong in the template. The template also includes the November 2026 Priors snapshot and an optional live Priors comparison; this separate projection does not refresh the canonical historical ledger. Tier multipliers are subjective, optional, and default to neutral.

Source acquisition is intentionally not hidden inside the deterministic calibration pass. The source manifest, exact entry points, fields, provenance rules, and refresh playbooks are consolidated in `project-config.json` and the source-acquisition appendix of `ardf-research-paper.md`. A refresh updates atomic rows in the canonical CSV first; calibration then consumes that ledger.

## What happened to the former 40-file v7.3 tree?

No historical material was destroyed. The original v7.3 ZIP is the archive. The consolidated working package keeps only the current responsibilities, while unique content/function from the old files is folded into the nine files above.

| Former v7.3 file | Disposition in consolidated package | Rationale |
|---|---|---|
| `INDEX.md` | → `INDEX.md` | Rewritten around the nine-file authority model. |
| `README.md` | → `INDEX.md` + `ardf-research-paper.md` Appendix B | Quick-start/package semantics moved to the index; substantive project notes preserved in the paper. |
| `archive/README.md` | → `INDEX.md` | Archive policy is now simple: the original ZIP itself is the archive. |
| `archive/release-notes/current-model-refresh-2026-08-08.md` | → `ardf-research-paper.md` Appendix C | The forensic refresh history remains readable without a release-note subdirectory. |
| `archive/superseded/pareto-cheatsheet.md` | → original v7.3 ZIP + canonical `pareto-frontier-cheatsheet.md` | It was a byte-identical/superseded duplicate and has no independent working role. |
| `calibration-studio.html` | → `project-config.json` + `calibrate.py` + dashboard calibration selectors | Its durable need was editable calibration policy and inspectable algorithms, not a second application. |
| `config/analysis-policy.json` | → `project-config.json` → `analysis` | Consolidated machine-readable policy. |
| `config/calibration-algorithms.json` | → `project-config.json` → `calibration` | Consolidated machine-readable policy. |
| `config/dashboard-views.json` | → `project-config.json` → `dashboard` | Consolidated machine-readable UI policy. |
| `config/source-acquisition-manifest.json` | → `project-config.json` → `source_acquisition` | Source manifest remains machine-readable. |
| `dashboard.html` | → `dashboard.html` | Retained as the single visualization surface. |
| `data/unified-model-evidence.csv` | → `data/unified-model-evidence.csv` | Retained as the one canonical ledger. |
| `docs/context-restart-meta-prompt.md` | → `user-prompt-aggregation.md` | Expanded into the canonical accumulated-intent/restart artifact. |
| `docs/methodology.md` | → `ardf-research-paper.md` | Methodology became the main body of the overall project paper. |
| `docs/pareto-executor-cheatsheet.md` | → `pareto-frontier-cheatsheet.md` | Retained, renamed, and generated by the single build script. |
| `docs/source-acquisition-cheatsheet.md` | → `ardf-research-paper.md` Appendix A + `project-config.json` | Human playbooks live in the paper; machine source definitions live in config. |
| `generated/analysis-data.js` | → embedded `window.ARDF_ANALYSIS` inside `dashboard.html` | Browser payload is generated state, not a separate user artifact. |
| `generated/analysis-data.json` | → embedded dashboard analysis + generated Markdown decision docs | Same derived information no longer needs a second serialized copy. |
| `generated/calibration-report.json` | → embedded calibration reports in dashboard payload + `calibrate.py` runtime validation | Audit data remains available without another sidecar report. |
| `generated/dashboard-data.js` | → embedded `window.ARDF_DATA` inside `dashboard.html` | Eliminates a generated-file dependency for offline viewing. |
| `generated/unified-evidence-csv.js` | → canonical CSV + embedded calibrated dashboard payload | It existed mainly to bypass local-file browser restrictions for Calibration Studio; that separate app is gone. |
| `reports/build-integrity.md` | → `calibrate.py` validation + this index contract | Build-integrity assertions are executable rather than a stale snapshot. |
| `reports/validation-report.md` | → `calibrate.py` validation | Validation is rerun, not shipped as another dated report. |
| `scripts/augment_cost.py` | → `calibrate.py` `augment_standardized_cost()` | Recurring standardized cost derivation is preserved in the single executable. |
| `scripts/build-analysis.py` | → `calibrate.py` analysis section | Pareto/tier/near-frontier/executor calculations are preserved. |
| `scripts/build-package.py` | → `calibrate.py` `main()` | A second orchestrator is unnecessary when there is only one executable. |
| `scripts/calibrate.py` | → `calibrate.py` | Core robust calibration engine retained. |
| `scripts/migrations/refresh-current-sources-2026-08-08.py` | → canonical ledger + `ardf-research-paper.md` refresh record + source manifest | It was a dated one-time migration. Its results and provenance survive; replay code does not belong in the current build. |
| `scripts/migrations/update-2026-08-08.py` | → canonical ledger + `ardf-research-paper.md` forensic refresh record | Same: one-time correction results are materialized and documented. |
| `scripts/rebuild.py` | → `calibrate.py` | The compatibility wrapper existed only because build logic was fragmented. |
| `scripts/refresh-source-manifest.py` | → `project-config.json` + research-paper source appendix | Manifest/source documentation now share one authoritative configuration and one human document. |
| `scripts/render-pareto-cheatsheet.py` | → `calibrate.py` renderer | No separate renderer needed. |
| `scripts/render-source-cheatsheet.py` | → `ardf-research-paper.md` source appendix | Source documentation is no longer a separately generated product. |
| `scripts/sync_models_dev.py` | → optional `calibrate.py --sync-models-dev` phase + source protocol in `project-config.json` / `ardf-research-paper.md` | The live/offline models.dev metadata synchronizer is preserved, but it no longer deserves a standalone source-specific script. Network acquisition remains opt-in and precedes deterministic calibration. |
| `scripts/validate-source-methodology.py` | → `calibrate.py` structural validation + paper/config authority split | Its invariant is enforced by the consolidated architecture. |
| `scripts/validate_package.py` | → `calibrate.py` `validate_package()` | Validation logic is consolidated. |
| `source-methodology.html` | → `ardf-research-paper.md` + `dashboard.html` source inspection | A second rendered copy of the source manual was presentation duplication. |
| `sources/source-ledger.json` | → `project-config.json` → `source_ledger` | Source registry remains machine-readable. |
| `views/dashboard-claude-code.html` | → filters in `dashboard.html` | It was ~90% duplicate markup. Provider/harness/search filters reproduce the scoped view without a second app. |
| `views/pareto-cheatsheet.html` | → `pareto-frontier-cheatsheet.md` + decision panels in `dashboard.html` | The HTML copy duplicated the same decision content. |

## Deliberately not separate files

The following are **not** allowed to reappear as independent working artifacts unless a future requirement demonstrates a real responsibility boundary: generated JS/JSON payloads, rendered copies of Markdown documents, dated validation reports, one-source synchronization scripts, one-off migrations, duplicate scoped dashboards, duplicate config files, duplicate source ledgers, or an internal archive directory.

If a future artifact is proposed, first answer: **what independent responsibility does it have that cannot cleanly live in one of the nine current files?** If that answer is weak, consolidate instead of proliferating files.
