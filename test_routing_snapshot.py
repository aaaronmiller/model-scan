from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from routing_snapshot import (
    RoutingSnapshotRejected,
    build_snapshot_from_db,
    build_snapshot_from_dossiers,
    gateway_slot_definitions,
    load_provider_quota,
    provider_health_from_dossiers,
    validate_gateway_snapshot,
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


def test_dynamic_router_alias_is_not_a_rankable_snapshot_candidate():
    slot_defs = gateway_slot_definitions()
    fitness = {slot_id: 90 for slot_id in slot_defs}
    snapshot = build_snapshot_from_dossiers(
        [
            Dossier("openrouter", "openrouter/free", "openrouter/free", slot_fitness=fitness),
            Dossier("openrouter", "fixed/model:free", "fixed/model:free", slot_fitness=fitness),
        ],
        slot_defs,
        scan_id=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    for selection in snapshot["slots"].values():
        assert [candidate["api_model"] for candidate in selection["candidates"]] == [
            "fixed/model:free"
        ]


def test_gateway_rejects_preexisting_snapshot_with_dynamic_router_alias():
    slot_defs = gateway_slot_definitions()
    snapshot = build_snapshot_from_dossiers(
        [
            Dossier(
                "openrouter",
                "fixed/model:free",
                "fixed/model:free",
                slot_fitness={slot_id: 90 for slot_id in slot_defs},
            )
        ],
        slot_defs,
        scan_id=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    snapshot["slots"]["S01_haiku"]["candidates"][0]["api_model"] = "openrouter/free"

    try:
        validate_gateway_snapshot(snapshot)
    except RoutingSnapshotRejected as exc:
        assert "dynamic router" in str(exc)
    else:
        raise AssertionError("dynamic router alias was accepted as a stable model identity")


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

    slot_defs = gateway_slot_definitions()
    snapshot = build_snapshot_from_dossiers(
        [Dossier("openrouter", "m", "openrouter/m", slot_fitness={slot_id: 10 for slot_id in slot_defs})],
        slot_defs,
        scan_id=7,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    target = write_snapshot(snapshot, tmp_path / "routing_snapshot.json")
    monkeypatch.setattr(gateway, "DEFAULT_SNAPSHOT_PATH", target)

    resp = TestClient(gateway.app).get("/routing-snapshot")

    assert resp.status_code == 200
    assert resp.json()["scan_id"] == 7


def _snapshot_db(path: Path, *, scanned_at: str, slot_ids: list[str]) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE scans (scan_id INTEGER PRIMARY KEY, scanned_at TEXT NOT NULL);
        CREATE TABLE models (
            model_pk INTEGER PRIMARY KEY,
            scan_id INTEGER,
            provider TEXT,
            model_id TEXT,
            api_model TEXT,
            accessible INTEGER,
            has_tools INTEGER,
            has_vision INTEGER,
            price_blended REAL,
            tier TEXT
        );
        CREATE TABLE slot_fitness (
            model_pk INTEGER PRIMARY KEY AUTOINCREMENT,
            model_fk INTEGER,
            scan_id INTEGER,
            slot_id TEXT,
            fitness REAL
        );
        """
    )
    conn.execute("INSERT INTO scans VALUES (7, ?)", (scanned_at,))
    conn.execute(
        "INSERT INTO models VALUES (1, 7, 'fixture', 'm', 'fixture/m', 1, 1, 0, 0.0, 'A')"
    )
    conn.executemany(
        "INSERT INTO slot_fitness (model_fk, scan_id, slot_id, fitness) VALUES (1, 7, ?, 80.0)",
        [(slot_id,) for slot_id in slot_ids],
    )
    conn.commit()
    conn.close()
    return path


def test_db_fallback_preserves_source_scan_timestamp(tmp_path):
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    scanned_at = (now - timedelta(hours=2)).isoformat()
    db = _snapshot_db(
        tmp_path / "fresh.db",
        scanned_at=scanned_at,
        slot_ids=list(gateway_slot_definitions()),
    )

    snapshot = build_snapshot_from_db(db, now=now)

    assert snapshot is not None
    assert snapshot["generated_at"] == scanned_at.replace("+00:00", "Z")
    assert set(snapshot["slots"]) == set(gateway_slot_definitions())


def test_db_fallback_rejects_stale_scan_instead_of_restamping_it(tmp_path):
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    db = _snapshot_db(
        tmp_path / "stale.db",
        scanned_at=(now - timedelta(days=3)).isoformat(),
        slot_ids=list(gateway_slot_definitions()),
    )

    assert build_snapshot_from_db(db, now=now) is None


def test_db_fallback_rejects_legacy_role_namespace(tmp_path):
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    db = _snapshot_db(
        tmp_path / "legacy.db",
        scanned_at=now.isoformat(),
        slot_ids=["R1_primary", "R6_compression"],
    )

    assert build_snapshot_from_db(db, now=now) is None


def test_gateway_routing_snapshot_rejects_stale_or_legacy_file(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    import gateway

    snapshot = build_snapshot_from_dossiers(
        [Dossier("openrouter", "m", "openrouter/m", slot_fitness={"R1_primary": 10})],
        {"R1_primary": {"label": "legacy", "eval_mode": "free"}},
        scan_id=7,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    target = write_snapshot(snapshot, tmp_path / "routing_snapshot.json")
    monkeypatch.setattr(gateway, "DEFAULT_SNAPSHOT_PATH", target)
    monkeypatch.setattr(gateway, "build_snapshot_from_db", lambda *_args, **_kwargs: None)

    resp = TestClient(gateway.app).get("/routing-snapshot")

    assert resp.status_code == 404


def test_gateway_routing_snapshot_rejects_stale_s_slot_file(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    import gateway

    slot_defs = gateway_slot_definitions()
    snapshot = build_snapshot_from_dossiers(
        [Dossier("openrouter", "m", "openrouter/m", slot_fitness={slot_id: 10 for slot_id in slot_defs})],
        slot_defs,
        scan_id=7,
        generated_at="2026-01-01T00:00:00Z",
    )
    target = write_snapshot(snapshot, tmp_path / "routing_snapshot.json")
    monkeypatch.setattr(gateway, "DEFAULT_SNAPSHOT_PATH", target)
    monkeypatch.setattr(gateway, "build_snapshot_from_db", lambda *_args, **_kwargs: None)

    resp = TestClient(gateway.app).get("/routing-snapshot")

    assert resp.status_code == 404


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
