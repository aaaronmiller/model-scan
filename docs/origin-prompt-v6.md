You want one clean, self-contained project brief that a fresh model can follow from scratch, with the **authoritative table built first**, every model and graph derived from that table, no invented values, and one usable dark-mode HTML deliverable.

You are right. I failed this job badly. Do not use any of my previous generated HTML as the implementation base.

If you are experiencing real chest pain, shortness of breath, faintness, or pressure in your chest, stop working and call emergency services now.

Copy the following entire specification into a fresh model:

---

# Build the Model-Routing Evidence Dashboard From Scratch

Create a new model-routing research dashboard from a blank project. Do not repair, extend, copy, or refactor any previously generated dashboard. Previous generated artifacts contain incorrect model lists, unsupported values, broken plots, duplicated rows, and confused metrics.

The final deliverable must be a single, self-contained, dark-mode `index.html` file. It may be placed alone inside a zip file, but there must not be a maze of supporting documents. All data, prose, tables, JavaScript, CSS, source notes, and interactive charts must be embedded in the HTML.

The project’s central rule is:

**Build the canonical data table first. Derive every model list, chart, selector, frontier, role assignment, tooltip, count, and conclusion from that one table. Never maintain a separate hand-written model list.**

Do not begin drawing charts until the table has been assembled, validated, and printed for inspection.

## Purpose of the project

This dashboard should explain how model intelligence, effort level, task cost, agentic success rate, token consumption, latency, and validation requirements can be used to choose the most efficient model for a delegated task.

The dashboard must answer three practical questions:

1. What Claude Code model-and-effort configurations are actually available?
2. Which configurations or cross-provider alternatives provide the strongest capability at a given accepted task cost?
3. How should an orchestrator route general tasks and coding tasks based on empirical evidence rather than model reputation, provider labels, or token price alone?

The dashboard is evidence first and routing advice second. It must never present invented benchmark values merely to produce a visually pleasing line.

## Authoritative input files

Use these files as the supplied raw evidence:

* `artificial-analysis-operational-frontier(1).csv`
* `skatebench-official-operational-frontier(1).csv`
* `skatebench-v2-operational-frontier(1).csv`
* `frontier-visual-audit(1).csv`
* `aaa-routing-dispatch-line-graph-fixed(1).html`
* The supplied reference screenshot showing model-family lines on a cost-versus-score graph

Treat the CSV files as data sources.

Treat the reference screenshot as a visual and interaction reference only. Do not extract benchmark values from its pixels unless the same values cannot be obtained from a structured source. Any value transcribed from an image must be labeled as image-transcribed and lower confidence.

Treat the old routing HTML only as a statement of desired concepts and interface ideas. Do not trust its embedded values, model names, charts, rankings, cost coordinates, or invented models without independently validating each one.

## Required live research

The supplied Artificial Analysis CSV does not contain all Claude Code model-and-effort combinations. Use the live Artificial Analysis interface or its underlying structured data to retrieve the missing combinations.

Use the site’s dropdown selectors, page data, network responses, downloadable CSV, or browser developer tools. Record:

* Exact model name
* Exact model ID, where available
* Exact effort level
* Artificial Analysis Intelligence Index
* Artificial Analysis cost per task
* Source URL
* Retrieval date and time
* Whether the value came from a structured export, page data, API/network response, article text, or manual transcription

Do not use search-result snippets as final numeric evidence.

Do not estimate intermediate effort levels.

Do not interpolate low, medium, high, xhigh, or max values.

Do not infer that effort levels are evenly spaced.

Do not derive one model’s values from another model’s curve.

If exact structured values cannot be found, leave the field missing and explain why.

## The canonical table must come first

Before writing chart code, create one canonical JavaScript data array containing every model configuration used anywhere in the dashboard.

Each row must contain these fields:

* `row_id`
* `display_name`
* `canonical_model_id`
* `provider`
* `family`
* `effort`
* `harness`
* `is_native_claude_code_configuration`
* `is_routing_candidate`
* `aa_intelligence_index`
* `aa_cost_per_task`
* `aa_source`
* `aa_retrieved_at`
* `official_skatebench_success_rate`
* `official_skatebench_cost_per_success`
* `official_skatebench_average_cost`
* `official_skatebench_average_tokens`
* `official_skatebench_average_duration`
* `official_skatebench_tps`
* `official_skatebench_source`
* `v2_skatebench_accuracy`
* `v2_skatebench_cost_per_success`
* `v2_skatebench_average_cost`
* `v2_skatebench_average_tokens`
* `v2_skatebench_average_duration`
* `v2_skatebench_tps`
* `v2_skatebench_source`
* `combined_benchmark_cost`
* `combined_benchmark_method`
* `data_quality`
* `missing_fields`
* `frontier_status`
* `dominance_reason`
* `recommended_roles`
* `required_validator`
* `notes`

