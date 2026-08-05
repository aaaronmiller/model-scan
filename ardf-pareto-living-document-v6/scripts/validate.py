# ---
# title: ARDF v6 Full-Universe Package Validator
# version: 6.0.0
# created: 2026-07-28
# model: GPT-5.6 Thinking
# reasoning_level: high
# purpose: Verify the one-CSV contract, complete graph geometry, calibration coverage, schemas, and offline package.
# ---
"""Validate the portable ARDF package before it is archived.

The most important tests are not cosmetic. They reproduce the default dashboard
aggregation from the canonical CSV and assert that the graph represents the
entire 669-configuration catalog rather than silently shrinking to the paired
or Pareto subset.
"""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data/unified-model-evidence.csv"

EXPECTED_SOURCE_COUNTS = {
    "livebench-2026-06-25": 45,
    "vals-index-v1-2-2026-07-23": 40,
    "vals-terminal-bench-2-1-2026-07-22": 45,
    "vals-vibe-code-v1-1-2026-07-23": 76,
    "vals-swe-bench-2026-07-22": 75,
    "aa-token-price-proxy-v6": 284,
    "standard-task-price-proxy-v6": 398,
}

EXPECTED_GEOMETRY = {
    "catalog": 669,
    "paired": 391,
    "unpriced": 238,
    "unscored": 40,
    "frontier": 20,
}

TARGETS = [
    "claude-fable-5-max",
    "claude-opus-5-max",
    "gpt-5-6-sol-max",
    "kimi-k3-max",
]


def number(value: Any) -> float | None:
    """Return a finite float or preserve the value as missing."""
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def check(condition: bool, label: str, detail: str = "") -> dict[str, str]:
    """Create one machine-readable validation result."""
    return {"status": "PASS" if condition else "FAIL", "check": label, "detail": detail}


def extract_inline_scripts(html: str) -> list[str]:
    """Extract inline scripts while ignoring external script tags."""
    return [
        match.group(1)
        for match in re.finditer(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.S | re.I)
        if match.group(1).strip()
    ]


def weighted_mean(values: list[tuple[float, float]]) -> float | None:
    """Mirror the dashboard's source-weighted arithmetic capability mean."""
    total = sum(value * weight for value, weight in values if weight > 0)
    weight_sum = sum(weight for _, weight in values if weight > 0)
    return total / weight_sum if weight_sum else None


def weighted_geometric_mean(values: list[tuple[float, float]]) -> float | None:
    """Mirror the dashboard's multiplicative cost aggregation."""
    valid = [(value, weight) for value, weight in values if value > 0 and weight > 0]
    if not valid:
        return None
    return math.exp(sum(math.log(value) * weight for value, weight in valid) / sum(weight for _, weight in valid))


def cost_priority(row: dict[str, str]) -> int:
    """Mirror the default best-evidence task-cost hierarchy in dashboard.html."""
    metric_name = row.get("metric_name", "")
    raw_unit = row.get("raw_unit", "").lower()
    source_id = row.get("source_id", "")
    if metric_name == "aa_cost_per_task_usd":
        return 5
    if source_id == "aa-token-price-proxy-v6":
        return 3
    if source_id == "standard-task-price-proxy-v6":
        return 2
    if (
        "per successful" in raw_unit
        or "per task" in raw_unit
        or "cost_per_success" in metric_name
        or "cost_per_task" in metric_name
    ):
        return 4
    return 1


