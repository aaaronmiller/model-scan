# Data Quality and Methodology

## Provenance

- Canonical ledger: `data/unified_model_observations.csv` — 2829 rows at grain model_key × effort × harness × source_id × metric_name × source_date.
- Calibrated ledger: `data/calibrated_model_observations.csv` — same rows + `calibrated_score_v1` (robust-affine, Theil-Sen) and `v2` (auto-best). Raw values never overwritten.
- Sources: 28 benchmark/price sources (target 12–15). Examples: Artificial Analysis (Intelligence Index + cost-per-task), LiveBench, BenchLM, Vals Index/SWE-Bench/Terminal-Bench/Vibe-Code, Kilo, SkateBench, official provider pricing, models.dev static metadata (25+ fields).
- Refresh: single current snapshot per source with `retrieved_at` and `source_date`; stale vs fresh not mixed without version tag.

## Pricing assumptions

- **Task Cost** = (T_in·P_in + T_out·P_out + T_cached·P_cached)/1e6. Standardized mix: T_in=12000, T_out=2500, T_cached≈0 (cached tier $0.002 for Muse Contributor vs $0.15 standard). Effort multipliers: input {minimal 0.85, high 1.1, xhigh 1.15}, output {high 3.2, xhigh 4.75, max 8.5}. Output-token price alone is not used.
- Muse Spark 1.2 uses **Contributor/data-sharing tier $0.10/$0.002/$0.20 (repriced task $0.02123)** as primary coordinate; Standard $1.25/$0.15/$4.25 ($0.40) kept as secondary. Luna reduction re-checked at ingestion (gpt-5-6-luna $0.20/$1.20 confirmed).
- Direct measured AA cost-per-task outranks token-price proxy rows in `cost_priority` hierarchy; proxy weight 0.35–0.65 and is calibrated via exact model overlaps, not billed directly.

## Calibration math

- **Outside the HTML**: `scripts/calibrate.py` reads canonical CSV, fits per-group `metric_axis × source_id × metric_name` mappings to AA Intelligence Index (capability) and AA cost-per-task (cost, in log10), writes `cal_*` columns. Dashboards only filter/aggregate precomputed values.
- **Multi-point overlap-graph**: each benchmark normalized via shared models; robust Theil-Sen affine (median slope+intercept, 30k slopes cap, cost in log10) is production default; Huber IRLS and monotone piecewise linear are alternatives; `auto-best` picks lowest RMSE per group (optimistic envelope).
- Chains only when direct overlap unavailable; anchor_count ≥4 (≥5 for monotone), blank calibration otherwise (never zero). Confidence = anchor_count + RMSE + status.
- Versioned fields: `calibrated_score_v1` (robust) and `v2` (auto-best); adding `v3` via workbench never breaks prior.

## Uncertainty

- 72% of cost rows are derived proxies (standardized estimator + AA token×price), mapped through 7 direct anchors → higher variance at tails; see `cal_*_rmse` per group.
- Thin-evidence models (Luna high 4 obs/2 sources, DeepSeek Flash 0731 7 obs) flagged; ≥8 points / 12–15 sources target documented in source_catalog.
- 5/50 models.dev fields are 0% populated upstream (experimental, input_limit_tokens, interleaved fields, reasoning_price_per_m) — hidden in UI, documented here.

## How to add a new benchmark or algorithm

1. `python scripts/ingest_sources.py --source-id my-bench-2026-08-11 --csv my_bench.csv --source-url https://... --source-date 2026-08-11`
2. `python scripts/validate_data.py` — checks grain, uniqueness, raw finite, catalog consistency.
3. `python scripts/calibrate.py` — refits all groups, writes new `cal_*` columns and versioned `calibrated_score_vN` (edit `project-config.json` or use `calibration-workbench.html` to add algorithm).
4. `python scripts/compute_frontier.py --floor 45` — regenerates `artifacts/*.md` and validates frontier.
5. Open `calibration-workbench.html` to tune anchors/weights, compare algorithms, export new calibrated CSV without touching raw.