Every value must have provenance.

Missing values must remain `null`, not zero.

The visible HTML must show this canonical table before the analytical charts.

Every table must be searchable and sortable.

Each row must have a stable hover ID.

The UI must display the number of rows loaded, the number containing AA data, the number containing official SkateBench data, the number containing v2 data, and the number missing a required crosswalk.

## Claude Code native configuration table

The Claude Code native table must contain exactly these 15 configurations:

### Haiku 4.5

* Default or standard only

### Sonnet 5

* Low
* Medium
* High
* Xhigh

### Opus 4.8

* Low
* Medium
* High
* Xhigh
* Max

### Fable 5

* Low
* Medium
* High
* Xhigh
* Max

That is:

* 1 Haiku configuration
* 4 Sonnet configurations
* 5 Opus configurations
* 5 Fable configurations
* 15 total configurations

Do not omit configurations because they are dominated.

Do not replace missing native configurations with GPT, Gemini, DeepSeek, or any other provider.

Do not add Opus 4.7, Sonnet 4.6, or another historical Claude model to this native table unless it is presented separately as a historical comparison.

The table must visibly assert:

`1 + 4 + 5 + 5 = 15`

The page must fail its own validation check if the count is not 15.

## Figure 1: complete Claude Code family graph

Figure 1 must be generated only after the 15-row Claude Code table is complete.

It must show all 15 configurations.

The Y axis must be Artificial Analysis Intelligence Index or the exact equivalent score returned by the selected AA source.

The X axis must be Artificial Analysis cost per task.

Use a logarithmic X axis if necessary for readability.

Draw one family line for each family:

* Haiku 4.5
* Sonnet 5
* Opus 4.8
* Fable 5

Haiku has one point and therefore no meaningful family line.

Sonnet has four points.

Opus has five points.

Fable has five points.

The graph is not the frontier graph. It is the complete family graph. Dominated configurations remain visible.

Every point must show its effort label.

Hovering a point must reveal:

* Model family
* Canonical model ID
* Effort level
* AA Intelligence Index
* AA cost per task
* Data source
* Retrieval timestamp
* Data quality
* Whether the point is dominated
* Which cheaper or stronger point dominates it, if applicable

Hovering one point must bring the entire associated family into focus and dim the other families. This is required so overlapping points can be inspected.

Clicking a legend item must toggle that family.

There must be a “Show all families” button.

The title must explicitly say that the figure contains all 15 Claude Code native configurations.

## The 14-point progression

The 14-point progression consists of all non-Haiku native Claude Code configurations:

* Sonnet 5: four configurations
* Opus 4.8: five configurations
* Fable 5: five configurations

That produces 14 candidate points.

Do not secretly substitute other models into this progression.

Do not call all 14 points the efficient frontier unless all 14 are actually non-dominated.

The dashboard must distinguish between:

1. The **14-point candidate progression**, containing every Sonnet, Opus, and Fable configuration.
2. The **observed efficiency frontier**, containing only the non-dominated subset.

Both must be visible in Figure 2.

Family lines may connect all members of the same family.

The frontier line may connect only observed non-dominated points.

## Figure 2: 14-point progression and observed frontier

Figure 2 should visually resemble the supplied reference image:

* Large readable plotting area
* Family-colored lines
* Labels close to points
* Clear legend
* Logarithmic cost axis where needed
* Y axis labeled with AA Intelligence Index
* No tiny chart stranded in the top-left corner
* No extreme empty whitespace caused by one outlier
* No overlapping labels covering most of the data
* No undefined models
* No invisible points
* No point outside the plot bounds

The top of the page must contain selector buttons that change the X axis among these modes:

### Mode 1: Official SkateBench

Use official SkateBench cost per successful task.

Display raw official values in tooltips.

Only use exact crosswalks.

### Mode 2: SkateBench v2

Use v2 SkateBench cost per successful task.

Display raw v2 values in tooltips.

Only use exact crosswalks.

### Mode 3: Combined benchmark coverage

This mode must not blindly average official and v2 numbers.

Use a documented crosswalk procedure:

* Identify models present in both datasets.
* Calculate a robust dataset conversion factor using the median ratio between official and v2 cost-per-success values for overlapping models.
* Convert one dataset into the scale of the other.
* Prefer exact official values where available.
* Use converted v2 values only where official values are missing.
* Store both the raw value and converted value.
* Label converted values clearly in tooltips.
* Show the common-anchor models and the calculated conversion factor in the methodology section.
* Do not combine the datasets if there are too few trustworthy overlapping models.
* If a model is absent from both datasets, leave it unplotted.

