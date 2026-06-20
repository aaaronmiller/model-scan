#!/usr/bin/env python3
"""
Auto-update script for model-scan — refreshes AA cache and updates DB scores.

Designed to run weekly via systemd timer or cron.
Logs to ~/model-scan-logs/auto-update-<date>.log

Usage:
    python3 scripts/auto_update.py           # full update
    python3 scripts/auto_update.py --dry-run # preview only
"""
from __future__ import annotations
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "model-scan"
DB = CONFIG_DIR / "model_scan.db"
AA_CACHE = CONFIG_DIR / "aa_cache.json"
LOG_DIR = HOME / "model-scan-logs"
MODEL_SCAN_DIR = HOME / "code" / "model-scan"


def log(msg: str, file=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if file:
        file.write(line + "\n")


def refresh_aa_cache() -> dict:
    """Refresh AA cache via direct API call."""
    api_key = os.environ.get("AA_API_KEY", "").strip()
    if not api_key:
        return {"status": "skipped", "output": "no AA_API_KEY"}

    try:
        import httpx
        resp = httpx.get(
            "https://artificialanalysis.ai/api/v2/data/llms/models",
            headers={"x-api-key": api_key},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            # Build lookup (same as dink.py)
            lookup = {}
            for entry in data:
                slug = (entry.get("slug") or "").lower()
                name = (entry.get("name") or "").lower()
                evals = entry.get("evaluations", {})
                record = {
                    "id": entry.get("id"),
                    "name": entry.get("name"),
                    "slug": slug,
                    "ai_index": evals.get("artificial_analysis_intelligence_index"),
                    "ai_coding": evals.get("artificial_analysis_coding_index"),
                    "median_tps": entry.get("median_output_tokens_per_second"),
                }
                lookup[slug] = record
                if name:
                    lookup[name] = record

            from datetime import timezone
            AA_CACHE.write_text(json.dumps({
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "lookup": lookup,
                "model_count": len(data),
            }, indent=2))
            return {"status": "ok", "models": len(data)}
        elif resp.status_code == 429:
            return {"status": "rate-limited", "output": "using stale cache"}
        else:
            return {"status": "error", "output": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "output": str(e)}


def load_aa_scores() -> dict:
    """Load AA scores from cache. Returns model_slug -> ai_index."""
    if not AA_CACHE.exists():
        return {}
    data = json.loads(AA_CACHE.read_text())
    lookup = data.get("lookup", {})
    scores = {}
    for slug, rec in lookup.items():
        if isinstance(rec, dict) and rec.get("ai_index") is not None:
            scores[slug] = rec["ai_index"]
    return scores


def update_db_scores(aa_scores: dict) -> int:
    """Update model-scan DB scores from AA cache. Returns count of updates."""
    if not DB.exists():
        return 0

    conn = sqlite3.connect(str(DB))
    scan_id = conn.execute("SELECT MAX(scan_id) FROM scans").fetchone()[0]
    if scan_id is None:
        conn.close()
        return 0

    rows = conn.execute(
        "SELECT model_id, ai_index FROM models WHERE scan_id = ?", (scan_id,)
    ).fetchall()

    updated = 0
    for model_id, old_ai in rows:
        mid = model_id.lower().replace("-", "").replace("/", "").replace(":", "")
        new_ai = None
        for slug, ai in aa_scores.items():
            slug_norm = slug.lower().replace("-", "").replace("/", "").replace(":", "")
            if mid in slug_norm or slug_norm in mid:
                new_ai = ai
                break
        if new_ai is not None and new_ai != old_ai:
            conn.execute(
                "UPDATE models SET ai_index = ? WHERE model_id = ? AND scan_id = ?",
                (new_ai, model_id, scan_id),
            )
            updated += 1

    conn.commit()
    conn.close()
    return updated


def check_free_status() -> list:
    """Verify Zen free models are still free."""
    zen_models = [
        "deepseek-v4-flash-free",
        "mimo-v2.5-free",
        "nemotron-3-ultra-free",
    ]
    issues = []
    for model in zen_models:
        try:
            result = subprocess.run(
                ["curl", "-s", "https://opencode.ai/zen/v1/chat/completions",
                 "-H", f"Authorization: Bearer {os.environ.get('OPENCODE_ZEN_API_KEY', '')}",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({
                     "model": model,
                     "messages": [{"role": "user", "content": "Say hi"}],
                     "max_tokens": 5,
                 })],
                capture_output=True, text=True, timeout=15,
            )
            data = json.loads(result.stdout)
            if "error" in data:
                issues.append(f"{model}: {data['error'].get('message', 'error')}")
        except Exception as e:
            issues.append(f"{model}: {e}")
    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="model-scan auto-update")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"auto-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

    with open(log_file, "w") as f:
        log("=== model-scan auto-update ===", f)

        # 1. Refresh AA cache
        log("Refreshing AA cache...", f)
        if not args.dry_run:
            result = refresh_aa_cache()
            log(f"  AA refresh: {result['status']}", f)
        else:
            log("  [dry-run] Would refresh AA cache", f)

        # 2. Load scores and update DB
        log("Loading AA scores...", f)
        aa_scores = load_aa_scores()
        log(f"  {len(aa_scores)} scores loaded", f)

        if not args.dry_run:
            updated = update_db_scores(aa_scores)
            log(f"  DB updated: {updated} scores changed", f)
        else:
            log("  [dry-run] Would update DB scores", f)

        # 3. Check free status
        log("Checking Zen free status...", f)
        if not args.dry_run:
            issues = check_free_status()
            if issues:
                for issue in issues:
                    log(f"  ⚠️  {issue}", f)
            else:
                log("  All Zen models still free", f)
        else:
            log("  [dry-run] Would check free status", f)

        log("=== Done ===", f)

    print(f"\nLog: {log_file}")


if __name__ == "__main__":
    main()
