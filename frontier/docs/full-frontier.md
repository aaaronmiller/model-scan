# Full frontier for all models

Generated 2026-11-17 by `calibrate.py` from `sources/current/` (AA snapshot 2026-11-10). Do not edit by hand.

Primary AA v4.2 recomputation. Pool: 109 configurations with a complete score and a trusted cost: prices above $0, plus a $0 only when a free route with the same name is listed in a pinned catalog (verified free). Unknown cost is excluded. An AA $0 with no such route is unverified: it is held out of dominance and listed in its own band below, so it can neither dominate a paid model nor drop one from the frontier. A configuration is on the frontier when no other is at least as cheap and at least as good with one strict improvement; exact ties are kept. This is the measured universe, not every model that exists.

**Warning on default-fallback tracks.** Rows marked FALLBACK are AA default-fallback tracks. The pinned data does not say what the fallback covers, and most have no scored standard-track counterpart, so read them as their own configurations, not as the standalone model. The fallback-free frontier is listed after the paid-only frontier.

## All providers: 22 frontier configurations

| Cost / task | Score | Model | Track | Provider | Effort |
|---:|---:|---|---|---|---|
| $0 | 3.42 | North Mini Code | standard | Cohere | none |
| $0.00512 | 9.67 | GPT-6 Luna (Low) | standard | OpenAI | low |
| $0.0422 | 18.43 | GPT-6 Luna (Medium) | standard | OpenAI | medium |
| $0.0438 | 18.64 | Claude Haiku 5.5 (Low) | standard | Anthropic | low |
| $0.0713 | 29.42 | GPT-6.1 Terra (Low) | standard | OpenAI | low |
| $0.116 | 34.11 | Muse Ember (Xhigh) | standard | Meta | xhigh |
| $0.136 | 36.02 | Muse Ember (Max) | standard | Meta | max |
| $0.169 | 38.15 | GPT-6.1 Terra (Medium) | standard | OpenAI | medium |
| $0.259 | 42.43 | GPT-6.1 Terra (High) | standard | OpenAI | high |
| $0.359 | 46.31 | GPT-6.1 Sol (Medium) | standard | OpenAI | medium |
| $0.591 | 50.31 | GPT-6.1 Sol (High) | standard | OpenAI | high |
| $0.764 | 52.43 | GPT-6.1 Sol (Xhigh) | standard | OpenAI | xhigh |
| $1.27 | 54.54 | GPT-6.1 Sol (Max) | standard | OpenAI | max |
| $3.24 | 54.83 | GPT-6 Astra (High) | standard | OpenAI | high |
| $3.66 | 55.30 | GPT-6 Astra (Xhigh) | standard | OpenAI | xhigh |
| $3.80 | 56.37 | Claude Fable 5.2 (Medium, Default Fallback) | FALLBACK | Anthropic | medium |
| $6.05 | 57.29 | Claude Opus 5.5 (Xhigh, Default Fallback) | FALLBACK | Anthropic | xhigh |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | standard | Google | medium |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | standard | Google | high |
| $9.08 | 61.82 | Claude Fable 5.2 (High, Default Fallback) | FALLBACK | Anthropic | high |
| $14.83 | 62.22 | Claude Fable 5.2 (Xhigh, Default Fallback) | FALLBACK | Anthropic | xhigh |
| $26.54 | 64.56 | Claude Fable 5.2 (Max, Default Fallback) | FALLBACK | Anthropic | max |

## Paid-only frontier: 21 configurations (prices above $0 only, 108 configurations)

Same rule with every $0 configuration removed, so it does not depend on whether any free route is real. `pareto-frontier-cheatsheet.md` applies the same cost above $0 rule to the multi-source ledger.

| Cost / task | Score | Model | Track | Provider | Effort |
|---:|---:|---|---|---|---|
| $0.00512 | 9.67 | GPT-6 Luna (Low) | standard | OpenAI | low |
| $0.0422 | 18.43 | GPT-6 Luna (Medium) | standard | OpenAI | medium |
| $0.0438 | 18.64 | Claude Haiku 5.5 (Low) | standard | Anthropic | low |
| $0.0713 | 29.42 | GPT-6.1 Terra (Low) | standard | OpenAI | low |
| $0.116 | 34.11 | Muse Ember (Xhigh) | standard | Meta | xhigh |
| $0.136 | 36.02 | Muse Ember (Max) | standard | Meta | max |
| $0.169 | 38.15 | GPT-6.1 Terra (Medium) | standard | OpenAI | medium |
| $0.259 | 42.43 | GPT-6.1 Terra (High) | standard | OpenAI | high |
| $0.359 | 46.31 | GPT-6.1 Sol (Medium) | standard | OpenAI | medium |
| $0.591 | 50.31 | GPT-6.1 Sol (High) | standard | OpenAI | high |
| $0.764 | 52.43 | GPT-6.1 Sol (Xhigh) | standard | OpenAI | xhigh |
| $1.27 | 54.54 | GPT-6.1 Sol (Max) | standard | OpenAI | max |
| $3.24 | 54.83 | GPT-6 Astra (High) | standard | OpenAI | high |
| $3.66 | 55.30 | GPT-6 Astra (Xhigh) | standard | OpenAI | xhigh |
| $3.80 | 56.37 | Claude Fable 5.2 (Medium, Default Fallback) | FALLBACK | Anthropic | medium |
| $6.05 | 57.29 | Claude Opus 5.5 (Xhigh, Default Fallback) | FALLBACK | Anthropic | xhigh |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | standard | Google | medium |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | standard | Google | high |
| $9.08 | 61.82 | Claude Fable 5.2 (High, Default Fallback) | FALLBACK | Anthropic | high |
| $14.83 | 62.22 | Claude Fable 5.2 (Xhigh, Default Fallback) | FALLBACK | Anthropic | xhigh |
| $26.54 | 64.56 | Claude Fable 5.2 (Max, Default Fallback) | FALLBACK | Anthropic | max |

