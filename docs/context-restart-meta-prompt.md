<!--
---
title: ARDF Living Model-Evidence System — Context Restart Meta-Prompt
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
purpose: Comprehensive restart prompt carrying the full design intent, accumulated corrections, failure lessons, and deliverable contract into a fresh agent session.
---
-->

# Context restart meta-prompt

Use this prompt together with the latest ARDF ZIP. Treat the package as an existing code/data project that must be **revised in place**, never replaced by a clean-room rewrite unless the package is genuinely unrecoverable.

---

## Your role

You are maintaining a living evidence and routing-analysis system for comparing frontier, workhorse, lightweight, open-weight, and proprietary AI models. The system is called **ARDF** in the package lineage. Its purpose is not to produce a decorative leaderboard. Its purpose is to make model routing decisions from inspectable empirical evidence while preserving enough raw provenance that future agents can refresh, challenge, recalibrate, and reinterpret the analysis.

The user is specifically interested in:

1. **Capability versus real task economics.**
2. **One dense universe containing every model × reasoning/effort configuration**, not only Pareto winners.
3. **Strict Pareto-optimal models**, plus the important models that narrowly miss the frontier.
4. **Operational capability tiers** that make frontier misses easier to interpret.
5. A special **executor-value shortlist**: models that are unusually capable for their real task price and therefore make good worker/executor models in a multi-agent system.
6. A separate **Claude Code/native Anthropic configuration view**.
7. Enough static model metadata and source provenance that a later agent can understand every dot without reverse-engineering the code.

Do not collapse these distinct questions into one scalar ranking.

---

# I. Authority hierarchy

When package components disagree, use this authority order:

1. `data/unified-model-evidence.csv` — canonical atomic evidence and catalog ledger.
2. Current first-party source pages/API responses and current independent benchmark records.
3. `config/calibration-algorithms.json`, `config/analysis-policy.json`, and `config/dashboard-views.json` — explicit policy/math configuration.
4. Generated data under `generated/` — reproducible outputs of scripts, not independently edited sources.
5. HTML dashboards — display/controller only; they must not own benchmark values or fitting math.
6. Markdown prose and validation reports — documentation; update them if they diverge from the canonical CSV.

Never hand-edit generated frontier lists or benchmark coordinates in HTML.

---

# II. Artifact contract

Preserve the organized ZIP project. The user wants a **single downloadable ZIP**, not embedded ChatGPT frame rendering. Direct file links are acceptable, but do not inline-render the dashboard in the conversation.

The package must contain at minimum:

```text
README.md

dashboard.html                         # all-model living universe
dashboard-claude-code.html             # Claude Code/native Anthropic view
calibration-studio.html                 # interactive calibration workbench
source-methodology.html                 # searchable source-acquisition manual

data/
  unified-model-evidence.csv            # THE ONLY CSV in the package

config/
  calibration-algorithms.json
  analysis-policy.json
  dashboard-views.json
  source-acquisition-manifest.json

generated/
  dashboard-data.js
  unified-evidence-csv.js
  calibration-report.json
  analysis-data.js
  analysis-data.json

scripts/
  calibrate.py
  augment_cost.py
  build-analysis.py
  render-pareto-cheatsheet.py
  build-package.py                  # deterministic downstream orchestrator
  sync_models_dev.py
  refresh-source-manifest.py
  render-source-cheatsheet.py
  update-YYYY-MM-DD.py                  # dated release/source refresh adapter
  validation script(s)

docs/
  methodology.md
  source-acquisition-cheatsheet.md
  pareto-executor-cheatsheet.md
  context-restart-meta-prompt.md
  current-model-refresh.md
  validation-report.md

sources/
  source-ledger.json
  raw/ or preserved source snapshots where practical
```

**Exactly one CSV** is intentional. Additional structured products should be JSON/JS/config files, not parallel competing CSVs.

All scripts should be heavily commented for later revision agents. Include YAML metadata in the language-appropriate comment form, including model name and reasoning level used to create/revise the file.

---

# III. Canonical CSV design

The CSV is long-form, atomic, and source-aware. Every numerical evidence row is one metric on one axis.

Canonical observation grain:

```text
model_key × effort/reasoning × harness × source_id × metric_name × source_date
```

Three record classes may coexist in the one CSV:

```text
record_type=catalog       static model/configuration identity
record_type=observation   one capability OR cost observation
```

Catalog rows have no invented metric values.

Every observation must be either:

```text
metric_axis=capability
metric_axis=cost
```

Never make a row simultaneously represent capability and cost.

Missing values stay blank/null. Never zero-fill unknown data.

Important field groups:

### Identity

`record_type`, `observation_id`, `model_key`, `display_name`, `provider`, `family`, `effort`, `harness`, `official_model_id`, release/availability fields.

### Provenance

`source_id`, `source_original_id`, `source_label`, `source_publisher`, `source_version`, `source_date`, `source_url`, `source_mirror_url`, `retrieved_at`, `source_refresh_status`, `data_freshness_class`.

### Raw metric

`metric_axis`, `metric_name`, `raw_value`, `raw_unit`, `raw_direction`, benchmark domain/harness/version fields.

### Evidence policy

`quality`, `confidence`, `base_weight`, `use_in_aggregate`, `is_historical`, `is_vendor_reported`, `is_independent_source`, `identity_mapping`, `notes`.

### Calibration outputs

At least:

```text
cal_robust_affine
cal_huber_affine
cal_monotone_piecewise
calibrated_score
```

Each algorithm should carry status, anchor count, RMSE/residual metadata, and group key fields.

### Static model metadata

Retain the full `models_dev_*` envelope and expand it when models.dev adds useful fields.

---

# IV. models.dev policy

Use **models.dev as the primary static metadata backbone**, not as benchmark evidence.

For every model/configuration, acquire as much models.dev information as practical, including all fields exposed by the current schema. The project currently carries roughly fifty flattened fields and should expand rather than contract.

Important classes include:

- canonical model/provider IDs
- lab/family
- description
- release/update dates
- lifecycle/status/experimental state
- knowledge cutoff
- context/input/output limits
- input/output modalities
- reasoning options
- tools/function calling
- structured output
- attachments
- temperature/interleaving flags
- open-weight state and license
- input/output/cache/reasoning/audio pricing
- provider count and provider-specific rows
- min/max provider pricing
- parameter counts when known
- model/provider links
- provider availability and routing IDs
- raw provider-row JSON for fields not yet flattened
- exact/fallback identity match status

Static metadata is used for hover information and filters, never as an independent capability vote.

Be conservative with identity matching. Label exact matches versus compatible/local fallbacks. Do not claim a canonical models.dev match when only a provider-specific entry exists.

---

# V. Source acquisition policy

Maintain **one latest comparable slice per source**. Do not give Artificial Analysis from last month and Artificial Analysis from today two votes merely because both snapshots exist.

When refreshing a source:

1. Prefer API, downloadable CSV/JSON/Parquet, or repository result files.
2. Scrape HTML only when no structured route exists.
3. If scraping, document the exact page/table and expected fields.
4. Preserve `source_original_id` and retrieval provenance when normalizing old dated source IDs into a living source ID.
5. Import a **complete relevant source table/slice**, not two hand-picked celebrity models, whenever feasible.
6. Mirrors can verify evidence but must not duplicate the same underlying score in aggregation.
7. Vendor-published benchmark tables may be retained, but mark them vendor-reported and apply lower default weight than genuinely independent sources.
8. Target at least ~8 empirical data points for important newly released models when practical. This may require 12–15 benchmark/source families overall because not every source covers every model.

Keep `docs/source-acquisition-cheatsheet.md`, `source-methodology.html`, `config/source-acquisition-manifest.json`, and `sources/source-ledger.json` synchronized.

The source manual must explain for every source:

- exact pages/endpoints
- API/CSV/scrape/repository method
- authentication requirements
- available fields
- fields currently ingested
- metadata/capability/cost/token/runtime coverage
- post-ingestion schema mapping
- known omissions
- unused data available at the same source
- source freshness and update cadence
- identity keys
- caveats
- refresh priority
- future sources that could add orthogonal evidence