The combined mode is a coverage union with documented normalization, not an arbitrary blended score.

Figure 2 must also offer an optional AA cost-per-task mode for comparison, but the three primary benchmark selectors are Official, v2, and Combined.

## The efficiency frontier

Do not draw a fitted curve.

Do not draw a regression line.

Do not create a theoretical mathematical boundary.

The frontier line must be derived from observed points.

The process is:

* Sort plotted points from lowest X value to highest X value.
* Starting at the cheapest point, retain a point only when its AA Intelligence Index is greater than every cheaper retained point.
* If a more expensive point has the same or lower AA IQ than a cheaper point, classify it as dominated.
* Connect only the retained points.
* Do not smooth the line.
* Do not interpolate between model families.
* Do not force the line to contain 14 points.
* If a supposedly omitted point sits above the current frontier, the frontier is wrong and must be recalculated.

This implements the empirical condition the user described:

A valid frontier has no observed point above it at the same or lower cost.

The line demonstrates the dominance relationship. It is not an imposed rule that generated the data.

Every omitted point must remain visible as a dimmed point and explain its dominance reason on hover.

## Artificial Analysis table

Create a dedicated visible table titled:

**Artificial Analysis Intelligence vs Cost per Task**

It must contain:

* Model
* Provider
* Effort
* Intelligence Index
* Cost per task
* Cost per Intelligence Index point
* Frontier status
* Data quality
* Source
* Retrieval date
* Notes

Sort by cost by default.

Allow sorting by Intelligence Index and cost per IQ point.

Do not call Intelligence Index literal human IQ. Use “AA Intelligence Index” in labels.

## SkateBench table

Create a separate visible table titled:

**SkateBench Agentic Success and Cost per Successful Task**

It must support three views:

* Official
* V2
* Combined

Columns must include:

* Model
* Provider
* Benchmark version
* Accuracy or success rate
* Average cost
* Cost per successful task
* Average tokens
* Average duration
* Tokens per second
* Errors
* Frontier status
* AA Intelligence Index, when a valid crosswalk exists
* Source

Do not mix official and v2 values in one row without labeling them.

Do not call SkateBench accuracy “IQ.”

Call it agentic success rate, task success, or operational success.

## All-model routing table

Create a routing table derived from the canonical data table.

Do not hand-write a separate list.

It should assign multiple candidate models to each role where appropriate.

General delegation roles should include:

* File and resource locator
* Structured extractor
* Classifier
* Summarizer
* Research scout
* Sentiment or semantic analyst
* Script generator
* Code patch worker
* Test generator
* Debugger
* Reviewer
* Judge
* Security and migration gate
* Architect
* Conductor

Coding-session roles should include:

* Repository navigator
* Symbol finder
* Dependency analyst
* Test writer
* Bounded patch worker
* Multi-file implementer
* Build failure investigator
* Refactor planner
* Adversarial code reviewer
* Security reviewer
* Migration planner
* Integration judge
* Project conductor

Each role must show:

* Lowest-cost candidate that has adequate evidence
* Higher-capability fallback
* Required validator
* Escalation trigger
* Data supporting the assignment
* Whether the recommendation comes from AA, SkateBench, live telemetry, or a combination

A role may have more than one model because different subtasks require different abilities. For example, locating a file can use a cheap model or deterministic script, while analyzing the sentiment or meaning of that file may require a stronger semantic model.

## DeepSeek correction

Do not include “DeepSeek V4 Flash” unless an actual source row proves that exact model exists in the dataset.

Use the exact supplied row:

`deepseek-v3.2-thinking-high`

Do not duplicate DeepSeek under two names.

Add a validation rule that normalizes model IDs and flags probable duplicates.

## Interface requirements

The final application must be one self-contained dark-mode HTML file.

It must work when opened directly from disk with no server.

It must not require external JavaScript libraries.

It must not require Google Fonts or another network resource.

It must have a sticky top control bar.

The sticky top bar must include:

* Claude Code view
* All-model routing view
* Official SkateBench
* SkateBench v2
* Combined benchmark
* AA cost/task
* Reset filters

The authoritative table must be shown before the first analytical chart.

The page may then present:

1. Canonical data table
2. Claude Code native table
3. Figure 1
4. Artificial Analysis table
5. SkateBench table
6. Figure 2
7. Routing tables
8. Proxy telemetry specification
9. Methodology and provenance
10. Raw embedded data

