"""Independent capability evidence publisher for the Clutch Gateway boundary."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0.0"
VALID_HEALTH = frozenset({"healthy", "degraded", "unreachable", "unknown"})
RECORD_FIELDS = frozenset(
    {
        "capability_id",
        "model_identity",
        "dimensions",
        "features",
        "health",
        "cost",
        "latency_ms",
        "confidence",
        "evidence_refs",
        "measured_at",
    }
)
CALLABLE_FIELDS = frozenset(
    {"provider_id", "api_model_id", "base_url", "credential_ref", "callable_id"}
)
DEFAULT_OUTPUT_PATH = (
    Path.home() / ".config" / "model-scan" / "capability_evidence.json"
)


class CapabilityEvidenceRejected(ValueError):
    """Raised before publication when capability evidence is unsafe."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _obj_get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _health(dossier: Any) -> str:
    accessible = _obj_get(dossier, "accessible")
    if accessible is False:
        return "unreachable"
    if accessible is not True:
        return "unknown"
    reliability = _number(_obj_get(dossier, "reliability"))
    if reliability is not None and reliability < 0.8:
        return "degraded"
    return "healthy"


def _dimensions(dossier: Any) -> dict[str, float]:
    dimensions: dict[str, float] = {}
    slot_fitness = _obj_get(dossier, "slot_fitness", {})
    if isinstance(slot_fitness, Mapping):
        for key, value in slot_fitness.items():
            number = _number(value)
            if number is not None:
                dimensions[f"slot:{key}"] = number
    for key in (
        "fitness",
        "composite_score",
        "intelligence_score",
        "coding_score",
        "agentic_score",
    ):
        number = _number(_obj_get(dossier, key))
        if number is not None:
            dimensions[key] = number
    return dict(sorted(dimensions.items()))


def _features(dossier: Any) -> list[str]:
    features: list[str] = []
    if bool(_obj_get(dossier, "has_tools", _obj_get(dossier, "tools", False))):
        features.append("tools")
    if bool(
        _obj_get(
            dossier,
            "has_vision_capability",
            _obj_get(dossier, "has_vision", False),
        )
    ):
        features.append("vision")
    context = _number(_obj_get(dossier, "context_length", _obj_get(dossier, "ctx")))
    if context is not None:
        features.append(f"context:{int(context)}")
    return features


def _cost(dossier: Any) -> dict[str, float | None]:
    return {
        "input_per_million": _number(
            _obj_get(dossier, "price_input", _obj_get(dossier, "input_price"))
        ),
        "output_per_million": _number(
            _obj_get(dossier, "price_output", _obj_get(dossier, "output_price"))
        ),
        "blended_per_million": _number(_obj_get(dossier, "price_blended")),
    }


def _latency_ms(dossier: Any) -> float | None:
    direct = _number(_obj_get(dossier, "latency_ms"))
    if direct is not None:
        return direct
    seconds = _number(
        _obj_get(
            dossier,
            "lat_s",
            _obj_get(dossier, "latency_seconds"),
        )
    )
    return None if seconds is None else seconds * 1000


def _record(
    dossier: Any,
    *,
    measured_at: str,
    evidence_ref: str,
) -> dict[str, Any]:
    model_identity = str(
        _obj_get(
            dossier,
            "model_identity",
            _obj_get(dossier, "model", _obj_get(dossier, "model_id", "")),
        )
        or ""
    )
    provider_identity = str(_obj_get(dossier, "provider", "") or "unknown")
    if not model_identity:
        raise CapabilityEvidenceRejected("model identity is required")
    confidence = _number(_obj_get(dossier, "confidence"))
    if confidence is None:
        confidence = 0.0
    return {
        "capability_id": (f"model-scan:{provider_identity.lower()}:{model_identity}"),
        "model_identity": model_identity,
        "dimensions": _dimensions(dossier),
        "features": _features(dossier),
        "health": _health(dossier),
        "cost": _cost(dossier),
        "latency_ms": _latency_ms(dossier),
        "confidence": confidence,
        "evidence_refs": [evidence_ref],
        "measured_at": measured_at,
    }


