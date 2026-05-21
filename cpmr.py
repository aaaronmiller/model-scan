"""
model-scan — CPMR: Config Patch Match Rate

Evaluates how closely the automated scoring engine matches the gold standard
(LLM-generated config recommendations). Produces:

  - Per-slot match rate (0-100%)
  - Divergence report with reasoning for each mismatch
  - Aggregate CPMR score across all slots
  - Improvement suggestions (which weights to tune, by how much)

The CPMR is the KEY METRIC for the optimization loop — maximizing it means
the automated system is converging on the gold standard.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scoring.engine import ScoringEngine, load_benchmarks

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
SLOTS_PATH = CONFIG_DIR / "slot_definitions.yaml"
GS_DIR = CONFIG_DIR / "gold_standard"
OUTPUT_DIR = CONFIG_DIR / "cpmr"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default composite weights (must match gold_standard.py)
COMPOSITE_WEIGHTS = {
    "intelligence": 0.40,
    "speed": 0.20,
    "agentic": 0.20,
    "coding": 0.20,
}


def load_gold_standard() -> dict | None:
    """Load the most recent gold standard file."""
    gs_files = sorted(GS_DIR.glob("gold_standard_*.json"))
    if not gs_files:
        return None
    return json.loads(gs_files[-1].read_text())


def load_slot_config(path: Path = SLOTS_PATH) -> dict:
    """Load slot definitions from YAML."""
    import yaml
    try:
        return yaml.safe_load(open(path)) or {}
    except Exception:
        return {}


def load_scan_models() -> list[dict]:
    """Load models from latest scan."""
    import sqlite3
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT MAX(scan_id) FROM scans")
    scan_id = cur.fetchone()[0]
    if not scan_id:
        conn.close()
        return []
    cur = conn.execute(
        "SELECT * FROM models WHERE scan_id = ? AND accessible = 1 ORDER BY composite DESC",
        (scan_id,)
    )
    models = [dict(r) for r in cur.fetchall()]
    conn.close()
    return models


def automated_rank(slot_id: str, slot_def: dict, models: list[dict],
                   benchmarks: dict, weights: dict | None = None) -> list[dict]:
    """Rank models for a slot using the automated scoring engine."""
    w = weights or COMPOSITE_WEIGHTS
    results = []
    for m in models:
        md = {
            "model_id": m.get("model_id") or m.get("model", ""),
            "provider": m.get("provider", ""),
            "tps": m.get("tps", 0),
            "latency_s": m.get("latency_s", 0),
            "ai_index": m.get("ai_index"),
            "ai_coding": m.get("ai_coding"),
            "has_tools": bool(m.get("has_tools", False)),
            "has_vision_capability": bool(m.get("has_vision_capability", False)),
            "has_reasoning": bool(m.get("has_reasoning", False)),
            "context_window": (m.get("ctx_k", 0) or 0) * 1024,
            "knowledge": str(m.get("knowledge", "") or ""),
            "release_date": str(m.get("release_date", "") or ""),
            "benchmark_swe_verified": m.get("benchmark_swe_verified"),
            "price_blended": m.get("price_blended"),
            "arch": m.get("arch", ""),
        }
        engine = ScoringEngine(md, benchmarks)
        scores = engine.compute_all()
        composite = scores.composite(w)
        
        # Gate checks
        gates_failed = []
        if slot_def.get("needs_tools", False) and not md["has_tools"]:
            gates_failed.append("tools")
        if slot_def.get("needs_vision", False) and not md["has_vision_capability"]:
            gates_failed.append("vision")
        if slot_def.get("min_ai", 0) > 0 and (md["ai_index"] or 0) < slot_def["min_ai"]:
            gates_failed.append("ai")
        if slot_def.get("min_tps", 0) > 0 and md["tps"] < slot_def["min_tps"]:
            gates_failed.append("tps")
        if slot_def.get("max_latency_s", 99) < 99 and md["latency_s"] > slot_def["max_latency_s"]:
            gates_failed.append("latency")
        
        results.append({
            "model_id": md["model_id"],
            "provider": md["provider"],
            "composite": round(composite, 1),
            "scores": scores.to_dict(),
            "qualified": len(gates_failed) == 0,
            "gates_failed": gates_failed,
        })
    
    results.sort(key=lambda r: (r["qualified"], r["composite"]), reverse=True)
    return results


def compute_cpmr(gold: dict, slot_defs: dict, models: list[dict],
                 benchmarks: dict) -> dict:
    """Compute CPMR between gold standard and automated scoring."""
    results = {}
    
    for slot_id, gs_slot in gold.get("slots", {}).items():
        sdef = slot_defs.get(slot_id, {})
        gs_primary = gs_slot.get("primary", {})
        if not gs_primary:
            results[slot_id] = {
                "label": gs_slot.get("label", slot_id),
                "gs_primary": None,
                "error": "No gold standard primary",
            }
            continue
        
        auto = automated_rank(slot_id, sdef, models, benchmarks)
        auto_qualified = [a for a in auto if a["qualified"]]
        
        auto_primary = auto_qualified[0] if auto_qualified else (auto[0] if auto else None)
        
        # Match: exact model match, or same model family
        gs_model = gs_primary["model_id"]
        auto_model = auto_primary["model_id"] if auto_primary else None
        
        exact_match = gs_model == auto_model
        # Fuzzy match: same model prefix (e.g., deepseek-v4-flash vs deepseek-v4-flash-free)
        gs_prefix = gs_model.split(":")[0].split("/")[-1]
        auto_prefix = (auto_model or "").split(":")[0].split("/")[-1]
        fuzzy_match = gs_prefix == auto_prefix or (
            gs_model.replace("-free", "") == (auto_model or "").replace("-free", "")
        )
        
        # Score divergence
        gs_score = gs_primary.get("composite", 0)
        auto_score = auto_primary["composite"] if auto_primary else 0
        score_diff = round(gs_score - auto_score, 1)
        
        # Position of GS primary in auto rankings
        gs_rank_in_auto = -1
        for i, a in enumerate(auto):
            if a["model_id"] == gs_model or a["model_id"].replace("-free", "") == gs_model.replace("-free", ""):
                gs_rank_in_auto = i + 1
                break
        
        results[slot_id] = {
            "label": gs_slot.get("label", slot_id),
            "gs_primary": gs_model,
            "auto_primary": auto_model,
            "auto_provider": auto_primary["provider"] if auto_primary else None,
            "exact_match": exact_match,
            "fuzzy_match": fuzzy_match,
            "gs_score": gs_score,
            "auto_score": auto_score,
            "score_diff": score_diff,
            "gs_rank_in_auto": gs_rank_in_auto,
            "auto_qualified_count": len(auto_qualified),
            "auto_total_count": len(auto),
            "gs_primary_trace": gs_primary.get("scores", {}).get("traces", {}),
            "auto_primary_trace": auto_primary["scores"]["traces"] if auto_primary else {},
        }
    
    # Aggregate CPMR
    scored_slots = {k: v for k, v in results.items() if "error" not in v}
    exact_matches = sum(1 for v in scored_slots.values() if v.get("exact_match"))
    fuzzy_matches = sum(1 for v in scored_slots.values() if v.get("fuzzy_match"))
    total = len(scored_slots) if scored_slots else 1
    
    cpmr_exact = round(exact_matches / total * 100, 1)
    cpmr_fuzzy = round(fuzzy_matches / total * 100, 1)
    avg_score_diff = round(
        sum(abs(v["score_diff"]) for v in scored_slots.values()) / total, 1
    ) if total > 0 else 0
    
    # Improvement suggestions
    suggestions = []
    for slot_id, v in sorted(scored_slots.items()):
        if not v.get("exact_match") and v.get("gs_rank_in_auto", -1) > 0:
            sdef = slot_defs.get(slot_id, {})
            suggestions.append({
                "slot": slot_id,
                "label": v.get("label", ""),
                "gs_model": v["gs_primary"],
                "auto_model": v["auto_primary"],
                "gs_rank": v["gs_rank_in_auto"],
                "score_diff": v["score_diff"],
                "weights": {
                    "intel": sdef.get("weight_intelligence", 0.35),
                    "speed": sdef.get("weight_speed", 0.35),
                    "reliability": sdef.get("weight_reliability", 0.30),
                },
            })
    
    return {
        "generated_at": datetime.now().isoformat(),
        "gold_standard_file": str(GS_DIR / f"gold_standard_{gold.get('scan_id')}.json"),
        "scan_id": gold.get("scan_id"),
        "cpmr_exact": cpmr_exact,
        "cpmr_fuzzy": cpmr_fuzzy,
        "avg_absolute_score_diff": avg_score_diff,
        "slots_evaluated": total,
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "per_slot": results,
        "improvement_suggestions": suggestions,
        "total_suggestions": len(suggestions),
    }


def format_report(cpmr: dict) -> str:
    """Format CPMR evaluation as readable report."""
    lines = [
        "# CPMR Evaluation Report",
        f"",
        f"**Generated:** {cpmr['generated_at'][:19]}",
        f"**Scan #:** {cpmr.get('scan_id')}",
        f"**Gold standard:** {cpmr.get('gold_standard_file')}",
        f"",
        f"## Aggregate Metrics",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **CPMR (exact)** | {cpmr['cpmr_exact']}% |",
        f"| **CPMR (fuzzy)** | {cpmr['cpmr_fuzzy']}% |",
        f"| **Avg score diff** | {cpmr['avg_absolute_score_diff']} pts |",
        f"| **Exact matches** | {cpmr['exact_matches']}/{cpmr['slots_evaluated']} |",
        f"| **Fuzzy matches** | {cpmr['fuzzy_matches']}/{cpmr['slots_evaluated']} |",
        f"",
        f"## Per-Slot Breakdown",
        f"",
    ]
    
    for slot_id, v in sorted(cpmr.get("per_slot", {}).items()):
        label = v.get("label", "")
        if "error" in v:
            lines.append(f"### {slot_id}: {label}")
            lines.append(f"")
            lines.append(f"- ⚠ {v['error']}")
            lines.append(f"")
            continue
        
        match_icon = "✅" if v.get("exact_match") else ("🔶" if v.get("fuzzy_match") else "❌")
        lines.append(f"### {match_icon} {slot_id}: {label}")
        lines.append(f"")
        lines.append(f"| | Gold Standard | Automated |")
        lines.append(f"|---|--------------|-----------|")
        lines.append(f"| **Primary** | {v['gs_primary']} | {v['auto_primary']} |")
        lines.append(f"| **Provider** | — | {v['auto_provider']} |")
        lines.append(f"| **Score** | {v['gs_score']} | {v['auto_score']} |")
        lines.append(f"| **Δ Score** | | {v['score_diff']:+.1f} |")
        lines.append(f"| **GS rank in auto** | | #{v['gs_rank_in_auto']} |")
        lines.append(f"")
        
        if v.get("gs_primary_trace"):
            lines.append(f"**Gold standard reasoning:**")
            for axis, text in v["gs_primary_trace"].items():
                lines.append(f"- {text}")
        if v.get("auto_primary_trace"):
            lines.append(f"")
            lines.append(f"**Automated reasoning:**")
            for axis, text in v["auto_primary_trace"].items():
                lines.append(f"- {text}")
        lines.append(f"")
    
    if cpmr.get("improvement_suggestions"):
        lines.append(f"## Improvement Suggestions")
        lines.append(f"")
        lines.append(f"These slots have mismatches where the gold standard model is in the automated rankings:")
        lines.append(f"")
        lines.append(f"| Slot | GS Model | Auto Model | GS Rank | Δ Score |")
        lines.append(f"|------|----------|------------|---------|---------|")
        for s in cpmr["improvement_suggestions"]:
            lines.append(f"| {s['slot']} | {s['gs_model']} | {s['auto_model']} | #{s['gs_rank']} | {s['score_diff']:+.1f} |")
    
    lines.append(f"---")
    lines.append(f"*Report generated by model-scan CPMR evaluator*")
    return "\n".join(lines)


def main():
    """Run CPMR evaluation."""
    print("┌─ CPMR Evaluator ─────────────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└───────────────────────────────────────────────────")
    
    print("  Loading gold standard...")
    gold = load_gold_standard()
    if not gold:
        print("  ✗ No gold standard found. Run --gold-standard first.")
        return 1
    print(f"  ✓ Loaded scan #{gold.get('scan_id')}, {len(gold.get('slots', {}))} slots")
    
    print("  Loading slot definitions...")
    slot_defs = load_slot_config()
    print(f"  ✓ {len(slot_defs)} slot defs")
    
    print("  Loading scan models...")
    models = load_scan_models()
    print(f"  ✓ {len(models)} models")
    
    print("  Loading benchmarks...")
    benchmarks = load_benchmarks()
    print(f"  ✓ {len(benchmarks)} benchmark sources")
    
    print("  Computing CPMR...")
    cpmr = compute_cpmr(gold, slot_defs, models, benchmarks)
    
    # Outputs
    json_path = OUTPUT_DIR / f"cpmr_{cpmr['scan_id']}.json"
    json_path.write_text(json.dumps(cpmr, indent=2, default=str))
    
    md_path = OUTPUT_DIR / f"report_{cpmr['scan_id']}.md"
    md_path.write_text(format_report(cpmr))
    
    print(f"\n  Results:")
    print(f"  ├─ CPMR (exact): {cpmr['cpmr_exact']}%")
    print(f"  ├─ CPMR (fuzzy): {cpmr['cpmr_fuzzy']}%")
    print(f"  ├─ Avg score Δ:  {cpmr['avg_absolute_score_diff']} pts")
    print(f"  ├─ Suggestions:   {cpmr['total_suggestions']}")
    print(f"  ├─ json:          {json_path.name}")
    print(f"  └─ md:            {md_path.name}")
    
    # Show per-slot summary
    print(f"\n  Per-slot matches:")
    for slot_id, v in sorted(cpmr.get("per_slot", {}).items()):
        if "error" in v:
            print(f"    {slot_id:20s}  ⚠ {v['error']}")
        elif v.get("exact_match"):
            print(f"    {slot_id:20s}  ✅ {v['gs_primary']} = {v['auto_primary']}")
        elif v.get("fuzzy_match"):
            print(f"    {slot_id:20s}  🔶 {v['gs_primary']} ≈ {v['auto_primary']}")
        else:
            print(f"    {slot_id:20s}  ❌ GS={v['gs_primary']} → Auto={v['auto_primary']} (rank #{v['gs_rank_in_auto']})")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