def reproduce_default_geometry(rows: list[dict[str, str]]) -> dict[str, int]:
    """Rebuild the default all-source robust-affine configuration geometry.

    This test protects against the exact regression reported by the user: a
    future interface must not collapse hundreds of configurations into a tiny
    already-paired or frontier-only model list.
    """
    catalog = [row for row in rows if row.get("record_type") == "catalog"]
    groups: dict[str, dict[str, list[tuple[float, float, dict[str, str]]]]] = defaultdict(
        lambda: {"capability": [], "cost": []}
    )

    for row in rows:
        if row.get("record_type") != "observation" or row.get("use_in_aggregate") != "1":
            continue
        value = number(row.get("cal_robust_affine"))
        if value is None or row.get("metric_axis") not in {"capability", "cost"}:
            continue
        weight = number(row.get("base_weight")) or 1.0
        groups[row["model_key"]][row["metric_axis"]].append((value, weight, row))

    points: list[tuple[str, float | None, float | None]] = []
    for meta in catalog:
        group = groups[meta["model_key"]]
        capability = weighted_mean([(value, weight) for value, weight, _ in group["capability"]])

        costs = group["cost"]
        if costs:
            best_class = max(cost_priority(row) for _, _, row in costs)
            selected = [(value, weight) for value, weight, row in costs if cost_priority(row) == best_class]
            cost = weighted_geometric_mean(selected)
        else:
            cost = None
        points.append((meta["model_key"], capability, cost))

    paired = [point for point in points if point[1] is not None and point[2] is not None]
    unpriced = [point for point in points if point[1] is not None and point[2] is None]
    unscored = [point for point in points if point[1] is None]

    frontier_count = 0
    best_capability = -math.inf
    for _, capability, cost in sorted(paired, key=lambda point: (point[2], -point[1])):
        assert capability is not None and cost is not None
        if capability > best_capability + 1e-12:
            frontier_count += 1
            best_capability = capability

    return {
        "catalog": len(points),
        "paired": len(paired),
        "unpriced": len(unpriced),
        "unscored": len(unscored),
        "frontier": frontier_count,
    }


