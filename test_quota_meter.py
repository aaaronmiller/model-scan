from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

import quota_meter as qm
from routing_snapshot import load_provider_quota

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _schema() -> dict:
    return json.loads((Path(__file__).parent / "contracts" / "routing_snapshot.schema.json").read_text())


def _quota_state_validator() -> Draft202012Validator:
    schema = _schema()
    sub = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/quotaState"}
    return Draft202012Validator(sub)


# ---------------------------------------------------------------- Pattern A


def test_headers_yield_measured_fraction():
    reading = qm.reading_from_headers(
        "groq",
        {
            "x-ratelimit-remaining-requests": "7000",
            "x-ratelimit-limit-requests": "14000",
            "x-ratelimit-reset-requests": "2m30s",
        },
        now=NOW,
    )
    assert reading.remaining_fraction == 0.5
    assert reading.confidence == qm.CONFIDENCE_MEASURED
    assert reading.source == qm.SOURCE_LIVE
    assert reading.reset_at == NOW + timedelta(seconds=150)


def test_header_matching_is_case_insensitive():
    reading = qm.reading_from_headers(
        "openrouter",
        {"X-RateLimit-Remaining": "10", "X-RateLimit-Limit": "40"},
        now=NOW,
    )
    assert reading.remaining_fraction == 0.25


def test_named_scheme_falls_back_to_generic_headers():
    """A named scheme is a preference, not an exclusive filter. Groq has its own
    header names, but a response carrying only the generic ones still tells us
    the answer and must not be discarded."""
    reading = qm.reading_from_headers(
        "groq", {"x-ratelimit-remaining": "3", "x-ratelimit-limit": "12"}, now=NOW
    )
    assert reading.remaining_fraction == 0.25
    assert reading.confidence == qm.CONFIDENCE_MEASURED


def test_provider_specific_headers_win_when_both_are_present():
    reading = qm.reading_from_headers(
        "groq",
        {
            "x-ratelimit-remaining-requests": "1",
            "x-ratelimit-limit-requests": "10",
            "x-ratelimit-remaining": "9",
            "x-ratelimit-limit": "10",
        },
        now=NOW,
    )
    assert reading.remaining_fraction == 0.1


def test_explicit_scheme_is_not_overridden_by_fallback():
    reading = qm.reading_from_headers(
        "groq", {"x-ratelimit-remaining": "3", "x-ratelimit-limit": "12"},
        scheme="groq", now=NOW,
    )
    assert reading.remaining_fraction is None


def test_missing_headers_fail_to_unknown_not_to_a_guess():
    """The spec requires failing to unknown rather than inventing capacity."""
    reading = qm.reading_from_headers("groq", {"content-type": "application/json"}, now=NOW)
    assert reading.remaining_fraction is None
    assert reading.confidence == qm.CONFIDENCE_UNKNOWN
    assert not reading.is_known()


def test_zero_limit_does_not_divide_by_zero():
    reading = qm.reading_from_headers(
        "generic", {"x-ratelimit-remaining": "0", "x-ratelimit-limit": "0"}, now=NOW
    )
    assert reading.remaining_fraction is None
    assert reading.confidence == qm.CONFIDENCE_UNKNOWN


def test_reset_parses_epoch_and_iso_and_seconds():
    epoch = qm._parse_reset("1785400000", NOW)
    assert epoch is not None and epoch.year == 2026
    iso = qm._parse_reset("2026-07-29T13:00:00Z", NOW)
    assert iso == datetime(2026, 7, 29, 13, 0, 0, tzinfo=timezone.utc)
    secs = qm._parse_reset("90", NOW)
    assert secs == NOW + timedelta(seconds=90)
    assert qm._parse_reset("not-a-time", NOW) is None


# ---------------------------------------------------------------- budget tier


def test_budget_window_computes_remaining_fraction():
    window = qm.BUDGET_WINDOWS["opencode-go"][0]  # 12 USD / 5h
    reading = qm.reading_from_budget(window, spent=3.0, window_started_at=NOW, now=NOW)
    assert reading.remaining_fraction == 0.75
    assert reading.unit == "usd"
    assert reading.reset_at == NOW + timedelta(hours=5)
    assert reading.confidence == qm.CONFIDENCE_MEASURED


