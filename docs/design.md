# model-scan v5: Architecture & Design Document
## Design Document — Web UX + Terminal TUI Enhancement

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACES                                    │
│  ┌────────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │   TERMINAL (CLI+TUI)       │  │   WEB UI (Svelte 5 + shadcn-svelte)  │   │
│  │   - Existing CLI output     │  │   - Dashboard with charts/tables     │   │
│  │   - Textual interactive TUI │  │   - Radar/spider charts (Chart.js)   │   │
│  │   - Keyboard-driven nav     │  │   - Historical trend lines           │   │
│  │   - ANSI colored tables     │  │   - Config patch preview             │   │
│  └───────────┬────────────────┘  └──────────────┬───────────────────────┘   │
│              │                                  │                            │
└──────────────┼──────────────────────────────────┼────────────────────────────┘
               │                                  │
               ▼                                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                       COMMAND & API LAYER                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ CLI Parser  │  │ REST API     │  │ TUI      │  │ WebSocket Server  │    │
│  │ (argparse)  │  │ (FastAPI)    │  │ (Textual)│  │ (real-time scan)  │    │
│  └──────┬──────┘  └──────┬───────┘  └────┬─────┘  └────────┬─────────┘    │
│         │                │               │                  │              │
│         └────────────────┴───────────────┴──────────────────┘              │
│                                  │                                         │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      CORE ENGINE                                            │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐    │
│  │ Orchestr.  │  │ Probe Engine │  │ Scoring     │  │ Routing Engine  │    │
│  │ (run_scan) │  │ (httpx,      │  │ Engine      │  │ (cascade,       │    │
│  │            │  │  asyncio)    │  │ (multi-axis) │  │  circuit break) │    │
│  └──────┬─────┘  └──────┬───────┘  └──────┬──────┘  └────────┬───────┘    │
│         │               │                  │                  │            │
│         └───────────────┴──────────────────┴──────────────────┘            │
│                                  │                                         │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                             │
│  ┌─────────────┐  ┌───────────────┐  ┌────────────┐  ┌──────────────┐    │
│  │ SQLite DB   │  │ JSON Cache    │  │ models.dev │  │ AA API       │    │
│  │ (analytics) │  │ (aa_cache,    │  │ API        │  │ (live data)  │    │
│  │             │  │  results.json)│  │ (static)   │  │              │    │
│  └─────────────┘  └───────────────┘  └────────────┘  └──────────────┘    │
│                                                                             │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────┐                    │
│  │ benchmarks  │  │ bad_models    │  │ scan_config   │                    │
│  │ .json       │  │ .json         │  │ .yaml         │                    │
│  └─────────────┘  └───────────────┘  └───────────────┘                    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Web UI Design (Svelte 5 + shadcn-svelte)

### 2.1 Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Svelte 5 (Runes) | Reactive, minimal boilerplate, excellent for dashboards |
| UI Library | shadcn-svelte | 80+ accessible components, dark mode, Tailwind v4 |
| Charts | Chart.js via svelte-chartjs | Radar, line, bar, scatter. Lightweight. |
| Routing | SvelteKit (file-based) | SSR for initial load, client-side navigation |
| Styling | Tailwind CSS v4 + shadcn defaults | Consistent design tokens |
| State | Svelte 5 $state / $derived | Runes-based reactivity |
| Backend API | FastAPI (Python) | Same process as model-scan, or sidecar |

### 2.2 Page Structure

```
/ (dashboard)
├── /scan/latest          → Latest scan results
├── /scan/history         → Historical trend charts
├── /slots                → Per-slot candidate breakdown
├── /slots/:id            → Single slot detail
├── /models               → Full model table (sortable, filterable)
├── /models/:id           → Single model detail page
├── /compare              → Radar chart comparison (2-5 models)
├── /config               → Config patch preview + apply
├── /routing              → Routing rules configuration
├── /providers            → Provider health status
└── /settings             → API keys, scan config, AA refresh
```

### 2.3 Key Components

**Dashboard (`/`):**
- `SectionCards` (4 summary cards: models scanned, slots filled, provider count, degrading/alerts)
- `ChartAreaInteractive` (fitness trend over last N scans)
- `DataTable` (top 10 models by composite score)
- Provider health row (green/yellow/red dots)

