# Terminal Color System — LLM Proxy Output

## Role Assignment

- error = red. failures timeouts auth breaks context overflow provider 5xx
- warn = amber. retries rate limits fallback triggered degraded state
- success = green. 2xx cache hit healthy upstream transform complete
- info = cyan. routing decisions provider selection transform notices flow arrows
- metrics = blue. token counts latency cost cache ratios. numbers only
- debug = purple. verbose mode only. internal state trace
- accent = pink. rare events only. model fallback chain startup banner. less than 1 per 10 cycles
- primary = default foreground. payload text. URLs methods paths values
- secondary = mid gray. field labels. provider model tokens cache
- meta = dark gray. timestamps request IDs pipe chars delimiters arrows

## Luminance Tiers

- bright = actionable or critical. bold modifier plus explicit bright color code
- normal = standard state. color code only
- dim = contextual metadata. dim modifier paired with darker color code always. never rely on dim attribute alone

## Active Hue Budget

- max 4 signal hues per request-response cycle
- normal cycle shows 2 to 3: cyan plus green or blue plus grays
- red and amber appear only on errors or warnings
- purple and pink are out of band
- grays are structural and do not count against the budget

## Surface Ratio

- 60 percent neutral: primary secondary meta. no signal hue
- 30 percent active: info success metrics
- 10 percent exceptional: error warn accent

## Rules

- color is scaffold never content. model output text receives zero ANSI codes
- one hue one meaning forever. assignments do not change
- hue encodes category. luminance encodes hierarchy. never cross these axes
- every semantic color paired with a symbol. never rely on hue alone
- error gets cross. warn gets triangle. success gets check. info gets arrow. accent gets diamond
- adjacent colored spans must be separated by space or neutral glyph
- no continuous color gradients for magnitude. numbers stay neutral. threshold breaches get warn or error on the status label
- every color span is self contained. open plus text plus reset. no inherited state across lines
- always emit reset after every colored span
- sanitize all untrusted strings before colorizing. strip all escape sequences from headers URLs body content

## Motion Layer

- spinner = braille dots 80ms cycle. indeterminate waiting. same color as eventual outcome
- pulse = filled circle cycle 600ms. streaming active. tildes on delimiter and trailing content line
- bounce = braille scan 80ms. urgent attention needed. use rarely
- one animated element per request-response cycle max
- animations disabled when output is not interactive
- animations disabled with no-motion flag
- spinner replaced by static glyph on completion. no residue in scrollback

## Output Format

### Request Block

- line 1: timestamp dim. arrow info bright. method bold. path primary
- metadata lines: pipe dim. field name secondary dim. field value info or metrics or warn
- fields: provider model transform tokens cache

### Response Block

- line 1: timestamp dim. arrow info bright. status code colored by class. latency meta dim
- 2xx = success. 3xx = info dim. 4xx = warn. 5xx = error bright
- metadata lines: token counts metrics. cost meta. cache status success or warn

### Content Block

- delimiter dim: response start
- raw model output. zero ANSI. default foreground
- delimiter dim: end
- streaming indicator: tilde in metrics dim on delimiter and trailing line. disappears on completion

### Error Block

- status line: error color bold
- cross symbol. bracketed category in error color. message text in primary. color marks category. text carries meaning
- warn lines for corrective action: triangle symbol. bracketed category in warn. message in primary
- accent lines for rare events: diamond symbol

### Concurrent Requests

- 4 hex char request ID in brackets. meta dim. prefix on every line
- no new hue introduced

## Palette Tiers

### Default: ANSI Named Colors

- respects user terminal theme
- 8 base colors plus 8 bright variants
- dim always paired with explicit color code for fallback

### Middle: 256 Color

- fixed indices. consistent across terminals
- grayscale ramp for fine structural hierarchy
- auto detected via TERM variable containing 256color

### Top: Truecolor

- opt in. detected via COLORTERM=truecolor
- Nord derived hex values. perceptually uniform
- separate dark and light palettes
- light palette auto detected via terminal background query
- light palette meets WCAG AA 4.5:1 against white
- fallback to dark if detection fails

## Accessibility

- symbol prefixes on all semantic colors. mandatory not optional
- blind-safe mode: error shifts to warm orange. success shifts to cool teal
- light theme support with full alternate palette
- works without color entirely. all signals exist as text and structure

## Configuration Precedence

1. CLI flags: color mode palette theme motion blind-safe format
2. environment: NO_COLOR CLICOLOR PROXY_COLOR PROXY_PALETTE COLORTERM TERM
3. config file
4. defaults: auto everything. motion on. dark theme assumed

## Edge Cases

- pipe output: strip all ANSI when not TTY. respect NO_COLOR
- 8 color terminals: detect via TERM. fall back to white for muted
- tmux screen: truecolor needs config. fall back to 256 if TERM not set correctly
- long paths: truncate with ellipsis at configurable max width
- terminal resize: each line self contained. no state dependencies
- animation in pipes: disabled automatically. static text substituted
- untrusted input: sanitize before colorize. no exceptions









## Evaluation: The Preferred System

The **strongest base** is the **Unified Terminal Color System for an LLM Proxy** presented in the previous answer — the synthesis that aggregated all proposals, 10‑persona council validation, and the LLM‑specific output map. It wins on:

