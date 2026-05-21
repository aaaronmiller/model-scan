# model-scan v5: Requirements & User Stories
## Requirements Document — Web UX + Terminal Enhancement

---

## 1. Executive Summary

model-scan v4 is a powerful model evaluation, slot-ranking, and config-patching tool. It currently runs as a terminal-only CLI with ANSI-colored output, SQLite analytics, and YAML config generation. This document specifies the requirements for **model-scan v5**, which adds:

1. **Web UI** (Svelte 5 + shadcn-svelte) for richer visualization, radar/spider charts, historical trend analysis, and config patching
2. **Terminal TUI enhancement** (Textual/Rich) for interactive browsing, model comparison, and real-time scan monitoring
3. **Model routing layer** with cascade fallback, circuit breakers, and task-specific routing for Hermes/proxy integration
4. **Multi-axis scoring engine** (IQ, Speed, Agentic, Coding) with cross-influence modifiers
5. **AA API + models.dev live integration** for up-to-the-minute benchmark data
6. **Historical analytics dashboard** from the existing SQLite database

**Primary goal:** Enable users to rapidly identify, select, and deploy the optimal model for each of ~12 task-specific roles in `~/.hermes/config.yaml`, with appropriate fallback chains.

---

## 2. User Personas

### Persona A: Power User / Developer (cheta)
- Runs model-scan weekly to get fresh model rankings
- Edits `~/.hermes/config.yaml` and `claude-code-proxy/.env` manually
- Wants terminal-first output, fast iteration
- Uses `--analyze-history`, `--rank-vs-benchmark`, `--tune`
- **Pain point:** Terminal tables are dense; hard to compare models across multiple axes visually

### Persona B: Vibe Coder / Casual User
- Wants to run model-scan and get clear recommendations
- Doesn't want to read complex tables
- Needs "which model should I use for X?" answered immediately
- Prefers a web dashboard or guided TUI

### Persona C: DevOps / Platform Engineer
- Wants to integrate model-scan into CI/CD pipelines
- Needs JSON output, API access, and automated config patching
- Wants circuit breaker health data and provider status monitoring
- Needs to evaluate model routing decisions across providers

---

## 3. User Stories

### 3.1 Web UI

**US-W01:** As a user, I want to see a radar/spider chart comparing 3-5 selected models across IQ, Speed, Agentic, and Coding axes so I can visually compare strengths and weaknesses.

**US-W02:** As a user, I want to see a historical trend chart showing how fitness scores changed over the last N scans so I can track model degradation/improvement.

**US-W03:** As a user, I want a per-slot breakdown showing the top 10 candidates ranked by fitness with their contributing scores broken down so I can understand *why* a model won a slot.

**US-W04:** As a user, I want to view the full scan results in a sortable/filterable data table with all columns (tier, model, provider, TPS, latency, tools, vision, price, benchmark scores, slot matches).

**US-W05:** As a user, I want to see provider status indicators (green/yellow/red) for each API provider so I know which are available.

**US-W06:** As a user, I want one-click "copy to clipboard" for model IDs and "apply to config" buttons so I can quickly update my configuration files.

**US-W07:** As a user, I want to export a PDF/PNG of a comparison chart for documentation or sharing.

**US-W08:** As a user, I want to see AA Intelligence Index scores overlaid on model cards as a composite intelligence bar (0-100 calibrated).

**US-W09:** As a user, I want to view the config patch preview (YAML diff) in the browser before applying it.

**US-W10:** As a user, I want to filter models by capability (has_tools, has_vision, reasoning, open_weights) and provider in the web UI.

### 3.2 Terminal TUI Enhancement

**US-T01:** As a user, I want to use arrow keys to navigate a list of models in the terminal, showing details on the right panel (split-screen).

**US-T02:** As a user, I want to press `s` to toggle sort mode (by fitness, TPS, latency, AI index, tier, price) while in TUI mode.

**US-T03:** As a user, I want to press `/` to search/filter models by name or provider in the terminal.

**US-T04:** As a user, I want to see color-coded benchmark scores directly in the terminal table (S=orange, A=green, B=cyan, C=gray).

**US-T05:** As a user, I want to press `c` to enter compare mode, select 2-4 models, and see a side-by-side comparison table.

**US-T06:** As a user, I want to press `p` to preview the config patch for a selected slot with diff highlighting in the terminal.

**US-T07:** As a user, I want the terminal table to dynamically resize columns based on terminal width (no text wrapping).

**US-T08:** As a user, I want to see at-a-glance indicators for which models are currently configured in my Hermes/proxy configs.

### 3.3 Model Routing Layer

**US-R01:** As a user, I want to configure a cascade routing chain per slot: try model A, if confidence < threshold, fall back to model B, then model C.

**US-R02:** As a user, I want circuit breakers that stop calling a provider after N consecutive failures (with configurable cooldown).

