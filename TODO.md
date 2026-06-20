# Model-Scan Task Tracker

## Phase 1: Existing Optimization Plan Tasks
- [ ] Gold standard generation (LLM-based config patches with reasoning traces)
- [ ] Convergence metric (CPMR) implementation
- [ ] Automated optimization loop (grid/evolutionary/gradient)
- [ ] Independent audit system
- [ ] Supplemental benchmark integration (Terminal-Bench, BFCL, Arena ELO)
- [ ] Iterative refinement (cron job)

## Phase 2: Token Economics Analysis
- [x] All tasks complete (see token-economics/ directory)

## Phase 3: Calibration & Empirical Validation (added 2026-06-19)
### P0
- [x] **CLI overall command** (`cli_overall.py`) — `model-scan overall -a --free`
      Returns best model for tier. Done.
- [x] **Conditional scoring engine** (`scoring/arch_predictor.py`)
      Estimates AI Index from arch type, params, release date. Scanned 5262 models. Done.

### P1
- [x] **User sentiment pipeline** (`scoring/sentiment.py`)
      Collection framework built. Manual entry via --add flag. Needs social media scraping.
- [x] **Paper benchmark extractor** (`scoring/paper_benchmarks.py`)
      Extraction framework built. Needs paper text input for GLM 5.2, Kimi K2.6, etc.
- [x] **Reliability calibration** (`scoring/reliability_calibration.py`)
      Analyzes probe data + Hermes logs. No probe data yet. Done.

### P2
- [x] **Magic factor tracking** (`empirical_adjustments.json`)
      Empirical deltas for 8 models. Updated with recalibrated AA scores. Done.
- [x] **AA cache refreshed** — 540 models, recalibrated 2026-06-19
      ALL scores dropped 6-11 points. GLM 5.2 now in cache (AI 51.1).

## Status
**Phase 3**: 1 task done, 6 remaining — see docs/SESSION_DATA_2026-06-19.md
**Last updated**: 2026-06-19
