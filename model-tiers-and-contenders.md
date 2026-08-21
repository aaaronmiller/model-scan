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

### T1 · Frontier ceiling (4)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Claude Opus 5 (xhigh) | 61.90 | $1.5779 | YES | — |
| Claude Opus 5 (max) | 61.13 | $2.2018 | no | near-frontier |
| GPT-5.6 Sol (max) | 60.65 | $1.5702 | YES | — |
| Claude Fable 5 (max) | 60.02 | $2.8223 | no | capability-close / price-heavy |

### T2 · Frontier (14)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Claude Opus 5 (high) | 59.97 | $1.0757 | no | razor-edge miss |
| Kimi K3 (max) | 59.87 | $0.92963 | YES | — |
| GPT-5.6 Sol (xhigh) | 59.16 | $0.83059 | YES | — |
| Claude Fable 5 (xhigh) | 59.12 | $1.7571 | no | capability-close / price-heavy |
| Claude Opus 5 (medium) | 59.00 | $0.62579 | YES | — |
| GPT-5.5 (high) | 58.55 | $0.9368 | YES | — |
| Claude Opus 4.8 (xhigh) | 58.27 | — | no | — |
| GPT-5.5 (xhigh) | 57.54 | $1.3827 | no | near-frontier |
| Muse Spark 1.2 (xhigh, Contributor pricing) | 57.10 | $0.12719 | YES | — |
| Muse Spark 1.2 (xhigh, Standard pricing) | 57.10 | $0.32331 | no | capability-close / price-heavy |
| GPT-5.6 Sol (high) | 57.00 | $0.54339 | no | capability-close / price-heavy |
| Gemini 3.1 Pro Preview | 57.00 | $0.37225 | no | capability-close / price-heavy |
| Qwen3.8 Max (xhigh) | 56.71 | $0.89547 | no | capability-close / price-heavy |
| GPT-5.6 Sol (medium) | 56.00 | $0.34726 | no | capability-close / price-heavy |

### T3 · Executor (41)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| GPT-5.6 Luna (max) | 55.75 | $0.078429 | no | capability-close / price-heavy |
| Claude Opus 4.8 (max) | 55.51 | $1.7767 | no | — |
| Muse Spark 1.1 (xhigh effort) | 55.23 | — | no | — |
| GPT-5.6 Terra (max) | 55.16 | $0.77262 | no | price-close / capability-behind |
| Claude Opus 4.7 (xhigh effort) | 54.88 | — | no | — |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | 54.34 | $1.9943 | no | — |
| Grok 4.5 | 54.19 | $0.42565 | no | — |
| Claude Sonnet 5 (max) | 53.93 | $1.9591 | no | — |
| Grok 4.3 (high) | 53.00 | $0.14774 | no | — |
| Muse Spark 1.1 (high effort) | 52.89 | — | no | — |
| Claude Sonnet 5 (xhigh) | 52.47 | — | no | — |
| GPT-5.4 (xhigh) | 52.31 | $1.1198 | no | price-close / capability-behind |
| Muse Spark 1.1 | 52.27 | — | no | — |
| openai/gpt-5.5 | 52.26 | — | no | — |
| Gemini 3.5 Flash (high) | 52.01 | $0.91825 | no | — |
| DeepSeek V4 Flash 0731 (max) | 52.00 | $0.034235 | no | price-close / capability-behind |
| Claude Opus 5 (low) | 52.00 | $0.34445 | no | — |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | 52.00 | $1.8744 | no | price-close / capability-behind |
| GPT-5.6 Terra (xhigh) | 51.90 | $0.48269 | no | — |
| GLM-5.2 (max) | 51.39 | $0.37697 | YES | — |
| GPT-5.5 (low) | 51.00 | $0.25183 | no | capability-close / price-heavy |
| GPT-5.6 Sol (low) | 51.00 | $0.2105 | no | capability-close / price-heavy |
| Gemini 3.6 Flash (high) | 50.59 | $0.33307 | no | capability-close / price-heavy |
| GPT-5.5 (medium) | 50.00 | $0.47587 | no | capability-close / price-heavy |
| Claude Opus 4.5 (high effort) | 49.35 | — | no | — |
| GPT-5.6 Terra (high) | 49.00 | $0.32221 | no | — |
| GPT-5.3 Codex | 48.92 | — | no | — |
| GPT-5.6 Luna (xhigh) | 48.83 | $0.037652 | no | — |
| DeepSeek V4 Flash 0731 (Xhigh) | 48.68 | $0.024463 | no | — |
| Qwen3.7 Max | 48.66 | $0.40806 | no | — |
| Gemini 3.1 Pro Preview | 48.23 | $0.19237 | no | — |
| Inkling (xhigh effort) | 48.08 | — | no | — |
| Inkling Small | 48.03 | — | no | — |
| Claude Opus 4.6 (Adaptive Reasoning, Max Effort) | 47.76 | $1.2116 | no | — |
| GPT-5.5 Factory | 47.75 | — | no | — |
| GPT-5.4 Codex | 47.70 | — | no | — |
| Gemini 3.1 Pro | 47.62 | — | no | — |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | 47.35 | $1.2999 | no | — |
| Composer 2.5 | 47.11 | — | no | — |
| Kimi K2.6 | 47.00 | $0.29485 | no | — |
| GPT-5.6 Luna (high) | 47.00 | $0.021778 | no | price-close / capability-behind |