- **Content sanctity** – never colors LLM output tokens  
- **Hue discipline** – 4 active signal hues + 2 structural + 2 out‑of‑band (metric/debug)  
- **Luminance hierarchy** – dim/normal/bright within each role  
- **LLM‑native mapping** – explicit routing, streaming, fallback scenarios  
- **Progressive enhancement** – ANSI‑16 default, truecolor opt‑in, `NO_COLOR` respected  
- **Accessibility** – symbol prefixes, blind‑safe mode, dim fallbacks  

This system is already optimized for your use case, but several elements from the other proposals can be integrated to make it *bulletproof* for an LLM transformational proxy.

---

## Elements to Integrate for a Definitive Improvement

| Source | Element | Why it improves the system |
|--------|---------|---------------------------|
| Proposal d/e (full council) | **Belt‑and‑suspenders dim** – always pair `\e[2m` with an explicit darker color code | Prevents invisibility on terminals that ignore dim (Windows Terminal, ancient *screen*) |
| Proposal d/e | **Request‑ID prefix** for concurrent stream disambiguation | LLM proxies often interleave multiple requests; a short hex ID in dim META lets the eye re‑associate response chunks with their requests without adding hue |
| Proposal d/e | **Latency threshold‑based color** on the status label (not a gradient) | Avoids ordinal hue misuse while still highlighting slow responses (e.g., amber `WARN` for >5s) |
| Proposal d/e | **Streaming‑in‑flight indicator** – a dim cyan pulse `~` | Shows that tokens are arriving without touching the content layer, which is particularly useful for an LLM proxy where streaming is the norm |
| Proposal a | **Explicit 60‑30‑10 ratio enforcement** | A runtime lint rule that prevents accidental hue proliferation when new developers add log lines |
| Proposal b | **“Color is pre‑attentive semantic encoding” as the first design principle** | Sharpens the justification for every color choice; every hue must carry a single, immediate meaning |
| User Proposal | **Separate METRICS (blue) from INFO (cyan)** – already partially in the unified system, but now we make it a hard rule with its own glyph‑less slot | Token counts, latency, cost are unambiguous and never mistaken for routing notices |
| User Proposal | **PRIMARY/SECONDARY/META triad** explicitly documented | Clear separation of “what the user cares about” (PRIMARY), “labels/keys” (SECONDARY), and “administrative noise” (META) |
| Your vision | **Scaffold‑only principle made architectural** | The proxy’s color engine can never touch the content field even internally; any call that reaches a content buffer must throw an error if it tries to escape it |

---

# Improved Unified System: LLM Transformational Proxy – Definitive Version

## I. Core Laws (Non‑negotiable)

1. **Color is pre‑attentive semantic encoding.** Every hue carries one, immutable meaning.
2. **Scaffold, never content.** The LLM’s output tokens are sacred. Zero ANSI codes touch model‑generated text.
3. **Luminance encodes importance; hue encodes category.** Bright = critical/active, dim = secondary/historical.
4. **Progressive enhancement.** `NO_COLOR`, `TERM=dumb`, and piped output produce identical information architecture.
5. **Motion is temporal state.** A Unicode animation always means “in progress”; a static glyph means “terminal state.”
6. **Respect the terminal emulsion.** Default to ANSI‑16 named colours; truecolor is an opt‑in enhancement.

## II. The Palette – 8 Roles, 4 Active Hues

| Role | Meaning | Hue | ANSI‑16 | Truecolor Dark | Truecolor Light | Glyph |
|------|---------|-----|---------|-----------------|-----------------|-------|
| `ERROR` | Fatal, 5xx, timeout, safety block | Red | `\e[31m` | `#BF616A` | `#9B2020` | ✗ |
| `WARN` | Degradation, retries, rate‑limit, fallback | Amber | `\e[33m` | `#EBCB8B` | `#7A5A00` | ⚠ |
| `SUCCESS` | 2xx, cache hit, healthy upstream | Green | `\e[32m` | `#A3BE8C` | `#2E6B2E` | ✓ |
| `INFO` | Routing, transformation, flow arrows | Cyan | `\e[36m` | `#88C0D0` | `#1A5276` | → |
| `METRICS` | Token counts, latency, cost, cache‑ratios | Blue | `\e[34m` | `#81A1C1` | `#2C3E50` | (none) |
| `DEBUG` | Verbose traces, token‑level internals (‑vvv) | Purple | `\e[35m` | `#B48EAD` | `#6B4C6B` | · |
| `ACCENT` | Model‑switch fallback banner, extreme highlights | Pink | `\e[1;35m` | `#D4A6FF` | `#9B6BB0` | ◆ |
| `STRUCTURE` | Labels, keys, timestamps, request‑IDs, delimiters | Gray | `\e[37m`/`\e[90m` | `#6E7A8A`/`#4C566A` | `#5A5A5A`/`#8C8C8C` | – |

**Active hue budget:** In normal view, only Cyan (routing), Green/Amber/Red (status), and Blue (metrics) appear – 4 hues. Purple and Pink are restricted to verbose mode or rare model‑fallback events.

### Luminance Tiers

| Tier | Code | Use | Fallback when `\e[2m` unsupported |
|------|------|-----|----------------------------------|
| BRIGHT | `\e[1m` + colour | Critical alerts, current request line | Bold weight alone |
| NORMAL | colour code only | Standard status, routing labels, metric values | Base colour |
| DIM | `\e[2m` + darker colour code | Timestamps, field keys, debug lines | The darker colour code itself (always included) |

