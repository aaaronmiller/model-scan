"""
Cron job launcher for model-scan auto-deployment.

Manages user crontab entries to run daily (--mode daily) and weekly
(--mode weekly) scans on a schedule. Stores config alongside existing
CONFIG_DIR files and uses `crontab` command to install/remove entries.

Config file: ~/.config/model-scan/cron_config.yaml
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader  # type: ignore[assignment]

CONFIG_DIR = Path.home() / ".config" / "model-scan"
CRON_CONFIG = CONFIG_DIR / "cron_config.yaml"
SCRIPT_PATH = Path(sys.argv[0] if sys.argv[0] != "" else __file__).resolve()

DEFAULT_CONFIG: dict = {
    "daily": {
        "schedule": None,  # e.g. "0 6 * * *"
        "enabled": False,
        "extra_args": "--mode daily --no-color --emit-snapshot",
    },
    "weekly": {
        "schedule": None,  # e.g. "0 7 * * 1"
        "enabled": False,
        "extra_args": "--mode weekly --no-color --emit-snapshot",
    },
}


def load_config() -> dict:
    """Load cron config from disk, returning defaults if missing."""
    if CRON_CONFIG.exists():
        raw = CRON_CONFIG.read_text()
        if raw.strip():
            try:
                cfg = yaml.safe_load(raw) or {}
                for key in DEFAULT_CONFIG:
                    if key not in cfg:
                        cfg[key] = dict(DEFAULT_CONFIG[key])
                    else:
                        for sub in DEFAULT_CONFIG[key]:
                            cfg[key].setdefault(sub, DEFAULT_CONFIG[key][sub])
                return cfg
            except Exception:
                pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """Persist cron config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CRON_CONFIG.write_text(yaml.safe_dump(cfg, default_flow_style=False, sort_keys=False))


def get_cron_entries() -> list[dict]:
    """Parse current user crontab into list of {schedule, command, raw} dicts."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().splitlines()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(maxsplit=5)
        if len(parts) >= 6:
            schedule = " ".join(parts[:5])
            command = parts[5]
            entries.append({"schedule": schedule, "command": command, "raw": stripped})
    return entries


def install_crontab(entries: list[str]) -> bool:
    """Write entries as the full user crontab. Returns True on success."""
    content = "# model-scan auto-deployment — managed by cron_manager.py\n"
    content += "# To override, use: dink.py --cron-set/--cron-remove\n"
    content += "\n".join(entries)
    content += "\n"
    try:
        proc = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, err = proc.communicate(input=content.encode(), timeout=10)
        if proc.returncode != 0:
            print(f"[cron] crontab install failed: {err.decode().strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
        print("[cron] crontab install timed out — killed child process")
        return False
    except (FileNotFoundError, OSError) as e:
        print(f"[cron] crontab not available: {e}")
        return False


def sync_crontab(cfg: dict) -> dict[str, str]:
    """Sync cron config into user crontab. Returns {job: status} dict."""
    existing = get_cron_entries()
    # Filter out old model-scan entries
    kept = [e["raw"] for e in existing if "dink.py" not in e["command"]]

    status = {}
    for job_key in ("daily", "weekly"):
        job = cfg.get(job_key, {})
        if job.get("enabled") and job.get("schedule"):
            python = sys.executable
            extra = job.get("extra_args", f"--mode {job_key} --no-color")
            command = f"{python} {SCRIPT_PATH} {extra}"
            line = f"{job['schedule']} {command}"
            kept.append(line)
            status[job_key] = f"scheduled @ {job['schedule']}"
        else:
            status[job_key] = "disabled"

    ok = install_crontab(kept)
    if not ok:
        return {k: f"FAILED: {v}" for k, v in status.items()}
    return status


def remove_cron_jobs() -> dict[str, str]:
    """Remove all model-scan entries from crontab."""
    existing = get_cron_entries()
    kept = [e["raw"] for e in existing if "dink.py" not in e["command"]]
    ok = install_crontab(kept)
    return {"removed": "ok" if ok else "failed"}


def show_status() -> str:
    """Return a human-readable status string for the cron system."""
    cfg = load_config()
    actual = get_cron_entries()
    lines: list[str] = []
    lines.append("Cron Auto-Deployment")
    lines.append(f"  Config: {CRON_CONFIG}")
    for job_key in ("daily", "weekly"):
        job = cfg.get(job_key, {})
        schedule = job.get("schedule", "—") or "—"
        enabled = job.get("enabled", False)
        lines.append(f"  {job_key:8s} {'●' if enabled else '○'}  {schedule}")
    lines.append(f"  Crontab entries: {len(actual)} total, {sum(1 for e in actual if 'dink.py' in e['command'])} model-scan")
    for e in actual:
        if "dink.py" in e["command"]:
            lines.append(f"    {e['schedule']}  {e['command'][:80]}…")
    return "\n".join(lines)