def main() -> int:
    """Run all validations, write Markdown evidence, and return nonzero on failure."""
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0]) if rows else []
    observations = [row for row in rows if row.get("record_type") == "observation"]
    catalog = [row for row in rows if row.get("record_type") == "catalog"]
    results: list[dict[str, str]] = []

    csv_files = list(ROOT.rglob("*.csv"))
    results.append(check(
        len(csv_files) == 1,
        "Exactly one CSV in package",
        ", ".join(str(path.relative_to(ROOT)) for path in csv_files),
    ))

    results.append(check(len(rows) == 2540, "Expected unified record count", str(len(rows))))
    results.append(check(len(observations) == 1871, "Expected atomic observation count", str(len(observations))))
    results.append(check(len(catalog) == 669, "Expected catalog row count", str(len(catalog))))
    results.append(check(
        Counter(row.get("metric_axis") for row in rows) == Counter({"capability": 974, "cost": 897, "catalog": 669}),
        "Expected capability/cost/catalog distribution",
        str(dict(Counter(row.get("metric_axis") for row in rows))),
    ))

    record_ids = [row.get("observation_id", "") for row in rows]
    results.append(check(
        all(record_ids) and len(record_ids) == len(set(record_ids)),
        "Unique stable record IDs",
        f"{len(set(record_ids))}/{len(record_ids)}",
    ))
    model_keys = [row.get("model_key", "") for row in catalog]
    results.append(check(
        all(model_keys) and len(model_keys) == len(set(model_keys)),
        "Unique catalog model/configuration keys",
        f"{len(set(model_keys))}/{len(model_keys)}",
    ))

    invalid_observations = [
        row.get("observation_id", "")
        for row in observations
        if row.get("metric_axis") not in {"capability", "cost"}
        or number(row.get("raw_value")) is None
        or not row.get("source_id")
        or not row.get("source_url")
    ]
    results.append(check(
        not invalid_observations,
        "Observation rows contain one valid sourced axis value",
        f"invalid={len(invalid_observations)}",
    ))

    invalid_catalog = [
        row.get("observation_id", "")
        for row in catalog
        if row.get("metric_axis") != "catalog" or row.get("raw_value") not in {"", None}
    ]
    results.append(check(
        not invalid_catalog,
        "Catalog rows remain metadata-only",
        f"invalid={len(invalid_catalog)}",
    ))

    for source_id, expected in EXPECTED_SOURCE_COUNTS.items():
        actual = sum(row.get("source_id") == source_id for row in observations)
        results.append(check(actual == expected, f"Complete source slice: {source_id}", f"{actual}/{expected}"))

    for field in ["cal_robust_affine", "cal_huber_affine", "cal_monotone_piecewise", "calibrated_score"]:
        results.append(check(field in fields, f"Calibration field exists: {field}"))
        populated = sum(number(row.get(field)) is not None for row in observations)
        results.append(check(populated == 1771, f"Calibration field populated: {field}", str(populated)))

    config = json.loads((ROOT / "config/calibration-algorithms.json").read_text(encoding="utf-8"))
    results.append(check(
        config.get("reference_scales", {}).get("cost", {}).get("metric_name") == "aa_cost_per_task_usd",
        "Task-level USD is the configured cost reference",
        str(config.get("reference_scales", {}).get("cost", {})),
    ))
    results.append(check(len(config.get("algorithms", [])) >= 3, "At least three configurable algorithms", str(len(config.get("algorithms", [])))))
    results.append(check(
        bool(config.get("task_cost_estimator", {}).get("enabled")),
        "Standardized task-price estimator is configured",
    ))
    results.append(check(
        bool(config.get("token_price_proxy", {}).get("enabled")),
        "Model-specific token-count × price proxy is configured",
    ))

    report_data = json.loads((ROOT / "generated/calibration-report.json").read_text(encoding="utf-8"))
    reports = report_data.get("reports", [])
    results.append(check(
        all(report.get("status") in {"identity", "calibrated", "insufficient-anchors"} for report in reports),
        "Calibration reports have explicit status",
        str(len(reports)),
    ))

    for source_id in [key for key in EXPECTED_SOURCE_COUNTS if key.startswith(("livebench", "vals-"))]:
        source_rows = [row for row in observations if row.get("source_id") == source_id]
        anchors = {int(float(row["cal_robust_affine_anchor_count"])) for row in source_rows if row.get("cal_robust_affine_anchor_count")}
        results.append(check(
            len(anchors) == 1 and next(iter(anchors)) >= 20,
            f"Multipoint anchors for {source_id}",
            str(sorted(anchors)),
        ))

    generated_anchor_expectations = {"aa-token-price-proxy-v6": 7, "standard-task-price-proxy-v6": 11}
    for source_id, expected in generated_anchor_expectations.items():
        source_rows = [row for row in observations if row.get("source_id") == source_id]
        anchors = {int(float(row["cal_robust_affine_anchor_count"])) for row in source_rows if row.get("cal_robust_affine_anchor_count")}
        results.append(check(
            anchors == {expected},
            f"Strict anchors for generated cost source: {source_id}",
            str(sorted(anchors)),
        ))

    for model_key in TARGETS:
        model_rows = [row for row in observations if row.get("model_key") == model_key]
        capability_count = sum(
            row.get("metric_axis") == "capability" and number(row.get("cal_robust_affine")) is not None
            for row in model_rows
        )
        cost_count = sum(
            row.get("metric_axis") == "cost" and number(row.get("cal_robust_affine")) is not None
            for row in model_rows
        )
        results.append(check(
            capability_count >= 5,
            f"Thin frontier target capability coverage: {model_key}",
            f"capability={capability_count}, cost={cost_count}",
        ))
        results.append(check(
            cost_count >= 1,
            f"Thin frontier target cost coverage: {model_key}",
            f"capability={capability_count}, cost={cost_count}",
        ))

    geometry = reproduce_default_geometry(rows)
    for key, expected in EXPECTED_GEOMETRY.items():
        results.append(check(
            geometry[key] == expected,
            f"Default full-universe geometry: {key}",
            f"{geometry[key]}/{expected}",
        ))
    results.append(check(
        geometry["paired"] + geometry["unpriced"] + geometry["unscored"] == geometry["catalog"],
        "Every catalog configuration is represented by graph or shelf",
        str(geometry),
    ))

    required_dashboard_tokens = {
        "All model names": "labels visible by default",
        "Capability evidence cloud": "atomic evidence-cloud mode",
        "UNPRICED CONFIGURATIONS": "unpriced shelf",
        "UNSCORED / NO SELECTED CAPABILITY EVIDENCE": "unscored shelf",
        "Logarithmic price": "logarithmic X-axis control",
        "Linear price": "linear X-axis control",
        'id="releaseAfter"': "release-date filter",
        'id="evidenceAfter"': "evidence-date filter",
        'id="capSources"': "independent capability-source filters",
        'id="costSources"': "independent cost-source filters",
        'href="calibration-studio.html"': "calibration-studio popout link",
        'value="3400" selected': "wall-map canvas default",
    }

    for html_name in ["dashboard.html", "dashboard-claude-code.html", "calibration-studio.html"]:
        path = ROOT / html_name
        results.append(check(path.exists(), f"HTML exists: {html_name}"))
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        results.append(check(
            "https://cdn." not in text and "unpkg.com" not in text and "jsdelivr.net" not in text,
            f"Offline dependency check: {html_name}",
        ))
        linked_assets = ["generated/dashboard-data.js"]
        if html_name == "calibration-studio.html":
            linked_assets.append("generated/unified-evidence-csv.js")
        for linked in linked_assets:
            results.append(check((ROOT / linked).exists(), f"Linked generated asset exists: {html_name} → {linked}"))

        for index, script in enumerate(extract_inline_scripts(text), 1):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
                handle.write(script)
                js_path = Path(handle.name)
            process = subprocess.run(["node", "--check", str(js_path)], capture_output=True, text=True)
            js_path.unlink(missing_ok=True)
            results.append(check(
                process.returncode == 0,
                f"JavaScript syntax: {html_name} script {index}",
                process.stderr.strip(),
            ))

        if html_name in {"dashboard.html", "dashboard-claude-code.html"}:
            for token, purpose in required_dashboard_tokens.items():
                results.append(check(token in text, f"Dashboard feature: {purpose} ({html_name})"))
        else:
            for token, purpose in {
                "Standardized task-price estimator": "editable token-price estimator",
                "Rebuild task-price proxy rows + recalibrate": "browser estimator rebuild",
                "Add algorithm": "dynamic algorithm creation",
                "Multipoint anchors": "anchor editor",
            }.items():
                results.append(check(token in text, f"Calibration Studio feature: {purpose}"))

    # Parse both schemas and check that the current dashboard config satisfies the
    # high-level contract without requiring an external jsonschema dependency.
    view_config = json.loads((ROOT / "config/dashboard-views.json").read_text(encoding="utf-8"))
    for schema_name in ["schema/unified-model-evidence.schema.json", "schema/dashboard-view.schema.json"]:
        try:
            parsed_schema = json.loads((ROOT / schema_name).read_text(encoding="utf-8"))
            results.append(check(bool(parsed_schema.get("$schema")), f"Valid JSON schema document: {schema_name}"))
        except Exception as error:  # pragma: no cover - included for report clarity.
            results.append(check(False, f"Valid JSON schema document: {schema_name}", str(error)))
    results.append(check(
        bool(view_config.get("views")) and bool(view_config.get("filters")) and bool(view_config.get("tables")),
        "Dashboard contract defines graphs, filters, and tables",
    ))

    required_files = [
        "README.md",
        "docs/methodology.md",
        "docs/new-source-notes.md",
        "schema/unified-model-evidence.schema.json",
        "schema/dashboard-view.schema.json",
        "scripts/augment_cost.py",
        "scripts/calibrate.py",
        "scripts/rebuild.py",
        "scripts/validate.py",
        "config/calibration-algorithms.json",
        "config/dashboard-views.json",
        "sources/attached-source-snapshots.json",
        "sources/new-benchmark-snapshots.json",
    ]
    for file_name in required_files:
        results.append(check((ROOT / file_name).exists(), f"Required package element: {file_name}"))

    failures = [result for result in results if result["status"] == "FAIL"]
    lines = [
        "<!--",
        "---",
        "title: ARDF v6 Validation Report",
        "version: 6.0.0",
        "created: 2026-07-28",
        "model: GPT-5.6 Thinking",
        "reasoning_level: high",
        "---",
        "-->",
        "",
        "# ARDF v6 validation report",
        "",
        f'**Result:** {"PASS" if not failures else "FAIL"}  ',
        f"**Checks:** {len(results)}  ",
        f"**Failures:** {len(failures)}  ",
        "",
        "## Default full-universe geometry",
        "",
        f"- Catalog configurations: {geometry['catalog']}",
        f"- Paired scatter points: {geometry['paired']}",
        f"- Unpriced shelf entries: {geometry['unpriced']}",
        f"- Unscored shelf entries: {geometry['unscored']}",
        f"- Empirical Pareto points: {geometry['frontier']}",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]
    for result in results:
        detail = result["detail"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {result['status']} | {result['check'].replace('|', '/')} | {detail} |")
    (ROOT / "docs/validation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS" if not failures else "FAIL",
        "checks": len(results),
        "geometry": geometry,
        "failures": failures,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
