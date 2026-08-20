<!--
---
title: ARDF v7 Calibration, Coverage, and Pareto Methodology
version: 7.0.0
created: 2026-08-04
model: GPT-5.6 Sol
reasoning_level: high
---
-->

# ARDF v7 calibration, coverage, and Pareto methodology

## 1. Why v5 failed

The v5 graph was mathematically valid for the tiny subset it admitted, but operationally useless for model discovery. It collapsed evidence to model-level coordinates only after requiring both axes. That implicit inner join removed most capability-bearing configurations because published task-cost evidence is much sparser than benchmark evidence. The interface then emphasized the Pareto subset, making a ledger containing hundreds of configurations look like a ten-point chart.

Four design errors compounded the failure:

1. **Cost scarcity was treated as model absence.** A missing X coordinate caused the entire configuration to vanish.
2. **Aggregation happened before exploration.** Users could not inspect the underlying capability cloud or source-specific disagreement.
3. **Labels were optimized for a sparse frontier.** They did not communicate the full model universe.
4. **Full-suite and task-level costs were conceptually mixed.** A chart labeled “price per task” needs a task-level reference scale and explicit transformations.

Version 7 preserves those corrections and adds a current models.dev metadata backbone, current-model source refresh, dual-axis scale controls, and a newest-model coverage audit.

## 2. Architectural rule

The package has exactly one canonical tabular file: `data/unified-model-evidence.csv`. Every observation, source label, raw value, model identity, generated task-price proxy, calibration result, and catalog-only configuration lives there.

The pipeline is intentionally separated:

1. `scripts/update_v7.py` refreshes current identities, source slices, models.dev-compatible metadata, and transparent token-price-derived cost observations.
2. `scripts/calibrate.py` owns all scale-fitting mathematics and writes calibrated columns.
3. `calibration-studio.html` exposes the estimator, anchors, and algorithms for experimentation and export.
4. `dashboard.html` and `dashboard-claude-code.html` consume precomputed calibrated columns, apply filters, aggregate selected evidence, and derive the visible empirical frontier.

The dashboards never estimate calibration coefficients.

## 3. Atomic evidence model

Each observation row measures one axis only:

- `metric_axis = capability`: benchmark score, intelligence index, success rate, completion rate, or composite capability score.
- `metric_axis = cost`: task cost, cost per success, token-price burden, or another monetary observation.

Catalog rows use `record_type = catalog` and `metric_axis = catalog`. They represent a model/reasoning configuration even when it lacks numerical evidence.

This separation allows three honest display states:

- **Paired:** capability and task-price coordinates are available.
- **Unpriced:** capability exists, but no defensible task-price coordinate exists.
- **Unscored:** the configuration is cataloged but has no selected calibrated capability evidence.

No state is silently discarded.

## 4. Reference scales

The default common axes are:

- **Y:** Artificial Analysis Intelligence Index equivalent, interpreted as a calibrated completion/capability index rather than literal human IQ.
- **X:** U.S. dollars per standardized task, calibrated to the attached Artificial Analysis task-cost reference.

Direct reference observations use the identity mapping. Other source groups are mapped using exact overlapping `model_key` configurations. Effort variants are not silently merged.

## 5. Expanding task-price coverage

### 5.1 Direct and observed task costs

Published cost per task and cost per successful task are the preferred evidence. The raw value remains in its original source scale and is calibrated through overlapping configurations when it is not already the reference metric.

### 5.2 Model-specific token-count × price proxy

When Artificial Analysis provides both a model-specific evaluation token total and a blended per-token price, the raw proxy is:

```text
raw_token_price_proxy = evaluation_tokens / 1,000,000 × blended_price_per_million
```

This is still a full-evaluation token burden, not directly a task bill. Therefore it is fitted in log space to exact overlapping task-cost records. In the current package this group has seven strict anchors.

### 5.3 Standardized task token-price estimate

When a configuration has catalog input and output prices but lacks model-specific task usage, a configurable standardized task profile supplies a fallback raw coordinate:

