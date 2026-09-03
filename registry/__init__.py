"""Registry loader: validates against schema, handles unknown sentinel."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

try:
    import jsonschema
except ImportError:
    jsonschema = None

SCHEMA_PATH = Path(__file__).parent / "schema.json"
REGISTRY_PATH = Path(__file__).parent / "registry.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_registry(path: Path | None = None) -> dict:
    p = path or REGISTRY_PATH
    return json.loads(p.read_text())


def validate_registry(data: dict | None = None, schema: dict | None = None) -> None:
    if jsonschema is None:
        raise RuntimeError("jsonschema not installed")
    d = data or load_registry()
    s = schema or load_schema()
    jsonschema.validate(d, s)


def is_unknown(value) -> bool:
    return value == "unknown"


def is_stale(freshness_entry: dict | None, now: datetime | None = None) -> bool:
    if not freshness_entry:
        return True
    expires = freshness_entry.get("expires_at")
    if not expires:
        return False
    try:
        exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
    except Exception:
        return True
    n = now or datetime.now(timezone.utc)
    return n >= exp


def binding_freshness(binding: dict, field: str, now: datetime | None = None) -> str:
    """Return freshness state for a field: fresh, stale, absent, unknown-field."""
    if field not in binding:
        return "absent"
    if field not in binding.get("freshness", {}):
        # field present but no stamp -> treat as stale (must be declared)
        return "stale"
    entry = binding["freshness"][field]
    if is_stale(entry, now):
        return "stale"
    return "fresh"


def all_fields_present_or_unknown(binding: dict) -> bool:
    """Acceptance gate 3: every schema field is present with freshness or explicitly unknown."""
    # Check that no field is missing without reason - unknown covers missing data
    # This is validated by schema; this helper checks freshness presence for present fields
    for field, value in binding.items():
        if field in ("binding_id", "lane", "adapter_id", "freshness", "fallback_chain"):
            continue
        if value == "unknown":
            # unknown is valid, but should still have freshness if we claim knowledge of unknown-ness
            continue
        if field not in binding.get("freshness", {}):
            return False
    return True
