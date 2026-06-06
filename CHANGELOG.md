# Changelog

All notable changes to model-scan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - v5.0.0

### Added
- **claude-code-proxy routing snapshot producer** (`routing_snapshot.py`, `dink.py --emit-snapshot`) — Emits credential-free `routing_snapshot.json` using the shared contract in `contracts/routing_snapshot.schema.json`, with per-role ranked candidates, provider health, blocklist export, atomic writes, and contract tests.
- **Gateway routing snapshot endpoint** (`GET /routing-snapshot`) — Serves the latest emitted snapshot and rebuilds from SQLite when the file is missing.
- **Router reliability feedback endpoint** (`POST /reliability`) — Persists claude-code-proxy reliability summaries and feeds provider error/rate-limit rates into future snapshot provider-health status.
- **Cron snapshot emission** (`cron_manager.py`) — Daily and weekly cron defaults now include `--emit-snapshot`; `dink.py` accepts `--no-color` for those existing cron arguments.
- **Dashboard UX polish** — auto-refresh toggle (30s interval), session detail modal with quota ledger, config diff viewer modal, issue distribution bar chart
- **Daily mode config generation** — generates all templates (primary, worker-a, worker-b) during `--mode daily` scan, writing to `generated/config-{template}.yaml`
- **Improved Hermes log model extraction** — captures `:free` suffix, `model_name=` syntax, provider-prefixed models (nvidia/, openrouter/, z-ai/, etc.), and special cases (openai-codex)
- **Concurrent session management** — `session_manager.py` provides session priority queue, quota ledger (SQLite), provider slot allocation with per-tier concurrency limits, and preemption logic for idle/low-priority sessions
- **Quota ledger** — tracks token usage, cost, and provider slot allocations per session with aggregate summaries by provider
- **Provider slot allocation** — per-provider concurrency limits by tier (S/A/B/C) with capacity checking and auto-preemption
- **Preemption engine** — identifies idle/low-priority sessions as preemption candidates when provider capacity is exhausted, with cooldown gating
- **Gateway quota endpoints** — `GET /quota/ledger` (provider/session token usage), `POST /sessions/{session_id}/release` (release provider slots), `GET /session-recommendations` (zombie detection, preemption suggestions)
- **Enhanced `/sessions` endpoint** — now returns state counts (active/idle/paused), program breakdown, provider slot usage, quota summary, and management recommendations
- **Enhanced `/sessions/{session_id}` endpoint** — merges filesystem session data with quota ledger
- **Session management dashboard card** — shows provider slot usage (used/limit with % fill), quota cost breakdown by provider, and management recommendations
- **Daily mode session pool snapshot** — `dink.py --mode daily` now prints total/active/idle/paused counts with top 3 recommendations
- **AA cache freshness multiplier** — `get_aa_current_multiplier()` decays intelligence score based on AA data age
- **Slot-specific architecture bonus** — `get_slot_arch_bonus()` with special combos (MoE+compression, multimodal+vision, dense+tool)
- **Gateway API** (`gateway.py`) — 7 endpoints: `/health`, `/models`, `/route`, `/quota`, `/programs`, `/swap`, `/iqtc` with standalone FastAPI server on port 8124
- **Gateway web dashboard** (`gateway_dashboard.html`) — real-time HTML dashboard served by gateway with provider health, quota, programs, conflicts, slot routing, and model table with tier/provider filters
- **Multi-program status in daily mode** — program health summary in `--mode daily` output
- **Multi-program footer** — Kiro credits warning and OCGo exhaustion alert in scan footer
- **Cron job launcher** — `cron_manager.py` CLI (`--cron-set`/`--cron-remove`/`--cron-install`/`--cron-uninstall`), `GET /cron` endpoint, dashboard cronCard, TUI CronModal + `k` binding
- **Dashboard micro-animations** — card hover lift, content fade-in, pulse on cron status dots, animated bar-fill transitions, empty state SVG icons with warning symbol
- **Connection status indicator** — green/red dot + online/offline label in dashboard header
- **TUI Tab focus cycling** — Search → List → Detail → Compare panels via Tab key
- **TUI Ctrl+S export** — save filtered model list to `~/.config/model-scan/tui_export_{ts}.json`
- **TUI StatusBar mode display** — color-coded sort key, filter mode, active preset shown in footer
- **TUI `_ensure_extractors_path()`** — deduplicated `sys.path.insert(0, ...)` across capability functions

### Fixed
- **Slot fitness calculation** — replaced static 5% arch bonus with slot-specific `get_slot_arch_bonus()`
- **Color constants** — replaced removed `C.UNDERLINE` references with `C.ACCENT`
- **check_provider_health() SQL target** — corrected query from `scans` (no provider/scan_time columns) to `models` table with COALESCE for NULL safety
- **Duplicate except block removed** — dead `_db_save_run()` catch block removed, keeping traceback variant
- **Exit code hygiene** — `sys.exit(main())` wrapper ensures all return paths produce proper OS exit codes
- **Hermes extractor file handle** — `open()` moved outside inner loop, opened once per batch
- **Config generation return type** — returns `(yaml_string, resolution_dict)` tuple so changelog summaries get real data
- **Session manager heuristic** — JSON content parsed before 100-byte size check (small valid sessions no longer misclassified)
- **ISO timestamp crash** — `_safe_ts()` helper with try/except guards all `datetime.fromisoformat()` calls
- **Config generator endpoint validation** — `_validate_inferred_endpoint()` warns on likely-wrong guessed API keys/base URLs
- **Cron manager zombie Popen** — `proc.kill(); proc.wait(5)` in TimeoutExpired handler
- **Duplicate TPS fallback** — removed redundant `if not d.tps and aa.get("median_tps"):` block in dossier loop

