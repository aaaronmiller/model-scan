"""Build and validate a portable, immutable ARDF input for Model Scan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_contract import canonical_json_bytes

EXPORT_VERSION = "1.0.0"
AUTHORITATIVE_FILES = {
    "data/unified-model-evidence.csv": "evidence-ledger",
    "project-config.json": "policy",
    "calibrate.py": "calibration-code",
    "dashboard.html": "dashboard-projection",
    "pareto-frontier-cheatsheet.md": "pareto-projection",
    "model-tiers-and-contenders.md": "tier-projection",
    "user-prompt-aggregation.md": "intent-source",
    "ardf-research-paper.md": "methodology",
    "INDEX.md": "authority-map",
}
SUPPORT_FILES = {
    "schemas/unified_observations.schema.json": "ledger-schema",
    "schemas/calibration_config.schema.json": "policy-schema",
}


class ArdfExportRejected(ValueError):
    """Raised when ARDF cannot produce a safe Model Scan input."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ArdfExportRejected(f"expected object: {path.name}")
    return value


def _csv_shape(path: Path) -> tuple[list[str], int]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        count = sum(1 for _ in reader)
    if not fields:
        raise ArdfExportRejected("ARDF ledger has no header")
    return fields, count


IDENTITY_FIELDS = {
    "model_key",
    "display_name",
    "provider",
    "family",
    "effort",
    "harness",
    "release_date",
    "availability",
    "is_open_weights",
    "context_window_tokens",
    "official_model_id",
}
SOURCE_FIELDS = {
    "source_id",
    "source_label",
    "source_publisher",
    "source_version",
    "source_date",
    "source_url",
    "source_mirror_url",
    "retrieved_at",
    "quality",
    "confidence",
    "base_weight",
    "use_in_aggregate",
    "is_historical",
    "identity_mapping",
    "notes",
    "source_refresh_status",
    "source_original_id",
    "is_vendor_reported",
    "is_independent_source",
    "data_freshness_class",
}
OBSERVATION_FIELDS = {
    "record_type",
    "observation_id",
    "input_price_per_m",
    "output_price_per_m",
    "metric_axis",
    "metric_name",
    "raw_value",
    "raw_unit",
    "raw_direction",
    "is_reference_scale",
    "calibration_group",
    "benchmark_domain",
    "benchmark_harness",
    "benchmark_version_exact",
}


def map_ardf_field(field: str) -> dict[str, str]:
    """Return an explicit migration disposition for one ARDF column."""

    if field in IDENTITY_FIELDS:
        return {
            "source_field": field,
            "target_family": "model_identity",
            "target_field": field,
            "mode": "retained",
            "reason": "Exact model, provider, harness, or configuration identity.",
        }
    if field in SOURCE_FIELDS:
        return {
            "source_field": field,
            "target_family": "source_snapshot",
            "target_field": field,
            "mode": "retained",
            "reason": "Source custody, provenance, freshness, or quality evidence.",
        }
    if field in OBSERVATION_FIELDS:
        return {
            "source_field": field,
            "target_family": "published_observation",
            "target_field": field,
            "mode": "retained",
            "reason": "Atomic published evidence or its observation grain.",
        }
    if field.startswith("cal_") or field.startswith("calibrated_"):
        return {
            "source_field": field,
            "target_family": "calibration_result",
            "target_field": field,
            "mode": "transformed",
            "reason": "Split into an algorithm-bound result with exact input and policy hashes.",
        }
    if field.startswith("models_dev_"):
        identity_markers = (
            "model_id",
            "name",
            "lab",
            "family",
            "release_date",
            "last_updated",
            "knowledge_cutoff",
            "reasoning",
            "status",
            "context_tokens",
            "input_limit_tokens",
            "output_limit_tokens",
            "modalities",
            "open_weights",
            "license",
            "provider_",
            "tool_call",
            "structured_output",
            "attachment",
            "temperature",
            "interleaved",
            "parameters",
            "weights_json",
            "links_json",
        )
        family = "model_identity" if any(marker in field for marker in identity_markers) else "published_observation"
        return {
            "source_field": field,
            "target_family": family,
            "target_field": field,
            "mode": "retained",
            "reason": "Preserve models.dev data with its source-specific field provenance.",
        }
    return {
        "source_field": field,
        "target_family": "published_observation",
        "target_field": field,
        "mode": "unsupported",
        "reason": "No accepted migration rule exists for this source field.",
    }


def build_field_migration(fields: list[str]) -> list[dict[str, str]]:
    if len(fields) != len(set(fields)):
        raise ArdfExportRejected("ARDF ledger contains duplicate field names")
    return [map_ardf_field(field) for field in fields]


def build_export(root: str | Path, *, generated_at: str | None = None) -> dict[str, Any]:
    package = Path(root)
    declared = {**AUTHORITATIVE_FILES, **SUPPORT_FILES}
    missing = [relative for relative in declared if not (package / relative).is_file()]
    if missing:
        raise ArdfExportRejected(f"missing ARDF export files: {', '.join(sorted(missing))}")

    fields, row_count = _csv_shape(package / "data/unified-model-evidence.csv")
    observation_schema = _json(package / "schemas/unified_observations.schema.json")
    declared_row_count = observation_schema.get("x-row-count")
    if declared_row_count != row_count:
        raise ArdfExportRejected(
            f"row count mismatch: schema={declared_row_count}, ledger={row_count}"
        )
    schema_columns = observation_schema.get("x-columns")
    if schema_columns != fields:
        raise ArdfExportRejected("schema x-columns do not exactly match the ledger header")

    policy = _json(package / "project-config.json")
    executor = policy.get("analysis", {}).get("executor", {})
    if executor.get("minimum_aggregate_capability") is not None:
        raise ArdfExportRejected("ARDF export contains an unscoped global capability floor")

    files = [
        {
            "path": relative,
            "role": declared[relative],
            "sha256": _sha256(package / relative),
            "bytes": (package / relative).stat().st_size,
        }
        for relative in sorted(declared)
    ]
    present = {
        str(path.relative_to(package))
        for path in package.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    extras = sorted(present - set(declared))
    migration = build_field_migration(fields)
    unsupported = [item["source_field"] for item in migration if item["mode"] == "unsupported"]
    if unsupported:
        raise ArdfExportRejected(
            f"unmapped ARDF fields: {', '.join(unsupported)}"
        )
    return {
        "export_version": EXPORT_VERSION,
        "generated_at": generated_at or utc_now(),
        "source_authority": "ardf",
        "consumer": "model-scan",
        "row_count": row_count,
        "field_count": len(fields),
        "files": files,
        "excluded_supporting_files": extras,
        "field_migration": migration,
        "policy_disposition": {
            "global_executor_capability_floor": "none",
            "role_specific_gates": "consumer-visible-only",
            "exact_zero_price": "preserve",
        },
    }


def validate_export(root: str | Path, export: dict[str, Any]) -> int:
    package = Path(root)
    if export.get("export_version") != EXPORT_VERSION:
        raise ArdfExportRejected("unsupported ARDF export version")
    expected = build_export(package, generated_at=export.get("generated_at"))
    if canonical_json_bytes(export) != canonical_json_bytes(expected):
        raise ArdfExportRejected("ARDF export does not match current bound inputs")
    return 8


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a portable Model Scan ARDF export manifest")
    parser.add_argument("--root", required=True)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    export = build_export(args.root, generated_at=args.generated_at)
    validate_export(args.root, export)
    print(json.dumps(export, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
