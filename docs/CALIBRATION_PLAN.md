# Calibration & Empirical Validation Plan
## model-scan v5 — Post-Scoring-Engine Enhancements

**Date:** 2026-06-19
**Status:** Planning phase — tasks identified, not yet started

---

## The Problem

The scoring engine produces quantitative scores (AI Index, composite fitness) that
don't always match real-world performance. Some models may outperform or underperform their benchmark scores. This is unverified — see empirical_observations.md for the only validated data points.
as of 2026-06-19.
Nemotron 3 Ultra in practice). The goal is to calibrate the scoring system so that
quantitative scores match empirical human judgment.

---

## Phase 1: Data Collection Infrastructure

### 1.1 Cross-Reference AI Index with Architecture Data
**Source:** models.dev (GitHub: anomalyco/models.dev, dev branch, models.json)
**Data:** parameter count, architecture type (dense/MoE), release date, context window

Cross-reference AA Intelligence Index scores with model architecture stats to build
a predictive model: given arch, release date, and params → estimate AI Index.

Implementation: `scoring/arch_predictor.py`
- Pull model metadata from models.dev `models.json` (dev branch)
- Build regression model: AI_Index ~ f(params, release_date, arch_type, is_moe)
- Fill in missing AA data for models not yet scraped (North Mini Code, Nex N2, etc.)

### 1.2 User Sentiment Pipeline
**Sources:** X/Twitter, Reddit (r/ClaudeCode, r/LocalLLaMA, r/OpenAI), HN, forums
**What to collect:**
- "feels like" comparisons (model X is better than Y despite benchmarks)
- Loop frequency reports
- Clarification-request rates
- "Just works" sentiment signals

Implementation: `scoring/sentiment.py`
- Web scraper using httpx (model-scan already has this dependency)
- Store sentiment deltas per model per source with region tags
- Calibrate composite score by sentiment delta: `adjusted_score = base_score + sentiment_bonus`

**Priority models for sentiment scraping:**
1. DeepSeek V4 Flash vs Nemotron 3 Ultra (user reports Flash "feels better")
2. MiniMax-M3 (new #1, needs validation)
3. StepFun models (unverified — needs sentiment pipeline)
4. Qwen 3.x series
5. GLM 5.x series
6. Gemini models (unverified — needs sentiment pipeline)
7. Gemma 4 series

### 1.3 Chinese Model Paper Benchmarks
**Papers to collect:**
- Kimi K2.6 — Moonshot AI (release paper benchmarks)
- GLM 5.2 — Zhipu AI
- Qwen 3.7 — Alibaba
- MiniMax M3 — MiniMax
- DeepSeek V4 — DeepSeek

**Benchmarks commonly referenced in these papers:**
- SWE-bench (coding agent tasks)
- BFCL (Berkeley Function Calling Leaderboard)
- Arena ELO (Chatbot Arena)
- MMLU-Pro (knowledge)
- MATH (mathematical reasoning)
- HumanEval (code generation)
- LiveCodeBench (real-world coding)

Implementation: `scoring/paper_benchmarks.py`
- Parse paper benchmark tables
- Align with existing scoring axes
- Flag models overfitted to specific benchmarks

---

## Phase 2: Calibration Mechanics

### 2.1 Conditional Scoring System
When AA data is missing for a model, estimate from:
- Architecture type (dense vs MoE)
- Release date (newer models tend to score higher)
- Parameter count (more params → higher IQ, with diminishing returns)
- Context window size
- Known lab quality factor (some labs consistently over/underperform)

Implementation: modify `scoring/engine.py` to accept fallback estimator
```python
def estimate_ai_index(arch_type, params, release_date, ctx_window, lab):
    """Estimate AI Index when AA data is unavailable."""
    ...
```

### 2.2 "Magic" Factor Tracking
Some models outperform benchmarks consistently. Track this as a modifier:
- `mod_magic_factor(model_id) → delta_score`
- Stored in `empirical_adjustments.json`
- Updated via user sentiment pipeline
- Applied as a modifier in the scoring engine

### 2.3 Benchmark Overfitting Detection
Flag models where paper benchmarks significantly exceed real-world performance:
- High benchmark score + low community sentiment = possible overfit
- Low benchmark score + high community sentiment = possible sleeper
- Store as `overfit_penalty` modifier

### 2.4 Calibration Against Real Error Logs
Source: model-scan's own probe data + Hermes gateway error logs
- Track per-provider, per-model error rates
- Identify models with high failure/loop rates despite good scores
- Adjust composite score downward for unreliable models

Implementation: `scoring/reliability_calibration.py`
- Read error logs from `~/.hermes/logs/` or gateway error data
- Compute reliability factor per model
- Apply as modifier in scoring engine

---

## Phase 3: Tooling & Commands

### 3.1 `model-scan overall` Command
CLI command that returns a single model ID for a given tier/criteria:
```bash
model-scan overall -a          # Best A-tier model (any provider)
model-scan overall -a --free   # Best A-tier free model
model-scan overall -t S        # Best S-tier model
```

Implementation: `cli_overall.py`
- Query SQLite for best composite score matching criteria
- Return model_id as plain text (for piping to scripts)
- Used by git-audit-sync, Hermes config, and other tools

### 3.2 `model-scan calibrate` Command
Interactive calibration mode:
```bash
model-scan calibrate --weights    # Adjust axis weights and test against known-good configs
model-scan calibrate --sentiment  # Re-scrape sentiment data
model-scan calibrate --papers     # Parse new paper benchmarks
```

---

## Phase 4: Empirical Data Collection (Current)

### 4.1 Models Missing AA Data
From the scan database, these models need alternative scoring:
- `cohere/north-mini-code-1-0:free`
- `nex-agi/nex-n2-pro:free`
- `openrouter/owl-alpha`
- `poolside/laguna-m.1:free`
- `poolside/laguna-xs.2:free`
- `stepfun/*` models
- `xiaomi/mimo-v2.5-pro-ultraspeed`

For these, use conditional estimation (Phase 2.1) until AA data is available.

### 4.2 Models with Sentiment Gaps
- MiniMax-M3 (new #1, user hasn't used much — needs empirical validation)
- DeepSeek V4 Flash (user reports better than benchmark, needs sentiment confirmation)
- Nemotron 3 Ultra (user reports worse than benchmark, needs sentiment confirmation)

---

## Prioritization

| Task | Effort | Impact | Priority |
|------|--------|--------|----------|
| Conditional scoring (arch estimator) | 1-2 days | 🔴 High — unblocks all missing models | P0 |
| `model-scan overall` command | 2-4 hours | 🔴 High — needed by downstream tools | P0 |
| User sentiment pipeline (X/Reddit) | 2-3 days | 🟡 Medium — fills "magic" gap | P1 |
| Paper benchmark collection | 1-2 days | 🟡 Medium — validates scoring axes | P1 |
| Error log calibration | 4-8 hours | 🟡 Medium — improves reliability scoring | P1 |
| Sentiment for Chinese models | 1 day | 🟢 Low — nice to have | P2 |

---

## Architecture Notes

The gold standard generator (`gold_standard.py`) already has the right structure.
It should be extended to:
1. Accept calibration weights from CLI
2. Display reasoning traces with sentiment annotations
3. Show "estimated" vs "scraped" badges on scores
4. Generate config patches that include confidence intervals