Promising future source families include official SWE-bench, official Terminal-Bench, BFCL/Gorilla, Aider Polyglot, LiveCodeBench, Epoch AI, LMArena, OpenRouter provider/performance APIs, HELM, OSWorld, BigCodeBench and METR. Verify current availability before ingesting.

---

# VI. Calibration math must live outside HTML

The user explicitly wants calibration logic outside the dashboard.

Use `scripts/calibrate.py` as the reproducible authority. The dashboard should consume already-calibrated values.

Support multiple calibration algorithms, at least:

1. **Robust affine / Theil-Sen** — default production mapping.
2. **Huber IRLS affine** — robust regression alternative.
3. **Monotone piecewise** — isotonic/PAV plus piecewise interpolation for nonlinear/compressed source scales.

Cost calibration should happen in log space because cost relationships are multiplicative.

Use **multipoint calibration** through overlapping model identities. Do not permanently pin everything to one model. Partial overlap is expected and is the reason multipoint bridges exist.

Calibration Studio should allow a human/agent to:

- inspect automatic anchors
- add/remove manual anchors
- change weights
- change fit constants
- preview residuals
- switch algorithms
- add a new algorithm configuration
- create new calibration columns automatically
- export updated config and recalibrated CSV

The Python engine remains the authoritative reproducible implementation.

Script naming is strict: `calibrate.py` performs calibration only; `augment_cost.py` creates derived cost observations; `build-analysis.py` derives decision products; `render-pareto-cheatsheet.py` only renders those products; `build-package.py` orchestrates the full deterministic downstream build. Do not recreate an ambiguous `rebuild.py` wrapper. Network acquisition/source scraping is performed before the deterministic build through dated adapters or saved raw source snapshots.

---

# VII. Capability aggregation

The main Y coordinate is a **calibrated AA-equivalent capability/completion index**, not literal human IQ.

Use source-weighted aggregation of calibrated capability observations. The default implementation uses a weighted arithmetic mean.

Do not interpolate unmeasured reasoning levels merely to fill a prettier family curve.

Do not allow a variant with more benchmark coverage to be called intrinsically better solely because it has more source rows. This matters especially for effort comparisons. For same-family reasoning-effort analysis, prefer a same-source capability curve such as exact current AA Intelligence Index where available.

---

# VIII. Task-cost / X-axis hierarchy

The central question is not token price alone. The X coordinate should approximate **price per completed/evaluated task**.

Use this best-available cost hierarchy:

1. direct current AA cost per task or equivalent direct task measurement
2. observed benchmark cost per task / cost per successful task
3. model-specific measured token use × current token prices
4. standardized task token-price estimate
5. other calibrated monetary evidence

Never hide which level produced the coordinate.

Keep the standardized task estimator low-weight and configurable. It exists to keep the universe visible, not to impersonate direct measured cost.

If no defensible price exists, do not invent one. Keep the configuration on the visible **unpriced shelf**.

If no capability exists, keep it on the visible **unscored shelf**.

---

# IX. Muse Spark 1.2 pricing policy

This is a project-specific override and must persist unless the user changes it.

For **Muse Spark 1.2**, preserve both Meta price tiers but use the lower **Contributor/data-sharing** tier as the primary economic coordinate because the user explicitly prefers it.

Primary Contributor tier:

```text
model ID: muse-spark-1.2-contributor
input:     $0.10 / 1M tokens
cache read:$0.002 / 1M tokens
output:    $0.20 / 1M tokens
meaning:   prompts/data may be used to improve Meta products
```

Secondary Standard/no-sharing tier:

```text
model ID: muse-spark-1.2
input:     $1.25 / 1M tokens
cache read:$0.15 / 1M tokens
output:    $4.25 / 1M tokens
meaning:   prompts/data not used to improve Meta products
```

Never average these tiers.

Artificial Analysis currently evaluates Muse at the Standard tier. If direct Contributor task-cost measurements are unavailable, transparently reprice the **same AA workload** to Contributor pricing. The current v7.3 derived coordinate is approximately:

```text
$0.02123 per AA-equivalent task
```

This is **derived/repriced**, not a direct AA Contributor billing observation. Keep the Standard AA `$0.40/task` observation as secondary evidence, not the primary project coordinate.

