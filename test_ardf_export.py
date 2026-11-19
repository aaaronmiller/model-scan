"""ARDF export and field-migration gates for MS-003."""

import copy
from pathlib import Path

import pytest

from ardf_export import ArdfExportRejected, build_export, validate_export

# ARDF was folded into model-scan as frontier/ on 2026-11-19.
ARDF_ROOT = Path(__file__).resolve().parent / "frontier"


def test_live_ardf_builds_a_bound_export_and_complete_field_map():
    export = build_export(ARDF_ROOT, generated_at="2026-08-15T22:00:00Z")
    assert validate_export(ARDF_ROOT, export) == 8
    # Tracks schemas/unified_observations.schema.json x-row-count, which is a
    # deliberate gate: the export refuses to build when the ledger disagrees
    # with the pin. Moved 2839 -> 5148 on 2026-08-20 when the authorized AA v2
    # refresh appended 2309 observations; moved 5148 -> 5180 on 2026-08-29 when
    # the authorized 2026-08-25 AA refresh (+32 rows) was re-pinned; moved
    # 5180 -> 7775 on 2026-11-19 when ARDF v7.5.0 (AA snapshot 2026-11-10) was
    # folded in as frontier/, whose ledger had grown without a re-pin here.
    # Update both together, never one.
    assert export["row_count"] == 7775
    assert export["field_count"] == len(export["field_migration"])
    assert len(export["files"]) == 11
    assert export["policy_disposition"]["global_executor_capability_floor"] == "none"
    assert not [item for item in export["field_migration"] if item["mode"] == "unsupported"]
    # docs/origin-prompt-v6.md was the August example; ARDF v7.5.0 staged it
    # out, so a supporting file that still exists stands in for it.
    assert "ERRATA-and-findings.md" in export["excluded_supporting_files"]


def test_export_detects_any_bound_input_change():
    export = build_export(ARDF_ROOT, generated_at="2026-08-15T22:00:00Z")
    changed = copy.deepcopy(export)
    changed["row_count"] -= 1
    with pytest.raises(ArdfExportRejected, match="does not match"):
        validate_export(ARDF_ROOT, changed)


def test_export_contains_relative_paths_only():
    export = build_export(ARDF_ROOT, generated_at="2026-08-15T22:00:00Z")
    assert all(not item["path"].startswith("/") for item in export["files"])
    assert all(not item.startswith("/") for item in export["excluded_supporting_files"])
