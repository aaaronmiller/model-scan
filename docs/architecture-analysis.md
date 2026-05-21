# model-scan Architecture Analysis & Design Document

**Generated:** 2026-05-13  
**Version:** v4 (with proposed v5 enhancements)

---

## Executive Summary

This document covers 5 major architecture questions for model-scan:

1. **Model Discovery** — How models are discovered, and how to implement weekly updates
2. **OpenCode Go Edge Case** — How to handle the subscription-based pricing model
3. **LLM-as-Judge Benchmark Evaluation** — How to validate slot rankings against external benchmarks
4. **Algorithm Refinement System** — How to iteratively improve slot fitness via historical data
5. **Remaining Features** — What's unfulfilled and what needs attention

---

## TRACK A: Model Discovery System

### Current State

The system uses **dynamic API discovery** — every scan fetches the full model list from each provider's API. There is **no hardcoded model list**.

**Provider discovery strategy:**

| Provider | API Endpoint | Strategy | Filter |
|----------|-------------|----------|--------|
| OpenRouter | `GET /models` | All models, filter for `:free` suffix | Only free models |
| NVIDIA NIM | `GET /models` | All models | Probe all |
| Groq | `GET /models` | All models | Probe all |
| Cerebras | `GET /models` | All models | Probe all |
| OpenCode Go | `GET /models` | All models (fixed list) | Probe all |
| Ollama Cloud | `GET /models` | Prefix whitelist only | `glm-5`, `kimi-k2`, `minimax-m2`, `qwen3-*`, etc. |
| Ollama Local | `GET /api/tags` | Local models only | None |
| Venice | `GET /models` | Catalog only | **No probes** (read-only API key) |

**Current flow:**
```
run_scan()
  → for each provider: list_models()     [fetches from API]
  → for each model: is_permanently_skipped() [checks bad_models.json]
  → for each candidate: probe_one()      [live HTTP probe]
  → for successful probes: probe_tools()  [tool call test]
  → build dossiers → compute fitness → render
```

**Key files:**
- `dink.py` lines 1024-1079: `list_models()` — fetches model catalog
- `dink.py` lines 1079-1147: `probe_one()` — live HTTP probe
- `dink.py` lines 1149-1197: `probe_tools()` — tool call capability test
- `~/.config/model-scan/bad_models.json` — permanently skipped models

### Design Decision: Weekly Update Process

**Architecture Decision: Hybrid Cache + Diff System**

The weekly update process should NOT be a separate script. Instead, it should be **integrated into the normal scan flow** with intelligent caching:

```
WEEKLY UPDATE FLOW (integrated into run_scan):

1. On first scan of the week:
   → Fetch full model list from all providers (current behavior)
   → Compare against last known list (from cached scan)
   → Report NEW models (added since last scan)
   → Report MISSING models (removed since last scan)
   → Update cached model list

2. On subsequent scans this week:
   → Use cached model list (no API calls for enumeration)
   → Only probe NEW models + all free-tier models
   → Skip probing unchanged models (use cached results)

3. Weekly trigger (via cron or manual):
   → Force full refresh (--refresh-all flag)
   → Full API enumeration for all providers
   → Re-probe any models that were "catalog-only" last week
   → Generate diff report
```

**Implementation:**

```python
# New constants
MODEL_LIST_CACHE = CONFIG_DIR / "model_list_cache.json"  # per-provider model lists
MODEL_LIST_TTL_HOURS = 168  # 1 week

# New CLI flag
--refresh-all        # Force full model list refresh (ignore cache)
--refresh-providers   # Force refresh for specific providers only
--model-diff         # Show model additions/removals since last scan

# New cache entry structure
{
  "providers": {
    "openrouter": {
      "fetched_at": "2026-05-13T00:00:00Z",
      "models": ["model-a:free", "model-b:free", ...],
      "etag": "abc123"  # for HTTP ETag support
    },
    "nvidia": { ... }
  },
  "scan_history": [
    {"date": "2026-05-06", "added": [...], "removed": [...]},
    {"date": "2026-05-13", "added": [...], "removed": [...]}
  ]
}
```

**Per-provider update strategies:**

