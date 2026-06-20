# Session Data — 2026-06-19
# Distilled from 69 raw prompts. Source: RAW_USER_PROMPTS_2026-06-19.md
# This file contains the actual data, observations, and tasks. Nothing fabricated.

---

## CONFIRMED DATA POINTS

### Model Intelligence (Artificial Analysis, cached 2026-06-07)
| Model | AI Index | Coding Index | Notes |
|-------|----------|-------------|-------|
| MiniMax-M3 | 54.7 | 43.4 | Highest scoring free model. User hasn't used much yet. |
| MiMo-V2.5-Pro | 53.8 | 45.5 | Nearly tied with MiniMax. Stronger coding score. |
| MiMo-V2.5 (base) | 49.0 | 42.1 | Base variant, not Flash. |
| DeepSeek V4 Flash (Reasoning Max) | 46.5 | 38.7 | User finds this "feels" better than 46.5 suggests |
| DeepSeek V4 Pro (Reasoning Max) | 51.5 | 47.5 | Paid variant, not free |
| Nemotron 3 Ultra 550B | 47.7 | 37.6 | Scores higher than V4 Flash on paper, but user reports worse in practice |
| Nemotron 3 Super 120B | 36.0 | 31.2 | Significantly behind Ultra |
| Nemotron 3 Nano 30B | 21.4 | 14.8 | Bottom tier for reasoning |
| Gemma 4 31B (Reasoning) | 39.2 | 38.7 | Underperforms per user |
| Gemma 4 26B A4B (Reasoning) | 31.2 | 22.4 | |
| Gemma 3 12B | 8.8 | 6.3 | Severely underpowered |
| GLM 5.1 (Reasoning) | 51.4 | 43.4 | GLM 5.2 not in cache. User says GLM 5.2 likely beats MiniMax |
| GLM-5 (Reasoning) | 49.8 | 44.2 | |
| Kimi K2.6 | 53.9 | 47.1 | Strong scores, not user-verified |
| Qwen 3.6+ | 50.0 | — | Fastest high-IQ free model (53 TPS) |

### Models Missing AA Data (need conditional estimation)
- North Mini Code (Cohere)
- Nex N2 Pro
- Owl Alpha (OpenRouter)
- Laguna M.1 / M.2 (Poolside)
- StepFun models
- MiMo-V2.5-Pro-UltraSpeed
- GLM 5.2 (not in cache, only GLM 5.1)

### Speed Data (from model-scan live probes)
| Model | TPS | Latency | AI Index |
|-------|-----|---------|----------|
| minimax-m3-free (opencode-zen) | 16.4 | 1.95s | 54.7 |
| mimo-v2.5-free (opencode-zen) | 16.8 | 1.90s | 49.0 |
| deepseek-v4-flash-free (opencode-zen) | 21.8 | 1.47s | 46.5 |
| nemotron-3-ultra-550b-a55b:free (openrouter) | 14.1 | 1.49s | 47.7 |
| nemotron-3-super-120b-a12b:free (openrouter) | 10.8 | 2.96s | 36.0 |
| qwen3.6-plus-free (opencode-zen) | 53.0 | 0.20s | 50.0 |
| kimi-k2.6:free (openrouter) | 43.3 | 0.61s | 53.9 |
| gemma-4-31b-it:free (openrouter) | 3.6 | 0.83s | 39.2 |
| gpt-oss-120b (cerebras) | 75.7 | 0.42s | 33.3 |
| gpt-oss-120b (groq) | 363.3 | 0.08s | 33.3 |

---

## USER OBSERVATIONS (empirical, not benchmark-verified)

1. **DeepSeek V4 Flash has "magic"**: Despite scoring lower than Nemotron 3 Ultra on AA (46.5 vs 47.7), its reasoning traces are more effective. It "just gets shit done instead of asking for clarification, or getting in loops." This is a real qualitative dimension benchmarks don't capture.

2. **Nemotron 3 Ultra lacks "magic"**: Higher AA score but feels worse in practice. Gets stuck in clarification loops.

