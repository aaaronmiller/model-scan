# Model-Scan Dynamic Addendum v2
## Dynamic Config Generation, Concurrent Sessions, Logfile Mining, Endpoint Capability Detection, and Live Web UX Dashboard for the Hermes AI Agent Fleet

**Addendum to:** Model-Scan Refinement Instructions v2  
**Assumes completion of:** Phases 1-9 from the Refinement Guide  
**Generated:** 2026-05-28 | Config Version: v39 alignment  
**Target Programs:** Hermes, Claude Code, Codex, OpenCode, Pi Agent

---

This document extends the model-scan-refinement-guide.md with five capabilities: (1) dynamic config generation that creates optimal Hermes YAML configs on demand based on real-time model availability and plan health, (2) concurrent session management that allows many more simultaneous sessions by quota-aware model allocation across all three machines, (3) logfile mining that identifies persistent issues and feeds corrections back into the model-scan fitness scoring system, (4) coding endpoint capability detection that probes what each model endpoint can actually do (function calling, structured output, vision, etc.) before assigning it to slots, and (5) a live web UX dashboard that displays real-time provider usage, remaining quota, countdown timers to quota reset, currently deployed configurations, and projected next-deployment configs. All five capabilities are designed to work together as an integrated system, building on the tier registry, fitness formula, and gateway architecture established in the base refinement guide.

---

## 1. Dynamic Config Generation on Demand

### 1.1 The Problem with Static Configs

The current Hermes configs (config-primary.yaml, config-worker-a.yaml, config-worker-b.yaml) are static files. They encode a specific set of model choices and fallback chains that were optimal at the time of authoring. But the model landscape changes constantly: OpenCode Go goes from healthy to fully utilized overnight, OpenRouter free models gain or lose availability, Ollama Cloud quotas drain and refill on a 3-hour cycle, and new models appear that may be strictly better than the ones hardcoded into the configs. A static config cannot adapt to these changes, which means the system operates suboptimally most of the time. The most recent example is the OpenCode Go exhaustion: the config had to be manually revised to remove all Go slots and redirect them to Ollama Cloud and OpenRouter free models. If model-scan had been able to generate configs dynamically, this would have been an automatic adjustment detected and applied without manual intervention.

The fundamental insight is that the config file is a snapshot of an optimization problem. Every slot in the config is a decision: which model, from which provider, with which fallbacks, given the current state of all providers, quotas, model quality, and historical failure rates. This is exactly the kind of problem that model-scan is designed to solve. By making model-scan the config generator rather than just an advisor, we close the loop: model-scan knows the current state of every provider and model, computes optimal assignments, and emits the config that the harness or CLI will use.

### 1.2 Architecture: model-scan as Config Generator

The architecture adds a new mode to model-scan: **config-generate**. When invoked, this mode performs the following pipeline: (1) probe all providers for current health and quota status, (2) load the tier registry and historical failure data, (3) compute fitness scores for every candidate model on every slot, (4) assign the best-fit model to each slot, (5) construct fallback chains respecting tier floors and provider diversity, and (6) emit a valid Hermes config YAML file. The config-generate mode replaces the manual config-authoring process with an automated, data-driven one. The human operator still controls the high-level policy (tier floors, slot definitions, provider key assignments per machine), but the specific model choices are determined by the optimizer.

#### 1.2.1 The Config Template System

Rather than generating configs from scratch, model-scan uses a template system. Each config type (primary, worker-a, worker-b) has a template that defines the structure: which slots exist, what their tier floors are, what providers are allowed, and what the non-model settings are (compression, display, memory, approvals, etc.). The template contains placeholders for the model selections, which model-scan fills in using the fitness optimization. This approach has several advantages over generating from scratch: the template ensures structural validity, the operator can override specific slots if desired, and the generated config is always a complete, valid Hermes config that can be inspected and modified by hand if needed.

Templates are stored in `~/.config/model-scan/templates/` as YAML files. Each template has three sections: **policy** (tier floors, provider allowlists, slot definitions), **skeleton** (the full config structure with `{{PLACEHOLDER}}` markers), and **constraints** (provider key isolation rules, diversity requirements).

