"""Adaptive rate limiting inferred from refusals, with no advance knowledge of limits.

Recovered user directive, 2026-07-05: "Implement adaptive rate limiting that
adjusts timing based on server refusal codes without needing to know limits in
advance." Supporting constraints, 2026-06-29: "Watch requests per minute to
avoid rate limiting while continuing work" and "Take note of API rate limits per
minute."

This closes the Tier 2 gap. Budget-denominated providers publish a ceiling, so
remaining capacity is computable. Rate-limited free providers publish nothing,
so the only evidence is how they respond. This module turns that response
history into a pace and a capacity signal.

The control law is additive-increase, multiplicative-decrease, the same shape
that makes TCP congestion control stable without knowing link capacity:

- every success nudges the allowed rate up by a small constant;
- every refusal cuts it by a constant factor.

AIMD converges toward the true limit from below and backs off fast when it
overshoots, which is the desired behaviour when overshooting means a 429.

Two properties matter for this codebase specifically:

- The derived signal is an **estimate** and is labelled as such. It never
  claims to be a provider assertion, per the rule that estimates must not be
  presented as provider truth.
- "Watch requests per minute while continuing work" means pacing, not stopping.
  The limiter reports a delay; it never blocks, sleeps, or cancels.

No network access, no sleeping. Pure state transitions over observed outcomes.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from quota_meter import (
    CONFIDENCE_ESTIMATED,
    CONFIG_DIR,
    SOURCE_MODEL_SCAN,
    QuotaReading,
)

LIMITER_STATE_PATH = CONFIG_DIR / "adaptive_limits.json"

# Control constants. Increase is additive and slow; decrease is multiplicative
# and fast, because the cost of overshooting is a refusal.
RATE_INCREASE_PER_SUCCESS = 0.5  # requests per minute
RATE_DECREASE_FACTOR = 0.5
MIN_RATE_RPM = 0.5
DEFAULT_START_RPM = 10.0
MAX_RATE_RPM = 6_000.0

# Outcomes a caller can report.
OUTCOME_SUCCESS = "success"
OUTCOME_REFUSED = "refused"  # 429 or explicit rate-limit rejection
OUTCOME_ERROR = "error"  # transport or server error, not a rate signal

# Status codes that mean "you are going too fast", as opposed to a plain failure.
REFUSAL_STATUS = frozenset({429, 503})


@dataclass
class LimiterState:
    """Inferred pacing state for one provider."""

    provider: str
    rate_rpm: float = DEFAULT_START_RPM
    successes: int = 0
    refusals: int = 0
    consecutive_refusals: int = 0
    last_outcome_at: datetime | None = None
    last_refusal_at: datetime | None = None
    # Highest rate seen to succeed, and lowest rate seen to be refused. Together
    # they bracket the true limit without ever being told what it is.
    best_known_good_rpm: float = 0.0
    worst_known_bad_rpm: float | None = None

    def min_interval(self) -> timedelta:
        """Minimum spacing between requests implied by the current rate."""

        rate = max(self.rate_rpm, MIN_RATE_RPM)
        return timedelta(seconds=60.0 / rate)

    def to_row(self) -> dict[str, Any]:
        def iso(value: datetime | None) -> str | None:
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None

        return {
            "provider": self.provider,
            "rate_rpm": round(self.rate_rpm, 4),
            "successes": self.successes,
            "refusals": self.refusals,
            "consecutive_refusals": self.consecutive_refusals,
            "last_outcome_at": iso(self.last_outcome_at),
            "last_refusal_at": iso(self.last_refusal_at),
            "best_known_good_rpm": round(self.best_known_good_rpm, 4),
            "worst_known_bad_rpm": (
                round(self.worst_known_bad_rpm, 4) if self.worst_known_bad_rpm is not None else None
            ),
        }

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "LimiterState | None":
        provider = row.get("provider")
        if not isinstance(provider, str) or not provider:
            return None

        def parse(value: Any) -> datetime | None:
            if not isinstance(value, str) or not value:
                return None
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

        def number(value: Any, fallback: float) -> float:
            try:
                result = float(value)
            except (TypeError, ValueError):
                return fallback
            return result if result == result else fallback

        worst = row.get("worst_known_bad_rpm")
        return cls(
            provider=provider.lower(),
            rate_rpm=max(MIN_RATE_RPM, number(row.get("rate_rpm"), DEFAULT_START_RPM)),
            successes=int(number(row.get("successes"), 0)),
            refusals=int(number(row.get("refusals"), 0)),
            consecutive_refusals=int(number(row.get("consecutive_refusals"), 0)),
            last_outcome_at=parse(row.get("last_outcome_at")),
            last_refusal_at=parse(row.get("last_refusal_at")),
            best_known_good_rpm=number(row.get("best_known_good_rpm"), 0.0),
            worst_known_bad_rpm=None if worst is None else number(worst, 0.0),
        )


@dataclass
class AdaptiveLimiter:
    """Per-provider AIMD pacing inferred purely from observed outcomes."""

    states: dict[str, LimiterState] = field(default_factory=dict)

    def state_for(self, provider: str) -> LimiterState:
        key = str(provider or "").strip().lower()
        if key not in self.states:
            self.states[key] = LimiterState(provider=key)
        return self.states[key]

    def observe(
        self,
        provider: str,
        outcome: str,
        *,
        at: datetime | None = None,
        status_code: int | None = None,
    ) -> LimiterState:
        """Fold one observed outcome into the provider's pacing estimate.

        A transport error is deliberately **not** treated as a rate signal.
        Slowing down because a connection dropped would conflate unavailability
        with throttling and would degrade the pace for the wrong reason.
        """

        state = self.state_for(provider)
        at = at or datetime.now(timezone.utc)

        if status_code is not None and status_code in REFUSAL_STATUS:
            outcome = OUTCOME_REFUSED

        if outcome == OUTCOME_REFUSED:
            state.refusals += 1
            state.consecutive_refusals += 1
            state.last_refusal_at = at
            # Record the bracket before cutting, so the estimate keeps the
            # tightest observed upper bound rather than the most recent one.
            if state.worst_known_bad_rpm is None or state.rate_rpm < state.worst_known_bad_rpm:
                state.worst_known_bad_rpm = state.rate_rpm
            # Repeated refusals compound the cut, since one halving was clearly
            # not enough.
            factor = RATE_DECREASE_FACTOR ** min(state.consecutive_refusals, 4)
            state.rate_rpm = max(MIN_RATE_RPM, state.rate_rpm * factor)
        elif outcome == OUTCOME_SUCCESS:
            state.successes += 1
            state.consecutive_refusals = 0
            state.best_known_good_rpm = max(state.best_known_good_rpm, state.rate_rpm)
            proposed = state.rate_rpm + RATE_INCREASE_PER_SUCCESS
            # Do not climb back above a rate already known to be refused; stop
            # just below it. Without this the limiter oscillates across the
            # limit forever instead of settling under it.
            if state.worst_known_bad_rpm is not None:
                proposed = min(proposed, state.worst_known_bad_rpm * 0.95)
            state.rate_rpm = max(MIN_RATE_RPM, min(proposed, MAX_RATE_RPM))

        state.last_outcome_at = at
        return state

    def delay_before_next(self, provider: str, *, now: datetime | None = None) -> timedelta:
        """How long to wait before the next request. Never sleeps; only reports."""

        state = self.state_for(provider)
        now = now or datetime.now(timezone.utc)
        if state.last_outcome_at is None:
            return timedelta(0)
        elapsed = now - state.last_outcome_at
        remaining = state.min_interval() - elapsed
        return remaining if remaining > timedelta(0) else timedelta(0)

    def may_send(self, provider: str, *, now: datetime | None = None) -> bool:
        return self.delay_before_next(provider, now=now) == timedelta(0)

    def headroom_fraction(self, provider: str) -> float | None:
        """Estimated remaining headroom as a 0-to-1 fraction, or ``None``.

        Derived from the bracket between the best rate known to work and the
        worst known to be refused. Returns ``None`` until a refusal has actually
        been observed, because before that there is no evidence of any ceiling
        and inventing one would be a guess.
        """

        state = self.state_for(provider)
        if state.worst_known_bad_rpm is None or state.worst_known_bad_rpm <= 0:
            return None
        ratio = state.rate_rpm / state.worst_known_bad_rpm
        return max(0.0, min(1.0, ratio))

    def quota_reading(self, provider: str, *, now: datetime | None = None) -> QuotaReading:
        """Express the inferred headroom as a meter reading.

        Always ``estimated`` and sourced to model-scan, never ``live``, because
        this is our inference rather than a provider statement. The meter's
        precedence rules then let any real provider figure override it.
        """

        now = now or datetime.now(timezone.utc)
        state = self.state_for(provider)
        fraction = self.headroom_fraction(provider)
        if fraction is None:
            return QuotaReading(
                provider=state.provider,
                remaining_fraction=None,
                confidence="unknown",
                source=SOURCE_MODEL_SCAN,
                observed_at=now,
                provenance="adaptive-limiter:no-refusal-observed",
            )
        return QuotaReading(
            provider=state.provider,
            remaining_fraction=fraction,
            confidence=CONFIDENCE_ESTIMATED,
            source=SOURCE_MODEL_SCAN,
            observed_at=now,
            unit="requests-per-minute",
            provenance=f"adaptive-limiter:aimd rate={state.rate_rpm:.2f}rpm",
        )

    def quota_readings(self, *, now: datetime | None = None) -> list[QuotaReading]:
        return [self.quota_reading(p, now=now) for p in sorted(self.states)]

    # ---------------------------------------------------------------- storage

    def save(self, path: str | os.PathLike[str] | None = None) -> Path:
        target = Path(path).expanduser() if path else LIMITER_STATE_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"providers": [s.to_row() for s in sorted(self.states.values(), key=lambda s: s.provider)]}
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(target)
        return target

    @classmethod
    def load(cls, path: str | os.PathLike[str] | None = None) -> "AdaptiveLimiter":
        target = Path(path).expanduser() if path else LIMITER_STATE_PATH
        limiter = cls()
        if not target.exists():
            return limiter
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return limiter
        rows = payload.get("providers") if isinstance(payload, Mapping) else None
        for row in rows or []:
            if isinstance(row, Mapping):
                state = LimiterState.from_row(row)
                if state is not None:
                    limiter.states[state.provider] = state
        return limiter


def observe_many(
    limiter: AdaptiveLimiter, events: Iterable[tuple[str, str, datetime | None]]
) -> AdaptiveLimiter:
    """Fold a sequence of ``(provider, outcome, at)`` observations."""

    for provider, outcome, at in events:
        limiter.observe(provider, outcome, at=at)
    return limiter
