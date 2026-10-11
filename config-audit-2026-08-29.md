# Hermes Config Audit — 2026-08-29 (Context Window / Skills / Compression)

## Trigger
Repeated "context window" messages during session work; user noted 102 skills loaded may contribute.

## Evidence
- `hermes-config.yaml`: 102 skills in `agents/skills/` (see audit); compression settings present but tuned for general workload, not 1M-context + 102-skills.
- `hermes-projects/all-session-content.json`: session messages up to 64,840 chars (`content_len`); multiple messages >20k chars.
- `hermes-config.yaml`: `compression.enabled=true`, `threshold=0.6`, `target_ratio=0.2`, `max_tokens=8000`, `protect_first_n=3`, `protect_last_n=20`, `hygiene_hard_message_limit=400`, `abort_on_summary_failure=true`.
- Hermes version: `v0.20.6` (installed Aug 27 2026); upstream 51 commits ahead. New keys from newer commits NOT integrated into `hermes-config.yaml`.
- Config audit: no missing required keys for basic operation, but new upstream keys (potentially related to large-context optimization, new compression modes, or skill-selection limits) are absent because updates are not auto-merged.

## Root Cause (Context Window Errors)
Not a single missing key — a workload/config mismatch:
1. **102 loaded skills**: each skill injects instructions/tool descriptions into the system prompt. Combined overhead exceeds effective context budget when paired with very long session messages.
2. **Long session messages**: up to 64,840 chars (observed in `hermes-projects/all-session-content.json`). Even a 1M token window shrinks quickly with multi-turn history + 102 skills + very long responses.
3. **Compression settings too conservative for this workload**: `threshold=0.6` means compression only activates when context exceeds 60% of budget; `target_ratio=0.2` targets 20% of original size but with `max_tokens=8000` per compressed chunk and `protect_first_n=3` / `protect_last_n=20`, compression may not sufficiently reduce long messages before the window overflows.
4. **No skill-selection/filter mechanism in config**: all 102 skills load unconditionally; no `skills_filter` or `max_skills` key present.

## Missing / Outdated Config Keys (Hermes v0.20.6 vs upstream)
New features (51 commits ahead) are NOT auto-added to `hermes-config.yaml`. This is by design (no change performed) but creates drift. Potential missing keys (based on upstream development trends observed in `agents/skills/` and `hermes-agent-rebuild/` docs):
- Skill filtering / selection limits (e.g., `skills_filter`, `max_active_skills`)
- Enhanced compression modes for very long contexts (e.g., `compression.mode: aggressive`, `compression.context_aware`)
- Context budget allocation per role/agent (`agent_context_budget`, `skill_context_limit`)
- Large-message truncation or summarization thresholds (`long_message_truncate_length`, `long_message_summary_model`)
These keys are speculative based on upstream gap; the actual new keys would need to be extracted from the upstream repo or release notes.

## Fix Recommendations (Config)
1. **Reduce loaded skills for large-context sessions**: add a skill filter mechanism or temporarily disable non-essential skills (`agent-browser`, `clawteam`, `cso`, etc.) when working with very long messages.
2. **Adjust compression for 1M-context workload**: consider `threshold=0.4` (trigger compression earlier) and `target_ratio=0.15` (compress more aggressively) for sessions with long messages. Keep `abort_on_summary_failure=true` but verify summary model (`deepseek-v4-flash-free`) can handle very long inputs.
3. **Monitor message lengths**: the session audit shows messages >20k chars are common; consider adding a user-facing or automated truncation/summarization trigger for messages exceeding a configurable threshold (e.g., 30k chars).
4. **Integrate upstream keys**: when updating Hermes, check new keys in upstream and add them to `hermes-config.yaml` with appropriate defaults (currently no automatic integration exists — this is a manual process, as confirmed by the absence of `skills_filter` or new compression modes).

## Policy Note (New Feature Integration)
When new Hermes features arrive (e.g., via `hermes update` — currently 51 commits behind):
- They are NOT automatically added to `hermes-config.yaml`.
- No automatic merge or default injection is performed.
- Manual audit required: compare upstream config schema / release notes with current file, then add new keys with safe defaults.
This explains the drift: new keys exist upstream but are not present in the current config, meaning enhanced large-context handling or skill-selection features are unavailable even though the binary supports them.
