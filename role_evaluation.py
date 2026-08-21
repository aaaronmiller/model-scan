"""Typed, advisory-only role evaluation and privacy-safe task telemetry."""

from __future__ import annotations

import hashlib
import hmac
import math
import statistics
from typing import Any, Mapping

ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "coding-execution": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"tools", "structured-output"},
        "required_harness_tools": {"read", "write", "shell"},
        "required_artifact": "repository patch plus test receipt",
        "failure_classes": {"invalid-patch", "test-failure", "tool-error"},
        "minimum_trials": 12,
        "minimum_success_lower_bound": 0.65,
    },
    "architecture-planning": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"structured-output"},
        "required_harness_tools": {"read"},
        "required_artifact": "decision trace with constraints and gates",
        "failure_classes": {"missing-constraint", "invented-scope", "unverifiable-plan"},
        "minimum_trials": 10,
        "minimum_success_lower_bound": 0.60,
    },
    "adversarial-review": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"structured-output"},
        "required_harness_tools": {"read"},
        "required_artifact": "ranked findings with evidence",
        "failure_classes": {"false-positive", "missed-defect", "unsupported-finding"},
        "minimum_trials": 12,
        "minimum_success_lower_bound": 0.65,
    },
    "research-synthesis": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"structured-output"},
        "required_harness_tools": {"web"},
        "required_artifact": "source-bound synthesis",
        "failure_classes": {"citation-mismatch", "stale-source", "unsupported-claim"},
        "minimum_trials": 10,
        "minimum_success_lower_bound": 0.60,
    },
    "web-extraction": {
        "family": "browser-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"tools"},
        "required_harness_tools": {"browser"},
        "required_artifact": "structured extraction plus source URL",
        "failure_classes": {"selector-failure", "partial-extraction", "wrong-page"},
        "minimum_trials": 12,
        "minimum_success_lower_bound": 0.65,
    },
    "vision-browser-qa": {
        "family": "browser-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"vision", "tools"},
        "required_harness_tools": {"browser", "screenshot"},
        "required_artifact": "visual finding with screenshot evidence",
        "failure_classes": {"visual-miss", "false-positive", "interaction-failure"},
        "minimum_trials": 12,
        "minimum_success_lower_bound": 0.65,
    },
    "retrieval": {
        "family": "retrieval-endpoint",
        "endpoint_class": "retrieval",
        "required_model_capabilities": set(),
        "required_harness_tools": set(),
        "required_artifact": "ranked document identifiers",
        "failure_classes": {"low-recall", "wrong-corpus", "timeout"},
        "minimum_trials": 30,
        "minimum_success_lower_bound": 0.70,
    },
    "reranking": {
        "family": "rerank-endpoint",
        "endpoint_class": "rerank",
        "required_model_capabilities": set(),
        "required_harness_tools": set(),
        "required_artifact": "reordered candidate identifiers",
        "failure_classes": {"ranking-regression", "invalid-score", "timeout"},
        "minimum_trials": 30,
        "minimum_success_lower_bound": 0.70,
    },
    "embeddings": {
        "family": "embedding-endpoint",
        "endpoint_class": "embedding",
        "required_model_capabilities": set(),
        "required_harness_tools": set(),
        "required_artifact": "finite vector with declared dimensions",
        "failure_classes": {"dimension-mismatch", "nonfinite-vector", "timeout"},
        "minimum_trials": 30,
        "minimum_success_lower_bound": 0.70,
    },
    "compression": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"structured-output"},
        "required_harness_tools": set(),
        "required_artifact": "compressed context preserving required facts",
        "failure_classes": {"fact-loss", "instruction-loss", "size-miss"},
        "minimum_trials": 12,
        "minimum_success_lower_bound": 0.65,
    },
    "approval": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"structured-output"},
        "required_harness_tools": {"read"},
        "required_artifact": "approve, reject, or abstain with evidence",
        "failure_classes": {"unsafe-approval", "unsupported-rejection", "missing-abstention"},
        "minimum_trials": 16,
        "minimum_success_lower_bound": 0.75,
    },
    "orchestration": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": {"tools", "structured-output"},
        "required_harness_tools": {"delegation"},
        "required_artifact": "bounded delegation plan and merged evidence",
        "failure_classes": {"authority-leak", "duplicate-work", "missing-leaf-evidence"},
        "minimum_trials": 16,
        "minimum_success_lower_bound": 0.70,
    },
    "low-latency-utility": {
        "family": "generative-agent",
        "endpoint_class": "chat",
        "required_model_capabilities": set(),
        "required_harness_tools": set(),
        "required_artifact": "short valid result",
        "failure_classes": {"timeout", "invalid-format", "wrong-answer"},
        "minimum_trials": 20,
        "minimum_success_lower_bound": 0.70,
    },
}


