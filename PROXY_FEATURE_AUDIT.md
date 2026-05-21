# Claude Code Proxy → Ante Agent: Complete Feature Integration Plan

**Source audited:** `/home/cheta/code/claude-code-proxy/`
**Target:** Rust-based ante agent
**Goal:** Fold every proxy feature into ante for a single turn-key agent. No independent proxies.

---

## Tier 1: Core Agent Pipeline (Integrate First — P0)

These are the non-negotiable features that make the agent functional.

### 1. Multi-Provider Cascade (Fallback Chain)
**Files:** `src/core/circuit_breaker.py`, `src/core/model_router.py`, `config/proxy_chain.json`
**What it does:** On provider/model failure, automatically tries the next model in the cascade list. Per-tier (big/middle/small) and per-slot (background, long_context, image, web_search).
**Config vars for ante:**
```rust
struct CascadeConfig {
    enabled: bool,                    // MODEL_CASCADE=true
    daily_limit_per_model: u32,       // MODEL_CASCADE_DAILY_LIMIT=0
    entries: Vec<CascadeEntry>,       // ordered list of (model, provider, base_url, api_key)
}
```
**Env vars:**
- `MODEL_CASCADE=true`
- `MODEL_CASCADE_DAILY_LIMIT=0`

### 2. Task-Specific Routing Slots
**Files:** `src/core/model_router.py`, `config/proxy_chain.json` (`router` block)
**What it does:** Routes requests to specific models based on use-case signals: default, background, think, long_context (>60K tokens), web_search, image. Custom Python/JS router script support for advanced logic.
**Config vars for ante:**
- `ROUTER_BACKGROUND=nvidia/nemotron-nano-9b-v2:free`
- `ROUTER_THINK=nvidia/nemotron-3-super-120b-a12b:free`
- `ROUTER_LONG_CONTEXT=minimax/minimax-m2.5:free`
- `ROUTER_LONG_CONTEXT_THRESHOLD=60000`
- `ROUTER_WEB_SEARCH=`
- `ROUTER_IMAGE=qwen/qwen2.5-vl-72b-instruct:free`

### 3. Circuit Breakers
**File:** `src/core/circuit_breaker.py`
**What it does:** Per-model state machine CLOSED → OPEN (N failures) → HALF_OPEN (cooldown) → probe → CLOSED. Persisted to disk (JSON sidecar). Prevents hammering dead endpoints.
**Config vars:**
- `CB_FAILURE_THRESHOLD=3`
- `CB_SUCCESS_THRESHOLD=1`
- `CB_TIMEOUT_SECONDS=300`
- `CB_STATE_FILE=data/circuit_breaker_state.json`

### 4. Usage Tracking (SQLite)
**Files:** `src/core/config.py`, `src/utils/request_logger.py`
**What it does:** Logs every request to SQLite: model, input_tokens, output_tokens, cost, duration_ms, status, error, timestamp. Powers analytics, billing, and refinement loop.
**DB Schema:**
```sql
CREATE TABLE api_requests (
  id INTEGER PRIMARY KEY,
  timestamp TEXT,
  model TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost REAL,
  duration_ms INTEGER,
  status TEXT,
  error TEXT,
  request_count INTEGER DEFAULT 1
);
```
**Env vars:**
- `TRACK_USAGE=true`
- `USAGE_TRACKING_DB_PATH=~/.ante/usage.db`

### 5. Tier System (Big / Middle / Small)
**Files:** `src/core/assignments.py`, `config/proxy_chain.json` (`assignments` block)
**What it does:** Three fixed tiers mapping model capability to task complexity. BIG = opus-level, MIDDLE = sonnet-level, SMALL = haiku-level. Each has its own cascade list and per-tier reasoning overrides.
**Core struct:**
```rust
enum Tier { Big, Middle, Small }
struct TierConfig {
    model: String,
    provider: String,
    base_url: String,
    api_key_env: String,
    cascade: Vec<String>,        // fallback models
    reasoning_override: Option<String>,  // high/low/medium
}
```

---

## Tier 2: Intelligence Layer (Integrate Second — P1)

### 6. Semantic Cache
**File:** `src/services/semantic_cache.py`
**What it does:** Two-level cache (exact SHA-256 + fuzzy SimHash) that skips provider calls for near-duplicate prompts. Zero ML deps — pure Python SimHash. 256-entry LRU with TTL.
**Agentic loops produce 40-60% near-duplicate prompts** (same system prompt, different tool output). This eliminates redundant API calls.
- `SEMANTIC_CACHE_ENABLED=true`
- `SEMANTIC_CACHE_THRESHOLD=0.97`
- `SEMANTIC_CACHE_SIZE=256`
- `SEMANTIC_CACHE_TTL=3600`
- `SEMANTIC_CACHE_MIN_TOKENS=200`

