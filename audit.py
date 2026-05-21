"""
model-scan — Independent Audit System

Compares model-scan recommendations against verified benchmarks to detect:
  - Classification accuracy: do tier assignments match benchmark performance?
  - False positives: recommended models with poor verified scores
  - False negatives: high-scoring models missed by slot gates/weights
  - Provider/systematic bias: over/under-rating particular providers
  - Tier/score drift: degradation across scan history

Audit produces a structured report with quantified findings and evidence.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
BENCHMARKS_PATH = CONFIG_DIR / "benchmarks.json"
OUTPUT_DIR = CONFIG_DIR / "audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tier thresholds (must match dink.py)
TIER_THRESHOLDS = {
    "S": (85, 100),
    "A": (70, 85),
    "B": (50, 70),
    "C": (0, 50),
}

# Benchmark quality thresholds
BENCHMARK_QUALITY = {
    "SWE-bench Verified": {"S": 70, "A": 50, "B": 30, "C": 0},
    "SWE-bench Pro": {"S": 50, "A": 35, "B": 20, "C": 0},
    "Terminal-Bench": {"S": 65, "A": 45, "B": 25, "C": 0},
    "BFCL v3": {"S": 80, "A": 65, "B": 50, "C": 0},
    "Arena ELO": {"S": 1350, "A": 1300, "B": 1250, "C": 0},
}


def load_benchmarks() -> dict:
    if not BENCHMARKS_PATH.exists():
        return {}
    try:
        raw = json.loads(BENCHMARKS_PATH.read_text())
        # Reorganize into a flat list of {model_id, score, benchmark} entries
        entries = []
        for key, val in raw.items():
            if not isinstance(val, dict) or key.startswith("_"):
                continue
            bench_name = val.get("_benchmark", key)
            for mid, score in val.items():
                if mid.startswith("_"):
                    continue
                if isinstance(score, (int, float)):
                    entries.append({
                        "benchmark": bench_name,
                        "model_id": mid,
                        "score": float(score),
                    })
                elif isinstance(score, dict):
                    # Nested structure like {swe_verified: 79, ...}
                    for sub_key, sub_val in score.items():
                        if isinstance(sub_val, (int, float)):
                            entries.append({
                                "benchmark": f"{bench_name}/{sub_key}",
                                "model_id": mid,
                                "score": float(sub_val),
                            })
        return {"_entries": entries}
    except (json.JSONDecodeError, Exception) as e:
        print(f"  ⚠ Error parsing benchmarks: {e}")
        return {}


def load_scan_history() -> list[tuple[int, list[dict]]]:
    """Load each scan and its models."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    scans = conn.execute("SELECT scan_id, scanned_at FROM scans ORDER BY scan_id ASC").fetchall()
    result = []
    for s in scans:
        models = conn.execute(
            "SELECT * FROM models WHERE scan_id = ?", (s["scan_id"],)
        ).fetchall()
        result.append((s["scan_id"], [dict(m) for m in models]))
    
    conn.close()
    return result


def tier_for_score(composite: float, thresholds: dict) -> str:
    for tier, (lo, hi) in sorted(thresholds.items(), key=lambda x: -x[1][1]):
        if lo <= composite <= hi:
            return tier
    return "C"


def benchmark_tier(model_id: str, entries: list[dict]) -> dict | None:
    """Get benchmark tier for a model."""
    for entry in entries:
        mid = entry.get("model_id", "").lower()
        if mid == model_id.lower():
            score = entry.get("score", 0)
            bench_name = entry.get("benchmark", "")
            quality_map = BENCHMARK_QUALITY.get(bench_name, {})
            if not quality_map:
                continue
            btier = "C"
            for t, threshold in sorted(quality_map.items(), key=lambda x: -x[1]):
                if score >= threshold or threshold == 0:
                    btier = t
                    break
            return {
                "benchmark": bench_name,
                "score": score,
                "tier": btier,
            }
    return None


