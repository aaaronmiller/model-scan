<!--
---
title: ARDF v6 Validation Report
version: 6.0.0
created: 2026-07-28
model: GPT-5.6 Thinking
reasoning_level: high
---
-->

# ARDF v6 validation report

**Result:** PASS  
**Checks:** 107  
**Failures:** 0  

## Default full-universe geometry

- Catalog configurations: 669
- Paired scatter points: 391
- Unpriced shelf entries: 238
- Unscored shelf entries: 40
- Empirical Pareto points: 20

| Status | Check | Detail |
|---|---|---|
| PASS | Exactly one CSV in package | data/unified-model-evidence.csv |
| PASS | Expected unified record count | 2540 |
| PASS | Expected atomic observation count | 1871 |
| PASS | Expected catalog row count | 669 |
| PASS | Expected capability/cost/catalog distribution | {'capability': 974, 'cost': 897, 'catalog': 669} |
| PASS | Unique stable record IDs | 2540/2540 |
| PASS | Unique catalog model/configuration keys | 669/669 |
| PASS | Observation rows contain one valid sourced axis value | invalid=0 |
| PASS | Catalog rows remain metadata-only | invalid=0 |
| PASS | Complete source slice: livebench-2026-06-25 | 45/45 |
| PASS | Complete source slice: vals-index-v1-2-2026-07-23 | 40/40 |
| PASS | Complete source slice: vals-terminal-bench-2-1-2026-07-22 | 45/45 |
| PASS | Complete source slice: vals-vibe-code-v1-1-2026-07-23 | 76/76 |
| PASS | Complete source slice: vals-swe-bench-2026-07-22 | 75/75 |
| PASS | Complete source slice: aa-token-price-proxy-v6 | 284/284 |
| PASS | Complete source slice: standard-task-price-proxy-v6 | 398/398 |
| PASS | Calibration field exists: cal_robust_affine |  |
| PASS | Calibration field populated: cal_robust_affine | 1771 |
| PASS | Calibration field exists: cal_huber_affine |  |
| PASS | Calibration field populated: cal_huber_affine | 1771 |
| PASS | Calibration field exists: cal_monotone_piecewise |  |
| PASS | Calibration field populated: cal_monotone_piecewise | 1771 |
| PASS | Calibration field exists: calibrated_score |  |
| PASS | Calibration field populated: calibrated_score | 1771 |
| PASS | Task-level USD is the configured cost reference | {'metric_name': 'aa_cost_per_task_usd', 'unit': 'USD per standardized task (AA-equivalent)', 'higher_is_better': False, 'transform': 'log10', 'comment': 'Every cost source is calibrated to task-level USD. Full-suite and source-specific costs remain raw evidence and are bridged through exact model overlaps.'} |
| PASS | At least three configurable algorithms | 3 |
| PASS | Standardized task-price estimator is configured |  |
| PASS | Model-specific token-count × price proxy is configured |  |
| PASS | Calibration reports have explicit status | 75 |
| PASS | Multipoint anchors for livebench-2026-06-25 | [32] |
| PASS | Multipoint anchors for vals-index-v1-2-2026-07-23 | [29] |
| PASS | Multipoint anchors for vals-terminal-bench-2-1-2026-07-22 | [30] |
| PASS | Multipoint anchors for vals-vibe-code-v1-1-2026-07-23 | [41] |
| PASS | Multipoint anchors for vals-swe-bench-2026-07-22 | [42] |
| PASS | Strict anchors for generated cost source: aa-token-price-proxy-v6 | [7] |
| PASS | Strict anchors for generated cost source: standard-task-price-proxy-v6 | [11] |
| PASS | Thin frontier target capability coverage: claude-fable-5-max | capability=9, cost=8 |
| PASS | Thin frontier target cost coverage: claude-fable-5-max | capability=9, cost=8 |
| PASS | Thin frontier target capability coverage: claude-opus-5-max | capability=6, cost=3 |
| PASS | Thin frontier target cost coverage: claude-opus-5-max | capability=6, cost=3 |
| PASS | Thin frontier target capability coverage: gpt-5-6-sol-max | capability=6, cost=2 |
| PASS | Thin frontier target cost coverage: gpt-5-6-sol-max | capability=6, cost=2 |
| PASS | Thin frontier target capability coverage: kimi-k3-max | capability=6, cost=2 |
| PASS | Thin frontier target cost coverage: kimi-k3-max | capability=6, cost=2 |
| PASS | Default full-universe geometry: catalog | 669/669 |
| PASS | Default full-universe geometry: paired | 391/391 |
| PASS | Default full-universe geometry: unpriced | 238/238 |
| PASS | Default full-universe geometry: unscored | 40/40 |
| PASS | Default full-universe geometry: frontier | 20/20 |
| PASS | Every catalog configuration is represented by graph or shelf | {'catalog': 669, 'paired': 391, 'unpriced': 238, 'unscored': 40, 'frontier': 20} |
| PASS | HTML exists: dashboard.html |  |
| PASS | Offline dependency check: dashboard.html |  |
| PASS | Linked generated asset exists: dashboard.html → generated/dashboard-data.js |  |
| PASS | JavaScript syntax: dashboard.html script 1 |  |
| PASS | Dashboard feature: labels visible by default (dashboard.html) |  |
| PASS | Dashboard feature: atomic evidence-cloud mode (dashboard.html) |  |
| PASS | Dashboard feature: unpriced shelf (dashboard.html) |  |
| PASS | Dashboard feature: unscored shelf (dashboard.html) |  |
| PASS | Dashboard feature: logarithmic X-axis control (dashboard.html) |  |
| PASS | Dashboard feature: linear X-axis control (dashboard.html) |  |
| PASS | Dashboard feature: release-date filter (dashboard.html) |  |
| PASS | Dashboard feature: evidence-date filter (dashboard.html) |  |
| PASS | Dashboard feature: independent capability-source filters (dashboard.html) |  |
| PASS | Dashboard feature: independent cost-source filters (dashboard.html) |  |
| PASS | Dashboard feature: calibration-studio popout link (dashboard.html) |  |
| PASS | Dashboard feature: wall-map canvas default (dashboard.html) |  |
| PASS | HTML exists: dashboard-claude-code.html |  |
| PASS | Offline dependency check: dashboard-claude-code.html |  |
| PASS | Linked generated asset exists: dashboard-claude-code.html → generated/dashboard-data.js |  |
| PASS | JavaScript syntax: dashboard-claude-code.html script 1 |  |
| PASS | Dashboard feature: labels visible by default (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: atomic evidence-cloud mode (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: unpriced shelf (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: unscored shelf (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: logarithmic X-axis control (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: linear X-axis control (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: release-date filter (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: evidence-date filter (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: independent capability-source filters (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: independent cost-source filters (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: calibration-studio popout link (dashboard-claude-code.html) |  |
| PASS | Dashboard feature: wall-map canvas default (dashboard-claude-code.html) |  |
| PASS | HTML exists: calibration-studio.html |  |
| PASS | Offline dependency check: calibration-studio.html |  |
| PASS | Linked generated asset exists: calibration-studio.html → generated/dashboard-data.js |  |
| PASS | Linked generated asset exists: calibration-studio.html → generated/unified-evidence-csv.js |  |
| PASS | JavaScript syntax: calibration-studio.html script 1 |  |
| PASS | Calibration Studio feature: editable token-price estimator |  |
| PASS | Calibration Studio feature: browser estimator rebuild |  |
| PASS | Calibration Studio feature: dynamic algorithm creation |  |
| PASS | Calibration Studio feature: anchor editor |  |
| PASS | Valid JSON schema document: schema/unified-model-evidence.schema.json |  |
| PASS | Valid JSON schema document: schema/dashboard-view.schema.json |  |
| PASS | Dashboard contract defines graphs, filters, and tables |  |
| PASS | Required package element: README.md |  |
| PASS | Required package element: docs/methodology.md |  |
| PASS | Required package element: docs/new-source-notes.md |  |
| PASS | Required package element: schema/unified-model-evidence.schema.json |  |
| PASS | Required package element: schema/dashboard-view.schema.json |  |
| PASS | Required package element: scripts/augment_cost.py |  |
| PASS | Required package element: scripts/calibrate.py |  |
| PASS | Required package element: scripts/rebuild.py |  |
| PASS | Required package element: scripts/validate.py |  |
| PASS | Required package element: config/calibration-algorithms.json |  |
| PASS | Required package element: config/dashboard-views.json |  |
| PASS | Required package element: sources/attached-source-snapshots.json |  |
| PASS | Required package element: sources/new-benchmark-snapshots.json |  |
