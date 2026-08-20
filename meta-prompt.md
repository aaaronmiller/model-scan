---
title: ARDF Canonical Meta-Prompt
version: 1.0.0
created: 2026-08-15
supersedes: ardf-pareto-living-document-v7.3/docs/context-restart-meta-prompt.md (historical draft)
companions: ../prompt-intent.md (intent), ../version-lineage-audit.md (lineage)
---

# ARDF Canonical Meta-Prompt

Restart prompt for a fresh agent session working on ARDF. Treat the repo as an
existing code/data project to be revised in place — never a clean-room rewrite.

## Where everything lives

- Canonical: `/home/cheta/code/ardf/ardf/` — dashboard.html (4-tier, LINEAR,
  promoted 2026-08-15 from ardf-ux-linear), calibrate.py, project-config.json,
  data/unified-model-evidence.csv (2839 rows), model-tiers-and-contenders.md,
  pareto-frontier-cheatsheet.md, docs/ (mined lineage + artifacts, see
  docs/README.md), sources/ (source ledger + raw snapshots), meta-prompt.md.
- Intent: `../prompt-intent.md` — master spec ("maintainable, packaged
  research system") + clause-form summary (done / rejected / future /
  undefined) + standing constraints.
- Lineage: `../version-lineage-audit.md` — version tree, uniqueness verdicts,
  extraction log.
- Sessions: `~/LIVING_DOCUMENTS/projects/ardf/` — session-history, project,
  history.

## Non-negotiables (from prompt-intent standing constraints)

1. Rank by capability per real task cost, never raw price. "Cheapest" and
   "best value" are separate outputs.
2. Show ALL data on one page, one dot per model-configuration. No
   model-level means, no hidden inner joins.
3. More data points are always better; from a new source, take everything.
4. Calibration lives outside the HTML (calibrate.py + calibration workbench);
   the dashboard is display-first.
5. Validate claims against authoritative sources; search snippets are not
   evidence.
6. No invented floors/tiers/deltas the user never specified.
7. Muse-1.2 analysis uses the lower shared-data price tier; both tiers
   annotated.

## Current state (2026-08-15)

- 4 real tiers (T1 Frontier-ceiling >=60, T2 Frontier >=56, T3 Executor
  47-56, T4 Utility <47), bottom-4 interchangeable differentiated by
  use-case, not fabricated deltas. 7-tier essay text is gone.
- Dashboard: single canonical ardf/dashboard.html at 127.0.0.1:8789
  (auto-started at WSL boot by ~/bin/ardf-dashboards.sh with a memory guard).
- Pipeline: harness_*.sh -> ingest_sources.py -> normalize_harness_output.py
  -> calibrate.py (Theil-Sen, calibrated_score_vN) -> dashboard embed.
- Open items: near-frontier report promotion (exists in docs/), source count
  toward 12-15, DeepSeek pricing tier reconciliation (see prompt-intent F6 /
  version-lineage-audit), "old model" filter.

## Working rules

- Revise in place; preserve data provenance; never delete user data without
  staging. Duplicates are archived under ardf-archive/staging-for-review.
- Confirm all user requests were analyzed before reporting completion.
- If conflicted evidence: deliberative refinement; state the resolution.
