"""Fetch raw source documents and keep each one as a dated, checksummed snapshot.

A snapshot directory is ``free_rank/snapshots/<YYYY-MM-DD>/``. Every raw body is stored
gzipped next to ``manifest.json``, which records the URL, the fetch time, the HTTP status,
the byte count and the SHA-256 of the raw body. A ranking built from a snapshot can be
rebuilt byte for byte later, and a failed fetch is recorded rather than silently skipped.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
SNAPSHOTS = PACKAGE / "snapshots"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) model-scan-free-rank/1.0"


def snapshot_dir(date: str | None = None) -> Path:
    """The snapshot folder for a date; the latest existing one when no date is given."""
    if date:
        return SNAPSHOTS / date
    existing = sorted(p for p in SNAPSHOTS.glob("*") if (p / "manifest.json").exists())
    if not existing:
        raise FileNotFoundError("no snapshot yet; run with --refresh")
    return existing[-1]


def _manifest(folder: Path) -> dict:
    path = folder / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}


def fetch(name: str, url: str, folder: Path, timeout: int = 60, key_env: str | None = None) -> dict:
    """Download one URL into the snapshot folder. Returns its manifest entry."""
    folder.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if key_env and os.environ.get(key_env):
        # The key is sent, never written to the manifest or printed.
        headers["Authorization"] = "Bearer " + os.environ[key_env]
    entry = {"url": url, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as resp:
            body = resp.read()
            entry["status"] = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read() or b""
        entry["status"] = exc.code
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        body = b""
        entry["status"] = None
        entry["error"] = type(exc).__name__ + ": " + str(exc)[:200]
    entry["bytes"] = len(body)
    entry["sha256"] = hashlib.sha256(body).hexdigest()
    entry["file"] = name + ".gz"
    # mtime=0 keeps the gzip bytes identical for identical bodies.
    (folder / entry["file"]).write_bytes(gzip.compress(body, mtime=0))
    manifest = _manifest(folder)
    manifest[name] = entry
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return entry


def read(name: str, folder: Path) -> tuple[bytes, dict]:
    """Raw body and manifest entry of a stored snapshot. Verifies the checksum."""
    entry = _manifest(folder).get(name)
    if not entry:
        raise KeyError(f"{name} is not in {folder}/manifest.json")
    body = gzip.decompress((folder / entry["file"]).read_bytes())
    if hashlib.sha256(body).hexdigest() != entry["sha256"]:
        raise ValueError(f"checksum mismatch for {name} in {folder}")
    return body, entry


def ok(entry: dict) -> bool:
    return entry.get("status") == 200 and entry.get("bytes", 0) > 0
