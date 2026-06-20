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
- [ ] **Conditional scoring engine** (`scoring/arch_predictor.py`)
      Estimate AI Index from arch type, params, release date when AA data missing.

### P1
- [ ] **User sentiment pipeline** (`scoring/sentiment.py`)
      Scrape X/Twitter, Reddit for "feels like" comparisons. Tag by region.
- [ ] **Paper benchmark extractor** (`scoring/paper_benchmarks.py`)
      Extract from Kimi K2.6, GLM 5.2, Qwen 3.7, MiniMax M3.
- [ ] **Reliability calibration** (`scoring/reliability_calibration.py`)
      Cross-reference model scores with real API error rates.

### P2
- [ ] **Magic factor tracking** (`empirical_adjustments.json`)
      Empirical over/underperformance deltas.
- [ ] **Benchmark scraping directory** — scraped data from paper sources.

## Status
**Phase 3**: 1 task done, 6 remaining — see docs/SESSION_DATA_2026-06-19.md
**Last updated**: 2026-06-19
