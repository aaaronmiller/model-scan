#!/usr/bin/env python3
"""
model-scan — Iterative Refinement (Hermes Heartbeat)

Runs a scheduled model-scan + gold standard + CPMR pipeline.
Intended to be invoked by Hermes Agent heartbeat scheduling.

Workflow:
  1. Run full model scan
  2. Generate gold standard config patches
  3. Evaluate CPMR against previous gold standard
  4. Run independent audit
  5. (Optionally) Apply best config patch to ~/.hermes/config.yaml

Usage:
  # Dry run (just generates artifacts, doesn't modify config)
  python3 refine.py

  # Apply recommendations to hermes config
  python3 refine.py --apply

  # Skip scan (use cached data)
  python3 refine.py --skip-scan

  # Force scan even if run recently
  python3 refine.py --force
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "model-scan"
HERMES_CONFIG = Path.home() / ".hermes" / "config.yaml"
DINK_PATH = Path(__file__).parent / "dink.py"
REFINE_LOG = CONFIG_DIR / "refinement_log.json"
BACKUP_DIR = CONFIG_DIR / "config_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    print(f"  {msg}")


def run_scan(force: bool = False) -> int:
    """Run full model scan. Returns 0 on success."""
    log("Running model scan...")
    cmd = [sys.executable, str(DINK_PATH)]
    if force:
        cmd.append("--clear-cache")
        subprocess.run(cmd, capture_output=True)
        cmd = [sys.executable, str(DINK_PATH)]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"  ⚠ Scan returned {result.returncode}")
        for line in result.stderr.split("\n")[-5:]:
            log(f"    {line}")
    else:
        lines = [l for l in result.stdout.split("\n") if l.strip()][:3]
        for line in lines:
            log(f"  {line}")
    return result.returncode


def run_gold_standard() -> int:
    """Generate gold standard config patches."""
    log("Generating gold standard...")
    result = subprocess.run(
        [sys.executable, str(DINK_PATH), "--gold-standard"],
        capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        if "✓" in line or "├" in line or "│" in line:
            log(line.strip())
    return result.returncode


def run_cpmr() -> int:
    """Evaluate CPMR."""
    log("Evaluating CPMR...")
    result = subprocess.run(
        [sys.executable, str(DINK_PATH), "--cpmr"],
        capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        if "CPMR" in line or "├" in line or "%" in line:
            log(line.strip())
    return result.returncode


def run_audit() -> int:
    """Run independent audit."""
    log("Running audit...")
    result = subprocess.run(
        [sys.executable, str(DINK_PATH), "--audit"],
        capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        if "False Positives" in line or "Tier Accuracy" in line or "Coverage" in line:
            log(line.strip())
    return result.returncode


def backup_config() -> Path | None:
    """Backup current hermes config before applying changes."""
    if not HERMES_CONFIG.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"config.yaml.{ts}.bak"
    shutil.copy2(str(HERMES_CONFIG), str(backup))
    log(f"  Backed up to {backup.name}")
    return backup


def find_latest_patch() -> Path | None:
    """Find the most recent gold standard YAML patch."""
    gs_dir = CONFIG_DIR / "gold_standard"
    patches = sorted(gs_dir.glob("patch_*.yaml"))
    return patches[-1] if patches else None


def apply_patch(dry_run: bool = False) -> bool:
    """Apply the latest gold standard patch to hermes config."""
    patch = find_latest_patch()
    if not patch:
        log("  ⚠ No patch found")
        return False
    
    log(f"  Found patch: {patch.name}")
    
    if dry_run:
        log(f"  [dry-run] Would apply changes from {patch.name}")
        patch_text = patch.read_text()
        # Show summary of changes
        for line in patch_text.split("\n"):
            if line.startswith("# ├") or line.startswith("# ─") or "# →" in line or "→" in line:
                log(f"  {line.strip()[:70]}")
        return True
    
    # Backup first
    backup = backup_config()
    if not backup:
        log("  ⚠ No config to backup (no ~/.hermes/config.yaml)")
        return False
    
    # Parse patch and apply
    # The patch is a YAML file with comments - we extract the model recommendations
    # and write them to hermes config
    try:
        import yaml
        patch_data = yaml.safe_load(patch.read_text())
        if isinstance(patch_data, dict) and "slots" in patch_data:
            hermes_config = yaml.safe_load(HERMES_CONFIG.read_text()) or {}
            for slot_id, slot_info in patch_data["slots"].items():
                primary = slot_info.get("primary", {})
                if primary and primary.get("model_id"):
                    model_key = primary["model_id"]
                    provider_key = primary.get("provider", "")
                    # Update hermes config
                    if "model" not in hermes_config:
                        hermes_config["model"] = {}
                    hermes_config["model"][slot_id] = {
                        "provider": "custom",
                        "model": model_key,
                        "base_url": f"https://api.{provider_key}.com/v1" if provider_key else "",
                    }
            
            HERMES_CONFIG.write_text(yaml.dump(hermes_config, default_flow_style=False))
            log("  ✓ Config applied")
            return True
        else:
            log("  ⚠ Patch format not recognized (expected 'slots' key)")
            return False
    except Exception as e:
        log(f"  ⚠ Error applying patch: {e}")
        return False


def log_refinement(success: bool, applied: bool, results: dict):
    """Log refinement run results."""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "patch_applied": applied,
        "results": results,
    }
    
    if REFINE_LOG.exists():
        try:
            history = json.loads(REFINE_LOG.read_text())
        except (json.JSONDecodeError, Exception):
            history = []
    else:
        history = []
    
    history.append(log_data)
    REFINE_LOG.write_text(json.dumps(history, indent=2, default=str))
    
    # Keep last 100 entries
    if len(history) > 100:
        REFINE_LOG.write_text(json.dumps(history[-100:], indent=2, default=str))


def main():
    import argparse
    p = argparse.ArgumentParser(description="model-scan refinement pipeline")
    p.add_argument("--apply", action="store_true", help="apply config changes")
    p.add_argument("--skip-scan", action="store_true", help="skip scan, use cached data")
    p.add_argument("--force", action="store_true", help="force fresh scan")
    args = p.parse_args()
    
    print("┌─ Iterative Refinement ────────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└────────────────────────────────────────────────────")
    
    results = {}
    overall_success = True
    patch_applied = False
    
    # Step 0: Config change detection (skip if no meaningful changes)
    from config_tracker import snapshot_today, diff_yesterday_today, should_trigger_refresh
    snapshot_dir = snapshot_today()
    config_changes = diff_yesterday_today()
    if config_changes:
        log(f"  Config drift detected: {len(config_changes)} file(s) changed")
        for c in config_changes:
            log(f"    {c['file']}: {c['pct_changed']}% changed")
    
    needs_full_refresh = should_trigger_refresh(config_changes)
    if not args.force and not needs_full_refresh and args.skip_scan:
        log("  No config drift — using cached data")
    
    # Step 1: Run scan
    if not args.skip_scan:
        t0 = time.time()
        rc = run_scan(force=args.force)
        elapsed = time.time() - t0
        results["scan"] = {"rc": rc, "elapsed_s": round(elapsed, 1)}
        if rc != 0:
            log("  ⚠ Scan failed, continuing with cached data...")
    else:
        log("  Skipping scan (--skip-scan)")
    
    # Step 2: Gold standard
    t0 = time.time()
    rc = run_gold_standard()
    results["gold_standard"] = {"rc": rc, "elapsed_s": round(time.time() - t0, 1)}
    if rc != 0:
        log("  ⚠ Gold standard generation failed")
        overall_success = False
    
    # Step 3: CPMR
    t0 = time.time()
    rc = run_cpmr()
    results["cpmr"] = {"rc": rc, "elapsed_s": round(time.time() - t0, 1)}
    if rc != 0:
        log("  ⚠ CPMR evaluation failed")
    
    # Step 4: Audit
    t0 = time.time()
    rc = run_audit()
    results["audit"] = {"rc": rc, "elapsed_s": round(time.time() - t0, 1)}
    if rc != 0:
        log("  ⚠ Audit failed")
    
    # Step 5: Apply patch
    dry_run = not args.apply
    log(f"\n  {'─' * 40}")
    log(f"{'Applying patch...' if not dry_run else 'Dry run (use --apply to apply):'}")
    patch_applied = apply_patch(dry_run=dry_run)
    results["patch"] = {"applied": patch_applied, "dry_run": dry_run}
    
    # Log refinement
    log_refinement(overall_success, patch_applied, results)
    
    lines = REFINE_LOG.read_text().split("\n")
    entry_count = len(json.loads(REFINE_LOG.read_text())) if REFINE_LOG.exists() else 0
    
    print(f"\n  {'─' * 40}")
    print(f"  Refinement complete")
    print(f"  ├─ Log:            {REFINE_LOG.name} ({entry_count} entries)")
    print(f"  ├─ Gold standard:  {'✓' if results.get('gold_standard',{}).get('rc') == 0 else '✗'}")
    print(f"  ├─ CPMR:           {'✓' if results.get('cpmr',{}).get('rc') == 0 else '✗'}")
    print(f"  ├─ Audit:          {'✓' if results.get('audit',{}).get('rc') == 0 else '✗'}")
    print(f"  └─ Patch:          {'applied' if patch_applied else 'dry-run' if not args.apply else 'failed'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
