# Changelog

All notable changes to model-scan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - v5.0.0

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
