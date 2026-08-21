"""Neutral provider-catalog adapter migrated from Model Scraper lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

SCHEMA_VERSION = "1.0.0"
STATES = frozenset({"true", "false", "unknown"})


class SourceAdapterRejected(ValueError):
    """Raised when a source payload or publication is unsafe."""


def payload_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _price(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {"state": "unknown", "value": None}
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise SourceAdapterRejected(f"invalid price value: {value!r}")
    if not math.isfinite(parsed) or parsed < 0:
        raise SourceAdapterRejected("price must be finite and nonnegative")
    return {"state": "known", "value": parsed}


def _features(model: Mapping[str, Any], source_id: str) -> list[dict[str, str]]:
    features: list[dict[str, str]] = []
    supported = model.get("supported_parameters")
    if isinstance(supported, list):
        for parameter in sorted({str(item) for item in supported if item}):
            features.append(
                {
                    "name": parameter,
                    "state": "advertised",
                    "provenance": f"{source_id}:supported_parameters",
                }
            )
    architecture = model.get("architecture")
    if isinstance(architecture, Mapping):
        modalities = architecture.get("input_modalities") or architecture.get("modality")
        if isinstance(modalities, list):
            for modality in sorted({str(item) for item in modalities if item}):
                features.append(
                    {
                        "name": f"input:{modality}",
                        "state": "advertised",
                        "provenance": f"{source_id}:architecture.input_modalities",
                    }
                )
    return features


def build_source_observations(
    payload: Mapping[str, Any] | list[Any],
    *,
    serving_provider: str,
    source_id: str,
    retrieved_at: str,
    source_sha256: str,
) -> dict[str, Any]:
    models = payload.get("data") if isinstance(payload, Mapping) else payload
    if not isinstance(models, list):
        raise SourceAdapterRejected("catalog payload must be an array or an object with data")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in models:
        if not isinstance(raw, Mapping):
            raise SourceAdapterRejected("catalog entries must be objects")
        api_model = raw.get("id")
        if not isinstance(api_model, str) or not api_model:
            raise SourceAdapterRejected("catalog entry needs an exact API model ID")
        if api_model in seen:
            raise SourceAdapterRejected(f"duplicate API model ID: {api_model}")
        seen.add(api_model)
        upstream = api_model.split("/", 1)[0] if "/" in api_model else "unknown"
        pricing = raw.get("pricing") if isinstance(raw.get("pricing"), Mapping) else {}
        records.append(
            {
                "observation_id": f"src_{serving_provider}_{hashlib.sha256(api_model.encode()).hexdigest()[:24]}",
                "serving_provider": serving_provider,
                "upstream_organization": upstream,
                "api_model": api_model,
                "display_name": raw.get("name"),
                "states": {
                    "discoverable": "true",
                    "callable": "unknown",
                    "probed_reachable": "unknown",
                    "policy_eligible": "unknown",
                },
                "context_tokens": raw.get("context_length"),
                "pricing": {
                    "input": _price(pricing.get("prompt")),
                    "output": _price(pricing.get("completion")),
                },
                "features": _features(raw, source_id),
                "field_provenance": {
                    "api_model": f"{source_id}:id",
                    "display_name": f"{source_id}:name",
                    "context_tokens": f"{source_id}:context_length",
                    "pricing.input": f"{source_id}:pricing.prompt",
                    "pricing.output": f"{source_id}:pricing.completion",
                },
                "retrieved_at": retrieved_at,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "source_sha256": source_sha256,
        "retrieved_at": retrieved_at,
        "records": records,
    }


def validate_observations(document: Any) -> None:
    if not isinstance(document, Mapping):
        raise SourceAdapterRejected("source observations must be an object")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise SourceAdapterRejected("unsupported source-observation schema")
    source_sha = document.get("source_sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64:
        raise SourceAdapterRejected("source SHA-256 is required")
    records = document.get("records")
    if not isinstance(records, list):
        raise SourceAdapterRejected("records must be an array")
    seen: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise SourceAdapterRejected("records must be objects")
        key = (record.get("serving_provider"), record.get("api_model"))
        if not all(isinstance(item, str) and item for item in key) or key in seen:
            raise SourceAdapterRejected("callable source keys must be exact and unique")
        seen.add(key)
        states = record.get("states")
        if not isinstance(states, Mapping) or set(states.values()) - STATES:
            raise SourceAdapterRejected("source states must use true, false, or unknown")
        if states.get("discoverable") != "true":
            raise SourceAdapterRejected("list records must remain discoverable")
        if states.get("probed_reachable") == "true" and not record.get("probe_observation_id"):
            raise SourceAdapterRejected("reachable true requires separate probe evidence")
        if record.get("retrieved_at") != document.get("retrieved_at"):
            raise SourceAdapterRejected("record time cannot restamp source retrieval")
        encoded = json.dumps(record, sort_keys=True)
        if "sk-or-" in encoded or "Bearer " in encoded:
            raise SourceAdapterRejected("credential values are forbidden")


def _price_value(record: Mapping[str, Any], direction: str) -> Any:
    return record.get("pricing", {}).get(direction, {}).get("value")


def diff_source_observations(previous: Mapping[str, Any], current: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_observations(previous)
    validate_observations(current)
    old = {record["api_model"]: record for record in previous["records"]}
    new = {record["api_model"]: record for record in current["records"]}
    events: list[dict[str, Any]] = []
    for model_id in sorted(new.keys() - old.keys()):
        events.append({"event": "model-added", "api_model": model_id})
    for model_id in sorted(old.keys() - new.keys()):
        events.append({"event": "model-removed", "api_model": model_id})
    for model_id in sorted(old.keys() & new.keys()):
        for direction in ("input", "output"):
            before = _price_value(old[model_id], direction)
            after = _price_value(new[model_id], direction)
            if before != after:
                events.append(
                    {
                        "event": "price-changed",
                        "api_model": model_id,
                        "direction": direction,
                        "before": before,
                        "after": after,
                    }
                )
    return events


def last_known_good_path(path: str | Path) -> Path:
    target = Path(path)
    return target.with_name(f"{target.stem}.last-known-good{target.suffix}")


def _atomic_write(document: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o600)
            json.dump(document, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def publish_observations(document: Mapping[str, Any], path: str | Path) -> Path:
    validate_observations(document)
    target = Path(path)
    _atomic_write(document, last_known_good_path(target))
    _atomic_write(document, target)
    return target


def refresh_with_retry(
    fetch: Callable[[], bytes],
    *,
    parse: Callable[[bytes], Mapping[str, Any] | list[Any]],
    attempts: int = 3,
) -> tuple[Mapping[str, Any] | list[Any] | None, list[str]]:
    if attempts < 1 or attempts > 5:
        raise SourceAdapterRejected("attempt count must be between 1 and 5")
    failures: list[str] = []
    for _ in range(attempts):
        try:
            payload = fetch()
            return parse(payload), failures
        except Exception as error:  # bounded adapter boundary records failures
            failures.append(type(error).__name__)
    return None, failures


def quarantine_receipt(
    payload: bytes, *, source_id: str, reason: str, observed_at: str
) -> dict[str, Any]:
    """Record invalid input without copying raw payload or possible secrets."""

    if not source_id or not reason:
        raise SourceAdapterRejected("quarantine needs source identity and reason")
    return {
        "schema_version": "1.0.0",
        "source_id": source_id,
        "observed_at": observed_at,
        "payload_sha256": payload_sha256(payload),
        "payload_bytes": len(payload),
        "reason": reason,
        "raw_payload_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize an offline provider catalog for Model Scan")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--retrieved-at", required=True)
    args = parser.parse_args()
    raw = Path(args.input).read_bytes()
    payload = json.loads(raw)
    document = build_source_observations(
        payload,
        serving_provider=args.provider,
        source_id=args.source_id,
        retrieved_at=args.retrieved_at,
        source_sha256=payload_sha256(raw),
    )
    publish_observations(document, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
