"""Immutable Model Scan evidence content and external manifest contract."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

CONTENT_SCHEMA_VERSION = "1.0.0"
MANIFEST_SCHEMA_VERSION = "1.0.0"
CANONICALIZATION = "model-scan-json-v1"
MISSING_REASONS = frozenset(
    {"unsupported", "redacted", "collection_failed", "not_applicable"}
)
SOURCE_TIERS = frozenset(
    {
        "official_primary",
        "official_secondary",
        "independent_benchmark",
        "local_runtime",
        "user_snapshot",
        "derived",
    }
)


class EvidenceContractRejected(ValueError):
    """Raised when content or a manifest fails a named contract check."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _reject(code: str, message: str) -> None:
    raise EvidenceContractRejected(code, message)


def _require_object(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _reject(code, "value must be an object")
    return value


def _require_list(value: Any, code: str) -> list[Any]:
    if not isinstance(value, list):
        _reject(code, "value must be an array")
    return value


def _required(record: Mapping[str, Any], fields: Iterable[str], code: str) -> None:
    missing = sorted(set(fields) - set(record))
    if missing:
        _reject(code, f"missing fields: {', '.join(missing)}")


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        _reject(code, "timestamp must be UTC and end in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _reject(code, "timestamp is not valid ISO 8601")
    if parsed.tzinfo is None:
        _reject(code, "timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _sha256(value: Any, code: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _reject(code, "value must be a lowercase SHA-256 digest")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize with the versioned Model Scan canonical JSON profile.

    The profile is UTF-8 JSON, sorted object keys, no insignificant whitespace,
    no ASCII escaping, and no NaN or infinity. It is deliberately named rather
    than mislabeled as full RFC 8785 support.
    """

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        _reject("canonical-json", str(error))
    return encoded.encode("utf-8")


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _unique_records(records: list[Any], field: str, code: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for raw in records:
        record = _require_object(raw, code)
        identifier = record.get(field)
        if not isinstance(identifier, str) or not identifier:
            _reject(code, f"{field} must be a nonempty string")
        if identifier in result:
            _reject(code, f"duplicate {field}: {identifier}")
        result[identifier] = record
    return result


def _validate_metric(metric: Any, name: str) -> None:
    item = _require_object(metric, "runtime-metric")
    _required(item, {"availability", "value", "reason"}, "runtime-metric")
    availability = item["availability"]
    value = item["value"]
    reason = item["reason"]
    if availability == "available":
        if value is None or reason is not None:
            _reject(
                "runtime-metric",
                f"available metric {name} needs a value and null reason",
            )
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _reject("runtime-metric", f"metric {name} must be numeric")
        if not math.isfinite(float(value)) or float(value) < 0:
            _reject("runtime-metric", f"metric {name} must be finite and nonnegative")
    elif availability == "unavailable":
        if value is not None or reason not in MISSING_REASONS:
            _reject(
                "runtime-metric",
                f"unavailable metric {name} needs a named missing reason",
            )
    else:
        _reject("runtime-metric", f"invalid availability for {name}")


def validate_content(content: Any) -> int:
    """Validate schema-critical and cross-record evidence obligations."""

    document = _require_object(content, "content")
    required_top = {
        "schema_version",
        "evidence_version",
        "generated_at",
        "authority",
        "source_snapshots",
        "model_identities",
        "published_observations",
        "runtime_observations",
        "calibration_results",
        "role_evaluations",
        "advisory_snapshot",
    }
    _required(document, required_top, "content")
    forbidden_top = {"content_sha256", "manifest", "validation", "signature"}
    if forbidden_top & set(document):
        _reject("circular-receipt", "content cannot attest to its own digest or validation")
    if document["schema_version"] != CONTENT_SCHEMA_VERSION:
        _reject("schema-version", "unsupported content schema version")
    if not isinstance(document["evidence_version"], str) or not document["evidence_version"]:
        _reject("evidence-version", "evidence_version is required")
    generated_at = _parse_utc(document["generated_at"], "generated-at")

    authority = _require_object(document["authority"], "authority")
    expected_authority = {
        "research_owner": "ardf",
        "evidence_owner": "model-scan",
        "routing_owner": "gateway",
        "decision_owner": "living-documents",
        "non_authority": True,
    }
    if dict(authority) != expected_authority:
        _reject("authority", "authority boundary does not match the accepted contract")

    sources = _unique_records(
        _require_list(document["source_snapshots"], "source-snapshots"),
        "source_snapshot_id",
        "source-snapshot",
    )
    identities = _unique_records(
        _require_list(document["model_identities"], "model-identities"),
        "identity_id",
        "model-identity",
    )
    observations = _unique_records(
        _require_list(document["published_observations"], "published-observations"),
        "observation_id",
        "published-observation",
    )
    runtime = _unique_records(
        _require_list(document["runtime_observations"], "runtime-observations"),
        "runtime_observation_id",
        "runtime-observation",
    )
    calibrations = _unique_records(
        _require_list(document["calibration_results"], "calibration-results"),
        "calibration_id",
        "calibration-result",
    )
    roles = _unique_records(
        _require_list(document["role_evaluations"], "role-evaluations"),
        "role_evaluation_id",
        "role-evaluation",
    )

    for source in sources.values():
        _required(
            source,
            {
                "source_snapshot_id",
                "source_id",
                "tier",
                "verification",
                "retrieved_at",
                "sha256",
                "privacy",
                "freshness",
            },
            "source-snapshot",
        )
        if source["tier"] not in SOURCE_TIERS:
            _reject("source-tier", f"invalid source tier: {source['tier']}")
        if source["verification"] not in {
            "verified",
            "provisional",
            "superseded",
            "quarantined",
            "failed",
        }:
            _reject("source-verification", "invalid source verification state")
        source_id = source["source_id"]
        if not isinstance(source_id, str) or not source_id or source_id.startswith(("/", "file:")):
            _reject("portable-source", "portable content needs a stable source ID, not a local path")
        retrieved_at = _parse_utc(source["retrieved_at"], "source-time")
        if retrieved_at > generated_at:
            _reject("source-time", "source retrieval cannot occur after publication")
        _sha256(source["sha256"], "source-sha256")
        freshness = _require_object(source["freshness"], "source-freshness")
        _required(freshness, {"evaluated_at", "state", "valid_until"}, "source-freshness")
        evaluated_at = _parse_utc(freshness["evaluated_at"], "source-freshness")
        if evaluated_at > generated_at:
            _reject("source-freshness", "freshness evaluation cannot postdate publication")
        if freshness["state"] not in {"current", "aging", "stale", "superseded", "unknown"}:
            _reject("source-freshness", "invalid freshness state")
        if freshness["valid_until"] is not None:
            valid_until = _parse_utc(freshness["valid_until"], "source-freshness")
            if freshness["state"] == "current" and valid_until < evaluated_at:
                _reject("source-freshness", "current source cannot be past valid_until")

    callable_keys: set[tuple[Any, ...]] = set()
    for identity in identities.values():
        _required(
            identity,
            {
                "identity_id",
                "provider",
                "api_model",
                "harness",
                "endpoint_class",
                "effort",
                "lifecycle",
                "source_snapshot_ids",
            },
            "model-identity",
        )
        callable_key = tuple(
            identity[field]
            for field in ("provider", "api_model", "harness", "endpoint_class", "effort")
        )
        if callable_key in callable_keys:
            _reject("duplicate-callable", f"duplicate callable key: {callable_key}")
        callable_keys.add(callable_key)
        source_ids = _require_list(identity["source_snapshot_ids"], "identity-sources")
        if not source_ids or any(source_id not in sources for source_id in source_ids):
            _reject("identity-source-join", "identity has an unresolved source reference")

    zero_price_observations: set[str] = set()
    for observation in observations.values():
        _required(
            observation,
            {
                "observation_id",
                "identity_id",
                "source_snapshot_id",
                "dimension",
                "metric",
                "value_state",
                "value",
                "unit",
                "observed_at",
                "confidence",
                "missing_reason",
            },
            "published-observation",
        )
        if observation["identity_id"] not in identities:
            _reject("observation-identity-join", "observation identity does not resolve")
        if observation["source_snapshot_id"] not in sources:
            _reject("observation-source-join", "observation source does not resolve")
        observed_at = _parse_utc(observation["observed_at"], "observation-time")
        source_time = _parse_utc(
            sources[observation["source_snapshot_id"]]["retrieved_at"], "source-time"
        )
        if observed_at > source_time:
            _reject("observation-time", "observation cannot postdate its source retrieval")
        state = observation["value_state"]
        value = observation["value"]
        missing_reason = observation["missing_reason"]
        if state == "known":
            if value is None or missing_reason is not None:
                _reject("value-state", "known values need data and a null missing reason")
        elif state in {"unknown", "not_applicable"}:
            if value is not None or missing_reason not in MISSING_REASONS:
                _reject("value-state", "missing values need a named reason and null value")
        else:
            _reject("value-state", "invalid value state")
        if observation["dimension"] == "monetary_token_price" and value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                _reject("monetary-price", "monetary price must be nonnegative")
            if value == 0:
                zero_price_observations.add(observation["observation_id"])

    for item in runtime.values():
        _required(
            item,
            {
                "runtime_observation_id",
                "task_id",
                "attempt_id",
                "role",
                "fixture_id",
                "identity_id",
                "started_at",
                "ended_at",
                "metrics",
                "outcome",
                "privacy",
            },
            "runtime-observation",
        )
        if item["identity_id"] not in identities:
            _reject("runtime-identity-join", "runtime identity does not resolve")
        started_at = _parse_utc(item["started_at"], "runtime-time")
        ended_at = _parse_utc(item["ended_at"], "runtime-time")
        if ended_at < started_at or ended_at > generated_at:
            _reject("runtime-time", "runtime time order is invalid")
        metrics = _require_object(item["metrics"], "runtime-metrics")
        required_metrics = {"input_tokens", "cached_input_tokens", "output_tokens"}
        if not required_metrics <= set(metrics):
            _reject("runtime-metrics", "token counters must remain separate")
        for name, metric in metrics.items():
            _validate_metric(metric, name)
        privacy = _require_object(item["privacy"], "runtime-privacy")
        if privacy.get("raw_prompt_stored") is not False or privacy.get("raw_output_stored") is not False:
            _reject("runtime-privacy", "raw prompt and output storage is forbidden")
        retention_days = privacy.get("retention_days")
        if isinstance(retention_days, bool) or not isinstance(retention_days, int) or not 0 <= retention_days <= 365:
            _reject("runtime-privacy", "retention_days must be between 0 and 365")

    for result in calibrations.values():
        _required(
            result,
            {
                "calibration_id",
                "axis",
                "observation_ids",
                "algorithm_id",
                "config_sha256",
                "zero_policy",
                "output",
                "abstention_reason",
                "generated_at",
            },
            "calibration-result",
        )
        input_ids = _require_list(result["observation_ids"], "calibration-inputs")
        if not input_ids or any(item not in observations for item in input_ids):
            _reject("calibration-join", "calibration input does not resolve")
        _sha256(result["config_sha256"], "calibration-config")
        calibration_time = _parse_utc(result["generated_at"], "calibration-time")
        if calibration_time > generated_at:
            _reject("calibration-time", "calibration cannot postdate publication")
        if result["output"] is None and not result["abstention_reason"]:
            _reject("calibration-abstention", "missing output needs an abstention reason")
        if result["output"] is not None and result["abstention_reason"] is not None:
            _reject("calibration-abstention", "successful output cannot claim abstention")
        if (
            result["axis"] == "cost"
            and zero_price_observations.intersection(input_ids)
            and result["zero_policy"] == "positive_log"
        ):
            _reject("zero-price-geometry", "exact zero cannot enter positive-log calibration")

    evidence_version = document["evidence_version"]
    for evaluation in roles.values():
        _required(
            evaluation,
            {
                "role_evaluation_id",
                "role_id",
                "fixture_set_id",
                "evidence_version",
                "candidates",
                "decision",
                "recommended_identity_id",
                "reason",
            },
            "role-evaluation",
        )
        if evaluation["evidence_version"] != evidence_version:
            _reject("role-version-join", "role evaluation uses another evidence version")
        candidates = _require_list(evaluation["candidates"], "role-candidates")
        by_identity: dict[str, Mapping[str, Any]] = {}
        for raw_candidate in candidates:
            candidate = _require_object(raw_candidate, "role-candidate")
            _required(candidate, {"identity_id", "gates", "score", "confidence", "sample_count"}, "role-candidate")
            identity_id = candidate["identity_id"]
            if identity_id not in identities or identity_id in by_identity:
                _reject("role-candidate-join", "role candidate is unresolved or duplicated")
            by_identity[identity_id] = candidate
        decision = evaluation["decision"]
        recommended = evaluation["recommended_identity_id"]
        if decision == "recommend":
            if recommended not in by_identity:
                _reject("role-recommendation", "recommended identity was not evaluated")
            candidate = by_identity[recommended]
            gates = _require_list(candidate["gates"], "role-gates")
            if not gates or any(not isinstance(gate, Mapping) or gate.get("passed") is not True for gate in gates):
                _reject("role-gates", "recommendation requires every minimum gate to pass")
            if candidate["confidence"] in {"insufficient", "unknown"} or candidate["score"] is None:
                _reject("role-confidence", "recommendation needs adequate confidence and score")
            if identities[recommended]["lifecycle"] != "current":
                _reject("role-lifecycle", "recommendation needs a current callable identity")
            identity_sources = identities[recommended]["source_snapshot_ids"]
            if any(sources[source_id]["freshness"]["state"] != "current" for source_id in identity_sources):
                _reject("role-freshness", "recommendation needs current identity sources")
        elif decision == "abstain":
            if recommended is not None or not evaluation["reason"]:
                _reject("role-abstention", "abstention needs no recommendation and a reason")
        else:
            _reject("role-decision", "decision must be recommend or abstain")

    advisory = _require_object(document["advisory_snapshot"], "advisory")
    _required(
        advisory,
        {"evidence_version", "non_authority", "role_evaluation_ids", "recommendations"},
        "advisory",
    )
    if advisory["evidence_version"] != evidence_version or advisory["non_authority"] is not True:
        _reject("advisory-authority", "advisory must be bound and non-authoritative")
    forbidden_advisory = {"apply", "route", "fallback_chain", "credential", "config_patch"}
    if forbidden_advisory & set(advisory):
        _reject("advisory-action", "advisory content cannot contain an executable action")
    role_ids = _require_list(advisory["role_evaluation_ids"], "advisory-roles")
    if any(role_id not in roles for role_id in role_ids):
        _reject("advisory-role-join", "advisory role reference does not resolve")

    return 17


def build_manifest(
    content: Mapping[str, Any],
    *,
    content_schema: bytes,
    generated_at: str,
    validator_id: str = "model-scan:evidence-contract",
    validator_version: str = "1.0.0",
) -> dict[str, Any]:
    checks = validate_content(content)
    _parse_utc(generated_at, "manifest-time")
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "evidence_version": content["evidence_version"],
        "generated_at": generated_at,
        "canonicalization": CANONICALIZATION,
        "content_sha256": content_sha256(content),
        "content_schema_sha256": bytes_sha256(content_schema),
        "validator": {
            "id": validator_id,
            "version": validator_version,
            "status": "pass",
            "checks": checks,
        },
    }


def validate_manifest(
    content: Mapping[str, Any], manifest: Any, *, content_schema: bytes
) -> int:
    validate_content(content)
    receipt = _require_object(manifest, "manifest")
    _required(
        receipt,
        {
            "schema_version",
            "evidence_version",
            "generated_at",
            "canonicalization",
            "content_sha256",
            "content_schema_sha256",
            "validator",
        },
        "manifest",
    )
    if receipt["schema_version"] != MANIFEST_SCHEMA_VERSION:
        _reject("manifest-version", "unsupported manifest version")
    if receipt["evidence_version"] != content["evidence_version"]:
        _reject("manifest-version-join", "manifest evidence version does not match")
    _parse_utc(receipt["generated_at"], "manifest-time")
    if receipt["canonicalization"] != CANONICALIZATION:
        _reject("canonicalization", "unsupported canonicalization profile")
    if receipt["content_sha256"] != content_sha256(content):
        _reject("content-hash", "manifest content digest does not match")
    if receipt["content_schema_sha256"] != bytes_sha256(content_schema):
        _reject("schema-hash", "manifest schema digest does not match")
    validator = _require_object(receipt["validator"], "validator-receipt")
    if validator.get("status") != "pass" or not isinstance(validator.get("checks"), int) or validator["checks"] < 1:
        _reject("validator-receipt", "external validator receipt is not passing")
    return 7


def _write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _reject("write-once", f"publication already exists: {path.name}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o600)
            stream.write(data)
            stream.write(b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def publish(
    content: Mapping[str, Any],
    *,
    content_schema_path: str | Path,
    output_directory: str | Path,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    schema_bytes = Path(content_schema_path).read_bytes()
    manifest = build_manifest(
        content,
        content_schema=schema_bytes,
        generated_at=generated_at or utc_now(),
    )
    validate_manifest(content, manifest, content_schema=schema_bytes)
    output = Path(output_directory)
    stem = content["evidence_version"].replace("/", "_")
    content_path = output / f"{stem}.content.json"
    manifest_path = output / f"{stem}.manifest.json"
    _write_once(content_path, canonical_json_bytes(content))
    _write_once(manifest_path, canonical_json_bytes(manifest))
    return content_path, manifest_path
