# MODEL-SCAN OPTIMIZATION PLAN v2
# Comprehensive Methodology for Iterative Grading Algorithm Improvement
# Aligned with Pi Agent Session User Intent Analysis
# Generated: 2026-05-13

## 1. EXECUTIVE SUMMARY

This plan defines a two-phase system for deriving optimal models for Hermes task slots,
grounded in the actual user intent extracted from 36 Pi agent session prompts and 33
historical requirements.

**cheta's Primary Purpose for model-scan:** Find the optimal model for every slot in
`~/.hermes/config.yaml` and `~/code/claude-code-proxy/.env`, plus the best fallback
chain for each. Generate config patches with reasoning. Everything else serves this.

**Phase 1 — LLM-Enhanced System:** An LLM reasoning over model-scan output + multi-source
analytics to produce "gold standard" model rankings AND config.yaml/.env patches per
Hermes task slot, with full reasoning traces.

**Phase 2 — Automated System:** A programmatic process that replicates Phase 1's outputs
using only algorithmic scoring, iteratively adjusting weights and variables to converge
on Phase 1's findings. The Phase 2→Phase 1 convergence IS the Karpathy loop applied to
model selection.

**Editable surface:** tiers.yaml + slot_definitions.yaml (weights, thresholds, scoring params)
**Metric:** Config patch convergence (does the automated system suggest the same model replacements as the LLM?)
**Time budget:** ~60 seconds per experiment cycle

## 2. DATA SOURCES

### Already Integrated (in model-scan v4)
| Source | Data Provided | API |
|--------|--------------|-----|
| Live probes | Latency, TPS, reliability, tool-calling, empty-response detection | Direct API calls |
| Artificial Analysis | AI index, coding index, math index, agentic index, pricing, TPS, TTFT | artificialanalysis.ai/api/v2/data/llms/models |
| models.dev | Context length, pricing, vision, reasoning capabilities | models.dev/api.json |
| OpenRouter | Model list + pricing (free tier only per user intent) | openrouter.ai/api/v1/models |
| Groq | Model list + pricing (all models) | api.groq.com/openai/v1/models |
| NVIDIA NIM | Model list + pricing (all models) | integrate.api.nvidia.com/v1/models |
| OpenCode Go | Model list + pricing (best bang for buck, no American models per user intent) | opencode.ai/zen/go/v1/models |
| Cerebras | Model list + pricing (all models) | api.cerebras.ai/v1/models |
| Ollama Cloud | Model list (filtered to specific families) | ollama.com/v1/models |
| Venice | Catalog-only (no probe per user intent) | api.venice.ai/api/v1/models |

### To Be Integrated (New — per user intent for multi-source audit)
| Source | Data Provided | Access Method | Priority |
|--------|--------------|---------------|----------|
| **Terminal-Bench** | Agentic terminal task scores (0-100%) | Web scrape or API at tbench.ai | HIGH |
| **SWE-Bench Verified** | Software engineering task scores | swebench.com JSON endpoint | HIGH |
| **LiveBench** | Contamination-resistant evaluation | livebench.ai | MEDIUM |
| **LMSYS Chatbot Arena** | Human preference ELO scores | llm-stats.com or lmsys.org API | MEDIUM |
| **GPQA** | Graduate-level QA accuracy | Already in AA API | DONE |
| **Social media signals** | Reddit/X mentions, community sentiment | web_search | LOW |

### Hermes Task Slots (from config.yaml — cheta's primary optimization targets)
| Slot ID | Label | Key Requirements (from user intent) |
|---------|-------|-----------------|
| R1_primary | Primary agent | Smart, tool-calling, fast, S-tier MoE (per req R1) |
| R2-R11_fallback | Fallback chain | Decreasing intelligence, increasing speed |
| R6_compression | Context compression | Speed > intelligence, 30+ tps |
| R7_vision | Multi-modal vision | MUST have vision capability |
| R8_web_extract | Web content extraction | Quality > speed, 40+ min AI |
| R9_session_search | Session search/replay | Balanced quality + speed |
| R10_approval | Approval gate | Decent intelligence, 20+ tps |
| R11_flush_memories | Memory flush | Balanced, 20+ tps |
| R12_delegation | Sub-agent delegation | High intelligence + tool-calling |
| R_mcp | MCP orchestration | High intelligence + tools + 128K+ ctx |
| R_skills_hub | Skills/hub operations | Speed focused, 25+ min AI |

