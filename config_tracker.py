"""
Config Change Tracker — Snapshots + Drift Detection

Daily snapshots of config files. Diff engine links config changes to CPMR shifts.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, date
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "model-scan"
SNAPSHOT_DIR = CONFIG_DIR / "snapshots"
OUTPUT_DIR = CONFIG_DIR / "drift"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRACKED_FILES = [
    "slot_definitions.yaml",
    "scan_config.yaml",
    "free_model_whitelist.json",
    "benchmarks.json",
    "tiers.yaml",
]


def snapshot_today() -> Path:
    """Copy all tracked config files to a dated snapshot directory."""
    today_str = date.today().isoformat()
    snap_dir = SNAPSHOT_DIR / today_str
    snap_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for fname in TRACKED_FILES:
        src = CONFIG_DIR / fname
        if src.exists():
            shutil.copy2(str(src), str(snap_dir / fname))
            count += 1
    
    return snap_dir


def diff_yesterday_today() -> list[dict]:
    """Compare today's snapshot with yesterday's. Return list of changes."""
    today_str = date.today().isoformat()
    today_dir = SNAPSHOT_DIR / today_str
    
    # Find most recent snapshot before today
    snap_dirs = sorted([d for d in SNAPSHOT_DIR.iterdir() if d.is_dir() and d.name < today_str])
    if not snap_dirs:
        return []
    yesterday_dir = snap_dirs[-1]
    
    changes = []
    for fname in TRACKED_FILES:
        today_file = today_dir / fname
        yesterday_file = yesterday_dir / fname
        if not today_file.exists() or not yesterday_file.exists():
            continue
        
        old_text = yesterday_file.read_text()
        new_text = today_file.read_text()
        
        if old_text == new_text:
            continue
        
        # Compute diff lines
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        added = sum(1 for l in new_lines if l not in old_lines)
        removed = sum(1 for l in old_lines if l not in new_lines)
        
        changes.append({
            "file": fname,
            "date": today_str,
            "added_lines": added,
            "removed_lines": removed,
            "pct_changed": round((added + removed) / max(len(old_lines), 1) * 100, 1),
        })
    
    return changes


def should_trigger_refresh(changes: list[dict], threshold_pct: float = 5.0) -> bool:
    """Return True if any tracked file changed more than threshold_pct."""
    for c in changes:
        if c["pct_changed"] >= threshold_pct:
            return True
    return False


def analyze_drift_history(days: int = 30) -> dict:
    """Analyze config drift over the last N days."""
    history = []
    snap_dirs = sorted([d for d in SNAPSHOT_DIR.iterdir() if d.is_dir()], reverse=True)
    
    for snap_dir in snap_dirs[:days]:
        day_changes = []
        for fname in TRACKED_FILES:
            fp = snap_dir / fname
            if fp.exists():
                day_changes.append({
                    "file": fname,
                    "size": fp.stat().st_size,
                    "modified": datetime.fromtimestamp(fp.stat().st_mtime).isoformat(),
                })
        history.append({"date": snap_dir.name, "files": day_changes})
    
    return {
        "tracked_files": TRACKED_FILES,
        "snapshot_count": len(history),
        "history": history,
    }


def main():
    """Run snapshot + drift check."""
    print(f"┌─ Config Change Tracker ─────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└──────────────────────────────────────────────────")
    
    snap_dir = snapshot_today()
    print(f"  ✓ Snapshot saved to {snap_dir.name}/")
    
    changes = diff_yesterday_today()
    if changes:
        print(f"  ⚠ {len(changes)} file(s) changed:")
        for c in changes:
            icon = "🔴" if c["pct_changed"] > 10 else "🟡"
            print(f"    {icon} {c['file']}: {c['pct_changed']}% changed ({c['added_lines']}+ / {c['removed_lines']}-)")
        
        if should_trigger_refresh(changes):
            print(f"\n  → Change threshold exceeded — refresh recommended")
    else:
        print(f"  ✓ No config changes since last snapshot")
    
    # Save drift report
    drift_report = {
        "generated_at": datetime.now().isoformat(),
        "snapshot_dir": snap_dir.name,
        "changes": changes,
    }
    drift_path = OUTPUT_DIR / f"drift_{datetime.now().strftime('%Y%m%d')}.json"
    drift_path.write_text(json.dumps(drift_report, indent=2))
    print(f"  ✓ Drift report saved to {drift_path.name}")


if __name__ == "__main__":
    main()
