# ARDF recomputation versus Priors: exact deltas

Generated 2026-11-17 by `calibrate.py` from `sources/current/` (AA snapshot 2026-11-10). Do not edit by hand.

## Read this first: this agreement is circular, not independent validation

ARDF's composite score applies the ten benchmark weights 15/5/10/15/10/5/5/10/10/15 (the weights of the owner-selected Priors index) to AA's per-benchmark components. Priors applies the same weights to the same AA data. So ARDF versus Priors below is the same arithmetic on the same AA snapshot: agreement to within Priors' two-decimal rounding is guaranteed by construction and says nothing about whether those weights are right. API-basis costs agree to within the maximum cost delta below, which is consistent with Priors using AA's own per-task costs; the pinned Priors snapshot does not state its method.

The comparator that does not share ARDF's weights is AA's own published `intelligenceIndex`. ARDF's composite differs from it on 116 scored configurations by a median 0.0202 and at most 0.2824 points; 15 differ by more than 0.1 and 80 by more than 0.005. AA's published values carry full float precision in the snapshot, so the gap is not rounding. The pinned data does not say why (AA's own weighting or normalization is not in the snapshot). The two columns at the right of the matched table and the table of largest divergences below show it.

ARDF scores and costs are recomputed from the primary Artificial Analysis snapshot (2026-11-10, 734 configurations preserved, 116 with a complete 10-benchmark score). Priors (API cost basis, snapshot in `sources/current/priors-api.json`) is a cross-check only; no Priors value enters any ARDF score or cost. Delta = ARDF minus Priors.

Matched 93 of 100 Priors rows (91 by exact identity, 2 by a flagged loose name-plus-effort pass). Score delta: median |d| 0.002541, max |d| 0.004967. Priors publishes two decimals, so a score delta up to 0.005 is rounding. Cost delta (USD per task): median |d| 0.000042, max |d| 0.003892.

## AA published index versus the ARDF composite: 116 configurations, largest divergences

| Model / effort | ARDF score | AA published index | ARDF minus AA |
|---|---:|---:|---:|
| Qwen3.8 Max (0902) | 33.372188 | 33.654563 | -0.282375 |
| GLM-5.3 (Max) | 31.479982 | 31.653382 | -0.173400 |
| Claude Opus 5.5 (High, Default Fallback) | 51.670471 | 51.835996 | -0.165525 |
| Claude Opus 5.5 (Medium, Default Fallback) | 48.043777 | 48.208102 | -0.164325 |
| Grok 4.7 (Xhigh) | 35.322862 | 35.485012 | -0.162150 |
| Claude Sonnet 5.5 (Medium, Default Fallback) | 30.658752 | 30.819552 | -0.160800 |
| Claude Opus 5.5 (Max, Default Fallback) | 58.946509 | 59.106034 | -0.159525 |
| Claude Opus 5.5 (Xhigh, Default Fallback) | 57.287056 | 57.444706 | -0.157650 |
| Claude Fable 5.1 (Xhigh, Default Fallback) | 49.871713 | 50.021638 | -0.149925 |
| Claude Opus 5 (Max) | 44.024598 | 44.164623 | -0.140025 |

## Matched rows, largest absolute score delta first

| Model / effort | Match | ARDF score | Priors score | Score delta | ARDF cost | Priors cost | Cost delta | AA published index | ARDF minus AA |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Muse Wonder (high) | exact identity | 40.525033 | 40.530000 | -0.004967 | 4.560546 | 4.561000 | -0.000454 | 40.526608 | -0.001575 |
| MiMo V2.6 Pro (default) | exact identity | 29.805033 | 29.810000 | -0.004967 | 0.257180 | 0.257200 | -0.000020 | 29.889783 | -0.084750 |
| Muse Wonder (max) | exact identity | 43.574823 | 43.570000 | 0.004823 | 6.952036 | 6.952000 | 0.000036 | 43.574823 | 0.000000 |
| Haiku 5.5 (xhigh) | exact identity | 34.565201 | 34.570000 | -0.004799 | 0.248361 | 0.248400 | -0.000039 | 34.638776 | -0.073575 |
| GPT-6 Luna (low) | exact identity | 9.665208 | 9.670000 | -0.004792 | 0.005115 | 0.005115 | 0.000000 | 9.666108 | -0.000900 |
| North Mini Code (default) | exact identity | 3.424703 | 3.420000 | 0.004703 | 0.000000 | 0.000000 | 0.000000 | 3.424703 | -0.000000 |
| Fable 5.2 (max) | exact identity | 64.564646 | 64.560000 | 0.004646 | 26.538558 | 26.540000 | -0.001442 | 64.563596 | 0.001050 |
| GPT-6 Astra (xhigh) | exact identity | 55.304622 | 55.300000 | 0.004622 | 3.658926 | 3.659000 | -0.000074 | 55.305747 | -0.001125 |
| Haiku 5.5 (high) | exact identity | 29.865540 | 29.870000 | -0.004460 | 0.158560 | 0.158600 | -0.000040 | 29.874315 | -0.008775 |
| Sonnet 5.5 (xhigh) | exact identity | 49.894408 | 49.890000 | 0.004408 | 4.091985 | 4.092000 | -0.000015 | 49.924033 | -0.029625 |
| Qwen 3.8 27B (none) | exact identity | 10.075618 | 10.080000 | -0.004382 | 3.772944 | 3.773000 | -0.000056 | 10.031668 | 0.043950 |
| GPT-6 Luna (xhigh) | exact identity | 23.444348 | 23.440000 | 0.004348 | 0.104093 | 0.104100 | -0.000007 | 23.450873 | -0.006525 |
| GPT-6.1 Terra (medium) | exact identity | 38.154333 | 38.150000 | 0.004333 | 0.168805 | 0.168800 | 0.000005 | 38.165208 | -0.010875 |
| GPT-6 Astra (max) | exact identity | 56.854306 | 56.850000 | 0.004306 | 6.244667 | 6.245000 | -0.000333 | 56.853856 | 0.000450 |
| Gemini 3.5 Flash-Lite (high) | exact identity | 11.724221 | 11.720000 | 0.004221 | 0.692902 | 0.692900 | 0.000002 | 11.656346 | 0.067875 |
| GPT-6.1 Terra (xhigh) | exact identity | 45.284177 | 45.280000 | 0.004177 | 0.400689 | 0.400700 | -0.000011 | 45.250052 | 0.034125 |
| GPT-6 Astra (low) | exact identity | 43.304157 | 43.300000 | 0.004157 | 1.423723 | 1.424000 | -0.000277 | 43.334982 | -0.030825 |
| DeepSeek V4 Pro 0813 (none) | exact identity | 12.565944 | 12.570000 | -0.004056 | 0.976988 | 0.977000 | -0.000012 | 12.567594 | -0.001650 |
| Muse Ember (Max) (max) | exact identity | 36.016049 | 36.020000 | -0.003951 | 0.135936 | 0.135900 | 0.000036 | 36.021299 | -0.005250 |
| Inkling (xhigh) | exact identity | 12.506070 | 12.510000 | -0.003930 | 1.351958 | 1.352000 | -0.000042 | 12.478170 | 0.027900 |
| Opus 5.5 (medium) | exact identity | 48.043777 | 48.040000 | 0.003777 | 2.451089 | 2.451000 | 0.000089 | 48.208102 | -0.164325 |
| GPT-6.1 Terra (none) | exact identity | 30.496249 | 30.500000 | -0.003751 | 0.225896 | 0.225900 | -0.000004 | 30.515899 | -0.019650 |
| Sonnet 5.5 (low) | exact identity | 25.616330 | 25.620000 | -0.003670 | 0.511342 | 0.511300 | 0.000042 | 25.649705 | -0.033375 |
| K2 Horizon 375B A23B (high) | exact identity | 17.733648 | 17.730000 | 0.003648 | 0.000000 | 0.000000 | 0.000000 | 17.820273 | -0.086625 |
| K-EXAONE 2.0 (default) | exact identity | 7.563574 | 7.560000 | 0.003574 | - | - | - | 7.563574 | -0.000000 |
| Opus 5.5 (max) | exact identity | 58.946509 | 58.950000 | -0.003491 | 10.036410 | 10.040000 | -0.003590 | 59.106034 | -0.159525 |
| Kimi K3 (low) | exact identity | 17.433449 | 17.430000 | 0.003449 | 2.368774 | 2.369000 | -0.000226 | 17.419199 | 0.014250 |
| Fable 5.2 (xhigh) | exact identity | 62.216739 | 62.220000 | -0.003261 | 14.828588 | 14.830000 | -0.001412 | 62.216739 | -0.000000 |
| Haiku 5.5 (max) | exact identity | 36.443219 | 36.440000 | 0.003219 | 0.411007 | 0.411000 | 0.000007 | 36.484544 | -0.041325 |
| GPT-6 Luna (none) | exact identity | 9.443119 | 9.440000 | 0.003119 | 0.071417 | 0.071420 | -0.000003 | 9.442444 | 0.000675 |
| Muse Spark Open (xhigh) | exact identity | 24.873112 | 24.870000 | 0.003112 | 2.017668 | 2.018000 | -0.000332 | 24.881587 | -0.008475 |
| Grok 4.7 (low) | exact identity | 31.043053 | 31.040000 | 0.003053 | 2.922201 | 2.922000 | 0.000201 | 31.132078 | -0.089025 |
| Opus 5.5 (xhigh) | exact identity | 57.287056 | 57.290000 | -0.002944 | 6.047194 | 6.047000 | 0.000194 | 57.444706 | -0.157650 |
| GPT-6.1 Sol (max) | exact identity | 54.537109 | 54.540000 | -0.002891 | 1.272063 | 1.272000 | 0.000063 | 54.608734 | -0.071625 |
| Nanbeige4.3-33B (default) | exact identity | 20.407112 | 20.410000 | -0.002888 | - | - | - | 20.407112 | -0.000000 |
| Grok 4.7 (xhigh) | exact identity | 35.322862 | 35.320000 | 0.002862 | 7.771539 | 7.772000 | -0.000461 | 35.485012 | -0.162150 |
| Gemini 4 Carbon (low) | exact identity | 54.222861 | 54.220000 | 0.002861 | 7.186577 | 7.187000 | -0.000423 | 54.220611 | 0.002250 |
| GPT-6 Luna (max) | exact identity | 27.867200 | 27.870000 | -0.002800 | 0.151956 | 0.152000 | -0.000044 | 27.855200 | 0.012000 |
| Muse Wonder Full (max) | exact identity | 50.077212 | 50.080000 | -0.002788 | - | - | - | 50.077212 | -0.000000 |
| GPT-6 Luna (medium) | exact identity | 18.432766 | 18.430000 | 0.002766 | 0.042202 | 0.042200 | 0.000002 | 18.454216 | -0.021450 |
| Inkling Small (default) | exact identity | 12.927262 | 12.930000 | -0.002738 | 0.203161 | 0.203200 | -0.000039 | 12.910162 | 0.017100 |
| GPT-6.1 Terra (max) | exact identity | 51.322694 | 51.320000 | 0.002694 | 0.961108 | 0.961100 | 0.000008 | 51.326519 | -0.003825 |
| Gemini 3.8 Flash (high) | exact identity | 30.857312 | 30.860000 | -0.002688 | 7.766006 | 7.766000 | 0.000006 | 30.846812 | 0.010500 |
| Granite 4.2 3B (default) | exact identity | 4.722687 | 4.720000 | 0.002687 | - | - | - | 4.722687 | 0.000000 |
| Nemotron 3.5 Lightning (default) | exact identity | 5.582666 | 5.580000 | 0.002666 | 0.314452 | 0.314500 | -0.000048 | 5.534666 | 0.048000 |
| Muse Spark 1.3 (max) | exact identity | 36.487454 | 36.490000 | -0.002546 | 2.385781 | 2.386000 | -0.000219 | 36.617204 | -0.129750 |
| Fable 5.2 (medium) | exact identity | 56.372541 | 56.370000 | 0.002541 | 3.802605 | 3.803000 | -0.000395 | 56.408316 | -0.035775 |
| Qwen 3.8 27B (low) | exact identity | 15.602486 | 15.600000 | 0.002486 | 1.905905 | 1.906000 | -0.000095 | 15.685061 | -0.082575 |
| GPT-6 Astra (high) | exact identity | 54.832438 | 54.830000 | 0.002438 | 3.238572 | 3.239000 | -0.000428 | 54.849838 | -0.017400 |
| Gemini 4 Argon (high) | exact identity | 50.382419 | 50.380000 | 0.002419 | 9.946609 | 9.947000 | -0.000391 | 50.412194 | -0.029775 |
| Haiku 5.5 (medium) | exact identity | 24.577625 | 24.580000 | -0.002375 | 0.091765 | 0.091760 | 0.000005 | 24.601325 | -0.023700 |
| GPT-6 Astra (medium) | exact identity | 51.567664 | 51.570000 | -0.002336 | 2.732439 | 2.732000 | 0.000439 | 51.554839 | 0.012825 |
| Fable 5.2 (low) | exact identity | 53.892314 | 53.890000 | 0.002314 | 3.097242 | 3.097000 | 0.000242 | 53.924939 | -0.032625 |
| GLM 5.3 (low) | exact identity | 23.072312 | 23.070000 | 0.002312 | 1.574930 | 1.575000 | -0.000070 | 23.107937 | -0.035625 |
| Step 5 Preview (default) | exact identity | 28.467709 | 28.470000 | -0.002291 | 2.345253 | 2.345000 | 0.000253 | 28.528309 | -0.060600 |
| Qwen 3.8 Max (xhigh) | loose name plus effort (identity unverified) | 33.372188 | 33.370000 | 0.002188 | 10.023892 | 10.020000 | 0.003892 | 33.654563 | -0.282375 |
| Opus 5.5 (low) | exact identity | 34.707935 | 34.710000 | -0.002065 | 0.975529 | 0.975500 | 0.000029 | 34.752785 | -0.044850 |
| Fable 5.2 (high) | exact identity | 61.821879 | 61.820000 | 0.001879 | 9.078415 | 9.078000 | 0.000415 | 61.821879 | -0.000000 |
| Beam 1.0 (default) | exact identity | 17.731853 | 17.730000 | 0.001853 | 0.284407 | 0.284400 | 0.000007 | 17.730728 | 0.001125 |
| GPT-6 Luna (high) | exact identity | 21.438167 | 21.440000 | -0.001833 | 0.072948 | 0.072950 | -0.000002 | 21.429017 | 0.009150 |
| Grok 4.7 (high) | exact identity | 35.101821 | 35.100000 | 0.001821 | 6.183596 | 6.184000 | -0.000404 | 35.212296 | -0.110475 |
| Granite 4.2 8B (default) | exact identity | 5.098265 | 5.100000 | -0.001735 | 0.040463 | 0.040460 | 0.000003 | 5.098265 | 0.000000 |
| DeepSeek V4 Pro 0813 (max) | exact identity | 23.001723 | 23.000000 | 0.001723 | 1.769134 | 1.769000 | 0.000134 | 23.063298 | -0.061575 |
| Muse Ember (Xhigh) (xhigh) | loose name plus effort (identity unverified) | 34.111661 | 34.110000 | 0.001661 | 0.116228 | 0.116200 | 0.000028 | 34.114961 | -0.003300 |
| DeepSeek V4.1 Flash 1017 (none) | exact identity | 18.511584 | 18.510000 | 0.001584 | 0.425420 | 0.425400 | 0.000020 | 18.513159 | -0.001575 |
| GPT-6.1 Sol (medium) | exact identity | 46.311480 | 46.310000 | 0.001480 | 0.359390 | 0.359400 | -0.000010 | 46.346880 | -0.035400 |
| Mistral Large 4 (medium) | exact identity | 23.108532 | 23.110000 | -0.001468 | 1.412097 | 1.412000 | 0.000097 | 23.127732 | -0.019200 |
| MiniMax M3 (default) | exact identity | 18.848608 | 18.850000 | -0.001392 | 1.285097 | 1.285000 | 0.000097 | 18.878908 | -0.030300 |
| Inkling 2 Small (default) | exact identity | 30.628678 | 30.630000 | -0.001322 | 1.178428 | 1.178000 | 0.000428 | 30.628678 | 0.000000 |
| Gemini 3.8 Flash (medium) | exact identity | 30.118694 | 30.120000 | -0.001306 | 6.258586 | 6.259000 | -0.000414 | 30.078569 | 0.040125 |
| GLM 5.3 Flash (max) | exact identity | 27.731289 | 27.730000 | 0.001289 | 0.583310 | 0.583300 | 0.000010 | 27.803889 | -0.072600 |
| Muse Glimmer (High) (high) | exact identity | 6.341287 | 6.340000 | 0.001287 | 0.169504 | 0.169500 | 0.000004 | 6.341287 | -0.000000 |
| Sonnet 5.5 (medium) | exact identity | 30.658752 | 30.660000 | -0.001248 | 0.780656 | 0.780700 | -0.000044 | 30.819552 | -0.160800 |
| Sonnet 5.5 (high) | exact identity | 41.518934 | 41.520000 | -0.001066 | 1.636129 | 1.636000 | 0.000129 | 41.515109 | 0.003825 |
| GPT-6.1 Sol (xhigh) | exact identity | 52.430994 | 52.430000 | 0.000994 | 0.763995 | 0.764000 | -0.000005 | 52.458219 | -0.027225 |
| Agnes 2.5 Pro Theta (default) | exact identity | 24.029013 | 24.030000 | -0.000987 | 0.574668 | 0.574700 | -0.000032 | 24.029013 | 0.000000 |
| GPT-6.1 Sol (low) | exact identity | 34.770824 | 34.770000 | 0.000824 | 0.161474 | 0.161500 | -0.000026 | 34.802924 | -0.032100 |
| Mistral Large 4 (high) | exact identity | 26.110820 | 26.110000 | 0.000820 | 2.061731 | 2.062000 | -0.000269 | 26.124995 | -0.014175 |
| Haiku 5.5 (low) | exact identity | 18.639231 | 18.640000 | -0.000769 | 0.043758 | 0.043760 | -0.000002 | 18.618006 | 0.021225 |
| Qwen 3.8 27B (xhigh) | exact identity | 20.010576 | 20.010000 | 0.000576 | 3.529549 | 3.530000 | -0.000451 | 20.106876 | -0.096300 |
| GPT-6.1 Terra (high) | exact identity | 42.429426 | 42.430000 | -0.000574 | 0.259280 | 0.259300 | -0.000020 | 42.434451 | -0.005025 |
| MiMo V2.6 Flash (default) | exact identity | 26.639498 | 26.640000 | -0.000502 | 0.128530 | 0.128500 | 0.000030 | 26.727698 | -0.088200 |
| Opus 5.5 (high) | exact identity | 51.670471 | 51.670000 | 0.000471 | 3.464662 | 3.465000 | -0.000338 | 51.835996 | -0.165525 |
| Gemini 4 Carbon (medium) | exact identity | 58.279632 | 58.280000 | -0.000368 | 6.585777 | 6.586000 | -0.000223 | 58.258782 | 0.020850 |
| DeepSeek V4.1 Flash 1017 (max) | exact identity | 32.589639 | 32.590000 | -0.000361 | 0.602105 | 0.602100 | 0.000005 | 32.589639 | 0.000000 |
| Nemotron 3.5 Super VL (high) | exact identity | 13.620342 | 13.620000 | 0.000342 | 0.519633 | 0.519600 | 0.000033 | 13.620342 | 0.000000 |
| Gemini 4 Carbon (high) | exact identity | 60.019664 | 60.020000 | -0.000336 | 7.755546 | 7.756000 | -0.000454 | 60.025739 | -0.006075 |
| DeepSeek V4.1 Flash 1017 (high) | exact identity | 28.640289 | 28.640000 | 0.000289 | 0.456194 | 0.456200 | -0.000006 | 28.643739 | -0.003450 |
| Sonnet 5.5 (max) | exact identity | 54.560159 | 54.560000 | 0.000159 | 10.020621 | 10.020000 | 0.000621 | 54.541334 | 0.018825 |
| GPT-6.1 Sol (high) | exact identity | 50.309848 | 50.310000 | -0.000152 | 0.590985 | 0.591000 | -0.000015 | 50.329123 | -0.019275 |
| GPT-6.1 Terra (low) | exact identity | 29.420078 | 29.420000 | 0.000078 | 0.071338 | 0.071340 | -0.000002 | 29.416928 | 0.003150 |
| Qwen 3.8 27B (medium) | exact identity | 17.400065 | 17.400000 | 0.000065 | 2.160005 | 2.160000 | 0.000005 | 17.483165 | -0.083100 |
| GLM 5.3 (max) | exact identity | 31.479982 | 31.480000 | -0.000018 | 5.009265 | 5.009000 | 0.000265 | 31.653382 | -0.173400 |

## Priors rows not compared

No ARDF configuration matched, or the matched ARDF configuration has no complete score.

- Kimi K3.1 (max)
- Hy4 (default)
- Gemini 3.8 Flash (low)
- Ling 3.1 Flash (default)
- MiniMax M3.1 (max)
- Mistral Large 4 (default)
- Nemotron 3 Ultra (max)
