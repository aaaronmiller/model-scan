# ARDF v7.5.0 - Errors, Omissions, and Judicial Audit Findings

**Refined from:** `ardf-pareto-living-document` v7.3 / v7.4.0 across 21 historical archive snapshots  
**Date:** 2026-11-09  
**Version:** 7.5.0  
**Scope:** Independent methodology and math validation pass (`gemini-4-argon-high` Judge), cross-lineage archive consolidation, cost-priority bug fix in `calibrate.py`, effort-lineage graph curves, smart frontier + contender label placement, and full integrated documentation inside `dashboard.html`.

## Summary verdict

The v7.5.0 canonical package resolves the divergence between the November 2026 Artificial Analysis v4.2 live refresh (`current_frontier.py`), the multi-source calibration engine (`calibrate.py`), and the standalone visualization (`dashboard-template.html` -> `dashboard.html`). All 21 archive lineages and ZIP snapshots were audited; constructive additions (`calibration-audit.md` dispersion and 6-MAD outlier filter, `ardf-ux-linear` 4-tier operational policy + pinch-point matrix + bottom-4 interchangeability matrix, and `model-routing-2026-11-04.md` subscription vs API routing matrix + provisional top-10 free candidates) have been integrated into the canonical working set.

## Part I - Judicial Audit Findings (v7.4.0 -> v7.5.0)

### Finding 1 - Cost priority bug in `calibrate.py: aggregate_sets` (Fixed in v7.5.0)

- **Defect:** `ana_aggregate()` (line 954) and `dashboard-template.html` (`combineCosts`, line 177) both implemented the documented `best_evidence_then_weighted_geometric_mean` rule, filtering cost observations to the highest priority tier (`priority 5` direct AA task cost over `priority 2` synthetic token-price proxy) and yielding **$26.539** for `Claude Fable 5.2 (Max, Default Fallback)`. However, `calibrate()`'s `aggregate_sets` loop (line 424, which feeds `render_tiers_document()`) took `weighted_geometric_mean` across all cost rows without priority filtering, blending `$26.539` (`w=1.0`) with `$10.506` (`w=0.35`) to produce `$18.654` in `model-tiers-and-contenders.md`.
- **Fix:** Updated `aggregate_sets` in `calibrate.py` to apply `ana_scale_filter` on capability and filter cost observations to `max(ana_cost_priority(r))` before computing `weighted_geometric_mean`. `pareto-frontier-cheatsheet.md`, `model-tiers-and-contenders.md`, and `dashboard.html` now agree to full precision (`$26.539`).

### Finding 2 - Pareto tie-breaking consistency in `calibrate.py: pareto()` (Fixed in v7.5.0)

- **Defect:** `pareto()` (line 246) used a single-pass `score > best + 1e-12` check after sorting by `(cost, -capability, model_key)`, which could drop a second model tied at the exact same `(cost, capability)` coordinate, whereas `ana_dominates()` (line 999) properly preserved exact coordinate ties.
- **Fix:** Unified `pareto()` with the strict dominance definition in `ana_dominates()`.

### Finding 3 - Stale source IDs and prefixes in `calibrate.py` analysis helpers (Fixed in v7.5.0)

- **Defect:** `ana_current_aa_by_model()` and `ana_external_frontier_comparisons()` checked only `source_id == 'artificial-analysis-current'`, missing `aa-primary-current` rows from the November 2026 refresh. Similarly, `luna_effort_curve` checked `gpt-5-6-luna-` instead of `GPT-6 Luna`, and `project-config.json` had August model keys in `major_model_keys` and `top_end`.
- **Fix:** Updated `project-config.json` and `calibrate.py` to include `'aa-primary-current'`, the 20 November 2026 watchlist keys, the 6-rung `GPT-6 Luna` effort curve (`none`, `low`, `medium`, `high`, `xhigh`, `max`), and both the unrestricted top-5 price/performance table and the **Role-Gated T3+ Executor Shortlist (`capability >= 47.0`)**.

### Finding 4 - Why August 2026 v4.0 rows are marked `is_historical=1, use_in_aggregate=0` (Verified intentional)

