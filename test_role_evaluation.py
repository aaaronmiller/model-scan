"""MS-005 role, telemetry, confidence, and abstention tests."""

import pytest

from role_evaluation import (
    ROLE_DEFINITIONS,
    RoleEvaluationRejected,
    build_runtime_observation,
    compare_paired_outcomes,
    evaluate_role,
    validate_role_definitions,
    wilson_interval,
)


def _coding_candidate(**changes):
    candidate = {
        "identity_id": "mdl_openrouter_qwen",
        "provider_available": True,
        "privacy_eligible": True,
        "endpoint_class": "chat",
        "model_capabilities": ["tools", "structured-output"],
        "harness_tools": ["read", "write", "shell"],
        "successes": 39,
        "trials": 40,
        "tool_successes": 38,
        "tool_trials": 40,
        "latency_ms": [400, 450, 500],
        "monetary_price": {"state": "known", "value": 0},
    }
    candidate.update(changes)
    return candidate


def test_role_families_are_typed_and_endpoint_roles_do_not_overlap():
    validate_role_definitions()
    assert ROLE_DEFINITIONS["retrieval"]["endpoint_class"] == "retrieval"
    assert ROLE_DEFINITIONS["reranking"]["endpoint_class"] == "rerank"
    assert ROLE_DEFINITIONS["embeddings"]["endpoint_class"] == "embedding"
    assert len(ROLE_DEFINITIONS) == 13


def test_role_recommendation_uses_gates_and_confidence_without_routing():
    result = evaluate_role(
        "coding-execution",
        [_coding_candidate()],
        evidence_version="2026.08.15-test.1",
        evidence_sha256="a" * 64,
        fixture_set_id="coding-v1",
    )
    assert result["decision"] == "recommend"
    assert result["recommended_identity_id"] == "mdl_openrouter_qwen"
    assert result["non_authority"] is True
    assert all(gate["passed"] for gate in result["candidates"][0]["gates"])
    assert result["candidates"][0]["monetary_price"] == {"state": "known", "value": 0}
    assert not ({"route", "apply", "fallback_chain"} & set(result))


def test_failed_hard_gate_or_insufficient_sample_abstains():
    result = evaluate_role(
        "coding-execution",
        [_coding_candidate(privacy_eligible=False, successes=10, trials=10, tool_successes=10, tool_trials=10)],
        evidence_version="2026.08.15-test.1",
        evidence_sha256="a" * 64,
        fixture_set_id="coding-v1",
    )
    assert result["decision"] == "abstain"
    assert result["recommended_identity_id"] is None
    assert result["candidates"][0]["score"] is None
    assert result["candidates"][0]["confidence"] == "insufficient"


def test_wilson_interval_is_bounded_and_rejects_invalid_counts():
    lower, upper = wilson_interval(39, 40)
    assert 0 < lower < upper <= 1
    with pytest.raises(RoleEvaluationRejected):
        wilson_interval(2, 1)


def test_per_call_telemetry_separates_token_counters_and_excludes_raw_text():
    observation = build_runtime_observation(
        raw_task_id="private-task-name",
        raw_attempt_id="attempt-one",
        project_salt="project-only-salt",
        identity_id="mdl_openrouter_qwen",
        role="coding-execution",
        fixture_id="coding-v1",
        started_at="2026-08-15T12:00:00Z",
        ended_at="2026-08-15T12:01:00Z",
        input_tokens=100,
        cached_input_tokens=None,
        output_tokens=50,
        missing_reasons={"cached_input_tokens": "unsupported"},
        accepted_first_pass=False,
        accepted_eventually=True,
        correction_count=1,
    )
    assert set(observation["metrics"]) == {"input_tokens", "cached_input_tokens", "output_tokens"}
    assert observation["metrics"]["cached_input_tokens"]["reason"] == "unsupported"
    assert "private-task-name" not in str(observation)
    assert observation["privacy"]["raw_prompt_stored"] is False
    assert observation["outcome"]["accepted_first_pass"] is False
    assert observation["outcome"]["accepted_eventually"] is True


def test_missing_metric_without_reason_is_rejected():
    with pytest.raises(RoleEvaluationRejected, match="bounded reason"):
        build_runtime_observation(
            raw_task_id="task",
            raw_attempt_id="attempt",
            project_salt="salt",
            identity_id="mdl",
            role="coding-execution",
            fixture_id="coding-v1",
            started_at="2026-08-15T12:00:00Z",
            ended_at="2026-08-15T12:01:00Z",
            input_tokens=None,
            cached_input_tokens=0,
            output_tokens=10,
            accepted_first_pass=True,
            accepted_eventually=True,
            correction_count=0,
        )


def test_paired_comparison_completes_or_blocks_without_inventing_causality():
    blocked = compare_paired_outcomes([], minimum_pairs=12)
    assert blocked["status"] == "blocked"
    pairs = [
        {
            "task_id": f"tsk_{index}",
            "fixture_id": "coding-v1",
            "left_success": index != 0,
            "right_success": index not in {0, 1, 2},
        }
        for index in range(12)
    ]
    result = compare_paired_outcomes(pairs, minimum_pairs=12)
    assert result["status"] == "complete"
    assert result["pair_count"] == 12
    assert len(result["confidence_interval_95"]) == 2
    assert result["causal_claim"] is False