def build_evidence(
    dossiers: Iterable[Any],
    *,
    generated_at: str,
    source: str,
    evidence_ref: str,
) -> dict[str, Any]:
    document = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "source": source,
        "records": [
            _record(
                dossier,
                measured_at=generated_at,
                evidence_ref=evidence_ref,
            )
            for dossier in dossiers
        ],
    }
    validate(document)
    return document


def _valid_utc(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate(document: Any) -> None:
    if not isinstance(document, dict):
        raise CapabilityEvidenceRejected("evidence must be an object")
    if set(document) != {"schema_version", "generated_at", "source", "records"}:
        raise CapabilityEvidenceRejected("unexpected top-level evidence fields")
    if document["schema_version"].split(".", 1)[0] != "1":
        raise CapabilityEvidenceRejected("unsupported schema major")
    if not _valid_utc(document["generated_at"]):
        raise CapabilityEvidenceRejected("generated_at must be a UTC timestamp")
    if not document["source"] or not isinstance(document["records"], list):
        raise CapabilityEvidenceRejected("source and records are required")

    seen: set[str] = set()
    for record in document["records"]:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise CapabilityEvidenceRejected("invalid capability record fields")
        if set(record) & CALLABLE_FIELDS:
            raise CapabilityEvidenceRejected("callable fields are forbidden")
        capability_id = record["capability_id"]
        if not capability_id or capability_id in seen:
            raise CapabilityEvidenceRejected(
                "capability_id values must be nonempty and unique"
            )
        seen.add(capability_id)
        if not record["model_identity"]:
            raise CapabilityEvidenceRejected("model_identity is required")
        if record["health"] not in VALID_HEALTH:
            raise CapabilityEvidenceRejected("invalid health value")
        if not isinstance(record["dimensions"], dict):
            raise CapabilityEvidenceRejected("dimensions must be an object")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in record["dimensions"].values()
        ):
            raise CapabilityEvidenceRejected("dimensions must be numeric")
        if len(record["features"]) != len(set(record["features"])):
            raise CapabilityEvidenceRejected("features must be unique")
        if not 0 <= record["confidence"] <= 1:
            raise CapabilityEvidenceRejected("confidence must be between 0 and 1")
        if not record["evidence_refs"]:
            raise CapabilityEvidenceRejected("evidence references are required")
        if not _valid_utc(record["measured_at"]):
            raise CapabilityEvidenceRejected("measured_at must be a UTC timestamp")
        if set(record["cost"]) != {
            "input_per_million",
            "output_per_million",
            "blended_per_million",
        }:
            raise CapabilityEvidenceRejected("invalid cost fields")
        for value in (*record["cost"].values(), record["latency_ms"]):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            ):
                raise CapabilityEvidenceRejected(
                    "cost and latency values must be nonnegative or null"
                )


def last_known_good_path(path: str | Path) -> Path:
    target = Path(path).expanduser()
    return target.with_name(f"{target.stem}.last-known-good{target.suffix}")


def _atomic_write(document: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_name = handle.name
            os.chmod(temp_name, 0o600)
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def publish(document: dict[str, Any], path: str | Path) -> Path:
    validate(document)
    target = Path(path).expanduser()
    _atomic_write(document, last_known_good_path(target))
    _atomic_write(document, target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish Model Scan capability evidence from dossier JSON"
    )
    parser.add_argument("--dossiers", required=True)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--generated-at")
    parser.add_argument("--source", default="model-scan:dossiers")
    parser.add_argument("--evidence-ref", required=True)
    args = parser.parse_args()

    raw = json.loads(Path(args.dossiers).read_text(encoding="utf-8"))
    dossiers = raw.get("dossiers") if isinstance(raw, dict) else raw
    if not isinstance(dossiers, list):
        raise CapabilityEvidenceRejected(
            "dossier input must be an array or an object with dossiers"
        )
    document = build_evidence(
        dossiers,
        generated_at=args.generated_at or utc_now(),
        source=args.source,
        evidence_ref=args.evidence_ref,
    )
    print(publish(document, args.output))


if __name__ == "__main__":
    main()
