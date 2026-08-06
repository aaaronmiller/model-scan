from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import gateway_bridge as gb
import quota_meter as qm
import slot_grid as sg
import spend_ledger as sl

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
EPOCH = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)


def outcome(**kw) -> gb.RequestOutcome:
    base = {"model": "opencode-go/deepseek-v4-flash", "started_at": NOW}
    base.update(kw)
    return gb.RequestOutcome(**base)


# ------------------------------------------------------------- inbound


def test_provider_is_inferred_from_the_model_prefix():
    assert outcome().resolved_provider() == "opencode-go"
    assert outcome(model="groq/llama").resolved_provider() == "groq"
    assert outcome(model="bare-model").resolved_provider() == "bare-model"
    assert outcome(model="x/y", provider="Explicit").resolved_provider() == "explicit"


def test_cost_header_is_preferred_over_the_supplied_figure():
    ev = gb.spend_event_from_outcome(outcome(cost=9.0, headers={"X-Cost-USD": "1.25"}))
    assert ev is not None and ev.amount == 1.25


def test_no_cost_anywhere_records_nothing_rather_than_guessing():
    """Inferring spend from token counts is excluded on purpose."""
    assert gb.spend_event_from_outcome(outcome()) is None
    assert gb.spend_event_from_outcome(outcome(cost=None, headers={"content-type": "x"})) is None


def test_negative_or_nonsense_cost_is_rejected():
    assert gb.spend_event_from_outcome(outcome(cost=-3.0)) is None
    assert gb.spend_event_from_outcome(outcome(cost="abc")) is None


def test_quota_reading_comes_from_headers_when_present():
    reading = gb.quota_reading_from_outcome(
        outcome(headers={"x-ratelimit-remaining": "5", "x-ratelimit-limit": "20"}), now=NOW
    )
    assert reading is not None and reading.remaining_fraction == 0.25


def test_insufficient_headers_yield_no_reading():
    assert gb.quota_reading_from_outcome(outcome(headers={"x-foo": "1"}), now=NOW) is None
    assert gb.quota_reading_from_outcome(outcome(), now=NOW) is None


def test_observe_writes_both_ledgers(tmp_path):
    spend = tmp_path / "spend.jsonl"
    ledger = tmp_path / "quota.jsonl"
    result = gb.observe(
        outcome(cost=0.5, headers={"x-ratelimit-remaining": "10", "x-ratelimit-limit": "40"}),
        spend_path=spend,
        ledger_path=ledger,
        now=NOW,
    )
    assert result["spend_recorded"] and result["quota_recorded"]
    assert len(list(sl.iter_events(spend))) == 1
    assert json.loads(ledger.read_text().strip())["remaining_fraction"] == 0.25


def test_observe_never_raises_on_a_bad_record(tmp_path):
    """A gateway callback must not be able to break request handling."""
    result = gb.observe(outcome(cost=float("nan")), spend_path=tmp_path / "s.jsonl", now=NOW)
    assert result["spend_recorded"] is False


def test_observe_with_nothing_useful_is_a_no_op(tmp_path):
    spend = tmp_path / "s.jsonl"
    result = gb.observe(outcome(), spend_path=spend, ledger_path=tmp_path / "q.jsonl", now=NOW)
    assert not result["spend_recorded"] and not result["quota_recorded"]
    assert not spend.exists()


# ------------------------------------------------------------- litellm shape


def test_litellm_callback_extracts_cost_and_headers(tmp_path):
    class Response:
        _hidden_params = {
            "additional_headers": {"x-ratelimit-remaining": "3", "x-ratelimit-limit": "12"}
        }

    result = gb.litellm_success_callback(
        {
            "model": "groq/llama-70b",
            "response_cost": 0.02,
            "litellm_params": {"metadata": {"slot_id": "S01_haiku", "request_id": "req-1"}},
        },
        Response(),
        NOW,
        NOW,
        spend_path=tmp_path / "spend.jsonl",
        ledger_path=tmp_path / "quota.jsonl",
    )
    assert result["spend_recorded"] and result["quota_recorded"]
    event = list(sl.iter_events(tmp_path / "spend.jsonl"))[0]
    assert event.provider == "groq" and event.amount == 0.02
    assert event.slot_id == "S01_haiku" and event.request_id == "req-1"


def test_litellm_callback_survives_a_minimal_payload(tmp_path):
    result = gb.litellm_success_callback({}, None, None, None, spend_path=tmp_path / "s.jsonl")
    assert result["spend_recorded"] is False


def test_litellm_callback_reads_standard_logging_object(tmp_path):
    result = gb.litellm_success_callback(
        {
            "model": "groq/x",
            "litellm_call_id": "call-standard-1",
            "standard_logging_object": {"response_cost": 0.4},
        },
        None,
        NOW,
        NOW,
        spend_path=tmp_path / "s.jsonl",
    )
    assert result["spend_recorded"] and result["amount"] == 0.4


