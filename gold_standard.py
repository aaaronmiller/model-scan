"""
model-scan — Gold Standard Config Generation

Generates optimal Hermes config patches using the multi-axis scoring engine.
Each recommendation includes full reasoning traces explaining WHY a model
was chosen. Output is consumed by the CPMR (Config Patch Match Rate) system
to evaluate convergence.

Output formats:
  - JSON: machine-readable with full trace data
  - YAML: directly applicable to ~/.hermes/config.yaml
  - Markdown: human-readable report with reasoning
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import scoring engine
sys.path.insert(0, str(Path(__file__).parent))
from scoring.engine import ScoringEngine, load_benchmarks

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
SLOTS_PATH = CONFIG_DIR / "slot_definitions.yaml"
OUTPUT_DIR = CONFIG_DIR / "gold_standard"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Weight profile for composite scoring — optimized for Hermes agent usage
COMPOSITE_WEIGHTS = {
    "intelligence": 0.40,
    "speed": 0.20,
    "agentic": 0.20,
    "coding": 0.20,
}


def load_slots() -> dict:
    """Load slot definitions from YAML."""
    try:
        import yaml
        return yaml.safe_load(open(SLOTS_PATH)) or {}
    except Exception as e:
        print(f"  ⚠ Warning: Could not load slots: {e}")
        return {}


def load_latest_scan() -> tuple[int | None, list[dict]]:
    """Load latest scan models from SQLite."""
    if not DB_PATH.exists():
        return None, []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT MAX(scan_id) FROM scans")
    scan_id = cur.fetchone()[0]
    if not scan_id:
        conn.close()
        return None, []
    cur = conn.execute(
        "SELECT * FROM models WHERE scan_id = ? AND accessible = 1 ORDER BY composite DESC",
        (scan_id,)
    )
    models = [dict(r) for r in cur.fetchall()]
    conn.close()
    return scan_id, models


def score_model_for_slot(m: dict, slot_def: dict, benchmarks: dict) -> dict:
    """Score a model for a specific slot using multi-axis engine."""
    # Prepare model data for scoring engine
    model_data = {
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
    
    engine = ScoringEngine(model_data, benchmarks)
    scores = engine.compute_all()
    composite = scores.composite(COMPOSITE_WEIGHTS)
    
    # Apply slot-specific gate checks
    gates_passed = []
    gates_failed = []
    needs_tools = slot_def.get("needs_tools", False)
    needs_vision = slot_def.get("needs_vision", False)
    min_ai = slot_def.get("min_ai", 0)
    min_tps = slot_def.get("min_tps", 0)
    max_lat = slot_def.get("max_latency_s", 99)
    
    if needs_tools and not model_data["has_tools"]:
        gates_failed.append("needs_tools")
    else:
        gates_passed.append("tools" if needs_tools else "no-tools-req")
    
    if needs_vision and not model_data["has_vision_capability"]:
        gates_failed.append("needs_vision")
    else:
        gates_passed.append("vision" if needs_vision else "no-vision-req")
    
    if min_ai > 0 and (model_data["ai_index"] or 0) < min_ai:
        gates_failed.append(f"ai<{min_ai}")
    else:
        gates_passed.append(f"ai>={min_ai}")
    
    if min_tps > 0 and model_data["tps"] < min_tps:
        gates_failed.append(f"tps<{min_tps}")
    else:
        gates_passed.append(f"tps>={min_tps}")
    
    if max_lat < 99 and model_data["latency_s"] > max_lat:
        gates_failed.append(f"lat>{max_lat}s")
    else:
        gates_passed.append(f"lat<={max_lat}s")
    
    return {
        "model_id": model_data["model_id"],
        "provider": model_data["provider"],
        "composite": round(composite, 1),
        "scores": scores.to_dict(),
        "gates_passed": gates_passed,
        "gates_failed": gates_failed,
        "qualified": len(gates_failed) == 0,
    }


def generate_gold_standard() -> dict:
    """Generate gold standard config recommendations for all slots."""
    print("  Loading scan data...")
    scan_id, models = load_latest_scan()
    if not models:
        return {"error": "No scan data found", "generated_at": datetime.now().isoformat()}
    
    print(f"  Loaded {len(models)} models from scan #{scan_id}")
    print("  Loading benchmarks...")
    benchmarks = load_benchmarks()
    print(f"  Loaded {len(benchmarks)} benchmark sources")
    
    print("  Loading slot definitions...")
    slot_defs = load_slots()
    print(f"  Loaded {len(slot_defs)} slots")
    
    print("  Scoring models per slot...")
    results = {}
    for slot_id, sdef in slot_defs.items():
        label = sdef.get("label", slot_id)
        print(f"    {slot_id} ({label})...")
        
        candidates = []
        for m in models:
            result = score_model_for_slot(m, sdef, benchmarks)
            if result["qualified"]:
                candidates.append(result)
        
        candidates.sort(key=lambda c: c["composite"], reverse=True)
        top3 = candidates[:3]
        
        results[slot_id] = {
            "label": label,
            "requirements": {
                "min_ai": sdef.get("min_ai"),
                "min_tps": sdef.get("min_tps"),
                "max_latency_s": sdef.get("max_latency_s"),
                "needs_tools": sdef.get("needs_tools", False),
                "needs_vision": sdef.get("needs_vision", False),
            },
            "candidates_count": len(candidates),
            "top_3": top3,
            "primary": top3[0] if top3 else None,
            "fallback_1": top3[1] if len(top3) > 1 else None,
            "fallback_2": top3[2] if len(top3) > 2 else None,
        }
    
    return {
        "generated_at": datetime.now().isoformat(),
        "scan_id": scan_id,
        "models_evaluated": len(models),
        "slots": results,
        "weights": COMPOSITE_WEIGHTS,
    }


def format_yaml_patch(data: dict) -> str:
    """Format gold standard as a YAML config patch."""
    lines = [
        "# ═══════════════════════════════════════════════════════════════════════════",
        f"# model-scan GOLD STANDARD — {data['generated_at']}",
        f"# Evaluated {data['models_evaluated']} models across {len(data['slots'])} slots",
        "# ═══════════════════════════════════════════════════════════════════════════",
        "",
        "# ── SLOT RECOMMENDATIONS ──────────────────────────────────────────────",
    ]
    
    for slot_id, slot in data["slots"].items():
        lines.append(f"")
        lines.append(f"# === {slot_id}: {slot['label']} ===")
        lines.append(f"# Requirements: AI>={slot['requirements']['min_ai']} TPS>={slot['requirements']['min_tps']} "
                     f"Lat<={slot['requirements']['max_latency_s']}s "
                     f"{'Tools' if slot['requirements']['needs_tools'] else ''} "
                     f"{'Vision' if slot['requirements']['needs_vision'] else ''}")
        lines.append(f"# Candidates: {slot['candidates_count']} qualified models")
        
        primary = slot["primary"]
        if primary:
            lines.append(f"")
            lines.append(f"# ── PRIMARY ─────────────────────────────────────────")
            lines.append(f"# Model:     {primary['model_id']}")
            lines.append(f"# Provider:  {primary['provider']}")
            lines.append(f"# Score:     {primary['composite']}")
            tr = primary['scores']['traces']
            lines.append(f"# Reasoning:")
            lines.append(f"#   {tr['intelligence']}")
            lines.append(f"#   {tr['speed']}")
            lines.append(f"#   {tr['agentic']}")
            lines.append(f"#   {tr['coding']}")
            
            # Fallbacks
            for i, fb in enumerate([slot["fallback_1"], slot["fallback_2"]]):
                if fb:
                    lines.append(f"# ── FALLBACK {i+1} ───────────────────────────────")
                    lines.append(f"# Model:     {fb['model_id']}")
                    lines.append(f"# Provider:  {fb['provider']}")
                    lines.append(f"# Score:     {fb['composite']}")
            
            # Config entry
            lines.append(f"")
            lines.append(f"# Recommended config entry for {slot_id}:")
            if slot_id.startswith("R"):
                lines.append(f"# {slot_id}:")
                lines.append(f"#   provider: custom")
                lines.append(f"#   model: {primary['model_id']}")
                lines.append(f"#   base_url: # provider endpoint")
        else:
            lines.append(f"#   ⚠ No qualified candidates found")
    
    return "\n".join(lines)


def format_markdown_report(data: dict) -> str:
    """Format gold standard as a markdown report."""
    lines = [
        f"# Gold Standard Config — {data['generated_at'][:10]}",
        f"",
        f"**Scan #{data['scan_id']}** | **{data['models_evaluated']} models** | **{len(data['slots'])} slots**",
        f"",
        f"## Weight Profile",
        f"| Axis | Weight |",
        f"|------|--------|",
    ]
    for axis, weight in data["weights"].items():
        lines.append(f"| {axis.title()} | {weight:.0%} |")
    lines.append(f"")
    
    for slot_id, slot in data["slots"].items():
        lines.append(f"## {slot_id}: {slot['label']}")
        lines.append(f"")
        lines.append(f"| Rank | Model | Provider | Score |")
        lines.append(f"|------|-------|----------|-------|")
        
        for i, cand in enumerate([slot["primary"], slot["fallback_1"], slot["fallback_2"]]):
            if cand:
                rank = "★ Primary" if i == 0 else f"  Fallback {i}"
                lines.append(f"| {rank} | {cand['model_id']} | {cand['provider']} | {cand['composite']} |")
        
        lines.append(f"")
        if slot["primary"]:
            tr = slot["primary"]["scores"]["traces"]
            lines.append(f"### Reasoning for {slot['primary']['model_id']}")
            lines.append(f"")
            lines.append(f"- {tr['intelligence']}")
            lines.append(f"- {tr['speed']}")
            lines.append(f"- {tr['agentic']}")
            lines.append(f"- {tr['coding']}")
        lines.append(f"")
    
    return "\n".join(lines)


def main():
    """Run gold standard generation."""
    print(f"┌─ Gold Standard Generator ──────────────────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"└────────────────────────────────────────────────────────")
    
    data = generate_gold_standard()
    
    if "error" in data:
        print(f"\n  ✗ {data['error']}")
        return 1
    
    # Write JSON
    json_path = OUTPUT_DIR / f"gold_standard_{data['scan_id']}.json"
    json_path.write_text(json.dumps(data, indent=2, default=str))
    
    # Write YAML patch
    yaml_patch = format_yaml_patch(data)
    yaml_path = OUTPUT_DIR / f"patch_{data['scan_id']}.yaml"
    yaml_path.write_text(yaml_patch)
    
    # Write markdown report
    md_report = format_markdown_report(data)
    md_path = OUTPUT_DIR / f"report_{data['scan_id']}.md"
    md_path.write_text(md_report)
    
    primary_count = sum(1 for s in data["slots"].values() if s["primary"])
    total_candidates = sum(s["candidates_count"] for s in data["slots"].values())
    
    print(f"\n  ✓ Gold standard generated")
    print(f"  ├─ {len(data['slots'])} slots evaluated")
    print(f"  ├─ {primary_count} slots with primary recommendations")
    print(f"  ├─ {total_candidates} total qualified candidates")
    print(f"  ├─ json:  {json_path.name}")
    print(f"  ├─ yaml:  {yaml_path.name}")
    print(f"  └─ md:    {md_path.name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
