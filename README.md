# model-scan

Model Scan is a local evidence and decision-support system. It discovers exact
provider model identities, combines published and observed evidence, evaluates
role fixtures, and publishes immutable advisory results. Gateway owns live
routing, fallback, and configuration changes. ARDF owns its research ledger,
calibration policy, Pareto analysis, and dashboard.

The canonical requirements and design are under
`/home/cheta/LIVING_DOCUMENTS/projects/model-scan`. Older v5 scoring and config
preview surfaces remain in this checkout as migration evidence. A preview is
not authority to apply a route or configuration.

## Quick Start

```bash
# Install
pip install --user httpx pyyaml python-dotenv
chmod +x dink.py
ln -s "$(pwd)/dink.py" ~/.local/bin/model-scan

# Set at least one API key
export OPENROUTER_API_KEY=sk-or-v1-...    # free models available
export OPENCODE_GO_API_KEY=ocgo_...        # subscription models
export AA_API_KEY=aa_...                   # benchmark data (free tier)

# Run
model-scan                                # full scan
model-scan --slot S01_haiku              # single current slot analysis
model-scan --free-mode                    # free models only
model-scan --emit-snapshot                # write ~/.config/model-scan/routing_snapshot.json
model-scan --analyze                      # multi-source analysis
model-scan --tui                          # keyboard terminal UI
```

## Features

### Core (CLI — 33 commands)
| Command | Description |
|---------|-------------|
| `model-scan` | Full scan across all configured providers |
| `--slot R1` | Candidates for a specific Hermes task slot |
| `--free-mode` | Only probe/evaluate free-whitelisted models |
| `--emit-snapshot [PATH]` | Emit the claude-code-proxy routing snapshot contract |
| `--score-engine` | Multi-axis scoring (Intel/Speed/Agentic/Coding) |
| `--gold-standard` | Generate optimal config patches with reasoning traces |
| `--cpmr` | Config Patch Match Rate vs gold standard |
| `--optimize` | Grid search over slot weights |
| `--audit` | Independent verification against benchmarks |
| `--analyze` | Multi-source fused analysis (3 data sources) |
| `--popularity` | HuggingFace community adoption scores |
| `--config-snapshot` | Daily config drift tracking |
| `--tui` | Keyboard-driven terminal UI |
| `--refine` | Weekly refinement pipeline |
| `--json` | Machine-readable output |

### claude-code-proxy Routing Snapshot

`model-scan --emit-snapshot` writes a credential-free routing snapshot for
claude-code-proxy:

```bash
model-scan --mode daily --emit-snapshot
# default: ~/.config/model-scan/routing_snapshot.json
```

The gateway also serves it:

```bash
python3 gateway.py 8124
curl http://127.0.0.1:8124/routing-snapshot
```

claude-code-proxy can post reliability summaries back to the gateway:

```bash
curl -X POST http://127.0.0.1:8124/reliability \
  -H 'content-type: application/json' \
  -d '{"providers":{"openrouter":{"requests":10,"error_rate":0.1,"rate_limit_frequency":0.0}}}'
```

The gateway appends those rows to `~/.config/model-scan/reliability_feedback.jsonl` and uses the
latest provider rates to degrade provider health in rebuilt snapshots.

Daily and weekly cron jobs installed by `cron_manager.py` include `--emit-snapshot` by default.

### Clutch Capability Evidence

The successor Gateway boundary keeps capability evidence separate from callable
provider identity. Publish it from a saved dossier JSON file without probing a
provider:

```bash
python capability_evidence.py \
  --dossiers dossiers.json \
  --output ~/.config/model-scan/capability_evidence.json \
  --evidence-ref scan:2026-07-23
```

The publisher writes atomically, keeps an independent
`capability_evidence.last-known-good.json` recovery copy, and never emits
provider API IDs, endpoints, credential references, or callable IDs. Those are
joined later through the Gateway's explicit identity map. The older
`routing_snapshot.py` format remains supported for the existing default-off
integration but is not the successor callable-identity contract.

