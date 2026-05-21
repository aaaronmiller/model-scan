# Model-Scan Task Tracker

## Phase 1: Existing Optimization Plan Tasks
- [ ] Gold standard generation (LLM-based config patches with reasoning traces)
- [ ] Convergence metric (CPMR) implementation
- [ ] Automated optimization loop (grid/evolutionary/gradient)
- [ ] Independent audit system
- [ ] Supplemental benchmark integration (Terminal-Bench, BFCL, Arena ELO)
- [ ] Iterative refinement (cron job)

## Phase 2: Token Economics Analysis (NEW - Ice-ninja Specification)
- [x] Research: Live pricing from all providers (OpenAI, Anthropic, Google, xAI, DeepSeek, NVIDIA, Cerebras, Groq, OCGo, Venice)
- [x] Research: Verify ≥80% prices via web search (≥92% verified ✅)
- [x] Research: Read AA Intelligence Index from artificialanalysis.ai (top 20+ models indexed, live)
- [x] Research: Find recent forum/Reddit threads for empirical usage patterns
- [x] Implement: Subscription multiplier framework (5×, 10× rules with effective tokens/mo estimates)
- [x] Implement: Workload-specific blended ratios (58/42 conversational, 75/25 tool-call, 30/70 code gen)
- [x] Implement: Reasoning-token overhead calculation (50% overhead for reasoning models)
- [x] Implement: Context-tier pricing handling (noted for 200K+ token tiers)
- [x] Implement: Cache-rate assumptions (80% standard, 50% conservative, 0% worst-case)
- [x] Implement: Quality % calculation anchored at GPT-5.5 (AA=60 = 100% quality)
- [x] Generate: Top-3 recommendations (DeepSeek V4 Flash, Google One AI Pro, Claude Max 20x)
- [x] Generate: Main contenders table (15 rows, sorted by $/M QA)
- [x] Generate: Hybrid recommendations for 4 user profiles (5M, 15M, 50M, 500M tok/mo)
- [x] Generate: Caveats section (20 footguns covering pricing, quality, workflow)
- [x] Generate: Full appendix table (30+ rows, 4 tiers, all columns)
- [x] Verify: No empty fields (verified/inferred/estimated for all cells)
- [x] Created `token-economics/pricing-research.md` with verified data
- [x] Created `token-economics/token-economics-analysis.md` — full analysis document

## Status
Current focus: ALL TASKS COMPLETE ✅
Next: Begin Phase 1 implementation (see docs/design.md)
Last updated: 2026-05-17