# Empirical Observations — Session 2026-06-19
# Mined from actual conversation, not fabricated.

DO NOT ADD claims not in this file. This is the ONLY source of truth for
empirical model sentiment until the sentiment pipeline is built.

---

## Observations Made by User in This Session

1. **DeepSeek V4 Flash vs Nemotron 3 Ultra**: User finds DeepSeek V4 Flash's
   reasoning traces more effective. Nemotron 3 Ultra lacks "magic" — it asks
   for clarification or gets in loops. DeepSeek "just gets shit done."
   *Source: User statement in session.*
   *Status: Empirical observation, single user, unverified against other sources.*

2. **MiniMax-M3**: User acknowledged it scores highest (AI 54.7) but hasn't
   used it much yet. Needs empirical validation.
   *Source: User statement: "i havent used minimax too much et"*
   *Status: Acknowledged gap.*

3. **GLM 5.2**: User states it's "very likely better than mimax by a considerable
   degree." AA cache only has GLM 5.1 (51.4). GLM 5.2 not in data.
   *Source: User correction when I falsely labeled it as "underperforming."*
   *Status: User assertion, needs data collection.*

4. **StepFun models**: User mentions they "punch above their weight."
   *Source: Brief mention in session.*
   *Status: Single mention, needs verification.*

5. **Qwen series**: User mentions newest Qwen models are strong performers.
   *Source: Brief mention.*
   *Status: Needs data collection.*

6. **Gemma series**: User confirms Gemma underperforms relative to benchmarks.
   *Source: User statement.*
   *Status: User assertion.*

7. **Gemini series**: User confirms Gemini underperforms in practice vs benchmarks.
   *Source: User statement.*
   *Status: User assertion.*

8. **The "magic" factor**: Some models "just get shit done instead of asking for
   clarification, or getting in loops." This is a real qualitative dimension
   that benchmarks don't capture. DeepSeek V4 Flash has it; Nemotron 3 Ultra
   doesn't.
   *Source: User statement.*
   *Status: Key qualitative insight for calibration.*

---

## Data Quality Notes

- AA cache date: 2026-06-07 (12 days old at time of session)
- AA cache contains GLM 5.1 but NOT GLM 5.2
- AA cache contains MiMo V2 Flash but NOT MiMo V2.5 Flash
- AA cache contains MiMo V2.5 and MiMo V2.5-Pro
- No models.dev architecture data has been cross-referenced yet
- No sentiment has been scraped from social media
- All "overperformer/underperformer" labels in CALIBRATION_PLAN.md were
  fabricated except where noted above

## Action Items

1. Remove all fabricated sentiment claims from CALIBRATION_PLAN.md and TODO.md
2. Replace with references to this file for verified observations only
3. Build sentiment pipeline before any more empirical claims are made