```text
estimated_input_tokens(effort) = base_input_tokens × input_multiplier(effort)
estimated_output_tokens(effort) = base_output_tokens × output_multiplier(effort)

raw_standard_task_price =
    estimated_input_tokens / 1,000,000 × input_price_per_million
  + estimated_output_tokens / 1,000,000 × output_price_per_million
```

The output multiplier represents response and reasoning-equivalent token burden. It is intentionally larger for high, xhigh, and max configurations. These constants are editable in `config/calibration-algorithms.json` and the Calibration Studio.

The standardized estimate is low-weight fallback evidence, not an observed invoice. It is calibrated to task-level USD through strict exact-model overlaps in the current build; the generated calibration report is authoritative for the current anchor count.

### 5.4 No invented price

If neither direct costs nor token pricing support a configuration, it remains in the unpriced shelf. The package does not assign a decorative X coordinate.

## 6. Multipoint calibration

For every `metric_axis × source_id × metric_name` group, the engine:

1. Collapses repeated source measurements for the same `model_key` with a weighted median.
2. Finds exact model/configuration overlaps with the configured reference metric.
3. Uses every exact overlap as an automatic calibration anchor.
4. Adds explicit manual anchors from `config/calibration-algorithms.json`.
5. Fits every enabled algorithm independently.
6. Stores each prediction, status, anchor count, RMSE, and group key in dedicated CSV columns.

This permits incomplete source overlap. A model does not need to appear in every dataset. The calibration graph becomes a mesh of source-to-reference bridges rather than a single pinned model.

## 7. Calibration algorithms

### 7.1 Robust affine, Theil-Sen

For anchor pairs `(xᵢ, yᵢ)`:

```text
slope = median((yⱼ - yᵢ) / (xⱼ - xᵢ))
intercept = weighted_median(yᵢ - slope × xᵢ)
prediction = slope × x + intercept
```

This is the default because it resists a minority of anomalous anchor models.

### 7.2 Huber affine IRLS

Huber calibration repeatedly down-weights large standardized residuals:

```text
huber_weight(z) = 1             when |z| ≤ delta
                  delta / |z|   otherwise
```

It can be more efficient than Theil-Sen when most anchors are clean.

### 7.3 Monotone piecewise linear

This method:

1. Collapses duplicate source values.
2. Applies weighted pool-adjacent-violators regression.
3. Enforces a non-decreasing source-to-reference relationship.
4. Interpolates between calibrated knots.
5. Caps edge extrapolation.

It is useful when a benchmark compresses or stretches portions of its scale.

### 7.4 Logarithmic cost fitting

Cost relationships are multiplicative, so all cost calibration occurs in base-10 logarithmic space:

```text
x′ = log10(source_cost)
y′ = log10(reference_task_cost)
```

Predictions return to dollars with `10ʸ′`. This makes proportional error meaningful and prevents expensive outliers from dominating an ordinary affine fit.

## 8. Dynamic calibration fields

Each enabled algorithm creates:

```text
cal_<algorithm>
cal_<algorithm>_status
cal_<algorithm>_anchor_count
cal_<algorithm>_rmse
cal_<algorithm>_group_key
```

The active algorithm for each axis is copied into:

```text
calibrated_score
calibrated_score_unit
calibrated_score_algorithm
```

Adding another algorithm therefore adds another independent field family. It does not overwrite previous methods.

## 9. Display aggregation

### 9.1 Configuration mode

Configuration mode produces one aggregate dot for each canonical `model_key` that has both coordinates.

Selected capability observations use a source-weighted arithmetic mean:

```text
capability(model) = Σ(weightᵢ × calibrated_capabilityᵢ) / Σ(weightᵢ)
```

The default cost selector first chooses the highest available evidence class. Multiple selected costs within that class use a weighted geometric mean:

```text
cost(model) = exp(Σ(weightᵢ × ln(calibrated_costᵢ)) / Σ(weightᵢ))
```

Alternative controls allow all-source geometric mean, median, or minimum cost.

### 9.2 Capability evidence cloud

Evidence-cloud mode plots each selected calibrated capability observation separately against the configuration’s selected task-price coordinate. It exposes cross-source variation that configuration aggregation otherwise compresses.

### 9.3 Full-universe shelves

The same SVG reserves:

