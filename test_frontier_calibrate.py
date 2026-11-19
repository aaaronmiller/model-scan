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


HOSTILE = "</script><img src=x onerror=alert(1)>"


def test_dashboard_embed_keeps_hostile_model_name_inside_the_script(tmp_path, monkeypatch):
    (tmp_path / "dashboard-template.html").write_text(
        "<html><body><!-- ARDF_DATA_BEGIN --><!-- ARDF_DATA_END --><p>after</p></body></html>",
        encoding="utf-8")
    out = tmp_path / "dashboard.html"
    monkeypatch.setattr(calibrate, "ROOT", tmp_path)
    monkeypatch.setattr(calibrate, "DASHBOARD_PATH", out)
    payload = {"models": [{"name": HOSTILE, "note": "a b & <!-- c"}]}
    calibrate.embed_dashboard(payload, {"frontier": [{"name": HOSTILE}]})
    text = out.read_text(encoding="utf-8")
    # one script element, closed only by its own tag; the hostile text appears only escaped
    assert text.count("<script") == 1 and text.count("</script") == 1
    assert "<img" not in text and " " not in text
    assert text.index("</script>") > text.index("onerror")
    values = calibrate.embedded_dashboard_values(text)
    assert values["ARDF_DATA"]["models"][0]["name"] == HOSTILE
    assert values["ARDF_DATA"]["models"][0]["note"] == "a b & <!-- c"
    assert values["ARDF_ANALYSIS"]["frontier"][0]["name"] == HOSTILE
    assert calibrate._validate_embedded_dashboard(out)
