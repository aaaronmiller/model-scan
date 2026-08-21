"""Provenance-bound capability-rank maps for Gateway slot resolution.

The map is intentionally separate from scan output: capability ranks are
evidence, not a score that may be inferred from a model name or stale slot id.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"
MAX_LADDER_RANK = 18


class RankMapRejected(ValueError):
    """Raised when rank evidence cannot safely drive a Gateway resolution."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def snapshot_sha256(snapshot: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(snapshot)).hexdigest()


def _parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RankMapRejected("generated_at must be a UTC timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RankMapRejected("generated_at must be a UTC timestamp") from exc


def snapshot_api_models(snapshot: Mapping[str, Any]) -> set[str]:
    models: set[str] = set()
    slots = snapshot.get("slots")
    if not isinstance(slots, Mapping):
        raise RankMapRejected("snapshot slots are required")
    for selection in slots.values():
        if not isinstance(selection, Mapping):
            raise RankMapRejected("snapshot selection is invalid")
        candidates = selection.get("candidates")
        if not isinstance(candidates, list):
            raise RankMapRejected("snapshot candidates are required")
        for candidate in candidates:
            if not isinstance(candidate, Mapping) or not isinstance(candidate.get("api_model"), str):
                raise RankMapRejected("snapshot candidate api_model is required")
            models.add(candidate["api_model"])
    return models


def build_rank_map(
    ranks: Mapping[str, int],
    snapshot: Mapping[str, Any],
    *,
    generated_at: str,
    evidence_ref: str,
    evidence_sha256: str,
) -> dict[str, Any]:
    """Build a credential-free rank map bound to one exact snapshot."""
    document = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "snapshot_sha256": snapshot_sha256(snapshot),
        "evidence": {"ref": evidence_ref, "sha256": evidence_sha256},
        "ranks": {str(api_model): int(rank) for api_model, rank in ranks.items()},
    }
    validate_rank_map(document, snapshot)
    return document


def validate_rank_map(
    document: Any,
    snapshot: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_age_seconds: int = 86_400,
) -> dict[str, int]:
    """Validate freshness, provenance, identity coverage, and ladder bounds."""
    if not isinstance(document, Mapping) or set(document) != {
        "schema_version", "generated_at", "snapshot_sha256", "evidence", "ranks"
    }:
        raise RankMapRejected("rank map has unexpected fields")
    if str(document["schema_version"]).split(".", 1)[0] != "1":
        raise RankMapRejected("unsupported rank-map schema major")
    generated_at = _parse_utc(document["generated_at"])
    current = now or datetime.now(timezone.utc)
    if (current - generated_at).total_seconds() > max_age_seconds:
        raise RankMapRejected("rank map is stale")
    if (generated_at - current).total_seconds() > 300:
        raise RankMapRejected("rank map timestamp is implausibly future-dated")
    if document["snapshot_sha256"] != snapshot_sha256(snapshot):
        raise RankMapRejected("rank map does not match snapshot")
    evidence = document["evidence"]
    if not isinstance(evidence, Mapping) or set(evidence) != {"ref", "sha256"}:
        raise RankMapRejected("rank map evidence is required")
    if not isinstance(evidence["ref"], str) or not evidence["ref"]:
        raise RankMapRejected("rank map evidence ref is required")
    evidence_sha = evidence["sha256"]
    if not (
        isinstance(evidence_sha, str)
        and len(evidence_sha) == 71
        and evidence_sha.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in evidence_sha[7:])
    ):
        raise RankMapRejected("rank map evidence sha256 is required")
    raw_ranks = document["ranks"]
    if not isinstance(raw_ranks, Mapping):
        raise RankMapRejected("rank map ranks are required")
    expected = snapshot_api_models(snapshot)
    if set(raw_ranks) != expected:
        raise RankMapRejected("rank map api_model identities are partial or mismatched")
    ranks: dict[str, int] = {}
    for api_model, value in raw_ranks.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_LADDER_RANK:
            raise RankMapRejected("rank map ranks must be integers from 1 through 18")
        ranks[str(api_model)] = value
    return ranks
