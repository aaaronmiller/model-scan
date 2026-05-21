# model-scan v5: Implementation Tasks
## Generated from requirements.md + design.md — Phase 1: Web UX

---

## Priority & Effort Key

| Icon | Meaning |
|------|---------|
| 🔥 P0 | Must-have for v5 launch |
| ⭐ P1 | Core value, ship in v5 |
| 📦 P2 | Important but can follow |
| 🧊 P3 | Icebox / nice-to-have |

| Effort | Range |
|--------|-------|
| 🟢 <2h | Quick win |
| 🟡 2-8h | Focused build |
| 🔴 8-24h | Multi-session |
| ⚫ 24h+ | Major feature |

---

## TASK 1: Project Scaffold — SvelteKit + shadcn-svelte
**🔥 P0** | Effort: 🟡 4h

| Step | What | Verification |
|------|------|-------------|
| 1.1 | `npx sv create web` — minimal skeleton + TypeScript + Tailwind | `npm run dev` starts clean |
| 1.2 | `npx shadcn-svelte init` — defaults | Components install without error |
| 1.3 | Add deps: `chart.js`, `svelte-chartjs`, `lucide-svelte` | Import works in `+page.svelte` |
| 1.4 | Configure SvelteKit adapter (node for dev, static for deploy) | `build/` dir produced |
| 1.5 | Set up Tailwind v4 with shadcn theme (dark mode toggle) | Dark/light class toggles on `<html>` |

**Depends on:** Nothing
**Files:** `web/` directory, `package.json`, `svelte.config.js`, `tailwind.config.js`

---

## TASK 2: FastAPI REST Backend
**🔥 P0** | Effort: 🟡 6h

| Step | What | Verification |
|------|------|-------------|
| 2.1 | Create `api/main.py` with FastAPI app + CORS | `uvicorn main:app` starts |
| 2.2 | Add `/api/v1/scan/latest` — read latest scan from SQLite | Returns JSON with models + fitness |
| 2.3 | Add `/api/v1/scan/history` — scan timestamps + counts | Returns list of scan summaries |
| 2.4 | Add `/api/v1/models` — all models with filters + pagination | Supports `?sort=tps&tier=S&limit=20` |
| 2.5 | Add `/api/v1/models/:id` — single model detail with all scores | Returns dossier JSON |
| 2.6 | Add `/api/v1/slots` — slot definitions with incumbents | Returns slot names + current model |
| 2.7 | Add `/api/v1/slots/:id` — slot detail with candidate rankings | Returns top 10 candidates per slot |
| 2.8 | Add `/api/v1/compare?models=a,b,c` — comparison data | Returns 4-axis scores + benchmarks |
| 2.9 | Add `/api/v1/providers` — provider health from scan results | Returns list with status colors |
| 2.10 | Add `/api/v1/config/preview` — generate YAML patch | Returns diff string |

**Depends on:** SQLite database from model-scan (`~/.config/model-scan/model_scan.db`)
**Files:** `api/main.py`, `api/requirements.txt`

---

## TASK 3: Dashboard Page (`/`)
**🔥 P0** | Effort: 🟡 8h

| Step | What | Verification |
|------|------|-------------|
| 3.1 | SectionCards — 4 KPI cards (model count, slots, providers, alerts) | Numbers update from API |
| 3.2 | ChartAreaInteractive — fitness score trend over last 10 scans | Line chart renders with axes |
| 3.3 | TopModelsTable — top 10 models by composite score (DataTable) | Sortable by tier/TPS/latency |
| 3.4 | Provider health row — color dots for each provider | Green/yellow/red per provider |
| 3.5 | RadarChart — mini-radar for top 3 models (spider chart) | 4 axes: IQ, Speed, Agentic, Coding |
| 3.6 | Auto-refresh button + last scan timestamp footer | Shows "scanned at 2026-05-17 14:30" |
| 3.7 | Dark mode toggle in header | Persists to localStorage |

**Depends on:** Task 1 (scaffold), Task 2 (API)
**Files:** `src/routes/+page.svelte`, `src/lib/components/dashboard/`

---

## TASK 4: Model List Page (`/models`)
**⭐ P1** | Effort: 🟡 6h

| Step | What | Verification |
|------|------|-------------|
| 4.1 | Fetch all models from `/api/v1/models` | JSON loads on mount |
| 4.2 | shadcn-svelte DataTable with columns: tier, model, provider, TPS, latency, tools, vision, price, benchmark, slots | All columns render |
| 4.3 | Column sorting by click (asc/desc toggle) | Sort indicator in header |
| 4.4 | Filter bar: provider dropdown, tier badge selector, search input | Filters reduce table rows |
| 4.5 | Click row → navigate to `/models/:id` | Route works |
| 4.6 | Color-coded tier badges (S=orange, A=green, B=cyan, C=gray) | Badges match dink.py colors |