#### 1.2.2 Slot Resolution Algorithm

For each slot in the template, model-scan runs the following resolution algorithm:
1. Gather all candidate models that meet the slot's tier floor and IQ/TC minimums
2. Filter candidates by provider health (exhausted providers excluded) and quota availability (<10% quota = deprioritized)
3. Compute composite fitness score (tier anchor × AA multiplier × historical failure × latency consistency × provider availability × TC weight)
4. Rank candidates by fitness; select top model as primary assignment
5. Construct fallback chain from next-best candidates, enforcing provider diversity and tier degradation constraints

#### 1.2.3 The Config Hydration Pipeline

1. **Validate**: Check slot assignments meet policy constraints (tier floors, provider allowlists, key isolation)
2. **Inject**: Fill skeleton template with resolved model names, providers, base_urls, api_key_envs, timeouts, fallback chains
3. **Deduplicate**: Scan for provider key conflicts; re-resolve conflicting slots with different-key constraints
4. **Emit**: Write final config YAML, compute content hash for change detection, log diff if changed

### 1.3 Pre-Run Hook: Auto-Generate Before Launch

The key integration point is a pre-run hook that runs before every session. The hook calls `model-scan --config-generate --template primary --output config-primary.yaml` and then launches the program with the fresh config. This ensures every session starts with the best available models.

### 1.4 Change Detection and Operator Review

Every generated config includes a comment header with: generation timestamp, content hash, previous content hash, and a summary of changes. The change log is appended to `~/.config/model-scan/config_changelog.jsonl` for historical debugging.

---

## 2. Concurrent Session Management

### 2.1 The Multi-Session Problem

With three machines running Hermes, Claude Code, Codex, OpenCode, and Pi Agent simultaneously, there can easily be 10-20 concurrent sessions. Each session consumes model API quota from one or more providers. The current approach of giving each config its own provider keys provides isolation but not coordination. The concurrent session management system makes model-scan the central allocator, tracking total quota consumption across all sessions in real time.

### 2.2 Session-Aware Quota Tracking

Model-scan maintains a quota ledger at `~/.config/model-scan/quota_ledger.json` that tracks, for each provider and model, the total requests consumed today and the allocation to each active session. For providers with native quota APIs (OpenRouter), the ledger is reconciled hourly. For others (OpenCode, Ollama Cloud), the ledger relies on local accounting with periodic health probes.

### 2.3 Quota-Aware Model Allocation

When a new session requests a model assignment, model-scan ranks candidates by a modified fitness that includes a quota availability multiplier:

```
fitness_quota = fitness_base × (remaining_quota / daily_limit)
```

This steers sessions toward less-used models as quotas drain. For hard quota limits (e.g., Go is exhausted), fitness = 0 (hard exclusion).

### 2.4 Session Priority and Preemption

| Priority | Description | Examples |
|----------|-------------|----------|
| P0 | User-facing, interactive | Coordinator Hermes session |
| P1 | Coordinator-level delegation | delegate_task subagents |
| P2 | Worker-level bulk processing | Worker A V4-Flash tasks |
| P3 | Background monitoring | Logfile mining, health probes |

When quota is scarce, P0 sessions are allocated first. If a P0 session cannot find a suitable model, it can preempt a lower-priority session, which is reassigned to a cheaper model.

### 2.5 Many-Session Architecture: 20+ Concurrent Sessions

Total aggregate free budget is ~19,000+ requests/day. At ~100 requests per session-hour, this supports ~190 session-hours/day, or about 20 concurrent sessions running 10 hours each. The bottleneck is per-model quota (1,000/day on OR free). Solution: distribute sessions across models round-robin (e.g., 15 sessions needing A-tier tool-calling: 5→GLM-4.5-Air, 5→M2.5, 5→V4-Flash).

### 2.6 Conflict Resolution Between Programs