Use clear, formal article-style prose between these components. Do not write it as a listicle or a collection of disconnected cards.

The opening paragraph should explain:

* Why cost per token is not enough
* Why accepted task cost matters
* How the table establishes the model universe
* How the plots reveal dominated and efficient configurations
* How the frontier can be converted into an operational delegation table
* How live proxy telemetry will replace static benchmark assumptions over time

## Proxy logging and live refinement

Include an implementation section explaining exactly what the proxy must log so this static dashboard can become self-improving.

Each model call must log:

* Request ID
* Parent task ID
* Workflow ID
* Timestamp
* User request hash
* Task class
* Task difficulty
* Risk class
* Provider
* Model ID
* Effort level
* Skill or system prompt version
* Input tokens
* Cached input tokens
* Output tokens
* Reasoning tokens, when exposed
* Tool calls
* Retry count
* Latency
* Tokens per second
* Provider-reported cost
* Calculated cost
* Quota before
* Quota after
* Execution status
* Error type
* Validator type
* Validator result
* Judge score
* Human acceptance
* Human correction count
* Final accepted result
* Total accepted task cost

Each completed task must log:

* Total number of model calls
* Total cost
* Total latency
* Models used
* Escalation path
* First-pass success
* Final success
* Validation evidence
* Human acceptance
* Failure reason
* Task tags

The dashboard must explain how to correlate live proxy data with the external benchmark data:

* Normalize provider and model IDs
* Match model plus effort, not model family alone
* Keep benchmark version and date
* Separate static benchmark accuracy from live task success
* Compare models only within similar task classes
* Maintain rolling windows
* Track model drift
* Re-run calibration tasks
* Demote routes whose accepted-task cost rises
* Promote routes only after sufficient validated samples

The primary live optimization metric should be:

**Total cost divided by accepted tasks**

Also display:

* First-pass success rate
* Retry-adjusted cost
* P50 and P95 latency
* Validation failure rate
* Human correction rate
* Cost by task class
* Cost by model-and-effort combination
* Cost by skill file
* Cost by provider route

Do not permanently blacklist models. Use task-specific states such as:

* Preferred
* Active
* Experimental
* Fallback
* Quarantined for this task class
* Insufficient evidence

## Required validation before delivery

Do not deliver the dashboard until all of these checks pass.

### Data checks

* Exactly 15 Claude Code native configurations exist.
* Exactly 14 non-Haiku progression candidates exist.
* Every row has a unique ID.
* No duplicate normalized model IDs exist.
* Missing values are `null`, not zero.
* Every numeric value has a source.
* No undefined model names appear.
* No fabricated benchmark values appear.
* DeepSeek is not duplicated.

### Chart checks

* Figure 1 renders 15 points.
* Figure 1 renders 1 Haiku, 4 Sonnet, 5 Opus, and 5 Fable points.
* Figure 2 renders all available 14 candidate points in AA mode.
* Every selector re-renders the X axis.
* Missing benchmark points are omitted with a visible explanation.
* The frontier is monotonic in cost and AA Intelligence Index.
* No dominated point is connected to the frontier.
* Every point has a working tooltip.
* Hovering focuses the relevant family.
* Labels remain readable.
* The chart uses the full plotting area.
* No line is compressed into a corner.
* No SVG element overflows its view box.

### Browser checks

Use Playwright or an equivalent browser test.

Test the HTML from a local `file://` URL.

Fail delivery if there is any JavaScript console error.

Capture screenshots at:

* 1920 × 1080
* 1440 × 900
* 1024 × 768
* 390 × 844

Programmatically assert:

* Table row counts
* SVG point counts
* Legend counts
* Selector behavior
* Tooltip behavior
* Family focus behavior
* Frontier monotonicity
* No undefined or NaN text
* No elements outside the chart bounds

### Visual audit

Compare Figure 2 to the supplied reference screenshot.

It should have the same overall readability:

* Clearly separated model-family lines
* Large central plotting area
* Labels near points
* Useful legend
* Readable axes
* Smooth interaction
* No useless blank canvas
* No giant clutter cloud
* No hidden primary line

## Final deliverable

Return only:

* `index.html`
* A zip containing that same `index.html`
* A brief validation report listing the checks performed and their results

Do not return dozens of supporting files.

Do not return placeholder data.

Do not claim missing values were researched unless the exact source is provided.

Do not produce a final chart until the canonical table has been completed and audited.

The table is the source of truth. The model list comes from the table. The charts come from the table. The routing roles come from the table. Nothing is separately invented.

---