**US-R03:** As a user, I want task-specific routing rules: route tool calls to models with high agentic scores, route summarization to high-context models, route general chat to cheap-fast models.

**US-R04:** As a user, I want to see routing decision logs showing which model was selected for each request type and why.

**US-R05:** As a user, I want confidence-based escalation: if the primary model returns low confidence, automatically escalate to the next model in the chain.

### 3.4 Multi-Axis Scoring

**US-S01:** As a user, I want to see the 4 primary scores (IQ, Speed, Agentic, Coding) for each model broken down by contributing factors.

**US-S02:** As a user, I want cross-influence modifiers visible: how context window affects agentic score, how reasoning affects speed score, etc.

**US-S03:** As a user, I want to see effective throughput calibration: speed × accuracy equivalence (a model with 2× speed but 0.5× accuracy has same throughput).

**US-S04:** As a user, I want a per-score breakout showing: base score + modifiers = final score with traceability.

### 3.5 Historical Analytics

**US-H01:** As a user, I want to see a line chart of top-10 model fitness scores over time (last 30 scans).

**US-H02:** As a user, I want to see which models appear most frequently in the top-3 of each slot (historical win rate).

**US-H03:** As a user, I want to see a degradation alert when a model's fitness drops by more than 15% between consecutive scans.

**US-H04:** As a user, I want to export historical analysis as CSV for external analysis.

### 3.6 AA API + models.dev Integration

**US-A01:** As a user, I want the scan to fetch fresh AA Intelligence Index, Coding Index, and Agentic Index scores when `AA_API_KEY` is set.

**US-A02:** As a user, I want models.dev data (context window, pricing, capabilities, architecture) to be fetched and cached as a secondary data source.

**US-A03:** As a user, I want to see which data came from AA API (live), models.dev (cached), or local heuristics (estimated) with clear provenance indicators.

**US-A04:** As a user, I want a `--refresh-provider-data` flag that updates models.dev cached data without running a full scan.

---

## 4. Non-Functional Requirements

| Requirement | Target | Priority |
|------------|--------|----------|
| Scan time for 200 models | < 60 seconds (probe) | Critical |
| Web UI page load | < 2 seconds initial, < 500ms subsequent | High |
| Database query for history | < 200ms for 30 scans × 200 models | High |
| TUI responsiveness | < 100ms keyboard latency | High |
| TUI process at 150+ models | Smooth scrolling, no frame drops | Medium |
| API freshness | AA data: 72h cache. models.dev: 24h | Medium |
| Offline capability | Full scan results viewable offline (cached) | Low |
| Web UI concurrency | Handle 3 concurrent users | Low |

---

## 5. Data Sources & Provenance

| Field | Primary Source | Fallback | Cache TTL |
|-------|---------------|----------|-----------|
| Intelligence Index | AA API (AA_API_KEY) | Heuristic (_estimate_intelligence) | 7 days |
| Coding Index | AA API | Heuristic | 7 days |
| Agentic Score | PinchBench API | Heuristic | 7 days |
| Speed (TPS, TTFT) | Live probe | AA API snapshot | Per scan |
| Context window | models.dev API | Hardware decode | 24h |
| Pricing | models.dev API | Per-provider defaults | 24h |
| Capabilities (tools, vision) | Live probe | Provider docs | Per scan |
| Architecture | models.dev API | Provider endpoint | 24h |
| Open weights | models.dev API | False (default) | 24h |
| Release date | models.dev API | N/A | On model add |
| SWE-Bench scores | benchmarks.json | N/A | Manual update |

---

## 6. Priority Matrix

| Feature | Value | Effort | Priority |
|---------|-------|--------|----------|
| Radar chart in web UI | High (visual comparison) | Medium | P1 |
| Terminal column alignment fix | Medium (readability) | Low | P1 |
| Compare mode (side-by-side) | High (decision making) | Medium | P1 |
| No "unknown" providers anywhere | Critical (trust) | Low | P1 |
| Historical trend charts | High (degradation detection) | Medium | P2 |
| Config patch preview (web) | High (safety) | Medium | P2 |
| Cascade routing layer | High (value add) | High | P2 |
| Circuit breaker integration | High (reliability) | Medium | P2 |
| Multi-axis scoring engine | High (better recommendations) | High | P2 |
| Per-slot candidate breakdown | Medium (understanding) | Medium | P2 |
| Provider status indicators | Medium (awareness) | Low | P2 |
| TUI model detail panel | Medium (exploration) | Medium | P3 |
| AA API live fetch | High (accuracy) | High | P3 |
| models.dev integration | High (accuracy) | High | P3 |
| Export/PDF download | Low (nice-to-have) | Medium | P4 |
| CSV historical export | Low (data portability) | Low | P4 |
