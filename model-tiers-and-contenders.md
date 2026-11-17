# ARDF Model Tiers + Contested Regions (v7.5.0)

This document answers a different question from the Pareto cheatsheet: **tiers classify calibrated capability**, while Pareto membership classifies economic non-dominance.

Canonical data: `data/unified-model-evidence.csv`. Policy: `project-config.json`. Regenerate with `python calibrate.py`.

## Fine-grained capability tier policy (S+ through D)

| Tier | Minimum calibrated capability | Interpretation |
|---|---:|---|
| T1 | 60 | Frontier ceiling |
| T2 | 56 | Frontier |
| T3 | 47 | Executor |
| T4 | 0 | Utility - bottom-4 interchangeable |

## Operational 4-tier routing policy (T1 to T4)

For day-to-day multi-agent orchestration, the capability space is partitioned into four operational routing tiers:

| Operational Tier | Capability Band (v4.2) | Primary Routing Role | Canonical Frontier & Near-Frontier Representatives |
|---|---|---|---|
| **T1 · Frontier Ceiling** | **>= 60.0** | Deep architectural judgment, hard verification, adversarial audits, final arbitration | `Claude Fable 5.2 (Max)` (64.56, $26.54), `Claude Fable 5.2 (Xhigh)` (62.22, $14.83), `Claude Fable 5.2 (High)` (61.82, $9.08), `Gemini 4 Carbon (High)` (60.02, $7.76) |
| **T2 · Frontier** | **56.0 to 59.9** | Complex multi-file synthesis, refactoring, spec-to-code implementation | `Claude Opus 5.5 (Max)` (58.95, $10.04, near-frontier), `Gemini 4 Carbon (Medium)` (58.28, $6.59), `Claude Opus 5.5 (Xhigh)` (57.29, $6.05), `GPT-6 Astra (Max)` (56.85, $6.24, razor-edge miss), `Claude Fable 5.2 (Medium)` (56.37, $3.80) |
| **T3 · Executor** | **47.0 to 55.9** | High-throughput subagent fan-outs, test generation, doc synthesis, autonomous coding | `GPT-6 Astra (Xhigh)` (55.30, $3.66), `GPT-6 Astra (High)` (54.83, $3.24), `GPT-6.1 Sol (Max)` (54.54, $1.27), `GPT-6.1 Sol (Xhigh)` (52.43, $0.76), `GPT-6.1 Terra (Max)` (51.32, $0.96, near-frontier), `GPT-6.1 Sol (High)` (50.31, $0.59) |
| **T4 · Utility (Bottom-4 Interchangeable)** | **< 47.0** | Classification, extraction, routing probes, high-volume batch filtering | `GPT-6.1 Sol (Medium)` (46.31, $0.36), `GPT-6.1 Terra (High)` (42.43, $0.26), `GPT-6.1 Terra (Medium)` (38.15, $0.17), `Muse Ember (Max)` (36.02, $0.14), `Muse Ember (Xhigh)` (34.11, $0.12), `GPT-6.1 Terra (Low)` (29.42, $0.071), `Claude Haiku 5.5 (Low)` (18.64, $0.044), `GPT-6 Luna (Low)` (9.67, $0.005) |

## Current scored configurations by tier

### T1 · Frontier ceiling (4)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Claude Fable 5.2 (Max, Default Fallback) | 64.56 | $26.539 | YES | - |
| Claude Fable 5.2 (Xhigh, Default Fallback) | 62.22 | $14.829 | YES | - |
| Claude Fable 5.2 (High, Default Fallback) | 61.82 | $9.0784 | YES | - |
| Gemini 4 Carbon (High) | 60.02 | $7.7555 | YES | - |

### T2 · Frontier (5)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Claude Opus 5.5 (Max, Default Fallback) | 58.95 | $10.036 | no | near-frontier |
| Gemini 4 Carbon (Medium) | 58.28 | $6.5858 | YES | - |
| Claude Opus 5.5 (Xhigh, Default Fallback) | 57.29 | $6.0472 | YES | - |
| GPT-6 Astra (Max) | 56.85 | $6.2447 | no | razor-edge miss |
| Claude Fable 5.2 (Medium, Default Fallback) | 56.37 | $3.8026 | YES | - |