### Immutable evidence contract

The current evidence boundary is split into a content object and an external
manifest:

```bash
pytest -q test_evidence_contract.py test_ardf_export.py \
  test_role_evaluation.py test_source_adapter.py
```

- `evidence_contract.py` validates joins, freshness, exact zero price,
  privacy-safe task telemetry, role gates, and advisory-only output. It then
  computes real content and schema hashes in a separate manifest.
- `ardf_export.py` binds the current ARDF ledger, policy, schemas, executable,
  projections, and a complete field migration map.
- `role_evaluation.py` defines typed fixtures, per-call telemetry, Wilson
  confidence intervals, paired comparison rules, explicit abstention, and
  hash-pinned advisory recommendations.
- `source_adapter.py` preserves the useful Model Scraper lineage as a neutral
  Model Scan module. Catalog discovery, callable state, probe reachability,
  and policy eligibility remain separate facts.

### Data Sources
| Source | Models | Data |
|--------|--------|------|
| **Live probes** | 100+ | TPS, latency, tool-calling, vision, reliability from 10 providers |
| **Artificial Analysis** | 1,436 | Intelligence/Coding/Math Index, 15 eval benchmarks |
| **Models.dev** | 4,817 | Pricing (6 tiers), context limits, 7 capabilities, 5 modalities |
| **PinchBench** | 50 | Agent task success rates, execution cost/time, 23 task categories |
| **HuggingFace** | 16+ | Download counts, community adoption scores |

### Scoring Axes
- **Intelligence** — benchmark-normalized, with sigmoid clamping and knowledge-freshness exponential decay
- **Speed** — TPS + latency with Gaussian bell-curve penalty for too-fast/slow
- **Agentic** — tool-calling, PinchBench integration, structured output support
- **Coding** — SWE-bench verified scores, coding index, context window

### Calculus-Enhanced Metrics
Sigmoid quality scores, quadratic diminishing returns, bell-curve latency penalties, marginal intelligence per dollar (dI/dC), integral cumulative value (∫P(c)dc), gradient sensitivity analysis (∂C/∂W), tanh-latency normalization, exponential knowledge decay.

### Free-Mode Evaluation
- 52 models on free whitelist across 8 providers
- `--free-mode` restricts probing and ranking to free models
- `--refresh-free` updates whitelist from provider APIs
- Slot-level `eval_mode: cost_basis | free` in `slot_definitions.yaml`

## Architecture

```
┌─────────────────────────────────────────────┐
│  CLI (dink.py) — 33 commands               │
│  ├── Run scan (10 providers)               │
│  ├── Analysis engine (3 sources fused)     │
│  ├── Scoring engine (4 axes + calculus)    │
│  ├── Gold standard / CPMR / Audit          │
│  └── Refinement pipeline                   │
├─────────────────────────────────────────────┤
│  Web UI (SvelteKit 5)                      │
│  ├── Dashboard with ECharts radar + charts │
│  ├── Model list with preset filters        │
│  ├── Compare with radar overlay            │
│  ├── Scan history with trend lines         │
│  └── Analysis dashboard (9 chart panels)   │
├─────────────────────────────────────────────┤
│  API (FastAPI, port 8123)                  │
│  ├── /api/v1/models — filter, sort, paginate│
│  ├── /api/v1/analysis — multi-source engine │
│  ├── /api/v1/popularity — HF adoption scores│
│  ├── /api/v1/compare — multi-model radars  │
│  ├── /api/v1/refinement/history            │
│  └── 12 endpoints; current S-slot contract │
├─────────────────────────────────────────────┤
│  TUI (Textual)                             │
│  ├── Keyboard navigation (↑↓/s/f/t/p)     │
│  ├── Preset filters, provenance tags       │
│  ├── Compare mode (up to 4 models)         │
│  └── Model detail with popularity scores   │
└─────────────────────────────────────────────┘
```