class RoleEvaluationRejected(ValueError):
    """Raised for malformed telemetry or evaluation inputs."""


def validate_role_definitions() -> None:
    if len(ROLE_DEFINITIONS) != len(set(ROLE_DEFINITIONS)):
        raise RoleEvaluationRejected("role identifiers must be unique")
    endpoint_families = {
        "retrieval": ("retrieval-endpoint", "retrieval"),
        "reranking": ("rerank-endpoint", "rerank"),
        "embeddings": ("embedding-endpoint", "embedding"),
    }
    for role, (expected_family, expected_endpoint) in endpoint_families.items():
        definition = ROLE_DEFINITIONS[role]
        if definition["family"] != expected_family or definition["endpoint_class"] != expected_endpoint:
            raise RoleEvaluationRejected(f"endpoint role is not typed independently: {role}")


def pseudonymous_id(prefix: str, raw_value: str, *, project_salt: str) -> str:
    if not raw_value or not project_salt:
        raise RoleEvaluationRejected("pseudonymous IDs require a value and project salt")
    digest = hmac.new(project_salt.encode(), raw_value.encode(), hashlib.sha256).hexdigest()
    return f"{prefix}_{digest[:32]}"


def metric(value: int | float | None, *, reason: str | None = None) -> dict[str, Any]:
    if value is None:
        if reason not in {"unsupported", "redacted", "collection_failed", "not_applicable"}:
            raise RoleEvaluationRejected("missing metric needs a bounded reason")
        return {"availability": "unavailable", "value": None, "reason": reason}
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
        raise RoleEvaluationRejected("metric values must be finite and nonnegative")
    return {"availability": "available", "value": value, "reason": None}


def build_runtime_observation(
    *,
    raw_task_id: str,
    raw_attempt_id: str,
    project_salt: str,
    identity_id: str,
    role: str,
    fixture_id: str,
    started_at: str,
    ended_at: str,
    input_tokens: int | None,
    cached_input_tokens: int | None,
    output_tokens: int | None,
    missing_reasons: Mapping[str, str] | None = None,
    accepted_first_pass: bool,
    accepted_eventually: bool,
    correction_count: int,
    retention_days: int = 30,
) -> dict[str, Any]:
    if role not in ROLE_DEFINITIONS:
        raise RoleEvaluationRejected(f"unknown role: {role}")
    if not 0 <= retention_days <= 365:
        raise RoleEvaluationRejected("retention_days must be between 0 and 365")
    if correction_count < 0:
        raise RoleEvaluationRejected("correction_count must be nonnegative")
    reasons = dict(missing_reasons or {})
    values = {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
    }
    metrics = {
        name: metric(value, reason=reasons.get(name) if value is None else None)
        for name, value in values.items()
    }
    task_id = pseudonymous_id("tsk", raw_task_id, project_salt=project_salt)
    attempt_id = pseudonymous_id("att", raw_attempt_id, project_salt=project_salt)
    return {
        "runtime_observation_id": f"run_{attempt_id[4:]}",
        "task_id": task_id,
        "attempt_id": attempt_id,
        "role": role,
        "fixture_id": fixture_id,
        "identity_id": identity_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "metrics": metrics,
        "outcome": {
            "accepted_first_pass": accepted_first_pass,
            "accepted_eventually": accepted_eventually,
            "correction_count": correction_count,
        },
        "privacy": {
            "raw_prompt_stored": False,
            "raw_output_stored": False,
            "retention_days": retention_days,
        },
    }