### T3 · Executor (18)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| GPT-6 Astra (Xhigh) | 55.30 | $3.6589 | YES | - |
| GPT-6 Astra (High) | 54.83 | $3.2386 | YES | - |
| Claude Sonnet 5.5 (Max, Default Fallback) | 54.56 | $10.021 | no | capability-close / price-heavy |
| GPT-6.1 Sol (Max) | 54.54 | $1.2721 | YES | - |
| Gemini 4 Carbon (Low) | 54.22 | $7.1866 | no | capability-close / price-heavy |
| Claude Fable 5.2 (Low, Default Fallback) | 53.89 | $3.0972 | no | capability-close / price-heavy |
| GPT-6.1 Sol (Xhigh) | 52.43 | $0.76399 | YES | - |
| Claude Opus 5.5 (High, Default Fallback) | 51.67 | $3.4647 | no | price-close / capability-behind |
| GPT-6 Astra (Medium) | 51.57 | $2.7324 | no | capability-close / price-heavy |
| GPT-6.1 Terra (Max) | 51.32 | $0.96111 | no | near-frontier |
| Gemini 4 Argon (High) | 50.38 | $9.9466 | no | - |
| GPT-6.1 Sol (High) | 50.31 | $0.59099 | YES | - |
| Muse Wonder Full (Max) | 50.08 | - | no | - |
| Claude Sonnet 5.5 (Xhigh, Default Fallback) | 49.89 | $4.092 | no | capability-close / price-heavy |
| Claude Fable 5.1 (Xhigh, Default Fallback) | 49.87 | $10.847 | no | - |
| Claude Fable 5.1 (Max, Default Fallback) | 49.09 | $12.994 | no | - |
| Claude Opus 5.5 (Medium, Default Fallback) | 48.04 | $2.4511 | no | - |
| Claude Fable 5.1 (High, Default Fallback) | 47.06 | $7.54 | no | - |

### T4 · Utility - bottom-4 interchangeable (89)

| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |
|---|---:|---:|---|---|
| Kimi K3.1 Pro | 46.43 | $3.6812 | no | - |
| GPT-6.1 Sol (Medium) | 46.31 | $0.35939 | YES | - |
| GPT-6.1 Terra (Xhigh) | 45.28 | $0.40069 | no | near-frontier |
| GPT-6 Sol (Max) | 44.14 | $2.4658 | no | - |
| Claude Opus 5 (Max) | 44.02 | $11.821 | no | - |
| Muse Wonder (Max) | 43.57 | $6.952 | no | - |
| GPT-6 Astra (Low) | 43.30 | $1.4237 | no | - |
| Claude Fable 5.1 (Medium, Default Fallback) | 43.04 | $5.5643 | no | - |
| GPT-6.1 Terra (High) | 42.43 | $0.25928 | YES | - |
| Claude Sonnet 5.5 (High, Default Fallback) | 41.52 | $1.6361 | no | capability-close / price-heavy |
| Muse Wonder (High) | 40.53 | $4.5605 | no | capability-close / price-heavy |
| Claude Fable 5.1 (Low, Default Fallback) | 38.60 | $4.4711 | no | - |
| GPT-6.1 Terra (Medium) | 38.15 | $0.1688 | YES | - |
| Muse Spark 1.3 (Max) | 36.49 | $2.3858 | no | capability-close / price-heavy |
| Claude Haiku 5.5 (Max) | 36.44 | $0.41101 | no | capability-close / price-heavy |
| Muse Ember (Max) | 36.02 | $0.13594 | YES | - |
| Grok 4.7 (Xhigh) | 35.32 | $7.7715 | no | - |
| Grok 4.7 (High) | 35.10 | $6.1836 | no | capability-close / price-heavy |
| GPT-6.1 Sol (Low) | 34.77 | $0.16147 | no | near-frontier |
| Claude Opus 5.5 (Low, Default Fallback) | 34.71 | $0.97553 | no | capability-close / price-heavy |
| Claude Haiku 5.5 (Xhigh) | 34.57 | $0.24836 | no | capability-close / price-heavy |
| Tencent Hy4 | 34.56 | $1.0311 | no | capability-close / price-heavy |
| Muse Ember (Xhigh) | 34.11 | $0.11623 | YES | - |
| Qwen3.8 Max (0902) | 33.37 | $10.024 | no | - |
| DeepSeek V4.1 Flash 1017 (Max) | 32.59 | $0.60211 | no | capability-close / price-heavy |
| GPT-5.6 Terra (Max) | 32.31 | $3.7349 | no | capability-close / price-heavy |
| GLM-5.3 (Max) | 31.48 | $5.0093 | no | - |
| Grok 4.7 (Low) | 31.04 | $2.9222 | no | - |
| Grok 4.6 (Xhigh) | 30.91 | $4.6786 | no | - |
| Gemini 3.8 Flash (High) | 30.86 | $7.766 | no | - |
| Claude Sonnet 5.5 (Medium, Default Fallback) | 30.66 | $0.78066 | no | - |
| Inkling 2 Small | 30.63 | $1.1784 | no | - |
| GPT-6.1 Terra (Non-reasoning) | 30.50 | $0.2259 | no | - |
| Gemini 3.8 Flash (Medium) | 30.12 | $6.2586 | no | - |
| Claude Haiku 5.5 (High) | 29.87 | $0.15856 | no | price-close / capability-behind |
| MiMo-V2.6-Pro | 29.81 | $0.25718 | no | - |
| Ling 3.1 Flash 1019 | 29.56 | $3.1851 | no | - |
| GPT-6.1 Terra (Low) | 29.42 | $0.071338 | YES | - |
| MiniMax-M3.1-Flash | 29.07 | $0.49097 | no | capability-close / price-heavy |
| DeepSeek V4.1 Flash 1017 (High) | 28.64 | $0.45619 | no | capability-close / price-heavy |
| Step 5 Preview | 28.47 | $2.3453 | no | capability-close / price-heavy |
| GPT-6 Luna (Max) | 27.87 | $0.15196 | no | capability-close / price-heavy |
| GLM-5.3-Flash | 27.73 | $0.58331 | no | capability-close / price-heavy |
| MiMo-V2.6-Flash | 26.64 | $0.12853 | no | - |
| Mistral Large 4 (High) | 26.11 | $2.0617 | no | - |
| Claude Sonnet 5.5 (Low, Default Fallback) | 25.62 | $0.51134 | no | - |
| Mistral Large 4 Preview | 25.33 | $4.2089 | no | - |
| Muse Spark Open (Xhigh) | 24.87 | $2.0177 | no | - |
| Claude Haiku 5.5 (Medium) | 24.58 | $0.091765 | no | price-close / capability-behind |
| Agnes 2.5 Pro Theta | 24.03 | $0.57467 | no | - |
| GPT-5.6 Luna (Max) | 23.74 | $0.33126 | no | - |
| GPT-6 Luna (Xhigh) | 23.44 | $0.10409 | no | price-close / capability-behind |
| Mistral Large 4 (Medium) | 23.11 | $1.4121 | no | - |
| GLM-5.3 (Low) | 23.07 | $1.5749 | no | - |
| DeepSeek V4 Pro 0813 (Max) | 23.00 | $1.7691 | no | - |
| GPT-6 Luna (High) | 21.44 | $0.072948 | no | price-close / capability-behind |
| Nanbeige4.3-33B | 20.41 | - | no | - |
| Qwen3.8 27B (Xhigh) | 20.01 | $3.5295 | no | - |
| MiniMax-M3 | 18.85 | $1.2851 | no | - |
| Claude Haiku 5.5 (Low) | 18.64 | $0.043758 | YES | - |
| DeepSeek V4.1 Flash 1017 (Non-reasoning) | 18.51 | $0.42542 | no | capability-close / price-heavy |
| GPT-6 Luna (Medium) | 18.43 | $0.042202 | YES | - |
| K2 Horizon 375B A23B | 17.73 | - | no | - |
| Beam 1.0 | 17.73 | $0.28441 | no | capability-close / price-heavy |
| Kimi K3 (Low) | 17.43 | $2.3688 | no | capability-close / price-heavy |
| Qwen3.8 27B (Medium) | 17.40 | $2.16 | no | capability-close / price-heavy |
| Qwen3.8 27B (Low) | 15.60 | $1.9059 | no | - |
| Nemotron 3.5 Super VL | 13.62 | $0.51963 | no | - |
| Inkling Small | 12.93 | $0.20316 | no | - |
| DeepSeek V4 Pro 0813 (Non-reasoning) | 12.57 | $0.97699 | no | - |
| Inkling (Xhigh) | 12.51 | $1.352 | no | - |
| Nemotron 3 Ultra 550B A55B (Reasoning) | 11.78 | $2.2257 | no | - |
| Gemini 3.5 Flash-Lite | 11.72 | $0.6929 | no | - |
| Qwen3.8 27B (Non-reasoning) | 10.08 | $3.7729 | no | - |
| GPT-6 Luna (Low) | 9.67 | $0.0051153 | YES | - |
| GPT-6 Luna (Non-reasoning) | 9.44 | $0.071417 | no | capability-close / price-heavy |
| K-EXAONE 2.0 | 7.56 | - | no | - |
| Claude 4.5 Haiku (Reasoning) | 7.47 | $0.53178 | no | - |
| Muse Glimmer (High) | 6.34 | $0.1695 | no | - |
| Command A+ | 6.24 | - | no | - |
| Gemini 3.1 Flash-Lite | 6.16 | $0.19445 | no | - |
| Nemotron 3.5 Lightning | 5.58 | $0.31445 | no | - |
| Granite 4.2 8B | 5.10 | $0.040463 | no | - |
| Granite 4.2 3B | 4.72 | - | no | - |
| Mistral Medium 3.5 | 4.71 | $1.0391 | no | - |
| Mistral Small 4 (Reasoning) | 4.30 | $0.039909 | no | - |
| gpt-oss-120b (High) | 3.82 | $0.34534 | no | - |
| North Mini Code | 3.42 | - | no | - |
| NVIDIA Nemotron 3 Nano 4B | 1.82 | - | no | - |

