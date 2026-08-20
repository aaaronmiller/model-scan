<!--
---
title: ARDF Current-Model and Identity Refresh
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
---
-->

# ARDF v7.3 current-model and identity refresh

This memo records the August 8 forensic refresh layered onto v7.2.1. It is intentionally separate from the general methodology because these facts are date-sensitive.

## DeepSeek V4 Pro

Treat all currently observed V4 Pro rows as **DeepSeek V4 Pro Preview**. DeepSeek's Apr. 24 announcement was `DeepSeek V4 Preview`; the Jul. 31 Flash 0731 announcement explicitly said Pro remained unchanged and its official release was still coming. API support changes do not create a new model checkpoint.

Current package identity keys remain `deepseek-v4-pro-*` for backward compatibility, but display/family/status metadata say Preview. A future official Pro release must receive a new explicit release/version identity unless DeepSeek states that the existing checkpoint was simply promoted unchanged.

## Xiaomi MiMo

Current AA identity check:

| Model | Current AA Intelligence Index | Current AA full evaluation cost | Identity action |
|---|---:|---:|---|
| MiMo-V2.5 | 38 | $25.18 | Canonical plain V2.5; merge old `mimo-v2-5-0424` alias |
| MiMo-V2.5-Pro | 43 | $98.86 | Distinct Pro model; do not borrow plain score |
| MiMo-V2-Pro | older separate evidence | — | Preserve predecessor as separate identity |

This changes routing: MiMo-V2.5-Pro no longer clears the project's 45-point general-executor eligibility floor.

## General executor zone

Current literal `$ / calibrated-capability` top five among current priced configurations with calibrated capability ≥45:

1. Muse Spark 1.2 (xhigh, Contributor pricing): capability 54.54, task $0.02123, ratio 0.0003893
2. GPT-5.6 Luna (high): capability 47.00, direct AA task $0.02000, ratio 0.0004255
3. DeepSeek V4 Flash 0731 (max): capability 52.00, direct AA task $0.03000, ratio 0.0005769
4. Grok 4.3 (high): capability 53.00, task $0.10662, ratio 0.0020117
5. MiniMax-M3: capability 46.59, task $0.12295, ratio 0.0026391

Muse's coordinate uses Contributor/data-sharing pricing; the AA Standard route remains separately visible. Luna high is now the nearest literal price/performance challenger because current AA direct Cost per Intelligence Index Task is $0.02. DeepSeek V4 Flash 0731 remains extremely close in absolute cost and carries higher calibrated capability, making it an important executor alternative despite its slightly worse ratio.

## Top-end zone

The preferred same-source pruning plane is now **AA Intelligence Index vs direct Cost per Intelligence Index Task** whenever AA publishes the task-cost field. Full Intelligence Index evaluation cost remains visible as a secondary diagnostic and is used only when direct task cost is unavailable.

Key current cuts:

- **Claude Opus 5 max: hard prune for general default routing.** Max and xhigh both score 63 on current AA, while direct AA task cost is $2.34 for max versus $1.80 for xhigh.
- **Claude Opus 5 medium/high/xhigh:** keep as explicit cost/quality rungs. High and GPT-5.6 Sol max are Pareto-equivalent on the current AA top-end slice at 61 / $1.23.
- **GPT-5.6 Sol:** low → medium → high → xhigh → max remains internally monotone. Cross-family, some rungs are dominated or tied, so retain Sol primarily where coding/agent evidence justifies it.
- **Kimi K3 max:** remains on both the audited ARDF operational top-end frontier and the current AA direct-task-cost top-end frontier. Kilo independently gives it a strong coding-agent cost/completion position.
- **Qwen3.8 Max xhigh:** currently misses both audited general top-end frontiers because cheaper configurations provide equal or higher general capability. Preserve it for Qwen-specific or specialist workloads, not as a default frontier route.
- **Fable 5 max:** remains near the capability ceiling but is price-heavy. In the audited general plane it is dominated by cheaper Opus/Sol/Kimi alternatives; Vals still shows Fable as the highest-scoring model on its workload, illustrating task sensitivity.

V7.3 therefore keeps independent source-native frontier views:

- AA Intelligence Index vs direct Cost per Intelligence Index Task
- Kilo coding completion vs cost/attempt
- Vals Index vs Cost/Test

These views intentionally disagree. Kilo's current public top-10 cost/completion plane retains Grok 4.5 → Kimi K3 → GPT-5.5 → GPT-5.6 Sol. Vals' current Index/Cost-Test plane retains DeepSeek Flash 0731 → Luna → Muse → Kimi K3 → Opus 5 → Fable 5. The disagreement is useful evidence of workload/harness specialization rather than an error to average away.

## Source URLs to re-check on the next refresh

- DeepSeek Preview release: `https://api-docs.deepseek.com/news/news260424/`
- DeepSeek current update/status: `https://x.com/deepseek_ai/status/2083084419515220191`
- AA model/Pareto explorer: `https://artificialanalysis.ai/`
- AA MiMo Pro: `https://artificialanalysis.ai/models/mimo-v2-5-pro`
- Kilo leaderboard: `https://kilo.ai/leaderboard`
- Vals current index/benchmarks: `https://www.vals.ai/home`

## Build script semantics

`calibrate.py` is the sole calibration engine. `build-package.py` is the sole complete package-generation/orchestration entry point. The ambiguous legacy `rebuild.py` wrapper was removed in v7.3 so future agents cannot mistake it for a second calibration implementation.
