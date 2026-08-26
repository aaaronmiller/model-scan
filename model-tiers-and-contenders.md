# ARDF Model Tiers + Contested Regions

This document answers a different question from the Pareto cheatsheet: **tiers classify calibrated capability**, while Pareto membership classifies economic non-dominance.

Canonical data: `data/unified-model-evidence.csv`. Policy: `project-config.json`. Regenerate with `python calibrate.py`.

## Capability tier policy

| Tier | Minimum calibrated capability | Interpretation |
|---|---:|---|
| T1 | 60 | Frontier ceiling |
| T2 | 56 | Frontier |
| T3 | 47 | Executor |
| T4 | 0 | Utility — bottom-4 interchangeable |

## Current scored configurations by tier

### T1 · Frontier ceiling (5)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Claude Opus 5 (max) | 61.15 | $2.2018 | YES | — |
| Claude Opus 5 (xhigh) | 61.02 | $1.0162 | YES | — |
| Claude Opus 5 (Adaptive Reasoning, Max Effort) | 60.67 | $0.48631 | no | — |
| GPT-5.6 Sol (max) | 60.65 | $1.5702 | YES | — |
| Claude Fable 5 (max) | 60.02 | $2.8223 | no | near-frontier |

### T2 · Frontier (24)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Kimi K3 (max) | 59.90 | $0.92963 | YES | — |
| Claude Opus 5 (high) | 59.66 | $0.79948 | no | near-frontier |
| Claude Fable 5 (Adaptive Reasoning, Max Effort, Opus 4.8 Fallback) | 59.61 | $1.0099 | no | — |
| GPT-5.6 Sol (max) | 59.35 | $0.53209 | no | — |
| Grok 4.6 (high) | 59.12 | $0.14385 | no | — |
| Claude Fable 5 (xhigh) | 59.03 | $1.7571 | no | near-frontier |
| GPT-5.6 Sol (xhigh) | 58.95 | $0.70321 | YES | — |
| Grok 4.6 (xhigh) | 58.33 | $0.14385 | no | — |
| Kimi K3 | 58.30 | $0.27405 | YES | — |
| Claude Opus 4.8 (xhigh) | 58.22 | — | no | — |
| Claude Opus 5 (medium) | 57.88 | $0.56949 | no | capability-close / price-heavy |
| GLM-5.3 (max) | 57.67 | $0.10106 | no | — |
| GPT-5.5 (xhigh) | 57.49 | $1.3827 | no | near-frontier |
| Grok 4.6 (medium) | 57.27 | $0.14385 | no | — |
| GPT-5.6 Sol (high) | 57.27 | $0.53914 | no | capability-close / price-heavy |
| Muse Spark 1.2 (xhigh, Contributor pricing) | 57.00 | $0.12719 | YES | — |
| Muse Spark 1.2 (xhigh, Standard pricing) | 57.00 | $0.32331 | no | capability-close / price-heavy |
| Gemini 3.1 Pro Preview | 57.00 | $0.37225 | no | capability-close / price-heavy |
| GPT-5.6 Terra (max) | 56.93 | $0.20251 | no | — |
| Qwen3.8 Max (xhigh) | 56.77 | $0.89547 | no | price-close / capability-behind |
| GPT-5.5 (high) | 56.43 | $0.71786 | no | capability-close / price-heavy |
| Gemini 3.7 Flash (high) | 56.41 | $0.065809 | no | — |
| Claude Opus 4.8 (Adaptive Reasoning, Max Effort) | 56.38 | $0.48631 | no | — |
| GPT-5.6 Sol (medium) | 56.16 | $0.40732 | no | — |

### T3 · Executor (58)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Qwen3.8 Max | 55.85 | $0.14385 | no | — |
| GPT-5.6 Luna (max) | 55.83 | $0.078429 | no | capability-close / price-heavy |
| Qwen3.8 2.4T A95B | 55.68 | $0.14385 | no | — |
| Claude Opus 4.8 (max) | 55.50 | $1.7767 | no | — |
| Muse Spark 1.2 (xhigh) | 55.35 | $0.093226 | no | — |
| GPT-5.6 Terra (max) | 55.22 | $0.77262 | no | price-close / capability-behind |
| Muse Spark 1.1 (xhigh effort) | 55.17 | — | no | — |
| Claude Opus 4.7 (xhigh effort) | 54.97 | — | no | — |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | 54.97 | $0.48631 | no | — |
| Grok 4.5 | 54.35 | $0.25235 | no | — |
| Claude Sonnet 5 (Adaptive Reasoning, Max Effort) | 54.33 | $0.18509 | no | — |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | 54.28 | $1.9943 | no | — |
| Claude Sonnet 5 (max) | 54.04 | $1.9591 | no | — |
| openai/gpt-5.5 | 53.76 | $0.53209 | no | — |
| Gemini 3.7 Flash (medium) | 53.38 | $0.065809 | no | — |
| GPT 5.4 | 53.08 | $0.25622 | no | — |
| Muse Spark 1.1 (high effort) | 53.08 | — | no | — |
| Grok 4.3 (high) | 53.00 | $0.14774 | no | — |
| GPT-5.6 Luna (max) | 52.80 | $0.017871 | no | — |
| Muse Spark 1.1 | 52.79 | $0.093226 | no | — |
| Claude Sonnet 5 (xhigh) | 52.68 | $0.18509 | no | — |
| GPT-5.4 (xhigh) | 52.41 | $1.1198 | no | price-close / capability-behind |
| GPT-5.6 Terra (xhigh) | 52.33 | $0.3074 | no | — |
| DeepSeek V4 Pro 0813 (Reasoning, Max Effort) | 52.27 | $0.092825 | no | — |
| google/gemini-3.5-flash | 52.16 | $0.14953 | no | — |
| DeepSeek V4 Flash 0731 (max) | 52.00 | $0.034235 | no | price-close / capability-behind |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | 52.00 | $1.8744 | no | price-close / capability-behind |
| GLM-5.2 (max) | 51.97 | $0.10106 | no | — |
| Gemini 3.7 Flash (low) | 51.95 | $0.065809 | no | — |
| Gemini 3.5 Flash (high) | 51.79 | $0.91825 | no | — |
| DeepSeek V4 Flash 0731 (Reasoning, Max Effort) | 51.68 | $0.02915 | no | — |
| Gemini 3.6 Flash | 51.62 | $0.071367 | no | — |
| Claude Opus 5 (low) | 51.55 | $0.39185 | no | — |
| GLM-5.2 (max) | 51.47 | $0.37697 | YES | — |
| GPT-5.5 (medium) | 51.47 | $0.50155 | no | — |
| Qwen3.8 27B | 51.41 | $0.043565 | no | — |
| GPT-5.6 Sol (low) | 51.21 | $0.29772 | no | capability-close / price-heavy |
| Kimi K3 (low) | 51.02 | $0.26587 | no | capability-close / price-heavy |
| Gemini 3.6 Flash (high) | 50.63 | $0.33307 | no | capability-close / price-heavy |
| Grok 4.6 (low) | 50.59 | $0.14385 | no | — |
| DeepSeek V4 Flash Vision (Reasoning, Max Effort) | 50.00 | $0.02915 | no | — |
| GPT-5.6 Luna (xhigh) | 49.74 | $0.028497 | no | capability-close / price-heavy |
| Claude Opus 4.5 (high effort) | 49.70 | — | no | — |
| GPT-5.6 Terra (high) | 49.62 | $0.25314 | no | capability-close / price-heavy |
| DeepSeek V4 Flash 0731 (Xhigh) | 48.86 | $0.024463 | no | — |
| Gemini 3.1 Pro Preview | 48.58 | $0.19907 | no | — |
| Inkling (xhigh effort) | 48.48 | — | no | — |
| Qwen3.7 Max | 48.47 | $0.27907 | no | capability-close / price-heavy |
| GPT-5.5 Factory | 47.93 | — | no | — |
| Gemini 3.1 Pro | 47.75 | — | no | — |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | 47.70 | $0.28381 | no | — |
| Claude Opus 4.6 (Adaptive Reasoning, Max Effort) | 47.56 | $1.2116 | no | — |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | 47.39 | $1.2999 | no | — |
| Motif 3 | 47.39 | — | no | — |
| GPT-5.3 Codex | 47.38 | $0.20274 | no | — |
| GPT-5.5 (low) | 47.28 | $0.35809 | no | — |
| GPT-5.6 Luna (high) | 47.07 | $0.019652 | no | price-close / capability-behind |
| Composer 2.5 | 47.01 | — | no | — |

