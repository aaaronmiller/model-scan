# ARDF routing rules of thumb

Generated 2026-11-17 by `calibrate.py` from `sources/current/` (AA snapshot 2026-11-10). Do not edit by hand.

Short list. Every rule cites the data behind it. Scores are the AA v4.2 composite recomputed by ARDF; costs are AA workload costs per task in USD, not subscription bills. Starting hypotheses, not guarantees: verify availability, quota and terms at dispatch, and check a rule on your own task before relying on it.

1. **Choose from the frontier first; a dominated configuration has a cheaper or equal and at least as good alternative.**  
   Data: 22 of 109 scored configurations with a trusted cost are undominated (21 of 108 when only prices above $0 count); 2 scored configurations with an unverified AA price of $0 are held out of both (full lists: docs/full-frontier.md). Example: Claude Fable 5.1 (Max, Default Fallback) (49.09, $12.99) is dominated by GPT-6.1 Sol (High) (50.31, $0.591).
2. **To reach a target score, start with the cheapest configuration that clears it.**  
   Data: Cheapest priced configuration at or above each score: 20: GPT-6.1 Terra (Low) $0.0713; 30: Muse Ember (Xhigh) $0.116; 40: GPT-6.1 Terra (High) $0.259; 50: GPT-6.1 Sol (High) $0.591; 55: GPT-6 Astra (Xhigh) $3.66; 60: Gemini 4 Carbon (High) $7.76.
3. **Each extra point at the top costs far more than at the bottom; buy the top tier only when the task needs it.**  
   Data: Cheapest config at 40 or more is $0.259; at 60 or more it is $7.76, 29.9x as much (GPT-6.1 Terra (High) versus Gemini 4 Carbon (High)).
4. **Treat max effort as an exception: price it against xhigh on your task before using it.**  
   Data: Across 10 families with both settings, max costs a median 1.66x xhigh for a median +2.01 points; 3 of 10 max configurations are on the frontier.
5. **Effort is not monotone value: the frontier mixes every effort setting, so choose model and effort together.**  
   Data: Frontier members by effort: none 1, low 3, medium 5, high 5, xhigh 5, max 3 (of 22).
6. **Treat default-fallback tracks as their own configurations, not as the standalone model; the pinned data does not say what the fallback covers.**  
   Data: 20 scored fallback tracks (Anthropic 20); 5 on the frontier (Anthropic 5); 0 have a scored standard-track counterpart.
7. **Do not lock to one vendor: the frontier is multi-provider.**  
   Data: Frontier members by provider: OpenAI 11, Anthropic 6, Google 2, Meta 2, Cohere 1. Each provider's own frontier is in docs/full-frontier.md.
8. **Do not trust an AA price of $0 until a free route with the same name is listed; unverified $0 configurations stay out of the frontier, and a verified one still needs its rate limits and terms checked.**  
   Data: AA lists 3 scored $0 configurations. Verified free route: North Mini Code 3.42 (free route listed: OpenRouter cohere/north-mini-code:free; Kilo cohere/north-mini-code:free). Unverified, held out of dominance: K2 Horizon 375B A23B 17.73 (AA lists $0 and no route with this name exists in the pinned OpenRouter, Kilo or OpenCode Zen catalogs); Command A+ 6.24 (AA lists $0 but the catalogs list a paid route: OpenRouter cohere/command-a-plus $0.3/M in, $1.5/M out; Kilo cohere/command-a-plus $0.3/M in, $1.5/M out). For scale, the best of all three (17.73) is matched by a paid configuration at $0.0422 (GPT-6 Luna (Medium)).
9. **Use free routes for bounded, verifiable work; they top out well below the paid frontier.**  
   Data: 8 free-route models have a measured score (39 free catalog entries in total). Best: DeepSeek V4.1 Flash 1017 (Max) at 32.59 (identity unverified) (50% of the top frontier score 64.56); the cheapest paid configuration at or above it is Muse Ember (Xhigh) at $0.116 (34.11). See docs/free-routes.md.
10. **Never mix cost bases: Priors subscription-equivalent costs sit below API workload costs by a lab-dependent factor.**  
   Data: Median Priors API to subscription cost ratio by lab: Anthropic 56.6x, Mistral 21.0x, OpenAI 18.5x, Alibaba 13.7x, xAI 10.8x, Google 2.8x, Meta 1.0x, Other 1.0x. ARDF costs are API workload costs.
11. **Keep each comparison within one source and one cost basis, even though ARDF and Priors scores agree closely.**  
   Data: On 93 of 100 Priors API rows the independently recomputed ARDF score differs from Priors by a median 0.0025 and at most 0.0050 points; API cost differs by a median 0.0000 and at most 0.0039 USD per task. Exact table: docs/priors-deltas.md.
12. **No score is not a low score; it means the benchmark set is incomplete.**  
   Data: 618 of 734 primary configurations have no complete 10-benchmark score and are not ranked; they are listed on the dashboard's unscored shelf.

Related: `docs/full-frontier.md` (every frontier), `docs/free-routes.md` (free routes), `pareto-frontier-cheatsheet.md` (multi-source ledger frontier), `docs/current-frontier.md` (AA vs Priors).