When multiple programs request the same model simultaneously:
- If enough quota for both → assign to both
- If not enough → higher priority gets the model; lower priority gets next-best fallback
- Same priority → proportional allocation

---

## 3. Logfile Mining for Persistent Issue Detection

### 3.1 Why Mine Logfiles?

Health probes detect whether a model responds to a minimal request, but they cannot detect:
- Consistent malformed tool calls (model responds but produces bad output)
- Context window truncation on multi-turn conversations
- Slot-specific degradation (works for compression, fails for MCP)
- Cross-session patterns (8/10 sessions using Owl Alpha hit structured output errors)

### 3.2 Log Sources and Locations

| Log Source | Location | Key Signals |
|-----------|----------|-------------|
| Hermes agent.log | ~/.hermes/logs/agent.log | Tool call failures, API errors, latency spikes |
| Hermes sessions/ | ~/.hermes/sessions/ | Per-session conversation logs, model assignments |
| Claude Code logs | ~/.claude/logs/ | Proxy routing, model swaps, token usage |
| Codex execution | ~/.codex/logs/ | Profile assignments, task completion rates |
| OpenCode CLI | ~/.opencode/logs/ | Plan quota, model availability, rate limits |
| Pi Agent output | ~/pi-agent/logs/ | Worker completion, quality, timeouts |
| Model-scan history | ~/.config/model-scan/history/ | Probe results, fitness scores over time |
| Gateway/proxy logs | ~/.config/model-scan-gateway/logs/ | Request routing, fallback activations |

### 3.3 Mining Pipeline Architecture

Three stages: **Extract** → **Classify** → **Aggregate**

#### Extract
Read raw log entries → structured JSONL with: timestamp, session_id, model_name, provider, slot, event_type, event_details. Idempotent (tracks position in each log file).

#### Classify
Apply pattern-matching rules from `~/.config/model-scan/mining_rules.yaml`:

| Rule ID | Condition | Category | Severity |
|---------|-----------|----------|----------|
| R001 | structured_output_error | struct_output_fail | 4 |
| R002 | tool_call_failure + slot in [mcp, skills_hub] | tool_call_fail | 5 |
| R003 | api_error + code in [402, 429] | quota_exhaustion | 3 |
| R004 | timeout + latency > 60s | timeout_critical | 4 |
| R005 | context_truncation | ctx_truncation | 3 |
| R006 | quality_degradation | quality_loss | 4 |
| R007 | fallback_activation > 3/session | fallback_storm | 3 |
| R008 | rate_limit + provider in [groq, cerebras] | rate_limit_free | 2 |
| R009 | error contains "overloaded" | provider_overload | 3 |
| R010 | tool_call_failure + model=owl-alpha | owl_alpha_struct_fail | 5 |

#### Aggregate
Persistence score per (model, slot, category) triplet:

```
P = (N_sessions_with_issue / N_sessions_total) × severity_weight × recency_weight
```

- `severity_weight` = avg severity normalized to 0.2-1.0
- `recency_weight` = 0.5^(hours_ago / 24) (half-life of 24 hours)
- Scores above 0.5 are persistent and trigger fitness adjustments

### 3.4 Issue-to-Fitness Feedback Loop

The persistence scores feed into the fitness formula as a new multiplier:

```
historical_issue_multiplier = 1.0 - persistence_score
```

- Model with persistence_score = 0.8 → multiplier = 0.2 (80% less likely to be selected)
- **Slot-specific**: a model penalized for MCP issues can still be fit for compression
- Mining runs every 6 hours; scores update `model_issue_scores.json`; next config-generate automatically benefits

### 3.5 Issue-to-Fix Pipeline

When persistence_score > 0.7 for any (model, slot, category) triplet, the system generates a fix record with:
- Model and slot affected
- Issue category and severity
- Sessions impacted
- Recommended action (e.g., "Remove owl-alpha from MCP slot: 13.5% structured output error rate across 8 sessions")
- Specific config change needed

Fixes are written to `~/.config/model-scan/fix_recommendations.jsonl` and displayed in daily scan output. Auto-applied if persistence_score > 0.9.

