from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

import quota_meter as qm
import spend_ledger as sl

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
EPOCH = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
WINDOW = qm.BUDGET_WINDOWS["opencode-go"][0]  # 12 USD / 5h


def ev(amount: float, at: datetime, provider: str = "opencode-go", unit: str = "usd") -> sl.SpendEvent:
    return sl.SpendEvent(provider=provider, amount=amount, unit=unit, at=at)


def test_record_and_read_round_trip(tmp_path):
    path = tmp_path / "spend.jsonl"
    sl.record_spend(ev(1.5, NOW), path)
    sl.record_spend(ev(2.5, NOW), path)
    events = list(sl.iter_events(path))
    assert [e.amount for e in events] == [1.5, 2.5]
    assert all(e.provider == "opencode-go" for e in events)


def test_negative_spend_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        sl.record_spend(ev(-1.0, NOW), tmp_path / "spend.jsonl")


def test_corrupt_and_truncated_lines_are_skipped_not_fatal(tmp_path):
    path = tmp_path / "spend.jsonl"
    sl.record_spend(ev(1.0, NOW), path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
        fh.write(json.dumps({"provider": "x"}) + "\n")  # no timestamp
        fh.write('{"provider":"opencode-go","amount":"abc","at":"2026-07-29T12:00:00Z"}\n')
        fh.write('{"provider":"opencode-go","amount":2.0,"at":"2026-07')  # truncated
    events = list(sl.iter_events(path))
    assert [e.amount for e in events] == [1.0]


def test_missing_file_yields_nothing(tmp_path):
    assert list(sl.iter_events(tmp_path / "absent.jsonl")) == []


# ------------------------------------------------------------- windowing


def test_window_start_is_a_fixed_boundary_not_a_trailing_average():
    start = sl.window_start(WINDOW, NOW, EPOCH)
    assert start == EPOCH  # 2h into a 5h window
    later = sl.window_start(WINDOW, EPOCH + timedelta(hours=5, minutes=1), EPOCH)
    assert later == EPOCH + timedelta(hours=5)


def test_spend_outside_the_current_window_is_excluded():
    events = [
        ev(5.0, EPOCH - timedelta(hours=1)),  # previous window
        ev(3.0, EPOCH + timedelta(minutes=30)),
        ev(1.0, NOW),
    ]
    spent, started = sl.spend_in_window(WINDOW, now=NOW, epoch=EPOCH, events=events)
    assert spent == 4.0
    assert started == EPOCH


def test_other_providers_are_not_counted():
    events = [ev(3.0, NOW), ev(9.0, NOW, provider="groq")]
    spent, _ = sl.spend_in_window(WINDOW, now=NOW, epoch=EPOCH, events=events)
    assert spent == 3.0


def test_mismatched_unit_is_ignored_rather_than_summed():
    """Adding requests to dollars would produce a confident wrong number."""
    events = [ev(2.0, NOW), ev(400.0, NOW, unit="requests")]
    spent, _ = sl.spend_in_window(WINDOW, now=NOW, epoch=EPOCH, events=events)
    assert spent == 2.0


# ------------------------------------------------------------- meter linkage


def test_measured_reading_replaces_the_seeded_estimate():
    events = [ev(3.0, NOW)]
    reading = sl.measured_reading(WINDOW, now=NOW, epoch=EPOCH, events=events)
    assert reading.remaining_fraction == 0.75
    assert reading.confidence == qm.CONFIDENCE_MEASURED
    assert reading.unit == "usd"


def test_no_spend_yet_stays_an_estimate_not_a_measurement():
    reading = sl.measured_reading(WINDOW, now=NOW, epoch=EPOCH, events=[])
    assert reading.remaining_fraction == 1.0
    assert reading.confidence == qm.CONFIDENCE_ESTIMATED


def test_measured_reading_feeds_the_published_contract():
    reading = sl.measured_reading(WINDOW, now=NOW, epoch=EPOCH, events=[ev(6.0, NOW)])
    payload = qm.build_provider_quota([reading])
    assert payload["opencode-go"]["remaining_fraction"] == 0.5
    assert payload["opencode-go"]["unit"] == "usd"


def test_measured_readings_covers_all_windows_in_one_pass(tmp_path):
    path = tmp_path / "spend.jsonl"
    sl.record_spend(ev(6.0, NOW), path)
    readings = sl.measured_readings(
        qm.BUDGET_WINDOWS["opencode-go"], now=NOW, epoch=EPOCH, path=path
    )
    assert len(readings) == 3
    by_label = {r.window_label: r.remaining_fraction for r in readings}
    assert by_label["5h"] == 0.5  # 6 of 12
    assert by_label["week"] == 0.8  # 6 of 30
    assert by_label["month"] == 0.9  # 6 of 60


def test_tightest_window_binds_when_merged():
    readings = sl.measured_readings(
        qm.BUDGET_WINDOWS["opencode-go"], now=NOW, epoch=EPOCH, events=None, path=None
    ) if False else [
        sl.measured_reading(w, now=NOW, epoch=EPOCH, events=[ev(6.0, NOW)])
        for w in qm.BUDGET_WINDOWS["opencode-go"]
    ]
    merged = qm.merge_readings(readings)
    assert merged is not None
    assert merged.remaining_fraction == 0.5, "the 5h window is the binding constraint"


# ------------------------------------------------------------- utilization


def test_utilization_flags_capacity_on_track_to_be_wasted(tmp_path):
    """The stated goal is using every quota; this reports when we will not."""
    path = tmp_path / "spend.jsonl"
    sl.record_spend(ev(0.5, EPOCH + timedelta(minutes=10)), path)
    stats = sl.utilization(WINDOW, now=NOW, epoch=EPOCH, path=path)
    assert stats["spent"] == 0.5
    assert stats["pace"] < 0, "spending slower than the clock"
    assert stats["projected_waste"] > 0.5, "most of the window will expire unused"


def test_utilization_reports_no_waste_when_on_pace(tmp_path):
    path = tmp_path / "spend.jsonl"
    # 2h into a 5h window, 12 USD budget: on pace means ~4.8 spent.
    sl.record_spend(ev(4.8, EPOCH + timedelta(minutes=5)), path)
    stats = sl.utilization(WINDOW, now=NOW, epoch=EPOCH, path=path)
    assert abs(stats["pace"]) < 0.05
    assert stats["projected_waste"] < 0.05


def test_utilization_handles_an_empty_ledger(tmp_path):
    stats = sl.utilization(WINDOW, now=NOW, epoch=EPOCH, path=tmp_path / "none.jsonl")
    assert stats["spent"] == 0.0
    assert stats["projected_waste"] == 1.0
    assert stats["resets_at"].endswith("Z")
