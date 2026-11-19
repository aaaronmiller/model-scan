"""Unit tests for frontier/calibrate.py helpers (ARDF, folded into model-scan 2026-11-19)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "frontier_calibrate", Path(__file__).resolve().parent / "frontier" / "calibrate.py")
calibrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calibrate)


def test_weighted_median_odd_and_unequal_weights():
    assert calibrate.weighted_median([(1, 1), (2, 1), (3, 1)]) == 2
    assert calibrate.weighted_median([(1, 5), (2, 1), (3, 1)]) == 1


def test_weighted_median_exact_tie_is_midpoint():
    # cumulative weight reaches exactly half at 2: the median lies between 2 and 4
    assert calibrate.weighted_median([(2, 1), (4, 1)]) == 3
    assert calibrate.weighted_median([(1, 1), (2, 1), (4, 1), (9, 1)]) == 3
    assert calibrate.weighted_median([(1, 0.5), (3, 0.25), (5, 0.25)]) == 2


def test_weighted_median_skips_zero_weight_neighbour_and_falls_back():
    assert calibrate.weighted_median([(1, 1), (2, 0), (5, 1)]) == 3
    assert calibrate.weighted_median([(1, 0), (3, 0)]) == 2