**Depends on:** Task 2 (API), Task 3.3 (DataTable base)
**Files:** `src/routes/models/+page.svelte`, `src/lib/components/models/`

---

## TASK 5: Model Detail Page (`/models/:id`)
**⭐ P1** | Effort: 🟡 4h

| Step | What | Verification |
|------|------|-------------|
| 5.1 | Fetch single model from `/api/v1/models/:id` | All fields render |
| 5.2 | Model identity card: provider, arch, params, context window | Card layout with shadcn-card |
| 5.3 | Radar chart miniature (IQ, Speed, Agentic, Coding) | 4-axis spider, colored fill |
| 5.4 | Score breakdown tabs: Intelligence, Speed, Agentic, Coding | Each tab shows modifier trace |
| 5.5 | Benchmark scores: SWE-Verified, SWE-Pro, Terminal-Bench badges | Colored badges (S/A/B/C) |
| 5.6 | Slot match table: which slots this model qualifies for | Table with fitness scores |
| 5.7 | "Copy model ID" + "View on provider" buttons | Clipboard API works |

**Depends on:** Task 4 (model list), Task 2.5 (API)
**Files:** `src/routes/models/[id]/+page.svelte`

---

## TASK 6: Slot Detail Page (`/slots/:id`)
**⭐ P1** | Effort: 🟡 6h

| Step | What | Verification |
|------|------|-------------|
| 6.1 | Fetch slot detail from `/api/v1/slots/:id` | Candidates + incumbent render |
| 6.2 | Slot metadata card: min_ai, min_tps, max_latency, needs_tools/vision | All gates displayed |
| 6.3 | Candidate table: rank, model, provider, fitness, breakdown | Fitness stacked bar (intel/speed/reliability) |
| 6.4 | Fitness breakdown bar: intel (blue) + speed (green) + reliability (yellow) stacked | Tooltip shows exact values |
| 6.5 | Incumbent marker: ✓ badge on current config model | Incumbent row highlighted |
| 6.6 | Config patch preview: YAML diff (current vs recommended) | Diff view with green/red lines |
| 6.7 | "Apply to config" button (writes YAML patch) | Confirmation dialog before write |

**Depends on:** Task 2.7 (API), Task 3.3
**Files:** `src/routes/slots/[id]/+page.svelte`

---

## TASK 7: Compare Mode (`/compare`)
**⭐ P1** | Effort: 🟡 6h

| Step | What | Verification |
|------|------|-------------|
| 7.1 | Multi-select panel: search + pick 2-5 models | Chip display for selected |
| 7.2 | Radar chart: overlay 2-5 models on 4 axes with filled polygons | Hover tooltip per model |
| 7.3 | Comparison table: side-by-side columns per model | Intel, Speed, Agentic, Coding, Context, Price, SWE-V, Tools, Vision |
| 7.4 | Export as PNG (radar chart download) | `canvas.toBlob()` download |
| 7.5 | Shareable URL: `/compare?models=a,b,c` | Loads comparison from params |

**Depends on:** Task 2.8 (API), Task 5.3 (radar component)
**Files:** `src/routes/compare/+page.svelte`

---

## TASK 8: Scan History (`/scan/history`)
**📦 P2** | Effort: 🟡 4h

| Step | What | Verification |
|------|------|-------------|
| 8.1 | Fetch history from `/api/v1/scan/history` | Timestamps + model counts |
| 8.2 | Line chart: top-5 model fitness over time | 5 colored lines, legend |
| 8.3 | Table: scan rows (date, models, healthy, degraded, failed) | Sorted by date desc |
| 8.4 | Click scan row → `/scan/history/:id` with detail | Single-scan drill-down |

**Depends on:** Task 2.3 (API)
**Files:** `src/routes/scan/history/+page.svelte`

---

## TASK 9: Config Preview & Apply (`/config`)
**📦 P2** | Effort: 🟡 4h

| Step | What | Verification |
|------|------|-------------|
| 9.1 | Fetch config patch preview from `/api/v1/config/preview` | YAML diff string renders |
| 9.2 | Code block with syntax-highlighted diff (green/red lines) | Line numbers + +/- markers |
| 9.3 | "Apply Changes" button → writes to `~/.hermes/config.yaml` | Backup original first |
| 9.4 | "Revert" button → restore from backup | Backup file is used |
| 9.5 | Status message: "Applied ✓" or error message | Toast notification |