def wilson_interval(successes: int, trials: int, *, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise RoleEvaluationRejected("success counts are invalid")
    rate = successes / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt((rate * (1 - rate) + z * z / (4 * trials)) / trials) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _gate(name: str, passed: bool, observed: Any, required: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "observed": observed, "required": required}


def _evaluate_candidate(candidate: Mapping[str, Any], definition: Mapping[str, Any]) -> dict[str, Any]:
    identity_id = candidate.get("identity_id")
    if not isinstance(identity_id, str) or not identity_id:
        raise RoleEvaluationRejected("candidate identity_id is required")
    model_capabilities = set(candidate.get("model_capabilities", []))
    harness_tools = set(candidate.get("harness_tools", []))
    required_capabilities = set(definition["required_model_capabilities"])
    required_tools = set(definition["required_harness_tools"])
    successes = candidate.get("successes")
    trials = candidate.get("trials")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise RoleEvaluationRejected("candidate successes and trials must be integers")
    lower, upper = wilson_interval(successes, trials)
    gates = [
        _gate("provider-available", candidate.get("provider_available") is True, candidate.get("provider_available"), True),
        _gate("privacy-eligible", candidate.get("privacy_eligible") is True, candidate.get("privacy_eligible"), True),
        _gate("endpoint-class", candidate.get("endpoint_class") == definition["endpoint_class"], candidate.get("endpoint_class"), definition["endpoint_class"]),
        _gate("model-capabilities", required_capabilities <= model_capabilities, sorted(model_capabilities), sorted(required_capabilities)),
        _gate("harness-tools", required_tools <= harness_tools, sorted(harness_tools), sorted(required_tools)),
        _gate("minimum-sample", trials >= definition["minimum_trials"], trials, definition["minimum_trials"]),
        _gate("success-lower-bound", lower >= definition["minimum_success_lower_bound"], round(lower, 6), definition["minimum_success_lower_bound"]),
    ]
    eligible = all(gate["passed"] for gate in gates)
    tool_successes = candidate.get("tool_successes", successes)
    tool_trials = candidate.get("tool_trials", trials)
    if not isinstance(tool_successes, int) or not isinstance(tool_trials, int) or not 0 <= tool_successes <= tool_trials:
        raise RoleEvaluationRejected("tool validity counts are invalid")
    success_rate = successes / trials
    tool_rate = tool_successes / tool_trials if tool_trials else 0.0
    score = round(0.75 * success_rate + 0.25 * tool_rate, 8) if eligible else None
    width = upper - lower
    confidence = "insufficient"
    if eligible:
        confidence = "high" if trials >= 2 * definition["minimum_trials"] and width <= 0.2 else "medium"
    prices = candidate.get("monetary_price", {})
    if not isinstance(prices, Mapping) or prices.get("state") not in {"known", "unknown"}:
        raise RoleEvaluationRejected("monetary_price needs known or unknown state")
    if prices["state"] == "known":
        price_value = prices.get("value")
        if isinstance(price_value, bool) or not isinstance(price_value, (int, float)) or price_value < 0:
            raise RoleEvaluationRejected("known monetary price must be nonnegative")
    elif prices.get("value") is not None:
        raise RoleEvaluationRejected("unknown monetary price must have a null value")
    return {
        "identity_id": identity_id,
        "gates": gates,
        "score": score,
        "confidence": confidence,
        "sample_count": trials,
        "success_interval_95": [round(lower, 8), round(upper, 8)],
        "median_latency_ms": statistics.median(candidate.get("latency_ms", [])) if candidate.get("latency_ms") else None,
        "monetary_price": dict(prices),
    }


def evaluate_role(
    role: str,
    candidates: list[Mapping[str, Any]],
    *,
    evidence_version: str,
    evidence_sha256: str,
    fixture_set_id: str,
) -> dict[str, Any]:
    validate_role_definitions()
    if role not in ROLE_DEFINITIONS:
        raise RoleEvaluationRejected(f"unknown role: {role}")
    if not candidates:
        raise RoleEvaluationRejected("at least one candidate is required")
    if len(evidence_sha256) != 64 or any(character not in "0123456789abcdef" for character in evidence_sha256):
        raise RoleEvaluationRejected("evidence_sha256 must be a lowercase SHA-256 digest")
    evaluated = [_evaluate_candidate(candidate, ROLE_DEFINITIONS[role]) for candidate in candidates]
    eligible = [candidate for candidate in evaluated if candidate["score"] is not None]
    if not eligible:
        decision = "abstain"
        recommended = None
        reason = "No candidate passed every role, evidence, privacy, and sample gate."
    else:
        eligible.sort(key=lambda candidate: (-candidate["score"], candidate["identity_id"]))
        decision = "recommend"
        recommended = eligible[0]["identity_id"]
        reason = "Highest evidence score among candidates that passed every minimum gate."
    return {
        "role_evaluation_id": f"role_{role}_{fixture_set_id}",
        "role_id": role,
        "fixture_set_id": fixture_set_id,
        "evidence_version": evidence_version,
        "evidence_sha256": evidence_sha256,
        "candidates": evaluated,
        "decision": decision,
        "recommended_identity_id": recommended,
        "reason": reason,
        "non_authority": True,
    }


def compare_paired_outcomes(
    pairs: list[Mapping[str, Any]], *, minimum_pairs: int = 12
) -> dict[str, Any]:
    """Compare two candidates only when exact task/fixture pairs are available."""

    if minimum_pairs < 2:
        raise RoleEvaluationRejected("minimum_pairs must be at least two")
    if len(pairs) < minimum_pairs:
        return {
            "status": "blocked",
            "reason": f"Need at least {minimum_pairs} paired attempts; found {len(pairs)}.",
            "pair_count": len(pairs),
        }
    differences: list[int] = []
    seen: set[tuple[str, str]] = set()
    for pair in pairs:
        required = {"task_id", "fixture_id", "left_success", "right_success"}
        if not required <= set(pair):
            raise RoleEvaluationRejected("paired outcomes are missing required fields")
        key = (str(pair["task_id"]), str(pair["fixture_id"]))
        if key in seen:
            raise RoleEvaluationRejected("paired outcomes contain duplicate task fixtures")
        seen.add(key)
        if not isinstance(pair["left_success"], bool) or not isinstance(pair["right_success"], bool):
            raise RoleEvaluationRejected("paired success values must be booleans")
        differences.append(int(pair["left_success"]) - int(pair["right_success"]))
    mean = statistics.mean(differences)
    if len(differences) > 1:
        standard_error = statistics.stdev(differences) / math.sqrt(len(differences))
    else:
        standard_error = 0.0
    margin = 1.96 * standard_error
    interval = [max(-1.0, mean - margin), min(1.0, mean + margin)]
    left_only = sum(1 for value in differences if value == 1)
    right_only = sum(1 for value in differences if value == -1)
    discordant = left_only + right_only
    if discordant:
        smaller = min(left_only, right_only)
        tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2**discordant)
        p_value = min(1.0, 2 * tail)
    else:
        p_value = 1.0
    return {
        "status": "complete",
        "pair_count": len(pairs),
        "left_minus_right_success": round(mean, 8),
        "confidence_interval_95": [round(value, 8) for value in interval],
        "discordant_pairs": {"left_only": left_only, "right_only": right_only},
        "mcnemar_exact_p": round(p_value, 8),
        "causal_claim": False,
    }