### 3.6 Mining Scripts

**Script 1: Hermes Log Extractor** — Extracts structured events from `~/.hermes/logs/agent.log` using regex patterns for ERROR/WARN/tool_call/fallback/timeout events. Tracks file offset for idempotent incremental processing.

**Script 2: Persistence Score Aggregator** — Reads all extracted JSONL files, groups by (model, slot, category), computes prevalence × severity × recency, and writes `model_issue_scores.json`.

**Script 3: Config Impact Analyzer** — Correlates config changelog timestamps with session failure rates before/after. Detects regressions (>20% increase in failures) and generates rollback recommendations.

*(Full Python source for all three scripts is included in the companion PDF.)*

---

## 4. Integration Matrix

### 4.1 Dynamic Generation ↔ Gateway

The gateway routes individual API requests; dynamic generation creates the configs that define available models. Integration: when the gateway detects a model is degraded, it triggers on-demand config regeneration for the affected program, even mid-session.

### 4.2 Logfile Mining → Fitness Scores

The `historical_issue_multiplier` (1.0 - persistence_score) is incorporated into the fitness formula used by both config-generate and the gateway's /route endpoint. Mining also enhances plan health monitoring: log spikes in 402/429 errors flag providers as degraded even when synthetic probes pass.

### 4.3 Concurrent Sessions ↔ Multi-Program Monitoring

The `program_assignments.json` file now includes per-session allocations, not just per-program. The /quota endpoint shows breakdown by session and program. The /swap endpoint can target specific sessions within a program.

### 4.4 Unified State Model

| File | Written By | Read By | Purpose |
|------|-----------|---------|---------|
| tiers.yaml | Operator | config-generate, gateway, daily scan | Static tier assignments |
| blocklist.yaml | Operator | config-generate, gateway, daily scan | Excluded models |
| plan_health.json | health_probe.py | config-generate, gateway, daily scan | Provider plan status |
| quota_ledger.json | gateway, session mgr | config-generate, gateway | Per-session quota tracking |
| model_issue_scores.json | persistence_scorer.py | config-generate, gateway, dashboard | Issue persistence scores |
| program_assignments.json | config-generate, gateway | daily scan, swap, dashboard | Model assignments per session |
| config_changelog.jsonl | config-generate | config_impact_analyzer, dashboard | Config change history |
| session_pool.yaml | Operator | session mgr, config-generate, dashboard | Session limits, quota reserves |
| mining_rules.yaml | Operator | persistence_scorer | Event classification rules |
| endpoint_capabilities.json | endpoint_prober.py | config-generate, gateway, dashboard | Endpoint capability data |
| dashboard_auth.yaml | Operator | dashboard backend | Dashboard access control |

**Data flow:**
```
logfiles → extractors → extracted events → classifier → classified events
    → aggregator → model_issue_scores.json → fitness formula → config-generate
    → config YAML → programs

provider APIs → health probes → plan_health.json → fitness formula → config-generate

model endpoints → endpoint_prober.py → endpoint_capabilities.json
    → capability_match_multiplier → fitness formula → config-generate

program sessions → gateway → quota_ledger.json → session manager → model allocations

all state files → dashboard backend → dashboard frontend (web UX)
    → provider status, quota tracker, countdown timers
    → current configs, next-deployment projection, session pool
    → issue heatmap, fix recommendations, config changelog
```

---

## 5. Data Requirements and Information Queries

### 5.1 Information Needed from the Operator

| Item | Source | Purpose |
|------|--------|---------|
| Hermes log sample (1 week) | Script 5.2 | Validate extractor rules |
| Session count per day (30 days) | Script 5.3 | Calibrate session pool and reserves |
| Current model-scan output | `model-scan --mode daily` | Baseline fitness scores |
| Claude Code proxy config | Operator input | Map CC big/med/small to gateway rules |
| Codex profile definitions | Operator input | Map profiles to tiers |
| Pi Agent task types | Operator input | Estimate quota consumption |
| OpenCode Go refill schedule | Operator input | Predict Go availability |
| Anthropic/OpenAI plan details | Operator input | Quota limits for $20 tier monitoring |

