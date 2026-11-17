# Full frontier for all models

Generated 2026-11-17 by `calibrate.py` from `sources/current/` (AA snapshot 2026-11-10). Do not edit by hand.

Primary AA v4.2 recomputation. Pool: 111 configurations with a complete score and a known cost (zero cost included, unknown cost excluded). A configuration is on the frontier when no other is at least as cheap and at least as good with one strict improvement; exact ties are kept. This is the measured universe, not every model that exists.

## All providers: 21 frontier configurations

| Cost / task | Score | Model | Provider | Effort |
|---:|---:|---|---|---|
| $0 | 17.73 | K2 Horizon 375B A23B | Institute of Foundation Models | high |
| $0.0422 | 18.43 | GPT-6 Luna (Medium) | OpenAI | medium |
| $0.0438 | 18.64 | Claude Haiku 5.5 (Low) | Anthropic | low |
| $0.0713 | 29.42 | GPT-6.1 Terra (Low) | OpenAI | low |
| $0.116 | 34.11 | Muse Ember (Xhigh) | Meta | xhigh |
| $0.136 | 36.02 | Muse Ember (Max) | Meta | max |
| $0.169 | 38.15 | GPT-6.1 Terra (Medium) | OpenAI | medium |
| $0.259 | 42.43 | GPT-6.1 Terra (High) | OpenAI | high |
| $0.359 | 46.31 | GPT-6.1 Sol (Medium) | OpenAI | medium |
| $0.591 | 50.31 | GPT-6.1 Sol (High) | OpenAI | high |
| $0.764 | 52.43 | GPT-6.1 Sol (Xhigh) | OpenAI | xhigh |
| $1.27 | 54.54 | GPT-6.1 Sol (Max) | OpenAI | max |
| $3.24 | 54.83 | GPT-6 Astra (High) | OpenAI | high |
| $3.66 | 55.30 | GPT-6 Astra (Xhigh) | OpenAI | xhigh |
| $3.80 | 56.37 | Claude Fable 5.2 (Medium, Default Fallback) | Anthropic | medium |
| $6.05 | 57.29 | Claude Opus 5.5 (Xhigh, Default Fallback) | Anthropic | xhigh |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | Google | medium |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | Google | high |
| $9.08 | 61.82 | Claude Fable 5.2 (High, Default Fallback) | Anthropic | high |
| $14.83 | 62.22 | Claude Fable 5.2 (Xhigh, Default Fallback) | Anthropic | xhigh |
| $26.54 | 64.56 | Claude Fable 5.2 (Max, Default Fallback) | Anthropic | max |

## Each provider's own frontier

A provider's frontier is computed over that provider's configurations only. "Global" marks members that are also on the all-provider frontier above.

### Anthropic (27 scored configurations, 13 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.0438 | 18.64 | Claude Haiku 5.5 (Low) | low | yes |
| $0.0918 | 24.58 | Claude Haiku 5.5 (Medium) | medium |  |
| $0.159 | 29.87 | Claude Haiku 5.5 (High) | high |  |
| $0.248 | 34.57 | Claude Haiku 5.5 (Xhigh) | xhigh |  |
| $0.411 | 36.44 | Claude Haiku 5.5 (Max) | max |  |
| $1.64 | 41.52 | Claude Sonnet 5.5 (High, Default Fallback) | high |  |
| $2.45 | 48.04 | Claude Opus 5.5 (Medium, Default Fallback) | medium |  |
| $3.10 | 53.89 | Claude Fable 5.2 (Low, Default Fallback) | low |  |
| $3.80 | 56.37 | Claude Fable 5.2 (Medium, Default Fallback) | medium | yes |
| $6.05 | 57.29 | Claude Opus 5.5 (Xhigh, Default Fallback) | xhigh | yes |
| $9.08 | 61.82 | Claude Fable 5.2 (High, Default Fallback) | high | yes |
| $14.83 | 62.22 | Claude Fable 5.2 (Xhigh, Default Fallback) | xhigh | yes |
| $26.54 | 64.56 | Claude Fable 5.2 (Max, Default Fallback) | max | yes |