def test_budget_window_rolls_over_after_period():
    window = qm.BUDGET_WINDOWS["opencode-go"][0]
    later = NOW + timedelta(hours=6)
    reading = qm.reading_from_budget(window, spent=12.0, window_started_at=NOW, now=later)
    assert reading.remaining_fraction == 1.0


def test_overspend_clamps_to_zero_not_negative():
    window = qm.BUDGET_WINDOWS["opencode-go"][0]
    reading = qm.reading_from_budget(window, spent=99.0, window_started_at=NOW, now=NOW)
    assert reading.remaining_fraction == 0.0


def test_seeded_windows_are_estimates_never_measured():
    for reading in qm.seed_estimated_windows(now=NOW):
        assert reading.confidence == qm.CONFIDENCE_ESTIMATED
        assert reading.source == qm.SOURCE_MODEL_SCAN


# ---------------------------------------------------------------- precedence


def test_live_measured_beats_local_estimate():
    live = qm.reading_from_headers(
        "openrouter", {"x-ratelimit-remaining": "1", "x-ratelimit-limit": "10"}, now=NOW
    )
    est = qm.QuotaReading(
        provider="openrouter",
        remaining_fraction=0.9,
        confidence=qm.CONFIDENCE_ESTIMATED,
        source=qm.SOURCE_MODEL_SCAN,
        observed_at=NOW,
    )
    merged = qm.merge_readings([est, live])
    assert merged is not None
    assert merged.remaining_fraction == 0.1


def test_tightest_window_wins_among_equals():
    """The binding constraint is the smallest remaining fraction."""
    a = qm.QuotaReading("opencode-go", 0.8, qm.CONFIDENCE_MEASURED, qm.SOURCE_MODEL_SCAN, NOW, window_label="week")
    b = qm.QuotaReading("opencode-go", 0.2, qm.CONFIDENCE_MEASURED, qm.SOURCE_MODEL_SCAN, NOW, window_label="5h")
    merged = qm.merge_readings([a, b])
    assert merged is not None and merged.remaining_fraction == 0.2


def test_all_unknown_stays_unknown():
    merged = qm.merge_readings([qm.unknown_reading("kilo", now=NOW), qm.unknown_reading("kilo", now=NOW)])
    assert merged is not None and not merged.is_known()


# ---------------------------------------------------- opportunity cost


def test_unknown_reading_does_not_look_cheap():
    """Ignorance must never make a provider appear attractive."""
    cost = qm.opportunity_cost(qm.unknown_reading("kilo", now=NOW), nominal_cost=1.0, now=NOW)
    assert cost == 1.0


def test_exhausted_window_is_not_a_candidate():
    reading = qm.QuotaReading("x", 0.0, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW)
    assert qm.opportunity_cost(reading, nominal_cost=1.0, now=NOW) == float("inf")


def test_capacity_near_reset_gets_cheaper_not_dearer():
    """Use-it-or-lose-it: expiring unused capacity must be discounted."""
    plenty_of_time = qm.QuotaReading(
        "x", 0.9, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW, reset_at=NOW + timedelta(hours=5)
    )
    about_to_expire = qm.QuotaReading(
        "x", 0.9, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW, reset_at=NOW + timedelta(minutes=2)
    )
    far = qm.opportunity_cost(plenty_of_time, nominal_cost=1.0, now=NOW)
    near = qm.opportunity_cost(about_to_expire, nominal_cost=1.0, now=NOW)
    assert near < far, "capacity about to expire unused should be cheaper"


def test_reserve_protection_is_the_only_thing_that_raises_cost():
    low = qm.QuotaReading(
        "x", 0.05, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW, reset_at=NOW + timedelta(hours=4)
    )
    guarded = qm.opportunity_cost(low, nominal_cost=1.0, now=NOW, reserve_fraction=0.30)
    unguarded = qm.opportunity_cost(low, nominal_cost=1.0, now=NOW, reserve_fraction=0.0)
    assert guarded > 1.0
    assert unguarded <= 1.0


# ------------------------------------------------- contract conformance


def test_emitted_state_validates_against_shared_contract():
    validator = _quota_state_validator()
    reading = qm.reading_from_headers(
        "groq",
        {
            "x-ratelimit-remaining-requests": "300",
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-reset-requests": "60s",
        },
        now=NOW,
    )
    state = qm.to_quota_state(reading, best_tier_available="A")
    assert state is not None
    validator.validate(state)