## Fallback-free frontier: 18 configurations (standard tracks only, $0 rule as in the all-provider frontier)

The same pool with every default-fallback track removed, so each row is a standard AA track.

| Cost / task | Score | Model | Provider | Effort |
|---:|---:|---|---|---|
| $0 | 3.42 | North Mini Code | Cohere | none |
| $0.00512 | 9.67 | GPT-6 Luna (Low) | OpenAI | low |
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
| $6.24 | 56.85 | GPT-6 Astra (Max) | OpenAI | max |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | Google | medium |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | Google | high |

## Unverified free: 2 configurations (AA lists $0, held out of dominance)

These have a score and an AA price of exactly $0 but no free route with the same name in the pinned OpenRouter, Kilo or OpenCode Zen catalogs. They are not compared with any paid model.

| Score | Model | Provider | Evidence |
|---:|---|---|---|
| 17.73 | K2 Horizon 375B A23B | Institute of Foundation Models | AA lists $0 and no route with this name exists in the pinned OpenRouter, Kilo or OpenCode Zen catalogs |
| 6.24 | Command A+ | Cohere | AA lists $0 but the catalogs list a paid route: OpenRouter cohere/command-a-plus $0.3/M in, $1.5/M out; Kilo cohere/command-a-plus $0.3/M in, $1.5/M out |

## Each provider's own frontier

A provider's frontier is computed over that provider's configurations only. "Global" marks members that are also on the all-provider frontier above.

### Anthropic (27 scored configurations, 13 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.0438 | 18.64 | Claude Haiku 5.5 (Low) | standard | low | yes |
| $0.0918 | 24.58 | Claude Haiku 5.5 (Medium) | standard | medium |  |
| $0.159 | 29.87 | Claude Haiku 5.5 (High) | standard | high |  |
| $0.248 | 34.57 | Claude Haiku 5.5 (Xhigh) | standard | xhigh |  |
| $0.411 | 36.44 | Claude Haiku 5.5 (Max) | standard | max |  |
| $1.64 | 41.52 | Claude Sonnet 5.5 (High, Default Fallback) | FALLBACK | high |  |
| $2.45 | 48.04 | Claude Opus 5.5 (Medium, Default Fallback) | FALLBACK | medium |  |
| $3.10 | 53.89 | Claude Fable 5.2 (Low, Default Fallback) | FALLBACK | low |  |
| $3.80 | 56.37 | Claude Fable 5.2 (Medium, Default Fallback) | FALLBACK | medium | yes |
| $6.05 | 57.29 | Claude Opus 5.5 (Xhigh, Default Fallback) | FALLBACK | xhigh | yes |
| $9.08 | 61.82 | Claude Fable 5.2 (High, Default Fallback) | FALLBACK | high | yes |
| $14.83 | 62.22 | Claude Fable 5.2 (Xhigh, Default Fallback) | FALLBACK | xhigh | yes |
| $26.54 | 64.56 | Claude Fable 5.2 (Max, Default Fallback) | FALLBACK | max | yes |

### OpenAI (26 scored configurations, 13 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.00512 | 9.67 | GPT-6 Luna (Low) | standard | low | yes |
| $0.0422 | 18.43 | GPT-6 Luna (Medium) | standard | medium | yes |
| $0.0713 | 29.42 | GPT-6.1 Terra (Low) | standard | low | yes |
| $0.161 | 34.77 | GPT-6.1 Sol (Low) | standard | low |  |
| $0.169 | 38.15 | GPT-6.1 Terra (Medium) | standard | medium | yes |
| $0.259 | 42.43 | GPT-6.1 Terra (High) | standard | high | yes |
| $0.359 | 46.31 | GPT-6.1 Sol (Medium) | standard | medium | yes |
| $0.591 | 50.31 | GPT-6.1 Sol (High) | standard | high | yes |
| $0.764 | 52.43 | GPT-6.1 Sol (Xhigh) | standard | xhigh | yes |
| $1.27 | 54.54 | GPT-6.1 Sol (Max) | standard | max | yes |
| $3.24 | 54.83 | GPT-6 Astra (High) | standard | high | yes |
| $3.66 | 55.30 | GPT-6 Astra (Xhigh) | standard | xhigh | yes |
| $6.24 | 56.85 | GPT-6 Astra (Max) | standard | max |  |

