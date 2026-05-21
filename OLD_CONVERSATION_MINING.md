# Old Conversation Mining — Applicable Ideas for model-scan

**Source:** Prior Gemini conversation about agentic framework benchmarking
**Date of original:** ~Sept 2025
**Goal:** Extract novel algorithms, metrics, analysis methods, and visualization approaches applicable to model-scan

---

## ✅ Already Implemented (in some form)

| Idea | How we do it | Could be better? |
|------|-------------|-------------------|
| 1-100 scoring system | Composite score (0-100) | Yes — make it clearer which sub-scores contribute |
| Multi-axis comparison | 4-axis radar (IS/SS/AS/CS) | Always room for more axes |
| Iterative refinement | CPMR + optimization loop | Yes — see below |
| Weekly data freshness | refine.py + heartbeat.yaml | Change-triggered would be smarter |
| Model-independent scoring | Live probes across 10 providers | Core design, keep emphasizing |
| Pareto frontier analysis | Intel vs TPS frontier | Could add more dimension pairs |
| Filtered table views | Sortable/filterable model list | Yes — see Preset Filters below |
| Gold standard comparison | Gold standard generator + CPMR | Core feature |

---

## 🔥 High-Value Ideas NOT Yet Implemented

### 1. Usage Popularity Metric (Community Trust Signal)

**The idea:** The old conversation mentions getting actual usage data from OpenRouter — which models are being used most, by token volume, ranked by software client. This is a real-world adoption signal we don't capture at all.

**What it adds:** A model could score high on benchmarks but have zero real-world adoption. Usage data catches vaporware and confirms practical utility.

**How to get it:**
- OpenRouter exposes `GET /api/v1/usage` or per-model pages with token usage stats
- Together.ai and other providers have similar data
- Could be a simple `popularity_score: float` (0-100 based on percentile of total tokens served)

**Implementation:**
```python
# In analysis/engine.py, add a popularity fetcher
def fetch_usage_popularity() -> dict[str, float]:
    """Returns {model_id: percentile_score} for models with real usage data."""
    # Fetch from OpenRouter usage stats
    # Normalize to 0-100 percentile
    return scores
```

**Where it fits:** New derived metric in the scoring engine. Blended into composite or shown separately as "Community Trust."

### 2. Config Change Tracking (Version History for Our Own Config)

**The idea:** Snapshot `slot_definitions.yaml`, `scan_config.yaml`, `tiers.yaml`, `free_model_whitelist.json` daily. Track changes over time. Link changes to CPMR score changes.

**What it adds:** When a weight change causes CPMR to drop, we can trace it back to the exact config change. Enables the "algorithm history page" the user requested.

**Implementation:**
```bash
# Daily cron: snapshot configs with timestamps
~/.config/model-scan/snapshots/2026-05-20/slot_definitions.yaml
~/.config/model-scan/snapshots/2026-05-20/scan_config.yaml
~/.config/model-scan/snapshots/2026-05-20/free_model_whitelist.json
```

```python
# Analysis: diff snapshots, link to CPMR changes
def analyze_config_drift():
    """Compare latest two snapshots, report changes, link to CPMR delta."""
```

### 3. Change-Triggered Re-Evaluation (Smarter Than Cron)

**The idea:** Instead of running full analysis on a fixed schedule, detect meaningful changes to configs, benchmarks, or model lists and trigger targeted re-evaluation only where needed.

**What it adds:** Saves API costs and compute. Full scan only when something actually changed.

**Implementation:**
```python
# Detect what changed
deltas = diff_configs(snapshot_yesterday, snapshot_today)
if deltas.get("free_model_whitelist"):
    trigger("--free-mode --refresh-free")  # targeted
if deltas.get("benchmarks"):
    trigger("--update-benchmarks")         # targeted
if deltas.get("slot_weights"):
    trigger("--optimize --slot R1")        # targeted only R1
```

### 4. Preset Filter Views (UX Enhancement for Web UI)

**The idea:** Radio buttons or tab-style presets that combine multiple filters into one click. The old conversation specifically called out radio buttons for this.

**What it adds:** One-click switching between common analysis views instead of manually setting 3-4 dropdowns.

**Presets:**
- **"All Models"** — no filters
- **"Free Only"** — `--free-mode` equivalent, shows only whitelisted models
- **"Cost-Basis"** — shows all models, cost-basis slots highlighted
- **"Best Value"** — sorted by cost-adjusted intelligence (CAI)
- **"Agent Ready"** — has tools + reasoning + pinchbench > 70%
- **"DeepSeek Fleet"** — all deepseek-v4-flash routes across providers
- **"S-Tier Only"** — composite > 80

### 5. Source Provenance Tagging in UI

**The idea:** The old conversation emphasized separating model-independent scores from benchmark-dependent ones. Make it visually obvious which data comes from where.

**What it adds:** Trust calibration — users know which scores are from live probes vs. third-party benchmarks.

**Implementation in UI:**
```
Composite: 76.9
  ├── Intelligence: 82.3   🔬 Live probe
  ├── Speed: 33.8          🔬 Live probe  
  ├── Agentic: 94.1        📊 AA + PinchBench
  └── Coding: 91.8         📊 AA + Benchmarks
```

---

## ⚠️ Ideas NOT Worth Implementing

| Idea | Why not |
|------|---------|
| Full agentic framework comparison table | Not what model-scan does — we compare LLM models, not agent frameworks |
| MCP failure rate tracking | Requires user-reported failure data we don't have |
| Hosting analysis (Cloudflare vs Vercel) | Irrelevant to model scanning |
| Verbal activation / TTS / STT tracking | Out of scope |
| Automatic new-file discovery for tracking list | Over-engineering — our tracked files are manually curated |
| Second-by-second benchmark obsolescence | Overkill — benchmarks don't change that fast |

---

## Implementation Priority

| # | Feature | Effort | Impact | Why now? |
|---|---------|--------|--------|----------|
| 1 | Usage popularity metric | 2h | Medium | New signal, easy API call |
| 2 | Config change snapshots | 1h | Medium | Enables history page + drift detection |
| 3 | Preset filter views (web) | 2h | High | Big UX win, low code |
| 4 | Change-triggered re-eval | 4h | High | Reduces API costs |
| 5 | Source provenance tags | 3h | Medium | Trust/transparency |
