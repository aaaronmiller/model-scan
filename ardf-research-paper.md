# ARDF: A Reproducible Evidence-Calibration and Pareto Framework for Model Selection

## Abstract

ARDF is a living evidence framework for comparing AI model configurations across heterogeneous benchmarks, task-cost measurements, provider pricing, reasoning levels, and access regimes without collapsing provenance or pretending incompatible metrics are directly commensurate. The project maintains atomic observations in one canonical ledger, calibrates capability and cost onto reference axes using overlap-based robust mappings, keeps uncertainty and calibration coverage visible, and separates three questions that are often conflated: absolute capability tiers, strict Pareto efficiency, and scalar price/performance for a specified executor role. This consolidated edition also defines the source-acquisition process, model-identity rules, reproducible build contract, external-frontier cross-checks, and failure modes discovered during earlier iterations.

## 1. Research question and intended utility

The practical question is not merely “which model scores highest?” It is: **given current evidence, pricing, access mode, reasoning configuration, and task constraints, which configurations are economically non-dominated, which are capability peers, and which apparent winners are artifacts of source mismatch or identity mistakes?** ARDF is designed to make that answer inspectable rather than magical.

The canonical working package deliberately contains only nine files. This paper absorbs what used to be separate methodology, source-acquisition manual, release notes, README guidance, and architectural rationale so those responsibilities do not fragment again.

<!--
---
title: ARDF v7 Calibration, Coverage, and Pareto Methodology
version: 7.0.0
created: 2026-08-04
model: GPT-5.6 Sol
reasoning_level: high
---
-->

## ARDF v7 calibration, coverage, and Pareto methodology

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

The working architecture is intentionally compact:

1. Acquisition updates atomic evidence and catalog metadata in `data/unified-model-evidence.csv` under the source rules in `project-config.json` and Appendix A.
2. `calibrate.py` regenerates the standardized task-cost fallback, fits all configured calibration mappings, writes calibrated columns, derives Pareto/tier/executor analyses, regenerates the decision documents, embeds browser payloads into `dashboard.html`, and validates the nine-file package.
3. `project-config.json` owns calibration algorithms, anchors, weights, analysis thresholds, dashboard policy, and source-acquisition/source-ledger metadata.
4. `dashboard.html` consumes only precomputed calibrated observations and derived analysis. It may filter, aggregate, and redraw a visible frontier, but it never fits calibration coefficients.

### 2.1 Single executable, no orchestration stack

The former multi-script pipeline was useful while responsibilities were still being discovered, but it became unnecessary once those responsibilities stabilized. The consolidated package has one executable, `calibrate.py`. One-time migrations are not replayed by the current build because their corrected results are already materialized in the canonical ledger and documented in the forensic history. The original v7.3 ZIP remains the archival record of those transformations.

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

The output multiplier represents response and reasoning-equivalent token burden. It is intentionally larger for high, xhigh, and max configurations. These constants are editable in `project-config.json` and the Calibration Studio.

The standardized estimate is low-weight fallback evidence, not an observed invoice. It is calibrated to task-level USD through strict exact-model overlaps in the current build; the generated calibration report is authoritative for the current anchor count.

### 5.4 No invented price

If neither direct costs nor token pricing support a configuration, it remains in the unpriced shelf. The package does not assign a decorative X coordinate.

## 6. Multipoint calibration

For every `metric_axis × source_id × metric_name` group, the engine:

1. Collapses repeated source measurements for the same `model_key` with a weighted median.
2. Finds exact model/configuration overlaps with the configured reference metric.
3. Uses every exact overlap as an automatic calibration anchor.
4. Adds explicit manual anchors from `project-config.json`.
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

The current consolidated build validates the following structural counts:

```text
cataloged configurations      683
atomic observations          2115
total canonical rows         2798
current paired configs        252
strict Pareto points           16
near-frontier configs          65
```

These counts are checked by `calibrate.py`. A future edit that silently collapses the universe back to a tiny subset fails validation.

## 14. Browser and Python responsibilities

The Python engine is authoritative because it can atomically rewrite the canonical CSV and regenerate all derived state. Browser security prevents a local HTML file from silently overwriting neighboring files, so policy editing occurs in `project-config.json` and recalibration occurs through `calibrate.py`.

The dashboard performs display-time selection, aggregation, and frontier calculation from already-calibrated evidence. It does not generate raw proxies or fit source mappings.

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
- `exact-live-api`: a record filled by the optional `calibrate.py --sync-models-dev` acquisition phase.
- `compatible-local-fallback`: existing ARDF catalog metadata normalized to the models.dev field schema.

Fallback metadata is never promoted to exact by inference. The optional models.dev synchronizer inside `calibrate.py` matches IDs before names, requires lab/provider compatibility for normalized fallback matching, and refuses ambiguous matches. It updates only static fields.

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

The detailed coverage state is retained in the canonical ledger and embedded dashboard payload rather than a separate generated audit file.

## 19. Known limits

1. The bundled exact models.dev snapshot prioritizes the current/new frontier cohort. Older rows carry explicit schema-compatible fallbacks until the live synchronizer is run with network access.
2. Vendor scorecards are not independent verification. They remain visible and lower-weight.
3. A large number of raw observations does not imply broad source independence; the hover panel and coverage JSON expose both row count and distinct source count.
4. Some current model effort variants have only token-price estimates because no public effort-specific benchmark result exists. They stay unscored instead of receiving interpolated capability.
5. Attached benchmark snapshots without a current structured export remain labeled retained snapshots.

## v7.3 capability tiers, identity hygiene, external-frontier validation, and routing value

The consolidated architecture keeps calibration, routing interpretation, and display as separate conceptual layers while housing deterministic computation in one executable. `calibrate.py` fills calibrated score columns and derives Pareto/tier/near-frontier/executor/top-end diagnostics; `dashboard.html` renders the results but does not fit calibration models.

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

`calibrate.py` is the sole deterministic executable. It contains the former recurring cost augmentation, robust calibration, Pareto/tier/near-frontier/executor analysis, document rendering, dashboard payload embedding, optional models.dev synchronization, and validation responsibilities. Diverse benchmark/source acquisition remains a pre-calibration evidence task governed by `project-config.json` and Appendix A rather than being hidden inside the deterministic pass.

This consolidation removes wrappers, render-only scripts, generated sidecars, and replay-only migration scripts from the working tree without removing their durable outputs or methodological rationale.


---

# Appendix A. Source Acquisition and Refresh Manual

<!--
---
title: ARDF Source Acquisition and Supplementation Cheatsheet
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
---
-->

## ARDF source acquisition and supplementation cheatsheet

This is the **v7.3 current-source field manual**. It is generated from `project-config.json` so source IDs, URLs and row counts stay synchronized with the canonical CSV. The source-methodology HTML is a searchable rendering of the same manifest.

> **Acquisition rule:** prefer official API/repository data; save a complete dated raw slice; normalize identities before observations; retain exactly one current vote per source; calibrate only after ingestion; never let a mirror or a copied vendor score vote twice.

## Ten-minute refresh workflow

1. Inspect `project-config.json` and this document.
2. Refresh critical/high sources first, especially models.dev, Artificial Analysis, official pricing, and recently released model pages.
3. Prefer structured API/CSV/JSON/repository results over rendered HTML.
4. Preserve raw native units and source dates.
5. Match exact model + reasoning/effort + harness identities before generating observations.
6. Emit one atomic capability or cost observation per metric; static facts belong in `models_dev_*` metadata.
7. Replace the previous current slice for the same source. Use `source_original_id` to retain historical provenance without extra voting weight.
8. Run `calibrate.py` for the stable one-command deterministic build (`calibrate.py` is the implementation/orchestrator), or run `augment_cost.py`, `calibrate.py`, and `build-analysis.py` individually when debugging one stage.
9. Review calibration anchor counts/residuals and the strict/near-frontier deltas.
10. Run validation and package only after the generated JS payloads exist.

## Current source matrix

