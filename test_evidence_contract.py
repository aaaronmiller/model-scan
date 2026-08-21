"""Contract tests for immutable Model Scan evidence publications."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from evidence_contract import (
    EvidenceContractRejected,
    build_manifest,
    canonical_json_bytes,
    publish,
    validate_content,
    validate_manifest,
)

ROOT = Path(__file__).parent
CONTENT_SCHEMA = ROOT / "contracts" / "evidence_content.schema.json"
MANIFEST_SCHEMA = ROOT / "contracts" / "evidence_manifest.schema.json"


def _metric(value, reason=None):
    if value is None:
        return {"availability": "unavailable", "value": None, "reason": reason}
    return {"availability": "available", "value": value, "reason": None}


def _content():
    return {
        "schema_version": "1.0.0",
        "evidence_version": "2026.08.15-test.1",
        "generated_at": "2026-08-15T14:00:00Z",
        "authority": {
            "research_owner": "ardf",
            "evidence_owner": "model-scan",
            "routing_owner": "gateway",
            "decision_owner": "living-documents",
            "non_authority": True,
        },
        "source_snapshots": [
            {
                "source_snapshot_id": "src_official_openrouter",
                "source_id": "openrouter-model-catalog",
                "tier": "official_primary",
                "verification": "verified",
                "retrieved_at": "2026-08-15T12:00:00Z",
                "sha256": "1" * 64,
                "privacy": "public",
                "freshness": {
                    "evaluated_at": "2026-08-15T13:00:00Z",
                    "state": "current",
                    "valid_until": "2026-08-16T12:00:00Z",
                },
            }
        ],
        "model_identities": [
            {
                "identity_id": "mdl_openrouter_qwen",
                "provider": "openrouter",
                "api_model": "qwen/qwen3-coder:free",
                "harness": "omp",
                "endpoint_class": "chat",
                "effort": "default",
                "lifecycle": "current",
                "source_snapshot_ids": ["src_official_openrouter"],
            }
        ],
        "published_observations": [
            {
                "observation_id": "obs_qwen_input_price",
                "identity_id": "mdl_openrouter_qwen",
                "source_snapshot_id": "src_official_openrouter",
                "dimension": "monetary_token_price",
                "metric": "input_per_million",
                "value_state": "known",
                "value": 0,
                "unit": "USD_per_1M_tokens",
                "observed_at": "2026-08-15T11:59:00Z",
                "confidence": "high",
                "missing_reason": None,
            }
        ],
        "runtime_observations": [
            {
                "runtime_observation_id": "run_attempt_000001",
                "task_id": "tsk_0123456789abcdef",
                "attempt_id": "att_0123456789abcdef",
                "role": "coding-execution",
                "fixture_id": "fixture-coding-v1",
                "identity_id": "mdl_openrouter_qwen",
                "started_at": "2026-08-15T12:10:00Z",
                "ended_at": "2026-08-15T12:11:00Z",
                "metrics": {
                    "input_tokens": _metric(100),
                    "cached_input_tokens": _metric(0),
                    "output_tokens": _metric(50),
                    "time_to_first_token_ms": _metric(None, "unsupported"),
                },
                "outcome": {
                    "accepted_first_pass": True,
                    "accepted_eventually": True,
                    "correction_count": 0,
                },
                "privacy": {
                    "raw_prompt_stored": False,
                    "raw_output_stored": False,
                    "retention_days": 30,
                },
            }
        ],
        "calibration_results": [
            {
                "calibration_id": "cal_zero_price_stratum",
                "axis": "cost",
                "observation_ids": ["obs_qwen_input_price"],
                "algorithm_id": "categorical-zero-v1",
                "config_sha256": "2" * 64,
                "zero_policy": "categorical_zero",
                "output": 0,
                "abstention_reason": None,
                "generated_at": "2026-08-15T13:30:00Z",
            }
        ],
        "role_evaluations": [
            {
                "role_evaluation_id": "role_coding_fixture_v1",
                "role_id": "coding-execution",
                "fixture_set_id": "fixture-coding-v1",
                "evidence_version": "2026.08.15-test.1",
                "candidates": [
                    {
                        "identity_id": "mdl_openrouter_qwen",
                        "gates": [
                            {"name": "identity", "passed": True},
                            {"name": "sample", "passed": True},
                        ],
                        "score": 0.9,
                        "confidence": "medium",
                        "sample_count": 20,
                    }
                ],
                "decision": "recommend",
                "recommended_identity_id": "mdl_openrouter_qwen",
                "reason": "Passed the fixed fixture gates.",
            }
        ],
        "advisory_snapshot": {
            "evidence_version": "2026.08.15-test.1",
            "non_authority": True,
            "role_evaluation_ids": ["role_coding_fixture_v1"],
            "recommendations": [
                {"role_id": "coding-execution", "identity_id": "mdl_openrouter_qwen"}
            ],
        },
    }


def _abstain(content, reason):
    evaluation = content["role_evaluations"][0]
    evaluation["decision"] = "abstain"
    evaluation["recommended_identity_id"] = None
    evaluation["reason"] = reason
    content["advisory_snapshot"]["recommendations"] = []


def _fixture_variant(name):
    content = _content()
    if name == "paid":
        content["published_observations"][0]["value"] = 1.25
        content["calibration_results"][0]["zero_policy"] = "positive_log"
        content["calibration_results"][0]["output"] = 1.25
    elif name == "unknown-price":
        observation = content["published_observations"][0]
        observation.update(
            {"value_state": "unknown", "value": None, "missing_reason": "collection_failed"}
        )
        calibration = content["calibration_results"][0]
        calibration.update(
            {"zero_policy": "positive_log", "output": None, "abstention_reason": "missing-price"}
        )
        _abstain(content, "Cost-sensitive ranking cannot use an unknown price.")
    elif name == "unscored":
        content["calibration_results"][0].update(
            {"output": None, "abstention_reason": "insufficient-calibration-overlap"}
        )
        _abstain(content, "No calibrated role score is available.")
    elif name == "deprecated":
        content["model_identities"][0]["lifecycle"] = "deprecated"
        _abstain(content, "Deprecated identities remain visible but cannot be recommended.")
    elif name == "multi-provider":
        source = copy.deepcopy(content["source_snapshots"][0])
        source.update(
            {
                "source_snapshot_id": "src_official_direct",
                "source_id": "qwen-direct-model-catalog",
                "sha256": "3" * 64,
            }
        )
        identity = copy.deepcopy(content["model_identities"][0])
        identity.update(
            {
                "identity_id": "mdl_qwen_direct",
                "provider": "qwen-direct",
                "source_snapshot_ids": ["src_official_direct"],
            }
        )
        content["source_snapshots"].append(source)
        content["model_identities"].append(identity)
    elif name == "multi-effort":
        identity = copy.deepcopy(content["model_identities"][0])
        identity.update({"identity_id": "mdl_openrouter_qwen_high", "effort": "high"})
        content["model_identities"].append(identity)
    else:
        raise AssertionError(name)
    return content


def test_content_and_external_manifest_validate_with_real_hashes():
    content = _content()
    schema_bytes = CONTENT_SCHEMA.read_bytes()
    assert validate_content(content) == 17
    manifest = build_manifest(
        content,
        content_schema=schema_bytes,
        generated_at="2026-08-15T14:01:00Z",
    )
    assert validate_manifest(content, manifest, content_schema=schema_bytes) == 7
    assert manifest["content_sha256"] not in {"0" * 64, "1" * 64, "2" * 64}
    assert "content_sha256" not in content

    content_schema = json.loads(schema_bytes)
    manifest_schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(content_schema, format_checker=FormatChecker()).iter_errors(content)) == []
    assert list(Draft202012Validator(manifest_schema, format_checker=FormatChecker()).iter_errors(manifest)) == []


@pytest.mark.parametrize(
    "variant",
    ["paid", "exact-zero", "unknown-price", "unscored", "deprecated", "multi-provider", "multi-effort"],
)
def test_complete_publication_fixture_matrix(variant):
    content = _content() if variant == "exact-zero" else _fixture_variant(variant)
    assert validate_content(content) == 17


def test_canonicalization_is_deterministic_and_rejects_nonfinite_values():
    first = {"b": [2, 1], "a": "é"}
    second = {"a": "é", "b": [2, 1]}
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    with pytest.raises(EvidenceContractRejected, match="canonical-json"):
        canonical_json_bytes({"bad": float("nan")})


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda value: value.__setitem__("content_sha256", "0" * 64), "circular-receipt"),
        (lambda value: value["model_identities"].append(copy.deepcopy(value["model_identities"][0])), "model-identity"),
        (lambda value: value["published_observations"][0].__setitem__("identity_id", "mdl_missing"), "observation-identity-join"),
        (lambda value: value["runtime_observations"][0]["metrics"]["output_tokens"].update({"value": None, "reason": None, "availability": "unavailable"}), "runtime-metric"),
        (lambda value: value["calibration_results"][0].__setitem__("zero_policy", "positive_log"), "zero-price-geometry"),
        (lambda value: value["role_evaluations"][0]["candidates"][0]["gates"][0].__setitem__("passed", False), "role-gates"),
        (lambda value: value["source_snapshots"][0]["freshness"].__setitem__("state", "stale"), "role-freshness"),
        (lambda value: value["model_identities"][0].__setitem__("lifecycle", "deprecated"), "role-lifecycle"),
    ],
)
def test_named_negative_contract_gates(mutate, code):
    content = _content()
    mutate(content)
    with pytest.raises(EvidenceContractRejected) as error:
        validate_content(content)
    assert error.value.code == code


def test_manifest_rejects_content_or_schema_mismatch():
    content = _content()
    schema = CONTENT_SCHEMA.read_bytes()
    manifest = build_manifest(content, content_schema=schema, generated_at="2026-08-15T14:01:00Z")
    changed = copy.deepcopy(content)
    changed["advisory_snapshot"]["recommendations"] = []
    with pytest.raises(EvidenceContractRejected, match="content-hash"):
        validate_manifest(changed, manifest, content_schema=schema)
    with pytest.raises(EvidenceContractRejected, match="schema-hash"):
        validate_manifest(content, manifest, content_schema=schema + b" ")


def test_publication_is_private_and_write_once(tmp_path):
    content_path, manifest_path = publish(
        _content(),
        content_schema_path=CONTENT_SCHEMA,
        output_directory=tmp_path,
        generated_at="2026-08-15T14:01:00Z",
    )
    assert content_path.stat().st_mode & 0o077 == 0
    assert manifest_path.stat().st_mode & 0o077 == 0
    with pytest.raises(EvidenceContractRejected, match="write-once"):
        publish(
            _content(),
            content_schema_path=CONTENT_SCHEMA,
            output_directory=tmp_path,
            generated_at="2026-08-15T14:01:00Z",
        )
