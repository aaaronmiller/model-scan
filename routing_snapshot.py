"""Routing snapshot producer for claude-code-proxy integration.

This module is the only shared-data producer for the proxy integration. It converts model-scan's
in-memory dossiers or latest SQLite scan into the credential-free contract in
`contracts/routing_snapshot.schema.json`.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - dink.py already requires yaml for full scans
    yaml = None

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DEFAULT_SNAPSHOT_PATH = CONFIG_DIR / "routing_snapshot.json"
RELIABILITY_FEEDBACK_PATH = CONFIG_DIR / "reliability_feedback.jsonl"
SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class SnapshotCandidate:
    model_id: str
    provider: str
    api_model: str
    base_url: str
    fitness: float
    price_blended: float | None
    tier: str
    has_tools: bool
    has_vision: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _obj_get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _eval_mode(slot_def: Mapping[str, Any]) -> str:
    return "free" if slot_def.get("eval_mode") == "free" else "cost_basis"


def _normal_blocklist(raw: Any) -> list[str]:
    if not isinstance(raw, Mapping):
        return []
    values: list[str] = []
    for key in ("exact", "patterns"):
        items = raw.get(key, [])
        if isinstance(items, list):
            values.extend(str(item) for item in items if item)
    for items in raw.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, Mapping):
                pattern = item.get("pattern")
                if pattern:
                    values.append(str(pattern))
    return sorted(set(values))


def load_blocklist_values(path: str | os.PathLike[str] | None = None) -> list[str]:
    """Load blocklisted model strings/patterns for the snapshot contract."""
    p = Path(path) if path else CONFIG_DIR / "blocklist.yaml"
    if yaml is None or not p.exists():
        return []
    try:
        return _normal_blocklist(yaml.safe_load(p.read_text()) or {})
    except Exception:
        return []


def load_provider_quota(path: str | os.PathLike[str] | None = None) -> dict[str, dict[str, Any]]:
    """Load optional provider quota state for snapshot publication."""
    p = Path(path).expanduser() if path else CONFIG_DIR / "provider_quota.json"
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, Mapping):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for provider, item in data.items():
        if not isinstance(item, Mapping) or "remaining_fraction" not in item:
            continue
        try:
            remaining = max(0.0, min(1.0, float(item["remaining_fraction"])))
        except (TypeError, ValueError):
            continue
        entry: dict[str, Any] = {"remaining_fraction": remaining}
        for key in ("reset_at", "unit", "best_tier_available", "source"):
            if item.get(key):
                entry[key] = str(item[key])
        result[str(provider).lower()] = entry
    return result


def load_reliability_feedback(
    path: str | os.PathLike[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Load latest router reliability rows, keyed by provider."""
    p = Path(path).expanduser() if path else RELIABILITY_FEEDBACK_PATH
    if not p.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    try:
        lines = p.read_text(encoding="utf-8").splitlines()[-100:]
    except OSError:
        return {}
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        providers = row.get("providers")
        if not isinstance(providers, Mapping):
            continue
        for provider, metrics in providers.items():
            if isinstance(metrics, Mapping):
                latest[str(provider).lower()] = dict(metrics)
    return latest


def _matches_blocklist(provider: str, model_id: str, api_model: str, blocklist: Iterable[str]) -> bool:
    haystacks = (model_id, api_model, f"{provider}/{model_id}")
    for item in blocklist:
        if not item:
            continue
        if item in haystacks:
            return True
        pattern = str(item).replace("*", ".*")
        try:
            if any(re.search(pattern, h, re.IGNORECASE) for h in haystacks):
                return True
        except re.error:
            continue
    return False


def _candidate_from_dossier(dossier: Any, slot_id: str, blocklist: Iterable[str]) -> SnapshotCandidate | None:
    provider = str(_obj_get(dossier, "provider", "") or "")
    model_id = str(_obj_get(dossier, "model", "") or _obj_get(dossier, "model_id", "") or "")
    api_model = str(_obj_get(dossier, "api_model", "") or f"{provider}/{model_id}")
    fitness = float((_obj_get(dossier, "slot_fitness", {}) or {}).get(slot_id, 0) or 0)
    if not _obj_get(dossier, "accessible", False) or fitness <= 0:
        return None
    if _matches_blocklist(provider, model_id, api_model, blocklist):
        return None
    return SnapshotCandidate(
        model_id=model_id,
        provider=provider,
        api_model=api_model,
        base_url="",
        fitness=round(fitness, 3),
        price_blended=_obj_get(dossier, "price_blended"),
        tier=str(_obj_get(dossier, "tier", "unknown") or "unknown"),
        has_tools=bool(_obj_get(dossier, "has_tools", False)),
        has_vision=bool(_obj_get(dossier, "has_vision_capability", False) or _obj_get(dossier, "has_vision", False)),
    )