Current Muse capability should use the latest AA composite, not an older launch-day composite. Keep component metrics as independent evidence where nonduplicative.

---

# X. GPT-5.6 Luna pricing and effort policy

The July 30, 2026 Luna price drop must remain current:

```text
standard short-context input:      $0.20 / 1M
cached input:                      $0.02 / 1M
cache write:                       $0.25 / 1M
output:                            $1.20 / 1M
```

Do not resurrect the old `$1/$6` pricing.

For literal executor **price/performance**, the current recommended Luna effort is **`high`**. `xhigh` remains a capability knee; `max` is the quality-first setting.

Reason: compare effort levels using the same AA source:

```text
high:  47 AA-equivalent reference capability
xhigh: 50
max:   52
```

Under the current standardized workload:

```text
high  raw task estimate ≈ $0.01224
xhigh raw task estimate ≈ $0.01701
max   raw task estimate ≈ $0.02838
```

Recompute calibrated task-price coordinates from the current CSV on every build. Under v7.3 the literal `$ / calibrated-capability` ranking makes **high** the Luna price/performance winner. High → xhigh still buys +3 exact AA points and xhigh → max +2, so xhigh may be chosen when the marginal capability gain is worth the extra price, but do not call it the ratio winner.

Recalculate these if source data or the standardized workload changes.

---

# XI. Main dashboard visual contract

The main graph must be useful at first glance, not a 10-dot postcard.

Default mode:

- one dot for **every cataloged model × effort/reasoning configuration**
- model names visible by default
- current and historical models included unless filtered
- hundreds of ordinary dots are expected
- unpriced models remain visible on an unpriced shelf
- unscored models remain visible on an unscored shelf
- Pareto frontier is an **overlay**, never the only visible data

Also provide Evidence Cloud mode that shows individual calibrated capability observations against each configuration’s task-price coordinate.

Hover must show:

- display/canonical model identity
- provider/lab/family
- reasoning/effort/harness
- release/update dates and lifecycle
- context/output limits
- modalities
- tools/structured output/attachments/reasoning
- open/closed weights and license
- provider count and relevant pricing
- calibrated capability
- task-price coordinate and provenance
- Pareto status/dominator
- all selected raw and calibrated evidence rows
- source links, quality, confidence, weights, and dates

Click should pin the complete evidence record.

Filters should include at least:

- source/dataset combinations
- capability and cost source filters independently
- calibration algorithm independently for both axes
- provider/lab/family
- effort/reasoning level
- harness
- release date range
- evidence date range
- current/recent/legacy status
- open/closed weights
- models.dev exact/fallback match
- license
- context minimum
- output limit minimum
- provider count minimum
- modalities
- reasoning/tool/structured/attachment support
- evidence quality
- paired/unpriced/unscored state

Both axes must have **independent linear/logarithmic toggles**.

Do not embed acquisition/calibration math in the dashboard.

---

# XII. Strict Pareto frontier

The strict empirical frontier is derived from observed/precomputed points. Do not draw a regression or fitted theoretical envelope.

Sort paired points by increasing task cost. Retain a point only if its capability is strictly greater than every cheaper/equal retained point.

A model is dominated when a different observed configuration has:

```text
cost <= candidate cost
AND
capability >= candidate capability
```

with at least one strict inequality.

Dominated configurations remain visible.

The dashboard must fail validation if a future change silently renders only frontier points or shrinks the visible universe through an accidental inner join.

---

# XIII. Capability tiers

Strict Pareto membership alone is too binary. Maintain operational capability tiers based on the multi-source calibrated Y coordinate.

Current v7.3 policy:

```text
S+  >= 60   Frontier ceiling
S   >= 56   Frontier
A+  >= 52   Premium executor / near-frontier
A   >= 47   Strong executor
B   >= 40   Workhorse
C   >= 30   Light workhorse
D   >= 0    Utility / lightweight
```

These thresholds are policy, not natural law. Keep them editable in `config/analysis-policy.json` and document any changes.

---

# XIV. Near-frontier analysis

For every important non-frontier configuration, identify the **closest frontier point that dominates it** and report:

- candidate capability tier
- candidate capability
- candidate task price
- dominating frontier model
- capability gap
- price premium percentage
- cost ratio
- verdict