## Top contested region

The upper contest zone includes configurations at capability >= 50, spanning the A+/S/S+ boundary neighborhood where small capability differences can carry large cost penalties.

| Model/configuration | Tier | Capability | Cost | Pareto | Closest economic verdict |
|---|---|---:|---:|---|---|
| Claude Fable 5.2 (Max, Default Fallback) | T1 | 64.56 | $26.539 | YES | STRICT FRONTIER |
| Claude Fable 5.2 (Xhigh, Default Fallback) | T1 | 62.22 | $14.829 | YES | STRICT FRONTIER |
| Claude Fable 5.2 (High, Default Fallback) | T1 | 61.82 | $9.0784 | YES | STRICT FRONTIER |
| Gemini 4 Carbon (High) | T1 | 60.02 | $7.7555 | YES | STRICT FRONTIER |
| Claude Opus 5.5 (Max, Default Fallback) | T2 | 58.95 | $10.036 | no | near-frontier |
| Gemini 4 Carbon (Medium) | T2 | 58.28 | $6.5858 | YES | STRICT FRONTIER |
| Claude Opus 5.5 (Xhigh, Default Fallback) | T2 | 57.29 | $6.0472 | YES | STRICT FRONTIER |
| GPT-6 Astra (Max) | T2 | 56.85 | $6.2447 | no | razor-edge miss |
| Claude Fable 5.2 (Medium, Default Fallback) | T2 | 56.37 | $3.8026 | YES | STRICT FRONTIER |
| GPT-6 Astra (Xhigh) | T3 | 55.30 | $3.6589 | YES | STRICT FRONTIER |
| GPT-6 Astra (High) | T3 | 54.83 | $3.2386 | YES | STRICT FRONTIER |
| Claude Sonnet 5.5 (Max, Default Fallback) | T3 | 54.56 | $10.021 | no | capability-close / price-heavy |
| GPT-6.1 Sol (Max) | T3 | 54.54 | $1.2721 | YES | STRICT FRONTIER |
| Gemini 4 Carbon (Low) | T3 | 54.22 | $7.1866 | no | capability-close / price-heavy |
| Claude Fable 5.2 (Low, Default Fallback) | T3 | 53.89 | $3.0972 | no | capability-close / price-heavy |
| GPT-6.1 Sol (Xhigh) | T3 | 52.43 | $0.76399 | YES | STRICT FRONTIER |
| Claude Opus 5.5 (High, Default Fallback) | T3 | 51.67 | $3.4647 | no | price-close / capability-behind |
| GPT-6 Astra (Medium) | T3 | 51.57 | $2.7324 | no | capability-close / price-heavy |
| GPT-6.1 Terra (Max) | T3 | 51.32 | $0.96111 | no | near-frontier |
| Gemini 4 Argon (High) | T3 | 50.38 | $9.9466 | no | dominated / outside near band |
| GPT-6.1 Sol (High) | T3 | 50.31 | $0.59099 | YES | STRICT FRONTIER |
| Muse Wonder Full (Max) | T3 | 50.08 | - | no | dominated / outside near band |