### OpenAI (26 scored configurations, 13 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.00512 | 9.67 | GPT-6 Luna (Low) | low |  |
| $0.0422 | 18.43 | GPT-6 Luna (Medium) | medium | yes |
| $0.0713 | 29.42 | GPT-6.1 Terra (Low) | low | yes |
| $0.161 | 34.77 | GPT-6.1 Sol (Low) | low |  |
| $0.169 | 38.15 | GPT-6.1 Terra (Medium) | medium | yes |
| $0.259 | 42.43 | GPT-6.1 Terra (High) | high | yes |
| $0.359 | 46.31 | GPT-6.1 Sol (Medium) | medium | yes |
| $0.591 | 50.31 | GPT-6.1 Sol (High) | high | yes |
| $0.764 | 52.43 | GPT-6.1 Sol (Xhigh) | xhigh | yes |
| $1.27 | 54.54 | GPT-6.1 Sol (Max) | max | yes |
| $3.24 | 54.83 | GPT-6 Astra (High) | high | yes |
| $3.66 | 55.30 | GPT-6 Astra (Xhigh) | xhigh | yes |
| $6.24 | 56.85 | GPT-6 Astra (Max) | max |  |

### Google (8 scored configurations, 5 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.194 | 6.16 | Gemini 3.1 Flash-Lite | high |  |
| $0.693 | 11.72 | Gemini 3.5 Flash-Lite | high |  |
| $6.26 | 30.12 | Gemini 3.8 Flash (Medium) | medium |  |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | medium | yes |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | high | yes |

### Meta (7 scored configurations, 5 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.116 | 34.11 | Muse Ember (Xhigh) | xhigh | yes |
| $0.136 | 36.02 | Muse Ember (Max) | max | yes |
| $2.39 | 36.49 | Muse Spark 1.3 (Max) | max |  |
| $4.56 | 40.53 | Muse Wonder (High) | high |  |
| $6.95 | 43.57 | Muse Wonder (Max) | max |  |

### Alibaba (5 scored configurations, 4 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $1.91 | 15.60 | Qwen3.8 27B (Low) | low |  |
| $2.16 | 17.40 | Qwen3.8 27B (Medium) | medium |  |
| $3.53 | 20.01 | Qwen3.8 27B (Xhigh) | xhigh |  |
| $10.02 | 33.37 | Qwen3.8 Max (0902) | xhigh |  |

### DeepSeek (5 scored configurations, 3 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.425 | 18.51 | DeepSeek V4.1 Flash 1017 (Non-reasoning) | none |  |
| $0.456 | 28.64 | DeepSeek V4.1 Flash 1017 (High) | high |  |
| $0.602 | 32.59 | DeepSeek V4.1 Flash 1017 (Max) | max |  |

### Mistral (5 scored configurations, 4 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.0399 | 4.30 | Mistral Small 4 (Reasoning) | none |  |
| $1.04 | 4.71 | Mistral Medium 3.5 | high |  |
| $1.41 | 23.11 | Mistral Large 4 (Medium) | medium |  |
| $2.06 | 26.11 | Mistral Large 4 (High) | high |  |

### SpaceXAI (4 scored configurations, 3 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $2.92 | 31.04 | Grok 4.7 (Low) | low |  |
| $6.18 | 35.10 | Grok 4.7 (High) | high |  |
| $7.77 | 35.32 | Grok 4.7 (Xhigh) | xhigh |  |

### NVIDIA (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.314 | 5.58 | Nemotron 3.5 Lightning | none |  |
| $0.52 | 13.62 | Nemotron 3.5 Super VL | high |  |

### Thinking Machines (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.203 | 12.93 | Inkling Small | none |  |
| $1.18 | 30.63 | Inkling 2 Small | none |  |

### Z AI (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.583 | 27.73 | GLM-5.3-Flash | max |  |
| $5.01 | 31.48 | GLM-5.3 (Max) | max |  |

### Cohere (2 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0 | 6.24 | Command A+ | none |  |

### Kimi (2 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $2.37 | 17.43 | Kimi K3 (Low) | low |  |
| $3.68 | 46.43 | Kimi K3.1 Pro | max |  |

### MiniMax (2 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.491 | 29.07 | MiniMax-M3.1-Flash | max |  |

### Xiaomi (2 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.129 | 26.64 | MiMo-V2.6-Flash | none |  |
| $0.257 | 29.81 | MiMo-V2.6-Pro | none |  |

### IBM (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.0405 | 5.10 | Granite 4.2 8B | none |  |

### InclusionAI (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $3.19 | 29.56 | Ling 3.1 Flash 1019 | none |  |

### Institute of Foundation Models (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0 | 17.73 | K2 Horizon 375B A23B | high | yes |

### Reflection (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.284 | 17.73 | Beam 1.0 | none |  |

### Sapiens AI (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $0.575 | 24.03 | Agnes 2.5 Pro Theta | none |  |

### StepFun (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $2.35 | 28.47 | Step 5 Preview | none |  |

### Tencent (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Effort | Global |
|---:|---:|---|---|:--:|
| $1.03 | 34.56 | Tencent Hy4 | none |  |