| Provider | Update Strategy | Rationale |
|----------|---------------|-----------|
| OpenRouter | Full refresh weekly | Free model list changes frequently |
| NVIDIA NIM | Full refresh weekly | New NIMs added regularly |
| Groq | Full refresh weekly | New models added |
| Cerebras | Full refresh weekly | Stable but small catalog |
| OpenCode Go | **Fixed list** (no refresh needed) | Curated list from opencode.ai/go |
| Ollama Cloud | Prefix whitelist refresh | Family list changes slowly |
| Venice | Full refresh weekly | Large catalog |

**OpenCode Go special handling:**
The model list is **fixed** at OpenCode Go — it's a curated subscription. The models available don't change week-to-week. The scan should hardcode the expected list and flag if a model disappears:

```python
OPENCODE_GO_FIXED_MODELS = [
    "glm-5.1", "glm-5",           # Zhipu AI flagship
    "kimi-k2.6", "kimi-k2.5",   # Moonshot reasoning
    "deepseek-v4-pro", "deepseek-v4-flash",  # DeepSeek family
    "mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-pro", "mimo-v2-omni",  # MiniMax family
    "minimax-m2.7", "minimax-m2.5",  # MiniMax
    "qwen3.6-plus", "qwen3.5-plus",  # Qwen
    "hy3-preview",                    # Hypertune
]

# On scan: if any OCGo model is MISSING from API response,
# flag it as potentially discontinued or access-restricted
```

### Configuration Changes

**File:** `~/.config/model-scan/scan_config.yaml` (new)

```yaml
# model-scan configuration
providers:
  openrouter:
    strategy: free_only      # only :free models
    refresh_interval: 168h   # 1 week
  nvidia:
    strategy: all
    refresh_interval: 168h
  groq:
    strategy: all
    refresh_interval: 168h
  opencode-go:
    strategy: fixed_list     # curated subscription list
    refresh_interval: 720h  # monthly check is fine
  ollama-cloud:
    strategy: whitelist
    refresh_interval: 168h
    prefixes:
      - glm-5
      - kimi-k2
      - minimax-m2
      - qwen3-next
      - qwen3.5
      - gemini-3-flash
      - deepseek-v
      - devstral
      - gemma4
      - ministerial-3
      - cogito-2
      - rnj-
  venice:
    strategy: catalog_only   # read-only, no probes
    refresh_interval: 168h

notification:
  on_new_model: true
  on_model_removed: true
  on_accessibility_change: true
  report_format: slack  # or: email, stdout
```

---

## TRACK B: OpenCode Go Edge Case

### The Problem

OpenCode Go is **NOT pay-per-token**. It's a **$10/month subscription** with dollar-equivalent credits:

| Model | Requests/5hr | Requests/week | Requests/month | $/M tokens |
|-------|-------------|--------------|---------------|------------|
| GLM-5.1 | 880 | 2,150 | 4,300 | ~$0.48 |
| Kimi K2.6 | 1,150 | 2,880 | 5,750 | ~$0.25 |
| MiniMax M2.7 | 3,400 | 8,500 | 17,000 | ~$0.09 |
| DeepSeek V4 Flash | 31,650 | 79,050 | 158,150 | ~$0.005 |
| Qwen3.5 Plus | 10,200 | 25,200 | 50,500 | ~$0.02 |

**Key insight from user research (Patshead.com, 2026):**
- DeepSeek V4 Flash is **63x cheaper per request** than GLM-5.1
- MiniMax M2.7 is **5.5x cheaper** than Kimi K2.6
- User's usage pattern: 2 tasks/day averaging $0.05-0.10 each (MiniMax) or $0.20-0.40 each (GLM-5.1)
- $10 subscription = ~35M tokens of GLM-5 or ~115M tokens of MiniMax M2.7

### Strategy: Budget-Aware Model Selection

The slot ranking should incorporate **token budget efficiency**:

```python
# New: OpenCode Go budget scoring
# Added to slot_fitness() or as a separate budget_score()

OPENCODE_GO_BUDGET = {
    "glm-5.1":     {"requests_per_month": 4300,  "cost_per_m": 0.48, "quality": "S"},
    "glm-5":        {"requests_per_month": 5750,  "cost_per_m": 0.35, "quality": "A"},
    "kimi-k2.6":   {"requests_per_month": 5750,  "cost_per_m": 0.25, "quality": "S"},  # 58.6% SWE-Pro
    "kimi-k2.5":   {"requests_per_month": 9250,  "cost_per_m": 0.15, "quality": "B"},  # multimodal
    "deepseek-v4-pro": {"requests_per_month": 17150, "cost_per_m": 0.08, "quality": "A"},
    "deepseek-v4-flash": {"requests_per_month": 158150, "cost_per_m": 0.005, "quality": "A"},  # 79% SWE-Verified!
    "minimax-m2.7": {"requests_per_month": 17000, "cost_per_m": 0.09, "quality": "B"},
    "minimax-m2.5": {"requests_per_month": 31800, "cost_per_m": 0.05, "quality": "B"},  # 80.2% SWE-Verified
    "mimo-v2.5-pro": {"requests_per_month": 6450,  "cost_per_m": 0.22, "quality": "B"},
    "mimo-v2.5":    {"requests_per_month": 10900, "cost_per_m": 0.13, "quality": "B"},
    "mimo-v2-pro":  {"requests_per_month": 6450,  "cost_per_m": 0.22, "quality": "B"},
    "qwen3.6-plus": {"requests_per_month": 16300, "cost_per_m": 0.09, "quality": "B"},  # 61.6% Terminal-Bench
    "qwen3.5-plus": {"requests_per_month": 50500, "cost_per_m": 0.03, "quality": "B"},
}

def budget_score(model_id: str, slot_def: dict) -> float:
    """
    Returns 0-100 score for OpenCode Go budget efficiency.
    Higher = more requests per dollar, better for high-frequency slots.
    """
    info = OPENCODE_GO_BUDGET.get(model_id)
    if not info:
        return 50.0  # neutral for unknown
    
    # Efficiency: requests per month normalized to 0-100
    requests_score = min(100, info["requests_per_month"] / 500)
    
    # Quality tier bonus
    quality_bonus = {"S": 20, "A": 10, "B": 0}.get(info["quality"], 0)
    
    # Cost efficiency: inverse of cost per million
    cost_efficiency = min(100, 10 / (info["cost_per_m"] + 0.001))
    
    return round(requests_score * 0.4 + quality_bonus * 0.3 + cost_efficiency * 0.3, 1)
```

### Slot-Specific Budget Strategies

| Slot | Budget Strategy | Rationale |
|------|---------------|-----------|
| R1_primary | Quality-first (GLM-5.1, Kimi K2.6) | SWE-Bench performance matters most |
| R2_fallback | Budget-balanced (MiniMax M2.7) | Good quality, high volume |
| R6_compression | Budget-first (DeepSeek V4 Flash) | 158K requests/month, 79% SWE-Verified! |
| R8_web_extract | Budget-first (Qwen3.5 Plus) | 50K requests, 10x cheaper than GLM-5.1 |
| R_skills_hub | Budget-first (DeepSeek V4 Flash) | High-volume skill execution |

**Key insight:** DeepSeek V4 Flash at OCGo is the **highest-value model** — 79% SWE-Verified at $0.005/M tokens. It's currently failing the R1 probe due to http_402 (likely budget exhaustion at OCGo).

### Implementation Plan

```python
# In slot_fitness() — add budget dimension for OpenCode Go slots
if provider == "opencode-go":
    budget_weight = slot_def.get("weight_budget", 0.0)
    if budget_weight > 0:
        budget = budget_score(model_id, slot_def)
        # Blend into existing fitness
        fitness = fitness * (1 - budget_weight) + budget * budget_weight

# In slot definitions YAML:
R6_compression:
  budget_strategy: max_volume   # maximize requests per dollar
  preferred_models:
    - deepseek-v4-flash    # 158K requests/month
    - minimax-m2.7          # 17K requests/month
    - qwen3.5-plus          # 50K requests/month
```

---

## TRACK C: LLM-as-Judge Benchmark Evaluation

### The Problem

The current slot fitness algorithm uses:
1. **`_estimate_intelligence()`** — heuristic estimates based on model name patterns
2. **`weight_intelligence`/`weight_speed`** — hardcoded weights (0.90/0.10 for R1)
3. **`_estimate_intelligence()` is static** — doesn't learn from actual benchmark data

