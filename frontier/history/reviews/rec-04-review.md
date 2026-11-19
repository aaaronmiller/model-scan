# ARDF-REC-04 Adversarial Review (REC-01 to REC-03)

Reviewer: Google (Gemini)
Targets: commits `55be034` (REC-02), `ad6ab36` (REC-03), `32ad673` (REC-01) on `master`, `MVP-PROGRESS.md`, `ardf/ERRATA-and-findings.md`.

## Findings

### 1. Unverified $0 AA prices dominate paid models and split the frontier
- **Location:** `ardf/calibrate.py:1353`, `ardf/docs/full-frontier.md:11`, `ardf/pareto-frontier-cheatsheet.md:19`
- **Severity:** High
- **Scenario:** `ana_routing` keeps `cost == 0` in dominance, placing `K2 Horizon 375B A23B` ($0, 17.73) at rank 1 of `docs/full-frontier.md`. It dominates 23 configurations and solely removes 5 from the frontier, including `GPT-6 Luna (Low)` ($0.00512, 9.67), `Granite 4.2 8B` ($0.0405, 5.10), and `Mistral Small 4 (Reasoning)` ($0.0399, 4.30). Yet `K2 Horizon` has no route in the pinned Kilo, OpenRouter, or OpenCode Zen catalogs, and AA's other `$0` entry `Command A+` (6.24) is priced at $0.30/M input and $1.50/M output in `ardf/sources/current/openrouter-catalog.json.gz`. Meanwhile `pareto()` (`ardf/calibrate.py:247`) requires `cost > 0`, so `pareto-frontier-cheatsheet.md` keeps `GPT-6 Luna (Low)` on the 21-point frontier while `docs/full-frontier.md` drops it. Note: raw sub-scores confirm `K2 Horizon` (17.7336) and `Beam 1.0` (17.7319) are distinct measurements, not duplicates.
- **Fix:** Require a verified free catalog route (or explicit `$0` provenance) before `$0` enters dominance, and publish both paid-only (`cost > 0`) and `$0`-included frontiers consistently.

### 2. Free routes assume best-effort scores without catalog support
- **Location:** `ardf/calibrate.py:1317-1318`, `ardf/docs/free-routes.md:11`, `ardf/docs/routing-rules.md:23-24`
- **Severity:** High
- **Scenario:** `ana_free_routes` picks `max(scored, key=lambda h: (h['score'], h['id']))` across matching AA effort variants. `opencode/deepseek-v4.1-flash-free` thus receives `DeepSeek V4.1 Flash 1017 (Max)` at 32.59 (cited in Rule 9 as 50% of the top score and compared against `Muse Ember (Xhigh)` at $0.116), though OpenCode Zen specifies no effort. `Non-reasoning` scores 18.51 and `(High)` scores 28.64.
- **Fix:** Report `[min_effort, max_effort]` (or default to `none` when effort is unspecified) and mark 32.59 an unverified ceiling.

### 3. HTML truncates ledger frontier, keeps stale August text, and splits Priors chart vs table
- **Location:** `ardf/dashboard-template.html:373`, `ardf/dashboard-template.html:160-161`, `ardf/dashboard-template.html:661-666`
- **Severity:** High
- **Scenario:**
  1. `populateFrontier()` (`:373`) runs `frontier.slice(0,14)` while `#frontier-list` (`:79`) declares 21 points, hiding the top 7 ledger frontier models.
  2. Lines `:160-161` retain hardcoded August v4.0 prose (`GPT-5.6 Luna ... Lowest-price-per-capability Luna effort: high`; `Opus 5 max ... both score 63`), contradicting the live tables above them (`GPT-6 Luna (Low)` wins; `Opus 5 (Max)` scores 44.02).
  3. In `#priors-current`, `dominatorIn(rows)` (`:656`) includes `$0` rows (`K2 Horizon` dominates `GPT-6 Luna (Low)` in the table), whereas `chartDominator` (`:661`) checks only `plotted` (`Cost > 0`), plotting `GPT-6 Luna (Low)` on the API chart's frontier line.
  4. Minor: `#primary-current` (`:573-574`) draws the `$0 shelf` label even under `Cost = Priced`, `#pc-table` omits `N/10` component counts when a `0` multiplier admits partial models, and `markFrontier` (`:214-241`) pins the static global frontier on `#frontier-graph`.