## Pinch-point contested pairs (delta capability <= 2.0, delta cost <= 25%)

Pinch points identify cross-family pairs that sit within 2.0 capability points and 25% task cost of one another. Within a pinch point, benchmark noise exceeds the capability gap, so harness fit, latency, context window, and subscription quota should decide routing.

| Model A | Tier A | Cap A | Cost A | Model B | Tier B | Cap B | Cost B | Cap Delta | Cost Delta |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| Claude Fable 5.2 (High, Default Fallback) | T1 | 61.82 | $9.0784 | Gemini 4 Carbon (High) | T1 | 60.02 | $7.7555 | 1.80 | 17.1% |
| Gemini 4 Carbon (Medium) | T2 | 58.28 | $6.5858 | GPT-6 Astra (Max) | T2 | 56.85 | $6.2447 | 1.43 | 5.5% |
| Gemini 4 Carbon (Medium) | T2 | 58.28 | $6.5858 | Claude Opus 5.5 (Xhigh, Default Fallback) | T2 | 57.29 | $6.0472 | 0.99 | 8.9% |
| Claude Opus 5.5 (Xhigh, Default Fallback) | T2 | 57.29 | $6.0472 | GPT-6 Astra (Max) | T2 | 56.85 | $6.2447 | 0.43 | 3.3% |
| Claude Fable 5.2 (Medium, Default Fallback) | T2 | 56.37 | $3.8026 | GPT-6 Astra (Xhigh) | T3 | 55.30 | $3.6589 | 1.07 | 3.9% |
| Claude Fable 5.2 (Medium, Default Fallback) | T2 | 56.37 | $3.8026 | GPT-6 Astra (High) | T3 | 54.83 | $3.2386 | 1.54 | 17.4% |
| GPT-6 Astra (Xhigh) | T3 | 55.30 | $3.6589 | Claude Fable 5.2 (Low, Default Fallback) | T3 | 53.89 | $3.0972 | 1.41 | 18.1% |
| GPT-6 Astra (High) | T3 | 54.83 | $3.2386 | Claude Fable 5.2 (Low, Default Fallback) | T3 | 53.89 | $3.0972 | 0.94 | 4.6% |
| Claude Opus 5.5 (High, Default Fallback) | T3 | 51.67 | $3.4647 | Claude Sonnet 5.5 (Xhigh, Default Fallback) | T3 | 49.89 | $4.092 | 1.78 | 18.1% |
| Gemini 4 Argon (High) | T3 | 50.38 | $9.9466 | Claude Fable 5.1 (Xhigh, Default Fallback) | T3 | 49.87 | $10.847 | 0.51 | 9.1% |
| GPT-6.1 Sol (Medium) | T4 | 46.31 | $0.35939 | GPT-6.1 Terra (Xhigh) | T4 | 45.28 | $0.40069 | 1.03 | 11.5% |
| Muse Ember (Max) | T4 | 36.02 | $0.13594 | GPT-6.1 Sol (Low) | T4 | 34.77 | $0.16147 | 1.25 | 18.8% |
| Claude Haiku 5.5 (Low) | T4 | 18.64 | $0.043758 | GPT-6 Luna (Medium) | T4 | 18.43 | $0.042202 | 0.21 | 3.7% |