def test_unknown_reading_is_omitted_rather_than_fabricated():
    assert qm.to_quota_state(qm.unknown_reading("kilo", now=NOW)) is None
    payload = qm.build_provider_quota([qm.unknown_reading("kilo", now=NOW)])
    assert payload == {}


def test_full_payload_validates_and_round_trips_through_the_consumer(tmp_path):
    """End to end: meter output must be readable by the existing snapshot loader."""
    readings = [
        qm.reading_from_headers(
            "groq",
            {
                "x-ratelimit-remaining-requests": "500",
                "x-ratelimit-limit-requests": "2000",
                "x-ratelimit-reset-requests": "120s",
            },
            now=NOW,
        ),
        qm.reading_from_budget(qm.BUDGET_WINDOWS["opencode-go"][0], spent=6.0, window_started_at=NOW, now=NOW),
        qm.unknown_reading("kilo", now=NOW),
    ]
    payload = qm.build_provider_quota(readings)
    assert set(payload) == {"groq", "opencode-go"}, "unknown providers must not appear"

    validator = _quota_state_validator()
    for state in payload.values():
        validator.validate(state)

    target = tmp_path / "provider_quota.json"
    qm.write_provider_quota(payload, target)
    loaded = load_provider_quota(target)

    assert loaded["groq"]["remaining_fraction"] == 0.25
    assert loaded["opencode-go"]["remaining_fraction"] == 0.5
    assert "kilo" not in loaded


def test_ledger_retains_confidence_the_contract_cannot_carry(tmp_path):
    ledger = tmp_path / "quota_ledger.jsonl"
    reading = qm.unknown_reading("kilo", now=NOW, reason="no-source")
    qm.append_observation(reading, ledger)
    row = json.loads(ledger.read_text().strip())
    assert row["confidence"] == qm.CONFIDENCE_UNKNOWN
    assert row["provenance"] == "no-source"
    assert row["remaining_fraction"] is None


def test_ledger_deduplicates_stable_request_id(tmp_path):
    ledger = tmp_path / "quota_ledger.jsonl"
    reading = qm.unknown_reading("kilo", now=NOW, reason="no-source")

    first = qm.append_observation_once(reading, "req-1", ledger)
    second = qm.append_observation_once(reading, "req-1", ledger)

    assert first == (ledger, True)
    assert second == (ledger, False)
    assert len(ledger.read_text().splitlines()) == 1


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    target = tmp_path / "provider_quota.json"
    qm.write_provider_quota({"groq": {"remaining_fraction": 0.5}}, target)
    assert target.exists()
    assert not list(tmp_path.glob("*.tmp"))


# ---------------------------------------- account scope and resource
# One provider can meter several independent pools. Blending them would report
# a depleted pre-paid balance as refilled by an unrelated free allowance.


def test_reading_carries_account_scope_and_resource():
    r = qm.reading_from_headers(
        "groq", {"x-ratelimit-remaining": "5", "x-ratelimit-limit": "10"}, now=NOW
    )
    assert r.account_scope == "default"
    assert r.resource == "requests"


def test_prepaid_balance_is_its_own_scope_and_resource():
    r = qm.reading_from_credit_balance(qm.CREDIT_BALANCES["google"], 5.0, now=NOW)
    assert r.account_scope == "google:prepaid"
    assert r.resource == "credits"


def test_merging_across_scopes_is_refused_not_averaged():
    free = qm.QuotaReading("google", 1.0, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW)
    prepaid = qm.reading_from_credit_balance(qm.CREDIT_BALANCES["google"], 19.0, now=NOW)
    try:
        qm.merge_readings([free, prepaid])
    except ValueError as exc:
        assert "account_scope" in str(exc)
    else:
        raise AssertionError("mixed scopes must not silently merge")


def test_same_scope_still_merges_normally():
    a = qm.QuotaReading("groq", 0.8, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW)
    b = qm.QuotaReading("groq", 0.3, qm.CONFIDENCE_MEASURED, qm.SOURCE_LIVE, NOW)
    merged = qm.merge_readings([a, b])
    assert merged is not None and merged.remaining_fraction == 0.3


def test_ledger_row_records_scope_and_resource(tmp_path):
    ledger = tmp_path / "q.jsonl"
    qm.append_observation(qm.reading_from_credit_balance(
        qm.CREDIT_BALANCES["openai"], 2.0, now=NOW), ledger)
    row = json.loads(ledger.read_text().strip())
    assert row["account_scope"] == "openai:prepaid"
    assert row["resource"] == "credits"