- **Fix:** Remove `.slice(0,14)` at `:373`; update/remove hardcoded `:160-161` notes; evaluate `chartDominator` against `rows` at `:661`; hide `$0 shelf` when `zeros.length === 0`; show coverage in `#pc-table`.

### 4. Routing rules overreach cited data (Rules 4, 5, 6, 7)
- **Location:** `ardf/docs/routing-rules.md:13-20`, `ardf/docs/full-frontier.md:25-31`, `ardf/calibrate.py:1386-1418`
- **Severity:** Medium
- **Scenario:**
  - Rule 5 ("the frontier mixes every effort setting") cites cross-model frontier counts (`low 2, medium 5, high 6, xhigh 5, max 3`). `none` and `minimal` have 0 frontier members, and cross-model counts do not prove effort non-monotonicity; actual within-family regressions (`Claude Fable 5.1 (Max)` -0.78 vs `Xhigh`; `GPT-6.1 Terra (Low)` -1.08 vs `none`) go uncited.
  - Rule 4 cites median +2.01 (`max` vs `xhigh`) without the range (-0.78 to +6.04) or `Fable 5.1 (Max)` regressing at 1.20x cost.
  - Rule 6 flags Anthropic's 20 scored fallback tracks (21 total in AA including unscored `Fable 5`), and 5 of 6 Anthropic global frontier points are `Default Fallback` with zero scored standard counterparts, yet `docs/full-frontier.md` prints them without an inline warning or fallback-free sub-frontier.
  - Rule 7 omits provider band limits (`Google` 58.28-60.02 only; `Meta` 34.11-36.02 only; `Anthropic` above 18.64 is 100% fallback tracks).
- **Fix:** Cite within-family regressions in Rule 5, add ranges to Rule 4, state provider bands in Rule 7, and tag/separate fallback tracks in `docs/full-frontier.md`.

### 5. Priors agreement is circular and hides AA's own divergence
- **Location:** `ardf/docs/priors-deltas.md:5-7`, `ardf/docs/routing-rules.md:27-28`, `ardf/current_frontier.py:18-29`
- **Severity:** Medium
- **Scenario:** `current_frontier.py` uses Priors' own weights (`15/5/10/15/10/5/5/10/10/15`, `dashboard-template.html:48`) on the same AA snapshot. Agreement within 0.0050 points and $0.0039 is circular arithmetic parity plus Priors rounding. Only `MVP-PROGRESS.md:30` and `ERRATA-and-findings.md:55` disclose this; `docs/priors-deltas.md` and Rule 11 present it as independent agreement and omit AA's published `intelligenceIndex` divergence (up to -0.2824 on `Qwen3.8 Max (0902)`, 15 of 116 configs > 0.1).
- **Fix:** Disclose shared-weight circularity in `docs/priors-deltas.md` and Rule 11, and add AA published-index deltas.

### 6. Regression check: Python 3.11 vs 3.12 float noise breaks determinism
- **Location:** `ardf/calibrate.py:392,1521`, `ardf/current_frontier.py:72`
- **Severity:** Medium
- **Scenario:** `cd ardf && /usr/bin/python3 calibrate.py` (Python 3.12.3) exits 0 with assertions passing and clean `git status`. `cd ardf && python3 calibrate.py` (`.litellm/venv/bin/python3`, 3.11.14) exits 0 but dirties 52 rows of `ardf/docs/priors-deltas.md` and 4,321 rows of `ardf/data/unified-model-evidence.csv` in the 16th-17th decimal digit (`Muse Wonder (high)` 40.52503291856043 vs ...42), due to Python 3.12 compensated `sum()` and unrounded `repr()`. `tests/verify_dashboard.py` exited 3 (`NOT VERIFIED`: no Chromium binary).
- **Fix:** Use `math.fsum()` in `current_frontier.py:72` and `calibrate.py:66`, and format `priors-deltas.md` to 6 decimals.

## Verdict
**Request changes before sign-off.** Core AA recomputation and `#primary-current` are sound, but the 14-row frontier truncation, stale August notes, Priors chart/table mismatch, unverified `$0` dominance, max-effort free-route assumption, undisclosed Priors circularity in generated docs, and Python 3.11/3.12 non-determinism should be fixed first.