## Bottom contested region

The lower end is contested by cost compression rather than flagship quality. This section combines the cheapest eight Pareto configurations with models within +/- 2 capability points of the D/C (30) and C/B (40) boundaries.

| Model/configuration | Tier | Capability | Cost | Pareto | Why included |
|---|---|---:|---:|---|---|
| GPT-6 Luna (Low) | T4 | 9.67 | $0.0051153 | YES | low-cost Pareto segment |
| GPT-6 Luna (Medium) | T4 | 18.43 | $0.042202 | YES | low-cost Pareto segment |
| Claude Haiku 5.5 (Low) | T4 | 18.64 | $0.043758 | YES | low-cost Pareto segment |
| GPT-6.1 Terra (Low) | T4 | 29.42 | $0.071338 | YES | low-cost Pareto segment; near D/C boundary |
| Muse Ember (Xhigh) | T4 | 34.11 | $0.11623 | YES | low-cost Pareto segment |
| Muse Ember (Max) | T4 | 36.02 | $0.13594 | YES | low-cost Pareto segment |
| GPT-6.1 Terra (Medium) | T4 | 38.15 | $0.1688 | YES | low-cost Pareto segment; near C/B boundary |
| GPT-6.1 Terra (High) | T4 | 42.43 | $0.25928 | YES | low-cost Pareto segment |
| Step 5 Preview | T4 | 28.47 | $2.3453 | no | near D/C boundary; capability-close / price-heavy |
| DeepSeek V4.1 Flash 1017 (High) | T4 | 28.64 | $0.45619 | no | near D/C boundary; capability-close / price-heavy |
| MiniMax-M3.1-Flash | T4 | 29.07 | $0.49097 | no | near D/C boundary; capability-close / price-heavy |
| Ling 3.1 Flash 1019 | T4 | 29.56 | $3.1851 | no | near D/C boundary |
| MiMo-V2.6-Pro | T4 | 29.81 | $0.25718 | no | near D/C boundary |
| Claude Haiku 5.5 (High) | T4 | 29.87 | $0.15856 | no | near D/C boundary; price-close / capability-behind |
| Gemini 3.8 Flash (Medium) | T4 | 30.12 | $6.2586 | no | near D/C boundary |
| GPT-6.1 Terra (Non-reasoning) | T4 | 30.50 | $0.2259 | no | near D/C boundary |
| Inkling 2 Small | T4 | 30.63 | $1.1784 | no | near D/C boundary |
| Claude Sonnet 5.5 (Medium, Default Fallback) | T4 | 30.66 | $0.78066 | no | near D/C boundary |
| Gemini 3.8 Flash (High) | T4 | 30.86 | $7.766 | no | near D/C boundary |
| Grok 4.6 (Xhigh) | T4 | 30.91 | $4.6786 | no | near D/C boundary |
| Grok 4.7 (Low) | T4 | 31.04 | $2.9222 | no | near D/C boundary |
| GLM-5.3 (Max) | T4 | 31.48 | $5.0093 | no | near D/C boundary |
| Claude Fable 5.1 (Low, Default Fallback) | T4 | 38.60 | $4.4711 | no | near C/B boundary |
| Muse Wonder (High) | T4 | 40.53 | $4.5605 | no | near C/B boundary; capability-close / price-heavy |
| Claude Sonnet 5.5 (High, Default Fallback) | T4 | 41.52 | $1.6361 | no | near C/B boundary; capability-close / price-heavy |

## Bottom-4 (T4 Utility) interchangeability matrix by use case

Below capability 47 (T4), specialized operational traits (latency, open-weights self-hosting, structured output reliability, and context window) dominate selection across interchangeable Pareto and near-frontier peers:

