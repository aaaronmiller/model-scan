"""
model-scan — Auto-Optimization Loop

Grid search over slot weight parameters to maximize CPMR (Config Patch Match Rate)
against the gold standard. Uses iterative search strategies:

  1. Grid sweep: test weight combinations across the full range
  2. Hill climb: from best grid point, refine with narrower steps
  3. Report: optimal weights per slot, CPMR improvement, convergence evidence

Strategy:
  - Sweep weight_intelligence: 0.1 → 0.9 (step 0.1)
  - Sweep weight_speed: 0.1 → 0.9 (step 0.1) 
  - weight_reliability = 1.0 - intel - speed (must be non-negative)
  - Only vary weights that differ from defaults
  - Evaluate CPMR for each combination
  - Output optimal + top-5 combinations per slot
"""
from __future__ import annotations

import itertools
import json
import sys
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

# Lazily loaded to support multiprocessing
CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
SLOTS_PATH = CONFIG_DIR / "slot_definitions.yaml"
GS_DIR = CONFIG_DIR / "gold_standard"
OUTPUT_DIR = CONFIG_DIR / "optimization"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMPOSITE_WEIGHTS = {
    "intelligence": 0.40,
    "speed": 0.20,
    "agentic": 0.20,
    "coding": 0.20,
}


def load_gold_standard() -> dict | None:
    gs_files = sorted(GS_DIR.glob("gold_standard_*.json"))
    if not gs_files:
        return None
    return json.loads(gs_files[-1].read_text())


def load_slots() -> dict:
    import yaml
    try:
        return yaml.safe_load(open(SLOTS_PATH)) or {}
    except Exception:
        return {}


def load_models() -> list[dict]:
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
        "SELECT * FROM models WHERE scan_id = ? AND accessible = 1",
        (scan_id,)
    )
    models = [dict(r) for r in cur.fetchall()]
    conn.close()
    return models


def _eval_combo(slot_id: str, slot_def: dict, models: list[dict],
                gs_primary: str, intel_w: float, speed_w: float) -> dict:
    """Evaluate a single weight combination for one slot."""
    from scoring.engine import ScoringEngine, load_benchmarks as lb
    benchmarks = lb()
    rel_w = max(0, 1.0 - intel_w - speed_w)
    
    # Map slot weights to 4-axis weights
    axis_weights = {
        "intelligence": intel_w,
        "speed": speed_w,
        "agentic": 0.15,
        "coding": 0.15,
    }
    # Normalize to 1.0
    total = sum(axis_weights.values())
    if total > 0:
        axis_weights = {k: v / total for k, v in axis_weights.items()}
    
    # Score all models with these weights
    best_model = None
    best_score = -1
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
            "has_reasoning": False,
            "context_window": (m.get("ctx_k", 0) or 0) * 1024,
            "knowledge": "",
            "release_date": "",
            "benchmark_swe_verified": m.get("benchmark_swe_verified"),
            "price_blended": m.get("price_blended"),
            "arch": m.get("arch", ""),
        }
        
        # Gate checks
        if slot_def.get("needs_tools", False) and not md["has_tools"]:
            continue
        if slot_def.get("needs_vision", False) and not md["has_vision_capability"]:
            continue
        if slot_def.get("min_tps", 0) > 0 and md["tps"] < slot_def["min_tps"]:
            continue
        if slot_def.get("min_ai", 0) > 0 and (md["ai_index"] or 0) < slot_def["min_ai"]:
            continue
        
        engine = ScoringEngine(md, benchmarks)
        scores = engine.compute_all()
        # Use varying weights to test what GS prefers
        composite = scores.composite(axis_weights)
        
        if composite > best_score:
            best_score = composite
            best_model = md["model_id"]
    
    match = best_model == gs_primary
    fuzzy = False
    if not match and best_model and gs_primary:
        gs_prefix = gs_primary.split(":")[0].split("/")[-1]
        auto_prefix = best_model.split(":")[0].split("/")[-1]
        fuzzy = gs_prefix == auto_prefix or (
            gs_primary.replace("-free", "") == best_model.replace("-free", "")
        )
    
    return {
        "slot_id": slot_id,
        "intel_w": round(intel_w, 2),
        "speed_w": round(speed_w, 2),
        "rel_w": round(rel_w, 2),
        "best_model": best_model,
        "best_score": round(best_score * 100, 1),
        "exact_match": match,
        "fuzzy_match": fuzzy,
        "gs_primary": gs_primary,
    }


