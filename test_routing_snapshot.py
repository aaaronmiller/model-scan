from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator

from routing_snapshot import (
    build_snapshot_from_dossiers,
    load_provider_quota,
    provider_health_from_dossiers,
    write_snapshot,
)


@dataclass
class Dossier:
    provider: str
    model: str
    api_model: str
    accessible: bool = True
    has_tools: bool = True
    has_vision_capability: bool = False
    price_blended: float | None = 0.0
    tier: str = "A"
    slot_fitness: dict[str, float] = field(default_factory=dict)


def _schema() -> dict:
    return json.loads((Path(__file__).parent / "contracts" / "routing_snapshot.schema.json").read_text())


def test_build_snapshot_validates_against_shared_contract():
    snapshot = build_snapshot_from_dossiers(
        [
            Dossier(
                provider="openrouter",
                model="deepseek/deepseek-v4-flash:free",
                api_model="openrouter/deepseek/deepseek-v4-flash:free",
                slot_fitness={"R1_primary": 81.2},
            ),
            Dossier(
                provider="anthropic",
                model="claude-opus-4-8",
                api_model="anthropic/claude-opus-4-8",
                price_blended=18.0,
                tier="S",
                slot_fitness={"R1_primary": 96.4},
            ),
            Dossier(
                provider="groq",
                model="gpt-oss-120b",
                api_model="groq/gpt-oss-120b",
                slot_fitness={"R1_primary": 75.0},
            ),
        ],
        {"R1_primary": {"label": "Interactive primary", "eval_mode": "cost_basis"}},
        scan_id=1487,
        blocklist=["groq/gpt-oss-120b"],
        generated_at="2026-06-02T12:00:00Z",
    )

    Draft202012Validator(_schema()).validate(snapshot)
    slot = snapshot["slots"]["R1_primary"]
    assert slot["best"]["api_model"] == "anthropic/claude-opus-4-8"
    assert [c["api_model"] for c in slot["candidates"]] == [
        "anthropic/claude-opus-4-8",
        "openrouter/deepseek/deepseek-v4-flash:free",
    ]
    assert snapshot["provider_health"]["openrouter"] == "ok"


def test_provider_quota_file_normalizes_snapshot_state(tmp_path):
    p = tmp_path / "provider_quota.json"
    p.write_text(json.dumps({"OpenRouter": {"remaining_fraction": 1.2, "unit": "tokens", "source": "merged"}}))

    quota = load_provider_quota(p)

    assert quota["openrouter"]["remaining_fraction"] == 1.0
    assert quota["openrouter"]["source"] == "merged"


def test_empty_slot_has_null_best_and_atomic_write(tmp_path):
    snapshot = build_snapshot_from_dossiers(
        [],
        {"R_empty": {"label": "No candidate", "eval_mode": "free"}},
        scan_id=1,
        generated_at="2026-06-02T12:00:00Z",
    )
    target = write_snapshot(snapshot, tmp_path / "routing_snapshot.json")

    loaded = json.loads(target.read_text())
    Draft202012Validator(_schema()).validate(loaded)
    assert loaded["slots"]["R_empty"]["best"] is None
    assert loaded["slots"]["R_empty"]["candidates"] == []


def test_gateway_routing_snapshot_serves_latest_file(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    import gateway

    snapshot = build_snapshot_from_dossiers(
        [Dossier("openrouter", "m", "openrouter/m", slot_fitness={"R": 10})],
        {"R": {"label": "role", "eval_mode": "free"}},
        scan_id=7,
        generated_at="2026-06-02T12:00:00Z",
    )
    target = write_snapshot(snapshot, tmp_path / "routing_snapshot.json")
    monkeypatch.setattr(gateway, "DEFAULT_SNAPSHOT_PATH", target)

    resp = TestClient(gateway.app).get("/routing-snapshot")

    assert resp.status_code == 200
    assert resp.json()["scan_id"] == 7


def test_reliability_feedback_degrades_provider_health():
    health = provider_health_from_dossiers(
        [Dossier("OpenRouter", "m", "openrouter/m")],
        {"openrouter": {"error_rate": 0.5, "rate_limit_frequency": 0.0}},
    )

    assert health["OpenRouter"] == "degraded"


def test_gateway_accepts_reliability_feedback(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    import gateway

    target = tmp_path / "reliability_feedback.jsonl"
    monkeypatch.setattr(gateway, "RELIABILITY_FEEDBACK_PATH", target)

    resp = TestClient(gateway.app).post(
        "/reliability",
        json={"providers": {"openrouter": {"requests": 2, "error_rate": 0.5}}},
    )

    assert resp.status_code == 200
    assert resp.json()["accepted"] is True
    assert json.loads(target.read_text())["providers"]["openrouter"]["requests"] == 2