### Proxy Tiers (from claude-code-proxy .env — also optimization targets)
| Tier | Label | Purpose |
|------|-------|---------|
| BIG | Primary proxy model | Main Claude Code model |
| MIDDLE | Mid-tier proxy | Balanced quality/speed |
| SMALL | Lightweight proxy | Fast, cheap |
| CASCADE | Fallback chain | Ordered by preference |
| TOOLCALL | Tool-calling specialist | Best function calling |

## 3. PHASE 1 — LLM-ENHANCED GOLD STANDARD

### 3.1 LLM Ranking + Config Patch Generator

**Input:** Full model-scan output (all dossiers with all metrics) + supplemental
benchmark data + current config.yaml + current proxy .env.

**Process:**
1. For each Hermes task slot AND proxy tier, feed the LLM:
   - The slot definition (needs_tools, needs_vision, min_ai, min_tps, etc.)
   - All accessible models with their complete metric profiles
   - Supplemental benchmark data (Terminal-Bench, SWE-Bench, Arena ELO)
   - Current incumbent model and its performance history
   - Historical failure data from bad_models.json
   - **User's stated intent** for each slot (e.g., "primary: smart, tool-calling, fast, S-tier MoE")

2. LLM produces:
   - Ranked list of top-5 models per slot/tier
   - **Config patch** — specific model replacements for config.yaml and .env
   - Reasoning trace explaining each recommendation
   - Confidence score (0-100%)
   - Key tradeoff notes
   - **Audit assessment** — where the current scan scoring got it right vs. wrong

**Output Format:**
```json
{
  "slot_id": "R1_primary",
  "generated_at": "2026-05-13T...",
  "current_incumbent": "openrouter/owl-alpha",
  "rankings": [
    {"rank": 1, "model": "inclusionai/ling-2.6-1t:free", "confidence": 95,
     "reasoning": "AA=92, BFCL #1 tool calling, 26.6 tps, S-tier MoE. Matches user intent: smart, tool-calling, fast, S-tier MoE."},
    {"rank": 2, "model": "deepseek-v4-pro", "confidence": 88, ...}
  ],
  "config_patch": {
    "file": "~/.hermes/config.yaml",
    "section": "model.default",
    "current": "openrouter/owl-alpha",
    "recommended": "inclusionai/ling-2.6-1t:free",
    "rationale": "ling-2.6-flash:free is S-tier (AA=92), BFCL #1, matches all stated requirements for primary slot"
  },
  "audit": {
    "scan_got_right": ["Correctly identified ling-2.6 as top candidate"],
    "scan_got_wrong": ["Over-weighted owl-alpha due to incumbent bias", "Under-weighted agentic score"],
    "missing_signals": ["Did not consider BFCL ranking"]
  },
  "traces": {
    "key_factors": ["AA intelligence > 65", "tool-calling verified", "tps > 20", "MoE architecture"],
    "tradeoffs_considered": ["speed vs quality for primary role"],
    "disqualified": ["model-x: no tools", "model-y: empty_response"]
  }
}
```

### 3.2 Gold Standard Dataset

Build a persistent dataset of LLM-enhanced rankings + config patches, refreshed periodically:
- Store in `~/.config/model-scan/gold_standard/YYYY-MM-DD.json`
- Include the model-scan run ID that was the input
- Version with timestamps for tracking drift
- **Include the config patch** (not just rankings) as the convergence target

## 4. PHASE 2 — AUTOMATED CONVERGENCE SYSTEM