- A right-side capability-ranked shelf for unpriced configurations
- A lower grid for unscored catalog configurations

The shelves are not fake numerical coordinates and never enter Pareto calculation.

## 10. Labels and dense rendering

The default 3,400-pixel wall-map canvas prints every configuration name. Paired-point labels use collision-aware offsets. Shelf entries use deterministic capability sorting and grid placement. Hovering reveals full model identity, release date, lifecycle, reasoning level, harness, aggregate values, cost provenance, frontier status, and every selected observation with its raw and calibrated values.

Users can switch to compact names, full names, current-only names, frontier-only names, hover-only labels, or no labels.

## 11. Lifecycle and date logic

The dashboard supports separate temporal filters:

- **Release date:** filters model/configuration release metadata.
- **Evidence date:** filters source-observation dates.
- **Lifecycle:** current, legacy, or unknown.

The current default heuristic marks explicitly current configurations as current. Otherwise, configurations released on or after January 28, 2025 are treated as current for exploratory filtering. This is a UI heuristic, not a claim of vendor support status, and is visible in the code for later revision.

## 12. Empirical Pareto frontier

Among visible paired points, lower task price and higher capability are preferred. Configuration `A` dominates `B` when:

```text
cost(A) ≤ cost(B)
capability(A) ≥ capability(B)
```

with at least one strict inequality.

The implementation sorts visible points from cheapest to most expensive and retains a point only when its capability is strictly greater than every cheaper retained point. The line is unsmoothed and recalculated after every filter or algorithm change.

Unpriced and unscored shelf entries never enter the frontier because they do not possess both numeric coordinates.

## 13. Default build geometry

With all sources enabled, robust-affine calibration, one-dot-per-configuration mode, and best-available cost evidence:

```text
cataloged configurations     676
paired scatter points        395
unpriced shelf entries       232
unscored shelf entries        49
default Pareto points         19
```

These counts are asserted by `scripts/validate.py`. A future edit that silently collapses the universe back to a tiny subset fails validation.

## 14. Browser and Python responsibilities

The Python engine is authoritative because it can atomically rewrite the canonical CSV and regenerate offline payloads. Browser security prevents a local HTML file from silently overwriting neighboring files. The Calibration Studio therefore exports revised CSV and JSON files for deliberate replacement.

The dashboards perform display-time selection, aggregation, and frontier calculation. They do not generate raw proxies or fit source mappings.

## 15. Limitations

- A calibrated equivalent is not the original benchmark score. Raw and calibrated values are both retained.
- Standardized token profiles are assumptions. Their estimates are labeled, adjustable, and down-weighted.
- Benchmark datasets sharing tasks, harnesses, or evaluation infrastructure are correlated.
- General capability is not task-specific routing truth. Production telemetry should create task-class-specific views.
- Provider-default labels may conceal proprietary effort settings.
- Release-date lifecycle heuristics can become stale and should be revised by future maintenance agents.
- Dense labels intentionally favor completeness over elegance. The interface provides canvas-size and label controls for narrower analyses.


## 14. models.dev metadata layer

Static specifications and benchmark evidence are intentionally distinct. The 50 flattened `models_dev_*` fields describe identity, capabilities, limits, modalities, prices, provider availability, model weights, parameters, links, and synchronization provenance. They are copied to both catalog and observation rows so a single CSV row is sufficient for hover inspection.

`models_dev_match_status` is mandatory in the v7 catalog:

- `exact-current-snapshot`: a curated exact record from the current models.dev catalog.
- `exact-live-api`: a record filled by `scripts/sync_models_dev.py`.
- `compatible-local-fallback`: existing ARDF catalog metadata normalized to the models.dev field schema.

Fallback metadata is never promoted to exact by inference. The live sync script matches IDs before names, requires lab/provider compatibility for normalized fallback matching, and refuses ambiguous matches. It updates only static fields.

## 15. Current source consolidation

Multiple Artificial Analysis snapshots are not treated as independent votes. They are deduplicated by exact `model_key × metric_axis × metric_name`, assigned the single current source ID `artificial-analysis-current`, and retain their original source ID in `source_original_id`.

Every observation also carries:

- `source_refresh_status`
- `source_original_id`
- `data_freshness_class`
- `is_vendor_reported`
- `is_independent_source`
- `benchmark_domain` and `benchmark_harness`
- exact benchmark/version and calibration-group fields

This enables source/date filtering without allowing a month-old and current snapshot of the same source to double-vote.

## 16. Calibration groups across publishers

A source ID remains provenance-specific. A `calibration_group` may nevertheless join rows that implement the same benchmark/version scale, such as Terminal-Bench 2.1 percentages published by different tables. Automatic anchors are then gathered across that common scale while each raw row keeps its original publisher and URL.

This mechanism must not be used merely because two metrics have similar names. Benchmark version, harness, scoring direction, and unit must be semantically identical.

## 17. Dual-axis transformations

X and Y scale toggles affect display only. Calibration still occurs in the mathematically appropriate space:

- Cost mapping is fitted in `log10` space.
- Capability mapping is fitted in its native score space.
- The X-axis can be rendered linearly or logarithmically.
- The Y-axis can be rendered linearly or logarithmically after clipping nonpositive values from the log view.

Changing display scale never changes aggregate coordinates or frontier membership.

## 18. Newest-model coverage audit

The dashboard groups exact release-dated models.dev records by canonical model ID and displays the newest families above the main graph. The card records configuration count, raw observation count, distinct source count, context limit, and provider count.

Coverage is measured using atomic source/metric rows, not generated calibration columns. Public benchmark tables often publish only one reasoning level. ARDF therefore reports coverage per exact configuration and never copies a max/xhigh score into low or medium rows.

The detailed machine-readable audit is `generated/latest-model-coverage.json`.

## 19. Known limits

1. The bundled exact models.dev snapshot prioritizes the current/new frontier cohort. Older rows carry explicit schema-compatible fallbacks until the live synchronizer is run with network access.
2. Vendor scorecards are not independent verification. They remain visible and lower-weight.
3. A large number of raw observations does not imply broad source independence; the hover panel and coverage JSON expose both row count and distinct source count.
4. Some current model effort variants have only token-price estimates because no public effort-specific benchmark result exists. They stay unscored instead of receiving interpolated capability.
5. Attached benchmark snapshots without a current structured export remain labeled retained snapshots.

## v7.3 capability tiers, identity hygiene, external-frontier validation, and routing value

V7.3 keeps calibration, routing interpretation, and display as separate layers. `scripts/calibrate.py` fills calibrated score columns. `scripts/build-analysis.py` consumes those columns and produces Pareto/tier/near-frontier/executor/top-end diagnostics. `dashboard.html` renders precomputed analysis but does not fit calibration models.

### Capability tiers

Operational tiers remain policy labels over the multi-source calibrated capability coordinate:

```text
S+ >= 60
S  >= 56
A+ >= 52
A  >= 47
B  >= 40
C  >= 30
D  >= 0
```

They are convenient routing bands, not a claim that capability is naturally discontinuous.

### Strict Pareto frontier

A configuration is Pareto-optimal when no visible/configured competitor is both cheaper and at least as capable, with one strict inequality. The algorithm sorts by ascending task cost and retains only configurations that set a new maximum capability. Pareto membership is a **dominance relation**, not a price/performance ranking.

### Price/performance and executor eligibility

The scalar price/performance diagnostic requested by the user is literal:

```text
price_per_capability = calibrated_task_cost / calibrated_capability
capability_per_dollar = calibrated_capability / calibrated_task_cost
```

Lower `$ / capability` is better. The executor shortlist applies a minimum multi-source capability threshold of 45 so a nearly-free toy model does not win a general-purpose executor role simply through a tiny denominator. No square-root price transform, capability subtraction, or hand-inserted candidate is used.

Exact current Artificial Analysis Intelligence Index is displayed as a **secondary same-source diagnostic**. It is especially useful for comparing reasoning levels because it avoids a data-density artifact where max effort appears stronger only because more third-party sources happened to publish max-effort rows.

### Near-frontier regret

For a non-frontier candidate, the analysis finds the closest frontier configuration satisfying:

```text
frontier_cost <= candidate_cost
frontier_capability >= candidate_capability
```