def test_litellm_callback_deduplicates_stable_call_id(tmp_path):
    spend_path = tmp_path / "s.jsonl"
    quota_path = tmp_path / "q.jsonl"
    payload = {
        "model": "groq/x",
        "response_cost": 0.4,
        "litellm_call_id": "call-1",
        "additional_headers": {
            "x-ratelimit-remaining": "3",
            "x-ratelimit-limit": "12",
        },
    }

    first = gb.litellm_success_callback(
        payload, None, NOW, NOW, spend_path=spend_path, ledger_path=quota_path
    )
    second = gb.litellm_success_callback(
        payload, None, NOW, NOW, spend_path=spend_path, ledger_path=quota_path
    )

    assert first["spend_recorded"] is True
    assert first["quota_recorded"] is True
    assert second["spend_recorded"] is False
    assert second["quota_recorded"] is False
    assert second["spend_duplicate"] is True
    assert second["quota_duplicate"] is True
    assert len(list(sl.iter_events(spend_path))) == 1
    assert len(quota_path.read_text().splitlines()) == 1


def test_litellm_callback_declines_spend_without_stable_id(tmp_path):
    path = tmp_path / "s.jsonl"

    result = gb.litellm_success_callback(
        {"model": "groq/x", "response_cost": 0.4},
        None,
        NOW,
        NOW,
        spend_path=path,
    )

    assert result["spend_recorded"] is False
    assert "missing stable request_id" in result["observation_error"]
    assert not path.exists()


def test_litellm_callback_declines_quota_without_stable_id(tmp_path):
    path = tmp_path / "q.jsonl"

    result = gb.litellm_success_callback(
        {
            "model": "groq/x",
            "additional_headers": {
                "x-ratelimit-remaining": "3",
                "x-ratelimit-limit": "12",
            },
        },
        None,
        NOW,
        NOW,
        ledger_path=path,
    )

    assert result["quota_recorded"] is False
    assert "missing stable request_id" in result["observation_error"]
    assert not path.exists()


# ------------------------------------------------------------- refresh


def test_refresh_quota_publishes_measured_state(tmp_path):
    spend = tmp_path / "spend.jsonl"
    sl.record_spend(sl.SpendEvent("opencode-go", 6.0, "usd", EPOCH + timedelta(minutes=5)), spend)
    payload = gb.refresh_quota(
        windows=qm.BUDGET_WINDOWS["opencode-go"],
        spend_path=spend,
        ledger_path=tmp_path / "absent.jsonl",
        quota_path=tmp_path / "provider_quota.json",
        epoch=EPOCH,
        now=NOW,
    )
    assert payload["opencode-go"]["remaining_fraction"] == 0.5  # tightest window binds
    assert (tmp_path / "provider_quota.json").exists()


def test_refresh_quota_replays_the_most_recent_live_reading(tmp_path):
    ledger = tmp_path / "quota.jsonl"
    old = qm.reading_from_headers(
        "groq", {"x-ratelimit-remaining": "9", "x-ratelimit-limit": "10"}, now=NOW - timedelta(hours=2)
    )
    new = qm.reading_from_headers(
        "groq", {"x-ratelimit-remaining": "1", "x-ratelimit-limit": "10"}, now=NOW
    )
    qm.append_observation(old, ledger)
    qm.append_observation(new, ledger)
    payload = gb.refresh_quota(
        windows=[],
        spend_path=tmp_path / "none.jsonl",
        ledger_path=ledger,
        quota_path=tmp_path / "pq.json",
        epoch=EPOCH,
        now=NOW,
    )
    assert payload["groq"]["remaining_fraction"] == 0.1, "newest live reading must win"


def test_refresh_quota_omits_providers_with_no_usable_data(tmp_path):
    payload = gb.refresh_quota(
        windows=[],
        spend_path=tmp_path / "a.jsonl",
        ledger_path=tmp_path / "b.jsonl",
        quota_path=tmp_path / "pq.json",
        epoch=EPOCH,
        now=NOW,
    )
    assert payload == {}


# ------------------------------------------------------------- outbound


def _snapshot(quota: dict) -> dict:
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    pool = [cand("go/deepseek", "opencode-go", 78), cand("kilo/ultra", "kilo", 72)]
    return {
        "schema_version": "1.0.0",
        "generated_at": NOW.isoformat().replace("+00:00", "Z"),
        "scan_id": "t",
        "blocklist": [],
        "provider_quota": quota,
        "slots": {
            s.slot_id: {"label": s.label, "eval_mode": "free", "best": None, "candidates": pool}
            for s in sg.SLOTS
        },
    }