### 4.1 Editable Surface (What Gets Modified)

**File: `~/.config/model-scan/tiers.yaml`**
```yaml
anchors:
  S: "GLM-5.1 / DeepSeek-V4-Pro intelligence level"
  A: "MiniMax-M2.7 intelligence level"
thresholds:
  S: 65    # <-- ADJUSTABLE: AA intelligence threshold for S-tier
  A: 55    # <-- ADJUSTABLE
  B: 40    # <-- ADJUSTABLE
  C: 15    # <-- ADJUSTABLE
composite_weights:
  ai_intelligence: 0.45    # <-- ADJUSTABLE: weight of AA intelligence in composite
  ai_coding:       0.20    # <-- ADJUSTABLE: weight of AA coding index
  ai_math:         0.10    # <-- ADJUSTABLE: weight of AA math index (NEW)
  ai_agentic:      0.10    # <-- ADJUSTABLE: weight of AA agentic index (NEW)
  latency_inv:     0.10    # <-- ADJUSTABLE: weight of latency
  reliability:     0.05    # <-- ADJUSTABLE: weight of reliability
```

**File: `~/.config/model-scan/slot_definitions.yaml`**
```yaml
R1_primary:
  label: primary
  needs_tools: True         # <-- User intent: primary must be tool-calling
  needs_vision: False
  min_ai: 55                # <-- ADJUSTABLE: S-tier threshold for primary
  min_tps: 15               # <-- ADJUSTABLE: "fast" per user intent
  max_latency_s: 3.0        # <-- ADJUSTABLE
  min_ctx_k: 128            # <-- ADJUSTABLE: user wants 128K+ for primary
  preferred_arch: ["MoE", "MoE-reasoning"]  # <-- User intent: S-tier MoE
  weight_intelligence: 0.50  # <-- ADJUSTABLE
  weight_speed: 0.20         # <-- ADJUSTABLE
  weight_reliability: 0.15   # <-- ADJUSTABLE
  weight_tool_calling: 0.15  # <-- ADJUSTABLE (NEW: BFCL score weight)

R6_compression:
  label: compression
  needs_tools: False
  needs_vision: False
  min_ai: 25
  min_tps: 30               # <-- User intent: "speed is king" for compression
  max_latency_s: 2.0
  min_ctx_k: 64
  weight_intelligence: 0.15
  weight_speed: 0.60         # <-- ADJUSTABLE: throughput is king
  weight_reliability: 0.25
```

**New File: `~/.config/model-scan/benchmark_overrides.yaml`**
```yaml
# Supplemental benchmark scores not in AA — for independent audit
manual_scores:
  "inclusionai/ling-2.6-1t:free":
    bfcl_rank: 1             # BFCL #1 for tool calling
    terminal_bench: null
    swe_verified: null
  "deepseek-v4-pro":
    terminal_bench: 55.1
    swe_verified: 79.0
  "glm-5.1":
    terminal_bench: 58.4
    swe_verified: null
```

### 4.2 Convergence Metric — Config Patch Accuracy

**Primary metric: Config Patch Match Rate (CPMR)**

The gold standard is NOT just rankings — it's the CONFIG PATCH. The automated system
must produce the same model recommendations for each slot/tier as the LLM.

```
CPMR = (number of slots where auto_recommended_model == llm_recommended_model) / total_slots

overall_convergence = CPMR * 100  (percentage of matching config recommendations)
```

**Secondary metrics:**
- Rank Distance: For slots where top-1 doesn't match, how far off is the ranking?
- Patch Quality Score: Weighted match (top-1 match = 1.0, top-2 match = 0.7, top-3 match = 0.3)
- Audit Accuracy: Does the automated system correctly identify where the scan got it right/wrong?

### 4.3 Weight Adjustment Strategy

**Approach 1: Per-Slot Grid Search (Phase 2a)**
- For each slot independently, sweep each weight parameter ±0.05
- Keep the adjustment that most improves that slot's CPMR
- Move to next slot after local optimum found
- Repeat full pass until no single-parameter adjustment improves overall CPMR

