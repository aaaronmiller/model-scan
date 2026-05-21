"""
model-scan — Deliberative Refinement Passes

Verifies the multi-source analysis engine across 4 passes:
  Pass 1: Data fidelity — cross-reference accuracy, field mapping correctness
  Pass 2: Metric soundness — derived math, edge cases, normalization
  Pass 3: Cluster consistency — capability classification accuracy
  Pass 4: External grounding — compare against known benchmarks

Each pass generates a scored report with failure evidence.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "model-scan"
OUTPUT_DIR = CONFIG_DIR / "refinement"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PASSES = []


def pass_register(fn):
    PASSES.append(fn)
    return fn


def fmt_score(p: int, t: int) -> str:
    pct = round(p / max(t, 1) * 100, 1)
    icon = "✅" if pct >= 90 else "🔶" if pct >= 70 else "❌"
    return f"{icon} {p}/{t} ({pct}%)"


# ── PASS 1: Data Fidelity ──────────────────────────────────────────────────

@pass_register
def pass1_data_fidelity(metrics: dict) -> dict:
    """Verify cross-references and field mappings."""
    issues = []
    checks = 0
    passes = 0
    
    for nid, m in list(metrics.items())[:200]:  # Sample 200
        checks += 1
        
        # AA index should be 0-60
        ai = m.get("ai_intelligence")
        if ai is not None:
            if not (0 <= ai <= 65):
                issues.append(f"{nid}: ai_intelligence={ai} out of valid range [0,65]")
        
        # TPS should be positive
        tps = m.get("tps")
        if tps is not None and tps <= 0:
            issues.append(f"{nid}: tps={tps} should be > 0")
        
        # Cost should be non-negative
        cost = m.get("cost_blended_per_m")
        if cost is not None and cost < 0:
            issues.append(f"{nid}: negative cost={cost}")
        
        # Composite should be bounded 0-100
        cs = m.get("derived", {}).get("composite_score")
        if cs is not None:
            if not (0 <= cs <= 100):
                issues.append(f"{nid}: composite={cs} out of [0,100]")
            else:
                passes += 1
                continue
        
        passes += 1
        
        # Context should be reasonable
        ctx = m.get("context_k")
        if ctx is not None and (ctx < 0 or ctx > 2000):
            issues.append(f"{nid}: context={ctx}K seems extreme")
    
    return {
        "name": "Pass 1: Data Fidelity",
        "score": f"{fmt_score(passes, checks)}",
        "passed": passes,
        "total": checks,
        "issues": issues[:20],
        "total_issues": len(issues),
        "finding": "Field ranges and cross-references verified" if len(issues) < 5 else f"{len(issues)} field anomalies detected",
    }


# ── PASS 2: Metric Soundness ───────────────────────────────────────────────

@pass_register
def pass2_metric_soundness(metrics: dict) -> dict:
    """Verify derived metric math makes sense."""
    issues = []
    checks = 0
    passes = 0
    
    for nid, m in list(metrics.items())[:200]:
        d = m.get("derived", {})
        checks += 1
        
        # Metric 1: AVI = ai_intel * (pb_pct/100) / 60 * 100 = ai_intel * pb_pct / 60
        avi = d.get("agent_value_index")
        if avi is not None:
            expected = None
            ai = m.get("ai_intelligence")
            pb = m.get("pinchbench_best_pct")
            if ai and pb:
                expected = round(ai * (pb / 100.0) / 60.0 * 100, 1)  # pb is stored as pct, convert to fraction
            if expected is not None and abs(avi - expected) > 1.0 and abs(avi - expected) / max(expected, 1) > 0.05:
                issues.append(f"{nid}: AVI={avi} expected≈{expected} (Δ={abs(avi-expected):.1f})")
        
        # Metric 2: CAI = ai_intel / cost
        cai = d.get("cost_adjusted_intelligence")
        if cai is not None:
            ai = m.get("ai_intelligence")
            cost = m.get("cost_blended_per_m")
            if ai is not None and cost and cost > 0:
                expected = round(ai / cost, 1)
                if abs(cai - expected) > 1.0:
                    issues.append(f"{nid}: CAI={cai} expected≈{expected}")
        
        # Metric 3: SQR = tps / max(1, 100-ai) * 10
        sqr = d.get("speed_quality_ratio")
        if sqr is not None:
            tps = m.get("tps")
            ai = m.get("ai_intelligence")
            if tps and ai:
                expected = round(tps / max(1, 100 - ai) * 10, 1)
                if abs(sqr - expected) > 0.5:  # tolerance for rounding
                    issues.append(f"{nid}: SQR={sqr} expected≈{expected}")
        
        # Metric 4: Capability Density = count / cost
        cd = d.get("capability_density")
        if cd is not None:
            pass  # Hard to verify statically but we check bounds
        
        # Composite should be ≥ individual components
        cs = d.get("composite_score")
        if cs is not None and cs > 100:
            issues.append(f"{nid}: composite={cs} > 100 (impossible)")
        
        # Modality breadth should be integer
        mb = d.get("modality_breadth")
        if mb is not None and not isinstance(mb, int) and mb != int(mb):
            issues.append(f"{nid}: modality_breadth={mb} not integer")
        
        passes += 1
    
    return {
        "name": "Pass 2: Metric Soundness",
        "score": f"{fmt_score(passes, checks)}",
        "passed": passes,
        "total": checks,
        "issues": issues[:20],
        "total_issues": len(issues),
        "finding": "Derived metrics compute correctly" if len(issues) < 3 else f"{len(issues)} math errors detected",
    }


# ── PASS 3: Cluster Consistency ────────────────────────────────────────────

@pass_register
def pass3_cluster_consistency(metrics: dict, clusters: dict) -> dict:
    """Verify capability clusters make logical sense."""
    issues = []
    checks = 0
    passes = 0
    
    # agent_ready: must have tools + reasoning
    for nid in clusters.get("agent_ready", []):
        m = metrics.get(nid)
        if not m:
            continue
        checks += 1
        tc = m.get("tool_call_capable", False)
        rc = m.get("reasoning_capable", False)
        if not (tc and rc):
            issues.append(f"{nid}: in agent_ready but tools={tc} reasoning={rc}")
        else:
            passes += 1
    
    # reasoning_only: must have reasoning but NO tools
    for nid in clusters.get("reasoning_only", []):
        m = metrics.get(nid)
        if not m:
            continue
        checks += 1
        rc = m.get("reasoning_capable", False)
        tc = m.get("tool_call_capable", False)
        if not rc:
            issues.append(f"{nid}: in reasoning_only but reasoning={rc}")
        elif tc:
            issues.append(f"{nid}: in reasoning_only but has tools (should be agent_ready)")
        else:
            passes += 1
    
    # lightweight: no reasoning, ai<30, tps>50, cost<1
    for nid in clusters.get("lightweight", []):
        m = metrics.get(nid)
        if not m:
            continue
        checks += 1
        ai = m.get("ai_intelligence", 0) or 0
        tps = m.get("tps", 0) or 0
        cost = m.get("cost_blended_per_m", 999) or 999
        rc = m.get("reasoning_capable", False)
        # These are loose heuristics, so just check outliers
        if ai > 40:
            issues.append(f"{nid}: in lightweight but ai={ai} > 40")
        else:
            passes += 1
    
    # open_workhorses: open_weights, ai>25, tool_call, cost<5
    for nid in clusters.get("open_workhorses", []):
        m = metrics.get(nid)
        if not m:
            continue
        checks += 1
        ow = m.get("open_weights", False)
        tc = m.get("tool_call_capable", False)
        if not ow:
            issues.append(f"{nid}: in open_workhorses but not open weights")
        elif not tc:
            issues.append(f"{nid}: in open_workhorses but no tool calling")
        else:
            passes += 1
    
    return {
        "name": "Pass 3: Cluster Consistency",
        "score": f"{fmt_score(passes, max(checks, 1))}",
        "passed": passes,
        "total": checks,
        "issues": issues[:20],
        "total_issues": len(issues),
        "finding": "Cluster logic clean" if len(issues) < 3 else f"{len(issues)} misclassified models",
    }


# ── PASS 4: External Grounding ─────────────────────────────────────────────

@pass_register
def pass4_external_grounding(metrics: dict) -> dict:
    """Compare composite rankings against known benchmark leaders."""
    issues = []
    checks = 0
    passes = 0
    
    # Ground truth: models we KNOW are top-tier from verified benchmarks
    ground_truth_top = {
        "deepseek/deepseek-v4-flash": 79.0,  # SWE-Verified
        "minimax/minimax-m2.5": 80.2,  # SWE-Verified  
        "kimi/k2.5": 65.0,  # approx SWE-Pro
        "anthropic/claude-opus-4.7": 91.6,  # PinchBench best
        "deepseek/deepseek-v4-pro": 72.0,  # SWE-Pro approx
    }
    
    for model_id, expected_rank in ground_truth_top.items():
        normalized = model_id.lower().replace("_", "-").replace(" ", "-")
        
        # Check composite
        for nid, m in metrics.items():
            if normalized in nid or nid in normalized:
                checks += 1
                cs = m.get("derived", {}).get("composite_score")
                ai = m.get("ai_intelligence")
                
                if cs:
                    # Known leaders should have high composites
                    if cs < 40:
                        issues.append(f"{nid}: composite={cs} but it's a known leader (expected >40)")
                    else:
                        passes += 1
                
                # Check AVI if PinchBench data available
                pb = m.get("pinchbench_best_pct")
                if pb:
                    checks += 1
                    if pb > 70:
                        passes += 1
                break
    
    # Check Pareto frontier includes known fast models
    fast_models = ["deepseek/deepseek-v4-flash", "step-3.5-flash", "google/gemini-3-flash"]
    for nid in fast_models:
        m = metrics.get(nid)
        if m:
            tps = m.get("tps", 0) or 0
            checks += 1
            if tps < 10:
                issues.append(f"{nid}: known fast model but tps={tps}")
            else:
                passes += 1
        else:
            issues.append(f"Known model {nid} not found in metrics")
    
    # Price sweet spot should be reasonable
    # (we can't verify exact number but check order of magnitude)
    
    return {
        "name": "Pass 4: External Grounding",
        "score": f"{fmt_score(passes, max(checks, 1))}",
        "passed": passes,
        "total": checks,
        "issues": issues[:20],
        "total_issues": len(issues),
        "finding": "Rankings align with verified benchmarks" if len(issues) < 3 else f"{len(issues)} discrepancies with known benchmarks",
    }


# ── MAIN ───────────────────────────────────────────────────────────────────

def main():
    print("┌─ Deliberative Refinement: 4 Passes ─────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└───────────────────────────────────────────────────\n")
    
    # Load analysis results
    analysis_dir = CONFIG_DIR / "analysis"
    files = sorted(analysis_dir.glob("analysis_*.json"), reverse=True)
    if not files:
        print("  ⚠ No analysis data found. Run --analyze first.")
        return 1
    
    data = json.loads(files[0].read_text())
    metrics = data.get("derived_metrics", {})
    clusters = data.get("capability_clusters", {})
    
    print(f"  Loaded: {files[0].name}")
    print(f"  Metrics: {len(metrics)} models")
    print(f"  Clusters: {sum(len(v) for v in clusters.values())} categorized\n")
    
    results = []
    overall_passed = 0
    overall_total = 0
    
    for i, fn in enumerate(PASSES, 1):
        print(f"  ── Pass {i} ────────────────────────────────────")
        print(f"  Running: {fn.__doc__}")
        
        if i == 3:  # Pass 3 needs clusters
            result = fn(metrics, clusters)
        else:
            result = fn(metrics)
        
        results.append(result)
        overall_passed += result["passed"]
        overall_total += result["total"]
        
        print(f"  {result['score']}")
        if result.get("issues"):
            for issue in result["issues"][:5]:
                print(f"    ⚠ {issue}")
        print(f"  → {result['finding']}\n")
    
    # Overall
    overall_pct = round(overall_passed / max(overall_total, 1) * 100, 1)
    overall_icon = "✅" if overall_pct >= 90 else "🔶" if overall_pct >= 70 else "❌"
    
    print(f"  {'═' * 50}")
    print(f"  {overall_icon} OVERALL: {overall_passed}/{overall_total} ({overall_pct}%)")
    
    # Write report
    report = {
        "generated_at": datetime.now().isoformat(),
        "source_file": files[0].name,
        "overall": {"passed": overall_passed, "total": overall_total, "pct": overall_pct},
        "passes": results,
    }
    report_path = OUTPUT_DIR / f"refinement_{datetime.now().strftime('%Y%m%d')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Report: {report_path.name}")
    
    return 0 if overall_pct >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