### 5.2 Script: Hermes Log Sampler

```bash
python3 ~/.config/model-scan/scripts/log_sampler.py
```

Extracts representative sample from Hermes agent.log. Shows first 20 events per category (errors, warnings, tool_calls, fallbacks, timeouts) and model usage counts.

### 5.3 Script: Session Activity Analyzer

```bash
python3 ~/.config/model-scan/scripts/session_analyzer.py
```

Analyzes session activity over past 30 days. Reports: total sessions, peak daily/peak hour, avg session size, concurrent peak estimate, model usage counts.

### 5.4 Script: Quota Capacity Estimator

```bash
python3 ~/.config/model-scan/scripts/quota_capacity.py
```

Estimates total concurrent session capacity based on provider quotas. Default calculation: ~19,000+ daily requests → ~190 session-hours → ~20 concurrent sessions (10hr day).

---

## 6. Implementation Roadmap (Addendum)

| Phase | Description | Duration | Dependencies | Deliverables |
|-------|-------------|----------|-------------|-------------|
| Phase 8 | Logfile Mining System | 1 weekend | Phase 2 | hermes_extractor.py, persistence_scorer.py, config_impact_analyzer.py, mining_rules.yaml, model_issue_scores.json |
| Phase 9 | Dynamic Config Generation | 1 weekend | Phase 5, Phase 8 | config-generate mode, templates, pre-run hooks, config_changelog.jsonl |
| Phase 10 | Concurrent Session Management | 1 weekend | Phase 6, Phase 9 | quota_ledger.json, session_pool.yaml, session-aware gateway, priority/preemption logic |

### Phase 8: Logfile Mining System
- [ ] Create ~/.config/model-scan/extractors/ directory
- [ ] Write hermes_extractor.py
- [ ] Write cc_extractor.py
- [ ] Write codex_extractor.py
- [ ] Create mining_rules.yaml with default rules R001-R010
- [ ] Write persistence_scorer.py
- [ ] Write config_impact_analyzer.py
- [ ] Add cron: `0 */6 * * * python3 ~/.config/model-scan/persistence_scorer.py`
- [ ] Add cron: `0 2 * * * python3 ~/.config/model-scan/config_impact_analyzer.py`
- [ ] Validate against 1 week of Hermes logs
- [ ] Verify owl-alpha structured output errors detected with P > 0.5

### Phase 9: Dynamic Config Generation
- [ ] Create ~/.config/model-scan/templates/ directory
- [ ] Write template-primary.yaml
- [ ] Write template-worker-a.yaml
- [ ] Write template-worker-b.yaml
- [ ] Add config-generate mode to model-scan CLI
- [ ] Implement slot resolution with issue score integration
- [ ] Implement fallback chain construction with diversity enforcement
- [ ] Implement config hydration pipeline (validate → inject → deduplicate → emit)
- [ ] Implement content hash and change detection
- [ ] Write pre-run hook scripts
- [ ] Test: compare generated config to hand-authored v38
- [ ] Test: simulate Go exhaustion, verify auto-removal

### Phase 10: Concurrent Session Management
- [ ] Write quota_ledger.json schema and initialization
- [ ] Write session_pool.yaml
- [ ] Add session-aware tracking to gateway /route endpoint
- [ ] Implement quota-aware allocation algorithm
- [ ] Implement priority system (P0-P3)
- [ ] Implement preemption logic
- [ ] Add per-session quota to /quota endpoint
- [ ] Add /swap with session granularity
- [ ] Load test: 20 concurrent sessions across 3 machines
- [ ] Verify no per-model quota exceeds daily limit
- [ ] Verify P0 sessions always get S/A-tier under contention

---