**Approach 2: Global Evolutionary Search (Phase 2b)**
- Population of weight configurations (tiers.yaml + all slot definitions)
- Fitness = overall CPMR
- Crossover: blend weights from two high-fitness configs
- Mutate: randomly perturb one weight by ±step
- Selection: top-N by CPMR
- Run for K generations or until plateau

**Approach 3: Gradient Approximation (Phase 2c)**
- After Phase 2b identifies promising regions
- Approximate ∂CPMR/∂weight_i for each parameter
- Take gradient steps with adaptive step size
- Reduce step size when oscillation detected

### 4.4 Experiment Loop Architecture

```
┌─────────────────────────────────────────────────────────┐
│              EXPERIMENT CONTROLLER                       │
│                                                          │
│  1. LOAD gold_standard (LLM config patches + rankings)   │
│  2. LOAD current weights from tiers.yaml + slot_defs     │
│  3. PROPOSE weight adjustment                            │
│     (strategy: per-slot grid / global evolutionary)      │
│  4. APPLY weights (write temp config)                    │
│  5. RUN model-scan (subprocess, ~60s)                    │
│  6. PARSE scan output (JSON)                             │
│  7. GENERATE config patches from scan output             │
│     (algorithmic: top-ranked model per slot → patch)     │
│  8. COMPARE patches to gold standard                     │
│     (CPMR + rank distance + audit accuracy)              │
│  9. IF CPMR improved:                                    │
│       COMMIT weights to tiers.yaml + slot_defs           │
│       LOG experiment (weight_delta, CPMR improvement)    │
│     ELSE:                                                │
│       REVERT weights                                     │
│       LOG experiment (weight_delta, regression)          │
│  10. UPDATE search state                                 │
│  11. GOTO 3 until plateau or budget exhausted            │
└─────────────────────────────────────────────────────────┘
```

### 4.5 Persistence and Tracking

Extend the existing SQLite schema:

```sql
CREATE TABLE IF NOT EXISTS optimization_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL,
    strategy        TEXT,           -- 'grid', 'evolutionary', 'gradient'
    initial_cpmr    REAL,           -- Config Patch Match Rate
    best_cpmr       REAL,
    experiments     INTEGER,
    duration_s      REAL,
    final_config_snap TEXT          -- YAML snapshot of best config
);

CREATE TABLE IF NOT EXISTS experiments (
    exp_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER,
    exp_number      INTEGER,
    config_snap     TEXT,           -- YAML snapshot of weights used
    cpmr            REAL,           -- Config Patch Match Rate
    patch_quality   REAL,           -- Weighted match score
    vs_baseline     REAL,           -- improvement over starting point
    is_accepted     INTEGER,        -- 1=kept, 0=reverted
    run_duration_s  REAL,
    FOREIGN KEY (run_id) REFERENCES optimization_runs(run_id)
);

CREATE TABLE IF NOT EXISTS slot_convergence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER,
    exp_id          INTEGER,
    slot_id         TEXT,
    auto_top1       TEXT,           -- model auto-selected
    llm_top1        TEXT,           -- model LLM selected
    match           INTEGER,        -- 1=same, 0=different
    rank_distance   INTEGER,        -- how far off
    FOREIGN KEY (run_id) REFERENCES optimization_runs(run_id),
    FOREIGN KEY (exp_id) REFERENCES experiments(exp_id)
);
```

## 5. IMPLEMENTATION WORK PLAN

### Step 1: Gold Standard Generation (Week 1)
- [ ] Build `gold_standard.py` — runs model-scan --json, feeds to LLM with user intent context
- [ ] LLM generates per-slot rankings + config patches + audit assessment
- [ ] Store in `~/.config/model-scan/gold_standard/YYYY-MM-DD.json`
- [ ] Validate: manually inspect 3-5 slot recommendations against known good choices
- [ ] Key: Include user intent ("primary: smart, tool-calling, fast, S-tier MoE") in LLM prompt