def provider_health_from_dossiers(
    dossiers: Iterable[Any],
    reliability_feedback: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    counts: dict[str, list[int]] = {}
    for d in dossiers:
        provider = str(_obj_get(d, "provider", "") or "")
        if not provider:
            continue
        total, ok = counts.setdefault(provider, [0, 0])
        counts[provider] = [total + 1, ok + (1 if _obj_get(d, "accessible", False) else 0)]
    health: dict[str, str] = {}
    for provider, (total, ok) in counts.items():
        if ok == 0:
            health[provider] = "down"
        elif ok < total:
            health[provider] = "degraded"
        else:
            health[provider] = "ok"
    health_key_by_lower = {provider.lower(): provider for provider in health}
    for provider, metrics in (reliability_feedback or {}).items():
        error_rate = float(metrics.get("error_rate", 0) or 0)
        rate_limited = float(metrics.get("rate_limit_frequency", 0) or 0)
        health_key = health_key_by_lower.get(str(provider).lower())
        if health_key is None:
            continue
        if error_rate >= 0.8:
            health[health_key] = "down"
        elif error_rate >= 0.25 or rate_limited >= 0.25:
            health[health_key] = "degraded"
    return health


def build_snapshot_from_dossiers(
    dossiers: Iterable[Any],
    slot_defs: Mapping[str, Mapping[str, Any]],
    *,
    scan_id: int,
    blocklist: Iterable[str] | None = None,
    provider_quota: Mapping[str, Mapping[str, Any]] | None = None,
    reliability_feedback: Mapping[str, Mapping[str, Any]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a routing snapshot from the active scan's in-memory dossiers."""
    dossier_list = list(dossiers)
    blocked = sorted(set(str(x) for x in (blocklist or []) if x))
    slots: dict[str, Any] = {}
    for slot_id, slot_def in slot_defs.items():
        candidates = [
            c
            for c in (_candidate_from_dossier(d, slot_id, blocked) for d in dossier_list)
            if c is not None
        ]
        candidates.sort(key=lambda c: c.fitness, reverse=True)
        candidate_dicts = [asdict(c) for c in candidates]
        slots[slot_id] = {
            "label": str(slot_def.get("label", slot_id)),
            "eval_mode": _eval_mode(slot_def),
            "best": candidate_dicts[0] if candidate_dicts else None,
            "candidates": candidate_dicts,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _utc_now(),
        "scan_id": int(scan_id or 0),
        "provider_health": provider_health_from_dossiers(dossier_list, reliability_feedback),
        "blocklist": blocked,
        "provider_quota": dict(provider_quota or {}),
        "slots": slots,
    }


def write_snapshot(snapshot: Mapping[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    """Atomically write a routing snapshot JSON file."""
    target = Path(path).expanduser() if path else DEFAULT_SNAPSHOT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snapshot, indent=2, sort_keys=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name, suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        Path(tmp_name).replace(target)
    finally:
        tmp = Path(tmp_name)
        if tmp.exists():
            tmp.unlink()
    return target


def load_latest_snapshot(path: str | os.PathLike[str] | None = None) -> dict[str, Any] | None:
    target = Path(path).expanduser() if path else DEFAULT_SNAPSHOT_PATH
    try:
        data = json.loads(target.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_slot_defs(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    p = Path(path) if path else CONFIG_DIR / "slot_definitions.yaml"
    if yaml is None or not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {}


def build_snapshot_from_db(
    db_path: str | os.PathLike[str] | None = None,
    *,
    slot_defs_path: str | os.PathLike[str] | None = None,
    blocklist_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    """Rebuild the latest routing snapshot from SQLite for gateway fallback."""
    db = Path(db_path) if db_path else CONFIG_DIR / "model_scan.db"
    if not db.exists():
        return None
    slot_defs = _load_slot_defs(slot_defs_path)
    if not slot_defs:
        return None
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT MAX(scan_id) AS scan_id FROM scans").fetchone()
        scan_id = int(row["scan_id"]) if row and row["scan_id"] is not None else 0
        if not scan_id:
            return None
        rows = conn.execute(
            """
            SELECT m.*, sf.slot_id, sf.fitness
            FROM models m
            JOIN slot_fitness sf ON sf.model_fk = m.model_pk
            WHERE m.scan_id = ? AND sf.scan_id = ? AND m.accessible = 1
            ORDER BY sf.slot_id, sf.fitness DESC
            """,
            (scan_id, scan_id),
        ).fetchall()
        by_model: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            d = dict(row)
            key = (d.get("provider", ""), d.get("model_id", ""))
            item = by_model.setdefault(
                key,
                {
                    "provider": d.get("provider", ""),
                    "model": d.get("model_id", ""),
                    "api_model": d.get("api_model", ""),
                    "accessible": bool(d.get("accessible")),
                    "has_tools": bool(d.get("has_tools")),
                    "has_vision_capability": bool(d.get("has_vision")),
                    "price_blended": d.get("price_blended"),
                    "tier": d.get("tier") or "unknown",
                    "slot_fitness": {},
                },
            )
            item["slot_fitness"][d["slot_id"]] = d["fitness"]
        return build_snapshot_from_dossiers(
            by_model.values(),
            slot_defs,
            scan_id=scan_id,
            blocklist=load_blocklist_values(blocklist_path),
            provider_quota=load_provider_quota(),
            reliability_feedback=load_reliability_feedback(),
        )
    finally:
        conn.close()