*This addendum assumes full completion of Phases 1-7 from the Model-Scan Refinement Guide v2. When all phases (1-12) are complete, model-scan will be a fully autonomous model management system that generates optimal configs on demand, manages quota across 20+ concurrent sessions, detects and corrects persistent issues from real usage data, probes coding endpoint capabilities before assignment, and serves as the unified gateway for Hermes, Claude Code, Codex, OpenCode, and Pi Agent — all visible through a live web UX dashboard.*

---

## 7. Coding Endpoint Capability Detection

### 7.1 Why Capability Detection Matters for Dynamic Configs

Dynamic config generation (Section 1) cannot produce optimal configs if it only knows whether a model is UP — it must know what the model can DO. A model that passes a health probe but lacks function calling support is useless for the MCP slot; a model that lacks structured output will fail silently in the approval slot. The dynamic config generator must have endpoint capability data to make informed slot assignments.

This is especially critical for new models like HY3-Preview ($0.06/$0.28/M, A-tier) — before it can be assigned to any slot, model-scan must verify that it supports the required capabilities for that slot. The cost of testing is negligible (~3,000 tokens for a full fleet probe), but the cost of NOT testing is silent failures in production.

### 7.2 Integration with Config Generation

The config-generate pipeline (Section 1.2) is extended with a new step between "probe all providers" and "compute fitness scores":

```
1. Probe all providers for health and quota
2. ★ Probe all candidate models for capabilities (NEW)
3. Load tier registry and historical failure data
4. Compute fitness scores (now includes capability_match_multiplier)
5. Assign best-fit model to each slot (with capability gating)
6. Construct fallback chains (respecting capability requirements)
7. Emit valid Hermes config YAML
```

The capability data is stored in `~/.config/model-scan/endpoint_capabilities.json` and is refreshed on the same schedule as the daily scan. When a new model is added to the tier registry (like HY3-Preview), it is probed immediately upon first appearance.

### 7.3 Cockpit Tools Integration

On machines where cockpit tools are available, model-scan can delegate endpoint probing to the cockpit infrastructure. This is preferable when:

1. The machine has cockpit tools installed and configured
2. Cockpit tools can access endpoints that model-scan cannot (e.g., internal endpoints behind VPN)
3. Cockpit tools provide richer capability data than a simple API probe

The integration path:

```python
def get_capabilities(model_name, provider):
    if cockpit_tools_available():
        result = subprocess.run(
            ["cockpit-tools", "endpoint-test", "--json", model_name],
            capture_output=True, text=True
        )
        return parse_cockpit_output(result.stdout)
    else:
        return endpoint_prober_native(model_name, provider)
```

### 7.4 Capability-Aware Fitness Formula Extension

The composite fitness formula from Section 4.1 of the base guide gains a new multiplier:

```
fitness = tier_anchor_score
        * aa_current_multiplier
        * historical_failure_multiplier
        * historical_issue_multiplier    # from logfile mining (Section 3)
        * latency_consistency_multiplier
        * provider_hour_availability
        * (1 + slot_specific_arch_bonus)
        * (1 + weight_toolcalling * (tc_score / 100))
        * capability_match_multiplier    # NEW: from endpoint probing
```

Where `capability_match_multiplier` is:
- 1.0 if the model has all hard-gate capabilities for the slot
- 0.0 if the model is missing any hard-gate capability (EXCLUDED)
- 0.3-0.7 if some non-hard-gate capabilities are missing (penalized)

### 7.5 Phase Extension

Add to Phase 9 (Dynamic Config Generation):
- [ ] Integrate endpoint_capabilities.json into slot resolution algorithm
- [ ] Add capability_match_multiplier to fitness computation
- [ ] Add capability gating to config validation step
- [ ] Test: verify HY3-Preview is only assigned to slots it supports
- [ ] Test: verify owl-alpha is excluded from MCP slot (missing parallel_tool_calls)

---

## 8. Live Web UX Dashboard

### 8.1 Dashboard as the Operational Interface for Dynamic Configs

The dynamic config generation system (Section 1) produces configs that change based on real-time conditions. But if the operator cannot see the current state or the projected next state, they are flying blind. The live web dashboard is the operational interface that makes the dynamic config system observable and controllable.