### Step 2: Convergence Metric (Week 1-2)
- [ ] Implement `convergence.py` with CPMR, patch quality score, rank distance
- [ ] Implement per-slot match tracking
- [ ] Unit test against known config patch pairs
- [ ] Verify: identical patches → CPMR=100%, completely different → CPMR=0%

### Step 3: Basic Automated Loop (Week 2-3)
- [ ] Build `optimize.py` experiment controller
- [ ] Implement per-slot grid search strategy
- [ ] Implement config apply/revert with git-backed versioning
- [ ] Run first optimization sweep across all slots
- [ ] Compare CPMR before/after

### Step 4: Evolutionary Search (Week 3-4)
- [ ] Implement population-based evolutionary strategy
- [ ] Add crossover and mutation operators for multi-slot weight vectors
- [ ] Run evolutionary optimization, compare to grid search results
- [ ] Tune population size, mutation rate, selection pressure

### Step 5: Gradient Approximation (Week 4-5)
- [ ] Implement numerical gradient estimation for CPMR
- [ ] Add momentum and adaptive step size
- [ ] Run gradient-based optimization from evolutionary best
- [ ] Compare convergence speed across all three strategies

### Step 6: Supplemental Benchmark Integration (Week 5-6)
- [ ] Add Terminal-Bench scoring (web scrape or API)
- [ ] Add SWE-Bench Verified scoring
- [ ] Add BFCL (Big Code Function Calling Leaderboard) scores
- [ ] Add Arena ELO scores
- [ ] Update `_estimate_intelligence()` with supplemental scores
- [ ] Regenerate gold standard with richer data
- [ ] Re-run optimization to measure improvement from additional signals

### Step 7: Independent Audit System (Week 6-7)
- [ ] Build `audit.py` — compares scan recommendations against external data
- [ ] Track where scan got best choices right vs. wrong over time
- [ ] Feed audit results back into weight adjustment (penalize weights that produce known-bad recommendations)
- [ ] Generate periodic audit reports

### Step 8: Iterative Refinement (Ongoing)
- [ ] Track convergence trajectories across scan runs
- [ ] Identify which slots converge fastest/slowest
- [ ] Adjust per-slot weight ranges based on convergence patterns
- [ ] Run optimization loop periodically (cron job) to adapt to model landscape changes
- [ ] Weekly gold standard refresh (LLM re-evaluates with latest scan data)

## 6. SAFETY CONSTRAINTS

1. **One editable surface:** Only `tiers.yaml` and `slot_definitions.yaml`. Cannot touch probing, data fetching, or rendering code.

2. **Revert capability:** Every config change is versioned (git). Any change that degrades CPMR by more than 5% is auto-reverted.

3. **Human review gate:** Configurations achieving CPMR > 85% are flagged for human review before being committed to production. The system proposes; the human disposes. (Per user intent: "don't change config.json yet until I approve")

4. **Bounded parameter space:** All weights must sum to 1.0 per slot. Thresholds must maintain S > A > B > C ordering. No weight can exceed 0.9 or go below 0.01.

5. **Metric gaming detection:** If optimization improves overall CPMR but degrades any individual critical slot (R1_primary, R6_compression, R7_vision) by more than 10%, the change is flagged and held for review.

6. **Log everything:** Every experiment is logged with full config snapshot, CPMR score, per-slot match data, and acceptance decision.

7. **No automatic config file changes:** The system generates patches but NEVER writes to config.yaml or proxy .env without explicit user approval. (Per user intent: "we are working on the script, not running the script")

## 7. CONVERGENCE TARGETS

| Milestone | Target CPMR | Definition |
|-----------|------------|-----------|
| Initial baseline | ~30% | Current algorithmic scoring vs LLM gold standard |
| After grid search | ~50% | Single-parameter optimizations found |
| After evolutionary | ~65% | Multi-parameter interactions captured |
| After gradient | ~75% | Fine-tuned in promising region |
| After supplemental benchmarks | ~85% | Richer signal enables better discrimination |
| After audit feedback loop | ~90%+ | Penalizing known-bad recommendations |
| Plateau detection | — | No CPMR improvement > 2% over 50 consecutive experiments |