## Web UI

```bash
# Start API backend
cd api && uvicorn main:app --port 8123 &

# Start web dev server
cd web && npm install && npm run dev
```

Then open `http://localhost:5173` for the main dashboard or `analysis/dashboard.html` for the ECharts analysis panels.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes* | OpenRouter API (free models available) |
| `AA_API_KEY` | No | Artificial Analysis benchmark data (free tier) |
| `OPENCODE_GO_API_KEY` | No | OpenCode Go subscription models |
| `OPENCODE_API_KEY` | No | OpenCode Zen free tier |
| `KILO_API_KEY` | No | Kilo Gateway |
| `NVIDIA_API_KEY` | No | NVIDIA NIM |
| `GROQ_API_KEY` | No | Groq LPU |
| `CEREBRAS_API_KEY` | No | Cerebras ASIC |

*At least one API key required for scanning.

## Project Structure

```
model-scan/
├── dink.py                    # Main CLI (33 commands)
├── api/main.py                # FastAPI backend (12 endpoints)
├── web/                       # SvelteKit 5 web UI
├── analysis/                  # Multi-source analysis engine
│   ├── engine.py              # Metric computation + data fusion
│   ├── dashboard.html         # ECharts interactive dashboard
│   ├── popularity.py          # HuggingFace adoption scores
│   └── refinement.py          # 4-pass deliberative refinement
├── gold_standard.py           # Config patch generator
├── cpmr.py                    # Config Patch Match Rate
├── optimize.py                # Weight grid search
├── audit.py                   # Independent audit system
├── tui.py                     # Textual terminal UI
├── refine.py                  # Weekly refinement pipeline
├── config_tracker.py          # Config drift detection
├── scoring/                   # 4-axis scoring engine
├── token-economics/           # Token economics analysis
├── archive/                   # Deprecated/old files
├── env_example.txt            # Reference env vars
├── test_api.py                # API integration tests (41)
├── .gitignore
├── LICENSE                    # MIT
├── CHANGELOG.md
├── FINAL_REPORT.md
└── README.md
```

## Tests

```bash
# Complete offline suite
pytest -q --ignore=test_api.py

# Read-only local API integration gate
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8123
python3 test_api.py
```

The API always exposes the code-owned 15-slot `S*` namespace. If its database
contains legacy or incomplete slot IDs, config preview returns an explicit
abstention instead of presenting stale recommendations as current.

## License

MIT © 2026 Aaron Miller

## Session Tasks — 2026-06-19 (14 items)

These tasks were defined during the calibration planning session. See
`docs/RAW_USER_PROMPTS_2026-06-19.md` for full verbatim source.

### P0 — Must build
- [ ] **Conditional scoring engine** (`scoring/arch_predictor.py`): Estimate AI Index
      from arch type, params, release date when AA data is missing
- [ ] **CLI overall command** (`cli_overall.py`): `model-scan overall -a --free`
      returns best model ID for tier. Done — see `cli_overall.py`

### P1 — Core improvements
- [ ] **User sentiment pipeline** (`scoring/sentiment.py`): Scrape X/Reddit for
      empirical "feels like" comparisons with region tags
- [ ] **Paper benchmark extractor** (`scoring/paper_benchmarks.py`): Extract
      benchmark tables from Kimi 2.6, GLM 5.2, Qwen 3.7, MiniMax M3 papers
- [ ] **Reliability calibration** (`scoring/reliability_calibration.py`):
      Cross-reference scores with real API error logs
- [ ] **Model size × AI Index cross-ref**: Apply size/arch data from models.dev
      to intelligence scores

### P2 — Nice to have
- [ ] **Magic factor tracking** (`empirical_adjustments.json`): Empirical
      over/underperformance deltas per model
- [ ] **Benchmark directory**: Scraped data from paper-referenced benchmark sources
