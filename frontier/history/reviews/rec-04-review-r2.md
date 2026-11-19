# ARDF-REC-04 Round 2 Re-Review

Reviewer: Google (Gemini)
Target: `master` at `42f4e49` (fixes `c860566..6c7d1aa`, `MVP-PROGRESS.md`)

## Round-1 Finding Verification

### 1. Unverified $0 AA prices (`c860566`) - Fixed
`classify_cost_states()` (`ardf/current_frontier.py:147-174`, called at `ardf/calibrate.py:1253`) classifies `$0` as `zero-verified` only on an exact catalog free-route name match (keeping `+` as `plus`, so `Command A+` does not collide with `Command A`). `comparable()` (`ardf/current_frontier.py:49`), `ana_routing()` (`ardf/calibrate.py:1410-1414`), and `eligible()` (`ardf/dashboard-template.html:521`) exclude `zero-unverified` from dominance. `North Mini Code` (`3.42`, `$0`) stays in the 22-point frontier (`ardf/docs/full-frontier.md:13`); `GPT-6 Luna (Low)` (`9.67`, `$0.00512`) returns at rank 2 (`:14`); `K2 Horizon 375B A23B` (`17.73`) and `Command A+` (`6.24`) sit in `Unverified free` (`:89-96`). Both the 21-point paid-only frontier (`:36-62`) and `ardf/pareto-frontier-cheatsheet.md:8` match `cost > 0`, enforced at `ardf/calibrate.py:1970-1979`.

### 2. Free-route effort assumptions (`2ee39e6`) - Fixed
`catalog_routes()` (`ardf/current_frontier.py:93-142`) reads effort lists and defaults from OpenRouter, Kilo, and OpenCode Zen. `ana_free_routes()` (`ardf/calibrate.py:1324-1374`) restricts `aa_effort()` to literal levels (or `none` only when AA's name includes `non-reasoning`). `DeepSeek V4.1 Flash 1017` is `18.51 to 32.59` labelled `CEILING` with no catalog default (`ardf/docs/free-routes.md:11`; Rule 9 at `ardf/docs/routing-rules.md:24`). `Beam 1.0`, `MiMo-V2.6-Flash`, `Nemotron 3 Ultra 550B A55B (Reasoning)`, `Nemotron 3.5 Lightning`, and `North Mini Code` are `ASSUMED`; `GLM-5.3-Flash` and `Nemotron 3.5 Super VL` are `LISTED` (`ardf/docs/free-routes.md:12-18`). Asserted at `ardf/calibrate.py:1983-1987`.

### 3. HTML truncation, stale August text, Priors mismatch (`8979511`) - Fixed
`populateFrontier()` (`ardf/dashboard-template.html:378-389`) removes `.slice(0,14)` and displays all 21 ledger frontier rows. Stale August v4.0 prose at `:161-162` is replaced by `#lunaNote`, `#topEndFamilies`, and `#topEndExample` computed from `ARDF_ANALYSIS` (`:325-327`). The Priors chart uses `chartDominator=r=>dominator(r)` (`:685`), matching the table over all 85 plotted points (0 disagreements). `$0 shelf` renders only when `zeros.length > 0` (`:585-586`), and `#pc-table` adds a `Components` column (`:38,532,564`). Guarded by self-test checks (`:617-624,653`).

### 4. Routing rules 4 to 7 (`1de3ca5`) - Fixed
`ardf/calibrate.py:1444-1505` and `ardf/docs/routing-rules.md:13-20` resolve all four gaps: Rule 4 adds cost-ratio (`1.17x to 2.45x`) and gain (`-0.78 to +6.04`) ranges plus the `Claude Fable 5.1` regression; Rule 5 narrows to 53 within-family adjacent steps (2 regressions cited) and marks cross-model counts as context; Rule 6 reports 21 fallback tracks (20 scored, 1 unscored), 5 of 22 frontier members, and zero standard counterparts; Rule 7 states each provider's frontier score span without claiming interior coverage. `ardf/docs/full-frontier.md:7,11-87` adds `FALLBACK` tags, a warning, and an 18-point fallback-free frontier.

### 5. Priors circularity and AA divergence (`aba2cf2`) - Fixed
`ardf/docs/priors-deltas.md:5-29`, Rule 11 (`ardf/docs/routing-rules.md:27-28`), and `#priors-circularity` (`ardf/dashboard-template.html:50,504-505,625`) state that agreement is circular by construction (shared `15/5/10/15/10/5/5/10/10/15` weights on the same AA snapshot) and report AA `intelligenceIndex` divergence across 116 configs (median `0.0202`, max `0.2824`, 15 above `0.1`, top-10 table and per-row columns).

### 6. Cross-version determinism (`6c7d1aa`) - Fixed
Float summations use `math.fsum` (`ardf/calibrate.py:66-167,259-321,877-908,1210-1213`; `ardf/current_frontier.py:79,82,187`) and outputs round to 12 significant digits (`SIG_DIGITS=12`, `ardf/calibrate.py:213-228`) or 6 decimals (`ardf/calibrate.py:1648`).

## Verification & New-Issue Check

- `cd ardf && python3 calibrate.py` exited 0 and left `git status` clean.
- `python3 tests/verify_determinism.py --pythons 3.11 3.12 3.13` passed (`RESULT OK`) across Python `3.11.14`, `3.12.3`, and `3.13.11`: all 8 generated files are byte-identical, and `SOURCE_DATE_EPOCH` changes only the date stamp (`model-tiers-and-contenders.md` omits the date stamp and stayed identical across dates).
- Headless Playwright Chromium (cached `chromium-1234`, since `verify_dashboard.py` with `--virtual-time-budget=40000` stalled under Chrome 151) passed all 32 checks (28 in-page self-test + 4 Python parity checks) with 0 page errors. Screenshot inspection of `ardf/dashboard.html` confirms `734` configurations, `22` frontier points, `1` verified free point on the `$0 shelf`, and `unverified free 2` in the count line.
- **Cosmetic label overlap (`ardf/dashboard-template.html:591`):** Severity is **Low** (non-blocking). Parity y-offsets (`i%2 ? 14 : -8`) and `Math.min(X(r)+8, R-60)` overlap labels in the top-right cluster (`Claude Fable 5.2`, `Gemini 4 Carbon`, `Claude Opus 5.5`) and mid-band (`GPT-6.1 Terra low` / `Muse Ember xhigh`, `GPT-6.1 Terra high` / `GPT-6.1 Sol medium`), while clipping long right-edge labels. Full details remain legible in SVG tooltips and `#pc-table`.
- **Minor holdover prose:** `ardf/dashboard-template.html:161` still reads `Muse uses Contributor/data-sharing pricing as its primary economic coordinate` (true for August v4.0, superseded by `Muse Ember` in `ardf/pareto-frontier-cheatsheet.md:14`). Non-blocking.

## Verdict
**Sign-off.** All six round-1 findings are fixed and verified; no blocking regressions were introduced.