**Radar Chart Component (`/compare`):**
- Selection panel: multi-select dropdown or side list
- Chart panel: 4-axis radar (IQ, Speed, Agentic, Coding) with colored filled polygons
- Hover tooltip: exact scores per axis per model
- Legend: model names with color swatches
- Export button: PNG download

**Slot Detail (`/slots/:id`):**
- Slot metadata card (min_ai, min_tps, max_latency, needs_tools/vision)
- Candidate table: rank, model name, provider, fitness, score breakdown, status (incumbent/challenger)
- Fitness breakdown bar: intel (blue) + speed (green) + reliability (yellow) stacked bar
- Config patch preview: YAML diff showing current vs recommended model

**Model Detail (`/models/:id`):**
- Model identity card (provider, architecture, total/active params, context window)
- Radar chart miniature (this model's shape)
- Score breakdown tabs: Intelligence, Speed, Agentic, Coding with modifier traceability
- Benchmark scores: SWE-Verified, SWE-Pro, Terminal-Bench, Aider (colored badges)
- Slot match table: which slots this model qualifies for, with fitness scores

### 2.4 shadcn-svelte Components Used

```
Accordion    → Slot explanation panels
Button       → Apply config, run scan, refresh AA
Card         → Model detail cards, summary cards
Chart        → Wraps Chart.js radar/line/bar charts
Collapsible  → Score breakdown details
Command      → Model search combobox
DataTable    → Main model table, slot candidates table
Dialog       → Compare modal, config apply confirmation
DropdownMenu → Sort/filter menus
Select       → Slot selector, provider filter
Sheet        → Side panel for model detail
Tabs         → Score breakdown tabs
Tooltip      → Hover details on scores, benchmarks
Badge        → Tier indicators, capability flags
Progress     → Fitness score bars
```

---

## 3. Terminal TUI Design (Textual)

### 3.1 TUI Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│  model-scan v5 TUI — 47 models · 12 slots · ✓ AA fresh    │
├─────────────────────────────────────────────────────────────┤
│  / search  [s]sort  [c]ompare  [p]review  [f]ilter  [q]uit│
├────────────────────────────┬────────────────────────────────┤
│                            │                                │
│  #  MODEL          TIER    │  Model: qwen3-next-80b         │
│  1  qwen3-next-80b  S      │  Provider: NVIDIA NIM          │
│  2  deepseek-v4-f   A      │  TPS: 45.2  Lat: 1.2s         │
│  3  minimax-m2.7    A      │  Tools: ✓  Vision: ·          │
│  4  kimi-k2.6       A      │  AA Index: 55 (A-tier)        │
│  5  glm-5.1         A      │  Benchmarks:                  │
│  6  mimo-v2.5-pro   B      │    SWE-V: 79%  [████████░░]  │
│  7  deepseek-v4-p   B      │    Term: 61.6% [██████░░░░]  │
│  8  qwen3.6-plus    B      │  Slot Fitness:                 │
│  9  allam-2-7b      B      │    R1_primary:  93.3  ✓       │
│ 10  ling-2.6-flash  B      │    R12_delegate 87.1  ✓       │
│ 11  llama-3.3-70b   C      │    R_mcp:        82.4  ✓      │
│ 12  gpt-oss-120b    C      │  Score Breakdown:              │
│ 13  nemotron-3-su   C      │    Intel(90%): 55.0 → 49.5    │
│                            │    Speed(10%): 45.2 →  4.5    │
│                            │    Total:             54.0    │
│                            │    Arch bonus:         ×1.05  │
│                            │    Final:             56.7    │
├────────────────────────────┴────────────────────────────────┤
│  42 accessible  ·  5 degraded  ·  0 dead  ·  3 skip-listed │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Keyboard Map

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate model list |
| → | Expand model detail panel |
| ← | Collapse model detail panel |
| / | Search/filter models |
| s | Cycle sort: fitness → TPS → AI → tier → latency → price |
| c | Select current model for compare (up to 4), C to show compare |
| p | Preview config patch for current slot |
| f | Cycle fit filter: all → qualified → incumbent → accessible |
| t | Cycle tier filter: all → S/A/B/C/— |
| v | Toggle compact/comfortable row height |
| Tab | Focus shift: list ↔ detail ↔ footer |
| q / Esc | Quit / close panel |
| ? | Show help overlay |
| r | Force refresh scan data |
| Enter | Open model in web browser (if web UI running) |
| 1-9 | Quick switch to slot view for slot N |

### 3.3 Compare Mode

```
┌──────────────────────────────────────────────────────────────┐
│  COMPARE MODE — 3 models selected                           │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│             │ qwen3-next  │ deepseek-v4 │ minimax-m2.7      │
│             │ -80b        │ -flash      │                   │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ Intelligence│ 55.0 (A)    │ 60.0 (A)    │ 52.0 (B)          │
│ Speed       │ 45.2 t/s    │ 105.0 t/s   │ 48.0 t/s          │
│ Agentic     │ 78.3        │ 65.2        │ 71.5              │
│ Coding      │ 72.1        │ 80.4        │ 68.9              │
│ Context     │ 262K        │ 1M          │ 205K              │
│ Price $/M   │ $1.88       │ $0.18       │ $0.52             │
│ SWE-V       │ 52.0%       │ 79.0%       │ 80.2%             │
│ Tools       │ ✓           │ ✓           │ ✓                 │
│ Vision      │ ·           │ ·           │ ·                 │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ Winner:     │             │ ✓ Agentic   │ ✓ SWE-Bench       │
│             │             │ ✓ Cost      │                   │
└─────────────┴─────────────┴─────────────┴───────────────────┘
  [1-3] toggle selection  [c] close compare  [Enter] export
```

---

## 4. REST API Design (FastAPI)

### 4.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/scan/latest` | Latest scan results (models, slots, fitness) |
| GET | `/api/v1/scan/history` | Historical scan summaries (timestamps, counts) |
| GET | `/api/v1/scan/history/:scan_id` | Single scan detail |
| GET | `/api/v1/models` | All models with scores, filters, pagination |
| GET | `/api/v1/models/:model_id` | Single model detail with all scores |
| GET | `/api/v1/slots` | All slot definitions with incumbents |
| GET | `/api/v1/slots/:slot_id` | Slot detail with candidate rankings |
| POST | `/api/v1/scan` | Trigger a new scan (async) |
| GET | `/api/v1/scan/status/:scan_id` | Check scan progress (WebSocket fallback) |
| GET | `/api/v1/compare?models=a,b,c` | Comparison data for N models |
| GET | `/api/v1/benchmarks` | Benchmark data sources and scores |
| POST | `/api/v1/config/preview` | Preview config patch for a slot |
| POST | `/api/v1/config/apply` | Apply config patch to filesystem |
| GET | `/api/v1/providers` | Provider health status |
| GET | `/api/v1/aa/status` | AA API cache status |
| POST | `/api/v1/aa/refresh` | Force refresh AA cache |

### 4.2 WebSocket

| Event | Direction | Payload |
|-------|-----------|---------|
| `scan:progress` | Server→Client | `{scan_id, pct, current_model, provider}` |
| `scan:complete` | Server→Client | `{scan_id, model_count, duration}` |
| `scan:error` | Server→Client | `{scan_id, model, error}` |
| `provider:status_change` | Server→Client | `{provider, status, message}` |

---

## 5. Multi-Axis Scoring Engine Design

### 5.1 Architecture

The scoring engine from the Ice-ninja specification is implemented as a composable pipeline:

```
Raw Data → Calibration → Base Scores → Modifiers → Final Scores → Slot Matching
```

Each primary axis (IS, SS, AS, CS) has:
- A **calibration function** that normalizes raw data to 0-100
- A set of **modifier functions** that apply cross-influence
- A **trace recorder** that logs each modification step (for UI display)
- A **final clamp** to 0-100

### 5.2 Python Implementation Structure

```python
# scoring/engine.py
class ScoringEngine:
    def __init__(self, model_data, benchmark_data):
        self.raw = model_data
        self.benchmarks = benchmark_data

    def compute_all(self) -> MultiAxisScores:
        return MultiAxisScores(
            intelligence=self._compute_intelligence(),
            speed=self._compute_speed(),
            agentic=self._compute_agentic(),
            coding=self._compute_coding(),
        )

    def _compute_intelligence(self) -> AxisScore:
        base = self._calibrate(self.raw.aa_index, self.benchmarks.aa_max)
        modifiers = [
            KnowledgeCutoffModifier(self.raw.knowledge_cutoff),
            ReleaseDateModifier(self.raw.release_date),
            ReasoningModifier(self.raw.has_reasoning, self.raw.reasoning_depth),
            ContextWindowModifier(self.raw.context_window),
            MultimodalModifier(self.raw.modalities),
        ]
        return self._apply_modifiers(base, modifiers)

    def _compute_agentic(self) -> AxisScore:
        # ... etc
```

### 5.3 Modifier Chain (per Illinois tracing)

```python
@dataclass
class ModifierTrace:
    name: str
    description: str
    input_value: float
    modifier_delta: float
    output_value: float

class Modifier:
    name: str
    def apply(self, value: float, model) -> tuple[float, ModifierTrace]: ...
```

Each modifier records its input, the delta it applied, and the output. The UI renders these as a traceable chain: `base 55 → +8 (context 128K) → -3 (knowledge cutoff 18mo) → +5 (reasoning) = 65`.

---

## 6. Model Routing Engine Design

### 6.1 Routing Strategies

```python
# routing/strategies.py

@dataclass
class RouterConfig:
    """Per-slot routing configuration."""
    slot_id: str
    primary_model: str
    primary_provider: str
    fallback_chain: list[tuple[str, str]]  # [(model, provider), ...]
    strategy: Literal["cascade", "confidence", "cost-optimized", "latency"]
    circuit_breaker: CircuitBreakerConfig
    confidence_threshold: float = 0.85

class CascadeRouter:
    """Try primary, escalate on failure/low-confidence."""
    def route(self, request, config) -> RouterResult: ...

class CircuitBreaker:
    """N-failures-in-window → open → cooldown → half-open → test."""
    state: BreakerState
    failure_window: deque[float]
    threshold: int = 5
    window_seconds: float = 60.0
    cooldown_seconds: float = 30.0

    def can_attempt(self) -> bool: ...
    def record_success(self): ...
    def record_failure(self): ...
```

### 6.2 Config Output (YAML)

```yaml
# ~/.hermes/routing.yaml
routing:
  R1_primary:
    primary: { model: "qwen3-next-80b", provider: "nvidia" }
    fallbacks:
      - { model: "deepseek-v4-flash", provider: "opencode-go" }
      - { model: "minimax-m2.7", provider: "opencode-go" }
    strategy: confidence
    confidence_threshold: 0.85
    circuit_breaker:
      failure_threshold: 5
      cooldown_seconds: 30

  R12_delegation:
    primary: { model: "minimax-m2.7", provider: "opencode-go" }
    fallbacks:
      - { model: "deepseek-v4-pro", provider: "deepseek" }
    strategy: cascade
    circuit_breaker:
      failure_threshold: 3
      cooldown_seconds: 60
```

---

## 7. Data Flow: End-to-End Scan

```
1. User invokes scan (CLI or Web "Run Scan")

2. Orchestrator reads config:
   - slot_definitions.yaml (slot requirements)
   - benchmarks.json (reference scores)
   - scan_config.yaml (provider strategies)

3. For each provider:
   a. list_models() → API catalog
   b. is_permanently_skipped() → bad_models.json check
   c. probe_one() → TPS, latency, HTTP status
   d. probe_tools() → tool call capability
   e. (_with AA API): fetch intelligence/coding/agentic scores
   f. (_with models.dev): fetch context/pricing/architecture

4. DossierAssembly:
   - Merge probe results + AA data + models.dev data
   - _estimate_intelligence() if AA unavailable
   - _match_benchmark() for SWE scores
   - _ocgo_budget_score() for budget analysis
   - compute_tier()
   - compute_composite()

5. Slot Matching:
   - For each slot_def:
     - Gate check (min_ai, min_tps, max_latency, tools, vision, ctx)
     - slot_fitness() → weighted score
     - Qualify top 10 candidates

6. Output Generation:
   - CLI: ANSI-colored tables (incumbent panel, per-slot, appendix)
   - TUI: Interactive terminal interface
   - Web API: JSON response → Web UI renders
   - DB: SQLite write (scans, models, slot_fitness, incumbents)

7. Config Patching:
   - generate_hermes_patch() → YAML diff
   - Web UI: preview → apply
   - CLI: --patch-hermes direct apply
```

---

## 8. Database Schema (Additions for v5)

```sql
-- New tables for v5
CREATE TABLE IF NOT EXISTS routing_configs (
    config_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id     TEXT    NOT NULL,
    primary_model TEXT  NOT NULL,
    fallback_chain  TEXT,      -- JSON array of {model, provider}
    strategy    TEXT    NOT NULL DEFAULT 'cascade',
    confidence_threshold REAL DEFAULT 0.85,
    circuit_breaker_config TEXT, -- JSON
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS circuit_breaker_events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    provider    TEXT    NOT NULL,
    slot_id     TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,  -- open/close/half-open/failure
    timestamp   TEXT    NOT NULL,
    failure_count INTEGER,
    cooldown_s   REAL
);

CREATE TABLE IF NOT EXISTS routing_decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     INTEGER,
    slot_id     TEXT    NOT NULL,
    request_type TEXT,  -- general/code/tool/summarize
    selected_model TEXT,
    selected_provider TEXT,
    fallback_used   INTEGER DEFAULT 0,
    confidence      REAL,
    latency_ms      REAL,
    cost_usd        REAL,
    error           TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
);

-- Additional columns for models table
ALTER TABLE models ADD COLUMN aa_coding_index REAL;
ALTER TABLE models ADD COLUMN aa_agentic_index REAL;
ALTER TABLE models ADD COLUMN use_case TEXT;  -- primary use case
ALTER TABLE models ADD COLUMN pin_slot TEXT;  -- best-fit slot
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Week 1)
- Fix all bugs from deliberative refinement (A1-A9)
- Implement terminal column alignment fixes
- Remove all "unknown" provider strings (replace with meaningful fallbacks)
- Add TUI mode structure (Textual app shell)
- REST API scaffold (FastAPI with SQLite read endpoints)

### Phase 2: Web UI Core (Week 2)
- SvelteKit + shadcn-svelte project setup
- Dashboard page with summary cards and data table
- Model list page with sortable DataTable
- API integration (connect to FastAPI backend)
- Dark mode + responsive layout

### Phase 3: Visualization (Week 3)
- Radar chart component (4-axis comparison)
- Historical trend chart (fitness over time)
- Slot detail page with score breakdown
- Model detail page with radar miniature
- Compare mode (select 2-5 models, overlay charts)

### Phase 4: Scoring Engine (Week 4)
- Module: `scoring/engine.py` with 4-axis pipeline
- Module: `scoring/modifiers.py` with trace recording
- Module: `scoring/calibration.py`
- Module: `scoring/roles.py` (12 Hermes slot profiles)
- Integration tests comparing output to known rankings

### Phase 5: Routing & Circuit Breakers (Week 5)
- Module: `routing/strategies.py`
- Module: `routing/circuit_breaker.py`
- Router config YAML generation
- Routing decision logging to DB
- Web UI routing rules page

### Phase 6: AA API + models.dev Integration (Week 6)
- Enhanced `_fetch_aa()` with Coding + Agentic indices
- models.dev client: `list_models`, `get_model`, `search`
- Cache layer with configurable TTL
- Provenance tracking (live/cached/heuristic)
- Web UI data freshness indicators

---

## 10. Design Principles

1. **Terminal First** — Every feature must work in the terminal before the web UI gets it.
2. **Traceability** — Every score must be explainable: "why did this model get 55 instead of 60?"
3. **No Black Boxes** — All data sources have provenance labels (live/cached/estimated/heuristic).
4. **Offline Capable** — Once cached, all data must be viewable without network access.
5. **Zero Configuration** — Running `model-scan` with no flags must produce complete, useful output.
6. **Fail Gracefully** — If AA API is down, use cached data. If models.dev is down, use heuristics.
7. **Data Portability** — All data is in SQLite or JSON files (git-friendly).
8. **Progressive Disclosure** — Show summary first, details on demand (accordion, drill-down).

---

## 11. Key References

| Resource | Usage |
|----------|-------|
| shadcn-svelte.com/docs | Web UI component library |
| github.com/huntabyte/shadcn-svelte | Svelte port of shadcn/ui |
| textual.textualize.io | Terminal TUI framework |
| github.com/arimxyer/models | Reference for models.dev + AA TUI integration |
| chartjs.org | Radar, line, bar charts |
| arxiv.org/abs/2410.10347 | Cascade routing theory (ETH Zurich) |
| github.com/eth-sri/cascade-routing | Cascade routing implementation |
| blog.appxlab.io/2026/04/05/llm-router | Production LLM routing patterns |
| learnwithparam.com/blog/circuit-breakers-llm-calls | Circuit breaker patterns |
| github.com/kefyusuf/llm-terminal | Reference TUI implementation |
| artificialanalysis.ai | AA Intelligence Index API |
| models.dev | Model metadata API |