### T4 · Utility — bottom-4 interchangeable (675)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| GPT-5.5 Codex | 46.88 | — | no | — |
| GPT-5.6 Terra (medium) | 46.88 | $0.21008 | no | — |
| Kimi K2.6 | 46.57 | $0.15729 | no | — |
| GPT-5.4 Codex | 46.41 | — | no | — |
| MiniMax-M3 | 46.13 | $0.050966 | no | — |
| Claude Sonnet 5 (Non-reasoning, High Effort) | 46.07 | $0.18509 | no | — |
| Gemini 3.5 Flash (medium) | 46.04 | $0.20764 | no | — |
| Kimi K2.7 Code | 45.90 | $0.15822 | no | — |
| Motif 3 (Beta) | 45.77 | — | no | — |
| DeepSeek V4 Pro Preview (Reasoning, Max Effort) | 44.95 | $0.058402 | no | — |
| Claude Opus 4.6 (Adaptive Reasoning, Max Effort) | 44.90 | $0.48631 | no | — |
| DeepSeek V4 Pro (Reasoning, Max Effort) | 44.80 | $0.023579 | no | — |
| Inkling Small | 44.74 | $0.022435 | no | — |
| gpt-5.4-high | 44.33 | — | no | — |
| GPT-5.3 Codex (xhigh) | 44.27 | $0.49321 | no | — |
| GPT-5.6 Sol (non-reasoning) | 43.85 | $0.2786 | no | — |
| GPT-5.2 Codex (xhigh) | 43.80 | $0.57109 | no | capability-close / price-heavy |
| DeepSeek V4 Pro (Reasoning, High Effort) | 43.74 | $0.023579 | no | — |
| MiMo-V2.5-Pro | 43.42 | $0.031292 | no | — |
| gpt-5.4-pro-thinking | 43.36 | — | no | — |
| Claude Opus 4.7 (Non-reasoning, High Effort) | 43.29 | $0.44489 | no | — |
| DeepSeek V4 Flash (Reasoning, Max Effort) | 43.26 | $0.038017 | no | — |
| Qwen3.8 27B (medium) | 43.16 | $0.046957 | no | — |
| Qwen3.8 27B (low) | 43.15 | $0.046957 | no | — |
| GPT-5.2 (xhigh) | 43.07 | $0.54196 | no | — |
| Nex-N2-Pro | 42.89 | $0.042917 | no | — |
| GPT-5.4 mini (xhigh) | 42.65 | $0.37373 | no | — |
| GLM-5.1 (Reasoning) | 42.26 | $0.14274 | no | — |
| DeepSeek V4 Flash (Reasoning, Max Effort) | 42.00 | $0.0068453 | no | — |
| Muse Spark | 41.97 | — | no | — |
| Qwen3.7 Plus | 41.89 | $0.041047 | no | — |
| gpt-5.2-high | 41.85 | — | no | — |
| MiMo-V2.5 | 41.84 | $0.010649 | YES | — |
| Agnes 2.5 Pro Alpha | 41.77 | $0.024437 | no | — |
| gpt-5-default | 41.51 | — | no | — |
| openai/gpt-5.4-mini | 41.36 | $0.072003 | no | — |
| Qwen3.6 Plus | 41.33 | $0.08672 | no | capability-close / price-heavy |
| GPT-5.6 Terra (low) | 41.32 | $0.15051 | no | capability-close / price-heavy |
| google/gemini-3-flash-preview | 41.29 | — | no | — |
| gemini-3-flash-high | 41.26 | — | no | — |
| GPT-5.2 Codex (xhigh) | 41.20 | $0.20274 | no | — |
| GPT-5.4 nano (xhigh) | 41.16 | $0.12138 | no | capability-close / price-heavy |
| MiMo-V2-Pro | 40.84 | $0.11881 | no | capability-close / price-heavy |
| Nemotron 3 Ultra 550B A55B (Reasoning) | 40.83 | $0.14206 | no | capability-close / price-heavy |
| DeepSeek V4 Pro Preview (Reasoning, High Effort) | 40.83 | $0.035156 | no | capability-close / price-heavy |
| openai/gpt-5.4-nano | 40.76 | $0.018235 | no | — |
| Inkling | 40.66 | $0.080325 | no | — |
| Qwen3.6 Max Preview | 40.55 | $0.14555 | no | capability-close / price-heavy |
| Solar Pro 4 | 40.44 | $0.022435 | no | — |
| Qwen3.6 Max Preview | 40.43 | — | no | — |
| MiMo-V2.5 | 40.17 | $0.0071358 | no | — |
| gemini-3-flash-low | 39.94 | — | no | — |
| Hy3-preview (Reasoning) | 39.88 | $0.011861 | no | capability-close / price-heavy |
| Gemini 3.5 Flash-Lite (high) | 39.78 | $0.071951 | no | capability-close / price-heavy |
| GPT-5.4 (low) | 39.67 | $0.2317 | no | — |
| Gemini 3 Pro Preview (high) | 39.55 | $0.20704 | no | — |
| Grok Build 0.1 0616 | 39.54 | $0.056711 | no | — |
| gemini-3-pro-preview | 39.49 | — | no | — |
| JT-4.1 Flash 236B A21B | 39.48 | — | no | — |
| GPT-5.1 (high) | 39.39 | $0.16911 | no | — |
| GLM-5 (Reasoning) | 38.95 | $0.069641 | no | — |
| DeepSeek V4 Flash (Reasoning, High Effort) | 38.88 | $0.0068453 | no | — |
| MiniMax-M2.7 | 38.84 | $0.033488 | no | — |
| Claude Opus 4.6 | 38.80 | $0.48631 | no | — |
| GPT-5 (high) | 38.71 | $0.20957 | no | — |
| x-ai/grok-build-0.1 | 38.66 | — | no | — |
| Qwen 3.6 Plus | 38.65 | — | no | — |
| GLM-5-Turbo | 38.58 | — | no | — |
| GPT-5.6 Luna (medium) | 38.56 | $0.0145 | YES | — |
| Ling 3.0 Flash (reasoning) | 38.00 | $0.022481 | no | capability-close / price-heavy |
| KAT Coder Pro V2 | 37.82 | $0.024354 | no | capability-close / price-heavy |
| Claude Opus 4.6 (Non-reasoning, High Effort) | 37.79 | $0.49706 | no | capability-close / price-heavy |
| Ling 3.0 Flash | 37.75 | $0.004464 | no | — |
| Nemotron 3 Ultra 550B A55B (Reasoning) | 37.60 | $0.083936 | no | capability-close / price-heavy |
| gpt-5.2-pro | 37.58 | — | no | — |
| Grok 4.20 0309 v2 (Reasoning) | 37.50 | $0.092205 | no | capability-close / price-heavy |
| GPT-5.5 (Non-reasoning) | 37.44 | $0.26725 | no | capability-close / price-heavy |
| DeepSeek V4 Flash (Reasoning, High Effort) | 37.36 | $0.014061 | no | capability-close / price-heavy |
| Qwen3.6 27B (Reasoning) | 37.32 | $0.11274 | no | capability-close / price-heavy |
| Claude Sonnet 4.5 20250929 Thinking | 37.21 | — | no | — |
| Gemini 3.5 Flash-Lite | 37.06 | $0.032257 | no | — |
| DeepSeek V4 Flash 0731 (High) | 37.00 | $0.010662 | no | near-frontier |
| claude-4.6-opus-thinking-high | 36.86 | — | no | — |
| MiMo-V2-Omni-0327 | 36.85 | $0.04104 | no | capability-close / price-heavy |
| Grok 4.20 0309 (Reasoning) | 36.80 | $0.13253 | no | capability-close / price-heavy |
| Claude Sonnet 4.6 (Non-reasoning, High Effort) | 36.80 | $0.28381 | no | — |
| GPT-5.1 Codex Max | 36.59 | — | no | — |
| Qwen3.5 Plus Thinking | 36.46 | — | no | — |
| Grok 4.3 (medium) | 36.45 | $0.065073 | no | — |
| x-ai/grok-4.3 | 36.33 | $0.071752 | no | — |
| Kimi K2.5 (Reasoning) | 36.25 | $0.059846 | no | — |
| GPT-5 Codex (high) | 36.12 | $0.27279 | no | — |
| Claude Sonnet 4.6 (Non-reasoning, High Effort) | 35.89 | $0.41651 | no | — |
| Grok 4.3 (low) | 35.87 | $0.057495 | no | — |
| Claude Haiku 4.5 | 35.85 | — | no | — |
| GLM-5.1 (Non-reasoning) | 35.84 | $0.092698 | no | — |
| Muse Glimmer (high) | 35.80 | $0.024869 | no | — |
| GPT-5.6 Terra (non-reasoning) | 35.59 | $0.19028 | no | — |
| MiMo-V2-Omni | 35.45 | — | no | — |
| Claude Opus 4.5 (Reasoning) | 35.39 | $0.52061 | no | — |
| Gemini 3.5 Flash (minimal) | 35.36 | $0.17277 | no | — |
| Solar Open2 250B | 35.34 | — | no | — |
| Mistral Medium 3.5 | 35.10 | $0.22123 | no | — |
| Claude Sonnet 4.6 (Non-reasoning, Low Effort) | 35.10 | $0.28381 | no | — |
| Kimi K2.6 (Non-reasoning) | 34.99 | $0.09211 | no | — |
| GLM 5V Turbo (Reasoning) | 34.90 | — | no | — |
| GPT-5.1 Codex (high) | 34.73 | $0.39286 | no | — |
| GLM-5.2 (Non-reasoning) | 34.71 | $0.10106 | no | — |
| Claude Opus 4.5 (Non-reasoning) | 34.71 | $0.43072 | no | — |
| Qwen3.5 397B A17B (Reasoning) | 34.63 | $0.10015 | no | — |
| GPT-5.1 | 34.47 | $0.14219 | no | — |
| Hy3-preview (Reasoning) | 34.40 | $0.0039563 | no | — |
| Claude Sonnet 4.6 (Non-reasoning, Low Effort) | 34.26 | $0.21801 | no | — |
| GPT-5.2 (xhigh) | 34.26 | $0.20274 | no | — |
| Qwen3.5 27B (Reasoning) | 34.19 | $0.041652 | no | — |
| Qwen3.8 27B (Non-reasoning) | 33.95 | $0.046957 | no | — |
| GPT-5.5 Instant (May 2026) | 33.91 | $0.41819 | no | — |
| LongCat 2.0 | 33.86 | $0.058461 | no | — |
| GPT-5.2 (medium) | 33.85 | $0.245 | no | — |
| Mistral Medium 3.5 | 33.85 | — | no | — |
| Gemini 3 Flash Preview (Reasoning) | 33.74 | $0.049269 | no | — |
| MiMo-V2-Flash (Feb 2026) | 33.61 | $0.012765 | no | — |
| GPT-5.6 Luna (low) | 33.60 | $0.013942 | no | price-close / capability-behind |
| Claude 4.5 Sonnet (Reasoning) | 33.41 | $0.29833 | no | capability-close / price-heavy |
| Qwen3.5 122B A10B (Reasoning) | 33.04 | $0.076882 | no | — |
| GPT-5 mini (high) | 32.96 | $0.040684 | no | — |
| o3-pro | 32.91 | $1.7741 | no | — |
| deepseek-v3.2-thinking-high | 32.87 | — | no | — |
| GLM-5 (Non-reasoning) | 32.80 | $0.066024 | no | — |
| DeepSeek V3p2 Thinking | 32.71 | — | no | — |
| Gemini 3 Pro Preview (high) | 32.54 | $0.20251 | no | — |
| GLM-4.7 (Reasoning) | 32.51 | $0.043705 | no | — |
| Claude Opus 4.5 20251101 Thinking | 32.46 | $0.48631 | no | — |
| Grok 4 | 32.45 | $0.3905 | no | — |
| Qwen3.5 397B A17B (Non-reasoning) | 32.34 | $0.064778 | no | — |
| Qwen3.5 Flash | 32.23 | — | no | — |
| Qwen3 Max Thinking | 32.12 | $0.12376 | no | — |
| claude-4.5-opus-thinking-high | 32.06 | — | no | — |
| A.X-K2 | 31.93 | — | no | — |
| DeepSeek V4 Pro (Non-reasoning) | 31.90 | $0.023579 | no | — |
| Qwen3.6 27B (Non-reasoning) | 31.76 | $0.068984 | no | — |
| GPT-5 | 31.70 | $0.14219 | no | — |
| Qwen3.6 35B A3B (Reasoning) | 31.64 | $0.059689 | no | — |
| Ring-2.6-1T | 31.38 | $0.066441 | no | — |
| Laguna M.1 | 31.31 | — | no | — |
| MiniMax-M2.1 | 31.30 | $0.027252 | no | — |
| MiniMax-M2.5 | 31.23 | $0.026511 | no | — |
| DeepSeek V4 Pro Preview (Non-reasoning) | 31.22 | $0.030397 | no | — |
| GPT-5 Codex (high) | 31.07 | $0.14219 | no | — |
| GPT-5.1 Codex | 30.98 | $0.14219 | no | — |
| Qwen3.5 Omni Plus | 30.97 | $0.063648 | no | — |
| DeepSeek V3.2 (Reasoning) | 30.70 | $0.01568 | no | — |
| mistralai/devstral-2512 | 30.67 | — | no | — |
| GPT-5 (medium) | 30.64 | $0.14486 | no | — |
| GPT-5.1 Codex mini (high) | 30.63 | $0.071461 | no | — |
| K-EXAONE 2.0 0803 | 30.60 | — | no | — |
| GPT-5.4 nano (medium) | 30.48 | $0.02209 | no | — |
| Gemma 4 31B (Reasoning) | 30.45 | — | no | — |
| Kimi K2 Thinking | 30.34 | $0.056531 | no | — |
| Step 3.7 Flash | 30.18 | $0.017425 | no | — |
| GPT-5.4 mini (medium) | 30.16 | $0.079495 | no | — |
| Gemini 3 Pro Preview (low) | 29.81 | $0.17306 | no | — |
| Claude 4.1 Opus (Reasoning) | 29.75 | $1.4704 | no | — |
| Kimi K2.5 (Non-reasoning) | 29.75 | $0.056627 | no | — |
| Qwen3.5 27B (Non-reasoning) | 29.66 | $0.037208 | no | — |
| Qwen3.5 35B A3B (Reasoning) | 29.58 | $0.038556 | no | — |
| Qwen3.5 122B A10B (Non-reasoning) | 29.52 | $0.048867 | no | — |
| G9v3-39A5B | 29.29 | — | no | — |
| Claude 4.5 Sonnet (Non-reasoning) | 29.28 | $0.25479 | no | — |
| GPT-5.5 Instant (June 2026) | 29.25 | $0.53209 | no | — |
| MiMo-V2-Flash (Reasoning) | 29.24 | $0.0081631 | no | — |
| DeepSeek V4 Flash (Non-reasoning) | 28.98 | $0.00578 | no | price-close / capability-behind |
| Claude 4.1 Opus (Non-reasoning) | 28.80 | $1.5486 | no | — |
| claude-4.6-sonnet | 28.80 | — | no | — |
| JT-35B-Flash | 28.68 | — | no | — |
| Claude 4.5 Haiku (Reasoning) | 28.49 | $0.12432 | no | — |
| Laguna Xs.2 | 28.35 | — | no | — |
| Grok 4.1 Fast (Reasoning) | 28.32 | — | no | — |
| DeepSeek V3.1 Terminus (Reasoning) | 28.32 | $0.10068 | no | — |
| mistralai/mistral-small-2603 | 28.31 | — | no | — |
| Gemini 3.1 Flash-Lite | 28.31 | $0.025517 | no | — |
| Claude 4.1 Opus (Non-reasoning) | 28.24 | $0.7145 | no | — |
| GPT-5 (low) | 28.23 | $0.11885 | no | — |
| GPT-5 mini (medium) | 28.20 | $0.025136 | no | — |
| MiMo-V2.5-Pro (Non-reasoning) | 28.13 | $0.038539 | no | — |
| o3 | 28.11 | $0.19886 | no | — |
| GPT-5.4 (Non-reasoning) | 27.99 | $0.21261 | no | — |
| GLM-4.6 (Reasoning) | 27.69 | $0.041679 | no | — |
| GPT-5.6 Luna (non-reasoning) | 27.68 | $0.01365 | no | price-close / capability-behind |
| Grok 4.3 (Non-reasoning) | 27.66 | $0.085521 | no | — |
| GPT-5.1 Codex mini (high) | 27.44 | $0.02606 | no | — |
| Claude 4 Opus (Reasoning) | 27.38 | $1.4704 | no | — |
| Gemini 3 Flash Preview (Non-reasoning) | 27.37 | $0.031696 | no | — |
| KAT-Coder-Pro V1 | 27.14 | $0.029311 | no | — |
| Gemini 2.5 Pro Preview (Mar' 25) | 27.07 | — | no | — |
| Claude 4 Sonnet (Reasoning) | 27.03 | $0.28656 | no | — |
| Gemma 4 26B A4B (Reasoning) | 27.01 | $0.011434 | no | — |
| MiMo-V2-Flash (Non-reasoning) | 26.81 | — | no | — |
| Step 3.5 Flash 2603 | 26.50 | $0.0060994 | YES | — |
| gpt-5.2-default | 26.42 | — | no | — |
| NVIDIA Nemotron 3 Super 120B A12B (Reasoning) | 26.38 | $0.033264 | no | capability-close / price-heavy |
| Hy3-preview (Non-reasoning) | 26.35 | $0.0056901 | no | capability-close / price-heavy |
| Ling-2.6-1T | 26.33 | $0.038814 | no | capability-close / price-heavy |
| Grok 4 Fast (Reasoning) | 26.14 | $0.012734 | no | capability-close / price-heavy |
| Step 3.5 Flash | 26.00 | $0.0060994 | no | razor-edge miss |
| MiniMax-M2 | 25.94 | $0.026545 | no | capability-close / price-heavy |
| Grok 4 0709 | 25.79 | — | no | — |
| o1 | 25.62 | $1.3009 | no | — |
| o4-mini (high) | 25.55 | $0.11314 | no | — |
| Claude 4 Opus (Non-reasoning) | 25.50 | $0.7145 | no | — |
| Claude 4 Sonnet (Non-reasoning) | 25.49 | $0.19661 | no | — |
| Gemini 2.5 Pro | 25.22 | $0.13871 | no | — |
| Qwen3.5 35B A3B (Non-reasoning) | 25.06 | $0.031036 | no | capability-close / price-heavy |
| Ling 3.0 Tiny (reasoning) | 25.00 | — | no | — |
| gpt-5-mini | 24.88 | $0.02606 | no | — |
| o4-mini (high) | 24.73 | $0.088273 | no | — |
| DeepSeek V3.2 Exp (Reasoning) | 24.68 | $0.013609 | no | capability-close / price-heavy |
| DeepSeek V3.2 (Non-reasoning) | 24.66 | $0.073409 | no | capability-close / price-heavy |
| Qwen3 Max | 24.63 | $0.12243 | no | capability-close / price-heavy |
| Doubao Seed Code | 24.43 | — | no | — |
| Claude 3.7 Sonnet (Reasoning) | 24.35 | — | no | — |
| Command A+ | 24.23 | — | no | — |
| Qwen3 Max Thinking (Preview) | 24.00 | $0.11401 | no | — |
| Gemma 4 31B (Non-reasoning) | 23.94 | $0.0093614 | no | — |
| Claude 4.5 Haiku (Non-reasoning) | 23.71 | $0.076464 | no | — |
| K-EXAONE (Reasoning) | 23.58 | — | no | — |
| Claude 3.7 Sonnet (Non-reasoning) | 23.50 | $0.18628 | no | — |
| Mercury 2 | 23.44 | $0.016347 | no | — |
| Qwen3.6 35B A3B (Non-reasoning) | 23.20 | $0.04541 | no | — |
| DeepSeek V3.2 Speciale | 23.18 | — | no | — |
| Qwen3 Coder Next | 23.13 | $0.032243 | no | — |
| GLM-4.7-Flash (Reasoning) | 23.09 | $0.0058059 | no | price-close / capability-behind |
| MiMo-V2-Flash (Non-reasoning) | 23.07 | $0.0096254 | no | — |
| Nova 2.0 Pro Preview (medium) | 23.03 | $0.15554 | no | — |
| GLM-4.6 (Non-reasoning) | 22.98 | $0.026546 | no | — |
| Gemini 2.5 Flash Preview (Sep '25) (Reasoning) | 22.86 | — | no | — |
| Grok 4.20 0309 (Non-reasoning) | 22.69 | $0.1266 | no | — |
| Qwen3.5 9B (Reasoning) | 22.69 | $0.0092905 | no | — |
| North Mini Code | 22.63 | — | no | — |
| Gemini 2.5 Pro Preview (May' 25) | 22.52 | $0.14005 | no | — |
| Grok 3 mini Reasoning (high) | 22.50 | $0.027676 | no | — |
| GLM-4.7 (Non-reasoning) | 22.50 | $0.041309 | no | — |
| Grok 3 mini Reasoning (high) | 22.46 | $0.014566 | no | — |
| Gemma 4 12B (Reasoning) | 22.40 | $0.0086082 | no | — |
| GPT-5.2 (Non-reasoning) | 22.34 | $0.18457 | no | — |
| ERNIE 5.0 Thinking Preview | 22.10 | — | no | — |
| Ling 3.0 Tiny | 22.07 | — | no | — |
| Grok 4.20 0309 v2 (Non-reasoning) | 22.02 | $0.081002 | no | — |
| Nova 2.0 Pro Preview (medium) | 22.00 | $0.1952 | no | — |
| gpt-oss-120b (high) | 21.88 | $0.033808 | no | — |
| Apriel-v1.5-15B-Thinker | 21.83 | — | no | — |
| Nova 2.0 Omni (medium) | 21.79 | $0.033888 | no | — |
| Nemotron 3.5 Lightning | 21.73 | $0.0042946 | no | — |
| Gemini 3 Flash | 21.73 | $0.046957 | no | — |
| DeepSeek V3.1 (Reasoning) | 21.60 | $0.062454 | no | — |
| GLM 4.6 | 21.56 | $0.04358 | no | — |
| Qwen3 VL 235B A22B (Reasoning) | 21.44 | $0.064423 | no | — |
| DeepSeek V3.1 Terminus (Non-reasoning) | 21.41 | $0.022504 | no | — |
| Apriel-v1.6-15B-Thinker | 21.37 | — | no | — |
| DeepSeek V3.2 Exp (Non-reasoning) | 21.33 | $0.017076 | no | — |
| Kimi K2 0905 | 21.15 | $0.055817 | no | — |
| DeepSeek V3.1 (Non-reasoning) | 21.05 | $0.050689 | no | — |
| GPT-5 nano (high) | 20.95 | $0.0047759 | no | — |
| DeepSeek V3.2 | 20.70 | $0.012858 | no | — |
| Mi:dm K 2.5 Pro Preview | 20.68 | — | no | — |
| Nova 2.0 Lite (high) | 20.66 | $0.032225 | no | — |
| Claude 4.5 Sonnet (Non-reasoning) | 20.64 | $0.28381 | no | — |
| Qwen3 235B A22B 2507 (Reasoning) | 20.50 | $0.030958 | no | — |
| Nova 2.0 Lite (high) | 20.50 | $0.060754 | no | — |
| Kimi K2 | 20.38 | $0.054568 | no | — |
| Nova 2.0 Lite (medium) | 20.37 | $0.037612 | no | — |
| EXAONE 4.5 33B | 20.31 | — | no | — |
| Seed-OSS-36B-Instruct | 20.26 | $0.012602 | no | — |
| Gemma 4 26B A4B (Non-reasoning) | 20.25 | $0.0094515 | no | — |
| DeepSeek R1 0528 (May '25) | 20.19 | $0.089381 | no | — |
| o1-preview | 20.10 | $1.4514 | no | — |
| Mistral Small 4 (Reasoning) | 20.05 | $0.01253 | no | — |
| Gemini 2.5 Flash (Reasoning) | 19.95 | $0.03463 | no | — |
| GPT-5 nano (high) | 19.87 | $0.010205 | no | — |
| grok-4.1-fast | 19.67 | — | no | — |
| GLM-4.5 (Reasoning) | 19.63 | — | no | — |
| GPT-5 nano (medium) | 19.60 | $0.0054877 | no | — |
| GLM-4.5 (Reasoning) | 19.49 | $0.038759 | no | — |
| Qwen3 Max (Preview) | 19.48 | $0.12365 | no | — |
| Qwen3.5 9B (Non-reasoning) | 19.44 | $0.0075241 | no | price-close / capability-behind |
| Qwen3 VL 32B (Reasoning) | 19.35 | $0.030505 | no | — |
| Cogito v2.1 (Reasoning) | 19.35 | $0.050776 | no | — |
| Nemotron Cascade 2 30B A3B | 19.26 | — | no | — |
| HyperNova 60B 2605 | 19.20 | $0.0091062 | no | — |
| Qwen3.5 Omni Flash | 19.09 | $0.012735 | no | — |
| o3-mini | 19.09 | $0.08593 | no | — |
| Qwen3.5 4B (Reasoning) | 19.07 | $0.0034276 | no | — |
| openai/gpt-oss-120b | 19.04 | $0.010803 | no | — |
| o1-pro | 18.99 | $14.534 | no | — |
| Nova 2.0 Pro Preview (low) | 18.93 | $0.13124 | no | — |
| Trinity Large Thinking | 18.91 | $0.016555 | no | — |
| DeepSeek V3.2 Exp (Non-reasoning) | 18.85 | $0.012858 | no | — |
| Gemini 2.5 Flash Preview (Sep '25) (Non-reasoning) | 18.83 | — | no | — |
| Magistral Medium 1.2 | 18.82 | $0.14336 | no | — |
| Claude 4 Sonnet (Non-reasoning) | 18.80 | $0.28381 | no | — |
| Grok Code Fast 1 | 18.80 | — | no | — |
| JT-MINI | 18.67 | — | no | — |
| Claude 4 Opus (Non-reasoning) | 18.61 | $1.5486 | no | — |
| GLM-4.6V (Reasoning) | 18.60 | $0.019201 | no | — |
| Qwen3 235B A22B 2507 Instruct | 18.56 | $0.021722 | no | — |
| Ring-1T | 18.50 | — | no | — |
| DeepSeek V3.1 Terminus (Non-reasoning) | 18.40 | $0.019328 | no | — |
| GLM-4.5-Air | 18.12 | $0.014725 | no | — |
| INTELLECT-3 | 18.02 | — | no | — |
| Sonar Reasoning Pro | 18.00 | — | no | — |
| Claude 4.5 Haiku (Non-reasoning) | 17.97 | $0.089126 | no | — |
| Qwen3 Next 80B A3B (Reasoning) | 17.85 | $0.028197 | no | — |
| openai/gpt-oss-20b | 17.85 | $0.003664 | no | — |
| DeepSeek V3.1 (Non-reasoning) | 17.81 | $0.037589 | no | — |
| Mi:dm K 2.5 Pro | 17.75 | — | no | — |
| GPT-5.4 nano (Non-Reasoning) | 17.70 | $0.015779 | no | — |
| Grok 3 | 17.67 | $0.33683 | no | — |
| Gemini 2.5 Flash Preview (Reasoning) | 17.62 | — | no | — |
| GPT-5.1 (Non-reasoning) | 17.57 | $0.11022 | no | — |
| Grok 4 Fast Reasoning | 17.52 | $0.011603 | no | — |
| Gemini 2.5 Flash Preview (Sep '25) (Non-reasoning) | 17.44 | — | no | — |
| MiniMax M1 80k | 17.44 | $0.046666 | no | — |
| K2-V2 (high) | 17.40 | — | no | — |
| Ling 2.6 Flash | 17.40 | $0.006587 | no | price-close / capability-behind |
| Devstral 2 | 17.31 | — | no | — |
| LongCat Flash Lite | 17.31 | — | no | — |
| DeepSeek R1 (Jan '25) | 16.92 | $0.19333 | no | — |
| Grok 4.1 Fast (Non-reasoning) | 16.88 | — | no | — |
| HyperCLOVA X SEED Think (32B) | 16.84 | — | no | — |
| GPT-5.4 mini (Non-Reasoning) | 16.71 | $0.055288 | no | — |
| K2 Think V2 | 16.67 | — | no | — |
| GPT-4.1 | 16.61 | $0.15648 | no | — |
| gpt-oss-120b (low) | 16.57 | $0.010552 | no | — |
| NVIDIA Nemotron 3 Nano 30B A3B (Reasoning) | 16.50 | $0.0048584 | no | — |
| Grok 4 Fast (Non-reasoning) | 16.47 | $0.010827 | no | — |
| Nova 2.0 Lite (low) | 16.45 | $0.032247 | no | — |
| Nova 2.0 Pro Preview (Non-reasoning) | 16.42 | $0.46701 | no | — |
| Nova 2.0 Omni (low) | 16.30 | $0.033787 | no | — |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Reasoning) | 16.26 | $0.0078123 | no | — |
| Qwen3 235B A22B (Reasoning) | 16.12 | $0.11744 | no | — |
| Qwen3 VL 30B A3B (Reasoning) | 16.07 | $0.027927 | no | — |
| Qwen3 Coder 480B A35B Instruct | 16.03 | $0.11664 | no | — |
| Qwen3 VL 235B A22B Instruct | 15.87 | $0.04007 | no | — |
| Claude 3.7 Sonnet (Non-reasoning) | 15.86 | $0.28381 | no | — |
| Devstral Small 2 | 15.84 | — | no | — |
| Qwen3.5 4B (Non-reasoning) | 15.70 | $0.0032935 | no | — |
| GPT-5 (minimal) | 15.64 | $0.11827 | no | — |
| GLM-4.7-Flash (Non-reasoning) | 15.56 | $0.0054331 | YES | — |
| Motif-2-12.7B-Reasoning | 15.54 | — | no | — |
| K-EXAONE (Non-reasoning) | 15.53 | — | no | — |
| Gemini 2.5 Flash (Non-reasoning) | 15.39 | $0.032225 | no | — |
| o3-mini (high) | 15.36 | $0.089396 | no | — |
| gpt-oss-20B (low) | 15.26 | $0.0042047 | no | — |
| Solar Open 100B (Reasoning) | 15.20 | — | no | — |
| Grok 3 Reasoning Beta | 15.17 | — | no | — |
| Qwen3 Next 80B A3B Instruct | 15.15 | $0.02541 | no | capability-close / price-heavy |
| Qwen3 4B 2507 (Reasoning) | 15.15 | — | no | — |
| Llama Nemotron Super 49B v1.5 (Reasoning) | 15.02 | $0.014689 | no | — |
| gpt-oss-20B (high) | 14.89 | $0.010323 | no | — |
| GPT-5 (ChatGPT) | 14.87 | $0.12839 | no | — |
| GPT-4.1 mini | 14.86 | $0.029059 | no | — |
| Ling-1T | 14.83 | — | no | — |
| Gemini 2.0 Flash Thinking Experimental (Jan '25) | 14.80 | — | no | — |
| DeepSeek V3 0324 | 14.71 | $0.026423 | no | — |
| Mistral Large 3 | 14.63 | $0.031704 | no | capability-close / price-heavy |
| K2-V2 (high) | 14.19 | — | no | — |
| Gemini 2.0 Pro Experimental (Feb '25) | 14.18 | — | no | — |
| Gemini 2.5 Flash (Non-reasoning) | 14.14 | $0.029032 | no | — |
| K2-V2 (medium) | 14.13 | — | no | — |
| Mistral Medium 3.1 | 14.07 | $0.034626 | no | capability-close / price-heavy |
| Claude 3.5 Sonnet (Oct '24) | 14.04 | $0.27405 | no | — |
| GPT-5 mini (minimal) | 14.03 | $0.021437 | no | — |
| EXAONE 4.0 32B (Reasoning) | 14.02 | — | no | — |
| DiffusionGemma 26B A4B | 14.02 | — | no | — |
| o1-mini | 13.99 | — | no | — |
| Magistral Small 1.2 | 13.82 | $0.036175 | no | — |
| Qwen3 30B A3B 2507 (Reasoning) | 13.74 | $0.027647 | no | — |
| Tri-21B-think Preview | 13.60 | — | no | — |
| GPT-4.5 (Preview) | 13.59 | — | no | — |
| Falcon-H1R-7B | 13.49 | — | no | — |
| Qwen3 VL 32B Instruct | 13.48 | $0.026223 | no | — |
| Nemotron 3 Nano Omni 30B A3B Reasoning | 13.35 | $0.0069442 | no | — |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Non-reasoning) | 13.32 | $0.0070454 | no | — |
| Llama 4 Maverick | 13.28 | $0.023699 | no | — |
| Nova 2.0 Pro Preview (Non-reasoning) | 13.27 | $0.14219 | no | — |
| Llama 3.3 Nemotron Super 49B v1 (Reasoning) | 13.26 | — | no | — |
| Solar Pro 3 | 13.21 | $0.010803 | no | — |
| Gemma 4 12B (Non-reasoning) | 13.19 | $0.0096685 | no | — |
| Qwen3 32B (Reasoning) | 13.13 | $0.013036 | no | — |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Non-reasoning) | 13.10 | $0.0084156 | no | — |
| DeepSeek R1 Distill Qwen 32B | 13.07 | — | no | — |
| Qwen3 VL 30B A3B Instruct | 13.06 | $0.021405 | no | — |
| Qwen3 Omni 30B A3B (Reasoning) | 12.92 | $0.024414 | no | — |
| Solar Pro 2 (Reasoning) | 12.80 | — | no | — |
| Hermes 4 - Llama-3.1 70B (Reasoning) | 12.77 | $0.010746 | no | — |
| DeepSeek R1 0528 Qwen3 8B | 12.67 | — | no | — |
| Claude 3 Opus | 12.66 | $1.4704 | no | — |
| Ring-flash-2.0 | 12.65 | $0.010081 | no | — |
| DeepSeek V3 (Dec '24) | 12.63 | $0.021026 | no | — |
| Gemini 2.5 Flash-Lite (Reasoning) | 12.61 | $0.0089426 | no | — |
| Qwen3 30B A3B (Reasoning) | 12.59 | $0.018337 | no | — |
| NVIDIA Nemotron Nano 12B v2 VL (Reasoning) | 12.54 | $0.01894 | no | — |
| GLM-4.5V (Reasoning) | 12.52 | $0.039586 | no | — |
| Solar Pro 2 (Preview) (Reasoning) | 12.50 | — | no | — |
| Gemini 1.5 Pro (Sep '24) | 12.44 | — | no | — |
| Magistral Medium 1 | 12.38 | — | no | — |
| Ling-flash-2.0 | 12.35 | $0.0098298 | no | — |
| Mistral Small 4 (Non-reasoning) | 12.34 | $0.010707 | no | — |
| Tri-21B-Think | 12.30 | — | no | — |
| Qwen3 Coder 30B A3B Instruct | 12.27 | $0.029386 | no | — |
| Hermes 4 - Llama-3.1 405B (Reasoning) | 12.16 | $0.084718 | no | — |
| QwQ 32B | 12.13 | $0.031557 | no | — |
| Olmo 3.1 32B Think | 12.12 | — | no | — |
| NVIDIA Nemotron Nano 9B V2 (Non-reasoning) | 12.11 | $0.0033505 | no | — |
| Claude 3.5 Haiku | 12.10 | $0.03087 | no | — |
| NVIDIA Nemotron Nano 9B V2 (Reasoning) | 12.07 | $0.0031819 | no | price-close / capability-behind |
| Qwen3 30B A3B 2507 Instruct | 11.96 | $0.017211 | no | — |
| Sarvam 105B (high) | 11.94 | $0.0060991 | no | — |
| MiniCPM5-1B (Reasoning) | 11.93 | — | no | — |
| Sarvam 105B (high) | 11.90 | $0.0028395 | no | — |
| Claude 3.5 Sonnet (June '24) | 11.89 | $0.27405 | no | — |
| Nova 2.0 Lite (Non-reasoning) | 11.83 | $0.12715 | no | — |
| Devstral Small (May '25) | 11.81 | — | no | — |
| Llama 3.1 Nemotron Ultra 253B v1 (Reasoning) | 11.77 | $0.06501 | no | — |
| Mistral Small 3.1 | 11.73 | $0.0089731 | no | — |
| MiniCPM5-1B (Non-reasoning) | 11.72 | — | no | — |
| MiniMax M1 40k | 11.70 | — | no | — |
| DeepSeek R1 Distill Qwen 14B | 11.70 | — | no | — |
| G9v3-3B | 11.70 | — | no | — |
| Gemini 2.5 Flash Preview (Non-reasoning) | 11.66 | — | no | — |
| GPT-4o (May '24) | 11.64 | $0.362 | no | — |
| Mistral Medium 3 | 11.63 | $0.033477 | no | — |
| DeepSeek R1 Distill Llama 70B | 11.61 | $0.034058 | no | — |
| Gemini 2.5 Flash Preview (Non-reasoning) | 11.60 | — | no | — |
| Sonar Reasoning | 11.60 | — | no | — |
| Qwen3 14B (Reasoning) | 11.55 | $0.037849 | no | — |
| Celeris-1 | 11.48 | $0.013698 | no | — |
| Qwen3 14B (Non-reasoning) | 11.43 | $0.026394 | no | — |
| Nova 2.0 Lite (Non-reasoning) | 11.22 | $0.032225 | no | — |
| Magistral Small 1 | 11.21 | — | no | — |
| GPT-4o (March 2025, chatgpt-4o-latest) | 11.16 | — | no | — |
| GLM-4.6V (Non-reasoning) | 10.98 | $0.012525 | no | — |
| Nova 2.0 Omni (Non-reasoning) | 10.89 | $0.032225 | no | — |
| Qwen3 235B A22B (Non-reasoning) | 10.86 | $0.054864 | no | — |
| Gemini 2.0 Flash (Feb '25) | 10.81 | $0.0088201 | no | — |
| Nova Premier | 10.81 | $0.22446 | no | — |
| Olmo 3 32B Think | 10.69 | — | no | — |
| Gemini 2.0 Flash (experimental) | 10.64 | — | no | — |
| Nova 2.0 Omni (Non-reasoning) | 10.53 | $0.17066 | no | — |
| Gemma 4 E4B (Reasoning) | 10.50 | $0.0014415 | YES | — |
| GPT-4 Turbo | 10.49 | $0.74634 | no | — |
| Llama 3.1 Nemotron Nano 4B v1.1 (Reasoning) | 10.41 | — | no | — |
| Ministral 3 14B | 10.39 | $0.0088432 | no | capability-close / price-heavy |
| Qwen3 VL 8B (Reasoning) | 10.35 | $0.030454 | no | — |
| Qwen2.5 Max | 10.17 | $0.10654 | no | — |
| ERNIE 4.5 300B A47B | 10.09 | $0.020415 | no | — |
| GLM-4.6V (Non-reasoning) | 9.95 | $0.019466 | no | — |
| Solar Pro 2 (Preview) (Non-reasoning) | 9.90 | — | no | — |
| mistralai/mistral-large-2512 | 9.78 | — | no | — |
| Devstral Medium | 9.66 | $0.048781 | no | — |
| Qwen3 235B A22B (Non-reasoning) | 9.61 | $0.054812 | no | — |
| Qwen3 4B 2507 Instruct | 9.61 | — | no | — |
| Mistral Small 3.2 | 9.53 | $0.0072922 | no | — |
| GPT-4o (Aug '24) | 9.49 | $0.18667 | no | — |
| Sonar | 9.40 | — | no | — |
| Kimi Linear 48B A3B Instruct | 9.39 | — | no | — |
| Devstral Small (Jul '25) | 9.34 | $0.012508 | no | — |
| Nanbeige4.1-3B | 9.34 | — | no | — |
| K2-V2 (low) | 9.32 | — | no | — |
| Step3 VL 10B | 9.30 | — | no | — |
| QwQ 32B-Preview | 9.22 | — | no | — |
| QwQ 32B-Preview | 9.10 | — | no | — |
| Sonar Pro | 9.10 | — | no | — |
| Gemini 1.5 Pro (May '24) | 9.01 | — | no | — |
| GPT-4o (Nov '24) | 8.92 | $0.18328 | no | — |
| Gemini 2.5 Flash-Lite (Non-reasoning) | 8.85 | $0.0070454 | no | — |
| Olmo 3 7B Think | 8.82 | — | no | — |
| Gemma 4 E4B (Non-reasoning) | 8.81 | $0.0014415 | no | near-frontier |
| Hermes 4 - Llama-3.1 405B (Non-reasoning) | 8.80 | $0.095707 | no | capability-close / price-heavy |
| EXAONE 4.0 32B (Non-reasoning) | 8.80 | — | no | — |
| Ministral 3 8B | 8.79 | $0.006869 | no | capability-close / price-heavy |
| Solar Pro 2 (Non-reasoning) | 8.71 | — | no | — |
| Gemini 2.0 Flash-Lite (Feb '25) | 8.69 | — | no | — |
| Llama Nemotron Super 49B v1.5 (Non-reasoning) | 8.68 | $0.010798 | no | — |
| Qwen3 32B (Non-reasoning) | 8.63 | $0.0069657 | no | — |
| Qwen3 VL 8B Instruct | 8.61 | $0.017533 | no | capability-close / price-heavy |
| Gemini 2.0 Flash-Lite (Preview) | 8.50 | — | no | — |
| Llama 3.3 Nemotron Super 49B v1 (Non-reasoning) | 8.47 | — | no | — |
| Qwen2.5 Instruct 72B | 8.41 | $0.018135 | no | — |
| Granite 4.1 30B | 8.38 | — | no | — |
| GPT-4.1 nano | 8.36 | $0.0084229 | no | — |
| GPT-5 nano (minimal) | 8.34 | $0.0058449 | no | — |
| DeepSeek R1 Distill Llama 8B | 8.32 | — | no | — |
| LFM2.5-2.6B | 8.27 | — | no | — |
| Qwen3 Omni 30B A3B Instruct | 8.24 | $0.022887 | no | — |
| Qwen3 4B (Reasoning) | 8.22 | $0.015266 | no | — |
| LFM2.5-8B-A1B | 8.21 | — | no | — |
| GPT-4o (ChatGPT) | 8.17 | — | no | — |
| Qwen3 VL 4B (Reasoning) | 8.16 | — | no | — |
| Mistral Large 2 (Nov '24) | 8.13 | $0.10455 | no | — |
| Llama 4 Scout | 8.13 | $0.013819 | no | — |
| Llama 3.1 Tulu3 405B | 8.10 | — | no | — |
| Qwen3 32B (Non-reasoning) | 8.01 | $0.011564 | no | — |
| Gemma 4 E2B (Reasoning) | 7.97 | — | no | — |
| Grok 2 (Dec '24) | 7.92 | — | no | — |
| Gemini 1.5 Flash (Sep '24) | 7.88 | — | no | — |
| Llama 3.3 Instruct 70B | 7.86 | $0.032047 | no | — |
| GPT-4 | 7.80 | $1.9322 | no | — |
| NVIDIA Nemotron 3 Nano 4B | 7.71 | — | no | — |
| Hermes 4 - Llama-3.1 405B (Non-reasoning) | 7.57 | $0.06927 | no | — |
| Qwen2.5 Instruct 32B | 7.45 | — | no | — |
| Grok Beta | 7.40 | — | no | — |
| Qwen3 8B (Reasoning) | 7.40 | $0.019824 | no | — |
| NVIDIA Nemotron 3 Nano 30B A3B (Non-reasoning) | 7.39 | $0.0062524 | no | — |
| NVIDIA Nemotron Nano 9B V2 (Non-reasoning) | 7.38 | $0.0062016 | no | — |
| Gemini 1.0 Ultra | 7.30 | — | no | — |
| Qwen3 30B A3B (Non-reasoning) | 7.29 | $0.014631 | no | — |
| Qwen2.5 Instruct 32B | 7.20 | — | no | — |
| Ling-mini-2.0 | 7.09 | — | no | — |
| GPT-4o mini | 7.09 | $0.010738 | no | — |
| Command A | 7.07 | $0.2143 | no | — |
| Qwen3 14B (Non-reasoning) | 7.02 | $0.012481 | no | — |
| Qwen2.5 Coder Instruct 32B | 7.01 | — | no | — |
| GLM-4.5V (Non-reasoning) | 7.00 | $0.024775 | no | — |
| Qwen3 1.7B (Reasoning) | 6.98 | — | no | — |
| Gemini 2.5 Flash-Lite (Non-reasoning) | 6.92 | $0.0070451 | no | — |
| Hermes 4 - Llama-3.1 70B (Non-reasoning) | 6.90 | $0.014291 | no | — |
| Llama 3.1 Nemotron Instruct 70B | 6.87 | $0.049497 | no | — |
| Llama 3.1 Instruct 405B | 6.87 | $0.4077 | no | — |
| Gemma 3 27B Instruct | 6.82 | $0.0098818 | no | — |
| Qwen3 30B A3B (Non-reasoning) | 6.80 | $0.0064199 | no | — |
| Qwen3 4B (Non-reasoning) | 6.77 | $0.0050759 | no | — |
| Llama Nemotron Super 49B v1.5 (Non-reasoning) | 6.71 | $0.015332 | no | — |
| Qwen3 8B (Non-reasoning) | 6.68 | $0.012912 | no | — |
| GLM-4.5V (Non-reasoning) | 6.67 | $0.040425 | no | — |
| Granite 4.1 8B | 6.65 | $0.0028896 | no | — |
| NVIDIA Nemotron 3 Nano 30B A3B (Non-reasoning) | 6.65 | $0.0033926 | no | — |
| DeepSeek-V2.5 (Dec '24) | 6.64 | — | no | — |
| NVIDIA Nemotron Nano 12B v2 VL (Non-reasoning) | 6.64 | $0.012695 | no | — |
| Nova Pro | 6.62 | $0.069561 | no | — |
| Pixtral Large | 6.60 | $0.11482 | no | — |
| Exaone 4.0 1.2B (Reasoning) | 6.58 | — | no | — |
| Llama 3.3 Nemotron Super 49B v1 (Non-reasoning) | 6.57 | — | no | — |
| Qwen3.5 2B (Reasoning) | 6.53 | $0.0065687 | no | — |
| Gemini 2.0 Flash Thinking Experimental (Dec '24) | 6.51 | — | no | — |
| DeepSeek-V2.5 | 6.51 | — | no | — |
| Qwen3 4B (Non-reasoning) | 6.50 | — | no | — |
| Sarvam 30B (high) | 6.40 | $0.0017504 | no | — |
| Qwen3 VL 4B Instruct | 6.39 | — | no | — |
| Olmo 3.1 32B Instruct | 6.33 | — | no | — |
| Mistral Saba | 6.32 | — | no | — |
| Gemma 4 E2B (Non-reasoning) | 6.31 | — | no | — |
| Hermes 4 - Llama-3.1 70B (Non-reasoning) | 6.18 | $0.0081624 | no | — |
| R1 1776 | 6.16 | — | no | — |
| Qwen2.5 Turbo | 6.15 | $0.003411 | no | — |
| Reka Flash (Sep '24) | 6.15 | $0.014499 | no | — |
| Reka Flash 3 | 6.14 | $0.014499 | no | — |
| Llama 3.2 Instruct 90B (Vision) | 6.12 | $0.054766 | no | — |
| Nova Lite | 6.10 | $0.0050577 | no | — |
| Ministral 3 3B | 6.03 | $0.0046144 | no | — |
| EXAONE 4.0 32B (Non-reasoning) | 6.01 | — | no | — |
| Solar Mini | 6.00 | $0.0055525 | no | — |
| Grok-1 | 5.92 | — | no | — |
| Mistral Small 3 | 5.91 | $0.0057821 | no | — |
| Claude 2.1 | 5.88 | — | no | — |
| Qwen2 Instruct 72B | 5.86 | — | no | — |
| Olmo 3 7B Instruct | 5.85 | $0.0069061 | no | — |
| Mistral Large 2 (Jul '24) | 5.80 | $0.1391 | no | — |
| Llama 3.1 Instruct 70B | 5.76 | $0.030554 | no | — |
| Phi-4 | 5.54 | $0.008877 | no | — |
| Claude 2.0 | 5.46 | — | no | — |
| Exaone 4.0 1.2B (Non-reasoning) | 5.44 | — | no | — |
| Granite 4.0 H Small | 5.44 | $0.0040529 | no | — |
| Gemini 1.5 Flash-8B | 5.36 | — | no | — |
| Llama 3.1 Instruct 8B | 5.35 | $0.0022767 | no | — |
| DeepHermes 3 - Mistral 24B Preview (Non-reasoning) | 5.31 | — | no | — |
| Qwen3.5 2B (Non-reasoning) | 5.21 | $0.0029064 | no | — |
| Qwen3 8B (Non-reasoning) | 5.07 | $0.014985 | no | — |
| Gemma 3 12B Instruct | 5.05 | $0.011167 | no | — |
| DeepHermes 3 - Mistral 24B Preview (Non-reasoning) | 5.00 | — | no | — |
| DeepSeek R1 Distill Qwen 1.5B | 5.00 | — | no | — |
| Jamba 1.5 Large | 4.97 | $0.16038 | no | — |
| Hermes 3 - Llama-3.1 70B | 4.94 | $0.024484 | no | — |
| DeepSeek-Coder-V2 | 4.88 | — | no | — |
| GPT-3.5 Turbo | 4.85 | $0.032726 | no | — |
| Jamba 1.6 Large | 4.85 | $0.1327 | no | — |
| LFM2 24B A2B | 4.77 | $0.0045435 | no | — |
| Gemini 1.5 Flash (May '24) | 4.76 | — | no | — |
| Jamba 1.7 Large | 4.65 | $0.46868 | no | — |
| NVIDIA Nemotron Nano 12B v2 VL (Non-reasoning) | 4.58 | $0.031833 | no | — |
| Claude 3 Sonnet | 4.57 | $0.22436 | no | — |
| Nova Micro | 4.54 | $0.0024572 | no | — |
| OLMo 2 32B | 4.53 | — | no | — |
| Jamba Reasoning 3B | 4.48 | — | no | — |
| Mistral Small (Sep '24) | 4.48 | $0.012575 | no | — |
| Gemma 3n E4B Instruct Preview (May '25) | 4.38 | — | no | — |
| Phi-4 Multimodal Instruct | 4.37 | — | no | — |
| Qwen2.5 Coder Instruct 7B  | 4.29 | — | no | — |
| Mistral Large (Feb '24) | 4.26 | $0.28679 | no | — |
| Mixtral 8x22B Instruct | 4.18 | — | no | — |
| Qwen1.5 Chat 110B | 4.08 | — | no | — |
| Llama 2 Chat 7B | 4.08 | $0.0038172 | no | — |
| Qwen3 0.6B (Reasoning) | 4.07 | — | no | — |
| Phi-3 Mini Instruct 3.8B | 4.03 | — | no | — |
| Llama 3.2 Instruct 3B | 4.00 | $0.006167 | no | — |
| Phi-4 Mini Instruct | 3.99 | — | no | — |
| LFM2 8B A1B | 3.95 | — | no | — |
| Qwen1.5 Chat 110B | 3.70 | — | no | — |
| Claude 3 Haiku | 3.68 | $0.022711 | no | — |
| Granite 4.1 3B | 3.62 | — | no | — |
| OLMo 2 7B | 3.55 | — | no | — |
| DeepSeek-V2-Chat | 3.47 | — | no | — |
| Molmo 7B-D | 3.45 | — | no | — |
| Mistral Small (Feb '24) | 3.41 | $0.013877 | no | — |
| Mistral Medium | 3.40 | $0.13935 | no | — |
| Qwen3.5 0.8B (Reasoning) | 3.39 | $0.0026599 | no | — |
| LFM2 2.6B | 3.33 | — | no | — |
| Llama 3 Instruct 70B | 3.29 | $0.051034 | no | — |
| Llama 3.2 Instruct 11B (Vision) | 3.28 | $0.012597 | no | — |
| Qwen3 0.6B (Non-reasoning) | 3.21 | — | no | — |
| Arctic Instruct | 3.21 | — | no | — |
| Qwen Chat 72B | 3.21 | — | no | — |
| LFM 40B | 3.18 | — | no | — |
| Claude Instant | 3.15 | — | no | — |
| Granite 4.0 H 1B | 3.13 | — | no | — |
| PALM-2 | 3.08 | — | no | — |
| Granite 3.3 8B (Non-reasoning) | 2.96 | $0.0028439 | no | — |
| Granite 4.0 Micro | 2.95 | — | no | — |
| Qwen3 1.7B (Non-reasoning) | 2.93 | — | no | — |
| Gemini 1.0 Pro | 2.91 | — | no | — |
| DeepSeek Coder V2 Lite Instruct | 2.90 | — | no | — |
| DeepSeek LLM 67B Chat (V1) | 2.80 | — | no | — |
| Llama 2 Chat 70B | 2.80 | — | no | — |
| Llama 2 Chat 13B | 2.80 | — | no | — |
| Command-R+ (Apr '24) | 2.79 | $0.27405 | no | — |
| OpenChat 3.5 (1210) | 2.78 | — | no | — |
| DBRX Instruct | 2.78 | — | no | — |
| Exaone 4.0 1.2B (Non-reasoning) | 2.77 | — | no | — |
| MiniCPM-V 4.6 1.3B | 2.76 | — | no | — |
| Jamba 1.7 Mini | 2.74 | — | no | — |
| Granite 4.0 1B | 2.73 | — | no | — |
| Gemma 3 270M | 2.68 | — | no | — |
| Gemma 3n E4B Instruct | 2.67 | $0.0027787 | no | — |
| Qwen3.5 0.8B (Non-reasoning) | 2.66 | $0.0014213 | no | — |
| Qwen3 1.7B (Reasoning) | 2.63 | $0.014783 | no | — |
| Sarvam M (Reasoning) | 2.60 | — | no | — |
| LFM2.5-1.2B-Thinking | 2.52 | — | no | — |
| LFM2.5-1.2B-Instruct | 2.50 | — | no | — |
| Jamba 1.5 Mini | 2.50 | $0.010342 | no | — |
| Gemma 3n E2B Instruct | 2.48 | — | no | — |
| Gemma 3 4B Instruct | 2.47 | $0.0035156 | no | — |
| Jamba 1.6 Mini | 2.33 | $0.010051 | no | — |
| DeepHermes 3 - Llama-3.1 8B Preview (Non-reasoning) | 2.29 | — | no | — |
| Mixtral 8x7B Instruct | 2.21 | $0.021419 | no | — |
| Apertus 70B Instruct | 2.20 | $0.05968 | no | — |
| LFM2 1.2B | 2.01 | — | no | — |
| Gemma 3 1B Instruct | 1.96 | — | no | — |
| Command-R (Mar '24) | 1.92 | $0.032726 | no | — |
| Llama 65B | 1.92 | — | no | — |
| Mistral 7B Instruct | 1.92 | $0.0091976 | no | — |
| Qwen Chat 14B | 1.92 | — | no | — |
| DeepHermes 3 - Llama-3.1 8B Preview (Non-reasoning) | 1.90 | — | no | — |
| Molmo2-8B | 1.81 | — | no | — |
| Granite 4.0 H 350M | 1.81 | — | no | — |
| Granite 3.3 8B (Non-reasoning) | 1.75 | $0.0070694 | no | — |
| Llama 3.2 Instruct 1B | 1.74 | $0.0020919 | no | — |
| Granite 4.0 350M | 1.71 | — | no | — |
| Qwen3 1.7B (Non-reasoning) | 1.53 | $0.0092152 | no | — |
| Qwen3 0.6B (Reasoning) | 1.28 | $0.012478 | no | — |
| Llama 3 Instruct 8B | 1.10 | $0.0027449 | no | — |
| LFM2.5-VL-1.6B | 1.00 | — | no | — |
| Apertus 8B Instruct | 1.00 | $0.005016 | no | — |
| Qwen3 0.6B (Non-reasoning) | 1.00 | $0.01165 | no | — |
| Tiny Aya Global | 1.00 | — | no | — |
| Command A 03 2025 | 0.00 | — | no | — |

## Top contested region

The upper contest zone includes configurations at capability ≥50, spanning the A+/S/S+ boundary neighborhood where small capability differences can carry large cost penalties.

| Model/configuration | Tier | Capability | Cost | Pareto | Closest economic verdict |
|---|---|---:|---:|---|---|
| Claude Opus 5 (max) | T1 | 61.15 | $2.2018 | YES | STRICT FRONTIER |
| Claude Opus 5 (xhigh) | T1 | 61.02 | $1.0162 | YES | STRICT FRONTIER |
| Claude Opus 5 (Adaptive Reasoning, Max Effort) | T1 | 60.67 | $0.48631 | no | dominated / outside near band |
| GPT-5.6 Sol (max) | T1 | 60.65 | $1.5702 | YES | STRICT FRONTIER |
| Claude Fable 5 (max) | T1 | 60.02 | $2.8223 | no | near-frontier |
| Kimi K3 (max) | T2 | 59.90 | $0.92963 | YES | STRICT FRONTIER |
| Claude Opus 5 (high) | T2 | 59.66 | $0.79948 | no | near-frontier |
| Claude Fable 5 (Adaptive Reasoning, Max Effort, Opus 4.8 Fallback) | T2 | 59.61 | $1.0099 | no | dominated / outside near band |
| GPT-5.6 Sol (max) | T2 | 59.35 | $0.53209 | no | dominated / outside near band |
| Grok 4.6 (high) | T2 | 59.12 | $0.14385 | no | dominated / outside near band |
| Claude Fable 5 (xhigh) | T2 | 59.03 | $1.7571 | no | near-frontier |
| GPT-5.6 Sol (xhigh) | T2 | 58.95 | $0.70321 | YES | STRICT FRONTIER |
| Grok 4.6 (xhigh) | T2 | 58.33 | $0.14385 | no | dominated / outside near band |
| Kimi K3 | T2 | 58.30 | $0.27405 | YES | STRICT FRONTIER |
| Claude Opus 4.8 (xhigh) | T2 | 58.22 | — | no | dominated / outside near band |
| Claude Opus 5 (medium) | T2 | 57.88 | $0.56949 | no | capability-close / price-heavy |
| GLM-5.3 (max) | T2 | 57.67 | $0.10106 | no | dominated / outside near band |
| GPT-5.5 (xhigh) | T2 | 57.49 | $1.3827 | no | near-frontier |
| Grok 4.6 (medium) | T2 | 57.27 | $0.14385 | no | dominated / outside near band |
| GPT-5.6 Sol (high) | T2 | 57.27 | $0.53914 | no | capability-close / price-heavy |
| Muse Spark 1.2 (xhigh, Contributor pricing) | T2 | 57.00 | $0.12719 | YES | STRICT FRONTIER |
| Muse Spark 1.2 (xhigh, Standard pricing) | T2 | 57.00 | $0.32331 | no | capability-close / price-heavy |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.37225 | no | capability-close / price-heavy |
| GPT-5.6 Terra (max) | T2 | 56.93 | $0.20251 | no | dominated / outside near band |
| Qwen3.8 Max (xhigh) | T2 | 56.77 | $0.89547 | no | price-close / capability-behind |
| GPT-5.5 (high) | T2 | 56.43 | $0.71786 | no | capability-close / price-heavy |
| Gemini 3.7 Flash (high) | T2 | 56.41 | $0.065809 | no | dominated / outside near band |
| Claude Opus 4.8 (Adaptive Reasoning, Max Effort) | T2 | 56.38 | $0.48631 | no | dominated / outside near band |
| GPT-5.6 Sol (medium) | T2 | 56.16 | $0.40732 | no | dominated / outside near band |
| Qwen3.8 Max | T3 | 55.85 | $0.14385 | no | dominated / outside near band |
| GPT-5.6 Luna (max) | T3 | 55.83 | $0.078429 | no | capability-close / price-heavy |
| Qwen3.8 2.4T A95B | T3 | 55.68 | $0.14385 | no | dominated / outside near band |
| Claude Opus 4.8 (max) | T3 | 55.50 | $1.7767 | no | dominated / outside near band |
| Muse Spark 1.2 (xhigh) | T3 | 55.35 | $0.093226 | no | dominated / outside near band |
| GPT-5.6 Terra (max) | T3 | 55.22 | $0.77262 | no | price-close / capability-behind |
| Muse Spark 1.1 (xhigh effort) | T3 | 55.17 | — | no | dominated / outside near band |
| Claude Opus 4.7 (xhigh effort) | T3 | 54.97 | — | no | dominated / outside near band |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | T3 | 54.97 | $0.48631 | no | dominated / outside near band |
| Grok 4.5 | T3 | 54.35 | $0.25235 | no | dominated / outside near band |
| Claude Sonnet 5 (Adaptive Reasoning, Max Effort) | T3 | 54.33 | $0.18509 | no | dominated / outside near band |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | T3 | 54.28 | $1.9943 | no | dominated / outside near band |
| Claude Sonnet 5 (max) | T3 | 54.04 | $1.9591 | no | dominated / outside near band |
| openai/gpt-5.5 | T3 | 53.76 | $0.53209 | no | dominated / outside near band |
| Gemini 3.7 Flash (medium) | T3 | 53.38 | $0.065809 | no | dominated / outside near band |
| GPT 5.4 | T3 | 53.08 | $0.25622 | no | dominated / outside near band |
| Muse Spark 1.1 (high effort) | T3 | 53.08 | — | no | dominated / outside near band |
| Grok 4.3 (high) | T3 | 53.00 | $0.14774 | no | dominated / outside near band |
| GPT-5.6 Luna (max) | T3 | 52.80 | $0.017871 | no | dominated / outside near band |
| Muse Spark 1.1 | T3 | 52.79 | $0.093226 | no | dominated / outside near band |
| Claude Sonnet 5 (xhigh) | T3 | 52.68 | $0.18509 | no | dominated / outside near band |
| GPT-5.4 (xhigh) | T3 | 52.41 | $1.1198 | no | price-close / capability-behind |
| GPT-5.6 Terra (xhigh) | T3 | 52.33 | $0.3074 | no | dominated / outside near band |
| DeepSeek V4 Pro 0813 (Reasoning, Max Effort) | T3 | 52.27 | $0.092825 | no | dominated / outside near band |
| google/gemini-3.5-flash | T3 | 52.16 | $0.14953 | no | dominated / outside near band |
| DeepSeek V4 Flash 0731 (max) | T3 | 52.00 | $0.034235 | no | price-close / capability-behind |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | T3 | 52.00 | $1.8744 | no | price-close / capability-behind |
| GLM-5.2 (max) | T3 | 51.97 | $0.10106 | no | dominated / outside near band |
| Gemini 3.7 Flash (low) | T3 | 51.95 | $0.065809 | no | dominated / outside near band |
| Gemini 3.5 Flash (high) | T3 | 51.79 | $0.91825 | no | dominated / outside near band |
| DeepSeek V4 Flash 0731 (Reasoning, Max Effort) | T3 | 51.68 | $0.02915 | no | dominated / outside near band |
| Gemini 3.6 Flash | T3 | 51.62 | $0.071367 | no | dominated / outside near band |
| Claude Opus 5 (low) | T3 | 51.55 | $0.39185 | no | dominated / outside near band |
| GLM-5.2 (max) | T3 | 51.47 | $0.37697 | YES | STRICT FRONTIER |
| GPT-5.5 (medium) | T3 | 51.47 | $0.50155 | no | dominated / outside near band |
| Qwen3.8 27B | T3 | 51.41 | $0.043565 | no | dominated / outside near band |
| GPT-5.6 Sol (low) | T3 | 51.21 | $0.29772 | no | capability-close / price-heavy |
| Kimi K3 (low) | T3 | 51.02 | $0.26587 | no | capability-close / price-heavy |
| Gemini 3.6 Flash (high) | T3 | 50.63 | $0.33307 | no | capability-close / price-heavy |
| Grok 4.6 (low) | T3 | 50.59 | $0.14385 | no | dominated / outside near band |

## Bottom contested region

The lower end is contested by cost compression rather than flagship quality. This section combines the cheapest eight Pareto configurations with models within ±2 capability points of the D↔C (30) and C↔B (40) boundaries.

| Model/configuration | Tier | Capability | Cost | Pareto | Why included |
|---|---|---:|---:|---|---|
| Gemma 4 E4B (Reasoning) | T4 | 10.50 | $0.0014415 | YES | low-cost Pareto segment |
| GLM-4.7-Flash (Non-reasoning) | T4 | 15.56 | $0.0054331 | YES | low-cost Pareto segment |
| Step 3.5 Flash 2603 | T4 | 26.50 | $0.0060994 | YES | low-cost Pareto segment |
| MiMo-V2.5 | T4 | 41.84 | $0.010649 | YES | low-cost Pareto segment; near C/B boundary |
| GPT-5.6 Luna (medium) | T4 | 38.56 | $0.0145 | YES | low-cost Pareto segment; near C/B boundary |
| Muse Spark 1.2 (xhigh, Contributor pricing) | T2 | 57.00 | $0.12719 | YES | low-cost Pareto segment |
| Kimi K3 | T2 | 58.30 | $0.27405 | YES | low-cost Pareto segment |
| GLM-5.2 (max) | T3 | 51.47 | $0.37697 | YES | low-cost Pareto segment |
| o3 | T4 | 28.11 | $0.19886 | no | near D/C boundary |
| MiMo-V2.5-Pro (Non-reasoning) | T4 | 28.13 | $0.038539 | no | near D/C boundary |
| GPT-5 mini (medium) | T4 | 28.20 | $0.025136 | no | near D/C boundary |
| GPT-5 (low) | T4 | 28.23 | $0.11885 | no | near D/C boundary |
| Claude 4.1 Opus (Non-reasoning) | T4 | 28.24 | $0.7145 | no | near D/C boundary |
| Gemini 3.1 Flash-Lite | T4 | 28.31 | $0.025517 | no | near D/C boundary |
| mistralai/mistral-small-2603 | T4 | 28.31 | — | no | near D/C boundary |
| DeepSeek V3.1 Terminus (Reasoning) | T4 | 28.32 | $0.10068 | no | near D/C boundary |
| Grok 4.1 Fast (Reasoning) | T4 | 28.32 | — | no | near D/C boundary |
| Laguna Xs.2 | T4 | 28.35 | — | no | near D/C boundary |
| Claude 4.5 Haiku (Reasoning) | T4 | 28.49 | $0.12432 | no | near D/C boundary |
| JT-35B-Flash | T4 | 28.68 | — | no | near D/C boundary |
| claude-4.6-sonnet | T4 | 28.80 | — | no | near D/C boundary |
| Claude 4.1 Opus (Non-reasoning) | T4 | 28.80 | $1.5486 | no | near D/C boundary |
| DeepSeek V4 Flash (Non-reasoning) | T4 | 28.98 | $0.00578 | no | near D/C boundary; price-close / capability-behind |
| MiMo-V2-Flash (Reasoning) | T4 | 29.24 | $0.0081631 | no | near D/C boundary |
| GPT-5.5 Instant (June 2026) | T4 | 29.25 | $0.53209 | no | near D/C boundary |
| Claude 4.5 Sonnet (Non-reasoning) | T4 | 29.28 | $0.25479 | no | near D/C boundary |
| G9v3-39A5B | T4 | 29.29 | — | no | near D/C boundary |
| Qwen3.5 122B A10B (Non-reasoning) | T4 | 29.52 | $0.048867 | no | near D/C boundary |
| Qwen3.5 35B A3B (Reasoning) | T4 | 29.58 | $0.038556 | no | near D/C boundary |
| Qwen3.5 27B (Non-reasoning) | T4 | 29.66 | $0.037208 | no | near D/C boundary |
| Kimi K2.5 (Non-reasoning) | T4 | 29.75 | $0.056627 | no | near D/C boundary |
| Claude 4.1 Opus (Reasoning) | T4 | 29.75 | $1.4704 | no | near D/C boundary |
| Gemini 3 Pro Preview (low) | T4 | 29.81 | $0.17306 | no | near D/C boundary |
| GPT-5.4 mini (medium) | T4 | 30.16 | $0.079495 | no | near D/C boundary |
| Step 3.7 Flash | T4 | 30.18 | $0.017425 | no | near D/C boundary |
| Kimi K2 Thinking | T4 | 30.34 | $0.056531 | no | near D/C boundary |
| Gemma 4 31B (Reasoning) | T4 | 30.45 | — | no | near D/C boundary |
| GPT-5.4 nano (medium) | T4 | 30.48 | $0.02209 | no | near D/C boundary |
| K-EXAONE 2.0 0803 | T4 | 30.60 | — | no | near D/C boundary |
| GPT-5.1 Codex mini (high) | T4 | 30.63 | $0.071461 | no | near D/C boundary |
| GPT-5 (medium) | T4 | 30.64 | $0.14486 | no | near D/C boundary |
| mistralai/devstral-2512 | T4 | 30.67 | — | no | near D/C boundary |
| DeepSeek V3.2 (Reasoning) | T4 | 30.70 | $0.01568 | no | near D/C boundary |
| Qwen3.5 Omni Plus | T4 | 30.97 | $0.063648 | no | near D/C boundary |
| GPT-5.1 Codex | T4 | 30.98 | $0.14219 | no | near D/C boundary |
| GPT-5 Codex (high) | T4 | 31.07 | $0.14219 | no | near D/C boundary |
| DeepSeek V4 Pro Preview (Non-reasoning) | T4 | 31.22 | $0.030397 | no | near D/C boundary |
| MiniMax-M2.5 | T4 | 31.23 | $0.026511 | no | near D/C boundary |
| MiniMax-M2.1 | T4 | 31.30 | $0.027252 | no | near D/C boundary |
| Laguna M.1 | T4 | 31.31 | — | no | near D/C boundary |
| Ring-2.6-1T | T4 | 31.38 | $0.066441 | no | near D/C boundary |
| Qwen3.6 35B A3B (Reasoning) | T4 | 31.64 | $0.059689 | no | near D/C boundary |
| GPT-5 | T4 | 31.70 | $0.14219 | no | near D/C boundary |
| Qwen3.6 27B (Non-reasoning) | T4 | 31.76 | $0.068984 | no | near D/C boundary |
| DeepSeek V4 Pro (Non-reasoning) | T4 | 31.90 | $0.023579 | no | near D/C boundary |
| A.X-K2 | T4 | 31.93 | — | no | near D/C boundary |
| Ling 3.0 Flash (reasoning) | T4 | 38.00 | $0.022481 | no | near C/B boundary; capability-close / price-heavy |
| GLM-5-Turbo | T4 | 38.58 | — | no | near C/B boundary |
| Qwen 3.6 Plus | T4 | 38.65 | — | no | near C/B boundary |
| x-ai/grok-build-0.1 | T4 | 38.66 | — | no | near C/B boundary |
| GPT-5 (high) | T4 | 38.71 | $0.20957 | no | near C/B boundary |
| Claude Opus 4.6 | T4 | 38.80 | $0.48631 | no | near C/B boundary |
| MiniMax-M2.7 | T4 | 38.84 | $0.033488 | no | near C/B boundary |
| DeepSeek V4 Flash (Reasoning, High Effort) | T4 | 38.88 | $0.0068453 | no | near C/B boundary |
| GLM-5 (Reasoning) | T4 | 38.95 | $0.069641 | no | near C/B boundary |
| GPT-5.1 (high) | T4 | 39.39 | $0.16911 | no | near C/B boundary |
| JT-4.1 Flash 236B A21B | T4 | 39.48 | — | no | near C/B boundary |
| gemini-3-pro-preview | T4 | 39.49 | — | no | near C/B boundary |
| Grok Build 0.1 0616 | T4 | 39.54 | $0.056711 | no | near C/B boundary |
| Gemini 3 Pro Preview (high) | T4 | 39.55 | $0.20704 | no | near C/B boundary |
| GPT-5.4 (low) | T4 | 39.67 | $0.2317 | no | near C/B boundary |
| Gemini 3.5 Flash-Lite (high) | T4 | 39.78 | $0.071951 | no | near C/B boundary; capability-close / price-heavy |
| Hy3-preview (Reasoning) | T4 | 39.88 | $0.011861 | no | near C/B boundary; capability-close / price-heavy |
| gemini-3-flash-low | T4 | 39.94 | — | no | near C/B boundary |
| MiMo-V2.5 | T4 | 40.17 | $0.0071358 | no | near C/B boundary |
| Qwen3.6 Max Preview | T4 | 40.43 | — | no | near C/B boundary |
| Solar Pro 4 | T4 | 40.44 | $0.022435 | no | near C/B boundary |
| Qwen3.6 Max Preview | T4 | 40.55 | $0.14555 | no | near C/B boundary; capability-close / price-heavy |
| Inkling | T4 | 40.66 | $0.080325 | no | near C/B boundary |
| openai/gpt-5.4-nano | T4 | 40.76 | $0.018235 | no | near C/B boundary |
| DeepSeek V4 Pro Preview (Reasoning, High Effort) | T4 | 40.83 | $0.035156 | no | near C/B boundary; capability-close / price-heavy |
| Nemotron 3 Ultra 550B A55B (Reasoning) | T4 | 40.83 | $0.14206 | no | near C/B boundary; capability-close / price-heavy |
| MiMo-V2-Pro | T4 | 40.84 | $0.11881 | no | near C/B boundary; capability-close / price-heavy |
| GPT-5.4 nano (xhigh) | T4 | 41.16 | $0.12138 | no | near C/B boundary; capability-close / price-heavy |
| GPT-5.2 Codex (xhigh) | T4 | 41.20 | $0.20274 | no | near C/B boundary |
| gemini-3-flash-high | T4 | 41.26 | — | no | near C/B boundary |
| google/gemini-3-flash-preview | T4 | 41.29 | — | no | near C/B boundary |
| GPT-5.6 Terra (low) | T4 | 41.32 | $0.15051 | no | near C/B boundary; capability-close / price-heavy |
| Qwen3.6 Plus | T4 | 41.33 | $0.08672 | no | near C/B boundary; capability-close / price-heavy |
| openai/gpt-5.4-mini | T4 | 41.36 | $0.072003 | no | near C/B boundary |
| gpt-5-default | T4 | 41.51 | — | no | near C/B boundary |
| Agnes 2.5 Pro Alpha | T4 | 41.77 | $0.024437 | no | near C/B boundary |
| gpt-5.2-high | T4 | 41.85 | — | no | near C/B boundary |
| Qwen3.7 Plus | T4 | 41.89 | $0.041047 | no | near C/B boundary |
| Muse Spark | T4 | 41.97 | — | no | near C/B boundary |
| DeepSeek V4 Flash (Reasoning, Max Effort) | T4 | 42.00 | $0.0068453 | no | near C/B boundary |

## Closest competitors to the strict Pareto frontier

| Model/configuration | Tier | Capability | Cost | Dominated by | Capability gap | Cost premium | Status |
|---|---|---:|---:|---|---:|---:|---|
| Step 3.5 Flash | T4 | 26.00 | $0.0060213 | Step 3.5 Flash 2603 | 0.50 | 0.0% | razor-edge miss |
| Claude Opus 5 (high) | T2 | 59.66 | $1.23 | Kimi K3 (max) | 0.24 | 46.4% | near-frontier |
| Claude Fable 5 (max) | T1 | 60.41 | $3.14 | Claude Opus 5 (max) | 0.74 | 34.2% | near-frontier |
| GPT-5.5 (xhigh) | T2 | 57.49 | $0.99918 | GPT-5.6 Sol (xhigh) | 1.46 | 23.4% | near-frontier |
| DeepSeek V4 Flash 0731 (High) | T4 | 37.00 | $0.010662 | GPT-5.6 Luna (medium) | 1.56 | 6.6% | near-frontier |
| Claude Fable 5 (xhigh) | T2 | 59.03 | $1.7571 | GPT-5.6 Sol (max) | 1.62 | 42.9% | near-frontier |
| Gemma 4 E4B (Non-reasoning) | T4 | 8.81 | $0.0014415 | Gemma 4 E4B (Reasoning) | 1.70 | 0.0% | near-frontier |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.16836 | Muse Spark 1.2 (xhigh, Contributor pricing) | 0.00 | 693.0% | capability-close / price-heavy |
| Ministral 3 14B | T4 | 10.39 | $0.016064 | Gemma 4 E4B (Reasoning) | 0.12 | 1014.4% | capability-close / price-heavy |
| NVIDIA Nemotron 3 Super 120B A12B (Reasoning) | T4 | 26.38 | $0.061718 | Step 3.5 Flash 2603 | 0.12 | 925.0% | capability-close / price-heavy |
| Hy3-preview (Non-reasoning) | T4 | 26.35 | $0.017755 | Step 3.5 Flash 2603 | 0.15 | 194.9% | capability-close / price-heavy |
| Ling-2.6-1T | T4 | 26.33 | $0.07578 | Step 3.5 Flash 2603 | 0.17 | 1158.5% | capability-close / price-heavy |
| GPT-5.6 Sol (low) | T3 | 51.21 | $0.23 | GLM-5.2 (max) | 0.27 | 1460.0% | capability-close / price-heavy |
| Grok 4 Fast (Reasoning) | T4 | 26.14 | $0.018358 | Step 3.5 Flash 2603 | 0.36 | 204.9% | capability-close / price-heavy |
| Qwen3 Next 80B A3B Instruct | T4 | 15.15 | $0.10553 | GLM-4.7-Flash (Non-reasoning) | 0.41 | 2633.7% | capability-close / price-heavy |
| Claude Opus 5 (medium) | T2 | 57.88 | $0.72 | Kimi K3 | 0.42 | 220.9% | capability-close / price-heavy |
| Qwen3.6 27B (Reasoning) | T4 | 38.13 | $0.25276 | GPT-5.6 Luna (medium) | 0.43 | 2427.6% | capability-close / price-heavy |
| Kimi K3 (low) | T3 | 51.02 | $0.18307 | GLM-5.2 (max) | 0.45 | 1141.7% | capability-close / price-heavy |
| Qwen3.6 Plus | T4 | 41.33 | $0.14709 | MiMo-V2.5 | 0.50 | 1233.2% | capability-close / price-heavy |
| Gemini 3.5 Flash-Lite (high) | T4 | 41.33 | $0.060754 | MiMo-V2.5 | 0.51 | 450.7% | capability-close / price-heavy |

## Named high-interest competitors

These entries come from the explicit analysis-policy watchlist and remain visible even when they are not among the twenty numerically closest misses.

| Model/configuration | Tier | Capability | Cost | Status |
|---|---|---:|---:|---|
| Qwen3.8 Max (xhigh) | T2 | 56.77 | $1.13 | price-close / capability-behind |
| Claude Fable 5 (max) | T1 | 60.41 | $3.14 | near-frontier |
| GPT-5.6 Sol (max) | T1 | 60.65 | $1.23 | STRICT FRONTIER |
| Kimi K3 (max) | T2 | 59.90 | $0.84 | STRICT FRONTIER |
| Claude Sonnet 5 (max) | T3 | 54.04 | $0.58975 | economically dominated |
| DeepSeek V4 Flash 0731 (max) | T3 | 52.00 | $0.03 | price-close / capability-behind |
| GPT-5.6 Luna (xhigh) | T3 | 49.74 | $0.03 | capability-close / price-heavy |
| Grok 4.3 (high) | T3 | 53.00 | $0.10662 | economically dominated |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.16836 | capability-close / price-heavy |
| MiMo-V2.5-Pro | T4 | 43.42 | $0.034705 | economically dominated |