Current interpretation bands:

```text
razor-edge miss:
  capability gap <= 0.75
  AND price premium <= 25%

near-frontier:
  capability gap <= 2.0
  AND price premium <= 50%

capability-close / price-heavy:
  capability gap <= 2.0 but price premium is larger

price-close / capability-behind:
  price premium <= 50% but capability gap is larger

economically dominated:
  neither condition is close
```

Always explicitly inspect prominent models such as:

- Qwen3.8 Max
- Claude Fable 5
- GPT-5.6 Sol
- Kimi K3
- Claude Sonnet 5
- DeepSeek V4 Flash 0731
- GPT-5.6 Luna
- Grok frontier/workhorse variants
- Gemini Pro frontier variants
- MiMo-V2.5-Pro

This directly answers whether a famous model barely misses the line or is economically far below it.

---

# XV. Executor-value analysis

The executor shortlist is **not the same thing as the strict Pareto frontier**. Pareto is a dominance relation; the executor list is a scalar ranking intended for the high-volume worker role.

The user explicitly requires literal price per capability:

```text
minimum multi-source capability = 45
price_per_capability = calibrated_task_cost / calibrated_capability
lower_is_better = true
capability_per_dollar = calibrated_capability / calibrated_task_cost
```

Do **not** use square-root cost, a capability subtraction, a hand-created bonus, or a forced model slot. Exact AA capability may be displayed as a secondary same-source diagnostic, but it does not replace the multi-source numerator used by the primary executor ratio.

Collapse effort siblings only when presenting the top-five *models*: keep the best literal ratio from each family. Preserve the full effort table separately.

Current v7.3 expected executor-grade order, subject to deterministic recalculation after every source refresh:

1. Muse Spark 1.2 xhigh — Contributor/data-sharing economics
2. GPT-5.6 Luna high
3. DeepSeek V4 Flash 0731 max
4. Grok 4.3 high
5. MiniMax-M3

MiMo-V2.5-Pro must **not** be promoted using the stale 54 score. Current AA is 43, so it currently falls below the 45 executor eligibility floor. DeepSeek V4 Pro is the Preview model; its current aggregate/AA level likewise does not justify silently forcing it into the shortlist.

For every executor candidate show:

- multi-source calibrated capability
- exact/current AA reference when available
- calibrated task cost
- raw direct/observed/estimated cost class
- literal `$ / capability` and `capability / $`
- price ratio versus Muse Contributor
- input/output API pricing and pricing tier
- context/output limits and static models.dev metadata
- evidence/source count
- Pareto status and closest dominator
- disagreement flags when AA and multi-source aggregate materially diverge
- specialist reasons the nominally dominated model may still win a real workload

Also show the **global no-floor** price/performance list so the effect of the 45-point eligibility threshold is transparent.

---

# XV-A. Identity hygiene for high-value candidates

Before calibration or routing, resolve exact checkpoint identity.

**DeepSeek V4 Pro:** all current Pro evidence belongs to the Apr. 24 **DeepSeek V4 Pro Preview** checkpoint unless DeepSeek explicitly publishes a final Pro release. The Jul. 31 `V4-Flash-0731` update changed/promoted Flash while DeepSeek stated Pro remained unchanged and the official Pro release was forthcoming. Do not infer a final Pro from API availability.

**MiMo:** keep these separate:

- MiMo-V2.5 — current AA 38
- MiMo-V2.5-Pro — current AA 43
- MiMo-V2-Pro — older predecessor
- non-reasoning/provider/UltraSpeed variants when measurements differ

Merge only genuine aliases such as the old `mimo-v2-5-0424` row into canonical MiMo-V2.5. Never copy a score across similarly named variants.

---

# XV-B. Top-end routing/pruning surface

Treat the highest-cost capability region as a separate decision problem because small routing mistakes are expensive. Always audit at least:

- Claude Opus 5, all measured reasoning/effort levels
- Claude Fable 5, all measured levels
- GPT-5.6 Sol, all measured levels
- Qwen3.8 Max, measured levels
- Kimi K3, measured levels

Emit two planes:

1. **ARDF operational plane:** multi-source calibrated capability vs operational task cost.
2. **AA same-source effort plane:** exact current AA Intelligence Index vs full AA Intelligence Index evaluation cost.

The second plane exists specifically to eliminate source-density bias when comparing effort levels. A configuration dominated within its own family should normally be removed from default routing unless a specialist source proves a compensating advantage. Current regression example: **Opus 5 max is dominated by Opus 5 xhigh** on the exact AA plane because both score 63 while xhigh costs less to evaluate.

Do not equate 'not on the general ARDF frontier' with 'useless'. Sol, Kimi K3, Fable and Qwen may be preferred on specific coding, economic-work, latency, reliability or open-weight criteria. Preserve near-frontier regret and source-specific performance.

---

# XV-C. External Pareto cross-checks

In addition to the synthesized ARDF frontier, preserve source-native cost/performance graphs when the source provides paired metrics. These graphs are diagnostics and must **not** be averaged together in raw units.

Required current cross-checks:

1. **Artificial Analysis:** AA Intelligence Index vs Cost per Intelligence Index Task. AA now exposes its own public Pareto line. Prefer the structured AA model/API values; the graph is a validation view, not a reason to scrape pixels.
2. **KiloBench:** coding-agent completion rate vs cost per attempt. Import the complete current leaderboard slice.
3. **Vals Index:** Vals accuracy vs Cost/Test. Import the current paired slice and retain other Vals task/latency dimensions separately.

For each source-native graph:

- label every point/model
- show the observed non-dominated frontier
- preserve the source's native X/Y units
- provide hover with exact source values, date, harness/version and model identity
- state clearly that the source-native graph is not the ARDF calibrated plane
- highlight disagreements with ARDF because they reveal task specialization rather than hiding them

# XVI. New-release refresh behavior

On every refresh:

1. Determine the latest release date represented by exact models.dev/catalog records.
2. Search models.dev, current Artificial Analysis models, first-party model announcements, and benchmark directories for releases after that cutoff.
3. Add new model identities as separate configurations, including reasoning/effort variants when explicitly measured.
4. Do not conflate preview/stable or dated revisions. Example: `DeepSeek V4 Flash 0731` is distinct from earlier V4 Flash.
5. For a new model, aggressively seek multiple independent sources. Import full relevant source tables where possible.
6. Add models.dev static metadata and provider pricing.
7. Rebuild cost proxies only from current price data.
8. Recalibrate all source groups.
9. Regenerate Pareto/tier/near-frontier/executor analysis.
10. Update source and validation documentation.

Current post-v7.1 / immediate-delta models already incorporated in the v7.3 lineage include:

- **LFM2.5-2.6B** — 2026-08-04; benchmarked but intentionally unpriced for hosted-task economics.
- **Ling 3.0 Flash FP8** — 2026-08-04; keep separate from the Jul-23 BF16/base model and never copy BF16 scores/pricing onto the quantized checkpoint.
- **Muse Spark 1.2** — 2026-08-05; Contributor/data-sharing pricing is the user-selected primary economic tier.
- **Hark Handoff** — 2026-08-05 research preview; currently unscored/unpriced rather than estimated.
- **Ling 3.0 Tiny** — 2026-08-06; promotional $0 pricing is visible but excluded from Pareto denominator.

The same audit corrected omitted-current entries including **Ling 3.0 Flash BF16/base** and **Pokee-Isaac 28B v0**. Treat quantized checkpoints, preview/stable releases and dated revisions as separate identities when measurements differ.

Before claiming no newer model exists, verify the current date and live catalogs.

---

# XVII. Known failure modes you must not reintroduce

These failures occurred in earlier iterations:

### Failure: tiny 10–15 point graph
Cause: hidden inner join required both capability and directly measured cost, then emphasized only the Pareto subset.

Fix: every catalog configuration remains represented; task-cost fallback hierarchy and unpriced/unscored shelves prevent disappearance.

### Failure: graph flashes then disappears
Cause: HTML referenced `generated/dashboard-data.js` and `generated/unified-evidence-csv.js`, but the ZIP omitted `generated/`.

Fix: validation must assert every referenced generated file exists inside the ZIP and JavaScript parses before packaging.

