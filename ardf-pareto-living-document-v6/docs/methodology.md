<!--
---
title: ARDF v6 Calibration, Coverage, and Pareto Methodology
version: 6.0.0
created: 2026-07-28
model: GPT-5.6 Thinking
reasoning_level: high
---
-->

# ARDF v6 calibration, coverage, and Pareto methodology

## 1. Why v5 failed

The v5 graph was mathematically valid for the tiny subset it admitted, but operationally useless for model discovery. It collapsed evidence to model-level coordinates only after requiring both axes. That implicit inner join removed most capability-bearing configurations because published task-cost evidence is much sparser than benchmark evidence. The interface then emphasized the Pareto subset, making a ledger containing hundreds of configurations look like a ten-point chart.

Four design errors compounded the failure:

1. **Cost scarcity was treated as model absence.** A missing X coordinate caused the entire configuration to vanish.
2. **Aggregation happened before exploration.** Users could not inspect the underlying capability cloud or source-specific disagreement.
3. **Labels were optimized for a sparse frontier.** They did not communicate the full model universe.
4. **Full-suite and task-level costs were conceptually mixed.** A chart labeled “price per task” needs a task-level reference scale and explicit transformations.

Version 6 corrects all four.

## 2. Architectural rule

The package has exactly one canonical tabular file: `data/unified-model-evidence.csv`. Every observation, source label, raw value, model identity, generated task-price proxy, calibration result, and catalog-only configuration lives there.

The pipeline is intentionally separated:

1. `scripts/augment_cost.py` creates transparent token-price-derived cost observations.
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

The standardized estimate is low-weight fallback evidence, not an observed invoice. It is calibrated to task-level USD through eleven strict overlap anchors in the current build.

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
cataloged configurations     669
paired scatter points        391
unpriced shelf entries       238
unscored shelf entries        40
default Pareto points         20
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