### 7. Tool Schema Stripping (Compression)
**File:** `src/core/pipeline.py` (env-var driven)
**What it does:** Strips redundant fields from tool schemas, truncates descriptions to configurable max lengths. Saves 20-40% tokens on tool-call-heavy workloads.
- `TOOL_SCHEMA_STRIP=true`
- `TOOL_DESC_MAX=200`
- `TOOL_PARAM_DESC_MAX=120`

### 8. Token Budget / Cost Controls
**Files:** `src/core/config.py` (env vars)
**What it does:** Hard limits on per-request tokens, daily spend, mid-stream output budget (route to cheaper model after N output tokens).
- `DAILY_TOKEN_BUDGET=0` (max tokens per UTC day)
- `PER_REQUEST_TOKEN_BUDGET=0` (max input tokens per request)
- `DAILY_COST_BUDGET=0.0` (max USD per UTC day)
- `MID_STREAM_OUTPUT_BUDGET=0` (output tokens before switching to cheaper model)

### 9. Reasoning / Thinking Controls
**Files:** `src/core/reasoning_validator.py`, `src/models/reasoning.py`
**What it does:** Per-tier reasoning effort override, max thinking tokens, strip thinking from response option.
- `REASONING_EFFORT=low` (default)
- `REASONING_MAX_TOKENS=32000`
- `REASONING_EXCLUDE=false`
- `BIG_MODEL_REASONING=high`
- `MIDDLE_MODEL_REASONING=low`

---

## Tier 3: Operations Layer (Integrate Third — P2)

### 10. Identifier Mapping
**File:** `src/core/identifier_mapping.py`, `config/proxy_chain.json` (`identifier_mappings` block)
**What it does:** Maps incoming model name aliases to internal tier assignments. E.g. `claude-haiku-4-5` → SMALL tier, `gemini-3-pro-preview` → BIG tier. 100+ mappings in the current config.
```json
{
  "incoming_identifier": "claude-haiku-4-5",
  "assignment_id": "small",
  "enabled": true
}
```

### 11. Custom Router (Python/JS)
**File:** `src/core/model_router.py` (custom_router.py/js support)
**What it does:** Extensible routing via external scripts. Python function or Node.js module that receives the request and returns a provider/model string or null to fall through.
```python
# custom_router.py
def route(request: dict, config: object) -> str | None:
    if "expensive-operation" in str(request):
        return "big"
    return None
```

### 12. Health Monitoring & Watchdog
**File:** `config/proxy_chain.json` (watchdog settings in .env.example)
**What it does:** Auto-recovery watchdog that checks service health and restarts dead services.
- `PROXY_WATCHDOG=false`
- `WATCHDOG_INTERVAL=30`
- `WATCHDOG_GRACE=5`

### 13. Semantic Dedup / SimHash
**File:** `src/services/semantic_cache.py`
**What it does:** In addition to exact-match SHA-256, fuzzy matching via SimHash fingerprinting catches near-duplicates where only a search keyword changed. Configurable threshold.

---

## Tier 4: Analytics & UI Layer (Integrate Fourth — P3)

### 14. Usage Dashboard
**Files:** `src/dashboard/terminal_dashboard.py`, `src/dashboard/live_dashboard.py`
**What it does:** Terminal-based real-time dashboard showing: active routes, model health, cost breakdown, request rates. Also WebSocket live dashboard for browser.
**Should feed into:** model-scan's existing web UI and the refinement loop.

### 15. Analytics CLI & TUI
**Files:** `src/cli/analytics.py`, `src/cli/analytics_tui.py`
**What it does:** CLI commands for querying usage data: top models by cost, failure rates, token consumption trends. TUI for interactive exploration.

### 16. Reports (PDF/CSV)
**File:** `src/services/report_generator.py`, `src/api/reports.py`
**What it does:** Generates PDF/CSV reports from usage data for sharing or archiving.

### 17. Predictive Alerting
**File:** `src/services/predictive_alerting.py`
**What it does:** Anomaly detection on usage patterns, predictive cost alerts before budget is hit. Uses trend analysis against historical data.
**Value for a single user:** Catches runaway spend before the bill arrives.

