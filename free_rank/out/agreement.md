---
title: Formula agreement with the reference tiers
date: 2026-11-19
---

# Formula agreement with the reference tiers

- Kendall tau-b over Tier 1 and 2 order: **0.855** (11 reference models the formula places)
- Spearman rho over the same: **0.945**
- Tier agreement over all reference entries: **31/36**
- Same Tier 1 set: **True** (missing none, extra none)

| Reference order (T1, T2) | Formula order |
|---|---|
| DeepSeek V4.1 Flash 1017 | DeepSeek V4.1 Flash 1017 |
| Inkling 2 Small | ERNIE 5.5 Flash Preview |
| LongCat-2.5 | Inkling 2 Small |
| ERNIE 5.5 Flash Preview | MiMo-V2.6-Flash |
| MiMo-V2.6-Flash | LongCat-2.5 |
| Hy4 Flash | Hy4 Flash |
| Beam 1.0 501B A23B | Beam 1.0 501B A23B |
| Dots3-Note Preview | Dots3-Note Preview |
| Flint 40B / Flint v1.0 | Flint 40B / Flint v1.0 |
| Nemotron 3.5 Super VL | Nemotron 3 Ultra 550B A55B |
| Nemotron 3 Ultra 550B A55B | Nemotron 3.5 Super VL |
| Particle-1 |  |

## Disagreements

| Model | Reference tier | Formula tier | Score | Evidence | Reason |
|---|---|---|---|---|---|
| Particle-1 | 2 | None | 0.23 | 0.0 | no matched benchmark evidence |
| Ling 3.2 Flash | 3 | None | 0.23 | 0.0 | no matched benchmark evidence |
| Gemma 4 26B A4B Instruct | 3 | 2 | 0.263 | 5.5 |  |
| North Mini Code | 3 | 4 | 0.138 | 12.0 |  |
| Nemotron 3 Nano Omni 30B A3B Reasoning | 4 | 3 | 0.205 | 3.62 |  |