def run_audit() -> dict:
    """Run full audit against all available data."""
    results = {
        "generated_at": datetime.now().isoformat(),
        "sections": {},
    }
    
    print("  Loading benchmarks...")
    benchmark_data = load_benchmarks()
    benchmark_entries = benchmark_data.get("_entries", [])
    results["benchmark_sources"] = list(set(e["benchmark"] for e in benchmark_entries))
    print(f"  ✓ {len(benchmark_entries)} entries")
    
    print("  Loading scan history...")
    scan_history = load_scan_history()
    results["scan_count"] = len(scan_history)
    print(f"  ✓ {len(scan_history)} scans loaded")
    
    # ── Section 1: Tier Accuracy ──
    print("  Checking tier classification accuracy...")
    tier_errors = []
    tier_stats = {"S": {"correct": 0, "total": 0}, "A": {"correct": 0, "total": 0},
                  "B": {"correct": 0, "total": 0}, "C": {"correct": 0, "total": 0}}
    confidence_gaps = []
    
    for scan_id, models in scan_history:
        for m in models:
            mtier = m.get("tier", "C")
            composite = m.get("composite", 0) or 0
            expected = tier_for_score(composite, TIER_THRESHOLDS)
            
            if mtier in tier_stats:
                tier_stats[mtier]["total"] += 1
                if mtier == expected:
                    tier_stats[mtier]["correct"] += 1
                else:
                    tier_errors.append({
                        "scan_id": scan_id,
                        "model": m.get("model_id", ""),
                        "assigned": mtier,
                        "expected": expected,
                        "composite": composite,
                    })
            
            # Check confidence gap: high composite but low tier (or vice versa)
            ai = m.get("ai_index")
            if ai is not None and composite > 0:
                gap = abs(composite - ai)
                if gap > 25:
                    confidence_gaps.append({
                        "scan_id": scan_id,
                        "model": m.get("model_id", ""),
                        "composite": composite,
                        "ai_index": ai,
                        "gap": round(gap, 1),
                    })
    
    results["sections"]["tier_accuracy"] = {
        "total_models_checked": sum(s["total"] for s in tier_stats.values()),
        "per_tier": tier_stats,
        "overall_accuracy": round(
            sum(s["correct"] for s in tier_stats.values()) / max(
                sum(s["total"] for s in tier_stats.values()), 1
            ) * 100, 1
        ),
        "tier_errors_count": len(tier_errors),
        "tier_errors": tier_errors[:20],  # Top 20
        "confidence_gaps_count": len(confidence_gaps),
        "confidence_gaps": confidence_gaps[:10],
    }
    
    # ── Section 2: Benchmark Correlation ──
    print("  Checking benchmark correlation...")
    bench_correlations = []
    
    for scan_id, models in scan_history:
        for m in models:
            mid = m.get("model_id", "").lower()
            mtier = m.get("tier", "C")
            bt = benchmark_tier(mid, benchmark_entries)
            
            if bt:
                # Compare model-scan tier to benchmark tier
                tier_order = ["C", "B", "A", "S"]
                scan_tier_idx = tier_order.index(mtier) if mtier in tier_order else 0
                bench_tier_idx = tier_order.index(bt["tier"]) if bt["tier"] in tier_order else 0
                discrepancy = abs(scan_tier_idx - bench_tier_idx)
                
                bench_correlations.append({
                    "scan_id": scan_id,
                    "model": mid,
                    "scan_tier": mtier,
                    "benchmark": bt["benchmark"],
                    "benchmark_score": bt["score"],
                    "benchmark_tier": bt["tier"],
                    "discrepancy": discrepancy,
                })
    
    # False positives: S/A tier in scan but C/B in benchmark
    false_positives = [c for c in bench_correlations if c["scan_tier"] in ("S", "A") and c["benchmark_tier"] == "C"]
    false_negatives = [c for c in bench_correlations if c["scan_tier"] == "C" and c["benchmark_tier"] in ("S", "A")]
    high_discrepancy = [c for c in bench_correlations if c["discrepancy"] >= 2]
    
    results["sections"]["benchmark_correlation"] = {
        "total_models_with_benchmarks": len(bench_correlations),
        "false_positives": {
            "count": len(false_positives),
            "examples": false_positives[:10],
        },
        "false_negatives": {
            "count": len(false_negatives),
            "examples": false_negatives[:10],
        },
        "high_discrepancy": {
            "count": len(high_discrepancy),
            "examples": high_discrepancy[:10],
        },
        "avg_discrepancy": round(
            mean([c["discrepancy"] for c in bench_correlations]) if bench_correlations else 0, 2
        ),
    }
    
    # ── Section 3: Provider Bias ──
    print("  Checking provider bias...")
    provider_stats = defaultdict(lambda: {"count": 0, "composites": [], "tiers": []})
    
    for scan_id, models in scan_history:
        for m in models:
            prov = m.get("provider", "unknown")
            provider_stats[prov]["count"] += 1
            provider_stats[prov]["composites"].append(m.get("composite", 0) or 0)
            provider_stats[prov]["tiers"].append(m.get("tier", "C"))
    
    provider_analysis = {}
    for prov, stats in sorted(provider_stats.items()):
        tier_order = ["C", "B", "A", "S"]
        avg_tier_idx = mean([tier_order.index(t) if t in tier_order else 0 for t in stats["tiers"]])
        provider_analysis[prov] = {
            "model_count": stats["count"],
            "avg_composite": round(mean(stats["composites"]), 1) if stats["composites"] else 0,
            "avg_tier": tier_order[min(int(round(avg_tier_idx)), 3)] if stats["tiers"] else "C",
            "std_composite": round(stdev(stats["composites"]), 1) if len(stats["composites"]) > 1 else 0,
        }
    
    results["sections"]["provider_bias"] = provider_analysis
    
    # ── Section 4: Coverage Gaps ──
    print("  Checking coverage gaps...")
    all_benchmark_models = set()
    for entry in benchmark_entries:
        all_benchmark_models.add(entry.get("model_id", "").lower())
    
    scanned_models = set()
    for scan_id, models in scan_history:
        for m in models:
            scanned_models.add(m.get("model_id", "").lower())
    
    missed_models = all_benchmark_models - scanned_models
    
    results["sections"]["coverage_gaps"] = {
        "benchmark_models_total": len(all_benchmark_models),
        "scanned_models_total": len(scanned_models),
        "missed_benchmark_models": sorted(missed_models)[:30],
        "missed_count": len(missed_models),
        "coverage_rate": round(
            len(all_benchmark_models - missed_models) / max(len(all_benchmark_models), 1) * 100, 1
        ),
    }
    
    # ── Section 5: Score Drift ──
    print("  Checking score drift over time...")
    top_models_over_time = {}
    for scan_id, models in scan_history:
        sliced = sorted(models, key=lambda m: -(m.get("composite", 0) or 0))[:5]
        for m in sliced:
            mid = m.get("model_id", "").lower()
            if mid not in top_models_over_time:
                top_models_over_time[mid] = []
            top_models_over_time[mid].append({
                "scan_id": scan_id,
                "composite": m.get("composite", 0) or 0,
                "tps": m.get("tps", 0) or 0,
                "tier": m.get("tier", "C"),
            })
    
    drift_models = {}
    for mid, entries in top_models_over_time.items():
        if len(entries) >= 3:
            scores = [e["composite"] for e in entries]
            drift = round(max(scores) - min(scores), 1)
            if drift > 10:
                drift_models[mid] = {
                    "entries": len(entries),
                    "score_range": drift,
                    "first_score": scores[0],
                    "last_score": scores[-1],
                    "trend": "up" if scores[-1] > scores[0] else "down",
                }
    
    results["sections"]["score_drift"] = {
        "models_with_drift": drift_models,
        "high_drift_count": len(drift_models),
    }
    
    # Summary
    results["summary"] = {
        "tier_accuracy": results["sections"]["tier_accuracy"]["overall_accuracy"],
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "high_discrepancies": len(high_discrepancy),
        "provider_count": len(provider_analysis),
        "missed_benchmark_models": len(missed_models),
        "models_with_high_drift": len(drift_models),
    }
    
    return results