### 18. Notification Engine
**File:** `src/services/notifications.py`
**What it does:** Sends alerts via Slack, email, PagerDuty, webhooks when circuit breakers trip, budgets approach limits, or models fail.

---

## Tier 5: Multi-User & Integration Layer (Integrate Fifth — P4)

### 19. User Management & RBAC
**Files:** `src/auth/user_manager.py`, `src/api/users_rbac.py`
**What it does:** Multi-user auth, role-based access control, per-user quotas and model restrictions.

### 20. Third-Party Integrations
**File:** `src/services/integrations.py`, `src/api/integrations.py`
**What it does:** Slack bot command handling, PagerDuty event routing, generic webhook dispatch.

### 21. GraphQL API
**File:** `src/api/graphql_schema.py`
**What it does:** Full GraphQL endpoint for querying usage data, model health, cost analytics. Complement to the REST API.

### 22. Web UI Dashboard
**Files:** `src/dashboard/`, `src/api/web_ui.py`, `web-ui/`
**What it does:** SvelteKit-based web dashboard with usage charts, model health, cost breakdowns, routing configuration. **Duplicates model-scan's existing web UI** — merge, don't reimplement.

---

## Implementation Priority Matrix

| Layer | Features | Depends On | Effort |
|-------|----------|-----------|--------|
| T1 Core | cascade, routing, breakers, SQLite, tiers | Nothing | 4-6 days |
| T2 Intelligence | semantic cache, tool stripping, budgets, reasoning | T1 | 3-5 days |
| T3 Operations | identifier mapping, custom router, watchdog, simhash | T1 | 2-3 days |
| T4 Analytics | dashboards, analytics CLI, reports, alerts, notifications | T1+T2 | 5-7 days |
| T5 Multi-User | RBAC, integrations, GraphQL, web UI | T1+T2+T4 | 4-6 days |

---

## Complete Env Var Inventory

```bash
# ── Cascade ──
MODEL_CASCADE=true
MODEL_CASCADE_DAILY_LIMIT=0

# ── Routing Slots ──
ROUTER_BACKGROUND=nvidia/nemotron-nano-9b-v2:free
ROUTER_THINK=nvidia/nemotron-3-super-120b-a12b:free
ROUTER_LONG_CONTEXT=minimax/minimax-m2.5:free
ROUTER_LONG_CONTEXT_THRESHOLD=60000
ROUTER_WEB_SEARCH=
ROUTER_IMAGE=qwen/qwen2.5-vl-72b-instruct:free

# ── Circuit Breaker ──
CB_FAILURE_THRESHOLD=3
CB_SUCCESS_THRESHOLD=1
CB_TIMEOUT_SECONDS=300
CB_STATE_FILE=data/circuit_breaker_state.json

# ── Usage Tracking ──
TRACK_USAGE=true
USAGE_TRACKING_DB_PATH=~/.ante/usage.db

# ── Semantic Cache ──
SEMANTIC_CACHE_ENABLED=true
SEMANTIC_CACHE_THRESHOLD=0.97
SEMANTIC_CACHE_SIZE=256
SEMANTIC_CACHE_TTL=3600
SEMANTIC_CACHE_MIN_TOKENS=200

# ── Compression ──
TOOL_SCHEMA_STRIP=true
TOOL_DESC_MAX=200
TOOL_PARAM_DESC_MAX=120

# ── Budget Controls ──
DAILY_TOKEN_BUDGET=0
PER_REQUEST_TOKEN_BUDGET=0
DAILY_COST_BUDGET=0.0
MID_STREAM_OUTPUT_BUDGET=0

# ── Reasoning ──
REASONING_EFFORT=low
REASONING_MAX_TOKENS=32000
REASONING_EXCLUDE=false
BIG_MODEL_REASONING=high
MIDDLE_MODEL_REASONING=low

# ── Watchdog ──
PROXY_WATCHDOG=false
WATCHDOG_INTERVAL=30
WATCHDOG_GRACE=5

# ── Providers ──
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
AA_API_KEY=${AA_API_KEY}
```

---

## Proxy Chain Config (for reference)

The current proxy_chain.json manages multiple services. Each service ante should absorb:

| Service | Port | What It Does | Absorb Into Ante? |
|---------|------|-------------|-------------------|
| claude_code_proxy | 8082 | Main routing/caching/breaker layer | ✅ Yes (this entire doc) |
| headroom | 8787 | Token headroom management middleware | ✅ Yes (T2 budget controls) |

After ante absorbs both, the proxy chain and its orchestration can be retired.