The dashboard serves three functions relative to dynamic config generation:

1. **Visibility**: Shows what configs are currently deployed and what models are assigned. This is critical when configs change automatically — the operator needs to know what changed and why.

2. **Projection**: Shows the projected next-deployment config based on current consumption rates. This lets the operator anticipate changes and intervene proactively (e.g., "OR free quota is draining fast — should I ration sessions or let the system auto-promote HY3-Preview?").

3. **Control**: Allows the operator to trigger a config regeneration, swap a model, or pin a specific model to a slot. Without this, the dynamic system is a black box that the operator cannot override.

### 8.2 Dashboard Panels for Dynamic Config Management

| Panel | Data Shown | Dynamic Config Connection |
|-------|-----------|--------------------------|
| Provider Status | Real-time health of all providers | Determines which models are available for config generation |
| Quota Tracker | Remaining quota per provider/model | Drives the quota-aware fitness formula |
| Countdown Timers | Time until refill/reset | Predicts when exhausted providers will become available |
| Current Configs | Deployed config YAMLs with slot assignments | Shows the output of the last config-generate run |
| Next Deployment | Projected config diff | Previews what config-generate will produce next |
| Config Changelog | History of all config changes | Audit trail for automatic and manual changes |
| Session Pool | Active sessions with models and priorities | Shows what's consuming quota right now |

### 8.3 Next-Deployment Projection Algorithm

The next-deployment config is computed by:

1. Reading the current quota_ledger.json (total consumption today)
2. Estimating the consumption rate per model (requests/hour from recent history)
3. Projecting quota remaining at the next scheduled config-generate time
4. Running the slot resolution algorithm with projected quota values
5. Diffing the result against the current deployed config

Example projection output:
```
NEXT DEPLOYMENT (projected for 06:00 UTC):
  Changes from current config-primary v39:
    - R3_fallback: kimi-k2.6:free → hy3-preview (OR K2.6 quota at 12%)
    - R4_fallback: V4-Flash:free → hy3-preview (OR V4-Flash free quota at 8%)
    - R6_fallback: M2.5:free → hy3-preview (OR M2.5 quota at 15%)
  No changes for config-worker-a (OR paid quota healthy)
  No changes for config-worker-b (Ollama Cloud refills at 14:00 UTC)

  Projected cost impact: +$0.02/hr (HY3 at $0.06/$0.28/M vs free OR models)
  Recommendation: Accept auto-promotion or ration OR free quota
```

### 8.4 Dashboard as a Concurrent Session Manager

The dashboard also serves as the visual interface for the concurrent session management system (Section 2). It shows:

1. All active sessions with their model assignments and priority levels
2. Per-session quota consumption (how much of each provider's quota each session is using)
3. Session preemption events (when a P0 session preempts a P2 session's model)
4. Quota allocation recommendations (which sessions should be moved to different models)

### 8.5 Integration with Logfile Mining

The dashboard surfaces the results of logfile mining (Section 3) in a dedicated panel:

| Panel | Data Shown |
|-------|-----------|
| Issue Heatmap | Models × Slots grid, color-coded by persistence score |
| Top Issues | Highest persistence_score (model, slot, category) triplets |
| Fix Recommendations | Auto-generated and manual fix records |
| Regression Monitor | Before/after failure rates for recent config changes |

### 8.6 Phase Extension

Add to Phase 10 (Concurrent Session Management):
- [ ] Add /api/sessions endpoint to dashboard backend
- [ ] Add session list panel to dashboard frontend
- [ ] Add /api/configs/next endpoint with projection algorithm
- [ ] Add next-deployment diff panel to dashboard frontend
- [ ] Add issue heatmap panel from logfile mining results
- [ ] Add /api/swap endpoint with confirmation UI
- [ ] Add config changelog viewer
- [ ] Deploy dashboard on coordinator machine (port 8765)
- [ ] Test: verify next-deployment projection matches actual config-generate output
