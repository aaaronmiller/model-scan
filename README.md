# model-scan v3

**Diagnostic instrument panel for LLM provider health.**

One unified list of all models, sorted by **Tier** (S/A/B/C) + **Composite Score**. Shows live probe data (latency, throughput, reliability), AA benchmark scores, use-case roles, and API key health.

---

## Features

- **One unified table** — all providers, all models, sorted by tier + score
- **TUIDS-LLM color system** — semantic colors + glyphs for instant scanning
- **Tier grading** — S/A/B/C based on composite score (AA intel + latency + reliability)
- **Role classification** — primary, reasoner, fast, vision, code, hybrid, general
- **Live probes** — latency, tokens/sec, reliability via actual API calls
- **AA integration** — Artificial Analysis benchmark scores (ai, ac, am, mmlu)
- **models.dev integration** — context limits, pricing, capabilities
- **API key health** — identifies failing keys with causes
- **Concurrent scanning** — semaphore-controlled parallelism (8 concurrent)
- **OpenRouter free models** — auto-fetched from API and included
- **History tracking** — last 30 runs stored in `~/.config/model-scan/results.json`

---

## Quick Start

```bash
# Install (copies to ~/.local/bin)
./install.sh

# Run
model-scan

# Working models only
model-scan -w

# Verbose (show failure details)
model-scan -v

# JSON output
model-scan --json

# Filter by provider
model-scan --provider groq
```

---

## Output Format

```
┌─ model-scan v3 ──────────────────────────────────────────────────────────────┐
│ FORGE  8 providers  55 models  47 failing  AA: ✓  │  ⏱ 16.1s             │
├──────────────────────────────────────────────────────────────────────────────┤
│ TIER │ MODEL (provider/path)          │ ROLE      │ LAT │ T/S │ AA  │ STATUS │
├──────────────────────────────────────────────────────────────────────────────┤
│  B   │ gemini-2.5-flash (google)     │ reasoner  │  2s │ 0.4 │ 82  │   ✓    │
│  B   │ owl-alpha (openrouter)        │ code      │  2s │ 1.3 │ 72  │   ✓    │
│  —   │ claude-sonnet-4 (anthropic)  │ —         │  —  │  —  │ 95  │   ✗    │
└──────────────────────────────────────────────────────────────────────────────┘

  ✓ 8 healthy  ✗ 47 dead

  󰓎 3 keys failing
    ✗ OPENROUTER_API_KEY  Invalid
    ✗ NVIDIA_API_KEY  Not found
```

---

## Column Definitions

| Column | Color | Content |
|--------|-------|---------|
| **TIER** | Green dim (S/A), Gray (B/C), Dark gray (—) | S, A, B, C, — |
| **MODEL** | White (name), Gray (provider) | Sacred content — no ANSI |
| **ROLE** | Cyan | primary, reasoner, fast, vision, code, hybrid, general |
| **LAT** | Blue (<2s), Amber (>2s), Red (>5s) | Latency in seconds |
| **T/S** | Blue (normal), Amber (<1.0 tok/s) | Tokens per second |
| **AA** | Blue (≥80), Amber (60-79), Dim (<60) | Artificial Analysis intelligence score |
| **STATUS** | Green ✓, Amber ⚠, Red ✗ | Health indicator |

---

## Tier Grading System

| Tier | Criteria | Example |
|------|----------|---------|
| **S** | Composite ≥89 (better than MiniMax-2.7 baseline) | claude-sonnet-4, deepseek-v4-pro |
| **A** | Composite 84-89 (MiniMax-2.7 baseline) | minimax-2.7, llama-4-maverick |
| **B** | Composite 70-83 | gemini-2.5-flash, owl-alpha |
| **C** | Composite 55-69 | functional but not recommended |
| **—** | Composite <55 or reliability <50% | ungraded |

**Composite Score** = AA intelligence + latency penalty + reliability bonus + MoE bonus

---

## Role Classification

| Role | Criteria |
|------|----------|
| `primary` | S-tier, tool-calling, AA ≥85 |
| `reasoner` | AA ≥70, no tools, slow (<50 tok/s) |
| `fast` | ≥100 tok/s, reliable |
| `vision` | Multimodal model |
| `code` | AA coding score ≥65 |
| `hybrid` | Balanced capabilities |
| `general` | Standard use |
| `—` | Unassigned or down |

---

## Data Sources

| Source | Data |
|--------|------|
| **Live probes** | Latency, throughput, reliability (1-shot ping) |
| **Artificial Analysis** | AA scores: ai, ac, am, mmlu (hardcoded, May 2026) |
| **models.dev** | Context limits, pricing, reasoning, tool_calling (via API) |
| **OpenRouter API** | Free model list + context from `/api/v1/models` |

---

## Supported Providers

| Provider | API Key | Models |
|----------|---------|--------|
| OpenRouter | `OPENROUTER_API_KEY` | owl-alpha, llama-3.3-70b, qwen3-coder, + auto free |
| Cerebras | `CEREBRAS_API_KEY` | qwen-3-235b, llama3.1-8b |
| Groq | `GROQ_API_KEY` | llama-3.3-70b, qwen3-32b, gpt-oss |
| NVIDIA NIM | `NVIDIA_API_KEY` | qwen3-next-80b, llama-3.1-8b |
| OpenCode Go | `OPENCODE_GO_API_KEY` | qwen3.6-plus |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4 |
| OpenAI | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| Google | `GOOGLE_API_KEY` | gemini-2.5-pro, gemini-2.5-flash |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-v4-pro |

---

## API Key Loading

Keys are loaded from (in order):
1. Environment variables already set
2. `~/.hermes/.env`
3. `~/code/claude-code-proxy/.env`
4. `~/.env`

---

## Requirements

- Python 3.8+
- `httpx` for async HTTP
- `python-dotenv` for .env loading (optional)

```bash
pip install --user httpx python-dotenv
```

---

## File Structure

```
~/.local/bin/model-scan          # Installed script
~/.config/model-scan/results.json  # History (last 30 runs)
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Missing httpx dependency |

---

## See Also

- [TUIDS-LLM Color System](color.md) — full color specification
- [User Requirements](USER_REQUIREMENTS.md) — aggregated from session history
- [Artificial Analysis](https://artificialanalysis.ai) — benchmark scores
- [models.dev](https://models.dev) — model metadata