- **Audit question:** Why did `current_frontier.py` demote August 2026 observations to `is_historical=1, use_in_aggregate=0`?
- **Verdict:** In August 2026, Artificial Analysis used the v4.0 Intelligence Index scale (where `Claude Opus 5 Max` scored `63.0` at `$2.34`). In November 2026, Artificial Analysis transitioned to the much harder 10-benchmark v4.2 suite (where the same `Claude Opus 5 Max` scores `44.02` at `$9.38`, and `Claude Fable 5.2 Max` leads at `64.56`, `$26.54`). Leaving raw August v4.0 reference scores active alongside November v4.2 scores would mix two incompatible reference scales.

### Finding 5 - Three HTML / Data Methodology Items Preserved Pending User Review

Per user instruction (*"if any issues are found with the html methodology inform me before changing it"*), the following three behaviors were identified by the judicial audit and **not altered** in the core scoring/HTML math:

1. **Static `ARDF_ANALYSIS.frontier` override in `dashboard-template.html` (`markFrontier`):** `markFrontier()` overrides dynamic subset frontier calculation with the precomputed 21-point global frontier whenever `ARDF_ANALYSIS.frontier` is non-empty, so filtering by provider or open-weights highlights which of the 21 global frontier models survive the filter rather than computing a new sub-frontier over the filtered subset.
2. **`$0`-cost models (`p.x === 0`) in `dashboard-template.html`:** `paired` filters `p.x > 0` (required for log-scale plotting) while `unpriced` filters `p.x === null`, leaving two `$0`-cost rows (`K2 Horizon 375B A23B` at score `17.73` and `North Mini Code` at score `3.42`) in the Priors/AA cross-check table (`docs/current-frontier.md`) rather than on the positive-cost scatter canvas or unpriced shelf.
3. **Partial-benchmark models in `aa-primary.json.gz`:** `current_frontier.py` computes the v4.2 average only when all 10 v4.2 sub-benchmarks are present (116 models). Two additional models (`Gemini 3.8 Flash (Low)` at `22.55` and `Gemma 4 31B (Reasoning)` at `4.38`) have published `intelligenceIndex` in `aa-primary.json.gz`, and 589 older/partial models have 6 to 9 sub-benchmarks that remain `use_in_aggregate=0` unless multipoint-calibrated onto v4.2.

---

## Part I-B - 2026-11-17 MVP pass, ARDF-REC-02 (HTML presentation), for owner review

Authorised by the owner's 2026-11-16 MVP instruction ("fix the ardf html page"; reviews follow the build). Finding 5 above had been held back pending review; items 2 and 3 are now addressed, item 1 is addressed for the new panel only. Please review these methodology changes:

1. **Misleading current/historical framing replaced.** The page called an embedded Priors snapshot "current" and the whole calibrated ledger "generated in August 2026 ... not a current model ranking". That was false for v7.5.0: the ledger is rebuilt on every `python3 calibrate.py` and carries the November AA v4.2 rows. The page now leads with a **primary current frontier** panel (AA v4.2 recomputed by ARDF, source `aa-primary-current`, 734 catalog configurations, 116 fully scored). Priors is relabelled an external cross-check and never feeds ARDF scores. A ledger-vintage note is generated from the embedded observations (current vs reference-only vs historical counts). The August essay is kept verbatim inside a closed, labelled archive block; its hardcoded 14-point frontier list is no longer presented as current.
2. **Zero is a price, unknown is not zero** (Finding 5, item 2). The primary panel keeps $0 configurations in the comparison (Command A+, K2 Horizon 375B A23B, North Mini Code) on a labelled $0 shelf, and lists scored configurations with no published cost (Granite 4.2 3B, K-EXAONE 2.0, Muse Wonder Full (Max), Nanbeige4.3-33B, NVIDIA Nemotron 3 Nano 4B) as unpriced, outside the chart and dominance. Counts are displayed. Note this widens Finding 5 item 2: there are three scored $0 rows, not two. The legacy ledger plot (`combineCosts` requires cost above 0) is unchanged and still cannot plot $0.
3. **Filters recompute the frontier** (Finding 5, item 1, new panel only). The primary panel computes the frontier within the filtered selection and across all configurations; the legacy plot's static 21-point override (`markFrontier`) is unchanged.
4. **Offline tier weighting.** Tier multipliers (S, A, B, C, Unrated; 0 to 5) re-score every configuration in the page from embedded per-benchmark AA components. No network and no Priors value is used. A multiplier of 0 removes a tier and can let configurations lacking those benchmarks be scored (116 scored at default, 133 with only the B tier). The Priors panel's own reweighting still needs mypriors.com.
5. **Deterministic build.** `generated_at` was a microsecond timestamp inside `dashboard.html`; it is now a calendar date (`SOURCE_DATE_EPOCH` pins it). Two consecutive builds are byte-identical (same SHA-256 for CSV, tiers, cheatsheet and dashboard).
6. **Committed generated files were stale against the committed generator.** At commit 3752a90 the tiers document and cheatsheet did not match what `calibrate.py` produces (for example Claude Fable 5.2 Xhigh 60.53 committed vs 62.22 regenerated), and the CSV differs from a rebuild only in last-digit float noise (for example `0.24567387882790453` vs `...56`), consistent with a different libm or Python on the committing host. This pass commits the regenerated files.

