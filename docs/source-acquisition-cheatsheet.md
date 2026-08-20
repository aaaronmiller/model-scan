<!--
---
title: ARDF Source Acquisition and Supplementation Cheatsheet
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
---
-->

# ARDF source acquisition and supplementation cheatsheet

This is the **v7.3 current-source field manual**. It is generated from `config/source-acquisition-manifest.json` so source IDs, URLs and row counts stay synchronized with the canonical CSV. The source-methodology HTML is a searchable rendering of the same manifest.

> **Acquisition rule:** prefer official API/repository data; save a complete dated raw slice; normalize identities before observations; retain exactly one current vote per source; calibrate only after ingestion; never let a mirror or a copied vendor score vote twice.

## Ten-minute refresh workflow

1. Inspect `sources/source-ledger.json` and this document.
2. Refresh critical/high sources first, especially models.dev, Artificial Analysis, official pricing, and recently released model pages.
3. Prefer structured API/CSV/JSON/repository results over rendered HTML.
4. Preserve raw native units and source dates.
5. Match exact model + reasoning/effort + harness identities before generating observations.
6. Emit one atomic capability or cost observation per metric; static facts belong in `models_dev_*` metadata.
7. Replace the previous current slice for the same source. Use `source_original_id` to retain historical provenance without extra voting weight.
8. Run `scripts/build-package.py` for the complete deterministic build, or run `augment_cost.py`, `calibrate.py`, and `build-analysis.py` individually when debugging one stage.
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

**Acquisition used:** JSON catalog synchronization through scripts/sync_models_dev.py, with an offline snapshot accepted when live download fails.

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
- [Derivation methodology](docs/methodology.md#52-model-specific-token-count--price-proxy)

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
- [Current methodology](docs/methodology.md#53-standardized-task-token-price-estimate)
- [Calibration configuration](config/calibration-algorithms.json)

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
