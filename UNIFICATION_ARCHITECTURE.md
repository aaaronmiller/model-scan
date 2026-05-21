# model-scan ↔ claude-code-proxy: Unification Architecture

**Analyzed:** 2026-05-20
**Goal:** Single turn-key system where model-scan's data feeds the proxy's model selection

---

## 1. Current Architecture (Two Separate Systems)

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│     model-scan          │     │     claude-code-proxy        │
│  Python / FastAPI       │     │  Python 3.10+ / FastAPI      │
│  Port 8123              │     │  Port 8082                   │
│                         │     │                              │
│  Live probes (10 prov)  │     │  Request routing & cascade   │
│  Scoring engine (4 ax)  │     │  Circuit breakers            │
│  Analysis (AA+MD+PB)    │     │  Usage tracking (SQLite)     │
│  Calculus metrics       │     │  Semantic cache              │
│  Gold standard configs  │     │  Model recommender (guesst.) │
│  SvelteKit web UI       │     │  Model ranker (web search)   │
│  SQLite DB              │     │  SvelteKit web UI            │
│  REST API (11 endpoints)│     │  MCP server (crosstalk)      │
└─────────────────────────┘     └──────────────────────────────┘
```

**The gap:** The proxy's `recommender.py` analyzes saved config patterns (not real data). Its `model_ranker.py` uses LLM + web search to guess at model quality. Model-scan has **actual live probe data** (TPS, latency, reliability) + **multi-source analysis** (AA, Models.dev, PinchBench) + **16 derived metrics**. The proxy should consume this instead of guessing.

---

## 2. Integration Layer: Why REST + MCP + Shared DB

### Primary: REST API (already works)
Both are FastAPI. Zero new code to start.

| model-scan endpoint | Proxy consumer | What it replaces |
|---|---|---|
| `GET /api/v1/analysis` | `recommender.py`, `model_ranker.py` | Web search guesstimates → real scored data |
| `GET /api/v1/compare?models=a,b` | Cascade slot selection | Manual tier config → data-driven selection |
| `GET /api/v1/slots/:id` | Configuration wizard | Hardcoded model choices → fitness-ranked |
| `GET /api/v1/models?tier=S&free=true` | Free model discovery | OpenRouter model list → filtered + scored |
| `GET /api/v1/providers` | Provider health | Hardcoded provider list → live health |
| `GET /api/v1/scan/latest` | Any decision | Stale caches → current probe data |

### Secondary: MCP (agent-driven queries)
The proxy already has `src/api/mcp_server.py`. Model-scan adds an MCP server exposing:

```
model_scan__query("best model for task X")     → returns ranked models
model_scan__compare(["model-a", "model-b"])     → returns multi-axis comparison
model_scan__analyze("slot R1_primary")          → returns slot fitness analysis
model_scan__free_models()                       → returns whitelisted free models
```

MCP allows the proxy's agent (or any LLM) to query model-scan mid-conversation without hitting REST endpoints manually.

### Data Backbone: Shared SQLite
Currently:
- model-scan: `~/.config/model-scan/model_scan.db` (scans, models, slot_fitness, incumbents)
- proxy: `usage_tracking.db` (api_requests)

**Merge plan:** Proxy reads model-scan's DB directly for:
- Latest probe results (avoids duplicate scanning)
- Benchmark scores (avoids duplicate fetching)
- Free model whitelist (single source of truth)

Proxy writes to a shared schema for:
- Usage tracking (model-scan's analytics read this)
- Circuit breaker state (model-scan's audit checks this)

---

## 3. Integration Points (Specific Files)

### Proxy files to modify

| File | What to change |
|------|---------------|
| `src/services/models/recommender.py` | Replace config-pattern analysis with model-scan API calls for actual scored data |
| `src/services/models/model_ranker.py` | Replace web search with model-scan's multi-axis scores + PinchBench data |
| `src/services/models/free_model_rankings.py` | Consume `free_model_whitelist.json` from model-scan instead of maintaining separate list |
| `src/services/models/cost_lookup.py` | Use model-scan's pricing data from AA + Models.dev (more comprehensive) |
| `src/core/config.py` | Add model-scan API URL config, wire up health checks |
| `config/proxy_chain.json` | Remove as separate orchestrator → model-scan handles this |
| `src/api/mcp_server.py` | Add model-scan tool definitions |
| `src/core/model_router.py` | Use model-scan's slot fitness to auto-select cascade targets |

### Model-scan files to add/modify

| File | What to change |
|------|---------------|
| `api/main.py` | Add MCP server extension alongside existing REST routes |
| `analysis/engine.py` | Expose as importable library (so proxy can import directly) |
| No new DB schema | Proxy reads existing `model_scan.db` |

---

## 4. Integration Protocol Decision

| Approach | Latency | Complexity | Flexibility | Winner? |
|----------|---------|-----------|-------------|---------|
| **REST API** | Low (same machine) | Minimal | High | ✅ **Primary** |
| **MCP** | Low (stdio) | Medium | Very high (any LLM) | ✅ **Secondary** |
| **Python import** | Zero | Low (tight coupling) | Low | ⚠ For hot paths only |
| **Shared SQLite** | Zero | Low | Medium | ✅ **Data backbone** |
| **Subprocess/CLI** | Medium | High | Medium | ❌ Unnecessary |
| **WebSocket** | Low | Medium | Medium | ❌ Overkill here |

**Decision: REST API is the primary contract.** It's already built, both sides speak FastAPI, zero dependencies. MCP adds agent-driven query capability. Shared SQLite eliminates data duplication.

---

## 5. Priority Integration Order

### Phase 1 (Today — drop-in, no refactors)
1. Wire `recommender.py` → `GET /api/v1/analysis` — replace web search with real scores
2. Wire `model_ranker.py` → `GET /api/v1/models?sort=composite` — replace LLM ranking with multi-axis
3. Wire `free_model_rankings.py` → read `free_model_whitelist.json` from model-scan config

### Phase 2 (This week)
4. Proxy reads `model_scan.db` directly for circuit breaker + model health
5. Model-scan adds MCP server with `model_scan__*` tools
6. Model-selector TUI calls model-scan analysis for real-time model comparisons

### Phase 3 (Next week)
7. Merge web UIs — proxy's web UI becomes a tab in model-scan's dashboard
8. Merge config — proxy reads slot_definitions.yaml from model-scan config
9. Proxy chain orchestration retired — model-scan handles health checks

---

## 6. Env Vars to Add (to proxy's .env)

```bash
# model-scan integration
MODELSCAN_API_URL=http://localhost:8123
MODELSCAN_DB_PATH=~/.config/model-scan/model_scan.db
MODELSCAN_FREE_WHITELIST=~/.config/model-scan/free_model_whitelist.json
MODELSCAN_SLOT_DEFS=~/.config/model-scan/slot_definitions.yaml