### T4 · Utility — bottom-4 interchangeable (548)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| GPT-5.5 Codex | 46.85 | — | no | — |
| Kimi K2.7 Code | 46.73 | $0.25447 | no | — |
| MiniMax-M3 | 46.69 | $0.10569 | no | — |
| GPT-5.6 Terra (medium) | 46.00 | $0.25914 | no | — |
| Gemini 3.5 Flash (medium) | 45.38 | $0.40039 | no | — |
| DeepSeek V4 Pro Preview (Reasoning, Max Effort) | 44.95 | $0.058402 | no | — |
| GPT-5.3 Codex (xhigh) | 44.27 | $0.49321 | no | — |
| GPT-5.2 Codex (xhigh) | 44.15 | $0.57109 | no | — |
| GPT-5.2 (xhigh) | 43.75 | $0.54196 | no | — |
| MiMo-V2.5-Pro | 43.39 | $0.039243 | no | — |
| DeepSeek V4 Flash (Reasoning, Max Effort) | 43.08 | $0.038017 | no | — |
| gpt-5.2-high | 43.07 | — | no | — |
| gpt-5.4-high | 42.98 | — | no | — |
| GLM-5.1 (Reasoning) | 42.93 | $0.23951 | no | — |
| Qwen3.7 Plus | 42.93 | $0.055453 | no | — |
| gpt-5-default | 42.79 | — | no | — |
| Claude Opus 4.7 (Non-reasoning, High Effort) | 42.68 | $0.37232 | no | — |
| GPT-5.4 mini (xhigh) | 42.55 | $0.37373 | no | capability-close / price-heavy |
| gpt-5.4-pro-thinking | 42.28 | — | no | — |
| GPT-5.6 Sol (non-reasoning) | 42.00 | $0.13841 | no | — |
| MiMo-V2.5 | 41.96 | $0.010649 | YES | — |
| google/gemini-3-flash-preview | 41.80 | — | no | — |
| Qwen3.6 Plus | 41.78 | $0.16015 | no | capability-close / price-heavy |
| gemini-3-flash-high | 41.71 | — | no | — |
| gemini-3-flash-low | 41.43 | — | no | — |
| Muse Spark | 41.35 | — | no | — |
| Nemotron 3 Ultra 550B A55B (Reasoning) | 41.29 | $0.14206 | no | capability-close / price-heavy |
| GPT-5.4 nano (xhigh) | 41.25 | $0.12138 | no | capability-close / price-heavy |
| Inkling | 41.25 | — | no | — |
| Claude Opus 4.5 20251101 Thinking | 41.22 | — | no | — |
| DeepSeek V4 Pro Preview (Reasoning, High Effort) | 40.83 | $0.035156 | no | capability-close / price-heavy |
| Claude Opus 4.5 (Reasoning) | 40.77 | $0.59664 | no | capability-close / price-heavy |
| gemini-3-pro-preview | 40.54 | — | no | — |
| Qwen3.6 Max Preview | 40.48 | — | no | — |
| MiMo-V2-Pro | 40.29 | $0.11881 | no | capability-close / price-heavy |
| GPT-5.1 (high) | 40.07 | $0.16911 | no | capability-close / price-heavy |
| GPT-5.6 Terra (low) | 40.00 | $0.1092 | no | capability-close / price-heavy |
| Qwen3.6 Max Preview | 40.00 | $0.18647 | no | capability-close / price-heavy |
| Gemini 3.5 Flash-Lite (high) | 39.73 | $0.071951 | no | — |
| x-ai/grok-build-0.1 | 39.64 | — | no | — |
| Gemini 3 Pro Preview (high) | 39.55 | $0.20704 | no | — |
| GLM-5 (Reasoning) | 39.42 | $0.059855 | no | — |
| gpt-5.2-pro | 39.39 | — | no | — |
| GPT-5 (high) | 39.29 | $0.20957 | no | — |
| MiniMax-M2.7 | 39.18 | $0.049986 | no | — |
| GPT-5.4 (low) | 39.14 | $0.18948 | no | — |
| Qwen 3.6 Plus | 39.12 | — | no | — |
| GPT-5.1 Codex Max | 39.09 | — | no | — |
| GPT-5.6 Luna (medium) | 39.00 | $0.011567 | YES | — |
| Mistral Medium 3.5 | 39.00 | $0.33945 | no | capability-close / price-heavy |
| GPT-5.1 | 38.75 | — | no | — |
| Claude Sonnet 4.5 20250929 Thinking | 38.51 | — | no | — |
| claude-4.6-opus-thinking-high | 38.13 | — | no | — |
| GLM-5-Turbo | 38.06 | — | no | — |
| Ling 3.0 Flash (reasoning) | 38.00 | $0.022481 | no | capability-close / price-heavy |
| GPT-5.2 (medium) | 37.95 | $0.35776 | no | capability-close / price-heavy |
| Qwen3.5 Plus Thinking | 37.92 | — | no | — |
| Claude Opus 4.6 (Non-reasoning, High Effort) | 37.79 | $0.49706 | no | capability-close / price-heavy |
| Nemotron 3 Ultra 550B A55B (Reasoning) | 37.76 | $0.14139 | no | capability-close / price-heavy |
| Gemini 3 Flash Preview (Reasoning) | 37.76 | $0.054242 | no | capability-close / price-heavy |
| Kimi K2.5 (Reasoning) | 37.76 | $0.079227 | no | capability-close / price-heavy |
| GPT-5 | 37.61 | — | no | — |
| DeepSeek V4 Flash (Reasoning, High Effort) | 37.36 | $0.014061 | no | capability-close / price-heavy |
| x-ai/grok-4.3 | 37.33 | — | no | — |
| Grok 4.20 0309 (Reasoning) | 37.16 | $0.1125 | no | capability-close / price-heavy |
| DeepSeek V4 Flash 0731 (High) | 37.00 | $0.010662 | no | near-frontier |
| Grok 4.20 0309 v2 (Reasoning) | 37.00 | $0.15226 | no | capability-close / price-heavy |
| Qwen3.6 27B (Reasoning) | 36.93 | $0.22335 | no | — |
| Claude Haiku 4.5 | 36.45 | — | no | — |
| MiMo-V2-Omni-0327 | 36.39 | $0.04104 | no | — |
| MiniMax-M2.1 | 36.29 | $0.040209 | no | — |
| GPT-5.1 Codex | 36.13 | — | no | — |
| GPT-5 Codex (high) | 36.12 | $0.27279 | no | — |
| Grok 4 | 36.03 | $0.73932 | no | — |
| Grok 4.3 (medium) | 36.00 | $0.053521 | no | — |
| Claude Sonnet 4.6 (Non-reasoning, High Effort) | 35.89 | $0.41651 | no | — |
| Grok 4.3 (low) | 35.44 | $0.036917 | no | — |
| KAT Coder Pro V2 | 35.39 | $0.028699 | no | — |
| GLM-5.1 (Non-reasoning) | 35.37 | $0.057908 | no | — |
| GLM-4.7 (Reasoning) | 35.29 | $0.038759 | no | — |
| deepseek-v3.2-thinking-high | 35.04 | — | no | — |
| GPT-5.5 (Non-reasoning) | 35.00 | $0.1449 | no | — |
| MiMo-V2-Omni | 34.99 | — | no | — |
| Gemini 3.5 Flash (minimal) | 34.91 | $0.23066 | no | — |
| GPT-5.1 Codex (high) | 34.73 | $0.39286 | no | — |
| Claude Opus 4.5 (Non-reasoning) | 34.71 | $0.43072 | no | — |
| Claude 4.5 Sonnet (Reasoning) | 34.65 | $0.32966 | no | — |
| claude-4.5-opus-thinking-high | 34.62 | — | no | — |
| Kimi K2.6 (Non-reasoning) | 34.58 | $0.12988 | no | — |
| Mistral Medium 3.5 | 34.56 | — | no | — |
| GLM 5V Turbo (Reasoning) | 34.49 | — | no | — |
| DeepSeek V3p2 Thinking | 34.41 | — | no | — |
| Claude Sonnet 4.6 (Non-reasoning, Low Effort) | 34.26 | $0.21801 | no | — |
| GPT-5.6 Luna (low) | 34.00 | $0.01066 | no | price-close / capability-behind |
| GPT-5.6 Terra (non-reasoning) | 34.00 | $0.13332 | no | — |
| Qwen3.5 27B (Reasoning) | 33.78 | $0.072442 | no | — |
| GPT-5 (medium) | 33.74 | $0.15035 | no | — |
| Claude 4.1 Opus (Reasoning) | 33.71 | $1.0934 | no | — |
| Qwen3.5 397B A17B (Reasoning) | 33.68 | $0.17626 | no | — |
| Hy3-preview (Reasoning) | 33.58 | $0.017265 | no | — |
| GPT-5.5 Instant (May 2026) | 33.52 | $0.25833 | no | — |
| DeepSeek V3.2 (Reasoning) | 33.45 | $0.02332 | no | — |
| MiMo-V2-Flash (Feb 2026) | 33.22 | $0.012765 | no | — |
| Gemini 3 Pro Preview (low) | 33.07 | $0.12639 | no | — |
| Kimi K2 Thinking | 33.02 | $0.07994 | no | — |
| GPT-5 mini (high) | 32.96 | $0.040684 | no | — |
| GLM 4.6 | 32.85 | — | no | — |
| MiniMax-M2.5 | 32.70 | $0.03702 | no | — |
| o3-pro | 32.52 | $1.2792 | no | — |
| gpt-5-mini | 32.46 | — | no | — |
| GLM-5 (Non-reasoning) | 32.41 | $0.041836 | no | — |
| Qwen3.5 122B A10B (Reasoning) | 32.28 | $0.13819 | no | — |
| Qwen3.5 Flash | 32.23 | — | no | — |
| claude-4.6-sonnet | 32.18 | — | no | — |
| Qwen3.5 397B A17B (Non-reasoning) | 31.98 | $0.083931 | no | — |
| Laguna M.1 | 31.87 | — | no | — |
| mistralai/mistral-small-2603 | 31.84 | — | no | — |
| Qwen3 Max Thinking | 31.75 | $0.12376 | no | — |
| Qwen3.6 35B A3B (Reasoning) | 31.65 | $0.10276 | no | — |
| DeepSeek V4 Pro Preview (Non-reasoning) | 31.22 | $0.030397 | no | — |
| MiMo-V2-Flash (Reasoning) | 31.20 | $0.014556 | no | — |
| GPT-5 (low) | 31.15 | $0.083038 | no | — |
| Grok 4.3 (Non-reasoning) | 31.00 | $0.099963 | no | — |
| Claude 4 Opus (Reasoning) | 30.97 | $1.0934 | no | — |
| GPT-5 mini (medium) | 30.92 | $0.023386 | no | — |
| Claude 4 Sonnet (Reasoning) | 30.67 | $0.29216 | no | — |
| mistralai/devstral-2512 | 30.66 | — | no | — |
| Qwen3.5 Omni Plus | 30.64 | $0.094459 | no | — |
| GPT-5.1 Codex mini (high) | 30.63 | $0.071461 | no | — |
| Grok 4.1 Fast (Reasoning) | 30.62 | — | no | — |
| Ring-2.6-1T | 30.57 | $0.13699 | no | — |
| o3 | 30.40 | $0.28612 | no | — |
| Gemini 3.1 Flash-Lite | 30.28 | $0.028797 | no | — |
| GPT-5.4 nano (medium) | 30.16 | $0.032419 | no | — |
| GPT-5.4 mini (medium) | 29.81 | $0.0969 | no | — |
| gpt-5.2-default | 29.74 | — | no | — |
| Claude 4.5 Haiku (Reasoning) | 29.58 | $0.17341 | no | — |
| Kimi K2.5 (Non-reasoning) | 29.40 | $0.067118 | no | — |
| Gemma 4 31B (Reasoning) | 29.35 | — | no | — |
| Qwen3.5 27B (Non-reasoning) | 29.31 | $0.051641 | no | — |
| Command A+ | 29.29 | — | no | — |
| Qwen3.6 27B (Non-reasoning) | 29.28 | $0.10137 | no | — |
| Claude 4.5 Sonnet (Non-reasoning) | 29.28 | $0.25479 | no | — |
| Qwen3.5 35B A3B (Reasoning) | 29.26 | $0.084398 | no | — |
| Laguna Xs.2 | 28.97 | — | no | — |
| DeepSeek V4 Flash (Non-reasoning) | 28.65 | $0.0084724 | no | price-close / capability-behind |
| JT-35B-Flash | 28.36 | — | no | — |
| MiniMax-M2 | 28.31 | $0.03716 | no | — |
| KAT-Coder-Pro V1 | 28.26 | $0.029311 | no | — |
| Claude 4.1 Opus (Non-reasoning) | 28.24 | $0.7145 | no | — |
| Qwen3 Max | 28.14 | $0.15729 | no | — |
| Qwen3.5 122B A10B (Non-reasoning) | 28.12 | $0.063783 | no | — |
| MiMo-V2.5-Pro (Non-reasoning) | 27.86 | $0.10295 | no | — |
| GPT-5.4 (Non-reasoning) | 27.68 | $0.1464 | no | — |
| Grok 4 Fast (Reasoning) | 27.37 | $0.015336 | no | — |
| Gemini 3 Flash Preview (Non-reasoning) | 27.37 | $0.031696 | no | — |
| Gemini 2.5 Pro | 27.20 | $0.13198 | no | — |
| Claude 3.7 Sonnet (Reasoning) | 27.06 | — | no | — |
| GPT-5.6 Luna (non-reasoning) | 27.00 | $0.0102 | no | price-close / capability-behind |
| GLM-4.7 (Non-reasoning) | 26.56 | $0.026546 | no | — |
| DeepSeek V3.1 Terminus (Reasoning) | 26.35 | $0.13352 | no | — |
| Hy3-preview (Non-reasoning) | 26.10 | $0.01177 | no | — |
| Ling-2.6-1T | 26.05 | $0.056307 | no | — |
| GPT-5.2 (Non-reasoning) | 26.02 | $0.15296 | no | — |
| Doubao Seed Code | 25.98 | — | no | — |
| Grok 4 0709 | 25.74 | — | no | — |
| grok-4.1-fast | 25.70 | — | no | — |
| Gemma 4 26B A4B (Reasoning) | 25.69 | $0.017831 | no | — |
| o4-mini (high) | 25.55 | $0.11314 | no | — |
| Claude 4 Opus (Non-reasoning) | 25.50 | $0.7145 | no | — |
| Claude 4 Sonnet (Non-reasoning) | 25.49 | $0.19661 | no | — |
| DeepSeek V3.2 Exp (Reasoning) | 25.45 | $0.015245 | no | — |
| NVIDIA Nemotron 3 Super 120B A12B (Reasoning) | 25.41 | $0.075624 | no | — |
| Mercury 2 | 25.33 | $0.016932 | no | — |
| GLM-4.6 (Reasoning) | 25.05 | $0.03725 | no | — |
| Qwen3 Max Thinking (Preview) | 25.03 | $0.12702 | no | — |
| Ling 3.0 Tiny (reasoning) | 25.00 | — | no | — |
| Qwen3.5 9B (Reasoning) | 24.97 | $0.022863 | no | — |
| Gemma 4 31B (Non-reasoning) | 24.85 | $0.010487 | no | price-close / capability-behind |
| K-EXAONE (Reasoning) | 24.70 | — | no | — |
| DeepSeek V3.2 (Non-reasoning) | 24.66 | $0.073409 | no | — |
| Qwen3.6 35B A3B (Non-reasoning) | 24.15 | $0.077895 | no | — |
| gpt-oss-120b (high) | 23.83 | $0.033808 | no | — |
| Gemini 2.5 Flash Preview (Sep '25) (Reasoning) | 23.80 | — | no | — |
| Claude 4.5 Haiku (Non-reasoning) | 23.71 | $0.076464 | no | — |
| Kimi K2 0905 | 23.54 | $0.076951 | no | — |
| Claude 3.7 Sonnet (Non-reasoning) | 23.50 | $0.18628 | no | — |
| o1 | 23.44 | $1.1441 | no | — |
| Qwen3.5 35B A3B (Non-reasoning) | 23.38 | $0.044019 | no | — |
| Kimi K2 | 23.27 | $0.082689 | no | — |
| MiMo-V2-Flash (Non-reasoning) | 23.07 | $0.0096254 | no | price-close / capability-behind |
| Gemini 2.5 Pro Preview (Mar' 25) | 23.03 | — | no | — |
| GLM-4.6 (Non-reasoning) | 22.98 | $0.026546 | no | — |
| Grok 4 Fast Reasoning | 22.98 | — | no | — |
| EXAONE 4.5 33B | 22.96 | — | no | — |
| GLM-4.7-Flash (Reasoning) | 22.89 | $0.0060278 | YES | — |
| Grok 3 mini Reasoning (high) | 22.50 | $0.027676 | no | — |
| Grok 4.20 0309 (Non-reasoning) | 22.48 | $0.098046 | no | capability-close / price-heavy |
| Gemini 2.5 Pro Preview (May' 25) | 22.34 | $0.12839 | no | — |
| Qwen3 235B A22B 2507 (Reasoning) | 22.34 | $0.041792 | no | — |
| DeepSeek V3.2 Speciale | 22.24 | — | no | — |
| HyperNova 60B 2605 | 22.14 | $0.0091062 | no | capability-close / price-heavy |
| Gemma 4 12B (Reasoning) | 22.00 | $0.017069 | no | capability-close / price-heavy |
| Nova 2.0 Pro Preview (medium) | 22.00 | $0.1952 | no | capability-close / price-heavy |
| ERNIE 5.0 Thinking Preview | 21.92 | — | no | — |
| Grok 4.20 0309 v2 (Non-reasoning) | 21.84 | $0.10323 | no | capability-close / price-heavy |
| Nova 2.0 Pro Preview (medium) | 21.77 | $0.17013 | no | capability-close / price-heavy |
| Grok Code Fast 1 | 21.61 | — | no | — |
| DeepSeek V3.1 Terminus (Non-reasoning) | 21.41 | $0.022504 | no | capability-close / price-heavy |
| DeepSeek V3.2 Exp (Non-reasoning) | 21.33 | $0.017076 | no | capability-close / price-heavy |
| Nemotron Cascade 2 30B A3B | 21.25 | — | no | — |
| Apriel-v1.5-15B-Thinker | 21.23 | — | no | — |
| Qwen3 Coder Next | 21.18 | $0.056019 | no | capability-close / price-heavy |
| DeepSeek V3.1 (Non-reasoning) | 21.05 | $0.050689 | no | capability-close / price-heavy |
| Nova 2.0 Omni (medium) | 20.95 | $0.037475 | no | capability-close / price-heavy |
| Mistral Small 4 (Reasoning) | 20.75 | $0.016855 | no | — |
| DeepSeek V3.1 (Reasoning) | 20.67 | $0.16165 | no | — |
| Qwen3 VL 235B A22B (Reasoning) | 20.60 | $0.11726 | no | — |
| North Mini Code | 20.56 | — | no | — |
| Apriel-v1.6-15B-Thinker | 20.54 | — | no | — |
| Nova 2.0 Lite (high) | 20.50 | $0.060754 | no | — |
| GPT-5.1 (Non-reasoning) | 20.40 | $0.066228 | no | — |
| Qwen3.5 9B (Non-reasoning) | 20.32 | — | no | — |
| Magistral Medium 1.2 | 20.11 | $0.17046 | no | — |
| Gemma 4 26B A4B (Non-reasoning) | 20.10 | $0.012673 | no | — |
| Qwen3.5 4B (Reasoning) | 20.09 | $0.0082427 | no | — |
| DeepSeek R1 0528 (May '25) | 20.08 | $0.10628 | no | — |
| Gemini 2.5 Flash (Reasoning) | 20.06 | $0.03999 | no | — |
| GPT-5 nano (high) | 19.87 | $0.010205 | no | — |
| Qwen3 Next 80B A3B (Reasoning) | 19.77 | $0.096923 | no | — |
| GPT-5 (minimal) | 19.71 | $0.08181 | no | — |
| Nova 2.0 Pro Preview (low) | 19.50 | $0.11179 | no | — |
| GLM-4.5 (Reasoning) | 19.49 | $0.038759 | no | — |
| GPT-4.1 | 19.36 | $0.13939 | no | — |
| Ling 2.6 Flash | 19.25 | $0.0076478 | no | price-close / capability-behind |
| Qwen3 Max (Preview) | 19.18 | $0.16204 | no | — |
| Nova 2.0 Lite (medium) | 19.00 | $0.051235 | no | — |
| GPT-5 nano (medium) | 19.00 | $0.0072453 | no | — |
| Qwen3.5 Omni Flash | 18.99 | $0.020996 | no | — |
| o3-mini | 18.98 | $0.073683 | no | — |
| o1-pro | 18.89 | $9.2912 | no | — |
| Gemini 2.5 Flash Preview (Sep '25) (Non-reasoning) | 18.83 | — | no | — |
| JT-MINI | 18.53 | — | no | — |
| o3-mini (high) | 18.38 | $0.091684 | no | — |
| Grok 3 | 18.35 | $0.25866 | no | — |
| Qwen3 235B A22B 2507 Instruct | 18.16 | $0.035659 | no | — |
| Llama 4 Maverick | 18.00 | $0.030169 | no | — |
| Qwen3 Coder 480B A35B Instruct | 17.98 | $0.084973 | no | — |
| Qwen3 VL 32B (Reasoning) | 17.93 | $0.21227 | no | — |
| Nova 2.0 Lite (low) | 17.81 | $0.03229 | no | — |
| gpt-oss-120b (low) | 17.70 | $0.01015 | no | — |
| MiniMax M1 80k | 17.67 | $0.056245 | no | — |
| GPT-5.4 nano (Non-Reasoning) | 17.61 | $0.011815 | no | — |
| Gemini 2.5 Flash Preview (Reasoning) | 17.55 | — | no | — |
| NVIDIA Nemotron 3 Nano 30B A3B (Reasoning) | 17.53 | $0.0099634 | no | — |
| LongCat Flash Lite | 17.22 | — | no | — |
| o1-preview | 17.04 | $1.0586 | no | — |
| HyperCLOVA X SEED Think (32B) | 17.02 | — | no | — |
| K2 Think V2 | 17.00 | — | no | — |
| Grok 4.1 Fast (Non-reasoning) | 16.88 | — | no | — |
| GLM-4.6V (Reasoning) | 16.75 | $0.017751 | no | — |
| K-EXAONE (Non-reasoning) | 16.74 | — | no | — |
| GPT-5.4 mini (Non-Reasoning) | 16.62 | $0.032599 | no | — |
| Nova 2.0 Omni (low) | 16.56 | $0.037142 | no | — |
| GLM-4.5-Air | 16.52 | $0.014513 | no | — |
| Grok 4 Fast (Non-reasoning) | 16.47 | $0.010827 | no | — |
| Nova 2.0 Pro Preview (Non-reasoning) | 16.42 | $0.46701 | no | — |
| Mi:dm K 2.5 Pro | 16.42 | — | no | — |
| GPT-4.1 mini | 16.27 | $0.02658 | no | — |
| Mistral Large 3 | 16.19 | $0.028641 | no | — |
| Ring-1T | 16.16 | — | no | — |
| Qwen3.5 4B (Non-reasoning) | 16.00 | $0.0073123 | no | — |
| Qwen3 30B A3B 2507 (Reasoning) | 15.83 | $0.033388 | no | — |
| DeepSeek V3 0324 | 15.71 | $0.044156 | no | — |
| INTELLECT-3 | 15.61 | — | no | — |
| GLM-4.7-Flash (Non-reasoning) | 15.52 | $0.0038603 | YES | — |
| Devstral 2 | 15.49 | — | no | — |
| GPT-5 (ChatGPT) | 15.30 | $0.12839 | no | — |
| Grok 3 Reasoning Beta | 15.13 | — | no | — |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Reasoning) | 15.13 | $0.0096055 | no | capability-close / price-heavy |
| Nemotron 3 Nano Omni 30B A3B Reasoning | 14.93 | $0.012374 | no | capability-close / price-heavy |
| gpt-oss-20B (high) | 14.89 | $0.010323 | no | — |
| Mistral Medium 3.1 | 14.77 | $0.03608 | no | capability-close / price-heavy |
| MiniMax M1 40k | 14.41 | — | no | — |
| gpt-oss-20B (low) | 14.34 | $0.0044279 | no | — |
| Qwen3 VL 235B A22B Instruct | 14.31 | $0.069688 | no | capability-close / price-heavy |
| GPT-5 mini (minimal) | 14.25 | $0.014506 | no | — |
| K2-V2 (high) | 14.19 | — | no | — |
| Gemini 2.5 Flash (Non-reasoning) | 14.14 | $0.029032 | no | — |
| o1-mini | 13.98 | — | no | — |
| Qwen3 Next 80B A3B Instruct | 13.72 | $0.07093 | no | capability-close / price-heavy |
| Qwen3 Coder 30B A3B Instruct | 13.61 | $0.017205 | no | — |
| GPT-4.5 (Preview) | 13.59 | — | no | — |
| Qwen3 235B A22B (Reasoning) | 13.43 | $0.18235 | no | — |
| QwQ 32B | 13.37 | $0.029616 | no | — |
| Qwen3 VL 30B A3B (Reasoning) | 13.34 | $0.03441 | no | — |
| Gemini 2.0 Flash Thinking Experimental (Jan '25) | 13.26 | — | no | — |
| Gemma 4 12B (Non-reasoning) | 13.19 | $0.024186 | no | — |
| Devstral Small 2 | 13.14 | — | no | — |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Non-reasoning) | 13.10 | $0.0084156 | no | — |
| Motif-2-12.7B-Reasoning | 12.79 | — | no | — |
| Ling-1T | 12.75 | — | no | — |
| Nova Premier | 12.73 | $0.20621 | no | — |
| DeepSeek R1 (Jan '25) | 12.57 | $0.521 | no | — |
| Magistral Medium 1 | 12.51 | — | no | — |
| Gemma 4 E4B (Reasoning) | 12.50 | — | no | — |
| Mistral Medium 3 | 12.49 | $0.032608 | no | — |
| K2-V2 (medium) | 12.43 | — | no | — |
| Llama Nemotron Super 49B v1.5 (Reasoning) | 12.42 | $0.013483 | no | — |
| Claude 3.5 Haiku | 12.41 | $0.03087 | no | — |
| Devstral Medium | 12.40 | $0.048781 | no | — |
| Mistral Small 4 (Non-reasoning) | 12.37 | $0.010516 | no | — |
| GPT-4o (March 2025, chatgpt-4o-latest) | 12.31 | — | no | — |
| Gemini 2.0 Flash (Feb '25) | 12.27 | $0.0088201 | no | — |
| Llama 3.3 Nemotron Super 49B v1 (Reasoning) | 12.25 | — | no | — |
| Qwen3 4B 2507 (Reasoning) | 11.96 | — | no | — |
| MiniCPM5-1B (Reasoning) | 11.96 | — | no | — |
| Magistral Small 1.2 | 11.95 | $0.042547 | no | — |
| Sarvam 105B (high) | 11.94 | $0.0060991 | no | — |
| Gemini 2.0 Pro Experimental (Feb '25) | 11.85 | — | no | — |
| Nova 2.0 Lite (Non-reasoning) | 11.83 | $0.12715 | no | — |
| Devstral Small (May '25) | 11.82 | — | no | — |
| Claude 3 Opus | 11.80 | $1.0934 | no | — |
| MiniCPM5-1B (Non-reasoning) | 11.74 | — | no | — |
| Gemini 2.5 Flash Preview (Non-reasoning) | 11.66 | — | no | — |
| Gemini 2.5 Flash-Lite (Reasoning) | 11.41 | $0.014407 | no | — |
| GPT-4o (Nov '24) | 11.18 | $0.13993 | no | — |
| Qwen3 VL 32B Instruct | 11.06 | $0.13484 | no | — |
| DeepSeek R1 Distill Qwen 32B | 11.04 | — | no | — |
| GLM-4.6V (Non-reasoning) | 10.98 | $0.012525 | no | — |
| Qwen3 235B A22B (Non-reasoning) | 10.86 | $0.054864 | no | — |
| Magistral Small 1 | 10.70 | — | no | — |
| Gemini 2.0 Flash (experimental) | 10.68 | — | no | — |
| EXAONE 4.0 32B (Reasoning) | 10.59 | — | no | — |
| Qwen3 VL 8B (Reasoning) | 10.58 | $0.057294 | no | — |
| Nova 2.0 Omni (Non-reasoning) | 10.53 | $0.17066 | no | — |
| Qwen3 32B (Reasoning) | 10.46 | $0.016567 | no | — |
| DeepSeek V3 (Dec '24) | 10.39 | $0.020214 | no | — |
| DeepSeek R1 0528 Qwen3 8B | 10.37 | — | no | — |
| Qwen3.5 2B (Reasoning) | 10.24 | $0.0065687 | no | — |
| Qwen2.5 Max | 10.23 | $0.10654 | no | — |
| Qwen3 14B (Reasoning) | 10.15 | $0.026323 | no | — |
| Nanbeige4.1-3B | 10.05 | — | no | — |
| Llama 4 Scout | 10.04 | $0.016773 | no | — |
| Qwen3 VL 30B A3B Instruct | 10.02 | $0.045811 | no | — |
| Hermes 4 - Llama-3.1 70B (Reasoning) | 9.97 | $0.018625 | no | — |
| Gemini 1.5 Pro (Sep '24) | 9.97 | — | no | — |
| Ministral 3 14B | 9.96 | $0.012687 | no | — |
| DeepSeek R1 Distill Llama 70B | 9.93 | $0.031285 | no | — |
| Claude 3.5 Sonnet (Oct '24) | 9.91 | $0.22436 | no | — |
| DeepSeek R1 Distill Qwen 14B | 9.83 | — | no | — |
| Falcon-H1R-7B | 9.79 | — | no | — |
| Ling-flash-2.0 | 9.74 | $0.0092496 | no | — |
| mistralai/mistral-large-2512 | 9.63 | — | no | — |
| Qwen3 Omni 30B A3B (Reasoning) | 9.63 | $0.04376 | no | — |
| GPT-4o (Aug '24) | 9.58 | $0.14784 | no | — |
| Qwen2.5 Instruct 72B | 9.57 | $0.014966 | no | — |
| Qwen3 30B A3B (Reasoning) | 9.31 | $0.0097407 | no | — |
| Devstral Small (Jul '25) | 9.26 | $0.012508 | no | — |
| Gemma 4 E2B (Reasoning) | 9.26 | — | no | — |
| QwQ 32B-Preview | 9.22 | — | no | — |
| GLM-4.5V (Reasoning) | 9.15 | $0.035112 | no | — |
| Mistral Large 2 (Nov '24) | 9.15 | $0.10455 | no | — |
| Mistral Small 3.2 | 9.12 | $0.010376 | no | — |
| Llama 3.1 Nemotron Ultra 253B v1 (Reasoning) | 9.08 | $0.16813 | no | — |
| Qwen3 30B A3B 2507 Instruct | 9.06 | $0.023814 | no | — |
| ERNIE 4.5 300B A47B | 9.02 | $0.018985 | no | — |
| Hermes 4 - Llama-3.1 405B (Reasoning) | 9.00 | $0.12672 | no | — |
| NVIDIA Nemotron Nano 12B v2 VL (Reasoning) | 8.96 | $0.042159 | no | — |
| Ministral 3 8B | 8.92 | $0.010906 | no | — |
| Gemma 4 E4B (Non-reasoning) | 8.91 | — | no | — |
| Granite 4.1 30B | 8.86 | — | no | — |
| NVIDIA Nemotron Nano 9B V2 (Reasoning) | 8.84 | $0.0044805 | no | price-close / capability-behind |
| Hermes 4 - Llama-3.1 405B (Non-reasoning) | 8.80 | $0.095707 | no | — |
| Gemini 2.0 Flash-Lite (Feb '25) | 8.79 | — | no | — |
| NVIDIA Nemotron 3 Nano 4B | 8.77 | — | no | — |
| Qwen3.5 2B (Non-reasoning) | 8.76 | $0.0029064 | no | price-close / capability-behind |
| Llama Nemotron Super 49B v1.5 (Non-reasoning) | 8.68 | $0.010798 | no | — |
| Qwen3 32B (Non-reasoning) | 8.63 | $0.0069657 | no | — |
| GPT-4o (May '24) | 8.60 | $0.28288 | no | — |
| Llama 3.3 Instruct 70B | 8.59 | $0.045082 | no | — |
| Gemini 2.0 Flash-Lite (Preview) | 8.59 | — | no | — |
| Mistral Small 3.1 | 8.59 | $0.019333 | no | — |
| K2-V2 (low) | 8.55 | — | no | — |
| Llama 3.1 Nemotron Nano 4B v1.1 (Reasoning) | 8.54 | — | no | — |
| Kimi Linear 48B A3B Instruct | 8.53 | — | no | — |
| Llama 3.1 Instruct 405B | 8.50 | $0.4077 | no | — |
| Llama 3.3 Nemotron Super 49B v1 (Non-reasoning) | 8.47 | — | no | — |
| Qwen3 VL 8B Instruct | 8.42 | $0.03233 | no | — |
| Qwen3 4B (Reasoning) | 8.35 | $0.015266 | no | — |
| LFM2.5-8B-A1B | 8.32 | — | no | — |
| Claude 3.5 Sonnet (June '24) | 8.30 | $0.22436 | no | — |
| GPT-4o (ChatGPT) | 8.25 | — | no | — |
| Ring-flash-2.0 | 8.16 | $0.009784 | no | — |
| Pixtral Large | 8.15 | $0.11482 | no | — |
| Olmo 3.1 32B Think | 8.09 | — | no | — |
| Grok 2 (Dec '24) | 8.04 | — | no | — |
| GPT-5 nano (minimal) | 8.00 | $0.0087543 | no | — |
| Gemini 1.5 Flash (Sep '24) | 7.96 | — | no | — |
| Qwen3 VL 4B (Reasoning) | 7.90 | — | no | — |
| GPT-4 Turbo | 7.89 | $0.55955 | no | — |
| Nova Pro | 7.67 | $0.084541 | no | — |
| Command A | 7.67 | $0.22366 | no | — |
| Llama 3.1 Nemotron Instruct 70B | 7.64 | $0.050875 | no | — |
| Grok Beta | 7.49 | — | no | — |
| Qwen2.5 Instruct 32B | 7.45 | — | no | — |
| Qwen3 8B (Reasoning) | 7.40 | $0.015804 | no | — |
| NVIDIA Nemotron 3 Nano 30B A3B (Non-reasoning) | 7.39 | $0.0062524 | no | — |
| NVIDIA Nemotron Nano 9B V2 (Non-reasoning) | 7.38 | $0.0062016 | no | — |
| GPT-4.1 nano | 7.27 | $0.012038 | no | — |
| Mistral Large 2 (Jul '24) | 7.27 | $0.11482 | no | — |
| Qwen3 4B 2507 Instruct | 7.12 | — | no | — |
| Qwen2.5 Coder Instruct 32B | 7.11 | — | no | — |
| Qwen3 14B (Non-reasoning) | 7.02 | $0.012481 | no | — |
| GPT-4 | 7.01 | $1.392 | no | — |
| GLM-4.5V (Non-reasoning) | 7.00 | $0.024775 | no | — |
| Mistral Small 3 | 6.93 | $0.0042064 | no | — |
| Gemini 2.5 Flash-Lite (Non-reasoning) | 6.92 | $0.0070451 | no | — |
| Nova Lite | 6.92 | $0.007653 | no | — |
| GPT-4o mini | 6.91 | $0.010372 | no | — |
| Hermes 4 - Llama-3.1 70B (Non-reasoning) | 6.90 | $0.014291 | no | — |
| Qwen3 30B A3B (Non-reasoning) | 6.80 | $0.0064199 | no | — |
| DeepSeek-V2.5 (Dec '24) | 6.79 | — | no | — |
| Qwen3 4B (Non-reasoning) | 6.77 | $0.0050759 | no | — |
| Llama 3.1 Instruct 70B | 6.75 | $0.059686 | no | — |
| Granite 4.1 8B | 6.67 | $0.0041543 | no | price-close / capability-behind |
| Gemini 2.0 Flash Thinking Experimental (Dec '24) | 6.63 | — | no | — |
| DeepSeek-V2.5 | 6.62 | — | no | — |
| Olmo 3.1 32B Instruct | 6.47 | — | no | — |
| Mistral Saba | 6.44 | — | no | — |
| DeepSeek R1 Distill Llama 8B | 6.41 | — | no | — |
| Gemma 4 E2B (Non-reasoning) | 6.41 | — | no | — |
| Olmo 3 32B Think | 6.40 | — | no | — |
| Gemini 1.5 Pro (May '24) | 6.32 | — | no | — |
| R1 1776 | 6.31 | — | no | — |
| Qwen2.5 Turbo | 6.30 | $0.0035182 | no | — |
| Reka Flash (Sep '24) | 6.29 | $0.013766 | no | — |
| Llama 3.2 Instruct 90B (Vision) | 6.23 | $0.054766 | no | — |
| Llama 3.1 Instruct 8B | 6.10 | $0.011255 | no | — |
| Grok-1 | 6.04 | — | no | — |
| Qwen2 Instruct 72B | 6.01 | — | no | — |
| EXAONE 4.0 32B (Non-reasoning) | 6.01 | — | no | — |
| Ministral 3 3B | 5.63 | $0.0077738 | no | — |
| Gemini 1.5 Flash-8B | 5.53 | — | no | — |
| DeepHermes 3 - Mistral 24B Preview (Non-reasoning) | 5.31 | — | no | — |
| Jamba 1.7 Large | 5.30 | $0.46868 | no | — |
| Granite 4.0 H Small | 5.24 | $0.0037824 | YES | — |
| Jamba 1.5 Large | 5.13 | $0.1327 | no | — |
| Qwen3 Omni 30B A3B Instruct | 5.11 | $0.036052 | no | capability-close / price-heavy |
| Hermes 3 - Llama-3.1 70B | 5.09 | $0.012199 | no | — |
| Qwen3 8B (Non-reasoning) | 5.07 | $0.014985 | no | — |
| DeepSeek-Coder-V2 | 5.05 | — | no | — |
| OLMo 2 32B | 5.01 | — | no | — |
| Jamba 1.6 Large | 5.00 | $0.1327 | no | — |
| Qwen3.5 0.8B (Reasoning) | 4.97 | $0.0026599 | no | near-frontier |
| LFM2 24B A2B | 4.95 | $0.0045435 | no | capability-close / price-heavy |
| Gemini 1.5 Flash (May '24) | 4.92 | — | no | — |
| Phi-4 | 4.87 | $0.0086681 | no | — |
| Gemma 3 27B Instruct | 4.78 | $0.0098818 | no | — |
| Claude 3 Sonnet | 4.74 | $0.22436 | no | — |
| Nova Micro | 4.74 | $0.0027346 | no | — |
| Mistral Small (Sep '24) | 4.66 | $0.01191 | no | — |
| Gemini 1.0 Ultra | 4.63 | — | no | — |
| Phi-3 Mini Instruct 3.8B | 4.59 | — | no | — |
| NVIDIA Nemotron Nano 12B v2 VL (Non-reasoning) | 4.58 | $0.031833 | no | capability-close / price-heavy |
| Gemma 3n E4B Instruct Preview (May '25) | 4.55 | — | no | — |
| Phi-4 Multimodal Instruct | 4.53 | — | no | — |
| Qwen2.5 Coder Instruct 7B  | 4.48 | — | no | — |
| Qwen3.5 0.8B (Non-reasoning) | 4.42 | $0.0014213 | YES | — |
| Mistral Large (Feb '24) | 4.41 | $0.22711 | no | — |
| Mixtral 8x22B Instruct | 4.35 | — | no | — |
| Llama 2 Chat 7B | 4.26 | $0.0039913 | no | — |
| Llama 3.2 Instruct 3B | 4.22 | $0.006167 | no | — |
| MiniCPM-V 4.6 1.3B | 4.19 | — | no | — |
| Jamba Reasoning 3B | 4.13 | — | no | — |
| Qwen3 VL 4B Instruct | 4.09 | — | no | — |
| Qwen1.5 Chat 110B | 4.08 | — | no | — |
| Reka Flash 3 | 4.06 | $0.013766 | no | — |
| Olmo 3 7B Think | 3.97 | — | no | — |
| Claude 2.1 | 3.88 | — | no | — |
| Claude 3 Haiku | 3.86 | $0.027428 | no | — |
| OLMo 2 7B | 3.85 | — | no | — |
| Molmo 7B-D | 3.81 | — | no | — |
| Ling-mini-2.0 | 3.75 | — | no | — |
| DeepSeek R1 Distill Qwen 1.5B | 3.65 | — | no | — |
| Claude 2.0 | 3.64 | — | no | — |
| DeepSeek-V2-Chat | 3.64 | — | no | — |
| Mistral Small (Feb '24) | 3.62 | $0.058045 | no | — |
| Mistral Medium | 3.59 | $0.15574 | no | — |
| GPT-3.5 Turbo | 3.57 | $0.029345 | no | — |
| Llama 3 Instruct 70B | 3.47 | $0.04527 | no | — |
| Arctic Instruct | 3.42 | — | no | — |
| Qwen Chat 72B | 3.42 | — | no | — |
| Gemma 3 12B Instruct | 3.39 | $0.011167 | no | — |
| LFM 40B | 3.37 | — | no | — |
| Llama 3.2 Instruct 11B (Vision) | 3.33 | $0.0099944 | no | — |
| PALM-2 | 3.21 | — | no | — |
| Granite 4.1 3B | 3.17 | — | no | — |
| Gemini 1.0 Pro | 3.13 | — | no | — |
| DeepSeek Coder V2 Lite Instruct | 3.11 | — | no | — |
| Phi-4 Mini Instruct | 3.03 | — | no | — |
| DeepSeek LLM 67B Chat (V1) | 3.01 | — | no | — |
| Llama 2 Chat 70B | 3.01 | — | no | — |
| Llama 2 Chat 13B | 3.00 | — | no | — |
| Command-R+ (Apr '24) | 2.99 | $0.22436 | no | — |
| OpenChat 3.5 (1210) | 2.96 | — | no | — |
| DBRX Instruct | 2.96 | — | no | — |
| Exaone 4.0 1.2B (Reasoning) | 2.90 | — | no | — |
| Olmo 3 7B Instruct | 2.81 | $0.013151 | no | — |
| Exaone 4.0 1.2B (Non-reasoning) | 2.77 | — | no | — |
| LFM2.5-1.2B-Thinking | 2.75 | — | no | — |
| Jamba 1.7 Mini | 2.73 | — | no | — |
| LFM2 2.6B | 2.71 | — | no | — |
| LFM2.5-1.2B-Instruct | 2.71 | — | no | — |
| Jamba 1.5 Mini | 2.70 | $0.010051 | no | — |
| Granite 4.0 H 1B | 2.66 | — | no | — |
| Qwen3 1.7B (Reasoning) | 2.63 | $0.014783 | no | — |
| Jamba 1.6 Mini | 2.55 | $0.010051 | no | — |
| Mixtral 8x7B Instruct | 2.43 | $0.020484 | no | — |
| Gemma 3 270M | 2.41 | — | no | — |
| Apertus 70B Instruct | 2.40 | $0.051922 | no | — |
| Granite 4.0 Micro | 2.37 | — | no | — |
| DeepHermes 3 - Llama-3.1 8B Preview (Non-reasoning) | 2.29 | — | no | — |
| Claude Instant | 2.14 | — | no | — |
| Command-R (Mar '24) | 2.14 | $0.029345 | no | — |
| Llama 65B | 2.14 | — | no | — |
| Mistral 7B Instruct | 2.14 | $0.0084186 | no | — |
| Qwen Chat 14B | 2.14 | — | no | — |
| Granite 4.0 1B | 2.07 | — | no | — |
| Molmo2-8B | 2.03 | — | no | — |
| openai/gpt-oss-120b | 1.97 | — | no | — |
| LFM2 8B A1B | 1.78 | — | no | — |
| Granite 3.3 8B (Non-reasoning) | 1.75 | $0.0070694 | no | — |
| Qwen3 1.7B (Non-reasoning) | 1.53 | $0.0092152 | no | — |
| Qwen3 0.6B (Reasoning) | 1.28 | $0.012478 | no | — |
| Llama 3 Instruct 8B | 1.19 | $0.0028393 | no | — |
| Gemma 3n E4B Instruct | 1.19 | $0.002515 | no | — |
| LFM2 1.2B | 1.15 | — | no | — |
| Gemma 3 4B Instruct | 1.12 | $0.0035156 | no | — |
| Llama 3.2 Instruct 1B | 1.10 | $0.0020919 | no | — |
| LFM2.5-VL-1.6B | 1.01 | — | no | — |
| Apertus 8B Instruct | 1.00 | $0.0050811 | no | — |
| Gemma 3 1B Instruct | 1.00 | — | no | — |
| Gemma 3n E2B Instruct | 1.00 | — | no | — |
| Granite 4.0 350M | 1.00 | — | no | — |
| Granite 4.0 H 350M | 1.00 | — | no | — |
| Qwen3 0.6B (Non-reasoning) | 1.00 | $0.01165 | no | — |
| Command A 03 2025 | 0.00 | — | no | — |

## Top contested region

The upper contest zone includes configurations at capability ≥50, spanning the A+/S/S+ boundary neighborhood where small capability differences can carry large cost penalties.

| Model/configuration | Tier | Capability | Cost | Pareto | Closest economic verdict |
|---|---|---:|---:|---|---|
| Claude Opus 5 (xhigh) | T1 | 61.90 | $1.5779 | YES | STRICT FRONTIER |
| Claude Opus 5 (max) | T1 | 61.13 | $2.2018 | no | near-frontier |
| GPT-5.6 Sol (max) | T1 | 60.65 | $1.5702 | YES | STRICT FRONTIER |
| Claude Fable 5 (max) | T1 | 60.02 | $2.8223 | no | capability-close / price-heavy |
| Claude Opus 5 (high) | T2 | 59.97 | $1.0757 | no | razor-edge miss |
| Kimi K3 (max) | T2 | 59.87 | $0.92963 | YES | STRICT FRONTIER |
| GPT-5.6 Sol (xhigh) | T2 | 59.16 | $0.83059 | YES | STRICT FRONTIER |
| Claude Fable 5 (xhigh) | T2 | 59.12 | $1.7571 | no | capability-close / price-heavy |
| Claude Opus 5 (medium) | T2 | 59.00 | $0.62579 | YES | STRICT FRONTIER |
| GPT-5.5 (high) | T2 | 58.55 | $0.9368 | YES | STRICT FRONTIER |
| Claude Opus 4.8 (xhigh) | T2 | 58.27 | — | no | dominated / outside near band |
| GPT-5.5 (xhigh) | T2 | 57.54 | $1.3827 | no | near-frontier |
| Muse Spark 1.2 (xhigh, Contributor pricing) | T2 | 57.10 | $0.12719 | YES | STRICT FRONTIER |
| Muse Spark 1.2 (xhigh, Standard pricing) | T2 | 57.10 | $0.32331 | no | capability-close / price-heavy |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.37225 | no | capability-close / price-heavy |
| GPT-5.6 Sol (high) | T2 | 57.00 | $0.54339 | no | capability-close / price-heavy |
| Qwen3.8 Max (xhigh) | T2 | 56.71 | $0.89547 | no | capability-close / price-heavy |
| GPT-5.6 Sol (medium) | T2 | 56.00 | $0.34726 | no | capability-close / price-heavy |
| GPT-5.6 Luna (max) | T3 | 55.75 | $0.078429 | no | capability-close / price-heavy |
| Claude Opus 4.8 (max) | T3 | 55.51 | $1.7767 | no | dominated / outside near band |
| Muse Spark 1.1 (xhigh effort) | T3 | 55.23 | — | no | dominated / outside near band |
| GPT-5.6 Terra (max) | T3 | 55.16 | $0.77262 | no | price-close / capability-behind |
| Claude Opus 4.7 (xhigh effort) | T3 | 54.88 | — | no | dominated / outside near band |
| Claude Opus 4.7 (Adaptive Reasoning, Max Effort) | T3 | 54.34 | $1.9943 | no | dominated / outside near band |
| Grok 4.5 | T3 | 54.19 | $0.42565 | no | dominated / outside near band |
| Claude Sonnet 5 (max) | T3 | 53.93 | $1.9591 | no | dominated / outside near band |
| Grok 4.3 (high) | T3 | 53.00 | $0.14774 | no | dominated / outside near band |
| Muse Spark 1.1 (high effort) | T3 | 52.89 | — | no | dominated / outside near band |
| Claude Sonnet 5 (xhigh) | T3 | 52.47 | — | no | dominated / outside near band |
| GPT-5.4 (xhigh) | T3 | 52.31 | $1.1198 | no | price-close / capability-behind |
| Muse Spark 1.1 | T3 | 52.27 | — | no | dominated / outside near band |
| openai/gpt-5.5 | T3 | 52.26 | — | no | dominated / outside near band |
| Gemini 3.5 Flash (high) | T3 | 52.01 | $0.91825 | no | dominated / outside near band |
| DeepSeek V4 Flash 0731 (max) | T3 | 52.00 | $0.034235 | no | price-close / capability-behind |
| Claude Opus 5 (low) | T3 | 52.00 | $0.34445 | no | dominated / outside near band |
| Claude Sonnet 4.6 (Adaptive Reasoning, Max Effort) | T3 | 52.00 | $1.8744 | no | price-close / capability-behind |
| GPT-5.6 Terra (xhigh) | T3 | 51.90 | $0.48269 | no | dominated / outside near band |
| GLM-5.2 (max) | T3 | 51.39 | $0.37697 | YES | STRICT FRONTIER |
| GPT-5.6 Sol (low) | T3 | 51.00 | $0.2105 | no | capability-close / price-heavy |
| GPT-5.5 (low) | T3 | 51.00 | $0.25183 | no | capability-close / price-heavy |
| Gemini 3.6 Flash (high) | T3 | 50.59 | $0.33307 | no | capability-close / price-heavy |
| GPT-5.5 (medium) | T3 | 50.00 | $0.47587 | no | capability-close / price-heavy |

## Bottom contested region

The lower end is contested by cost compression rather than flagship quality. This section combines the cheapest eight Pareto configurations with models within ±2 capability points of the D↔C (30) and C↔B (40) boundaries.

| Model/configuration | Tier | Capability | Cost | Pareto | Why included |
|---|---|---:|---:|---|---|
| Qwen3.5 0.8B (Non-reasoning) | T4 | 4.42 | $0.0014213 | YES | low-cost Pareto segment |
| Granite 4.0 H Small | T4 | 5.24 | $0.0037824 | YES | low-cost Pareto segment |
| GLM-4.7-Flash (Non-reasoning) | T4 | 15.52 | $0.0038603 | YES | low-cost Pareto segment |
| GLM-4.7-Flash (Reasoning) | T4 | 22.89 | $0.0060278 | YES | low-cost Pareto segment |
| MiMo-V2.5 | T4 | 41.96 | $0.010649 | YES | low-cost Pareto segment; near C/B boundary |
| GPT-5.6 Luna (medium) | T4 | 39.00 | $0.011567 | YES | low-cost Pareto segment; near C/B boundary |
| Muse Spark 1.2 (xhigh, Contributor pricing) | T2 | 57.10 | $0.12719 | YES | low-cost Pareto segment |
| GLM-5.2 (max) | T3 | 51.39 | $0.37697 | YES | low-cost Pareto segment |
| Qwen3.5 122B A10B (Non-reasoning) | T4 | 28.12 | $0.063783 | no | near D/C boundary |
| Qwen3 Max | T4 | 28.14 | $0.15729 | no | near D/C boundary |
| Claude 4.1 Opus (Non-reasoning) | T4 | 28.24 | $0.7145 | no | near D/C boundary |
| KAT-Coder-Pro V1 | T4 | 28.26 | $0.029311 | no | near D/C boundary |
| MiniMax-M2 | T4 | 28.31 | $0.03716 | no | near D/C boundary |
| JT-35B-Flash | T4 | 28.36 | — | no | near D/C boundary |
| DeepSeek V4 Flash (Non-reasoning) | T4 | 28.65 | $0.0084724 | no | near D/C boundary; price-close / capability-behind |
| Laguna Xs.2 | T4 | 28.97 | — | no | near D/C boundary |
| Qwen3.5 35B A3B (Reasoning) | T4 | 29.26 | $0.084398 | no | near D/C boundary |
| Claude 4.5 Sonnet (Non-reasoning) | T4 | 29.28 | $0.25479 | no | near D/C boundary |
| Qwen3.6 27B (Non-reasoning) | T4 | 29.28 | $0.10137 | no | near D/C boundary |
| Command A+ | T4 | 29.29 | — | no | near D/C boundary |
| Qwen3.5 27B (Non-reasoning) | T4 | 29.31 | $0.051641 | no | near D/C boundary |
| Gemma 4 31B (Reasoning) | T4 | 29.35 | — | no | near D/C boundary |
| Kimi K2.5 (Non-reasoning) | T4 | 29.40 | $0.067118 | no | near D/C boundary |
| Claude 4.5 Haiku (Reasoning) | T4 | 29.58 | $0.17341 | no | near D/C boundary |
| gpt-5.2-default | T4 | 29.74 | — | no | near D/C boundary |
| GPT-5.4 mini (medium) | T4 | 29.81 | $0.0969 | no | near D/C boundary |
| GPT-5.4 nano (medium) | T4 | 30.16 | $0.032419 | no | near D/C boundary |
| Gemini 3.1 Flash-Lite | T4 | 30.28 | $0.028797 | no | near D/C boundary |
| o3 | T4 | 30.40 | $0.28612 | no | near D/C boundary |
| Ring-2.6-1T | T4 | 30.57 | $0.13699 | no | near D/C boundary |
| Grok 4.1 Fast (Reasoning) | T4 | 30.62 | — | no | near D/C boundary |
| GPT-5.1 Codex mini (high) | T4 | 30.63 | $0.071461 | no | near D/C boundary |
| Qwen3.5 Omni Plus | T4 | 30.64 | $0.094459 | no | near D/C boundary |
| mistralai/devstral-2512 | T4 | 30.66 | — | no | near D/C boundary |
| Claude 4 Sonnet (Reasoning) | T4 | 30.67 | $0.29216 | no | near D/C boundary |
| GPT-5 mini (medium) | T4 | 30.92 | $0.023386 | no | near D/C boundary |
| Claude 4 Opus (Reasoning) | T4 | 30.97 | $1.0934 | no | near D/C boundary |
| Grok 4.3 (Non-reasoning) | T4 | 31.00 | $0.099963 | no | near D/C boundary |
| GPT-5 (low) | T4 | 31.15 | $0.083038 | no | near D/C boundary |
| MiMo-V2-Flash (Reasoning) | T4 | 31.20 | $0.014556 | no | near D/C boundary |
| DeepSeek V4 Pro Preview (Non-reasoning) | T4 | 31.22 | $0.030397 | no | near D/C boundary |
| Qwen3.6 35B A3B (Reasoning) | T4 | 31.65 | $0.10276 | no | near D/C boundary |
| Qwen3 Max Thinking | T4 | 31.75 | $0.12376 | no | near D/C boundary |
| mistralai/mistral-small-2603 | T4 | 31.84 | — | no | near D/C boundary |
| Laguna M.1 | T4 | 31.87 | — | no | near D/C boundary |
| Qwen3.5 397B A17B (Non-reasoning) | T4 | 31.98 | $0.083931 | no | near D/C boundary |
| Ling 3.0 Flash (reasoning) | T4 | 38.00 | $0.022481 | no | near C/B boundary; capability-close / price-heavy |
| GLM-5-Turbo | T4 | 38.06 | — | no | near C/B boundary |
| claude-4.6-opus-thinking-high | T4 | 38.13 | — | no | near C/B boundary |
| Claude Sonnet 4.5 20250929 Thinking | T4 | 38.51 | — | no | near C/B boundary |
| GPT-5.1 | T4 | 38.75 | — | no | near C/B boundary |
| Mistral Medium 3.5 | T4 | 39.00 | $0.33945 | no | near C/B boundary; capability-close / price-heavy |
| GPT-5.1 Codex Max | T4 | 39.09 | — | no | near C/B boundary |
| Qwen 3.6 Plus | T4 | 39.12 | — | no | near C/B boundary |
| GPT-5.4 (low) | T4 | 39.14 | $0.18948 | no | near C/B boundary |
| MiniMax-M2.7 | T4 | 39.18 | $0.049986 | no | near C/B boundary |
| GPT-5 (high) | T4 | 39.29 | $0.20957 | no | near C/B boundary |
| gpt-5.2-pro | T4 | 39.39 | — | no | near C/B boundary |
| GLM-5 (Reasoning) | T4 | 39.42 | $0.059855 | no | near C/B boundary |
| Gemini 3 Pro Preview (high) | T4 | 39.55 | $0.20704 | no | near C/B boundary |
| x-ai/grok-build-0.1 | T4 | 39.64 | — | no | near C/B boundary |
| Gemini 3.5 Flash-Lite (high) | T4 | 39.73 | $0.071951 | no | near C/B boundary |
| GPT-5.6 Terra (low) | T4 | 40.00 | $0.1092 | no | near C/B boundary; capability-close / price-heavy |
| Qwen3.6 Max Preview | T4 | 40.00 | $0.18647 | no | near C/B boundary; capability-close / price-heavy |
| GPT-5.1 (high) | T4 | 40.07 | $0.16911 | no | near C/B boundary; capability-close / price-heavy |
| MiMo-V2-Pro | T4 | 40.29 | $0.11881 | no | near C/B boundary; capability-close / price-heavy |
| Qwen3.6 Max Preview | T4 | 40.48 | — | no | near C/B boundary |
| gemini-3-pro-preview | T4 | 40.54 | — | no | near C/B boundary |
| Claude Opus 4.5 (Reasoning) | T4 | 40.77 | $0.59664 | no | near C/B boundary; capability-close / price-heavy |
| DeepSeek V4 Pro Preview (Reasoning, High Effort) | T4 | 40.83 | $0.035156 | no | near C/B boundary; capability-close / price-heavy |
| Claude Opus 4.5 20251101 Thinking | T4 | 41.22 | — | no | near C/B boundary |
| Inkling | T4 | 41.25 | — | no | near C/B boundary |
| GPT-5.4 nano (xhigh) | T4 | 41.25 | $0.12138 | no | near C/B boundary; capability-close / price-heavy |
| Nemotron 3 Ultra 550B A55B (Reasoning) | T4 | 41.29 | $0.14206 | no | near C/B boundary; capability-close / price-heavy |
| Muse Spark | T4 | 41.35 | — | no | near C/B boundary |
| gemini-3-flash-low | T4 | 41.43 | — | no | near C/B boundary |
| gemini-3-flash-high | T4 | 41.71 | — | no | near C/B boundary |
| Qwen3.6 Plus | T4 | 41.78 | $0.16015 | no | near C/B boundary; capability-close / price-heavy |
| google/gemini-3-flash-preview | T4 | 41.80 | — | no | near C/B boundary |
| GPT-5.6 Sol (non-reasoning) | T4 | 42.00 | $0.13841 | no | near C/B boundary |

## Closest competitors to the strict Pareto frontier

| Model/configuration | Tier | Capability | Cost | Dominated by | Capability gap | Cost premium | Status |
|---|---|---:|---:|---|---:|---:|---|
| Claude Opus 5 (high) | T2 | 59.97 | $1.23 | GPT-5.6 Sol (max) | 0.69 | 0.0% | razor-edge miss |
| Qwen3.5 0.8B (Reasoning) | T4 | 4.97 | $0.0050158 | Granite 4.0 H Small | 0.27 | 42.2% | near-frontier |
| Claude Opus 5 (max) | T1 | 61.13 | $2.34 | Claude Opus 5 (xhigh) | 0.77 | 30.0% | near-frontier |
| GPT-5.5 (xhigh) | T2 | 57.54 | $0.99918 | GPT-5.5 (high) | 1.02 | 42.5% | near-frontier |
| DeepSeek V4 Flash 0731 (High) | T4 | 37.00 | $0.010662 | GPT-5.6 Luna (medium) | 2.00 | 6.6% | near-frontier |
| Muse Spark 1.2 (xhigh, Standard pricing) | T2 | 57.10 | $0.4 | Muse Spark 1.2 (xhigh, Contributor pricing) | 0.00 | 1784.1% | capability-close / price-heavy |
| Mistral Medium 3.5 | T4 | 39.00 | $0.26612 | GPT-5.6 Luna (medium) | 0.00 | 2561.2% | capability-close / price-heavy |
| Claude Fable 5 (xhigh) | T2 | 59.12 | $1.7571 | GPT-5.6 Sol (xhigh) | 0.04 | 116.9% | capability-close / price-heavy |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.16836 | Muse Spark 1.2 (xhigh, Contributor pricing) | 0.10 | 693.0% | capability-close / price-heavy |
| GPT-5.6 Sol (high) | T2 | 57.00 | $0.55 | Muse Spark 1.2 (xhigh, Contributor pricing) | 0.10 | 2490.6% | capability-close / price-heavy |
| Qwen3 Omni 30B A3B Instruct | T4 | 5.11 | $0.054267 | Granite 4.0 H Small | 0.12 | 1438.1% | capability-close / price-heavy |
| Qwen3.6 Plus | T4 | 41.78 | $0.14709 | MiMo-V2.5 | 0.18 | 1233.2% | capability-close / price-heavy |
| LFM2 24B A2B | T4 | 4.95 | $0.0068352 | Granite 4.0 H Small | 0.29 | 93.7% | capability-close / price-heavy |
| Gemini 2.5 Flash-Lite Preview (Sep '25) (Reasoning) | T4 | 15.13 | $0.011426 | GLM-4.7-Flash (Non-reasoning) | 0.39 | 196.0% | capability-close / price-heavy |
| GPT-5.5 (low) | T3 | 51.00 | $0.21075 | GLM-5.2 (max) | 0.39 | 1329.4% | capability-close / price-heavy |
| GPT-5.6 Sol (low) | T3 | 51.00 | $0.23 | GLM-5.2 (max) | 0.39 | 1460.0% | capability-close / price-heavy |
| Grok 4.20 0309 (Non-reasoning) | T4 | 22.48 | $0.10865 | GLM-4.7-Flash (Reasoning) | 0.41 | 1702.6% | capability-close / price-heavy |
| GPT-5.4 mini (xhigh) | T4 | 41.43 | $0.3085 | MiMo-V2.5 | 0.53 | 2696.2% | capability-close / price-heavy |
| Nemotron 3 Nano Omni 30B A3B Reasoning | T4 | 14.93 | $0.019647 | GLM-4.7-Flash (Non-reasoning) | 0.59 | 408.9% | capability-close / price-heavy |
| NVIDIA Nemotron Nano 12B v2 VL (Non-reasoning) | T4 | 4.58 | $0.06521 | Granite 4.0 H Small | 0.66 | 1748.2% | capability-close / price-heavy |

## Named high-interest competitors

These entries come from the explicit analysis-policy watchlist and remain visible even when they are not among the twenty numerically closest misses.

| Model/configuration | Tier | Capability | Cost | Status |
|---|---|---:|---:|---|
| Qwen3.8 Max (xhigh) | T2 | 56.71 | $1.13 | capability-close / price-heavy |
| Claude Fable 5 (max) | T1 | 60.41 | $3.14 | capability-close / price-heavy |
| GPT-5.6 Sol (max) | T1 | 60.65 | $1.23 | STRICT FRONTIER |
| Kimi K3 (max) | T2 | 59.87 | $0.84 | STRICT FRONTIER |
| Claude Sonnet 5 (max) | T3 | 53.93 | $0.58975 | economically dominated |
| DeepSeek V4 Flash 0731 (max) | T3 | 52.00 | $0.03 | price-close / capability-behind |
| GPT-5.6 Luna (xhigh) | T3 | 48.83 | $0.03 | economically dominated |
| Grok 4.3 (high) | T3 | 53.00 | $0.10662 | economically dominated |
| Gemini 3.1 Pro Preview | T2 | 57.00 | $0.16836 | capability-close / price-heavy |
| MiMo-V2.5-Pro | T4 | 43.39 | $0.034705 | economically dominated |
