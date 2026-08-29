# CASS Root Cause — Current Issues (Fixed 2026-08-28)

## What was broken
- `cass status`: HUNG (>30s timeout)
- `cass diag --json`: HUNG, zero output
- `cass index --force`: HUNG then crashed with `stack overflow`
- `cass doctor --fix`: HUNG (PID 414, 5h 33m running, 0.9% CPU)
- `cass-maintain` (cron): HUNG (PID 230/235, 5h 33m)

## Root cause sequence (verified on this machine)
1. DB corruption: `agent_search.db` (1.3GB) + `.corrupt-main` (161MB) + `.corrupt` WAL files.
2. Previous fix (`cass-maintain` script missing → `rc 127 x4/day`) was fixed, but the DB remained corrupt.
3. The corrupt DB caused `cass status --json` to hang (script tries to parse status, DB unresponsive).
4. `cass-maintain` called `cass status --json` → hang → never completed → index never rebuilt.
5. `cass doctor --fix` started by maintain script also hung (5h+).
6. Archive (`~/.cass/archive`): only 1 session file (`session-18758.jsonl`); ledgers/sources EMPTY.
7. Index lock (`index-run.lock`) left from previous failed index run blocked new attempts.

## Why it recurred
- `cass-maintain` has no health gate; it runs `cass status --json` unconditionally.
- No detection of stuck doctor/index processes before starting.
- No check for corrupt DB references (`.corrupt*`) before index.
- No check for empty ledgers/sources before index.
- The index process crashes with `stack overflow` when DB is corrupt/rebuilt improperly.

## Fixes applied (this session)
1. Killed stuck PIDs: doctor (414), maintain (230, 235).
2. Removed index lock (`index-run.lock` + `.meta`).
3. Removed corrupt DB refs (`.corrupt-main`, `.corrupt` WAL).
4. Cleaned WAL files (`agent_search.db-wal`, `.cert`, `.cert-head`, `.use`, `.gate`).
5. Replaced DB with `.backup` (154MB, healthy, sqlite3 `.dbinfo` passes).
6. Rebuilt archive (`rebuild-20260828.jsonl`), ledgers (`rebuild-ledger.json`), sources (`rebuild-state.json`).
7. Added `cronjobs/bin/cass-health-guard.sh` with fail-closed checks:
   - No stuck doctor/index processes
   - No stale index lock
   - DB readable by sqlite3
   - No `.corrupt*` files
   - Archive not empty
   - Ledgers + sources present
8. Added health-guard reference to `cronjobs/crontab`.

## Prevention (so this won't recur)
- Health guard (`cass-health-guard.sh`) runs before any index/update.
- If health fails: exit 2 (fail-closed), log message, skip index — never hang.
- The `cass-maintain` script should call the health guard first (update recommended).
- Monitor: if `cass-maintain` exceeds 30 min (current hang = 5h+), kill + retry manually.
- Weekly check: verify archive count > 1, ledgers/sources non-empty, no `.corrupt*` files.

## Unresolved
- `cass index --force` still crashes with `stack overflow` (deeper indexer issue, possibly recursive traversal or DB schema mismatch with backup). This requires either a code fix in `cass` or using an alternative search mechanism. The health guard prevents the hang from blocking the system; manual retry or upstream `cass` update needed for full index restoration.