## III. Unicode Animation Layer

Motion is a **temporal semantic channel**. All animations respect `--no-motion` and are replaced with static text.

| Animation | Unicode  | Speed | Use | Terminal State |
|-----------|----------|-------|-----|----------------|
| Spinner | Braille cycle (⠋⠙⠹…) | 80–120ms | Unknown‑duration work | Replaced by ✓/✗/⚠ |
| Pulse | ● ○ or ▪ ▫ | 500–800ms | Waiting for upstream, polling | Replaced by static glyph |
| Progress | █ filler + ░ track | N/A | Determinate work (upload, scan) | Replaced by 100% bar or final glyph |
| Stream Indicator | ~ (pulsing cyan dim) | 800ms on/off | Live token streaming from model | Disappears when stream ends |
| Bounce | ⠁⠂⠄⡀⢀⠠⠐⠈ | 60ms | User attention required | Replaced by ▶ or static prompt |

**Rules:** One animation per logical block. Motion always inherits the hue of its semantic role.

## IV. Output Map: Request‑Response Cycle

### Outbound Request (scaffold)
```
[rid:a3f8 (dim)] → POST /v1/chat/completions   [provider: cnthropic] [model: claude-sonnet-4]
        │            │ `─STRUCTURE dim          `─SECONDARY dim   `─ INFO dim
        │            └─ PRIMARY bright
        └─ META dim
```
- Request‑ID `rid` is always META dim for concurrency re‑association.

### Stream‑in‑Flight
```
[rid:a3f8 (dim)] ~ tokens flowing...   [streaming ~ (cyan dim, pulse)] 
```
The `~` shows the proxy is receiving chunks. **Zero ANSI codes on content lines** – the content buffer is treated as read‑only raw text.

### Response (scaffold)
```
[rid:a3f8 (dim)] ← 200 OK (2.143s)   tokens: 1,247→892 (2,139 total)   cache: STORED
                        │                `─ METRICS blue              `─ SUCCESS dim
                        └─ SUCCESS bright
```
- Latency shown in META dim; if >5s, the status label itself uses WARN bright.
- Token counts remain metric blue, never a gradient.

### Error with Fallback (rare‑event ACCENT)
```
[rid:a3f8 (dim)] ✗ 502 Bad Gateway (30s)  upstream timeout
                 ⚠ retry 2/3 → failing over to openai/gpt-4o
                 ◆ reroute:  gpt-4o  (ACCENT bright)