def test_build_redirect_table_maps_vendor_models_to_targets():
    table, resolutions = gb.build_redirect_table(
        _snapshot({"opencode-go": {"remaining_fraction": 0.8}}),
        [("claude-opus-5", "medium"), ("gpt-5.5", "high")],
        candidate_ranks={"go/deepseek": 4, "kilo/ultra": 3},
        now=NOW,
    )
    assert table["claude-opus-5"] in {"go/deepseek", "kilo/ultra"}
    assert "gpt-5.5" not in table
    assert resolutions["S07_opus_medium"].resolved


def test_slots_below_floor_are_absent_so_vendor_default_holds():
    table, _ = gb.build_redirect_table(
        _snapshot({}),
        [("claude-fable-5", "max")],
        candidate_ranks={"go/deepseek": 4, "kilo/ultra": 3},
        now=NOW,
    )
    assert table == {}, "no free candidate meets the fable-max floor"


def test_litellm_aliases_are_shaped_for_model_list_and_carry_no_secrets():
    entries = gb.litellm_model_aliases({"claude-opus-5": "go/deepseek"})
    assert entries == [
        {
            "model_name": "claude-opus-5",
            "litellm_params": {"model": "go/deepseek"},
            "model_info": {"managed_by": "model-scan", "redirect_of": "claude-opus-5"},
        }
    ]
    assert "api_key" not in json.dumps(entries)


def test_overrides_are_written_atomically(tmp_path):
    target = tmp_path / "overrides.json"
    gb.write_litellm_overrides({"claude-opus-5": "go/deepseek"}, target)
    payload = json.loads(target.read_text())
    assert payload["model_list"][0]["model_name"] == "claude-opus-5"
    assert not list(tmp_path.glob("*.tmp"))


def test_utilization_report_ranks_the_most_wasted_window_first(tmp_path):
    spend = tmp_path / "spend.jsonl"
    sl.record_spend(sl.SpendEvent("opencode-go", 0.2, "usd", EPOCH + timedelta(minutes=5)), spend)
    rows = gb.utilization_report(
        windows=qm.BUDGET_WINDOWS["opencode-go"], spend_path=spend, epoch=EPOCH, now=NOW
    )
    assert len(rows) == 3
    assert rows[0]["projected_waste"] >= rows[-1]["projected_waste"]
    assert all(0.0 <= r["projected_waste"] <= 1.0 for r in rows)


# --------------------------- regression: provider is not the id prefix
# Recorded user correction, 2026-06-02, stated twice: the leading segment of a
# model id is not the provider. Filing spend under a protocol adapter corrupts
# every per-provider total.


def test_api_base_host_beats_the_id_prefix():
    assert gb.resolve_provider("openai/qwen/qwen3-next-80b",
                               "https://integrate.api.nvidia.com/v1") == "nvidia"
    assert gb.resolve_provider("openai/qwen/qwen3-32b",
                               "https://api.groq.com/openai/v1") == "groq"


def test_openrouter_prefix_is_a_real_routing_provider():
    """'google/gemma...' behind openrouter/ is an OpenRouter model."""
    assert gb.resolve_provider("openrouter/google/gemma-4-26b:free") == "openrouter"


def test_adapter_prefix_without_api_base_returns_unknown_not_a_guess():
    assert gb.resolve_provider("openai/qwen/qwen3-next-80b") == ""


def test_unknown_provider_declines_to_record_spend():
    """Better to record nothing than to attribute spend to 'openai'."""
    o = gb.RequestOutcome(model="openai/qwen/qwen3-next", started_at=NOW, cost=1.5)
    assert gb.spend_event_from_outcome(o) is None


def test_unknown_provider_declines_to_record_quota():
    o = gb.RequestOutcome(model="openai/qwen/q", started_at=NOW,
                          headers={"x-ratelimit-remaining": "5", "x-ratelimit-limit": "10"})
    assert gb.quota_reading_from_outcome(o, now=NOW) is None


def test_api_base_makes_the_same_request_recordable():
    o = gb.RequestOutcome(model="openai/qwen/qwen3-next", started_at=NOW, cost=1.5,
                          api_base="https://integrate.api.nvidia.com/v1")
    ev = gb.spend_event_from_outcome(o)
    assert ev is not None and ev.provider == "nvidia"


def test_litellm_callback_reads_api_base_from_params(tmp_path):
    gb.litellm_success_callback(
        {"model": "openai/nvidia/nemotron", "response_cost": 0.3,
         "litellm_call_id": "call-api-base-1",
         "litellm_params": {"api_base": "https://integrate.api.nvidia.com/v1"}},
        None, NOW, NOW, spend_path=tmp_path / "s.jsonl",
    )
    ev = list(sl.iter_events(tmp_path / "s.jsonl"))[0]
    assert ev.provider == "nvidia", "must not be filed under 'openai'"


def test_explicit_provider_still_wins():
    o = gb.RequestOutcome(model="openai/x", started_at=NOW, provider="Groq")
    assert o.resolved_provider() == "groq"
