from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import adaptive_limiter as al
import quota_meter as qm

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_starts_with_no_knowledge_and_permits_sending():
    lim = al.AdaptiveLimiter()
    assert lim.may_send("kilo", now=NOW)
    assert lim.headroom_fraction("kilo") is None, "no ceiling evidence yet"


def test_success_increases_the_rate_additively():
    lim = al.AdaptiveLimiter()
    start = lim.state_for("kilo").rate_rpm
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    assert lim.state_for("kilo").rate_rpm == start + al.RATE_INCREASE_PER_SUCCESS


def test_refusal_decreases_the_rate_multiplicatively():
    lim = al.AdaptiveLimiter()
    start = lim.state_for("kilo").rate_rpm
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    assert lim.state_for("kilo").rate_rpm == start * al.RATE_DECREASE_FACTOR


def test_status_code_429_is_read_as_a_refusal():
    lim = al.AdaptiveLimiter()
    start = lim.state_for("kilo").rate_rpm
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW, status_code=429)
    assert lim.state_for("kilo").rate_rpm < start


def test_transport_error_is_not_treated_as_a_rate_signal():
    """Slowing down for a dropped connection would conflate unavailability with
    throttling and degrade the pace for the wrong reason."""
    lim = al.AdaptiveLimiter()
    start = lim.state_for("kilo").rate_rpm
    lim.observe("kilo", al.OUTCOME_ERROR, at=NOW)
    assert lim.state_for("kilo").rate_rpm == start
    assert lim.state_for("kilo").refusals == 0


def test_repeated_refusals_compound_the_backoff():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    after_one = lim.state_for("kilo").rate_rpm
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    after_two = lim.state_for("kilo").rate_rpm
    assert after_two < after_one * al.RATE_DECREASE_FACTOR + 1e-9


def test_a_success_resets_the_consecutive_refusal_counter():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    assert lim.state_for("kilo").consecutive_refusals == 0


def test_rate_never_falls_below_the_floor():
    lim = al.AdaptiveLimiter()
    for _ in range(50):
        lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    assert lim.state_for("kilo").rate_rpm >= al.MIN_RATE_RPM


def test_rate_does_not_climb_back_above_a_known_bad_rate():
    """Without this the limiter oscillates across the limit forever."""
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    bad = lim.state_for("kilo").worst_known_bad_rpm
    for _ in range(200):
        lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    assert lim.state_for("kilo").rate_rpm < bad


def test_converges_toward_the_true_limit_without_being_told_it():
    """Simulate a provider that refuses above 20 rpm. The limiter must settle
    below that, never having been given the number."""
    lim = al.AdaptiveLimiter()
    true_limit = 20.0
    for _ in range(300):
        state = lim.state_for("sim")
        outcome = al.OUTCOME_REFUSED if state.rate_rpm > true_limit else al.OUTCOME_SUCCESS
        lim.observe("sim", outcome, at=NOW)
    settled = lim.state_for("sim").rate_rpm
    assert settled <= true_limit, f"settled above the limit at {settled}"
    assert settled > true_limit * 0.5, f"settled far too conservatively at {settled}"


# ------------------------------------------------------------- pacing


def test_delay_reflects_the_inferred_rate():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    state = lim.state_for("kilo")
    expected = timedelta(seconds=60.0 / state.rate_rpm)
    assert lim.delay_before_next("kilo", now=NOW) == expected


def test_delay_decays_as_time_passes():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    assert lim.delay_before_next("kilo", now=NOW + timedelta(minutes=5)) == timedelta(0)
    assert lim.may_send("kilo", now=NOW + timedelta(minutes=5))


def test_limiter_reports_but_never_blocks():
    """Pacing means continuing work at a safe rate, not stopping."""
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    delay = lim.delay_before_next("kilo", now=NOW)
    assert isinstance(delay, timedelta) and delay >= timedelta(0)


# ------------------------------------------------------------- meter linkage


def test_no_reading_until_a_ceiling_has_been_observed():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    reading = lim.quota_reading("kilo", now=NOW)
    assert not reading.is_known(), "inventing a ceiling would be a guess"


def test_reading_is_estimated_never_live():
    """This is our inference, not a provider statement."""
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    reading = lim.quota_reading("kilo", now=NOW)
    assert reading.is_known()
    assert reading.confidence == qm.CONFIDENCE_ESTIMATED
    assert reading.source == qm.SOURCE_MODEL_SCAN


def test_a_live_provider_reading_overrides_the_inference():
    lim = al.AdaptiveLimiter()
    lim.observe("groq", al.OUTCOME_REFUSED, at=NOW)
    lim.observe("groq", al.OUTCOME_SUCCESS, at=NOW)
    inferred = lim.quota_reading("groq", now=NOW)
    live = qm.reading_from_headers(
        "groq",
        {"x-ratelimit-remaining-requests": "1", "x-ratelimit-limit-requests": "10"},
        now=NOW,
    )
    merged = qm.merge_readings([inferred, live])
    assert merged is not None and merged.remaining_fraction == 0.1


def test_inferred_reading_publishes_into_the_shared_contract():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    payload = qm.build_provider_quota(lim.quota_readings(now=NOW))
    assert "kilo" in payload
    assert 0.0 <= payload["kilo"]["remaining_fraction"] <= 1.0


def test_providers_without_evidence_are_omitted_from_the_payload():
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    assert qm.build_provider_quota(lim.quota_readings(now=NOW)) == {}


# ------------------------------------------------------------- persistence


def test_state_round_trips_through_disk(tmp_path):
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_REFUSED, at=NOW)
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    path = lim.save(tmp_path / "limits.json")
    restored = al.AdaptiveLimiter.load(path)
    assert restored.state_for("kilo").rate_rpm == lim.state_for("kilo").rate_rpm
    assert restored.state_for("kilo").worst_known_bad_rpm == lim.state_for("kilo").worst_known_bad_rpm


def test_corrupt_state_file_loads_empty_rather_than_raising(tmp_path):
    path = tmp_path / "limits.json"
    path.write_text("{not json", encoding="utf-8")
    assert al.AdaptiveLimiter.load(path).states == {}


def test_missing_state_file_loads_empty(tmp_path):
    assert al.AdaptiveLimiter.load(tmp_path / "absent.json").states == {}


def test_save_is_atomic(tmp_path):
    lim = al.AdaptiveLimiter()
    lim.observe("kilo", al.OUTCOME_SUCCESS, at=NOW)
    target = lim.save(tmp_path / "limits.json")
    assert json.loads(target.read_text())["providers"][0]["provider"] == "kilo"
    assert not list(tmp_path.glob("*.tmp"))


def test_observe_many_folds_a_sequence():
    lim = al.observe_many(
        al.AdaptiveLimiter(),
        [("kilo", al.OUTCOME_SUCCESS, NOW), ("kilo", al.OUTCOME_REFUSED, NOW)],
    )
    assert lim.state_for("kilo").successes == 1
    assert lim.state_for("kilo").refusals == 1