We need to **validate and refine** this algorithm against real benchmark data.

### Benchmarks Available (2026)

| Benchmark | What it measures | Key scores (2026) |
|-----------|-----------------|-------------------|
| **SWE-bench Verified** | Real GitHub issues, Python, single-repo | Claude Opus 4.6: 80.9%, Kimi K2.5: 76.8%, MiniMax M2.5: 80.2%, DeepSeek V4 Flash: 79% |
| **SWE-bench Pro (SEAL)** | Multi-file, multi-language, harder | Claude Opus 4.5: 45.9%, GPT-5.3-Codex: 41.0% |
| **Terminal-Bench** | CLI agent workflows | GPT-5.3-Codex: 77.3%, Claude Code: 72% |
| **Aider Polyglot** | Code editing across languages | Claude Opus 4.6: 85%, GPT-5.3: 80% |
| **LiveCodeBench** | Competitive programming, contamination-free | Top models: 40-60% |
| **Tau-Bench** | Multi-turn tool+user interaction | pass^8: ~25% |

**Key data sources:**
- swe-bench.com (official leaderboard)
- awesomeagents.ai (aggregated leaderboards)
- aider.chat (polyglot benchmark)
- tbench.ai (terminal benchmark)
- morphllm.com (comprehensive 2026 guide)

### Design: LLM-as-Judge Evaluation Pipeline

```
LLM-AS-JUDGE EVALUATION FLOW:

1. Fetch benchmark data (weekly via web research)
   → SWE-bench Verified leaderboard
   → Terminal-Bench leaderboard
   → Aider Polyglot leaderboard
   → Update ~/.config/model-scan/benchmarks.json

2. Compare against slot rankings
   → For each slot, list top-5 ranked models
   → Cross-reference with benchmark scores
   → Flag discrepancies (high-benchmark model ranked low, or vice versa)

3. Generate discrepancy report
   → "kimi-k2.6 ranked #2 in R1 but has 58.6% SWE-Pro"
   → "deepseek-v4-flash ranked #5 in R1 but has 79% SWE-Verified"
   → "allam-2-7b ranked #1 in R6 but has NO benchmark data"

4. Manual review + algorithm adjustment
   → User reviews discrepancy report
   → Adjusts weights or adds benchmark override
   → Updated in slot_definitions.yaml

5. Validate over time
   → Track which adjustments improve outcomes
   → Store in SQLite for historical analysis
```

### Implementation

```python
# New file: benchmarks.py
BENCHMARK_SOURCES = {
    "swe_verified": "https://swe-bench.com/leaderboard",
    "terminal": "https://tbench.ai/leaderboard",
    "aider": "https://aider.chat/docs/leaderboards",
}

def fetch_benchmarks() -> dict:
    """Fetch latest benchmark data from web."""
    # Use web research to get current scores
    # Update ~/.config/model-scan/benchmarks.json
    
def compare_rankings(dossiers: list[Dossier], benchmarks: dict) -> list[Discrepancy]:
    """Compare slot rankings against benchmark data."""
    discrepancies = []
    for slot_id, slot_def in slot_defs.items():
        ranked = sorted(
            [d for d in dossiers if d.slot_fitness.get(slot_id, 0) > 0],
            key=lambda d: -d.slot_fitness.get(slot_id, 0)
        )[:5]
        
        for d in ranked:
            benchmark_score = find_benchmark(d.model, benchmarks)
            if benchmark_score:
                expected_rank = calculate_expected_rank(benchmark_score, ranked)
                actual_rank = ranked.index(d) + 1
                if abs(expected_rank - actual_rank) > 2:
                    discrepancies.append(Discrepancy(
                        slot=slot_id,
                        model=d.model,
                        benchmark=benchmark_score,
                        expected_rank=expected_rank,
                        actual_rank=actual_rank,
                        fitness=d.slot_fitness[slot_id]
                    ))
    return discrepancies

# New CLI command
--evaluate-rankings    # Compare rankings against benchmarks, report discrepancies
--update-benchmarks   # Fetch latest benchmark data from web
```

### Benchmark Data File

**File:** `~/.config/model-scan/benchmarks.json`

