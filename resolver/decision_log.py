"""Routing decision log — D2.6: which candidates, which floor eliminated each, ranking inputs.

Append-only JSONL. A bad route can be debugged after the fact.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from resolver.resolver import Resolution

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://model-scan/schemas/routing-decision.json",
    "title": "RoutingDecision",
    "type": "object",
    "required": ["timestamp", "lane", "outcome", "binding_id"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "lane": {"type": "string"},
        "outcome": {"type": "string", "enum": ["resolved", "resolved_with_degradation", "routing_policy_unavailable", "routing_blocked"]},
        "binding_id": {"type": ["string", "null"]},
        "degradation_notice": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
        "candidates_considered": {"type": "integer"},
        "eliminated_by_floor": {"type": "array", "items": {"type": "object"}},
        "ranking_inputs": {"type": ["object", "null"]},
        "request": {"type": "object"},
        "registry_version": {"type": "string"},
    }
}

DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "model-scan" / "routing_decisions.jsonl"


def format_decision(request: Any, resolution: Resolution, registry_version: str = "unknown") -> dict[str, Any]:
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lane": request.lane,
        "outcome": resolution.outcome,
        "binding_id": resolution.binding["binding_id"] if resolution.binding else None,
        "degradation_notice": resolution.degradation_notice,
        "reason": resolution.reason,
        "candidates_considered": resolution.candidates_considered,
        "eliminated_by_floor": resolution.eliminated_by_floor or [],
        "ranking_inputs": resolution.ranking_inputs,
        "request": {
            "lane": request.lane,
            "harness": request.harness,
            "floors": request.floors.__dict__,
            "prefer_low_cost": request.prefer_low_cost,
        },
        "registry_version": registry_version,
    }


def append_log(entry: dict[str, Any], path: Path = DEFAULT_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
