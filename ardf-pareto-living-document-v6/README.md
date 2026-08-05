<!--
---
title: ARDF Pareto Living Document
version: 6.0.0
created: 2026-07-28
model: GPT-5.6 Thinking
reasoning_level: high
status: validated-build-candidate
---
-->

# ARDF Pareto Living Document v6

ARDF v6 is a portable, offline-first evidence system for comparing model and reasoning-level configurations on one calibrated capability-versus-task-price plane.

The package fixes the central failure of v5: the old dashboard performed an implicit capability/cost inner join and then foregrounded the Pareto subset. Most cataloged configurations disappeared before the graph was drawn. Version 6 instead preserves the complete model universe, expands defensible task-price coverage before calibration, and renders incomplete configurations on explicit evidence shelves rather than deleting them.

## Open these first

- `dashboard.html`: the all-model wall map. Its default view names every model/reasoning configuration.
- `dashboard-claude-code.html`: the same machinery limited to Anthropic and Claude Code configurations.
- `calibration-studio.html`: multipoint-anchor editor, algorithm workbench, standardized-task estimator, and CSV/config exporter.
- `data/unified-model-evidence.csv`: the only CSV and canonical evidence ledger.

## What the main graph now displays

Under the default robust-affine calibration and all-source selection:

- **669** cataloged model/reasoning configurations are represented on the canvas.
- **391** configurations have both a calibrated capability coordinate and calibrated task-price coordinate, so they appear as ordinary scatter points.
- **238** capability-bearing configurations lack a defensible task-price coordinate and appear in the labeled **Unpriced Configurations** shelf.
- **40** cataloged configurations lack selected capability evidence and appear in the **Unscored Configurations** shelf.
- **20** paired configurations form the default empirical Pareto frontier.
- **974** raw capability observations can be exposed through **Capability Evidence Cloud** mode.

“All” therefore means the complete catalog after filters, not merely rows surviving a hidden inner join.

## Required graph controls

The all-model and Claude Code dashboards provide:

- One-dot-per-configuration and capability-evidence-cloud modes
- Every model name visible by default
- Compact or full labels
- Rich hover and click-to-pin evidence inspection
- Logarithmic or linear task-price scale
- Independent capability-source and cost-source selectors
- Independent calibration-algorithm selectors for each axis
- Provider, reasoning level, harness, lifecycle, open-weight, quality, and completeness filters
- Model release-date and evidence-date filters
- Current, legacy, unknown-date, paired, unpriced, and unscored views
- Provider, effort, lifecycle, or source coloring
- Adjustable 2,000, 2,600, or 3,400-pixel plotting canvas
- Optional empirical Pareto overlay
- Searchable, sortable configuration table and visible-view CSV export

## One canonical CSV

`data/unified-model-evidence.csv` contains catalog metadata, raw source observations, generated transparent task-price observations, provenance, calibration outputs, and diagnostics.

Current row counts:

- **2,540** total rows
- **1,871** atomic observations
- **974** capability observations
- **897** cost observations
- **669** catalog rows
- **398** standardized task token-price estimates
- **284** model-specific AA token-count × token-price proxies

Generated JavaScript files under `generated/` are offline delivery caches rebuilt from the CSV. They are not competing data sources.

## Task-price coverage ladder

The dashboard selects the highest-quality available cost class for each configuration by default:

1. Direct Artificial Analysis task cost
2. Observed benchmark cost per task or successful task
3. Model-specific evaluation token count × blended token price
4. Standardized task token-price estimate based on catalog prices and reasoning-level token multipliers
5. Other calibrated cost evidence

Every value retains its raw provenance and quality status. The two generated proxy classes are labeled as derived or estimated and never masquerade as observed bills.

## Package contents

```text
ardf-pareto-living-document-v6/
├── README.md
├── dashboard.html
├── dashboard-claude-code.html
├── calibration-studio.html
├── data/
│   └── unified-model-evidence.csv
├── config/
│   ├── calibration-algorithms.json
│   └── dashboard-views.json
├── generated/
│   ├── dashboard-data.js
│   ├── unified-evidence-csv.js
│   └── calibration-report.json
├── scripts/
│   ├── augment_cost.py
│   ├── calibrate.py
│   ├── validate.py
│   └── rebuild.py
├── schema/
│   ├── unified-model-evidence.schema.json
│   └── dashboard-view.schema.json
├── docs/
│   ├── methodology.md
│   ├── new-source-notes.md
│   └── validation-report.md
├── sources/
│   ├── attached-source-snapshots.json
│   ├── new-benchmark-snapshots.json
│   └── original non-CSV prompt, transcript, and interface artifacts
└── manifest.json
```

## Rebuild from the canonical source

Python 3.11 or newer is sufficient. The scripts use only the Python standard library.

```bash
cd ardf-pareto-living-document-v6
python scripts/rebuild.py
```

The rebuild sequence is deliberately ordered:

1. `augment_cost.py` removes and regenerates transparent price-derived task-cost observations.
2. `calibrate.py` fills every enabled `cal_*` field and refreshes the offline dashboard payloads.
3. `validate.py` checks the one-CSV contract, exact row counts, source slices, calibration coverage, full-universe graph invariants, JavaScript syntax, schemas, and required files.
4. `rebuild.py` writes the manifest and integrated ZIP.

The augmentation and calibration steps are idempotent. Repeated runs do not multiply generated rows.

## Change the standardized task profile

Use `calibration-studio.html` for interactive experimentation. It exposes:

- Base input and output token counts
- Reasoning-level input multipliers
- Reasoning/output token multipliers
- Automatic and manual calibration anchors
- Robust affine, Huber affine, and monotone-piecewise algorithms
- Per-algorithm parameters and output-column creation
- Recalibration and CSV/config download

For a reproducible package update, replace the downloaded CSV and JSON configuration in `data/` and `config/`, then run `python scripts/rebuild.py`.

## Integrity rules

- Raw source values are never overwritten.
- Missing values remain blank rather than becoming zero.
- Every observation measures exactly one axis: capability or cost.
- Every reasoning/effort configuration has a stable canonical `model_key`.
- Calibration happens outside the display dashboards.
- Different reasoning levels are never silently merged.
- The frontier is recalculated from visible paired points and is never fitted or smoothed.
- Unpriced and unscored configurations stay visible on the same canvas.
- Source filters alter displayed aggregates but never refit calibration mappings in the browser.

See `docs/methodology.md` for equations, assumptions, failure analysis, and edge cases.