| Workload / Use Case | Primary T4 Pick | Drop-in Interchangeable Peers | Selection Rationale |
|---|---|---|---|
| **Upper-T4 code & CLI worker (42 to 46 cap)** | `GPT-6.1 Sol (Medium)` (46.31, $0.359) | `GPT-6.1 Terra (Xhigh)` (45.28, $0.401), `GPT-6.1 Terra (High)` (42.43, $0.259), `Kimi K3.1 Pro` (46.43, $3.681, open-weights) | Sol Medium and Terra High sit on the strict Pareto frontier under $0.36/task; Kimi K3.1 Pro provides the highest open-weights capability in this band. |
| **Low-cost synthesis & reasoning (34 to 38 cap)** | `GPT-6.1 Terra (Medium)` (38.15, $0.169) | `Muse Ember (Max)` (36.02, $0.136), `GPT-6.1 Sol (Low)` (34.77, $0.161), `Muse Ember (Xhigh)` (34.11, $0.116), `Claude Haiku 5.5 (Max)` (36.44, $0.411) | Three strict Pareto points (`Muse Ember Xhigh`, `Muse Ember Max`, `GPT-6.1 Terra Medium`) cluster tightly between $0.116 and $0.169/task. |
| **Sub-$0.10 batch extraction & classification (18 to 30 cap)** | `GPT-6.1 Terra (Low)` (29.42, $0.071) | `Claude Haiku 5.5 (Medium)` (24.58, $0.092), `Claude Haiku 5.5 (Low)` (18.64, $0.044), `GPT-6 Luna (Medium)` (18.43, $0.042) | Strict Pareto rungs for high-volume JSON/schema extraction where T3 reasoning is unnecessary overhead. |
| **Ultra-floor micro-triage (< $0.045/task)** | `GPT-6 Luna (Low)` (9.67, $0.0051) | `Mistral Small 4 (Reasoning)` (4.30, $0.040), `Granite 4.2 8B` (5.10, $0.040), `GPT-6 Luna (Medium)` (18.43, $0.042) | `GPT-6 Luna (Low)` achieves the lowest literal $/capability ($0.000529/pt) in the entire current dataset. |

## Closest competitors to the strict Pareto frontier

| Model/configuration | Tier | Capability | Cost | Dominated by | Capability gap | Cost premium | Status |
|---|---|---:|---:|---|---:|---:|---|
| GPT-6 Astra (Max) | T2 | 56.85 | $6.2447 | Claude Opus 5.5 (Xhigh, Default Fallback) | 0.43 | 3.3% | razor-edge miss |
| GPT-6.1 Terra (Xhigh) | T4 | 45.28 | $0.40069 | GPT-6.1 Sol (Medium) | 1.03 | 11.5% | near-frontier |
| Claude Opus 5.5 (Max, Default Fallback) | T2 | 58.95 | $10.036 | Gemini 4 Carbon (High) | 1.07 | 29.4% | near-frontier |
| GPT-6.1 Terra (Max) | T3 | 51.32 | $0.96111 | GPT-6.1 Sol (Xhigh) | 1.11 | 25.8% | near-frontier |
| GPT-6.1 Sol (Low) | T4 | 34.77 | $0.16147 | Muse Ember (Max) | 1.25 | 18.8% | near-frontier |
| DeepSeek V4.1 Flash 1017 (Non-reasoning) | T4 | 18.51 | $0.42542 | Claude Haiku 5.5 (Low) | 0.13 | 872.2% | capability-close / price-heavy |
| GPT-6 Luna (Non-reasoning) | T4 | 9.44 | $0.071417 | GPT-6 Luna (Low) | 0.22 | 1296.2% | capability-close / price-heavy |
| MiniMax-M3.1-Flash | T4 | 29.07 | $0.49097 | GPT-6.1 Terra (Low) | 0.35 | 588.2% | capability-close / price-heavy |
| Claude Sonnet 5.5 (Xhigh, Default Fallback) | T3 | 49.89 | $4.092 | GPT-6.1 Sol (High) | 0.42 | 592.4% | capability-close / price-heavy |
| Claude Fable 5.2 (Low, Default Fallback) | T3 | 53.89 | $3.0972 | GPT-6.1 Sol (Max) | 0.64 | 143.5% | capability-close / price-heavy |
| Claude Sonnet 5.5 (Max, Default Fallback) | T3 | 54.56 | $10.021 | GPT-6 Astra (Xhigh) | 0.74 | 173.9% | capability-close / price-heavy |
| DeepSeek V4.1 Flash 1017 (High) | T4 | 28.64 | $0.45619 | GPT-6.1 Terra (Low) | 0.78 | 539.5% | capability-close / price-heavy |
| GPT-6 Astra (Medium) | T3 | 51.57 | $2.7324 | GPT-6.1 Sol (Xhigh) | 0.86 | 257.7% | capability-close / price-heavy |
| Beam 1.0 | T4 | 17.73 | $0.28441 | Claude Haiku 5.5 (Low) | 0.91 | 550.0% | capability-close / price-heavy |
| Claude Sonnet 5.5 (High, Default Fallback) | T4 | 41.52 | $1.6361 | GPT-6.1 Terra (High) | 0.91 | 531.0% | capability-close / price-heavy |
| Grok 4.7 (High) | T4 | 35.10 | $6.1836 | Muse Ember (Max) | 0.91 | 4448.9% | capability-close / price-heavy |
| Step 5 Preview | T4 | 28.47 | $2.3453 | GPT-6.1 Terra (Low) | 0.95 | 3187.5% | capability-close / price-heavy |
| Gemini 4 Carbon (Low) | T3 | 54.22 | $7.1866 | GPT-6 Astra (Xhigh) | 1.08 | 96.4% | capability-close / price-heavy |
| Kimi K3 (Low) | T4 | 17.43 | $2.3688 | Claude Haiku 5.5 (Low) | 1.21 | 5313.4% | capability-close / price-heavy |
| Qwen3.8 27B (Medium) | T4 | 17.40 | $2.16 | Claude Haiku 5.5 (Low) | 1.24 | 4836.3% | capability-close / price-heavy |