def format_report(results: dict) -> str:
    """Format audit as a readable markdown report."""
    s = results["sections"]
    summary = results["summary"]
    
    lines = [
        f"# Independent Audit Report",
        f"",
        f"**Generated:** {results['generated_at'][:19]}",
        f"**Scans analyzed:** {results['scan_count']}",
        f"**Benchmark sources:** {', '.join(results.get('benchmark_sources', []))}",
        f"",
        f"## Executive Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **Tier Classification Accuracy** | {summary['tier_accuracy']}% |",
        f"| **False Positives** (over-ranked) | {summary['false_positives']} |",
        f"| **False Negatives** (under-ranked) | {summary['false_negatives']} |",
        f"| **High Tier Discrepancies** (≥2 tiers off) | {summary['high_discrepancies']} |",
        f"| **Providers** | {summary['provider_count']} |",
        f"| **Missed Benchmark Models** | {summary['missed_benchmark_models']} |",
        f"| **Models with High Score Drift** | {summary['models_with_high_drift']} |",
        f"",
    ]
    
    # Tier accuracy
    ta = s["tier_accuracy"]
    lines += [
        f"## 1. Tier Classification Accuracy",
        f"",
        f"**{ta['overall_accuracy']}%** overall accuracy across {ta['total_models_checked']} model-scans.",
        f"",
        f"| Tier | Correct | Total | Accuracy |",
        f"|------|---------|-------|----------|",
    ]
    for t in ["S", "A", "B", "C"]:
        st = ta["per_tier"].get(t, {"correct": 0, "total": 0})
        acc = round(st["correct"] / max(st["total"], 1) * 100, 1)
        lines.append(f"| **{t}** | {st['correct']} | {st['total']} | {acc}% |")
    
    if ta["tier_errors"]:
        lines += [f"", f"### Tier Errors (first {len(ta['tier_errors'])})", f""]
        for e in ta["tier_errors"][:10]:
            lines.append(f"- {e['model']}: scan assigns **{e['assigned']}** but composite={e['composite']} → expected **{e['expected']}**")
    
    if ta["confidence_gaps"]:
        lines += [f"", f"### Confidence Gaps (composite vs AI index > 25pts)", f""]
        for g in ta["confidence_gaps"][:10]:
            lines.append(f"- {g['model']}: composite={g['composite']} vs ai_index={g['ai_index']} (gap={g['gap']})")
    
    # Benchmark correlation
    bc = s["benchmark_correlation"]
    lines += [
        f"",
        f"## 2. Benchmark Correlation",
        f"",
        f"**{bc['total_models_with_benchmarks']}** models have both a scan tier and at least one benchmark score.",
        f"Average tier discrepancy: **{bc['avg_discrepancy']}** tiers.",
        f"",
        f"### False Positives ({bc['false_positives']['count']})",
        f"Models rated S/A by scan but C-tier by benchmark:",
    ]
    for fp in bc["false_positives"]["examples"][:10]:
        lines.append(f"- {fp['model']}: scan={fp['scan_tier']}, benchmark={fp['benchmark']}={fp['benchmark_score']} ({fp['benchmark_tier']})")
    
    lines += [
        f"",
        f"### False Negatives ({bc['false_negatives']['count']})",
        f"Models rated C by scan but S/A-tier by benchmark:",
    ]
    for fn in bc["false_negatives"]["examples"][:10]:
        lines.append(f"- {fn['model']}: scan={fn['scan_tier']}, benchmark={fn['benchmark']}={fn['benchmark_score']} ({fn['benchmark_tier']})")
    
    # Provider bias
    lines += [f"", f"## 3. Provider Profiles", f""]
    lines += [f"| Provider | Models | Avg Composite | Avg Tier | Std Dev |"]
    lines += [f"|----------|--------|--------------|----------|---------|"]
    for prov, p in sorted(s["provider_bias"].items()):
        lines.append(f"| {prov} | {p['model_count']} | {p['avg_composite']} | {p['avg_tier']} | {p['std_composite']} |")
    
    # Coverage
    cov = s["coverage_gaps"]
    lines += [
        f"",
        f"## 4. Coverage Gaps",
        f"",
        f"**{cov['coverage_rate']}%** coverage rate ({cov['scanned_models_total']} scanned vs {cov['benchmark_models_total']} with benchmarks).",
        f"**{cov['missed_count']}** benchmarked models missing from scans:",
    ]
    for m in cov["missed_benchmark_models"][:20]:
        lines.append(f"- {m}")
    
    # Score drift
    drift = s["score_drift"]
    lines += [f"", f"## 5. Score Drift", f"", f"**{drift['high_drift_count']}** models show >10pt composite drift across 3+ scans:"]
    for mid, d in sorted(drift["models_with_drift"].items()):
        lines.append(f"- {mid}: {d['first_score']} → {d['last_score']} ({d['trend']}, range={d['score_range']})")
    
    lines += [f"", f"---", f"*Report by model-scan audit system*"]
    return "\n".join(lines)


def main():
    """Run independent audit."""
    print("┌─ Independent Audit ─────────────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└─────────────────────────────────────────────────────")
    
    results = run_audit()
    summary = results["summary"]
    
    # Write JSON
    json_path = OUTPUT_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.json"
    json_path.write_text(json.dumps(results, indent=2, default=str))
    
    # Write report
    md_path = OUTPUT_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.md"
    md_path.write_text(format_report(results))
    
    print(f"\n  ┌─ Results ──────────────────────────────")
    print(f"  │ Tier Accuracy:     {summary['tier_accuracy']}%")
    print(f"  │ False Positives:   {summary['false_positives']}")
    print(f"  │ False Negatives:   {summary['false_negatives']}")
    print(f"  │ High Discrepancy:  {summary['high_discrepancies']}")
    print(f"  │ Providers:         {summary['provider_count']}")
    print(f"  │ Missed Benchmarks: {summary['missed_benchmark_models']}")
    print(f"  │ High Drift:        {summary['models_with_high_drift']}")
    print(f"  └──────────────────────────────────────────────")
    print(f"  ├─ json:  {json_path.name}")
    print(f"  └─ md:    {md_path.name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
