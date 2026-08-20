<!--
---
title: ARDF v7.3 Build Integrity and Cohesion Audit
version: 7.3.0
created: 2026-08-08
model: GPT-5.6 Sol
reasoning_level: high
status: passed
---
-->

# ARDF v7.3 build integrity and cohesion audit

This file records the final deterministic-build audit performed after the DeepSeek/MiMo identity cleanup, direct Artificial Analysis task-cost refresh, strict-Pareto tie fix, external-frontier additions, and script-entry-point cleanup.

## Entry points

- `scripts/calibrate.py` is the **only calibration engine**. It fits configured mappings and fills calibrated CSV fields.
- `scripts/augment_cost.py` creates explicit derived cost observations. It does not fit calibration mappings.
- `scripts/build-analysis.py` computes strict Pareto membership, capability tiers, near-frontier regret, executor price/performance, top-end pruning, and external source-native frontier products.
- `scripts/build-package.py` is the **only complete package build/orchestration entry point**.
- The ambiguous historical `scripts/rebuild.py` wrapper has been removed.

## Determinism test

The complete package build was run twice consecutively from the same canonical inputs. The second run produced byte-identical canonical data and analysis outputs.

```text
unified-model-evidence.csv
SHA-256: 5e36c5968324fcbb4008b29580a85596ac7283b565f23c04c1c54df4c30580f8

analysis-data.json
SHA-256: 128eb2ddad17c0726d651958348ee196b3b4f4e4be4a3fe8669281350f9bddd5
```

This guards against a prior refresh bug where an explanatory Luna provenance sentence was appended again on every build. The dated refresh adapter is now explicitly idempotent.

## Mathematical regression checks

The validator confirms:

- strict Pareto dominance requires at least one strict inequality;
- exact coordinate ties are Pareto-equivalent rather than falsely eliminating one configuration;
- diagnostic metadata rows cannot vote in capability/cost calibration;
- MiMo-V2.5, MiMo-V2.5-Pro, and MiMo-V2-Pro remain separate identities;
- DeepSeek V4 Pro rows remain labeled Preview until an official final release exists;
- the executor list is sorted by literal `task_cost / calibrated_capability` above the visible capability floor;
- Muse Contributor pricing is primary while the Standard route is retained separately;
- Opus 5 max is removed from the AA same-source family frontier when xhigh has equal score at lower direct AA task cost;
- Opus 5 high and GPT-5.6 Sol max are both retained when their AA capability/task-cost coordinates are exactly tied;
- Kimi K3 max survives the audited top-end ARDF and AA frontiers;
- Qwen3.8 Max xhigh does not survive those general top-end planes under the current evidence;
- AA, Kilo, and Vals comparison products exist independently and are not silently averaged together.

## Static application checks

`node --check` passes for generated JavaScript and every inline script block in the four HTML applications. Every local `<script src>` reference resolves inside the package, protecting against the v7.1 flash-then-disappear failure caused by omitted generated payload files.

Pixel-level browser rendering is not claimed here. The audit covers data identity, deterministic derivation, file/link presence, JavaScript syntax, and analysis invariants.