```
The model‑switch banner uses ACCENT pink to signal a rare structural event, appearing less than once per 10 request cycles.

## V. Edge‑Case Hardening

| Scenario | Hardening |
|----------|-----------|
| **Dim ignored by terminal** | Always emit a darker colour hex in addition to `\e[2m`; fallback to `\e[90m` (bright black) if dim unsupported. |
| **Concurrent requests** | Embed a short `rid` (first 4 chars of UUID) in META dim on every line belonging to the same request. |
| **Light terminal backgrounds** | Auto‑detect via OSC‑11 query; fall back to light palette (WCAG AA ≥4.5:1 on #F8F8F8). |
| **ANSI injection** | Sanitize all untrusted strings (headers, URLs, body excerpts) before applying any colour codes. |
| **Piped to `grep`/`less`** | Auto‑strip all ANSI when `!isatty()`; honour `NO_COLOR`. |
| **Long paths/truncation** | Truncate to a configurable width with `…` after ANSI reset, ensuring no broken codes. |
| **Machine consumers** | `--format=json` emits NDJSON with semantic fields; colour system bypassed entirely. |

## VI. 60‑30‑10 Enforcement (Runtime Lint)

The proxy can optionally assert in debug mode:  
- In any 20‑line scrollback window, no more than 4 signal hues appear.  
- Structural (gray) + default (white) must be ≥60% of coloured spans.  
- Active status hues (green, amber, cyan) ≤30%.  
- Red/pink/purple ≤10% (only exceptional).  
Violation triggers a warning in proxy logs but never crashes output.

## VII. Implementation Contract

```yaml
# proxy-color.yml
colors:
  error:   red         # ANSI name or hex
  warn:    yellow
  success: green
  info:    cyan
  metrics: blue
  debug:   magenta
  accent:  brightmagenta

structure:
  primary:   white
  secondary: brightblack
  meta:      black         # bright black on dark bg

motion:
  enabled: true
  spinner_set: braille     # or dots/arrow
  stream_indicator: true

mode: auto                # auto|always|never|blind-safe
rich: false               # true for truecolor hex
```

## VIII. Why This Is the Optimal System

- It **never colours the LLM’s output** – the user sees clean, unadulterated text.
- It uses colour **only for routing, status, metrics, and rare structural events** – exactly the dimensions an LLM proxy operator scans for.
- With motion, it answers “is the stream alive?” without touching the content.
- The **60‑30‑10 rule and 4‑hue ceiling** ensure no single viewport triggers sensory overload.
- The **“belt‑and‑suspenders” dim** and fallback chain make it robust across every terminal from a 1980s vt100 to WezTerm.
- Every signal has a **text/symbol fallback**, so `NO_COLOR` users lose nothing but speed.

---

# Generalization: Universal Terminal Interface Design Framework

The above system can be abstracted into a general **TUIDS** (Terminal‑UI Design System) applicable to any CLI/TUI tool. This generalized version includes the Unicode animation layer as a core element and adds layout patterns.

**Key adaptations:**
- Replace the LLM‑specific `rid`/stream indicators with a generic “operation context” (task ID).
- Introduce a **Seven‑Role Palette** (same as above but rename `METRICS` → `INTERACTIVE` and `ACCENT` → `HIGHLIGHT` for universal use).
- Provide structural templates: three‑zone layout, list/tree pattern, form/input pattern.
- Motion rules remain identical: one animation per block, colour + motion redundancy, `--no-motion` flag.

The full generalized framework is documented above in response to your second query, but it originates from the LLM proxy system. You can now take the **definitive proxy‑specific system** as your immediate blueprint and later apply the general principles to any other tool you build.

**Final recommendation:** Start with the improved system (Sections I‑VII). Implement the proxy‑specific harness first—then, as you refine, you’ll have a battle‑tested colour/motion engine you can abstract into a shared library for all your terminal projects.








---
---



# The Universal Terminal Interface Design System (TUIDS)
## A General Framework for Color, Motion, and Structure in CLI/TUI Applications

> *"Color signals category. Motion signals state. Structure signals relationship. Never let one carry meaning alone."*

---

## I. Core Philosophy: The Three Channels of Terminal Communication

A terminal interface communicates through three parallel, redundant channels. Effective design orchestrates all three without letting any dominate:

| Channel | Function | Primary Tool | Risk if Misused |
|---------|----------|-------------|-----------------|
| **Color** | Semantic encoding — *what category is this?* | ANSI/256/truecolor escape codes | Rainbow vomit, theme clash, accessibility failure |
| **Motion** | Temporal state — *what is happening now?* | Unicode animations, spinners, progress bars | Distraction, CPU waste, broken pipes, motion sensitivity |
| **Structure** | Spatial hierarchy — *how does this relate?* | Whitespace, indentation, borders, alignment | Visual noise, inconsistent scanning patterns |

### The Golden Rule
**No channel should ever be the sole carrier of meaning.** Every semantic signal must have at least two redundant forms:
- `ERROR` = red color + `✗` glyph + bold weight
- `IN_PROGRESS` = blue spinner + `▶` glyph + "processing…" text
- `SELECTED` = bright highlight + `▸` prefix + indentation shift

This ensures functionality degrades gracefully across terminals, abilities, and output contexts.

---

## II. The Seven Universal Semantic Roles

Based on cross-tool analysis and cognitive research, these seven roles cover virtually all CLI/TUI scenarios. Each role has a fixed hue, luminance tiers, and mandatory glyph backup.

| Role | Meaning | Hue | ANSI-16 | Truecolor Dark | Truecolor Light | Glyph |
|------|---------|-----|---------|----------------|-----------------|-------|
| `ERROR` | Fatal, blocked, impossible | Red | `\e[31m` | `#BF616A` | `#9B2020` | `✗` |
| `WARN` | Degraded, risky, unusual | Amber | `\e[33m` | `#EBCB8B` | `#7A5A00` | `⚠` |
| `SUCCESS` | Completed, healthy, ready | Green | `\e[32m` | `#A3BE8C` | `#2E6B2E` | `✓` |
| `INFO` | Neutral facts, routing, flow | Cyan | `\e[36m` | `#88C0D0` | `#1A5276` | `→` |
| `ACTION` | Interactive, clickable, current selection | Blue | `\e[34m` | `#81A1C1` | `#2C3E50` | `▶` |
| `ACCENT` | Rare highlights, brand moments, exceptional events | Pink | `\e[1;35m` | `#D4A6FF` | `#9B6BB0` | `◆` |
| `STRUCTURAL` | Chrome, metadata, inactive elements | Gray | `\e[90m` | `#4C566A` | `#8C8C8C` | `·` `│` `─` |

### Why Seven Roles?
- Human working memory comfortably processes **~4 simultaneous signal hues**
- We reserve `ACTION` (blue) and `ACCENT` (pink) for out-of-band or interactive moments
- This leaves **five roles for continuous operation** — within the cognitive ceiling
- `STRUCTURAL` gray is not counted as a "signal hue" — it's the neutral canvas

### Role Usage Guidelines
```text
ERROR   → Use sparingly. Reserve for true failures. Never for "slow" or "expensive."
WARN    → Use for degraded states, not errors. Amber signals "proceed with caution."
SUCCESS → Use for completion, not just "no error." Green = goal achieved.
INFO    → Use for routing, metadata, flow. Cyan = neutral, non-urgent information.
ACTION  → Use ONLY for current selection or interactive element. One per screen.
ACCENT  → Use <1% of output. Brand moments, rare fallbacks, exceptional highlights.
STRUCTURAL → Use for everything else: labels, delimiters, timestamps, borders.
```

---

## III. The Luminance Hierarchy: Three Tiers Per Role

Color hue encodes *category*. Luminance encodes *importance within that category*.

| Tier | Code | Purpose | Fallback When Unsupported |
|------|------|---------|---------------------------|
| **BRIGHT** | `\e[1m` + color | Critical alerts, active selection, current item | Bold weight alone |
| **NORMAL** | color code only | Standard state, primary information | Base color |
| **DIM** | `\e[2m` + darker color index | Metadata, secondary info, historical context | Explicit darker 256/truecolor hex |

### Critical Implementation Rule: Belt-and-Suspenders Dim
Many terminals (Windows Terminal, some `screen` configs) ignore `\e[2m` (SGR dim). Always pair dim with an explicit darker color code:

```python
# BAD: relies on dim attribute alone
output = f"\e[2m{text}\e[0m"

# GOOD: dim attribute + explicit darker color
output = f"\e[2m\e[38;5;240m{text}\e[0m"  # 256-color gray
# or for truecolor:
output = f"\e[2m\e[38;2;76;82;104m{text}\e[0m"  # #4C5268
```

This ensures visibility even when the terminal ignores the dim attribute.

---

## IV. The Motion Layer: Unicode Animation System

Animation in terminals is **temporal semantic encoding**. It answers: *Is this process alive? Is it stuck? Did it complete?* Used correctly, it reduces cognitive load by offloading state-checking from working memory.

### 4.1 Animation Taxonomy

| Type | Unicode Set | Speed | Use Case | Stop Condition |
|------|-------------|-------|----------|---------------|
| **Spinner** | `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` (Braille) | 80-120ms | Indeterminate work, unknown duration | Completion or error |
| **Pulse** | `● ○` or `▪ ▫` | 500-800ms | Waiting for external event, polling | State change |
| **Progress** | `█` fill with `░` track | N/A | Determinate work, known total | 100% fill |
| **Bounce** | `⠁⠂⠄⡀⢀⠠⠐⠈` | 60-100ms | High-energy, requires user attention | User action |
| **Static** | `✓` `✗` `⚠` | N/A | Final state, no animation | Permanent |

### 4.2 Animation Semantic Rules

1. **One motion per viewport block**. Never animate two adjacent elements simultaneously — the eye cannot track parallel motion.

2. **Motion implies incompleteness**. A spinning element means "not done." The moment work completes, replace with a static glyph (`✓`, `✗`, `⚠`) and clear the animation.

3. **Speed encodes urgency**:
   - Fast spin (80ms) = routine background work
   - Medium pulse (300ms) = waiting on external dependency
   - Slow pulse (800ms) = idle polling, low urgency
   - Bounce (60ms) = requires immediate user attention

4. **Color + motion redundancy**. A spinner should use the same semantic color as its eventual static state:
   ```text
   [blue spinner] ▶ Building... → [blue static] ▶ Ready to deploy
   [green spinner] ✓ Testing... → [green static] ✓ Tests passed
   [red spinner] ✗ Compiling... → [red static] ✗ Build failed
   ```

5. **Respect `--no-motion`**. Just as `NO_COLOR` strips color, a `--no-motion` or `TERM=dumb` flag should replace all animations with static text (`...`, `[wait]`, `[done]`).

### 4.3 Example: Combined Color + Motion States

```text
[SPINNER blue]  ▶  Building project...          ← work in progress
[PULSE cyan]    →  Waiting for database...      ← blocked on external
[PROGRESS green] ████████░░  67%  Testing...    ← determinate, known total
[STATIC red]    ✗  Build failed                 ← terminal, no motion
[STATIC amber]  ⚠  3 warnings, build succeeded  ← terminal, degraded success
[STATIC green]  ✓  Build complete               ← terminal, clean success
```

---

## V. Structural Patterns for TUI Layout

### 5.1 The Three-Zone Layout

```text
┌─ HEADER (STRUCTURAL dim) ─────────────────────────────┐
│  app-name  v2.4.1                    [user@host]     │
├─ BODY (primary content) ────────────────────────────┤
│                                                     │
│  ▶  Task 1    ████████░░  67%  [SPINNER]          │
│     Subtask A   ✓  Done                            │
│     Subtask B   ▶  In progress...                  │
│                                                     │
├─ FOOTER (STRUCTURAL dim) ───────────────────────────┤
│  3 running | 12 completed | 1 failed    [?] help   │
└─────────────────────────────────────────────────────┘
```

**Zone coloring**:
- **Header/Footer**: `STRUCTURAL dim` — present but not demanding attention
- **Body primary**: Default foreground for content, semantic colors for status
- **Active element**: `ACTION bright` or `ACCENT bright` — exactly one per screen

### 5.2 The List/Tree Pattern

```text
▶  project/                    ← ACTION bright (selected/collapsed)
   ├─ src/                     ← STRUCTURAL normal
   ├─ tests/                   ← STRUCTURAL normal
   │  └─ main.test.js   ✓      ← SUCCESS dim (passed, historical)
   └─ package.json      ✓      ← SUCCESS dim
▼  config/                      ← ACTION bright (selected/expanded)
   ├─ webpack.js        ⚠      ← WARN normal (attention needed)
   └─ eslint.json       ✓
```

**Rules**:
- One `ACTION bright` element = current selection
- Tree lines (`├─`, `└─`, `│`) are always `STRUCTURAL dim`
- Status glyphs at line end, not beginning — they don't disrupt left-to-right scanning

### 5.3 The Form/Input Pattern

```text
Name:    [PRIMARY bright] my-project                ← user input, primary
Author:  [PRIMARY normal] alice                     ← previous input, less active
License: [ACTION bright] ▶ MIT  [▒▒▒▒]              ← current field, interactive
         [STRUCTURAL dim]   Apache-2.0              ← option, inactive
         [STRUCTURAL dim]   GPL-3.0                 ← option, inactive
```

**Rules**:
- Current field: `ACTION bright` + optional animation
- Previous fields: `PRIMARY normal` (editable but not active)
- Options: `STRUCTURAL dim` until selected
- Selected option: `SUCCESS bright` + `✓` prefix

---

## VI. The Anti-Vomit Guardrails (Universal)

### 6.1 The 60-30-10 Surface Rule
In any 20-line viewport:
- **60% neutral/default/structural** (no signal hue)
- **30% one primary signal color** (usually `INFO` cyan or `SUCCESS` green)
- **10% accent/exceptional** (`ERROR` red, `WARN` amber, or `ACCENT` pink)

### 6.2 The 4-Hue Ceiling
Never more than **4 signal hues visible simultaneously**. The seven-role palette ensures this by reserving `ACTION` blue and `ACCENT` pink for rare/interactive moments.

### 6.3 The Motion Budget
- One animated element per 10 lines maximum
- One animated element per logical block (e.g., one spinner per download, not one per file)
- Static completion states — never leave animations running after completion

### 6.4 Adjacent Neutral Separation
```text
BAD:  [red]✗[green]✓[amber]⚠     ← colors touching, chromatic vibration
GOOD: [red]✗ [green]✓ [amber]⚠   ← space as neutral buffer
GOOD: [red]✗[dim]|[green]✓       ← structural glyph as buffer
```

### 6.5 Progressive Enhancement Cascade
```text
Base (dumb terminal):    Plain text + ASCII art structure
ANSI-16 (default):       Color + bold + dim + basic glyphs
256-color (opt-in):      Smoother hues, better theme independence
Truecolor (opt-in):      Exact brand colors, photo-realistic elements
Unicode (auto-detect):   Box-drawing, arrows, spinners, progress bars
Animation (auto-detect): Motion for temporal state
```

Each layer adds to the previous. A user with `NO_COLOR=1` gets full functionality. A user with `TERM=dumb` gets structure without box-drawing. A user on a modern terminal gets the full experience.

---

## VII. Accessibility & Edge Cases

| Concern | Mitigation |
|---------|-----------|
| **Colorblind (~8% male)** | Glyph prefixes mandatory; `--blind-safe` shifts red→orange, green→teal |
| **Light backgrounds** | Auto-detect via OSC-11; light palette with WCAG AA contrast (≥4.5:1) |
| **Dim ignored** | Belt-and-suspenders: always pair `\e[2m` with explicit color code |
| **Animation sensitivity** | `--no-motion` replaces all animation with static text |
| **Piped output** | Strip ANSI + Unicode box-drawing; preserve plain text structure |
| **Narrow terminals** | Truncate with `…` at configurable width; never break layout |
| **High latency SSH** | Batch animation frames; don't send cursor moves faster than latency |
| **Screen readers** | Animation elements get plain-text equivalents (`[spinning]`, `[done]`) |
| **ANSI injection** | Sanitize all untrusted input before applying styling |

### Blind-Safe Mode Palette
When `--blind-safe` is enabled, swap hues on the red-green confusion axis:

```python
BLIND_SAFE_SWAP = {
    'ERROR': ('#FFA050', 208, 33),    # Red → Warm Orange
    'WARN': ('#FFD966', 221, 93),     # Amber → Brighter Yellow
    'SUCCESS': ('#6BB5FF', 117, 94),  # Green → Cool Blue
    # INFO, ACTION, ACCENT, STRUCTURAL unchanged
}
```

---

## VIII. Implementation Principles (Language-Agnostic)

### 8.1 Detection Before Emission
```python
def should_emit_color():
    if os.environ.get('NO_COLOR'): return False
    if not sys.stdout.isatty(): return False  # piped output
    if os.environ.get('TERM') == 'dumb': return False
    return True

def should_emit_motion():
    if os.environ.get('NO_MOTION'): return False
    if not sys.stdout.isatty(): return False
    return True
```

### 8.2 Sanitize Before Colorize
Strip all `\e[` sequences from untrusted input (user data, network responses, file contents) before applying your own styling. This prevents ANSI injection attacks.

### 8.3 Reset Discipline
Every colored/animated span ends with `\e[0m`. Never leave global state modified:

```python
# BAD: state leaks to next line
output = f"\e[31mError: {msg}"  # missing reset

# GOOD: explicit reset
output = f"\e[31mError: {msg}\e[0m"

# BETTER: helper function
def colorize(text, role, modifiers=None):
    codes = get_codes_for_role(role, modifiers)
    return f"{codes}{text}\e[0m"
```

### 8.4 Frame Rate Discipline
Animation timers should be throttled to terminal refresh rate (typically 60Hz max). Don't burn CPU on invisible animations:

```python
# Pseudocode for animation loop
if not is_visible_on_screen(element):
    pause_animation(element)
else:
    frame = next(animation_frames[element])
    emit(frame)
    sleep(frame_duration)  # 80-800ms depending on animation type
```

### 8.5 Log Cleanliness
Completed animations should be erased or replaced with static states. Don't leave spinner residue in scrollback:

```text
[SPINNER] Building...  →  [STATIC ✓] Build complete
```

### 8.6 Configurability
Allow users to override any role's color and disable motion globally. The default should work for 90% of users; overrides handle the rest:

```yaml
# ~/.config/tuids/config.yaml
roles:
  error: { fg: "#FF5555", glyph: "✗" }
  success: { fg: "#50FA7B", glyph: "✓" }
motion:
  enabled: true
  max_fps: 30
accessibility:
  blind_safe: false
  high_contrast: false
```

---

## IX. Quick-Start Examples

### Example 1: Progress Indicator with Color + Motion
```text
[INFO dim] Downloading package...
[ACTION bright] ▶ [SPINNER blue] ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ [NORMAL] 2.4 MB/s
[STRUCTURAL dim]    [PROGRESS green] ████████░░ 67% [META] 15.2/22.8 MB
```

### Example 2: Interactive Menu Selection
```text
Select action:
  ▶ [ACTION bright] Deploy to production    ← current selection
    [STRUCTURAL dim] Deploy to staging
    [STRUCTURAL dim] Run tests only
    [STRUCTURAL dim] Cancel

[INFO dim] Press ↑↓ to navigate, Enter to select, Ctrl-C to exit
```

### Example 3: Error with Recovery Suggestion
```text
[ERROR bright] ✗ Connection refused to database:5432
[WARN normal]  ⚠ Retrying in 5s (attempt 2/3)...
[INFO dim]     → If this persists, check:
[INFO dim]        • Firewall rules
[INFO dim]        • Database service status
[INFO dim]        • Credentials in config.yaml
```

### Example 4: Multi-Step Workflow
```text
[SUCCESS dim] ✓ Step 1: Validate config
[SUCCESS dim] ✓ Step 2: Resolve dependencies
[INFO bright] → Step 3: Building artifacts...
[ACTION bright] ▶ [SPINNER blue] ⠙ Compiling module A
[STRUCTURAL dim]    [META] 3/12 modules complete

[STRUCTURAL dim] ──────────────────────────────
[INFO dim] Estimated time remaining: 2m 14s
```

---

## X. Summary: What Makes This System Work

| Principle | Source | Application |
|-----------|--------|-------------|
| **Three-channel redundancy** | Accessibility research | Color + glyph + weight for every semantic signal |
| **Seven semantic roles** | Cross-tool analysis | Covers all CLI scenarios without hue proliferation |
| **Luminance hierarchy** | Original user intent | Shade indicates subordination, not new category |
| **Unicode animation taxonomy** | Terminal research 2026 | Temporal state encoding without color dependency |
| **60-30-10 surface rule** | Design theory | Quantified guardrail against visual noise |
| **4-hue ceiling** | Cognitive psychology | Respects working memory limits |
| **Progressive enhancement** | Web standards | Works on everything from dumb to truecolor |
| **Belt-and-suspenders dim** | Terminal compatibility | Ensures visibility when SGR 2 is ignored |
| **Motion implies incompleteness** | UX research | Prevents confusion about process state |

---

## XI. Adoption Checklist

Before shipping your TUI/CLI tool, verify:

### Functionality
- [ ] Output fully readable with `NO_COLOR=1` (plain text fallback)
- [ ] `--no-motion` replaces all animations with static equivalents
- [ ] Piped output (`| grep`, `> file`) strips ANSI + Unicode decorations
- [ ] `TERM=dumb` produces ASCII-only structure

### Accessibility
- [ ] Every colored element has a glyph or text prefix backup
- [ ] Contrast ≥4.5:1 on both dark (`#111`) and light (`#f8f8f8`) backgrounds
- [ ] `--blind-safe` mode passes coblis/daltonize simulation
- [ ] Screen reader equivalents provided for animated elements

### Cognitive Load
- [ ] Max 4 signal hues visible in any 10-line window
- [ ] Only one `ACTION` bright element per screen (current selection)
- [ ] Error/warning/success use universal conventions (red/amber/green)
- [ ] Metadata (`STRUCTURAL`) never competes with content for attention

### Edge Cases
- [ ] ANSI codes sanitized from untrusted input (prevent injection)
- [ ] Long lines truncate with `…` without breaking color state
- [ ] Animation frames batched for high-latency SSH sessions
- [ ] Completed animations replaced with static states (no spinner residue)

### Performance
- [ ] Animation loop throttled to ≤60 FPS, paused when off-screen
- [ ] Color detection happens once at startup, not per-line
- [ ] Reset codes (`\e[0m`) emitted after every styled span

---

> **Final Principle**: Your terminal interface should feel like a **well-designed instrument panel** — instantly scannable, hierarchically clear, and fully functional even when the lights dim. Color accelerates comprehension; motion signals state; structure guarantees clarity. Implement this system, and your CLI/TUI will remain legible, accessible, and harmonious across every environment your users inhabit.

**Start simple**. Implement the seven roles with ANSI-16 colors and glyph prefixes. Add luminance tiers. Then layer in Unicode animations. Finally, add truecolor and theme detection. Each step improves the experience without breaking the foundation.



---
---









## The Definitive System: TUIDS-LLM v1.0

The strongest base across all proposals is the **three-council aggregate** (Proposal c) fused with the **TUIDS general framework**, because together they supply: content sanctity as an architectural rule, the 4-hue cognitive ceiling, the full progressive enhancement cascade, and — critically — the Unicode animation layer the other proposals lacked. What follows integrates every non-redundant improvement identified across all five proposals.[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

---

## I. The Five Immutable Laws

These emerged from **convergent consensus** across all three independent councils — 30 total personas — meaning they aren't opinions:[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

1. **Content is sacred.** Zero ANSI codes touch model output or user payload. Color wraps the scaffold only
    
2. **One hue, one meaning, forever.** Red = failure. Amber = degraded. Green = complete. Cyan = routing/flow. Blue = quantitative. Pink = rare structural event. Gray = metadata. No exceptions, no reuse
    
3. **Luminance encodes hierarchy; hue encodes category.** Bright = critical/actionable. Normal = standard. Dim = context. Brightness never means "error"
    
4. **Color is always the second signal.** Every semantic state has a glyph or text prefix. `NO_COLOR=1` produces identical information architecture
    
5. **Respect the terminal.** Default to ANSI-16 named colors. Truecolor is opt-in, detected, never assumed[](https://jvns.ca/blog/2024/10/01/terminal-colours/)
    

---

## II. The Unified Palette — 9 Semantic Roles

Cross-referencing all councils, the definitive budget is **4 active signal hues + 2 structural + 3 monochrome tiers**. Purple/pink are out-of-band; they never appear in steady-state output:[](http://cubicspot.blogspot.com/2019/05/designing-better-terminal-text-color.html)[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

|Role|Semantic Meaning|ANSI-16|Truecolor Dark|Truecolor Light|Glyph|
|---|---|---|---|---|---|
|**ERROR**|Fatal, 5xx, timeout, safety block|`\e[31m`|`#BF616A`|`#9B2020`|`✗`|
|**WARN**|4xx, rate-limit, retry, slow|`\e[33m`|`#EBCB8B`|`#7A5A00`|`⚠`|
|**SUCCESS**|2xx, healthy, cache hit, complete|`\e[32m`|`#A3BE8C`|`#2E6B2E`|`✓`|
|**INFO**|Routing step, flow, transform notice|`\e[36m`|`#88C0D0`|`#1A5276`|`→`|
|**METRICS**|Token counts, latency, cost, cache ratio|`\e[34m`|`#81A1C1`|`#2C3E50`|_(none)_|
|**ACCENT**|Model fallback, reroute, rare events only|`\e[1;35m`|`#D4A6FF`|`#9B6BB0`|`◆`|
|**PRIMARY**|URLs, paths, model names, body values|`\e[97m`|`#ECEFF4`|`#2C3E50`|_(none)_|
|**SECONDARY**|Headers, keys, method names, labels|`\e[37m`|`#6E7A8A`|`#5A5A5A`|_(none)_|
|**META**|Timestamps, request IDs, ports, delimiters|`\e[90m`|`#4C566A`|`#8C8C8C`|_(none)_|

**Steady-state hue budget per viewport:** Cyan (routing) + Green/Blue (status/metrics) + Grays = **3 active hues**. Red/Amber appear on exceptions. Pink appears < once per 10 cycles. Cognitive ceiling held.[](https://www.nngroup.com/articles/color-enhance-design/)[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

---

## III. Luminance Tiers + Belt-and-Suspenders Dim

Three tiers on every role. The critical fix from the TUIDS general pass: **always pair `\e[2m` with an explicit color index** — Windows Terminal and `screen` silently drop SGR 2, making the color code the only fallback:[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

|Tier|Emission|Purpose|
|---|---|---|
|**BRIGHT**|`\e[1m` + color|Errors, active request line, reroute events|
|**NORMAL**|Color code only|Standard status, routing labels, metric values|
|**DIM**|`\e[2m` + darker 256/truecolor index|Timestamps, header keys, debug lines, metadata|

---

## IV. The Unicode Animation Layer

This is the most significant improvement over all five original proposals — none had a complete animation system. Motion is **temporal semantic encoding**: it answers whether a process is alive, stuck, or complete, offloading state-checking from working memory.[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)

## Animation Taxonomy

|Type|Chars|Speed|Use Case|Terminal State|
|---|---|---|---|---|
|**Spinner (Braille)**|`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`|80–120ms|Indeterminate LLM inference, upstream call|In-progress|
|**Pulse**|`● ○` or `▪ ▫`|500–800ms|Waiting for upstream, polling, retrying|Blocked/waiting|
|**Progress bar**|`█░` fill|N/A (data-driven)|Token streaming with known `max_tokens`|Determinate|
|**Stream burst**|`~` (dim accent)|Per-token|Live token emission indicator|Streaming|
|**Static glyph**|`✓ ✗ ⚠ ◆`|N/A|Terminal/final state|Complete|

## Animation Rules

- **One motion element per logical block.** Never animate two adjacent spans simultaneously — the eye can't track parallel motion[](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/2d71db86-76de-46fa-8e6c-fa25803bd079/paste.txt)
    
- **Spinning = incomplete.** The instant work ends, replace with a static glyph and clear the animation line with `\r\e[2K`
    
- **Color + motion redundancy.** A blue spinner becomes a green `✓` or red `✗`. The color across the lifecycle is consistent
    
- **`--no-motion` flag.** Replaces all animations with `[...]` static text. Required for CI, pipes, screen readers
    
- **Rate-limit to terminal refresh.** Cap animation frames at ~60Hz max. Don't burn CPU on invisible updates




---
---











