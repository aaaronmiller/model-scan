# Free-route evaluation

Generated 2026-11-17 by `calibrate.py` from `sources/current/` (AA snapshot 2026-11-10). Do not edit by hand.

Source: zero-price entries in the pinned OpenRouter, Kilo and OpenCode Zen catalogs (39 entries), matched to the primary AA scores by model name. A match ignores snapshot or version suffixes and is marked unverified when it does; zero listed price does not remove rate limits, privacy terms or availability changes. Scores are the AA v4.2 composite recomputed by ARDF at the model's best measured effort.

## Free routes with a measured score

| Score | Model (best measured configuration) | Effort | Match | Routes | Cheapest paid configuration at or above this score | Model on frontier at its paid price |
|---:|---|---|---|---|---|:--:|
| 32.59 | DeepSeek V4.1 Flash 1017 (Max) | max | name match, snapshot or version suffix ignored (identity unverified) | OpenCode Zen `opencode/deepseek-v4.1-flash-free` | Muse Ember (Xhigh) at $0.116 (34.11) | no |
| 27.73 | GLM-5.3-Flash | max | name match | OpenCode Zen `opencode/glm-5.3-flash-free` | GPT-6.1 Terra (Low) at $0.0713 (29.42) | no |
| 26.64 | MiMo-V2.6-Flash | none | name match | OpenCode Zen `opencode/mimo-v2.6-flash-free` | GPT-6.1 Terra (Low) at $0.0713 (29.42) | no |
| 17.73 | Beam 1.0 | none | name match | Kilo `reflection/beam-free` (may train on prompts); OpenCode Zen `opencode/beam-free` | GPT-6 Luna (Medium) at $0.0422 (18.43) | no |
| 13.62 | Nemotron 3.5 Super VL | high | name match | OpenRouter `nvidia/nemotron-3.5-super-vl:free`; Kilo `nvidia/nemotron-3.5-super-vl:free` (may train on prompts); OpenCode Zen `opencode/nemotron-3.5-super-vl-free` | GPT-6 Luna (Medium) at $0.0422 (18.43) | no |
| 11.78 | Nemotron 3 Ultra 550B A55B (Reasoning) | none | explicit alias (identity unverified) | OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free`; Kilo `nvidia/nemotron-3-ultra-550b-a55b:free` (may train on prompts) | GPT-6 Luna (Medium) at $0.0422 (18.43) | no |
| 5.58 | Nemotron 3.5 Lightning | none | name match | OpenRouter `nvidia/nemotron-3.5-lightning:free`; Kilo `nvidia/nemotron-3.5-lightning:free` (may train on prompts); OpenCode Zen `opencode/nemotron-3.5-lightning-free` | GPT-6 Luna (Low) at $0.00512 (9.67) | no |
| 3.42 | North Mini Code | none | name match | OpenRouter `cohere/north-mini-code:free`; Kilo `cohere/north-mini-code:free` (may train on prompts) | GPT-6 Luna (Low) at $0.00512 (9.67) | no |

The paid price of these models (AA workload cost per task) is: DeepSeek V4.1 Flash 1017 (Max) $0.602; GLM-5.3-Flash $0.583; MiMo-V2.6-Flash $0.129; Beam 1.0 $0.284; Nemotron 3.5 Super VL $0.52; Nemotron 3 Ultra 550B A55B (Reasoning) $2.23; Nemotron 3.5 Lightning $0.314; North Mini Code $0.

## AA lists a $0 price (route not identified in the three catalogs)

| Score | Model |
|---:|---|
| 17.73 | K2 Horizon 375B A23B |
| 6.24 | Command A+ |
| 3.42 | North Mini Code |

## Free routes with no measured score

No usable score exists in the pinned data, so they are not ranked. Names do not establish identity.

| Surface | Route | Kind | Why |
|---|---|---|---|
| Kilo | `dots-studio/dots-3-note-preview:free` | chat model | no matching primary configuration |
| Kilo | `google/lyria-3-clip-preview` | non-text output | no matching primary configuration |
| Kilo | `google/lyria-3-pro-preview` | non-text output | no matching primary configuration |
| Kilo | `kilo-auto/free` | router (not a stable model) | no matching primary configuration |
| Kilo | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | chat model | no matching primary configuration |
| Kilo | `openrouter/free` | router (not a stable model) | no matching primary configuration |
| Kilo | `stealth/crouton-alpha` | stealth or preview (identity unverified) | no matching primary configuration |
| Kilo | `stealth/glyph-cluster` | stealth or preview (identity unverified) | no matching primary configuration |
| OpenCode Zen | `opencode/big-pickle` | chat model | no matching primary configuration |
| OpenCode Zen | `opencode/crouton-alpha-free` | stealth or preview (identity unverified) | no matching primary configuration |
| OpenCode Zen | `opencode/flint-40b-free` | chat model | no matching primary configuration |
| OpenCode Zen | `opencode/pulse-alpha-free` | stealth or preview (identity unverified) | no matching primary configuration |
| OpenRouter | `dots-studio/dots-3-note-preview:free` | chat model | no matching primary configuration |
| OpenRouter | `google/gemma-4-26b-a4b-it:free` | chat model | matching primary configuration has no complete score |
| OpenRouter | `google/gemma-4-31b-it:free` | chat model | matching primary configuration has no complete score |
| OpenRouter | `google/lyria-3-clip-preview` | non-text output | no matching primary configuration |
| OpenRouter | `google/lyria-3-pro-preview` | non-text output | no matching primary configuration |
| OpenRouter | `liquid/lfm-2.5-2.6b:free` | chat model | matching primary configuration has no complete score |
| OpenRouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | chat model | no matching primary configuration |
| OpenRouter | `nvidia/nemotron-3.5-content-safety:free` | safety classifier | no matching primary configuration |
| OpenRouter | `openrouter/free` | router (not a stable model) | no matching primary configuration |
| OpenRouter | `recursive/flint-v1.0:free` | chat model | no matching primary configuration |
| OpenRouter | `stealth/crouton-alpha` | stealth or preview (identity unverified) | no matching primary configuration |
| OpenRouter | `xingchen-agi/xing4.0-29b-a4b:free` | chat model | no matching primary configuration |