**Depends on:** Task 2.10 (API)
**Files:** `src/routes/config/+page.svelte`

---

## TASK 10: Provider Status (`/providers`)
**📦 P2** | Effort: 🟢 2h

| Step | What | Verification |
|------|------|-------------|
| 10.1 | Fetch providers from `/api/v1/providers` | List renders |
| 10.2 | Provider cards with status dot (green/yellow/red/gray) | Color per status |
| 10.3 | Last-checked timestamp per provider | "3h ago" relative time |
| 10.4 | Model count per provider | Number badge |
| 10.5 | "Run Scan" button per provider | Triggers scan (async) |

**Depends on:** Task 2.9 (API)
**Files:** `src/routes/providers/+page.svelte`

---

## TASK 11: Animations & Visual Polish
**⭐ P1** | Effort: 🟡 6h

| Step | What | Technique |
|------|------|-----------|
| 11.1 | Dashboard entry fade-in for SectionCards | `svelte/transition` fade 300ms staggered |
| 11.2 | DataTable row entrance animation (list items enter left) | `svelte/transition` slide, 50ms interval |
| 11.3 | Radar chart area appear animation (fill grows from center) | Chart.js animation `duration: 800` |
| 11.4 | Page transitions between routes (fade + slight scale) | SvelteKit `beforeNavigate` + CSS transition |
| 11.5 | Button press feedback (scale 0.97 on mousedown) | CSS `:active { transform: scale(0.97) }` |
| 11.6 | Skeleton loading states (pulsing gray blocks) | shadcn-svelte `Skeleton` component |
| 11.7 | Theme toggle animation (icon rotation + smooth color change) | CSS `transition: background-color 0.3s` |
| 11.8 | Micro-interactions: hover lift on cards | `translateY(-2px)` + shadow on hover |

**Depends on:** Tasks 3-10
**Files:** `src/app.css` (global transitions), component-level styles

---

## TASK 12: FastAPI Integration Tests
**⭐ P1** | Effort: 🟡 4h

| Step | What | Verification |
|------|------|-------------|
| 12.1 | Test `/api/v1/scan/latest` returns valid JSON | Status 200, has `models` key |
| 12.2 | Test `/api/v1/models` pagination (limit/offset) | Correct slice returned |
| 12.3 | Test `/api/v1/models?tier=S` filter | Only S-tier models returned |
| 12.4 | Test `/api/v1/slots/:id` returns candidates | Top candidate has highest fitness |
| 12.5 | Test `/api/v1/compare?models=a,b` returns both models | 2 model objects in response |
| 12.6 | Test error handling (invalid model ID → 404) | Proper error JSON |
| 12.7 | Test CORS headers present | `Access-Control-Allow-Origin: *` |

**Depends on:** Task 2 (all endpoints built)

---

## Implementation Order (Recommended Sequence)

```
Week 1                          Week 2
┌─────────────┬─────────────┐  ┌─────────────┬─────────────┐
│ TASK 1      │ TASK 2      │  │ TASK 4      │ TASK 6      │
│ Scaffold    │ FastAPI     │  │ /models     │ /slots/:id  │
│ (4h)        │ (6h)        │  │ (6h)        │ (6h)        │
├─────────────┼─────────────┤  ├─────────────┼─────────────┤
│ TASK 3      │ TASK 5      │  │ TASK 7      │ TASK 11     │
│ Dashboard   │ /models/:id │  │ /compare    │ Animations  │
│ (8h)        │ (4h)        │  │ (6h)        │ (6h)        │
└─────────────┴─────────────┘  └─────────────┴─────────────┘

Week 3
┌─────────────┬─────────────┐
│ TASK 8      │ TASK 9      │
│ /history    │ /config     │
│ (4h)        │ (4h)        │
├─────────────┼─────────────┤
│ TASK 10     │ TASK 12     │
│ /providers  │ Tests       │
│ (2h)        │ (4h)        │
└─────────────┴─────────────┘
```

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | FastAPI (Python) | Same Python process as model-scan; direct SQLite reads |
| Frontend | SvelteKit 5 | Runes-based reactivity, shadcn-svelte, minimal boilerplate |
| Charts | Chart.js | Lightweight, radar/line/bar support, canvas-based |
| CSS | Tailwind v4 + shadcn | Design tokens, dark mode, utility-first |
| API style | REST (no GraphQL) | Direct mapping to SQLite queries, simple caching |
| Real-time | Server-Sent Events | Simpler than WebSocket for scan progress |
| State mgmt | Svelte 5 runes | `$state`, `$derived`, `$effect` — no external stores |
| Config apply | Backend file write | FastAPI writes YAML, creates `.bak` before edit |