```json
{
  "updated_at": "2026-05-13T00:00:00Z",
  "sources": ["swe-bench.com", "tbench.ai", "aider.chat"],
  "swe_verified": {
    "claude-opus-4.6": {"score": 80.9, "provider": "anthropic"},
    "gemini-3.1-pro": {"score": 80.6, "provider": "google"},
    "minimax-m2.5": {"score": 80.2, "provider": "opencode-go"},
    "kimi-k2.5": {"score": 76.8, "provider": "opencode-go"},
    "kimi-k2.6": {"score": 58.6, "provider": "opencode-go"},
    "deepseek-v4-flash": {"score": 79.0, "provider": "opencode-go"},
    "glm-5.1": {"score": 58.4, "provider": "opencode-go"},
    "qwen3.6-plus": {"score": 78.8, "provider": "opencode-go"},
    "qwen3.5-plus": {"score": 61.6, "provider": "opencode-go", "benchmark": "terminal"}
  },
  "terminal": {...},
  "aider": {...}
}
```

### Integration with `_estimate_intelligence()`

The benchmark data should **override heuristic estimates**:

```python
def _estimate_intelligence(d: Dossier) -> float | None:
    """
    Heuristic intelligence estimate.
    Priority: Benchmark data > model name heuristics > neutral 50.
    """
    # 1. Check for direct benchmark match
    benchmark = load_benchmarks()
    for bench_name, scores in benchmark.items():
        model_key = d.model.lower().replace("/", "-")
        if model_key in scores:
            return scores[model_key]["score"]  # Use verified benchmark
    
    # 2. Fall back to model name heuristics
    # ... (existing heuristic logic)
    
    # 3. Neutral fallback
    return None  # Don't guess — let slot_fitness use neutral 50
```

---

## TRACK D: Algorithm Refinement System

### Design: Historical Analysis + User-Initiated Tuning

**Philosophy:** Fully automated weight optimization is risky — small changes to fitness weights can have large, unpredictable effects across all slots. The system should **surface insights from historical data** and let the user make informed decisions.

```
ALGORITHM REFINEMENT FLOW:

1. Data Collection (automatic, ongoing)
   → Every scan stores: slot fitness scores, probe results, benchmark data
   → SQLite tracks: which models won which slots, how often
   → AA API data enriches: intelligence scores when available

2. Analytics Generation (user-initiated)
   → model-scan --analyze-history
   → Query SQLite for patterns:
     - Which models appear most often in top-3 for R1?
     - Which models consistently fail the min_ai gate?
     - How does speed correlate with reliability across providers?
     - What's the distribution of tps for models that "feel slow"?

3. Discrepancy Detection (automatic)
   → Compare actual usage patterns against expected rankings
   → Flag: "Moonshotai/kimi-k2.6 won R1 3x but has 58.6% SWE-Pro"
   → Flag: "deepseek-v4-flash never wins despite 79% SWE-Verified"

4. Weight Adjustment (user-initiated)
   → model-scan --tune-slot R1_primary --weight-intel 0.85 --weight-speed 0.10
   → model-scan --tune-slot R1_primary --min-tps 10 --min-ai 45
   → Changes written to ~/.config/model-scan/slot_definitions.yaml
   → Full scan re-run to validate

5. Validation (automatic)
   → After weight changes, re-run comparison against benchmarks
   → Report: "New weights would rank deepseek-v4-flash #2 (up from #5)"
   → User confirms or reverts
```

### SQLite Schema Enhancement

```sql
-- Add to models table
ALTER TABLE models ADD COLUMN benchmark_swe_verified REAL;
ALTER TABLE models ADD COLUMN benchmark_terminal REAL;
ALTER TABLE models ADD COLUMN benchmark_aider REAL;
ALTER TABLE models ADD COLUMN last_seen_at TEXT;

-- New table: slot_outcomes
CREATE TABLE slot_outcomes (
    outcome_id INTEGER PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(scan_id),
    slot_id TEXT,
    model_pk INTEGER REFERENCES models(model_pk),
    fitness_score REAL,
    was_incumbent BOOLEAN,
    replaced_incumbent BOOLEAN,
    probe_latency_s REAL,
    probe_tps REAL,
    benchmark_score_verified REAL,
    benchmark_score_terminal REAL
);

-- New table: weight_experiments
CREATE TABLE weight_experiments (
    experiment_id INTEGER PRIMARY KEY,
    slot_id TEXT,
    weight_intelligence REAL,
    weight_speed REAL,
    weight_reliability REAL,
    min_ai INTEGER,
    min_tps INTEGER,
    created_at TEXT,
    note TEXT
);
```