# When set, proxy uses model-scan data instead of its own guesstimates
MODELSCAN_ENABLED=true
```

---

## 7. Wire Diagram (After Unification)

```
┌──────────────────────────────────────────────────────────────┐
│                    Unified System                             │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────────────┐  │
│  │  model-scan       │  REST    │  claude-code-proxy       │  │
│  │  Port 8123        │◄────────►│  Port 8082               │  │
│  │                   │          │                          │  │
│  │  - Live probes    │  MCP     │  - Request routing      │  │
│  │  - Analysis eng.  │◄────────►│  - Circuit breakers     │  │
│  │  - Scoring eng.   │          │  - Semantic cache       │  │
│  │  - Gold standard  │  Shared  │  - Usage tracking       │  │
│  │  - Calculus metr. │  SQLite  │  - Model selection ✓    │  │
│  │  - SvelteKit UI   │◄────────►│  - MCP server           │  │
│  │  - REST API       │          │                          │  │
│  └──────────────────┘          └──────────────────────────┘  │
│         │                              │                     │
│         └─────────── Shared DB ────────┘                     │
│                      │                                       │
│              ┌───────┴────────┐                              │
│              │  model_scan.db │                              │
│              │  (scans,       │                              │
│              │   models,      │                              │
│              │   usage,       │                              │
│              │   breakers)    │                              │
│              └────────────────┘                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Key Finding

The proxy's `recommender.py` and `model_ranker.py` are doing **guesstimates** — analyzing saved config files and running web searches to guess which models are good. Model-scan has **actual data** — live probes from 10 providers, 16 derived metrics, multi-source analysis from AA (1,436 models), Models.dev (4,817 models), and PinchBench (50 models). 

The unification is straightforward: point the proxy's model selection code at model-scan's API instead of doing its own guesswork. The REST endpoints already exist. This is a configuration change, not a rewrite.