### Added
- **Multi-axis scoring engine** — 4-axis (Intelligence/Speed/Agentic/Coding) with 16 cross-influence modifiers and full trace recording
- **Gold standard generator** (`--gold-standard`) — LLM-style config patches with reasoning traces per slot
- **CPMR evaluator** (`--cpmr`) — Config Patch Match Rate, compares automated vs gold standard
- **Auto-optimization loop** (`--optimize`) — grid search over weights to maximize CPMR
- **Independent audit system** (`--audit`) — tier accuracy, false positives/negatives, provider bias, coverage gaps, score drift
- **Textual TUI** (`--tui`) — keyboard-driven terminal UI with model list, detail pane, compare mode
- **Iterative refinement pipeline** (`--refine`) — hermes heartbeat cron job (weekly: scan → gold standard → CPMR → audit → patch)
- **Scoring engine integration** (`--score-engine`) — selectable scoring backend for slot fitness
- **FastAPI REST API** — 10 endpoints returning scan data, model details, slots, compare, history, providers, config diffs
- **SvelteKit 5 web UX** — dashboard with bento layout, GSAP animations, radar charts, compare mode with PNG export
- **Design system** — Lexend/DM Sans/JetBrains Mono font trio, 5-state buttons, skeleton shimmer, staggered entrance animations
- **Web UX integration tests** (`test_api.py`) — 41 tests covering all endpoints, filters, pagination, CORS (100% passing)
- **Supplemental benchmarks** — BFCL v3 (10 models), Arena ELO (9 models), Terminal-Bench expanded (5 models)
- **OpenCode Go, OpenCode Zen, Kilo Gateway providers** — 3 new providers, 10 total scan sources
- **Hermes heartbeat config** — weekly scheduled refinement via `~/.config/model-scan/heartbeat_config.yaml`

### Fixed
- **Model detail API** — switched to `path` converter for model IDs with slashes
- **CORS middleware** — changed to allow all origins (`*`)
- **Compare endpoint** — made `models` parameter optional (returns empty array)
- **Slot list API** — returns proper list format matching frontend expectations
- **Benchmarks reader** — handles nested dict structures in benchmarks.json

### Added
- **TUIDS-LLM color system** — full implementation of 9 semantic roles with belt-and-suspenders dim
  - ERROR (red), WARN (amber), SUCCESS (green), INFO (cyan), METRICS (blue), ACCENT (pink)
  - Glyph prefixes on all semantic signals (✓ ✗ ⚠ → ◆)
  - Belt-and-suspenders dim: always pairs `\e[2m` with explicit darker color
- **One unified table** — all models in single scrollable table, sorted by Tier + Composite Score
- **Tier grading system** — S/A/B/C based on composite score
  - S: ≥89 (better than MiniMax-2.7 baseline)
  - A: 84-89 (MiniMax-2.7 baseline)
  - B: 70-83 (functional)
  - C: 55-69 (limited use)
  - —: ungraded
- **Role classification** — primary, reasoner, fast, vision, code, hybrid, general
- **AA benchmark integration** — Artificial Analysis scores (ai, ac, am, mmlu)
- **models.dev integration** — context limits, pricing, capabilities via API
- **API key health reporting** — identifies failing keys with causes
- **Concurrent scanning** — semaphore-controlled parallelism (8 concurrent requests)
- **Unicode animation layer** — Braille spinner cycle during probes
- **Request ID disambiguation** — 4-char hex rid prefix per scan batch
- **OpenRouter free models** — auto-fetched from API and included
- **History tracking** — last 30 runs persisted to `~/.config/model-scan/results.json`
- **Edge case handling** — NO_COLOR, TERM=dumb, piped output, narrow terminal

### Changed
- Complete rewrite from v2 → v3
- Color system now follows TUIDS-LLM specification
- Table format: TIER | MODEL | ROLE | LAT | T/S | AA | STATUS
- Removed separate sections — now single unified list
- Provider detection now uses global env + .env files

### Fixed
- OpenRouter model name format — now uses full `provider/model-id` format
- API key loading from multiple .env locations
- Duplicate model detection across providers
- Free model tagging (`:free` suffix)

### Removed
- Rich library dependency (now uses raw ANSI)
- Separate "working-only" list (now filtered via `-w` flag)

---

## [2.x] - Previous Versions

See session history for v2 changes.

---

## Principles

- **Sacred content**: Model names and paths receive zero ANSI codes
- **60-30-10 enforcement**: 60% neutral, 30% active signal, 10% exceptional
- **4-hue ceiling**: Max 4 signal hues visible in any viewport
- **Glyph redundancy**: Every color paired with a symbol
- **Motion semantic**: Spinner = in-progress, static glyph = terminal state