| Source ID | Source | Method | Metadata | Capability | Cost | Tokens | Runtime | Rows | Refresh |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `models-dev-current` | models.dev model catalog | API JSON | ✓ | — | ✓ | — | — | 0 | **critical** |
| `artificial-analysis-current` | Artificial Analysis current consolidated language-model data | Authenticated API preferred; HTML only as fallback | ✓ | ✓ | ✓ | ✓ | ✓ | 731 | **critical** |
| `meta-muse-pricing-current` | Meta Muse Spark 1.2 dual pricing | API/structured metadata preferred; HTML fallback | ✓ | — | ✓ | — | — | 6 | **critical** |
| `meta-muse-contributor-repricing-current` | Muse Spark 1.2 Contributor-equivalent AA task cost | local deterministic derivation | — | — | ✓ | ✓ | — | 1 | **critical** |
| `artificial-analysis-muse-1-2-components-2026-08-05` | Artificial Analysis Muse Spark 1.2 launch/component evaluation | API/article structured extraction | — | ✓ | — | — | — | 9 | **medium** |
| `meta-muse-1-2-model-card-current` | Meta Muse Spark 1.2 official benchmark card | official HTML/model-card table | ✓ | ✓ | — | — | — | 2 | **medium** |
| `inclusionai-ling-3-0-tiny-promotional-current` | Ling 3.0 Tiny promotional API pricing | AA API/provider page | ✓ | ✓ | ✓ | ✓ | ✓ | 2 | **high** |
| `openrouter-current-pricing` | OpenRouter current provider pricing | structured API preferred; model-page fallback | ✓ | — | ✓ | — | — | 1 | **high** |
| `aa-token-price-proxy-v7` | AA evaluation-token × blended-price proxy | Local derivation from AA API data | — | — | ✓ | ✓ | — | 284 | **high** |
| `benchlm-current` | BenchLM current benchmark/model pages | HTML extraction or official data download | ✓ | ✓ | ✓ | — | ✓ | 115 | **critical** |
| `openai-gpt-5-6-current` | OpenAI GPT-5.6 current comparative evaluation table | Official HTML table scrape | ✓ | ✓ | ✓ | — | — | 60 | **medium** |
| `official-token-pricing-current` | Official provider token pricing · current consolidated slice | Official docs scrape/API where offered | ✓ | — | ✓ | — | — | 34 | **critical** |
| `vals-index-current-2026-08-06` | Vals Index current accuracy + Cost/Test | structured page/API payload preferred | — | ✓ | ✓ | — | ✓ | 31 | **critical** |
| `kilo-leaderboard-current-2026-08-08` | KiloBench current coding-agent completion + cost/attempt | HTML/structured table extraction | — | ✓ | ✓ | — | — | 20 | **high** |
| `claw-eval-attached` | Claw-Eval attached snapshot | Official HTML leaderboard + repository/HF cross-check | — | ✓ | — | ✓ | — | 22 | **high** |
| `deepseek-v4-flash-0731-model-card-2026-07-31` | DeepSeek V4 Flash 0731 release/model-card table | Official HTML table scrape + official pricing page | ✓ | ✓ | ✓ | — | — | 7 | **medium** |
| `livebench-2026-06-25` | LiveBench release 2026-06-25 | Repository CSV preferred; HTML fallback | — | ✓ | ✓ | — | — | 45 | **medium** |
| `qwen3-8-max-stable-scorecard-2026-08-03` | Qwen3.8 Max stable-release scorecard | Official HTML/model-card table scrape | ✓ | ✓ | ✓ | — | — | 15 | **high** |
| `qwencloud-pricing-2026-08-03` | Alibaba Cloud Qwen3.8 Max pricing | Official documentation table scrape | ✓ | — | ✓ | — | — | 1 | **high** |
| `skatebench-official-attached` | SkateBench official attached table | Repository data extraction preferred; HTML tabs fallback | — | ✓ | ✓ | ✓ | ✓ | 48 | **high** |
| `skatebench-v2-attached` | SkateBench visible v2 attached table | Repository data extraction preferred; HTML tabs fallback | — | ✓ | ✓ | ✓ | ✓ | 30 | **high** |
| `standard-task-price-proxy-v7` | Standardized task token-price estimator | Local deterministic derivation | ✓ | — | ✓ | — | — | 413 | **high** |
| `user-best-cost-attached` | User-supplied best-cost table | Manual import with mandatory provenance manifest | — | — | ✓ | — | — | 47 | **critical** |
| `vals-swe-bench-2026-07-22` | Vals SWE-bench mirror | HTML table extraction; inspect network payload if stable | ✓ | ✓ | — | — | — | 74 | **critical** |
| `vals-terminal-bench-2-1-2026-07-22` | Vals Terminal-Bench 2.1 | HTML table extraction; inspect network payload if stable | ✓ | ✓ | — | — | — | 44 | **critical** |
| `vals-vibe-code-v1-1-2026-07-23` | Vals Vibe Code Bench v1.1 | HTML table extraction; inspect network payload if stable | ✓ | ✓ | — | — | — | 73 | **critical** |

## Canonical post-acquisition schema

Every acquired metric becomes one row in `data/unified-model-evidence.csv`. The canonical grain is:

```text
model_key × effort/reasoning × harness × source_id × metric_name × source_date
```

Core field groups:

- **Identity:** `record_type`, `observation_id`, `model_key`, `display_name`, `provider`, `family`, `effort`, `harness`, `official_model_id`.
- **Source provenance:** `source_id`, `source_original_id`, `source_label`, `source_publisher`, `source_version`, `source_date`, `source_url`, `source_mirror_url`, `retrieved_at`, `source_refresh_status`.
- **Raw evidence:** `metric_axis`, `metric_name`, `raw_value`, `raw_unit`, `raw_direction`, `benchmark_domain`, `benchmark_harness`, `benchmark_version_exact`.
- **Evidence policy:** `quality`, `confidence`, `base_weight`, `use_in_aggregate`, `is_historical`, `is_vendor_reported`, `is_independent_source`, `identity_mapping`, `notes`.
- **Calibration:** `cal_robust_affine*`, `cal_huber_affine*`, `cal_monotone_piecewise*`, `calibrated_score*`, `calibration_group`. Acquisition adapters leave these blank.
- **Static metadata:** all `models_dev_*` columns. They appear in hover/filter UI but are never benchmark votes.

Null is null, never zero-filled. Capability and monetary cost are separate axes. A promotional zero-dollar price may be preserved as raw metadata while being excluded from Pareto aggregation.

## Current source playbooks

### 1. models.dev model catalog (`models-dev-current`)

**Role:** Primary provider-independent metadata backbone. It must never be treated as benchmark evidence.

**Acquisition used:** JSON catalog synchronization through `calibrate.py --sync-models-dev`; `--models-dev-offline-json` accepts an offline snapshot when live download fails.

**Preferred next acquisition:** Use the documented https://models.dev/api.json endpoint. Retain https://models.dev/catalog.json only as a compatibility fallback. For audit-grade provenance, clone the official repository and preserve the provider/model TOML files used for the build.

