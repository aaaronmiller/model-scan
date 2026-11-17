"""API failure log for Kilo (and any CLI-routed provider).

Append-only JSONL, same pattern as spend_ledger: process-safe exclusive lock,
fsync, skip-corrupt-lines on read. Records what actually failed from our own
observation — provider error codes, latency, model, free vs paid — so failure
analysis is measured, not inferred.

Usage: wrap the CLI call, catch failures, record one event per failed call.
"""

from __future__ import annotations

import fcntl
import json
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

CONFIG_DIR = Path(os.environ.get("MODEL_SCAN_CONFIG_DIR", Path.home() / ".config" / "model-scan"))
FAILURE_LOG_PATH = CONFIG_DIR / "api_failure_log.jsonl"
MAX_ROWS_SCANNED = 50_000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FailureEvent:
    provider: str = ""       # kilo, opencode-zen, openrouter, ...
    model: str = ""          # full model id as requested
    error_type: str = ""     # auth, rate_limit, timeout, server_error, cli_crash, ...
    error_code: str = ""     # provider code (401, 429, INVALID_TOKEN, ...)
    error_msg: str = ""      # truncated provider message (no secrets)
    latency_ms: int = 0      # wall time before failure surfaced
    free_tier: bool = False  # was this a :free model?
    request_id: str = ""     # sessionID / vercelID for dedup; empty = append-only
    at: datetime = field(default_factory=_utcnow)

    def to_row(self) -> dict[str, Any]:
        return {
            "at": self.at.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_msg": self.error_msg[:500],
            "latency_ms": self.latency_ms,
            "free_tier": self.free_tier,
            "request_id": self.request_id,
        }


def record_failure(
    event: FailureEvent,
    path: str | os.PathLike[str] | None = None,
) -> tuple[Path, bool]:
    """Atomically append a failure event unless its request ID already exists."""
    target = Path(path).expanduser() if path else FAILURE_LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        if event.request_id:
            handle.seek(0)
            for line in deque(handle, maxlen=MAX_ROWS_SCANNED):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, Mapping) and row.get("request_id") == event.request_id:
                    return target, False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(event.to_row(), sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return target, True


def iter_failures(path: str | os.PathLike[str] | None = None) -> Iterator[FailureEvent]:
    """Yield well-formed failure events, skipping corrupt lines."""
    target = Path(path).expanduser() if path else FAILURE_LOG_PATH
    if not target.exists():
        return
    with target.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, Mapping):
                continue
            try:
                yield FailureEvent(
                    provider=str(row.get("provider", "")),
                    model=str(row.get("model", "")),
                    error_type=str(row.get("error_type", "")),
                    error_code=str(row.get("error_code", "")),
                    error_msg=str(row.get("error_msg", "")),
                    latency_ms=int(row.get("latency_ms", 0) or 0),
                    free_tier=bool(row.get("free_tier", False)),
                    request_id=str(row.get("request_id", "")),
                )
            except (TypeError, ValueError):
                continue


def failure_summary(hours: int = 24) -> dict[str, Any]:
    """Count failures by (provider, model, error_type) in the trailing window."""
    from datetime import timedelta
    cutoff = _utcnow() - timedelta(hours=hours)
    counts: dict[str, int] = {}
    total = 0
    for ev in iter_failures():
        # at is ISO; compare lexicographically (UTC ISO sorts chronologically)
        if ev.at.replace(tzinfo=None).isoformat() < cutoff.replace(tzinfo=None).isoformat():
            continue
        key = f"{ev.provider}/{ev.model} [{ev.error_type}/{ev.error_code}]"
        counts[key] = counts.get(key, 0) + 1
        total += 1
    return {"total": total, "hours": hours, "by_key": counts}