3. **GLM 5.2 > MiniMax-M3**: User states GLM 5.2 is "very likely better than mimax by a considerable degree." Not verifiable — GLM 5.2 not in AA cache.

4. **Gemma underperforms**: Confirmed by user. (Also supported by low AA scores.)

5. **Gemini underperforms**: User states it underperforms in practice vs benchmarks.

6. **StepFun punches above weight**: User assertion, unverified.

7. **Qwen series**: User says newest models are strong performers.

---

## AVAILABLE SERVICES (user's accounts)
| Service | Tier | Notes |
|---------|------|-------|
| Anthropic | $20/mo | Claude models |
| OpenAI | $20/mo | GPT-4o, o-series |
| Google | $20/mo | Gemini 2.5 Pro/Flash |
| Perplexity | $20/mo | Sonar with search |
| Opencode Go | $10/mo | ~$50 usage included + free models |
| Opencode Zen | Free | Part of Opencode account |
| Groq | Free quota | Llama/Mixtral |
| Cerebras | Free quota | Fast inference |
| NVIDIA NIM | Free quota | Nemotron models |
| Ollama Cloud | Free quota | |
| Antigravity | Via Gemini | Opus 4.7, restricted to Antigravity CLI |

---

## TASKS (14 items from Prompt 62)

### Task 1: User Sentiment Research
Find user sentiment for top 10 models on social media and X. Include region tags.

### Task 2: Slot Quality Refinement
Define what qualities each Hermes config role requires. Speed vs intelligence tradeoff analysis: if a model is 2x faster and fails tool calls at the same rate, it's better for that role.

### Task 3: Model Size × AI Index Cross-Reference
Cross-reference models.dev size/architecture data with AA intelligence scores. Build predictive understanding.

### Task 4: Conditional Scoring Engine (into model-scan)
Until full recalibration is done, estimate scores from release date + architecture + params. This is the fallback mechanic until scraped data is available.

### Task 5: Chinese Model Papers
Find release papers for: Kimi K2.6, GLM 5.2, Qwen 3.7, MiniMax M3.

### Task 6: Benchmark List from Papers
Extract which benchmarks each paper uses. Make a list of benchmarks to target.

### Task 7: Scrape Those Benchmarks
Scrape the benchmark data using model-scan's method. Understand what data they provide and how to use it.

### Task 8: Speed/Latency Calibration
Calibrate everything against real speed and latency data.

### Task 9: API Error Log Calibration
Calibrate against real API error logs from all sessions. Identify models that consistently underperform or have issues.

### Task 10: Write Project Summary
Include summarized version of all the above in model-scan itself. (Done — this file.)

### Task 11: Project Completion Check
Check if model-scan is "done" or has remaining items. (Done — TODO.md shows 14 remaining tasks.)

### Task 12: `model-scan overall -a` Command
CLI returning best A-tier model. `--free` flag for free tier. Slottable into git-audit-sync and other scripts.

### Task 13: Abstracted Evaluation Logic
The evaluation logic should be exposed as a callable interface. When a script calls for a model, it always gets an appropriate one.

### Task 14: Conditional Values Until Scraped
Until scrape data is available, conditional values set via arch/release-date estimation mechanic.

---

## FILES WRITTEN THIS SESSION

| File | Content |
|------|---------|
| `docs/RAW_USER_PROMPTS_2026-06-19.md` | All 69 prompts, full verbatim text |
| `docs/SESSION_DATA_2026-06-19.md` | This file — distilled data, observations, tasks |
| `docs/CALIBRATION_PLAN.md` | Phase 3 calibration plan (needs cleanup of fabricated claims) |
| `docs/SESSION_TASKS_2026-06-19.md` | Initial task capture (superseded by this file) |
| `empirical_observations.md` | User observations (superseded by this file) |
| `FULL_SESSION_LOG_2026-06-19.md` | Initial session log (superseded by RAW + DATA) |
| `TODO.md` | Updated with Phase 3 tasks |
