# Session Tasks — 2026-06-19
# Mined verbatim from user's instructions. These are the actual tasks given.

---

## Task List (14 items from user's instruction block)

### 1. User Sentiment Research
- Find user sentiment for top 10 models in social media and X posts
- Include what region the data is referring to
- Models to target: top 10 by AI Index
- *Source: User instruction*

### 2. Slot Quality Refinement
- Refine information on what qualities each role in the Hermes config requires
- Some roles prioritize speed over intelligence — if a model is twice as fast
  and fails tool calls at the same rate, it's better for those roles
- *Source: User instruction*

### 3. Cross-Reference AI Index with Model Size
- Apply AI Index and performance scores to model size data from models.dev
- Build a predictive understanding: based on release date and architecture,
  we should be close to identifying capabilities
- *Source: User instruction*

### 4. Conditional Scoring in model-scan
- Until model-scan does a full recalibration, it should have conditional values
  set via arch/release-date estimation
- This is the fallback mechanic until scraped data is available
- Depends on update schedule of various benchmarks and models.dev
- *Source: User instruction*

### 5. Chinese Model Release Papers
- Find release papers for: Kimi K2.6, GLM 5.2, Qwen 3.7, MiniMax M3
- *Source: User instruction*

### 6. Benchmark List from Papers
- See what benchmarks are referenced in those whitepapers
- Make a list of benchmarks we might want to use
- *Source: User instruction*

### 7. Scrape Those Benchmarks
- Scrape them using the method model-scan uses
- Gives us an idea of what data they provide and how we can use it
- *Source: User instruction*

### 8. Calibrate Against Speed/Latency Data
- Everything needs to be calibrated against the speed and latency data we record
- *Source: User instruction*

### 9. Calibrate Against API Error Logs
- Use API call error logs from all sessions
- Shows providers and models that consistently underperform or have issues
- *Source: User instruction*

### 10. Find Project Plan / Notes File
- Find a project plan or notes file in model-scan
- Include a summarized version of all the above in model-scan
- *Source: User instruction*

### 11. Project Completion Assessment
- Check if the project is "done" or has remaining unfinished items in the TODO list
- We can pivot to doing work on this
- *Source: User instruction*

### 12. `model-scan overall` Command
- A programmatic command: `model-scan overall -a`
- Returns a model that is in the "A" tier of overall models (or with --free flag)
- Can be slotted into scripts like git-audit-sync
- *Source: User instruction*

### 13. Abstracted Evaluation Logic
- The evaluation logic should be "diabmigated" (abstracted/exposed as a callable interface)
- When a script calls for a model, it always gets an appropriate one
- *Source: User instruction*

### 14. Conditional Values Until Scraped
- Until we can obtain data from a scrape (depends on update schedules),
  conditional values should be set via the arch/release-date estimation mechanic
- *Source: User instruction*

---

## Implementation Status

| # | Task | Status |
|---|------|--------|
| 1 | User sentiment + region data | ❌ Not started |
| 2 | Slot quality refinement | ❌ Not started |
| 3 | Cross-ref AI Index × model size | ❌ Not started |
| 4 | Conditional scoring engine | ❌ Not started |
| 5 | Chinese model papers | ❌ Not started |
| 6 | Benchmark list from papers | ❌ Not started |
| 7 | Scrape those benchmarks | ❌ Not started |
| 8 | Speed/latency calibration | ❌ Not started |
| 9 | API error log calibration | ❌ Not started |
| 10 | Write project plan summary | ❌ Not started |
| 11 | Project completion check | ✅ Done (see TODO.md) |
| 12 | `model-scan overall` command | ❌ Not started |
| 13 | Abstracted evaluation interface | ❌ Not started |
| 14 | Conditional values mechanic | ❌ Not started |