### Analytics CLI Commands

```bash
# Analyze historical patterns
model-scan --analyze-history --slot R1_primary
# Output:
#   Top models for R1_primary (last 10 scans):
#     1. qwen3-next-80b-a3b-thinking  (10/10 appearances)
#     2. allam-2-7b                   (7/10 appearances)
#     3. kimi-k2.6                    (3/10 appearances)
#   Average fitness score: 60.2
#   Benchmark correlation: 0.73 (good)

# Show discrepancy between rankings and benchmarks
model-scan --rank-vs-benchmark
# Output:
#   R1_primary ranking vs SWE-Verified:
#     Rank  Model                   Fitness  SWE-Verified  Discrepancy
#     1     qwen3-next-80b        60       ?             --
#     2     mimo-v2.5-pro        49       ?             --
#     3     minimax-m2.7          46       ?             --
#     -- BENCHMARK DATA (not in scan) --
#     1     deepseek-v4-flash     (no tps)  79.0%       ↓ missing
#     2     minimax-m2.5          (slow)   80.2%       ↓ slow
#     3     kimi-k2.6            (slow)   58.6%       ↓ slow

# Tune slot weights
model-scan --tune R1_primary \
    --intel 0.90 --speed 0.05 --rel 0.05 \
    --min-tps 5 --min-ai 45 \
    --note "Reduce speed further, allow slower OCGo models"

# Preview tune effect (before applying)
model-scan --preview-tune R1_primary \
    --intel 0.90 --speed 0.05 --rel 0.05

# Show weight experiment history
model-scan --weight-history R1_primary
```

### Task Description for User-Initiated Refinement

**File:** `~/.config/model-scan/REFINEMENT_TASK.md`

```markdown
# Algorithm Refinement Task

## Goal
Improve slot fitness weights so that the scan rankings accurately reflect:
1. Coding benchmark performance (SWE-bench, Terminal-bench)
2. Real-world agent effectiveness
3. Cost-efficiency for subscription providers

## When to Trigger
- After adding new benchmark data
- After noticing surprising rankings
- After provider model changes
- Monthly review recommended

## Steps

### 1. Fetch Latest Benchmarks
```bash
model-scan --update-benchmarks
```

### 2. Analyze Current Discrepancies
```bash
model-scan --rank-vs-benchmark
```
Look for:
- High-benchmark models ranked low
- Low-benchmark models ranked high
- Missing benchmark data for top-ranked models

### 3. Review Historical Patterns
```bash
model-scan --analyze-history --slot R1_primary
```
Ask:
- Is the same model always winning?
- Are there models that "should" win but never do?
- Is the speed/quality tradeoff working?

### 4. Tune Weights (if needed)
```bash
# Preview first
model-scan --preview-tune R1_primary --intel 0.90 --speed 0.05 --rel 0.05

# Apply if satisfied
model-scan --tune R1_primary --intel 0.90 --speed 0.05 --rel 0.05 --note "Reduced speed, increased intelligence"
```

### 5. Validate
```bash
# Run full scan with new weights
model-scan

# Check R1_primary candidates:
# - Are benchmark leaders now ranked higher?
# - Are there any surprising demotions?
```

## Weight Guidelines

### R1_primary (quality coding)
- **intel: 0.85-0.95** — SWE-bench Verified is the primary signal
- **speed: 0.05-0.15** — throughput matters less than quality
- **min_tps: 5-15** — allow OCGo models (7-14 tps) to qualify
- **min_ai: 40-50** — filter out C-tier models (allam-2-7b, llama-3.1-8b)

### R6_compression (high-volume, cost-sensitive)
- **budget: 0.50** — maximize requests per dollar
- **preferred: deepseek-v4-flash** — 158K requests/month, $0.005/M tokens
- **fallback: minimax-m2.7** — 17K requests/month

### R7_vision (multimodal)
- **intel: 0.40-0.50** — vision + intelligence both matter
- **preferred: kimi-k2.5** — multimodal at OCGo
- **fallback: llama-3.2-90b-vision** — NIM, good quality

## Benchmark Score Sources
- SWE-bench Verified: https://swe-bench.com/leaderboard
- Terminal-Bench: https://tbench.ai
- Aider Polyglot: https://aider.chat/docs/leaderboards
```

