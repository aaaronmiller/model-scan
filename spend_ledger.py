"""Local spend accounting, so budget windows report measured remaining capacity.

``quota_meter.reading_from_budget`` needs to know how much of a window has been
consumed. Without a spend feed it can only seed a published estimate, which is
why seeded readings carry ``confidence=estimated``.

This module is that feed. It records what we spent, from our own observation of
our own requests, and rolls it up per window. That is a measured fact about our
usage, distinct from a provider assertion about our remaining balance. When a
provider does report a balance, the meter's precedence rules prefer it.

Deliberately excluded, per the quota adjudication: token-count estimates of the
ccusage kind are telemetry, never authoritative quota, because that source
documents severe undercount. Nothing here infers spend from token counts. A
caller records the cost it actually incurred, or records nothing.

Append-only JSONL so a crash mid-write loses at most one line. No network access.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import quota_meter as qm
from quota_meter import CONFIG_DIR, BudgetWindow, QuotaReading, reading_from_budget

SPEND_LOG_PATH = CONFIG_DIR / "spend_log.jsonl"

# Retain a bounded tail when reading. The longest window in use is monthly, so
# a generous cap still covers every window while keeping reads cheap on a
# machine with limited memory.
MAX_ROWS_SCANNED = 50_000


@dataclass(frozen=True)
class SpendEvent:
    """One recorded cost, in the unit the provider meters against."""

    provider: str
    amount: float
    unit: str
    at: datetime
    model: str = ""
    slot_id: str = ""
    request_id: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "provider": self.provider.lower(),
            "amount": float(self.amount),
            "unit": self.unit,
            "at": self.at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "model": self.model,
            "slot_id": self.slot_id,
            "request_id": self.request_id,
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def record_spend(
    event: SpendEvent,
    path: str | os.PathLike[str] | None = None,
) -> Path:
    """Append one spend event. Rejects negative amounts rather than storing them."""

    if event.amount < 0:
        raise ValueError("spend amount must not be negative")
    target = Path(path).expanduser() if path else SPEND_LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_row(), sort_keys=True) + "\n")
    return target


def iter_events(path: str | os.PathLike[str] | None = None) -> Iterator[SpendEvent]:
    """Yield well-formed events, skipping corrupt lines rather than failing.

    A truncated final line is expected after a crash and must not make the whole
    ledger unreadable.
    """

    target = Path(path).expanduser() if path else SPEND_LOG_PATH
    if not target.exists():
        return
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines[-MAX_ROWS_SCANNED:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping):
            continue
        at = _parse_at(row.get("at"))
        amount = row.get("amount")
        provider = row.get("provider")
        if at is None or not isinstance(provider, str) or not provider:
            continue
        try:
            amount_value = float(amount)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if amount_value != amount_value or amount_value < 0:
            continue
        yield SpendEvent(
            provider=provider.lower(),
            amount=amount_value,
            unit=str(row.get("unit") or ""),
            at=at,
            model=str(row.get("model") or ""),
            slot_id=str(row.get("slot_id") or ""),
            request_id=str(row.get("request_id") or ""),
        )


def window_start(window: BudgetWindow, now: datetime, epoch: datetime | None = None) -> datetime:
    """The start of the window currently in progress.

    Windows are treated as fixed periods anchored to ``epoch`` rather than as a
    trailing average, because providers reset on a boundary. Without a known
    provider boundary the anchor is the caller's ``epoch``, and any error is a
    constant offset rather than a drift.
    """

    anchor = epoch or datetime(1970, 1, 1, tzinfo=timezone.utc)
    period = window.period.total_seconds()
    if period <= 0:
        return anchor
    elapsed = (now - anchor).total_seconds()
    completed = int(elapsed // period)
    return anchor + timedelta(seconds=completed * period)


def spend_in_window(
    window: BudgetWindow,
    *,
    now: datetime | None = None,
    epoch: datetime | None = None,
    events: Iterable[SpendEvent] | None = None,
    path: str | os.PathLike[str] | None = None,
) -> tuple[float, datetime]:
    """Total spend for a provider inside its current window.

    Returns ``(spent, window_started_at)``. Events in a different unit are
    ignored rather than summed, since adding dollars to requests would produce a
    confident wrong number.
    """

    now = now or _utcnow()
    started = window_start(window, now, epoch)
    source = events if events is not None else iter_events(path)
    total = 0.0
    for event in source:
        if event.provider != window.provider.lower():
            continue
        if window.unit and event.unit and event.unit != window.unit:
            continue
        if started <= event.at <= now:
            total += event.amount
    return total, started


def total_spend(
    provider: str,
    *,
    unit: str = "usd",
    events: Iterable[SpendEvent] | None = None,
    path: str | os.PathLike[str] | None = None,
) -> float:
    """Lifetime spend for a provider, ignoring window boundaries.

    Required for pre-paid balances, which never reset. Using the windowed figure
    here would report a depleted balance as full again on every window rollover.
    """

    source = events if events is not None else iter_events(path)
    target = provider.lower()
    return sum(
        e.amount for e in source
        if e.provider == target and (not unit or not e.unit or e.unit == unit)
    )


def credit_reading(
    balance: "qm.CreditBalance",
    *,
    now: datetime | None = None,
    events: Iterable[SpendEvent] | None = None,
    path: str | os.PathLike[str] | None = None,
) -> QuotaReading:
    """Pre-paid balance reading backed by lifetime recorded spend."""

    spent = total_spend(balance.provider, unit=balance.unit, events=events, path=path)
    return qm.reading_from_credit_balance(balance, spent, now=now or _utcnow())


def measured_reading(
    window: BudgetWindow,
    *,
    now: datetime | None = None,
    epoch: datetime | None = None,
    events: Iterable[SpendEvent] | None = None,
    path: str | os.PathLike[str] | None = None,
) -> QuotaReading:
    """Produce a budget reading backed by recorded spend rather than an estimate."""

    now = now or _utcnow()
    spent, started = spend_in_window(window, now=now, epoch=epoch, events=events, path=path)
    return reading_from_budget(window, spent=spent, window_started_at=started, now=now)


def measured_readings(
    windows: Iterable[BudgetWindow],
    *,
    now: datetime | None = None,
    epoch: datetime | None = None,
    path: str | os.PathLike[str] | None = None,
) -> list[QuotaReading]:
    """Readings for several windows from a single pass over the ledger."""

    now = now or _utcnow()
    events = list(iter_events(path))
    return [
        measured_reading(window, now=now, epoch=epoch, events=events)
        for window in windows
    ]


def utilization(
    window: BudgetWindow,
    *,
    now: datetime | None = None,
    epoch: datetime | None = None,
    path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """How fully a window is being used, and whether it is on pace to be wasted.

    Reports what the stated goal of using every quota actually needs: not just
    what is left, but whether the current burn rate will leave capacity unused
    at reset. ``projected_waste`` is the fraction expected to expire unused if
    the present rate holds.
    """

    now = now or _utcnow()
    spent, started = spend_in_window(window, now=now, epoch=epoch, path=path)
    elapsed = max((now - started).total_seconds(), 0.0)
    period = window.period.total_seconds()
    remaining_time = max(period - elapsed, 0.0)

    used_fraction = min(spent / window.budget, 1.0) if window.budget > 0 else 0.0
    time_fraction = min(elapsed / period, 1.0) if period > 0 else 0.0

    rate = spent / elapsed if elapsed > 0 else 0.0
    projected_total = spent + rate * remaining_time
    projected_waste = 0.0
    if window.budget > 0:
        projected_waste = max(0.0, (window.budget - projected_total) / window.budget)

    return {
        "provider": window.provider,
        "window": window.label,
        "unit": window.unit,
        "budget": window.budget,
        "spent": round(spent, 6),
        "used_fraction": round(used_fraction, 6),
        "time_fraction": round(time_fraction, 6),
        # Positive means burning faster than the clock, negative means capacity
        # is on track to be left on the table.
        "pace": round(used_fraction - time_fraction, 6),
        "projected_waste": round(projected_waste, 6),
        "window_started_at": started.isoformat().replace("+00:00", "Z"),
        "resets_at": (started + window.period).isoformat().replace("+00:00", "Z"),
    }