## Named high-interest competitors

These entries come from the explicit analysis-policy watchlist and remain visible even when they are not among the twenty numerically closest misses.

| Model/configuration | Tier | Capability | Cost | Status |
|---|---|---:|---:|---|
| GPT-6 Astra (Max) | T2 | 56.85 | $6.2447 | razor-edge miss |
| Claude Opus 5.5 (Max, Default Fallback) | T2 | 58.95 | $10.036 | near-frontier |
| Claude Sonnet 5.5 (Max, Default Fallback) | T3 | 54.56 | $10.021 | capability-close / price-heavy |
| Gemini 4 Carbon (Low) | T3 | 54.22 | $7.1866 | capability-close / price-heavy |
| Claude Fable 5.2 (Low, Default Fallback) | T3 | 53.89 | $3.0972 | capability-close / price-heavy |
| Claude Opus 5.5 (High, Default Fallback) | T3 | 51.67 | $3.4647 | price-close / capability-behind |
| GPT-6 Astra (Medium) | T3 | 51.57 | $2.7324 | capability-close / price-heavy |
| GPT-6.1 Terra (Max) | T3 | 51.32 | $0.96111 | near-frontier |
| Gemini 4 Argon (High) | T3 | 50.38 | $9.9466 | economically dominated |
| Claude Sonnet 5.5 (Xhigh, Default Fallback) | T3 | 49.89 | $4.092 | capability-close / price-heavy |
| Claude Fable 5.1 (Xhigh, Default Fallback) | T3 | 49.87 | $10.847 | economically dominated |
| Kimi K3.1 Pro | T4 | 46.43 | $3.6812 | economically dominated |
| GPT-6.1 Terra (Xhigh) | T4 | 45.28 | $0.40069 | near-frontier |
| GPT-6 Sol (Max) | T4 | 44.14 | $2.4658 | economically dominated |
| Muse Wonder (Max) | T4 | 43.57 | $6.952 | economically dominated |
| Muse Spark 1.3 (Max) | T4 | 36.49 | $2.3858 | capability-close / price-heavy |
| Claude Haiku 5.5 (Max) | T4 | 36.44 | $0.41101 | capability-close / price-heavy |
| Grok 4.7 (Xhigh) | T4 | 35.32 | $7.7715 | economically dominated |
| Qwen3.8 Max (0902) | T4 | 33.37 | $10.024 | economically dominated |