7. **ARDF-REC-01 (primary AA refresh): not refreshed, recomputed offline.** No live refresh was attempted. The keyed "authorized AA v2 API" path is the one the dossier records as HTTP 410, and the keyless public-page path needs a decoder that is not in this repository (`current_frontier.py` reads pinned snapshots only) plus a network request this session could not approve. Offline recomputation from the pinned 2026-11-10 snapshot: all 734 configurations preserved (734 snapshot models, 734 unique slugs, 734 `aa-primary-current` catalog rows in the CSV, enforced by a build assertion; the dossier's 725 was the 2026-11-04 public-page count); 116 have a complete 10-benchmark composite. Recomputed workload cost equals AA's published cost on all 111 priced rows (max difference 3.6e-15 USD). Recomputed composite differs from AA's published `intelligenceIndex` by at most 0.2824 points (15 of 116 differ by more than 0.1; largest Qwen3.8 Max (0902) 33.3722 vs 33.6546). Versus Priors (API basis) the difference is at most 0.004967 points on 93 of 100 rows, which is Priors' two-decimal rounding; exact rows in `docs/priors-deltas.md`. **Caveat for owner review:** the composite weights (15/5/10/15/10/5/5/10/10/15) are the owner-selected Priors index weights, so agreement with Priors is expected by construction and does not validate those weights; AA's own published index is the independent comparator and differs by up to 0.28.

Reproduce: `python3 calibrate.py && python3 tests/verify_dashboard.py` (needs Chromium; add `--screenshot out.png`).

## Part II - Historical v7.3 -> v7.4 Audit Record (Preserved)

### Cluster 1 - Policy / code alignment (Green)
- `project-config.json: analysis.top_end.same_source_diagnostic` aligned to *"AA Intelligence Index vs direct Cost per Intelligence Index Task (full-evaluation cost as fallback)"*.

### Cluster 2 - Cheatsheet provenance (Green)
- Generated headers point to `calibrate.py` and `project-config.json`.

### Cluster 3 - Standardized proxy version hygiene (Green)
- `augment_standardized_cost()` regenerates `standard-task-price-proxy-v7` rows deterministically from current catalog list prices (`854` rows in v7.5.0).

### Cluster 4 - `models.dev` empty-field disclosure (Green)
- Upstream-unpopulated `models.dev` fields (`models_dev_experimental`, `models_dev_input_limit_tokens`, `models_dev_interleaved`, `models_dev_interleaved_field`, `models_dev_reasoning_price_per_m`) are documented in `project-config.json: models_dev_coverage_note` without inventing values.

### Cluster 5 - Dispersion and 6-MAD scale outlier quarantine (Green)
- Rescued from the `2026-08-20` calibration audit (`calibrate.py` lines 849-915): per-model `capability_std_err`, `capability_std_dev`, `capability_spread`, and `capability_provisional` (`n < 3`) are computed as selector metadata, and observations more than `6.0` MADs from a model's median (when `n >= 4`) are quarantined before aggregation.

### Cluster 6 - Self-contained embedded dashboard (Green)
- `dashboard.html` embeds `window.ARDF_DATA` and `window.ARDF_ANALYSIS` directly from `dashboard-template.html`, eliminating external `generated/` script dependencies under `file://`.
