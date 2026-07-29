"""Model Scan publishes capability facts without callable identity inference."""

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from capability_evidence import (
    CapabilityEvidenceRejected,
    build_evidence,
    last_known_good_path,
    publish,
    validate,
)

ROOT = Path(__file__).parent
SCHEMA_PATH = ROOT / "contracts" / "capability_evidence.schema.json"


@dataclass
class Dossier:
    provider: str = "OpenRouter"
    model: str = "qwen/qwen3-coder:free"
    accessible: bool = True
    reliability: float = 0.98
    slot_fitness: dict = field(
        default_factory=lambda: {"coding": 91.2, "agentic": 88.0}
    )
    has_tools: bool = True
    has_vision: bool = False
    context_length: int = 131072
    price_blended: float = 0.0
    lat_s: float = 0.45
    confidence: float = 0.92


def _document(dossiers=None):
    return build_evidence(
        dossiers or [Dossier()],
        generated_at="2026-07-23T14:00:00Z",
        source="model-scan:test",
        evidence_ref="scan:fixture",
    )


def test_output_validates_against_shared_contract():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert list(validator.iter_errors(_document())) == []


def test_capability_identity_is_not_a_callable_identity():
    record = _document()["records"][0]
    assert record["model_identity"] == "qwen/qwen3-coder:free"
    assert record["capability_id"] == ("model-scan:openrouter:qwen/qwen3-coder:free")
    assert not (
        {"provider_id", "api_model_id", "base_url", "credential_ref", "callable_id"}
        & set(record)
    )


def test_dimensions_features_health_cost_and_latency_are_preserved():
    record = _document()["records"][0]
    assert record["dimensions"] == {
        "slot:agentic": 88.0,
        "slot:coding": 91.2,
    }
    assert record["features"] == ["tools", "context:131072"]
    assert record["health"] == "healthy"
    assert record["cost"]["blended_per_million"] == 0.0
    assert record["latency_ms"] == 450.0
    assert record["confidence"] == 0.92


def test_unknown_facts_stay_unknown_instead_of_being_inferred():
    dossier = {
        "provider": "Unmapped",
        "model": "Display Name Only",
        "accessible": None,
        "slot_fitness": {},
    }
    record = _document([dossier])["records"][0]
    assert record["health"] == "unknown"
    assert record["cost"] == {
        "input_per_million": None,
        "output_per_million": None,
        "blended_per_million": None,
    }
    assert record["latency_ms"] is None
    assert record["confidence"] == 0.0


def test_duplicate_or_missing_identity_is_rejected():
    with pytest.raises(CapabilityEvidenceRejected, match="unique"):
        _document([Dossier(), Dossier()])
    with pytest.raises(CapabilityEvidenceRejected, match="identity"):
        _document([{"provider": "x"}])


def test_callable_field_is_rejected():
    document = _document()
    document["records"][0]["api_model_id"] = "inferred/model"
    with pytest.raises(CapabilityEvidenceRejected, match="fields"):
        validate(document)


def test_publish_writes_current_and_last_known_good(tmp_path):
    target = tmp_path / "capability_evidence.json"
    document = _document()
    publish(document, target)
    assert json.loads(target.read_text(encoding="utf-8")) == document
    assert (
        json.loads(last_known_good_path(target).read_text(encoding="utf-8")) == document
    )
    assert target.stat().st_mode & 0o077 == 0


def test_invalid_refresh_does_not_replace_known_good(tmp_path):
    target = tmp_path / "capability_evidence.json"
    document = _document()
    publish(document, target)
    before = target.read_bytes()

    broken = copy.deepcopy(document)
    broken["records"][0]["confidence"] = 2.0
    with pytest.raises(CapabilityEvidenceRejected, match="confidence"):
        publish(broken, target)
    assert target.read_bytes() == before
    assert last_known_good_path(target).read_bytes() == before
