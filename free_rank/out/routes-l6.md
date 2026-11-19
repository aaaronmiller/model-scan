---
title: Free model routes for harness fallback chains
date: 2026-11-19
---

# Free model routes for harness fallback chains

One row per free route of every ranked model, in rank order. `omp` is the provider/model selector
for `~/.omp/agent/config.yml` fallbackChains; a route whose provider is not configured in omp is
marked. `opencode` uses the `opencode/` (Zen) or `opencode-go/` prefix. `kilo` is the Kilo gateway id.

| Rank | Tier | Model | Gateway | omp selector | OpenCode | Kilo | Limit tags |
|---|---|---|---|---|---|---|---|
| 1 | 1 | DeepSeek V4.1 Flash Free | opencode-zen | `opencode-zen/deepseek-v4.1-flash-free` | `opencode/deepseek-v4.1-flash-free` | - | none |
| 2 | 1 | Baidu: ERNIE-5.5-Flash-Preview (free) | kilo | `kilo/baidu/ernie-5.5-flash-preview:free` (provider not configured in omp) | - | `baidu/ernie-5.5-flash-preview:free` | sharing |
| 2 | 1 | Baidu: ERNIE-5.5-Flash-Preview (free) | openrouter | `openrouter/baidu/ernie-5.5-flash-preview:free` | `openrouter/baidu/ernie-5.5-flash-preview:free` | - | sharing |
| 3 | 1 | Inkling 2 Small Free | opencode-zen | `opencode-zen/inkling-2-small-free` | `opencode/inkling-2-small-free` | - | limited |
| 4 | 1 | MiMo-V2.6-Flash Free | opencode-zen | `opencode-zen/mimo-v2.6-flash-free` | `opencode/mimo-v2.6-flash-free` | - | none |
| 5 | 1 | LongCat 2.5 Free | opencode-go | `opencode-go/longcat-2.5-free` | `opencode-go/longcat-2.5-free` | - | zero-retention |
| 5 | 1 | LongCat 2.5 Free | opencode-zen | `opencode-zen/longcat-2.5-free` | `opencode/longcat-2.5-free` | - | zero-retention |
| 6 | 2 | Hy4 flash Free | opencode-go | `opencode-go/hy4-flash-free` | `opencode-go/hy4-flash-free` | - | zero-retention |
| 6 | 2 | Hy4 flash Free | opencode-zen | `opencode-zen/hy4-flash-free` | `opencode/hy4-flash-free` | - | zero-retention |
| 7 | 2 | Beam Free | kilo | `kilo/reflection/beam-free` (provider not configured in omp) | - | `reflection/beam-free` | region-restricted, sharing |
| 7 | 2 | Beam Free | opencode-go | `opencode-go/beam-free` | `opencode-go/beam-free` | - | region-restricted, sharing |
| 7 | 2 | Beam Free | opencode-zen | `opencode-zen/beam-free` | `opencode/beam-free` | - | region-restricted, sharing |
| 8 | 2 | Dots Studio: Dots3-Note Preview (free) | kilo | `kilo/dots-studio/dots-3-note-preview:free` (provider not configured in omp) | - | `dots-studio/dots-3-note-preview:free` | expires, sharing |
| 8 | 2 | Dots Studio: Dots3-Note Preview (free) | openrouter | `openrouter/dots-studio/dots-3-note-preview:free` | `openrouter/dots-studio/dots-3-note-preview:free` | - | expires, sharing |
| 9 | 2 | Flint 40B Free | kilo | `kilo/recursive/flint-v1.0:free` (provider not configured in omp) | - | `recursive/flint-v1.0:free` | sharing |
| 9 | 2 | Flint 40B Free | opencode-zen | `opencode-zen/flint-40b-free` | `opencode/flint-40b-free` | - | sharing |
| 9 | 2 | Flint 40B Free | openrouter | `openrouter/recursive/flint-v1.0:free` | `openrouter/recursive/flint-v1.0:free` | - | sharing |
| 10 | 2 | NVIDIA: Nemotron 3 Ultra (free) | kilo | `kilo/nvidia/nemotron-3-ultra-550b-a55b:free` (provider not configured in omp) | - | `nvidia/nemotron-3-ultra-550b-a55b:free` | sharing |
| 10 | 2 | NVIDIA: Nemotron 3 Ultra (free) | openrouter | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | - | sharing |
| 11 | 2 | Google: Gemma 4 26B A4B  (free) | openrouter | `openrouter/google/gemma-4-26b-a4b-it:free` | `openrouter/google/gemma-4-26b-a4b-it:free` | - | none |
| 12 | 2 | Nemotron 3.5 Super VL Free | kilo | `kilo/nvidia/nemotron-3.5-super-vl:free` (provider not configured in omp) | - | `nvidia/nemotron-3.5-super-vl:free` | sharing |
| 12 | 2 | Nemotron 3.5 Super VL Free | opencode-zen | `opencode-zen/nemotron-3.5-super-vl-free` | `opencode/nemotron-3.5-super-vl-free` | - | sharing |
| 12 | 2 | Nemotron 3.5 Super VL Free | openrouter | `openrouter/nvidia/nemotron-3.5-super-vl:free` | `openrouter/nvidia/nemotron-3.5-super-vl:free` | - | sharing |
| 13 | 3 | NVIDIA: Nemotron 3 Nano Omni (free) | kilo | `kilo/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (provider not configured in omp) | - | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | sharing |
| 13 | 3 | NVIDIA: Nemotron 3 Nano Omni (free) | openrouter | `openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | `openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | - | sharing |
| 14 | 3 | Google: Gemma 4 31B (free) | openrouter | `openrouter/google/gemma-4-31b-it:free` | `openrouter/google/gemma-4-31b-it:free` | - | none |
| 15 | 3 | Nemotron 3.5 Lightning Free | kilo | `kilo/nvidia/nemotron-3.5-lightning:free` (provider not configured in omp) | - | `nvidia/nemotron-3.5-lightning:free` | sharing |
| 15 | 3 | Nemotron 3.5 Lightning Free | opencode-zen | `opencode-zen/nemotron-3.5-lightning-free` | `opencode/nemotron-3.5-lightning-free` | - | sharing |
| 15 | 3 | Nemotron 3.5 Lightning Free | openrouter | `openrouter/nvidia/nemotron-3.5-lightning:free` | `openrouter/nvidia/nemotron-3.5-lightning:free` | - | sharing |
| 16 | 4 | Cohere: North Mini Code (free) | kilo | `kilo/cohere/north-mini-code:free` (provider not configured in omp) | - | `cohere/north-mini-code:free` | sharing |
| 16 | 4 | Cohere: North Mini Code (free) | openrouter | `openrouter/cohere/north-mini-code:free` | `openrouter/cohere/north-mini-code:free` | - | sharing |
| 17 | 4 | LiquidAI: LFM3-1.7B (free) | kilo | `kilo/liquid/lfm-3-1.7b:free` (provider not configured in omp) | - | `liquid/lfm-3-1.7b:free` | sharing |
| 17 | 4 | LiquidAI: LFM3-1.7B (free) | openrouter | `openrouter/liquid/lfm-3-1.7b:free` | `openrouter/liquid/lfm-3-1.7b:free` | - | sharing |