---

## TRACK E: Remaining Features & Implementation Status

### Implemented (v4)

| Feature | Status | Location |
|---------|--------|----------|
| Dynamic model discovery | ✅ | `list_models()` |
| Live HTTP probes | ✅ | `probe_one()` |
| Tool call detection | ✅ | `probe_tools()` |
| Slot fitness scoring | ✅ | `slot_fitness()` |
| Tier classification (S/A/B/C/—) | ✅ | `compute_tier()` |
| Hermes incumbent parsing | ✅ | `parse_hermes_slots()` |
| `--patch-hermes` | ✅ | CLI flag |
| AA API integration | ✅ | `fetch_aa_data()` |
| SQLite DB persistence | ✅ | `_db_save_run()` |
| Timestamp in footer | ✅ | `render_footer()` |
| Duplicate model detection | ✅ | `stripped_api` dedup |
| OpenCode Go provider | ✅ | `opencode-go` in PROVIDERS |
| `reasoning_content` support | ✅ | Empty response handling |
| `min_coding` removed | ✅ | Was broken (always 0) |
| `needs_tools=False` for R1 | ✅ | |
| Normalized TPS formula | ✅ | `tps/60*50` |
| `_estimate_intelligence()` in slot_fitness | ✅ | Benchmark heuristics |
| SQLite DB (scans, models, slot_fitness, incumbents) | ✅ | |
| `--clear-cache` includes DB | ✅ | |

### Partially Implemented

| Feature | Status | Gap |
|---------|--------|-----|
| OpenCode Go dual-endpoint probe | ⚠️ | MiniMax models use `/v1/messages`, not `/v1/chat/completions` |
| R12_delegation / R_mcp candidates | ⚠️ | Only 1 candidate each due to `needs_tools=True` |
| DeepSeek V4 Flash probe at OCGo | ⚠️ | Returns http_402 — budget issue |

### Not Implemented

| Feature | Priority | Complexity |
|---------|----------|------------|
| Weekly model update process | High | Medium |
| OpenCode Go budget scoring | High | Medium |
| LLM-as-judge benchmark evaluation | High | High |
| Benchmark data JSON file | High | Low |
| `--analyze-history` CLI | Medium | Medium |
| `--rank-vs-benchmark` CLI | Medium | Medium |
| `--tune` CLI for weight adjustment | Medium | Medium |
| Color output integration | Medium | Low |
| ETag support for provider APIs | Low | Medium |
| Per-slot benchmark override | Medium | Low |
| Model diff report (added/removed) | Medium | Low |
| `--refresh-providers` selective refresh | Low | Low |

---

## Color Output Integration

Currently the scan uses ANSI color codes via the `C` dataclass. Enhancement: **categorize by information type**:

```python
# Current: colors are applied somewhat arbitrarily
# Proposed: semantic coloring by information type

COLORS = {
    # Model tier (quality signal)
    "tier_S": "\033[38;5;208m",   # Orange — frontier quality
    "tier_A": "\033[38;5;75m",    # Green — strong
    "tier_B": "\033[38;5;117m",   # Cyan — capable
    "tier_C": "\033[38;5;145m",   # Gray — basic
    "tier_unknown": "\033[90m",   # Dark gray — unmeasured
    
    # Slot status
    "slot_winner": "\033[38;5;82m",    # Bright green — top pick
    "slot_candidate": "\033[38;5;147m", # Light purple — viable
    "slot_edge": "\033[38;5;221m",       # Yellow — borderline
    
    # Health indicators
    "healthy": "\033[38;5;82m",    # Green check
    "degraded": "\033[38;5;226m", # Yellow warning
    "failed": "\033[38;5;196m",   # Red cross
    
    # Benchmark data
    "benchmark_strong": "\033[38;5;82m",   # Green — >70% SWE
    "benchmark_moderate": "\033[38;5;75m", # Green — 50-70%
    "benchmark_weak": "\033[38;5;208m",   # Orange — <50%
    "benchmark_unknown": "\033[90m",       # Gray — no data
}
```

