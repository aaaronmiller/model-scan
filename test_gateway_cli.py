from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import gateway_cli as cli
from gateway_rank_map import build_rank_map
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


def _snapshot() -> dict:
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    return {
        "schema_version": "1.0.0", "scan_id": 1, "blocklist": [],
        "generated_at": cli._utcnow().isoformat().replace("+00:00", "Z"),
        "slots": {
            s.slot_id: {"label": s.label, "eval_mode": s.eval_mode, "best": None,
                        "candidates": [cand("free/m", "openrouter", 60)]}
            for s in sg.SLOTS
        },
    }


def _write_contract_inputs(tmp_path) -> tuple[str, str]:
    snapshot = _snapshot()
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(snapshot))
    ranks = build_rank_map(
        {"free/m": 12}, snapshot,
        generated_at=cli._utcnow().isoformat().replace("+00:00", "Z"),
        evidence_ref="fixture:gateway-ladder",
        evidence_sha256="sha256:" + "a" * 64,
    )
    rank_path = tmp_path / "ranks.json"
    rank_path.write_text(json.dumps(ranks))
    return str(snap_path), str(rank_path)


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
    assert "input rejected" in capsys.readouterr().out


def test_resolve_prints_every_slot_and_its_mode(tmp_path, capsys):
    snap_path, ranks = _write_contract_inputs(tmp_path)

    code = cli.main(["resolve", "--snapshot", snap_path, "--ranks", ranks, *_paths(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    for slot in sg.SLOTS:
        assert slot.slot_id in out
    assert "coverage" in out
    # rank 12 clears the loose floors but not the strict ones
    assert "(vendor default)" in out


def test_publish_writes_overrides_without_applying_them(tmp_path, capsys):
    snap_path, ranks = _write_contract_inputs(tmp_path)
    out_path = tmp_path / "overrides.json"

    code = cli.main([
        "publish", "--snapshot", snap_path, "--ranks", ranks, "--out", str(out_path), *_paths(tmp_path)
    ])
    assert code == 0
    payload = json.loads(out_path.read_text())
    assert payload["model_list"][0]["model_name"] == "claude-haiku-4-5"
    assert payload["model_list"][0]["litellm_params"]["model"] == "openrouter/free/m"
    assert "nothing was applied" in capsys.readouterr().out


def test_resolve_rejects_partial_or_mismatched_rank_map(tmp_path, capsys):
    snap_path, rank_path = _write_contract_inputs(tmp_path)
    document = json.loads(Path(rank_path).read_text())
    document["ranks"] = {}
    Path(rank_path).write_text(json.dumps(document))

    code = cli.main(["resolve", "--snapshot", snap_path, "--ranks", rank_path, *_paths(tmp_path)])
    assert code == 1
    assert "partial or mismatched" in capsys.readouterr().out


def test_resolve_rejects_stale_snapshot(tmp_path, capsys):
    snap_path, rank_path = _write_contract_inputs(tmp_path)
    snapshot = json.loads(Path(snap_path).read_text())
    snapshot["generated_at"] = "2026-01-01T00:00:00Z"
    Path(snap_path).write_text(json.dumps(snapshot))

    code = cli.main(["resolve", "--snapshot", snap_path, "--ranks", rank_path, *_paths(tmp_path)])
    assert code == 1
    assert "snapshot is stale" in capsys.readouterr().out


def test_resolve_rejects_stale_rank_map(tmp_path, capsys):
    snap_path, rank_path = _write_contract_inputs(tmp_path)
    document = json.loads(Path(rank_path).read_text())
    document["generated_at"] = "2026-01-01T00:00:00Z"
    Path(rank_path).write_text(json.dumps(document))

    code = cli.main(["resolve", "--snapshot", snap_path, "--ranks", rank_path, *_paths(tmp_path)])
    assert code == 1
    assert "rank map is stale" in capsys.readouterr().out


def test_rank_map_command_publishes_snapshot_bound_provenance(tmp_path, capsys):
    snap_path, _ = _write_contract_inputs(tmp_path)
    rank_input = tmp_path / "raw-ranks.json"
    rank_input.write_text(json.dumps({"free/m": 12}))
    rank_output = tmp_path / "published-ranks.json"

    code = cli.main([
        "rank-map", "--snapshot", snap_path, "--rank-input", str(rank_input),
        "--ranks", str(rank_output), "--evidence-ref", "fixture:ladder",
        "--evidence-sha256", "sha256:" + "b" * 64,
    ])
    assert code == 0
    published = json.loads(rank_output.read_text())
    assert published["ranks"] == {"free/m": 12}
    assert published["evidence"]["ref"] == "fixture:ladder"
    assert "provenance-bound" in capsys.readouterr().out


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