### Failure: stale prices
Cause: catalog/proxy data preserved old provider prices after a provider price cut.

Fix: price refresh precedes cost proxy regeneration. Luna’s July 30 prices are a specific regression test.

### Failure: double-counting source mirrors
Cause: the same vendor result appeared through both the vendor and a benchmark aggregator.

Fix: choose one aggregation vote; preserve the mirror as display/verification only.

### Failure: “all evidence” meant only calibrated rows
Fix: hover/pinned inspection must show all selected raw observations, even if a source metric lacks a calibration bridge.

### Failure: undocumented estimates masquerading as measurements
Fix: direct, observed, model-token-priced, standardized-estimate, and other calibrated cost classes are explicit and separately filterable.

### Failure: arbitrary single-anchor calibration
Fix: use multi-overlap robust calibration and expose anchors/residuals.

### Failure: effort interpolation
Fix: never synthesize missing low/medium/high/xhigh/max capability points from a family curve unless a dedicated estimated field is explicitly requested and visibly labeled; default is null.

---

# XVIII. Validation contract

Before packaging, verify at least:

- exactly one CSV exists in the package
- canonical CSV parses and has unique catalog model keys
- observation IDs are unique
- every observation has one declared axis: capability, cost, or diagnostic metadata; metadata rows must be excluded from calibration/aggregation
- every current source in the CSV exists in the source ledger/manifest
- exactly one current consolidated slice exists for living sources such as AA
- all configured calibration columns are present and populated where mappings exist
- multipoint calibration groups have recorded anchor counts/residuals
- generated JS payloads exist and parse
- dashboard references resolve inside the ZIP
- both X and Y log/linear controls exist
- all catalog configurations are represented by the graph/shelves under default filters
- strict Pareto is recomputed from the canonical data and matches generated analysis
- new-release regression keys exist
- Muse uses Contributor pricing as primary while Standard remains retained
- Luna catalog/proxy rows use current Standard/short-context `$0.20/$1.20` pricing; Standard long-context and Batch short/long schedules are retained as secondary metadata, not silently substituted into the synchronous executor coordinate
- Ling promotional zero price does not enter logarithmic/Pareto cost aggregation
- source methodology and cheatsheets use current source IDs
- MiMo-V2.5 = AA 38 and MiMo-V2.5-Pro = AA 43 are regression-tested separately; the old V2.5 alias is absent
- all DeepSeek V4 Pro display/status rows are explicitly Preview until an official final release exists
- AA/Kilo/Vals source-native Pareto comparison data and dashboard graph containers exist
- Opus 5 max is not incorrectly retained as AA same-source optimal when xhigh has equal score at lower direct AA task cost
- build-package.py is the sole package orchestrator; calibrate.py remains the sole calibration engine; no ambiguous rebuild.py wrapper exists
- ZIP integrity passes

If Chromium/headless rendering is unavailable, do **not** claim pixel-level rendering was tested. Do static JS syntax/link/payload validation and state the limitation.

---

# XIX. Deliverables after a refresh

Return one updated integrated ZIP containing:

1. revised canonical CSV
2. revised all-model dashboard
3. revised Claude Code dashboard
4. revised Calibration Studio
5. revised source-methodology page
6. current calibration/config files
7. source ledger and acquisition manifest
8. `pareto-executor-cheatsheet.md`
9. this context-restart meta-prompt
10. current-model refresh notes
11. validation report
12. reproducible scripts and generated payloads

In the final chat response, do not embed/render the HTML. Give the ZIP download link and a compact factual summary of major changes/findings.

---

# XX. Current user intent in one sentence

Build a living, source-auditable, multi-calibrated AI-model evidence universe where **every model/reasoning configuration remains visible**, strict Pareto efficiency is only one overlay, famous near-misses are explicitly quantified, and the system identifies the models that buy the most useful executor capability per real task dollar — currently with special emphasis on **Muse Spark 1.2 Contributor pricing, DeepSeek V4 Flash 0731, GPT-5.6 Luna high for executor value, and the Opus/Fable/Sol/Qwen3.8/Kimi-K3 top-end routing surface**, with independent AA/Kilo/Vals Pareto cross-checks and strict checkpoint identity hygiene.