**Rendering changes:**

```python
# In render_appendix(), color by benchmark when available:
if model.benchmark_swe_verified:
    tier_color = COLORS["benchmark_strong"] if model.benchmark_swe_verified > 70 \
           else COLORS["benchmark_moderate"] if model.benchmark_swe_verified > 50 \
           else COLORS["benchmark_weak"]
else:
    tier_color = COLORS[f"tier_{model.tier}"]

print(f"{tier_color}{model.model:<40}{RESET} {model.tier} ...")

# In render_per_slot_view(), color fitness delta:
if delta > 10:
    delta_color = COLORS["slot_winner"]
elif delta > 0:
    delta_color = COLORS["slot_candidate"]
else:
    delta_color = COLORS["tier_C"]
```

---

## Implementation Priority Order

### Phase 1: Quick Wins (1-2 hours each)

1. **Color output by benchmark** — Add benchmark data coloring to appendix and per-slot views
2. **OpenCode Go budget scoring** — Add `budget_score()` function, integrate into R6/R8 slots
3. **Benchmark JSON file** — Create `benchmarks.json` with verified SWE/Terminal scores

### Phase 2: Core Features (1-2 days each)

4. **Weekly update integration** — Hybrid cache + diff system in `run_scan()`
5. **`--analyze-history`** — Query SQLite for historical patterns
6. **`--rank-vs-benchmark`** — Discrepancy report between rankings and benchmarks
7. **Fix OCGo dual-endpoint probe** — Add `/v1/messages` support for MiniMax models

### Phase 3: Advanced (1 week)

8. **`--tune` CLI** — Weight adjustment with preview and validation
9. **ETag support** — Avoid re-fetching unchanged model lists
10. **Model diff report** — Track additions/removals over time
11. **OpenCode Go fixed list validation** — Flag if curated models disappear

---

## Configuration Files Reference

### Current Files

| File | Purpose |
|------|---------|
| `~/.config/model-scan/slot_definitions.yaml` | Slot weights, thresholds, preferred archs |
| `~/.config/model-scan/bad_models.json` | Permanently skipped models |
| `~/.config/model-scan/aa_cache.json` | Artificial Analyses API cache |
| `~/.config/model-scan/results.json` | Scan history (last 30 runs) |
| `~/.config/model-scan/model_scan.db` | SQLite DB (scans, models, slot_fitness, incumbents) |
| `~/.config/model-scan/cache.json` | Provider model list cache |

### Proposed Files

| File | Purpose |
|------|---------|
| `~/.config/model-scan/scan_config.yaml` | Provider strategies, refresh intervals |
| `~/.config/model-scan/benchmarks.json` | Verified benchmark scores per model |
| `~/.config/model-scan/model_list_cache.json` | Per-provider model lists with ETags |
| `~/.config/model-scan/REFINEMENT_TASK.md` | User guide for algorithm tuning |

---

## Summary: What's Implemented, What Isn't

### Implemented ✅
- Dynamic model discovery from provider APIs (no hardcoded lists)
- Live HTTP probing with latency/throughput measurement
- Tool call capability detection
- Slot fitness with intelligence/speed/reliability weights
- Tier classification (S/A/B/C)
- Hermes incumbent parsing + `--patch-hermes`
- AA API integration with caching
- SQLite persistence of scan history
- OpenCode Go provider (subscription-based, curated models)
- `_estimate_intelligence()` with heuristic + benchmark data
- Normalized TPS formula (60 tps = reference point)
- Benchmark-based min_ai gates

### Not Implemented ❌
- Weekly update process with model diff
- OpenCode Go budget-aware scoring
- LLM-as-judge benchmark validation
- `--analyze-history` / `--rank-vs-benchmark` / `--tune`
- Benchmark JSON file with verified scores
- Color output by benchmark tier
- Dual-endpoint probe for MiniMax at OCGo
- ETag support for provider APIs