### Google (8 scored configurations, 5 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.194 | 6.16 | Gemini 3.1 Flash-Lite | standard | high |  |
| $0.693 | 11.72 | Gemini 3.5 Flash-Lite | standard | high |  |
| $6.26 | 30.12 | Gemini 3.8 Flash (Medium) | standard | medium |  |
| $6.59 | 58.28 | Gemini 4 Carbon (Medium) | standard | medium | yes |
| $7.76 | 60.02 | Gemini 4 Carbon (High) | standard | high | yes |

### Meta (7 scored configurations, 5 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.116 | 34.11 | Muse Ember (Xhigh) | standard | xhigh | yes |
| $0.136 | 36.02 | Muse Ember (Max) | standard | max | yes |
| $2.39 | 36.49 | Muse Spark 1.3 (Max) | standard | max |  |
| $4.56 | 40.53 | Muse Wonder (High) | standard | high |  |
| $6.95 | 43.57 | Muse Wonder (Max) | standard | max |  |

### Alibaba (5 scored configurations, 4 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $1.91 | 15.60 | Qwen3.8 27B (Low) | standard | low |  |
| $2.16 | 17.40 | Qwen3.8 27B (Medium) | standard | medium |  |
| $3.53 | 20.01 | Qwen3.8 27B (Xhigh) | standard | xhigh |  |
| $10.02 | 33.37 | Qwen3.8 Max (0902) | standard | xhigh |  |

### DeepSeek (5 scored configurations, 3 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.425 | 18.51 | DeepSeek V4.1 Flash 1017 (Non-reasoning) | standard | none |  |
| $0.456 | 28.64 | DeepSeek V4.1 Flash 1017 (High) | standard | high |  |
| $0.602 | 32.59 | DeepSeek V4.1 Flash 1017 (Max) | standard | max |  |

### Mistral (5 scored configurations, 4 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.0399 | 4.30 | Mistral Small 4 (Reasoning) | standard | none |  |
| $1.04 | 4.71 | Mistral Medium 3.5 | standard | high |  |
| $1.41 | 23.11 | Mistral Large 4 (Medium) | standard | medium |  |
| $2.06 | 26.11 | Mistral Large 4 (High) | standard | high |  |

### SpaceXAI (4 scored configurations, 3 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $2.92 | 31.04 | Grok 4.7 (Low) | standard | low |  |
| $6.18 | 35.10 | Grok 4.7 (High) | standard | high |  |
| $7.77 | 35.32 | Grok 4.7 (Xhigh) | standard | xhigh |  |

### NVIDIA (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.314 | 5.58 | Nemotron 3.5 Lightning | standard | none |  |
| $0.52 | 13.62 | Nemotron 3.5 Super VL | standard | high |  |

### Thinking Machines (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.203 | 12.93 | Inkling Small | standard | none |  |
| $1.18 | 30.63 | Inkling 2 Small | standard | none |  |

### Z AI (3 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.583 | 27.73 | GLM-5.3-Flash | standard | max |  |
| $5.01 | 31.48 | GLM-5.3 (Max) | standard | max |  |

### Kimi (2 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $2.37 | 17.43 | Kimi K3 (Low) | standard | low |  |
| $3.68 | 46.43 | Kimi K3.1 Pro | standard | max |  |

### MiniMax (2 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.491 | 29.07 | MiniMax-M3.1-Flash | standard | max |  |

### Xiaomi (2 scored configurations, 2 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.129 | 26.64 | MiMo-V2.6-Flash | standard | none |  |
| $0.257 | 29.81 | MiMo-V2.6-Pro | standard | none |  |

### Cohere (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0 | 3.42 | North Mini Code | standard | none | yes |

### IBM (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.0405 | 5.10 | Granite 4.2 8B | standard | none |  |

### InclusionAI (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $3.19 | 29.56 | Ling 3.1 Flash 1019 | standard | none |  |

### Reflection (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.284 | 17.73 | Beam 1.0 | standard | none |  |

### Sapiens AI (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $0.575 | 24.03 | Agnes 2.5 Pro Theta | standard | none |  |

### StepFun (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $2.35 | 28.47 | Step 5 Preview | standard | none |  |

### Tencent (1 scored configurations, 1 on its frontier)

| Cost / task | Score | Model | Track | Effort | Global |
|---:|---:|---|---|---|:--:|
| $1.03 | 34.56 | Tencent Hy4 | standard | none |  |
