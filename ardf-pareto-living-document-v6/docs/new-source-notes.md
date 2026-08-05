<!--
---
title: ARDF v6 Added Source Notes
version: 6.0.0
created: 2026-07-28
model: GPT-5.6 Thinking
reasoning_level: high
---
-->

# Five added source slices

The update imports every published row from five current benchmark tables, for 281 new capability observations.

| Source | Rows | Date | Why it helps |
|---|---:|---|---|
| LiveBench | 45 | 2026-06-25 | Broad objective reasoning, coding, mathematics, language, data analysis, instruction following, and agentic coding coverage. |
| Vals Index v1.2 | 40 | 2026-07-23 | Composite economic-work evidence spanning finance and coding. Down-weighted because several component benchmarks are separately included. |
| Terminal-Bench 2.1 mirror | 45 | 2026-07-22 | Terminal-agent execution and tool-use evidence. |
| Vibe Code Bench v1.1 | 76 | 2026-07-23 | Full-stack web application delivery using production-like tools. |
| Vals SWE-bench mirror | 75 | 2026-07-22 | Software issue-resolution evidence. Kept distinct from canonical SWE-bench sources. |

Source pages:

- https://livebench.ai/
- https://benchlm.ai/benchmarks/liveBench
- https://www.vals.ai/benchmarks/vals_index
- https://benchlm.ai/benchmarks/valsIndex
- https://www.vals.ai/benchmarks/terminal-bench-2-1
- https://benchlm.ai/benchmarks/valsTerminalBench21
- https://www.vals.ai/benchmarks/vibe-code
- https://benchlm.ai/benchmarks/vibeCodeBench
- https://www.vals.ai/benchmarks/swebench
- https://benchlm.ai/benchmarks/valsSweBench

## Thin-model coverage after supplementation

Under the default identity crosswalk:

- Claude Fable 5 max receives all five new source measurements plus existing evidence.
- Claude Opus 5 max receives four source-default measurements plus existing evidence; high and xhigh retain effort-specific LiveBench evidence.
- GPT-5.6 Sol max receives all five source measurements plus existing evidence; xhigh retains effort-specific LiveBench evidence.
- Kimi K3 max receives all five new source measurements and can now pair with its existing cost record.

The raw leaderboard values remain available even when a source-default label is crosswalked to a max/default routing configuration. The `identity_mapping` field makes that decision auditable.