**Go directly here:**
- [Official JSON API](https://models.dev/api.json)
- [Compatibility catalog JSON](https://models.dev/catalog.json)
- [Official repository and schema](https://github.com/anomalyco/models.dev)
- [Per-model web catalog](https://models.dev/)

**Coverage:** metadata, cost_or_price.

**Available data:** Provider IDs and docs; canonical model IDs; names; release/update dates; lifecycle status; context/input/output limits; input/output/cache/reasoning/audio prices; input/output modalities; attachment, reasoning, tool-call, structured-output and temperature support; open-weight status; knowledge cutoff; provider variants and logos.

**Currently unused / expansion opportunity:** Provider-level npm package, environment-variable names, provider API base URL, provider documentation link, wrapper/base-model relationships, provider logos, and any model/provider fields left inside models_dev_provider_rows_json or the raw API object. The current CSV flattens 50 fields but preserves raw provider rows for later expansion.

**Post-ingestion fields:** `models_dev_* fields on every catalog and observation row`, `model_key`, `official_model_id`, `provider`, `family`, `effort`, `release_date`, `availability`

**Identity keys:** `models_dev_model_id`, `official_model_id`, `normalized model name + lab`, `base model without effort as cautious fallback`

**Caveats:** The current package has only 42 exact live matches and 634 compatibility fallbacks. A refresh agent should run the synchronizer against the current API and review every fuzzy or fallback match before accepting it.

### 2. Artificial Analysis current consolidated language-model data (`artificial-analysis-current`)

**Role:** Primary reference scale for the Y-axis AA Intelligence Index equivalent and the preferred source for exact task/full-suite cost evidence.

**Acquisition used:** Current consolidated slice refreshed through model pages/API-derived structured data; prior dated AA identities are retained only in source_original_id, never as extra votes.

**Preferred next acquisition:** Use the official Artificial Analysis Data API/model pages for structured current records. Cross-check the public Intelligence Index vs Cost per Task Pareto explorer; do not scrape chart pixels when numeric model records are available.

**Go directly here:**
- [AA model explorer + Cost per Task Pareto](https://artificialanalysis.ai/)
- [AA model directory](https://artificialanalysis.ai/models)
- [AA Data API docs](https://artificialanalysis.ai/data-api/docs)

**Coverage:** metadata, capability, cost_or_price, token_usage, latency_or_speed.

**Available data:** Headline and component evaluations, Intelligence Index and version, cost to run the index, cost per task, input/output and blended pricing, median throughput and latency, release/model-creator metadata, context, parameters, modalities, licensing and open-weight links. Detail endpoints add evaluation token counts and openness/omniscience breakdowns.

**Currently unused / expansion opportunity:** AA additionally exposes Cost per Task, Time per Task, Output Tokens per Task, provider speed/latency, token-use breakdowns, and its own Pareto line. Future adapters should ingest structured numeric rows for these views rather than treating the rendered graph as a second vote.

**Post-ingestion fields:** `metric_axis`, `metric_name`, `raw_value`, `raw_unit`, `is_reference_scale`, `source_id`, `source_date`, `retrieved_at`, `quality`, `confidence`, `benchmark_domain`, `benchmark_version_exact`

**Identity keys:** `AA slug`, `AA model ID`, `model creator + model name + reasoning mode`

**Caveats:** Do not mix multiple dated AA snapshots as independent votes. Refresh in place, preserve source_original_id, record the Intelligence Index version, and keep model/reasoning variants distinct.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `aa_intelligence_index` | AA Intelligence Index | 570 |
| cost | `aa_full_suite_cost_usd` | USD full AA suite | 54 |
| cost | `aa_cost_per_task_usd` | USD per Intelligence Index task | 24 |
| metadata | `aa_output_tokens_full_suite` | output tokens | 22 |
| cost | `aa_full_suite_cost_usd` | USD full AA Intelligence Index evaluation | 21 |
| metadata | `aa_output_speed_tokens_s` | tokens/s | 21 |
| cost | `aa_cost_per_task_usd` | USD per AA task | 9 |
| cost | `aa_full_eval_cost_usd` | USD full evaluation | 2 |
| metadata | `aa_index_output_tokens_m` | million output tokens | 2 |
| metadata | `aa_output_speed_tps` | tokens/sec | 2 |
| metadata | `aa_ttft_seconds` | seconds | 2 |
| cost | `input_price_per_m` | USD per 1M tokens | 1 |
| cost | `output_price_per_m` | USD per 1M tokens | 1 |

### 3. Meta Muse Spark 1.2 dual pricing (`meta-muse-pricing-current`)

**Role:** Preserves both Muse price tiers. Contributor/data-sharing is the primary economic tier; Standard/no-sharing is secondary metadata.

**Acquisition used:** Official Meta/models.dev provider rows checked on 2026-08-08.

**Preferred next acquisition:** Fetch models.dev meta/muse-spark-1.2 plus Meta Model API pricing documentation; preserve both SKU IDs and data-use semantics.

**Go directly here:**
- [models.dev Muse Spark 1.2](https://models.dev/models/meta/muse-spark-1.2)
- [Meta Muse Spark model page](https://developer.meta.com/ai/models/muse-spark/)

**Coverage:** metadata, cost_or_price.

**Available data:** Contributor SKU $0.10/M input, $0.002/M cache read, $0.20/M output; Standard SKU $1.25/M input, $0.15/M cache read, $4.25/M output; 1M context, 131k output, tools/reasoning/structured-output flags.

**Currently unused / expansion opportunity:** Future provider-specific throughput/latency and any additional caching/input modality pricing published by Meta.

**Post-ingestion fields:** `input_price_per_m`, `output_price_per_m`, `models_dev_provider_rows_json`, `official_model_id`

**Identity keys:** `meta/muse-spark-1.2`, `muse-spark-1.2-contributor`, `muse-spark-1.2`

**Caveats:** Never average the two price tiers. Contributor is primary only because the user explicitly accepts data sharing.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `contributor_cache_read_price_per_m` | USD per 1M tokens | 1 |
| cost | `contributor_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `contributor_output_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_cache_read_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_output_price_per_m` | USD per 1M tokens | 1 |

### 4. Muse Spark 1.2 Contributor-equivalent AA task cost (`meta-muse-contributor-repricing-current`)

**Role:** Primary Muse task-price coordinate for the user-selected data-sharing tier.

**Acquisition used:** Repriced AA Standard workload to Contributor pricing using the published 7:2:1 cache/input/output mix.

**Preferred next acquisition:** If AA begins measuring Contributor directly, replace this derived row with the direct task cost. Until then preserve the derivation and both base price tiers.

**Go directly here:**
- [AA Muse Spark 1.2](https://artificialanalysis.ai/models/muse-spark-1-2)
- [models.dev Muse pricing](https://models.dev/models/meta/muse-spark-1.2)

**Coverage:** cost_or_price, token_usage.

**Available data:** Contributor-equivalent task cost derived from the same AA workload: approximately $0.02123/task versus AA Standard $0.40/task.

**Currently unused / expansion opportunity:** Exact per-evaluation cache/input/output token breakdown would allow workload-specific repricing instead of blended 7:2:1 repricing.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=aa_cost_per_task_usd`, `quality=derived-repriced-exact-workload`

**Identity keys:** `muse-spark-1-2-xhigh`

**Caveats:** Derived dollar value, not a direct AA billing observation. It is intentionally given direct-task priority because workload evidence is exact and only the published price tier changes.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `aa_cost_per_task_usd` | USD per Intelligence Index task | 1 |

### 5. Artificial Analysis Muse Spark 1.2 launch/component evaluation (`artificial-analysis-muse-1-2-components-2026-08-05`)

**Role:** Adds component evidence around the current AA composite; composite 57 from the current page supersedes the launch article composite.

**Acquisition used:** Artificial Analysis launch/model article table extraction.

**Preferred next acquisition:** Use current AA Data API/model detail for the composite and retain dated article component metrics only when the API does not expose them.

**Go directly here:**
- [AA current Muse page](https://artificialanalysis.ai/models/muse-spark-1-2)
- [AA model directory](https://artificialanalysis.ai/models)

**Coverage:** capability.

**Available data:** GDPval-AA v2, Terminal-Bench, tau3 Banking, SciCode, HLE, CritPt, Omniscience components.

**Currently unused / expansion opportunity:** Provider performance/latency when AA publishes it.

**Post-ingestion fields:** `metric_axis=capability`, `benchmark_domain`, `source_date=2026-08-05`

**Identity keys:** `muse-spark-1-2-xhigh`

**Caveats:** Do not use an older launch-day composite when the current AA index has been revised.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `aa_omniscience_accuracy_pct` | percent | 1 |
| capability | `aa_omniscience_index` | index | 1 |
| capability | `aa_omniscience_non_hallucination_pct` | percent | 1 |
| capability | `critpt_pct` | percent | 1 |
| capability | `gdpval_aa_v2_elo` | Elo | 1 |
| capability | `humanitys_last_exam_pct` | percent | 1 |
| capability | `scicode_pct` | percent | 1 |
| capability | `tau3_banking_pct` | percent | 1 |
| capability | `terminal_bench_2_1_pct` | percent | 1 |

### 6. Meta Muse Spark 1.2 official benchmark card (`meta-muse-1-2-model-card-current`)

**Role:** First-party coding/agent benchmark evidence, retained at lower vendor weight.

**Acquisition used:** Official Meta model-card/launch benchmark table.

**Preferred next acquisition:** Fetch complete current model-card table rather than copying one headline score.

**Go directly here:**
- [Meta Muse Spark model page](https://developer.meta.com/ai/models/muse-spark/)

**Coverage:** metadata, capability.

**Available data:** Terminal-Bench 2.1 and deepSWE results plus model/spec information.

**Currently unused / expansion opportunity:** Any future expanded benchmark table, eval harness notes and ablations.

**Post-ingestion fields:** `is_vendor_reported=1`, `base_weight=0.55`, `metric_axis=capability`

**Identity keys:** `muse-spark-1-2-xhigh`

**Caveats:** If BenchLM mirrors the same Meta score, the mirror must be display-only to prevent duplicate voting.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `deep_swe_pct` | percent | 1 |
| capability | `terminal_bench_2_1_pct` | percent | 1 |

### 7. Ling 3.0 Tiny promotional API pricing (`inclusionai-ling-3-0-tiny-promotional-current`)

**Role:** Records current free API pricing without allowing a temporary $0 denominator to create a degenerate Pareto point.

**Acquisition used:** Artificial Analysis provider/model pages cross-checked against current InclusionAI/Novita availability.

**Preferred next acquisition:** Refresh provider price/latency from current provider pages; set use_in_aggregate=0 while pricing is promotional zero.

**Go directly here:**
- [AA Ling 3.0 Tiny](https://artificialanalysis.ai/models/ling-3-0-tiny)
- [AA Ling providers](https://artificialanalysis.ai/models/ling-3-0-tiny/providers)

**Coverage:** metadata, capability, cost_or_price, token_usage, latency_or_speed.

**Available data:** AA Intelligence Index 25, 262k context, provider output speed/latency, two API providers and current $0 promotional pricing.

**Currently unused / expansion opportunity:** Future non-promotional list price and richer benchmark components.

**Post-ingestion fields:** `metric_axis=cost`, `use_in_aggregate=0`, `data_freshness_class=current`

**Identity keys:** `ling-3-0-tiny-reasoning`

**Caveats:** Zero promotional price is real current availability but excluded from logarithmic/Pareto cost calculations until a durable nonzero price exists.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `promotional_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `promotional_output_price_per_m` | USD per 1M tokens | 1 |

### 8. OpenRouter current provider pricing (`openrouter-current-pricing`)

**Role:** Secondary provider-price evidence for discounted or alternate hosted routes; never silently replaces the project-selected first-party economic tier.

**Acquisition used:** Current OpenRouter model pages/API pricing checked during the August 8 refresh.

**Preferred next acquisition:** Use the OpenRouter models/provider API where available; preserve exact provider/model identity, promotion state and retrieval date.

**Go directly here:**
- [OpenRouter models API](https://openrouter.ai/api/v1/models)
- [OpenRouter Ling 3.0 Flash](https://openrouter.ai/inclusionai/ling-3.0-flash)

**Coverage:** metadata, cost_or_price.

**Available data:** Provider-specific input/output prices, context limits, model IDs and availability; some routes are temporary promotional discounts.

**Currently unused / expansion opportunity:** Provider routing order, throughput/latency and per-provider availability can be added when exposed in structured current endpoints.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name`, `raw_value`, `raw_unit`, `quality=promotional-provider-price when applicable`

**Identity keys:** `provider model id`, `canonical model key`

**Caveats:** Promotional or marketplace rates must be labeled and must not overwrite a user-selected first-party pricing policy without an explicit rule.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `promotional_input_output_price` | USD per 1M input tokens (output $0.063/M) | 1 |

### 9. AA evaluation-token × blended-price proxy (`aa-token-price-proxy-v7`)

**Role:** Extends task-cost coverage where AA exposes model-specific evaluation-token totals and pricing but an exact per-task observation is absent.

**Acquisition used:** Derived locally from structured AA fields already imported into the package.

**Preferred next acquisition:** Fetch evaluation_token_counts and pricing from the AA detail API, calculate the full-suite proxy, and recalibrate it to the reference task-cost scale through exact model/configuration overlaps.

**Go directly here:**
- [AA detail endpoint pattern](https://artificialanalysis.ai/api/v2/language/models/{slug})
- [Derivation methodology](ardf-research-paper.md#52-model-specific-token-count--price-proxy)

**Coverage:** cost_or_price, token_usage.

**Available data:** Full evaluation token totals and blended token price, producing an evaluation-wide USD burden before calibration.

**Currently unused / expansion opportunity:** Separate input/output/cache token counts, per-evaluation token counts, and uncertainty bands could support multiple workload profiles rather than one blended proxy.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=aa_token_price_full_suite_proxy_usd`, `raw_value`, `raw_unit`, `notes=formula`, `cal_* fields`

**Identity keys:** `exact AA model/reasoning configuration`

**Caveats:** This is not an invoice for one task. It is a full-suite burden that only becomes comparable after log-space multipoint calibration.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `aa_token_price_full_suite_proxy_usd` | USD token-price proxy for complete AA evaluation | 284 |

### 10. BenchLM current benchmark/model pages (`benchlm-current`)

**Role:** Adds broad recent benchmark coverage for frontier models and a sourced composite/category lens.

**Acquisition used:** Server-rendered HTML extraction from the main leaderboard, model pages and benchmark pages. The v7 package imported 59 observations for seven frontier configurations.

**Preferred next acquisition:** Use the benchmark directory and individual benchmark/model pages. Prefer BenchLM’s download-data surface when available, and preserve each row’s evidence citation, support/estimate label and review date.

**Go directly here:**
- [Main leaderboard](https://benchlm.ai/)
- [Methodology](https://benchlm.ai/methodology)
- [Benchmark directory](https://benchlm.ai/benchmarks)
- [Model directory](https://benchlm.ai/models)
- [Provider pages](https://benchlm.ai/providers)
- [Download data](https://benchlm.ai/download)

**Coverage:** metadata, capability, cost_or_price, latency_or_speed.

**Available data:** BenchAlign overall/category scores, hundreds of benchmark rows, price/context/runtime columns, open/closed and lifecycle metadata, evidence citations, freshness state, and Supported versus Estimated confidence labels.

**Currently unused / expansion opportunity:** The full 378-model × 381-benchmark evidence directory, provider rollups, evidence-path URLs, uncertainty/support labels, price and speed dashboards, release history, leaderboard history and many non-frontier models. The current package uses only a small frontier slice.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<normalized benchmark slug>`, `raw_value`, `raw_unit`, `benchmark_domain`, `is_independent_source`, `quality`, `confidence`, `source_url`

**Identity keys:** `BenchLM model slug`, `displayed provider + model + reasoning mode`

**Caveats:** BenchAlign is itself a calibrated composite. Keep raw benchmark rows separate from the composite to avoid double counting. Do not ingest BenchLM mirrors of a vendor scorecard and the vendor scorecard as two independent votes.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `terminal_bench_2_1_pct` | percent/score | 6 |
| capability | `benchalign_overall` | percent/score | 5 |
| capability | `agentic_category_score` | percent/score | 4 |
| capability | `coding_category_score` | percent/score | 4 |
| capability | `knowledge_category_score` | percent/score | 3 |
| capability | `multimodal_category_score` | percent/score | 3 |
| capability | `automation_bench_pct` | percent/score | 3 |
| capability | `deep_swe_pct` | percent/score | 3 |
| capability | `bfcl_v4_pct` | percent | 3 |
| capability | `ifbench_pct` | percent | 3 |
| capability | `kind_bench_pct` | percent/score | 2 |
| capability | `humanitys_last_exam_pct` | percent/score | 2 |
| capability | `swe_bench_pro_pct` | percent/score | 2 |
| capability | `browsecomp_pct` | percent | 2 |
| capability | `gpqa_pct` | percent | 2 |
| capability | `hle_pct` | percent | 2 |
| capability | `hmmt_feb_2026_pct` | percent | 2 |
| capability | `imoanswerbench_pct` | percent | 2 |
| capability | `mcp_atlas_pct` | percent | 2 |
| capability | `swe_bench_pro_pct` | percent | 2 |
| capability | `swe_multilingual_pct` | percent | 2 |
| capability | `terminal_bench_2_1_pct` | percent | 2 |
| capability | `agents_last_exam_pct` | percent/score | 2 |
| capability | `gpqa_diamond_pct` | percent/score | 2 |
| capability | `instruction_category_score` | percent/score | 2 |
| capability | `frontier_swe_pct` | percent/score | 2 |
| capability | `mathvision_python_pct` | percent/score | 2 |
| capability | `mls_lite_pct` | percent/score | 2 |
| capability | `pinchbench_pct` | percent | 2 |
| capability | `tau3_bench_pct` | percent | 2 |
| … | 36 additional metric definitions | … | … |

### 11. OpenAI GPT-5.6 current comparative evaluation table (`openai-gpt-5-6-current`)

**Role:** Supplies ten comparison metrics across seven frontier configurations, including OpenAI and competitor models.

**Acquisition used:** Direct extraction of complete comparison tables from the official launch page.

**Preferred next acquisition:** Parse every model row and every benchmark column from the current launch/system-card tables. Store table title and footnote text in notes or a raw snapshot so harness differences survive normalization.

**Go directly here:**
- [GPT-5.6 launch/current benchmark table](https://openai.com/index/gpt-5-6/)
- [July 30 price-performance update](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/)
- [API pricing](https://developers.openai.com/api/docs/pricing)

**Coverage:** metadata, capability, cost_or_price.

**Available data:** AA-style vendor table, agentic, coding, browsing, management, OS and economic-work scores across the GPT-5.6 family and selected competitors.

**Currently unused / expansion opportunity:** System-card safety/evaluation tables, model latency tiers, context/output limits, API feature support, batch/cache pricing and any per-domain or confidence details in footnotes.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<benchmark slug>`, `raw_value`, `raw_unit`, `is_vendor_reported=1`, `benchmark_harness`, `notes=<table footnote>`

**Identity keys:** `exact table row name + effort tier`

**Caveats:** Do not treat vendor comparisons as independent reruns. Competitor values copied into an OpenAI table remain vendor-reported and may use a vendor-selected harness.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `aa_intelligence_index_vendor_table` | percent/score | 7 |
| capability | `agents_last_exam_pct` | percent/score | 7 |
| capability | `gdpval_aa_elo` | Elo | 7 |
| capability | `management_bench_pct` | percent/score | 7 |
| capability | `swe_bench_pro_pct` | percent/score | 7 |
| capability | `terminal_bench_2_1_pct` | percent/score | 7 |
| capability | `aa_coding_agent_index` | percent/score | 6 |
| capability | `deep_swe_pct` | percent/score | 6 |
| capability | `browsecomp_pct` | percent/score | 3 |
| capability | `osworld_2_0_pct` | percent/score | 3 |

### 12. Official provider token pricing · current consolidated slice (`official-token-pricing-current`)

**Role:** Provides direct input/output token prices for seven frontier models.

**Acquisition used:** Manual extraction from official launch, model and API documentation pages.

**Preferred next acquisition:** Refresh from provider pricing/model docs, then compare against models.dev and OpenRouter. Store every price dimension separately rather than collapsing immediately.

**Go directly here:**
- [Anthropic Opus 5 launch/pricing](https://www.anthropic.com/news/claude-opus-5)
- [OpenAI GPT-5.6 launch/pricing](https://openai.com/index/gpt-5-6/)
- [Google Gemini model docs](https://ai.google.dev/gemini-api/docs/latest-model)
- [Kimi K3 quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart)

**Coverage:** metadata, cost_or_price.

**Available data:** Input and output USD per million tokens for the current package’s selected frontier models.

**Currently unused / expansion opportunity:** Cache read/write prices, reasoning-token prices, batch discounts, long-context tiers, regional pricing, image/audio/video pricing, free-tier limits and version-specific retirement dates.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=input_token_price_per_m or output_token_price_per_m`, `raw_value`, `raw_unit`, `use_in_aggregate=0 unless converted into a task profile`

**Identity keys:** `official provider model ID + pricing effective date`

**Caveats:** Token price alone is not cost per task. Keep raw price observations outside the Pareto task-cost axis until combined with a documented token-use profile.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `input_token_price_per_m` | USD per 1M tokens | 7 |
| cost | `output_token_price_per_m` | USD per 1M tokens | 7 |
| cost | `batch_long_cache_write_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_long_cached_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_long_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_long_output_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_short_cache_write_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_short_cached_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_short_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `batch_short_output_price_per_m` | USD per 1M tokens | 1 |
| cost | `cache_read_price_per_m` | USD per 1M tokens | 1 |
| cost | `cache_write_price_per_m` | USD per 1M tokens | 1 |
| cost | `input_price_per_m` | USD per 1M tokens | 1 |
| cost | `output_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_long_cache_write_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_long_cached_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_long_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_long_output_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_short_cache_write_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_short_cached_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_short_input_price_per_m` | USD per 1M tokens | 1 |
| cost | `standard_short_output_price_per_m` | USD per 1M tokens | 1 |

### 13. Vals Index current accuracy + Cost/Test (`vals-index-current-2026-08-06`)

**Role:** Current independent economic-work aggregate used both as calibrated evidence and as a source-native Pareto cross-check.

**Acquisition used:** Current Vals model/benchmark pages checked 2026-08-08; one current slice replaces the Jul. 23 Vals Index aggregate.

**Preferred next acquisition:** Fetch the current Vals Index/model pages or structured page payload. Preserve accuracy and Cost/Test as paired native metrics for each exact model identity.

**Go directly here:**
- [Vals home / current Index](https://www.vals.ai/home)
- [Vals benchmark directory](https://www.vals.ai/benchmarks)

**Coverage:** capability, cost_or_price, latency_or_speed.

**Available data:** Vals Index accuracy, Cost/Test, and per-benchmark/model pages; many benchmark pages also expose latency, category breakdowns and task-difficulty slices.

**Currently unused / expansion opportunity:** Ingest current latency plus additional Vals sub-benchmarks as independent source groups only when they add non-duplicative task evidence.

**Post-ingestion fields:** `metric_axis=capability or cost`, `metric_name=vals_index_accuracy / vals_cost_per_test_usd`, `raw_unit=percent / USD per test`

**Identity keys:** `exact model`, `reasoning/effort where published`

**Caveats:** Vals Cost/Test is a source-native workload cost, not the same unit/workload as AA Cost per Intelligence Index Task. It is calibrated through overlaps for ARDF and also displayed raw in a separate source-native graph.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `vals_index_accuracy_pct` | percent | 16 |
| cost | `vals_index_cost_per_test_usd` | USD per Vals Index test | 15 |

### 14. KiloBench current coding-agent completion + cost/attempt (`kilo-leaderboard-current-2026-08-08`)

**Role:** Source-native coding-agent Pareto cross-check for frontier models; useful because it directly pairs completion rate with real agent cost per attempt.

**Acquisition used:** Current Kilo leaderboard table checked 2026-08-08.

**Preferred next acquisition:** Fetch the complete current leaderboard table, not only top headlines. Preserve completion, cost/attempt, rank, harness/version and retrieval date.

**Go directly here:**
- [Kilo live model leaderboard](https://kilo.ai/leaderboard)
- [KiloBench](https://kilo.ai/kilobench)

**Coverage:** capability, cost_or_price.

**Available data:** Completion rate and cost per attempt across current coding models, with additional model/catalog pages.

**Currently unused / expansion opportunity:** If Kilo exposes run counts, confidence intervals, task classes, token use, latency or failure categories, ingest those fields as diagnostics rather than folding them into completion.

**Post-ingestion fields:** `metric_axis=capability or cost`, `metric_name=kilo_completion_pct / kilo_cost_per_attempt_usd`

**Identity keys:** `exact model family/version`

**Caveats:** Coding-agent workload only. Keep raw source-native Pareto separate from the general AA-equivalent task-cost plane.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `kilo_completion_pct` | percent | 10 |
| cost | `kilo_cost_per_attempt_usd` | USD per attempt | 10 |

### 15. Claw-Eval attached snapshot (`claw-eval-attached`)

**Role:** Adds a Pass^3-style autonomous-agent completion signal and preserves an older attached token-efficiency table.

**Acquisition used:** Manual attached table import. No reproducible fetch adapter is included in v7.

**Preferred next acquisition:** Refresh from the official leaderboard at claw-eval.github.io and cross-check against the official GitHub repository. For task data use the Hugging Face dataset; for token-efficiency claims inspect the separate AIgenteur/ClawEval repository and do not merge it with official Claw-Eval without explicit source IDs.

**Go directly here:**
- [Official leaderboard](https://claw-eval.github.io/)
- [Official repository](https://github.com/claw-eval/claw-eval)
- [Task dataset](https://huggingface.co/datasets/claw-eval/Claw-Eval)
- [Separate token-efficiency project](https://github.com/AIgenteur/ClawEval)

**Coverage:** capability, token_usage.

**Available data:** Official benchmark: Pass^3, completion, safety and robustness over 300 human-verified tasks, 2,159 rubrics and three trials. The attached table additionally mentions tokens per trajectory/point.

**Currently unused / expansion opportunity:** Average score, Pass@k, per-category completion/safety/robustness, task-level traces, audit logs, environment snapshots, language/category fields, failures and trajectory token counts.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=claw_eval_pass3_pct`, `raw_value`, `raw_unit`, `benchmark_harness`, `quality`, `use_in_aggregate`

**Identity keys:** `official leaderboard model label + exact harness/config`

**Caveats:** The attached snapshot contains repeated identical values and is historical. Preserve duplicate rows for provenance but exclude identical repeats from aggregate weighting. The package’s referenced attached-source mirror is absent and should be repaired.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `claw_eval_pass3_pct` | percent Pass@3 | 22 |

### 16. DeepSeek V4 Flash 0731 release/model-card table (`deepseek-v4-flash-0731-model-card-2026-07-31`)

**Role:** Adds seven current agentic/coding benchmark values for the dated DeepSeek V4 Flash 0731 configuration.

**Acquisition used:** Direct HTML table extraction from the official DeepSeek release note.

**Preferred next acquisition:** Scrape the benchmark table from the dated release page, preserve benchmark names exactly, then separately fetch current official API pricing and model specifications from DeepSeek documentation.

**Go directly here:**
- [Official 0731 release note](https://api-docs.deepseek.com/news/news250731)
- [Official pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [API documentation](https://api-docs.deepseek.com/)

**Coverage:** metadata, capability, cost_or_price.

**Available data:** Vendor-reported scores for Agents Last Exam, Automation Bench, CyberGym, DeepSWE, NL2Repo, Terminal-Bench 2.1 and Toolathlon Verified.

**Currently unused / expansion opportunity:** Pricing, cache-hit pricing, context limits, multimodal/API capabilities, token throughput, system card details and any downloadable/open-weight artifacts linked from official documentation.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<benchmark slug>`, `raw_value`, `raw_unit`, `is_vendor_reported=1`, `base_weight=vendor weight`, `source_version=0731`

**Identity keys:** `deepseek-v4-flash-0731 + exact effort/reasoning mode`

**Caveats:** Vendor scorecards are useful coverage but should be lower-weight than independent reruns. Never merge 0731 with an earlier V4 Flash identity.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `agents_last_exam_pct` | percent/score | 1 |
| capability | `automation_bench_public_pct` | percent/score | 1 |
| capability | `cybergym_pct` | percent/score | 1 |
| capability | `deep_swe_pct` | percent/score | 1 |
| capability | `nl2repo_pct` | percent/score | 1 |
| capability | `terminal_bench_2_1_pct` | percent/score | 1 |
| capability | `toolathlon_verified_pct` | percent/score | 1 |

### 17. LiveBench release 2026-06-25 (`livebench-2026-06-25`)

**Role:** Supplies an objective overall capability score across seven categories for 45 configurations.

**Acquisition used:** Official release CSV mirrored from the LiveBench repository/site; v7 keeps only the overall score.

**Preferred next acquisition:** Pin a LiveBench release. Pull generated all_groups.csv and all_tasks.csv from the official repository/output, or reproduce them with show_livebench_result.py. Record the release option and question source.

**Go directly here:**
- [Official leaderboard](https://livebench.ai/)
- [Official repository](https://github.com/livebench/livebench)
- [Paper](https://arxiv.org/abs/2406.19314)

**Coverage:** capability, cost_or_price.

**Available data:** Overall score, seven category scores, 23 task scores, release version, task/question source, model errors and website-displayed run cost.

**Currently unused / expansion opportunity:** All seven category columns, all task-level columns, per-model run cost, failure/error counts, older releases and release-to-release regression analysis. The official tooling explicitly emits all_groups.csv and all_tasks.csv.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=livebench_overall_pct or livebench_<category/task>`, `benchmark_version_exact=<release>`, `raw_value`, `raw_unit`, `source_date`

**Identity keys:** `LiveBench model ID + prompt/reasoning configuration`

**Caveats:** Never combine different LiveBench releases in one source slice. Use separate source IDs if historical comparisons are intentionally retained.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `livebench_overall_pct` | percent | 45 |

### 18. Qwen3.8 Max stable-release scorecard (`qwen3-8-max-stable-scorecard-2026-08-03`)

**Role:** Adds fifteen benchmark values for Qwen3.8 Max.

**Acquisition used:** Official Qwen blog table extraction, with BenchLM used as a mirror/cross-check.

**Preferred next acquisition:** Parse the official release blog/model card and preserve every row, model mode and footnote. Use the BenchLM model page only as a verification mirror, not a second independent source.

**Go directly here:**
- [Official Qwen release blog](https://qwen.ai/blog?id=qwen3.8)
- [BenchLM cross-check](https://benchlm.ai/models/qwen-3-8-max)
- [Alibaba Model Studio catalog/pricing](https://help.aliyun.com/zh/model-studio/models)

**Coverage:** metadata, capability, cost_or_price.

**Available data:** Fifteen vendor-reported benchmark scores spanning agents, coding, math, multimodal, research and computer use.

**Currently unused / expansion opportunity:** Architecture/parameter details, active parameters, context/output limits, modalities, open-weight/model-card links, inference recommendations, pricing tiers and benchmark harness footnotes.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<benchmark slug>`, `raw_value`, `raw_unit`, `is_vendor_reported=1`, `use_in_aggregate=0 when duplicate of mirror`

**Identity keys:** `qwen3.8-max + exact reasoning mode`

**Caveats:** The current rows are marked duplicate of the BenchLM mirror and excluded from weighting. A future refresh should choose the official scorecard as canonical and mark the mirror as verification-only.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `agents_last_exam_pct` | percent/score | 1 |
| capability | `automation_bench_pct` | percent/score | 1 |
| capability | `cowork_bench_pct` | percent/score | 1 |
| capability | `deep_swe_pct` | percent/score | 1 |
| capability | `frontier_swe_pct` | percent/score | 1 |
| capability | `gpqa_diamond_pct` | percent/score | 1 |
| capability | `humanitys_last_exam_pct` | percent/score | 1 |
| capability | `mathvision_pct` | percent/score | 1 |
| capability | `mathvision_python_pct` | percent/score | 1 |
| capability | `mmmu_pro_pct` | percent/score | 1 |
| capability | `osworld_verified_pct` | percent/score | 1 |
| capability | `paper_bench_pct` | percent/score | 1 |
| capability | `skills_bench_pct` | percent/score | 1 |
| capability | `swe_bench_pro_pct` | percent/score | 1 |
| capability | `terminal_bench_2_1_pct` | percent/score | 1 |

### 19. Alibaba Cloud Qwen3.8 Max pricing (`qwencloud-pricing-2026-08-03`)

**Role:** Adds a blended token-price observation for the stable Qwen3.8 Max release.

**Acquisition used:** Manual extraction from the Alibaba Model Studio model catalog.

**Preferred next acquisition:** Parse the exact model row and all context-tier/cache/batch price columns. Preserve region/currency and effective date.

**Go directly here:**
- [Alibaba Model Studio models/pricing](https://help.aliyun.com/zh/model-studio/models)

**Coverage:** metadata, cost_or_price.

**Available data:** Current package: one blended USD-per-million-token value.

**Currently unused / expansion opportunity:** Separate input/output rates, context-length tiers, cache pricing, batch/discount plans, regional availability and model retirement/version notes.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=blended_token_price_per_m`, `raw_value`, `raw_unit`, `source_date`, `notes=<pricing tier>`

**Identity keys:** `Alibaba Cloud deployment/model ID + region + effective date`

**Caveats:** A blended rate hides workload mix. Prefer separate input/output/cache rows and derive scenario-specific task cost later.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `blended_token_price_per_m` | USD per 1M blended tokens | 1 |

### 20. SkateBench official attached table (`skatebench-official-attached`)

**Role:** Provides success rate and cost per successful run for 24 models.

**Acquisition used:** Manual attached CSV/table import; no packaged live refresh adapter.

**Preferred next acquisition:** Inspect the open-source repository first for generated JSON/CSV or embedded visualizer data. If no stable file exists, scrape all four server-rendered views from the public site and save a dated raw snapshot.

**Go directly here:**
- [Live dashboard](https://skatebench.t3.gg/)
- [Open-source repository](https://github.com/t3-content/skatebench)

**Coverage:** capability, cost_or_price, token_usage, latency_or_speed.

**Available data:** Accuracy/success, cost per success, average cost, token use, duration, throughput and errors are represented in the original attached table.

**Currently unused / expansion opportunity:** The live site exposes Accuracy, Cost, Speed and Matrix views; the repository may expose raw run data or the visualizer data bundle. Current v7 retains only success and cost-per-success rows.

**Post-ingestion fields:** `capability row + cost row per model/configuration`, `benchmark_version_exact=official`, `raw_value`, `raw_unit`, `notes=<correct/tests or token-cost detail>`

**Identity keys:** `exact site model ID including reasoning level`

**Caveats:** Skateboarding knowledge is a narrow domain and should receive modest capability weight. Keep official and v2 versions separate. The referenced packaged attached-source snapshot is currently missing.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `skatebench_cost_per_success_usd` | USD per successful run | 24 |
| capability | `skatebench_success_rate_pct` | percent success | 24 |

### 21. SkateBench visible v2 attached table (`skatebench-v2-attached`)

**Role:** Provides separate v2 accuracy and cost-per-success rows for 15 models.

**Acquisition used:** Manual attached CSV/table import; no packaged live refresh adapter.

**Preferred next acquisition:** Inspect the open-source repository first for generated JSON/CSV or embedded visualizer data. If no stable file exists, scrape all four server-rendered views from the public site and save a dated raw snapshot.

**Go directly here:**
- [Live dashboard](https://skatebench.t3.gg/)
- [Open-source repository](https://github.com/t3-content/skatebench)

**Coverage:** capability, cost_or_price, token_usage, latency_or_speed.

**Available data:** Accuracy and cost-per-success for the v2 view.

**Currently unused / expansion opportunity:** Speed, matrix-level results, per-question outcomes, token totals, duration/TPS and the full current 28-model table are not imported.

**Post-ingestion fields:** `capability row + cost row per model/configuration`, `benchmark_version_exact=v2`, `raw_value`, `raw_unit`, `notes=<correct/tests or token-cost detail>`

**Identity keys:** `exact site model ID including reasoning level`

**Caveats:** Skateboarding knowledge is a narrow domain and should receive modest capability weight. Keep official and v2 versions separate. The referenced packaged attached-source snapshot is currently missing.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `skatebench_v2_accuracy_pct` | percent accuracy | 15 |
| cost | `skatebench_v2_cost_per_success_usd` | USD per successful run | 15 |

### 22. Standardized task token-price estimator (`standard-task-price-proxy-v7`)

**Role:** Gives a transparent fallback X coordinate to priced configurations that lack measured task usage.

**Acquisition used:** Local derivation from catalog input/output prices and effort-specific standard token profiles.

**Preferred next acquisition:** Recompute after every models.dev/official price refresh. Version the task profile and keep each scenario as a distinct metric rather than silently changing constants.

**Go directly here:**
- [Current methodology](ardf-research-paper.md#53-standardized-task-token-price-estimate)
- [Calibration configuration](project-config.json)

**Coverage:** metadata, cost_or_price.

**Available data:** Estimated standardized-task USD using 12k input tokens plus effort-adjusted output/reasoning-equivalent tokens.

**Currently unused / expansion opportunity:** Multiple task profiles, uncertainty ranges, cached-input scenarios, long-context surcharge tiers, batch discounts, provider-specific routing prices and empirically learned token profiles by task class.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=standardized_task_price_proxy_usd`, `quality=estimated`, `base_weight=low`, `notes=formula/profile version`, `cal_* fields`

**Identity keys:** `catalog model_key + effort + task profile version`

**Caveats:** This is a modelled coordinate, not observed cost. Keep the quality flag visible and let users filter it out.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `standardized_task_price_proxy_usd` | estimated USD per standardized task | 413 |

### 23. User-supplied best-cost table (`user-best-cost-attached`)

**Role:** Supplies source-specific cost values for 47 configurations.

**Acquisition used:** Manual CSV upload.

**Preferred next acquisition:** Require a companion provenance manifest for every row: upstream source URL, metric definition, currency, benchmark/task scope, retrieval date and calculation formula. Preserve the original file hash.

**Go directly here:**
- [Expected packaged mirror](sources/attached-source-snapshots.json)

**Coverage:** cost_or_price.

**Available data:** One source-specific cost value per imported model.

**Currently unused / expansion opportunity:** The original upstream URL, benchmark scope, token counts, calculation method and uncertainty are missing from the current package.

**Post-ingestion fields:** `metric_axis=cost`, `metric_name=user_best_cost_usd`, `source_url=<real upstream URL>`, `notes=<formula/scope>`, `quality=<verified or unknown>`

**Identity keys:** `uploaded model label crosswalked to exact model_key`

**Caveats:** The referenced packaged mirror does not exist in v7. Treat these rows as low-confidence until the original CSV and provenance are restored.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| cost | `user_best_cost_usd` | USD source-specific cost | 47 |

### 24. Vals SWE-bench mirror (`vals-swe-bench-2026-07-22`)

**Role:** Vals-hosted SWE-bench score.

**Acquisition used:** Server-rendered benchmark-table extraction, with BenchLM mirror pages used during the original v5 import.

**Preferred next acquisition:** Start at the live Vals benchmark directory, open the exact benchmark detail page, extract every displayed model row, rank, score, update date and mode/harness label, and save the page/JSON payload as a dated raw snapshot.

**Go directly here:**
- [Exact benchmark page](https://www.vals.ai/benchmarks/swebench)
- [Full Vals benchmark directory](https://www.vals.ai/benchmarks)
- [Vals model directory](https://www.vals.ai/models)

**Coverage:** metadata, capability.

**Available data:** Model score, rank, benchmark update date, model count and benchmark description. The directory exposes many additional current benchmarks.

**Currently unused / expansion opportunity:** Current model count, harness/model-mode details, ranks, and newer benchmark versions should be refreshed; compare with the official SWE-bench leaderboard to avoid treating a mirror as canonical.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<vals benchmark slug>`, `raw_value`, `raw_unit=percent`, `source_date=<page updated date>`, `benchmark_version_exact`, `notes=<rank/model count>`

**Identity keys:** `Vals displayed model + mode/reasoning label`

**Caveats:** The v7 snapshots are dated July 22–23 while the live Vals directory now shows August updates. Refresh them. Do not double-count Vals mirrors of official benchmarks alongside the official leaderboard without a correlation/down-weighting rule.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `vals_swe_bench_pct` | percent | 74 |

### 25. Vals Terminal-Bench 2.1 (`vals-terminal-bench-2-1-2026-07-22`)

**Role:** Terminal-agent task accuracy.

**Acquisition used:** Server-rendered benchmark-table extraction, with BenchLM mirror pages used during the original v5 import.

**Preferred next acquisition:** Start at the live Vals benchmark directory, open the exact benchmark detail page, extract every displayed model row, rank, score, update date and mode/harness label, and save the page/JSON payload as a dated raw snapshot.

**Go directly here:**
- [Exact benchmark page](https://www.vals.ai/benchmarks/terminal-bench-2-1)
- [Full Vals benchmark directory](https://www.vals.ai/benchmarks)
- [Vals model directory](https://www.vals.ai/models)

**Coverage:** metadata, capability.

**Available data:** Model score, rank, benchmark update date, model count and benchmark description. The directory exposes many additional current benchmarks.

**Currently unused / expansion opportunity:** Current rows, model modes, harness details and the official Terminal-Bench results/registry are not imported.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<vals benchmark slug>`, `raw_value`, `raw_unit=percent`, `source_date=<page updated date>`, `benchmark_version_exact`, `notes=<rank/model count>`

**Identity keys:** `Vals displayed model + mode/reasoning label`

**Caveats:** The v7 snapshots are dated July 22–23 while the live Vals directory now shows August updates. Refresh them. Do not double-count Vals mirrors of official benchmarks alongside the official leaderboard without a correlation/down-weighting rule.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `terminal_bench_2_1_pct` | percent | 44 |

### 26. Vals Vibe Code Bench v1.1 (`vals-vibe-code-v1-1-2026-07-23`)

**Role:** End-to-end web-application implementation score.

**Acquisition used:** Server-rendered benchmark-table extraction, with BenchLM mirror pages used during the original v5 import.

**Preferred next acquisition:** Start at the live Vals benchmark directory, open the exact benchmark detail page, extract every displayed model row, rank, score, update date and mode/harness label, and save the page/JSON payload as a dated raw snapshot.

**Go directly here:**
- [Exact benchmark page](https://www.vals.ai/benchmarks/vibe-code)
- [Full Vals benchmark directory](https://www.vals.ai/benchmarks)
- [Vals model directory](https://www.vals.ai/models)

**Coverage:** metadata, capability.

**Available data:** Model score, rank, benchmark update date, model count and benchmark description. The directory exposes many additional current benchmarks.

**Currently unused / expansion opportunity:** The current live page has more models and recent releases. Per-dimension app quality, task details, artifacts or rubric breakdowns may be available on the detail page/platform.

**Post-ingestion fields:** `metric_axis=capability`, `metric_name=<vals benchmark slug>`, `raw_value`, `raw_unit=percent`, `source_date=<page updated date>`, `benchmark_version_exact`, `notes=<rank/model count>`

**Identity keys:** `Vals displayed model + mode/reasoning label`

**Caveats:** The v7 snapshots are dated July 22–23 while the live Vals directory now shows August updates. Refresh them. Do not double-count Vals mirrors of official benchmarks alongside the official leaderboard without a correlation/down-weighting rule.

**Metrics currently present:**

| Axis | Metric | Unit | Rows |
|---|---|---|---:|
| capability | `vibe_code_bench_pct` | percent | 73 |

## Future source candidates

These sources are **not independent votes until ingested and deduplicated**. Their likely value is documented so a future agent can target gaps rather than randomly scrape another leaderboard.

### SWE-bench official leaderboards and experiment records — critical priority

**Why:** Canonical coding-agent source; resolves ambiguity introduced by Vals/BenchLM mirrors and lets the project distinguish model from scaffold.

**Likely findings:** Verified/Lite/Multimodal scores, exact agent scaffold and submission date, trajectories, execution logs, model/provider labels and reproducibility metadata.

**Acquisition:** Read data/leaderboards.json for the rendered leaderboard and ingest submission directories from the experiments repository for predictions, results, logs and trajectories.

**Entry points:**
- <https://www.swebench.com/>
- <https://github.com/swe-bench/swe-bench.github.io>
- <https://github.com/swe-bench/experiments>

### Terminal-Bench official leaderboard and registry — critical priority

**Why:** Independent source for one of the most influential agentic metrics already appearing in vendor tables.

**Likely findings:** Terminal-Bench 2.1/2.0 success, task-level results, model-agent combinations, registry metadata and challenge-specific evidence.

**Acquisition:** Use the official leaderboard/registry data or scrape the versioned benchmark page. Record benchmark version, agent harness, environment image and task registry commit.

**Entry points:**
- <https://www.tbench.ai/>
- <https://www.tbench.ai/registry>
- <https://www.tbench.ai/benchmarks/terminal-bench-2>

### Berkeley Function Calling Leaderboard (BFCL V4) — critical priority

**Why:** Rare source that provides capability, benchmark-wide USD cost and latency together, ideal for direct Pareto evidence.

**Likely findings:** Overall and subcategory tool-use accuracy, agentic/multi-turn/live/non-live/hallucination scores, estimated total benchmark cost, latency, function-calling mode and format sensitivity.

**Acquisition:** Parse the official leaderboard or repository result artifacts at the pinned evaluation commit/package version.

**Entry points:**
- <https://gorilla.cs.berkeley.edu/leaderboard.html>
- <https://github.com/ShishirPatil/gorilla>

### Aider Polyglot coding leaderboard — high priority

**Why:** Another direct capability-plus-cost source, with transparent coding workflow configuration.

**Likely findings:** Percent correct, total benchmark cost, correct-edit-format rate, edit format and exact invocation command.

**Acquisition:** Scrape the official leaderboard table and preserve command/model string, effort, edit format and benchmark version.

**Entry points:**
- <https://aider.chat/docs/leaderboards/>
- <https://aider.chat/docs/leaderboards/notes.html>

### LiveCodeBench official leaderboard — high priority

**Why:** Contamination-limited coding evidence that complements SWE-bench’s repository repair focus.

**Likely findings:** Pass@1 by difficulty, code generation, self-repair, execution and output-prediction scenarios, time-window freshness and model configuration.

**Acquisition:** Use official repository result files or the rendered leaderboard. Pin release_v1/release_v2, date window, scenario and fast/full setting.

**Entry points:**
- <https://livecodebench.github.io/leaderboard.html>
- <https://github.com/livecodebench/livecodebench>

### Epoch AI Benchmarking database — high priority

**Why:** High-quality normalization layer with explicit provenance and downloadable structured data.

**Likely findings:** Many benchmark/model pairs, evaluation setup, repeats, source provenance, model release metadata and confidence/strict-scoring context.

**Acquisition:** Download the official CSV or use the epochai Python client/Airtable API. Preserve whether each value was evaluated by Epoch or collected from an external official source.

**Entry points:**
- <https://epoch.ai/benchmarks>
- <https://epoch.ai/benchmarks/use-this-data>
- <https://epoch.ai/data/ai-models>

### Arena / LMArena leaderboard dataset — high priority

**Why:** Adds human preference and confidence intervals, a useful orthogonal signal to automatic task benchmarks.

**Likely findings:** Human-preference ratings, confidence intervals, sample counts, category/style controls, text/vision/agent arenas and historical snapshots.

**Acquisition:** Load the official Hugging Face Parquet dataset rather than scraping the UI. Pin methodology/changelog version and arena type.

**Entry points:**
- <https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset>
- <https://huggingface.co/spaces/lmarena-ai/arena-leaderboard>
- <https://arena.ai/blog/arena-leaderboard-dataset>

### OpenRouter Models and provider-performance API — high priority

**Why:** Best provider-routing and live-market complement to models.dev. Avoid using its AA-derived intelligence field as a new independent benchmark.

**Likely findings:** Model/provider availability, exact routing IDs, pricing structures, context, architecture, supported parameters, creation date, recent throughput/latency and popularity/token-volume sorting.

**Acquisition:** Call the public models API; optionally query provider/model performance and generation records with authenticated access.

**Entry points:**
- <https://openrouter.ai/docs/api/api-reference/models/get-models>
- <https://openrouter.ai/api/v1/models>

### Stanford HELM Capabilities — medium priority

**Why:** Broad reproducible academic evidence and detailed prompt-level auditability.

**Likely findings:** Scenario-level accuracy, calibration, robustness, fairness, efficiency and full prompt-level transparency under reproducible settings.

**Acquisition:** Use HELM result artifacts/framework outputs for a pinned leaderboard version, not screenshots.

**Entry points:**
- <https://crfm.stanford.edu/helm/index.html>
- <https://crfm.stanford.edu/helm/capabilities/>

### OSWorld / OSWorld 2.0 official results — high priority

**Why:** Adds genuine GUI/computer-use evidence for models whose marketing tables currently dominate that domain.

**Likely findings:** Computer-use completion, partial score, model-agent configuration, verified trajectories, step/tool-call counts and safety reports.

**Acquisition:** Ingest official team-verified result tables and trajectory links. Record OSWorld version, agent scaffold, step budget and tool mode.

**Entry points:**
- <https://osworld-v1.xlang.ai/>
- <https://github.com/xlang-ai/OSWorld>

### BigCodeBench official leaderboard — medium priority

**Why:** Broadens coding beyond repository patching into complex API/library use.

**Likely findings:** Pass@1 for practical multi-library code generation, hard/full subsets, instruction variants, model size and evaluation timing metadata.

**Acquisition:** Use official leaderboard data or evaluation-harness outputs, pin Full/Hard, Complete/Instruct and version.

**Entry points:**
- <https://bigcode-bench.github.io/>
- <https://github.com/bigcode-project/bigcodebench>

### METR time-horizon evaluations — medium priority

**Why:** Adds a different notion of capability: how long a task an agent can reliably complete, rather than one-shot benchmark accuracy.

**Likely findings:** 50%-success task time horizon, long-horizon autonomy curves, task duration, run cost/token use where disclosed, and scaffold sensitivity.

**Acquisition:** Use published result datasets/appendices and model-run metadata from the official research release. Preserve task suite, elicitation and scaffold.

**Entry points:**
- <https://metr.org/research/>
- <https://github.com/METR>

## v7.3 release-specific reminders

- **Muse Spark 1.2:** keep both Meta price tiers. For this project the Contributor/data-sharing SKU is primary: `$0.10/M input`, `$0.002/M cache read`, `$0.20/M output`. Standard/no-sharing remains secondary metadata. Never average the two.
- **Muse task cost:** the current `$0.02123` ARDF coordinate is a transparent reprice of the AA Standard workload to Contributor pricing. It is derived, not a direct AA Contributor billing observation.
- **GPT-5.6 Luna:** current normal short-context list pricing is `$0.20/M input`, `$0.02/M cached`, `$0.25/M cache write`, `$1.20/M output`. Do not resurrect the pre-July-30 `$1/$6` rates.
- **Ling 3.0 Tiny:** its current zero-dollar API availability is promotional. Preserve it, but exclude zero cost from logarithmic/Pareto calculations until a durable nonzero price exists.
- **Mirrors:** BenchLM or vendor pages that repeat the same underlying benchmark result must not both receive aggregation weight. One is evidence, the other is verification/display.


---

# Appendix B. Consolidated Operational Notes

The original v7.3 README contained useful operational facts mixed with a now-superseded multi-directory package layout. The folder-layout material is intentionally not reproduced here; `INDEX.md` contains the complete 40-file → 9-file migration map. The durable operational facts follow.

## Current build

- **683** cataloged model × reasoning/effort configurations
- **2115** atomic capability/cost/diagnostic-metadata observations
- **2798** total canonical CSV records
- **25** observation source datasets, plus models.dev static metadata
- **44** exact models.dev matches; remaining catalog rows are explicitly marked provider/fallback matches rather than faked exact matches
- **252** current/recent paired configurations under the default analysis policy
- **16** strict current Pareto points
- **65** current configurations in the configured near-frontier band

## Identity corrections that matter

### DeepSeek V4 Pro is still the Preview Pro identity

The package now labels all existing Pro rows **DeepSeek V4 Pro Preview**. DeepSeek's Apr. 24 release was explicitly the *V4 Preview* family. The Jul. 31 Flash update promoted Flash to `DeepSeek-V4-Flash-0731`, while DeepSeek stated that Pro remained unchanged and that the official Pro release was still forthcoming.

Do not create a separate final `DeepSeek V4 Pro` identity until DeepSeek actually announces one.

Verification targets:

- `https://api-docs.deepseek.com/news/news260424/`
- `https://x.com/deepseek_ai/status/2083084419515220191`
- `https://api-docs.deepseek.com/zh-cn/guides/responses_api`

### MiMo identities are separated

The earlier package mixed stale/current evidence around similarly named Xiaomi rows. V7.3 enforces:

- **MiMo-V2.5** — current AA Intelligence Index **38**
- **MiMo-V2.5-Pro** — current AA Intelligence Index **43**, 1.0T total / 42B active, current AA full-evaluation cost `$98.86`
- **MiMo-V2-Pro** — older predecessor, retained separately
- former alias `mimo-v2-5-0424` — merged into canonical `mimo-v2-5`; it is not a separate model vote
- non-reasoning/provider/UltraSpeed variants remain separate when measurements or economics differ

Verification targets:

- `https://artificialanalysis.ai/models/mimo-v2-5-pro`
- `https://artificialanalysis.ai/models/comparisons/mimo-v2-5-pro-vs-mimo-v2-5-0424`

This correction removes MiMo-V2.5-Pro from the current ≥45 executor shortlist rather than allowing its stale score to inflate the ranking.

## Pareto versus price/performance

These are deliberately separate concepts:

```text
Pareto optimal:
  no competitor exists with cost <= candidate cost
  AND capability >= candidate capability
  with at least one strict inequality

Executor price/performance:
  task_price / calibrated_capability
  lower is better
```

The executor list applies a calibrated-capability floor of 45. The floor is visible policy, not part of the score formula.

Current executor-grade ranking:

1. **Muse Spark 1.2 (xhigh, Contributor pricing)** — capability 54.54, task cost $0.02123, $/capability 0.0003893
2. **GPT-5.6 Luna (high)** — capability 47.00, direct AA task cost $0.02000, $/capability 0.0004255
3. **DeepSeek V4 Flash 0731 (max)** — capability 52.00, direct AA task cost $0.03000, $/capability 0.0005769
4. **Grok 4.3 (high)** — capability 53.00, task cost $0.10662, $/capability 0.0020117
5. **MiniMax-M3** — capability 46.59, task cost $0.12295, $/capability 0.0026391


Muse Spark 1.2 continues to use the user-selected **Contributor/data-sharing** price tier as its primary operational coordinate. AA's Standard-priced evaluation remains separate evidence and is not averaged with Contributor economics.

## GPT-5.6 Luna

Primary synchronous executor economics use the current Standard short-context price schedule `$0.20/M input` and `$1.20/M output`; long-context and Batch prices remain secondary metadata.

For literal `$ / calibrated-capability`, **Luna high** is the current value winner. `xhigh` is a capability knee, not the price/performance winner; `max` is the quality-first setting.

## Top-end routing zone

The package now audits these families/configurations separately:

- Claude Opus 5
- Claude Fable 5
- GPT-5.6 Sol
- Qwen3.8 Max
- Kimi K3

Two planes are shown side-by-side:

1. **ARDF operational:** multi-source calibrated capability vs operational task cost.
2. **AA same-source:** exact AA Intelligence Index vs direct AA Cost per Intelligence Index Task where available, with full-evaluation cost retained only as a diagnostic/fallback.

The same-source view is specifically for reasoning-level pruning. Current example: **Opus 5 max is dominated by Opus 5 xhigh** because both score 63 on current AA while direct task cost is $2.34 versus $1.80. Do not default-route a dominated effort level unless a specialist benchmark shows a compensating advantage.

## Independent Pareto cross-checks

The dashboard adds three source-native cost/performance graphs. Their raw axes remain separate rather than being pretended to be the same benchmark:

- **Artificial Analysis:** Intelligence Index vs Cost per Intelligence Index Task. AA's own site now exposes a public Pareto line.
- **KiloBench:** coding-agent completion rate vs cost per attempt.
- **Vals Index:** accuracy vs Cost/Test.

The package-calibrated ARDF graph remains the primary synthesized plane; source-native graphs are diagnostic checks for agreement and task specialization.

## Build architecture

The working package has one executable: `calibrate.py`. It owns recurring standardized-cost derivation, calibration, analysis, document regeneration, dashboard payload embedding, optional models.dev synchronization, and validation. Source acquisition from heterogeneous benchmark/provider sources remains a separate evidence-refresh step governed by the source manifest and Appendix A. The original v7.3 ZIP is the archive for dated migrations and superseded code.

Run:

```bash
python calibrate.py
```

## Dashboard contract

The main visualizer retains:

- one dot per model/reasoning configuration, plus Evidence Cloud mode
- all model names visible by default
- unpriced/unscored shelves rather than disappearing rows
- independent log/linear toggles on both axes
- source/provider/date/lifecycle/effort/harness and models.dev metadata filters
- complete raw/calibrated evidence on hover/pin
- optional strict Pareto overlay
- capability tiers and near-frontier tables
- executor price/performance table
- top-end reasoning-level audit
- AA/Kilo/Vals source-native Pareto comparison graphs

Calibration and source fitting do not occur in browser display code.

## Validation

Run `python calibrate.py`. The final validator checks identity separation, current source IDs, calibrated data, source-documentation coverage, generated payloads, dashboard script references, executor math, top-end pruning, external Pareto products, and ZIP-ready package cohesion.

Pixel-level browser rendering is not claimed unless a browser test completes successfully. Static JavaScript syntax/link/payload checks are part of package validation.


---

# Appendix C. 2026-08-08 Forensic Refresh Record

<!-- ARCHIVE STATUS: RELEASE SNAPSHOT
This dated v7.3 refresh memo is preserved for provenance. Durable identity/routing rules were folded into pareto-frontier-cheatsheet.md, ardf-research-paper.md, and user-prompt-aggregation.md.
-->

<!--
---
title: ARDF Current-Model and Identity Refresh
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
---
-->

## ARDF v7.3 current-model and identity refresh

This memo records the August 8 forensic refresh layered onto v7.2.1. It is intentionally separate from the general methodology because these facts are date-sensitive.

## DeepSeek V4 Pro

Treat all currently observed V4 Pro rows as **DeepSeek V4 Pro Preview**. DeepSeek's Apr. 24 announcement was `DeepSeek V4 Preview`; the Jul. 31 Flash 0731 announcement explicitly said Pro remained unchanged and its official release was still coming. API support changes do not create a new model checkpoint.

Current package identity keys remain `deepseek-v4-pro-*` for backward compatibility, but display/family/status metadata say Preview. A future official Pro release must receive a new explicit release/version identity unless DeepSeek states that the existing checkpoint was simply promoted unchanged.

## Xiaomi MiMo

Current AA identity check:

| Model | Current AA Intelligence Index | Current AA full evaluation cost | Identity action |
|---|---:|---:|---|
| MiMo-V2.5 | 38 | $25.18 | Canonical plain V2.5; merge old `mimo-v2-5-0424` alias |
| MiMo-V2.5-Pro | 43 | $98.86 | Distinct Pro model; do not borrow plain score |
| MiMo-V2-Pro | older separate evidence | — | Preserve predecessor as separate identity |

This changes routing: MiMo-V2.5-Pro no longer clears the project's 45-point general-executor eligibility floor.

## General executor zone

Current literal `$ / calibrated-capability` top five among current priced configurations with calibrated capability ≥45:

1. Muse Spark 1.2 (xhigh, Contributor pricing): capability 54.54, task $0.02123, ratio 0.0003893
2. GPT-5.6 Luna (high): capability 47.00, direct AA task $0.02000, ratio 0.0004255
3. DeepSeek V4 Flash 0731 (max): capability 52.00, direct AA task $0.03000, ratio 0.0005769
4. Grok 4.3 (high): capability 53.00, task $0.10662, ratio 0.0020117
5. MiniMax-M3: capability 46.59, task $0.12295, ratio 0.0026391

Muse's coordinate uses Contributor/data-sharing pricing; the AA Standard route remains separately visible. Luna high is now the nearest literal price/performance challenger because current AA direct Cost per Intelligence Index Task is $0.02. DeepSeek V4 Flash 0731 remains extremely close in absolute cost and carries higher calibrated capability, making it an important executor alternative despite its slightly worse ratio.

## Top-end zone

The preferred same-source pruning plane is now **AA Intelligence Index vs direct Cost per Intelligence Index Task** whenever AA publishes the task-cost field. Full Intelligence Index evaluation cost remains visible as a secondary diagnostic and is used only when direct task cost is unavailable.

Key current cuts:

- **Claude Opus 5 max: hard prune for general default routing.** Max and xhigh both score 63 on current AA, while direct AA task cost is $2.34 for max versus $1.80 for xhigh.
- **Claude Opus 5 medium/high/xhigh:** keep as explicit cost/quality rungs. High and GPT-5.6 Sol max are Pareto-equivalent on the current AA top-end slice at 61 / $1.23.
- **GPT-5.6 Sol:** low → medium → high → xhigh → max remains internally monotone. Cross-family, some rungs are dominated or tied, so retain Sol primarily where coding/agent evidence justifies it.
- **Kimi K3 max:** remains on both the audited ARDF operational top-end frontier and the current AA direct-task-cost top-end frontier. Kilo independently gives it a strong coding-agent cost/completion position.
- **Qwen3.8 Max xhigh:** currently misses both audited general top-end frontiers because cheaper configurations provide equal or higher general capability. Preserve it for Qwen-specific or specialist workloads, not as a default frontier route.
- **Fable 5 max:** remains near the capability ceiling but is price-heavy. In the audited general plane it is dominated by cheaper Opus/Sol/Kimi alternatives; Vals still shows Fable as the highest-scoring model on its workload, illustrating task sensitivity.

V7.3 therefore keeps independent source-native frontier views:

- AA Intelligence Index vs direct Cost per Intelligence Index Task
- Kilo coding completion vs cost/attempt
- Vals Index vs Cost/Test

These views intentionally disagree. Kilo's current public top-10 cost/completion plane retains Grok 4.5 → Kimi K3 → GPT-5.5 → GPT-5.6 Sol. Vals' current Index/Cost-Test plane retains DeepSeek Flash 0731 → Luna → Muse → Kimi K3 → Opus 5 → Fable 5. The disagreement is useful evidence of workload/harness specialization rather than an error to average away.

## Source URLs to re-check on the next refresh

- DeepSeek Preview release: `https://api-docs.deepseek.com/news/news260424/`
- DeepSeek current update/status: `https://x.com/deepseek_ai/status/2083084419515220191`
- AA model/Pareto explorer: `https://artificialanalysis.ai/`
- AA MiMo Pro: `https://artificialanalysis.ai/models/mimo-v2-5-pro`
- Kilo leaderboard: `https://kilo.ai/leaderboard`
- Vals current index/benchmarks: `https://www.vals.ai/home`

## Build script semantics

`calibrate.py` is the sole calibration engine. `calibrate.py` is the sole complete package-generation/orchestration entry point. The ambiguous legacy `rebuild.py` wrapper was removed in v7.3 so future agents cannot mistake it for a second calibration implementation.