def optimize_slot(slot_id: str, slot_def: dict, models: list[dict],
                  gs_primary: str) -> dict:
    """Grid search over weights for a single slot."""
    results = []
    grid_range = [round(x, 1) for x in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
    
    for intel_w, speed_w in itertools.product(grid_range, grid_range):
        rel_w = 1.0 - intel_w - speed_w
        if rel_w < -0.01:
            continue
        
        r = _eval_combo(slot_id, slot_def, models, gs_primary, intel_w, speed_w)
        results.append(r)
    
    # Sort: exact matches first, then by score descending
    results.sort(key=lambda r: (r["exact_match"], r["fuzzy_match"], r["best_score"]), reverse=True)
    
    best = results[0] if results else None
    exact_matches = [r for r in results if r["exact_match"]]
    best_exact = exact_matches[0] if exact_matches else None
    
    return {
        "slot_id": slot_id,
        "label": slot_def.get("label", slot_id),
        "gs_primary": gs_primary,
        "grid_size": len(results),
        "exact_match_count": len(exact_matches),
        "best_overall": best,
        "best_exact_match": best_exact,
        "weight_range_for_match": {
            "intel_min": min((r["intel_w"] for r in exact_matches), default=None),
            "intel_max": max((r["intel_w"] for r in exact_matches), default=None),
            "speed_min": min((r["speed_w"] for r in exact_matches), default=None),
            "speed_max": max((r["speed_w"] for r in exact_matches), default=None),
        } if exact_matches else None,
        "top_5": results[:5],
    }


def main():
    """Run auto-optimization."""
    print("┌─ Auto-Optimization Loop ──────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└────────────────────────────────────────────────────")
    
    print("  Loading gold standard...")
    gold = load_gold_standard()
    if not gold:
        print("  ✗ No gold standard. Run --gold-standard first.")
        return 1
    print(f"  ✓ {len(gold.get('slots', {}))} slots")
    
    print("  Loading slot definitions...")
    slot_defs = load_slots()
    print(f"  ✓ {len(slot_defs)} slot defs")
    
    print("  Loading models...")
    models = load_models()
    print(f"  ✓ {len(models)} models")
    
    print("  Running grid search per slot...")
    results = {}
    for slot_id, gs_slot in gold.get("slots", {}).items():
        gs_primary = gs_slot.get("primary", {}).get("model_id") if gs_slot.get("primary") else None
        if not gs_primary:
            print(f"    {slot_id:20s}  ⚠ no gold standard primary, skipping")
            continue
        
        sdef = slot_defs.get(slot_id, {})
        print(f"    {slot_id:20s}  grid search (121 combinations)...", end=" ")
        sys.stdout.flush()
        
        result = optimize_slot(slot_id, sdef, models, gs_primary)
        results[slot_id] = result
        
        best = result["best_overall"]
        match_info = "✅ exact" if best.get("exact_match") else ("🔶 fuzzy" if best.get("fuzzy_match") else "❌")
        print(f"{match_info}  i={best['intel_w']} s={best['speed_w']} r={best['rel_w']} → {best['best_model']} ({best['best_score']})")
    
    # Aggregate
    output = {
        "generated_at": datetime.now().isoformat(),
        "scan_id": gold.get("scan_id"),
        "slots_evaluated": len(results),
        "per_slot": results,
        "summary": {
            "slots_with_exact_match": sum(1 for v in results.values() if v["best_overall"] and v["best_overall"]["exact_match"]),
            "slots_with_fuzzy_match": sum(1 for v in results.values() if v["best_overall"] and v["best_overall"]["fuzzy_match"]),
            "total_slots": len(results),
        },
    }
    
    # Write output
    json_path = OUTPUT_DIR / f"optimization_{output['scan_id']}.json"
    json_path.write_text(json.dumps(output, indent=2, default=str))
    
    print(f"\n  Output: {json_path.name}")
    print(f"  Slots with exact match:  {output['summary']['slots_with_exact_match']}/{output['summary']['total_slots']}")
    print(f"  Slots with fuzzy match:  {output['summary']['slots_with_fuzzy_match']}/{output['summary']['total_slots']}")
    
    # Show best weights per slot
    print(f"\n  Recommended weights:")
    for slot_id, r in sorted(results.items()):
        best = r["best_overall"]
        if best["exact_match"]:
            print(f"    {slot_id:20s}  ✅ i={best['intel_w']} s={best['speed_w']} r={best['rel_w']}")
        elif best["fuzzy_match"]:
            print(f"    {slot_id:20s}  🔶 i={best['intel_w']} s={best['speed_w']} r={best['rel_w']}")
        else:
            print(f"    {slot_id:20s}  ❌ best: i={best['intel_w']} s={best['speed_w']} r={best['rel_w']} → {best['best_model']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