It then reports capability gap and price premium. This deliberately preserves models that narrowly miss the strict frontier, because real workload specialization can reverse a small nominal difference.

### Model identity rules: DeepSeek and MiMo

Identity is resolved before calibration.

- **DeepSeek V4 Pro** in the current package is renamed **DeepSeek V4 Pro Preview**. It is the Apr. 24 V4 Preview Pro model (1.6T total / 49B active). DeepSeek later promoted Flash to `DeepSeek-V4-Flash-0731` while stating that Pro was unchanged. As of 2026-08-08, do not invent a separate final V4-Pro identity until DeepSeek announces one.
- **MiMo-V2.5** and **MiMo-V2.5-Pro** are distinct models. The former dated alias `mimo-v2-5-0424` is merged into canonical MiMo-V2.5. Current AA Intelligence Index is 38 for MiMo-V2.5 and 43 for MiMo-V2.5-Pro. MiMo-V2-Pro is an earlier predecessor and remains separate. UltraSpeed/provider variants must also remain separate when their prices/runtime differ.
- A benchmark value is never copied between these identities merely because their names are similar.

### Top-end reasoning-level audit

The expensive frontier cohort is treated as a separate decision surface because routing mistakes there have disproportionate cost. The current focus families are:

- Claude Opus 5
- Claude Fable 5
- GPT-5.6 Sol
- Qwen3.8 Max
- Kimi K3

Two parallel analyses are emitted:

1. **ARDF operational plane:** multi-source calibrated capability vs calibrated task cost.
2. **AA same-source plane:** exact current AA Intelligence Index vs direct AA **Cost per Intelligence Index Task** wherever AA publishes it. AA full-evaluation cost remains a separate diagnostic and is used only as a clearly labeled fallback when direct task cost is unavailable.

Direct task cost is preferred for effort pruning because it is the native X coordinate on AA's public Intelligence-vs-Cost-per-Task Pareto view. Full-evaluation cost and task cost are never blended into one raw coordinate.

A configuration dominated **inside its own family** on exact AA capability/direct-task-cost should normally be removed from default routing unless a specialist benchmark supplies a concrete reason to keep it. Current example: Opus 5 max and xhigh both score 63, while direct AA task cost is $2.34 for max and $1.80 for xhigh, so xhigh strictly dominates max in that same-source plane.

### External Pareto cross-checks

V7.3 preserves independent cost/performance planes as diagnostics rather than blending their raw axes into a single pseudo-benchmark:

- **Artificial Analysis:** Intelligence Index vs Cost per Intelligence Index Task. AA's public model explorer includes an interactive Pareto graph. Direct AA task-cost rows are preserved for an extracted current subset.
- **KiloBench:** coding-agent completion percentage vs cost per attempt. This is a different task/harness and therefore an independent operational check.
- **Vals Index:** Vals accuracy vs Cost/Test. Raw Vals frontier membership is preserved, while Vals observations may also be multipoint-calibrated into ARDF through exact overlaps.

Agreement across these planes increases confidence. Disagreement is useful evidence of task specialization, harness effects, or benchmark semantics and must not be averaged away blindly.

### Muse dual-tier pricing

Muse Spark 1.2 uses Contributor/data-sharing pricing as the project's primary economic route at the user's explicit request. Standard/no-sharing pricing remains secondary evidence. Artificial Analysis measures the Standard route; the Contributor coordinate transparently reprices the same workload. The direct Standard AA task-cost row is excluded from the operational aggregate so the two tiers are not geometrically averaged together.

### Script responsibilities

The project now uses explicit names; the ambiguous legacy `rebuild.py` wrapper has been removed:

- `scripts/augment_cost.py` — creates derived task-cost observations from pricing/workload assumptions.
- `scripts/calibrate.py` — fits source-to-reference calibration mappings and fills calibrated columns/payloads.
- `scripts/build-analysis.py` — computes strict Pareto, tiers, near-frontier, price/performance, top-end, and external-comparison diagnostics.
- `scripts/build-package.py` — orchestrates the complete deterministic downstream build and validation sequence.

Network acquisition is intentionally not hidden inside `build-package.py`. Future agents should update a dated source adapter/raw snapshot first, then run the deterministic build.
