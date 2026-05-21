"""
Calibration functions — normalize raw data to 0-100 scales.
"""
from __future__ import annotations


def calibrate_aa_index(raw: float | None, aa_max: float = 60.0) -> float:
    """Calibrate AA Intelligence Index: top model (60) = 100. Linear scale with more spread."""
    if raw is None:
        return 30.0  # neutral default — conservative
    # Shift down to create more headroom for modifiers
    return min(100, max(0, (raw / aa_max * 100) - 10))


def calibrate_tps(tps: float | None, reference: float = 60.0) -> float:
    """Calibrate tokens/sec: 60 tps = 50 pts, logarithmic scaling."""
    if tps is None or tps <= 0:
        return 0.0
    import math
    return min(100, max(0, 50 * math.log2(1 + tps / reference)))


def calibrate_latency(seconds: float | None) -> float:
    """Calibrate latency: 0.1s = 80, 1s = 40, 5s = 0."""
    if seconds is None or seconds <= 0:
        return 50.0
    import math
    return max(0, 80 - math.log1p(seconds) * 30)


def calibrate_bfcl(overall: float | None) -> float:
    """Calibrate BFCL score: 92.5 = 100 (GPT-5.4), linear scale from 0."""
    if overall is None:
        return 50.0
    return min(100, max(0, overall / 92.5 * 100))


def calibrate_arena_elo(elo: float | None, max_elo: float = 1482.0) -> float:
    """Calibrate Arena ELO: 1482 = 100 (GPT-5.4)."""
    if elo is None:
        return 50.0
    return min(100, max(0, elo / max_elo * 100))


def calibrate_swe_verified(score: float | None) -> float:
    """Calibrate SWE-bench Verified: 80% = 100."""
    if score is None:
        return 50.0
    return min(100, max(0, score / 80.0 * 100))