## 8. ALIGNMENT WITH USER INTENT

This plan directly addresses the following user requirements from Pi sessions:

| User Requirement | How This Plan Addresses It |
|-----------------|---------------------------|
| "Find optimal models for every Hermes/proxy slot" | Phase 1 LLM generates per-slot recommendations; Phase 2 converges on same |
| "Generate config patches with reasoning" | Gold standard includes config_patch with rationale; automated system produces same format |
| "Audit suggestions independently (AA, social media)" | Step 7 audit system + supplemental benchmark integration |
| "Track where scan got it right vs. wrong" | Audit assessment in gold standard; slot_convergence table in SQLite |
| "Don't change config files without approval" | Safety constraint #7 — patches are proposed, never auto-applied |
| "Dynamic model discovery (not hardcoded)" | Already in model-scan v4; optimization layer inherits this |
| "Bad model tracking with failure types" | Already in model-scan v4; optimization uses bad_models.json |
| "Primary: smart, tool-calling, fast, S-tier MoE" | R1_primary slot definition includes all four criteria with adjustable weights |
| "OpenRouter free only, OCGo best bang for buck" | Already in model-scan v4 provider strategy; optimization inherits |
| "Unified output, not fragmented" | Convergence metric treats all slots as one unified optimization problem |
| "LLM-assisted config suggestion" | Phase 1 IS the LLM-assisted suggestion system |
| "Karpathy loop for weight adjustment" | Phase 2 IS the Karpathy loop — edit weights, run scan, measure CPMR, keep/revert |

## 9. DELIVERABLES

1. **Gold standard rankings + config patches** — LLM-enhanced per-slot model recommendations with reasoning traces and audit assessments
2. **`convergence.py`** — Config Patch Match Rate computation module
3. **`optimize.py`** — Experiment controller with grid/evolutionary/gradient strategies
4. **`audit.py`** — Independent recommendation audit against external data
5. **Optimization experiment logs** — Full SQLite history of all experiments with per-slot convergence tracking
6. **Convergence report** — Analysis of which strategies worked, which weights matter most, convergence trajectory
7. **Updated tiers.yaml + slot_definitions.yaml** — Optimized configurations (human-reviewed before application)
8. **Periodic cron job** — Automated re-optimization as model landscape changes

## 10. RELATIONSHIP TO EXISTING MODEL-SCAN

This plan does NOT edit model-scan itself. It builds an optimization layer ON TOP:

```
                    ┌──────────────────────┐
                    │  LLM Reasoning       │  (Phase 1)
                    │  Gold Standard       │
                    │  + Config Patches    │
                    │  + Audit Assessment  │
                    └──────────┬───────────┘
                               │ reference patches + rankings
                               ▼
┌──────────┐    ┌──────────────────────────┐    ┌──────────────────┐
│  AA API  │───▶│    EXPERIMENT            │───▶│  CPMR score      │
│  models  │───▶│    CONTROLLER            │───▶│  (Config Patch   │
│  .dev    │    │                          │    │   Match Rate)    │
│  (etc)   │    │  modifies weights in     │    └──────┬───────────┘
└──────────┘    │  tiers.yaml + slot_defs  │           │
                │  runs model-scan          │           ▼
                │  generates patches        │    ┌──────────────────┐
                │  measures CPMR            │    │  Best config     │
                └──────────┬───────────────┘    │  tiers.yaml      │
                           │                     │  slot_defs       │
                           │ snapshot            └──────────────────┘
                           └──────────────────▶  (human-reviewed)
```

model-scan remains the DATA COLLECTION engine (probes, AA data, models.dev data, scoring).
The optimization layer is a SEPARATE system that consumes model-scan's output and adjusts its config.
