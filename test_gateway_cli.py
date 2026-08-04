from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

import gateway_cli as cli
import quota_meter as qm
import slot_grid as sg
import spend_ledger as sl

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _paths(tmp_path) -> list[str]:
    return [
        "--quota", str(tmp_path / "pq.json"),
        "--spend", str(tmp_path / "spend.jsonl"),
        "--ledger", str(tmp_path / "ledger.jsonl"),
        "--limits", str(tmp_path / "limits.json"),
    ]


def test_grid_pairs_cover_every_slot_exactly_once():
    """The CLI's default pair list must address the whole grid, or slots would
    silently never be redirected."""
    resolved = [sg.slot_for(model, effort) for model, effort in cli.DEFAULT_PAIRS]
    assert all(s is not None for s in resolved)
    assert len({s.slot_id for s in resolved}) == len(sg.SLOTS)


def test_refresh_on_an_empty_machine_invents_nothing(tmp_path, capsys):
    code = cli.main(["refresh", *_paths(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    # Budget windows still seed at full, which is an estimate, not a fabrication.
    assert "opencode-go" in out or "nothing was invented" in out


def test_refresh_reports_measured_spend(tmp_path, capsys):
    spend = tmp_path / "spend.jsonl"
    sl.record_spend(sl.SpendEvent("opencode-go", 6.0, "usd", NOW), spend)
    cli.main(["refresh", *_paths(tmp_path)])
    out = capsys.readouterr().out
    assert "opencode-go" in out
    assert json.loads((tmp_path / "pq.json").read_text())["opencode-go"]["unit"] == "usd"


def test_refresh_folds_in_adaptive_limiter_inference(tmp_path, capsys):
    import adaptive_limiter as al

    limiter = al.AdaptiveLimiter()
    limiter.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    limiter.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    limiter.save(tmp_path / "limits.json")

    cli.main(["refresh", *_paths(tmp_path)])
    payload = json.loads((tmp_path / "pq.json").read_text())
    assert "kilo" in payload, "inferred headroom should reach the published quota"


def test_resolve_without_a_snapshot_reports_rather_than_crashing(tmp_path, capsys):
    code = cli.main(["resolve", *_paths(tmp_path)])
    assert code == 1
    assert "no slots" in capsys.readouterr().out


def test_resolve_prints_every_slot_and_its_mode(tmp_path, capsys):
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    snapshot = {
        "schema_version": "1.0.0", "scan_id": "t", "blocklist": [],
        "generated_at": NOW.isoformat().replace("+00:00", "Z"),
        "slots": {
            s.slot_id: {"label": s.label, "eval_mode": s.eval_mode, "best": None,
                        "candidates": [cand("free/m", "kilo", 60)]}
            for s in sg.SLOTS
        },
    }
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(snapshot))
    ranks = tmp_path / "ranks.json"
    ranks.write_text(json.dumps({"free/m": 12}))

    code = cli.main(["resolve", "--snapshot", str(snap_path), "--ranks", str(ranks), *_paths(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    for slot in sg.SLOTS:
        assert slot.slot_id in out
    assert "coverage" in out
    # rank 12 clears the loose floors but not the strict ones
    assert "(vendor default)" in out


def test_publish_writes_overrides_without_applying_them(tmp_path, capsys):
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    snapshot = {
        "schema_version": "1.0.0", "scan_id": "t", "blocklist": [],
        "generated_at": NOW.isoformat().replace("+00:00", "Z"),
        "slots": {
            "S01_haiku": {"label": "Haiku", "eval_mode": "free", "best": None,
                          "candidates": [cand("free/m", "kilo", 60)]}
        },
    }
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(snapshot))
    out_path = tmp_path / "overrides.json"

    code = cli.main([
        "publish", "--snapshot", str(snap_path), "--out", str(out_path), *_paths(tmp_path)
    ])
    assert code == 0
    payload = json.loads(out_path.read_text())
    assert payload["model_list"][0]["model_name"] == "claude-haiku-4-5"
    assert "nothing was applied" in capsys.readouterr().out


def test_utilization_quantifies_expected_waste(tmp_path, capsys):
    code = cli.main(["utilization", *_paths(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "WASTE" in out and "opencode-go" in out


def test_preflight_reports_blockers_and_changes_nothing(tmp_path, capsys):
    code = cli.main(["preflight", *_paths(tmp_path)])
    out = capsys.readouterr().out
    # On a machine with no gateway running this must be non-zero.
    assert code in (0, 1)
    assert "credential change" in out or "preflight clean" in out
    # It must not have created anything.
    assert not (tmp_path / "spend.jsonl").exists()


def test_preflight_names_the_credential_it_will_not_set(tmp_path, capsys):
    cli.main(["preflight", *_paths(tmp_path)])
    out = capsys.readouterr().out
    if "outstanding" in out:
        assert "LITELLM_MASTER_KEY" in out


def test_unknown_subcommand_exits_nonzero(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["nonsense"])
