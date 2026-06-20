#!/usr/bin/env python3
"""
Conditional Scoring Engine — estimates AI Index from architecture + params + release date.

Used when AA data is missing. Takes models.dev data and produces estimated scores.

Usage:
    from scoring.arch_predictor import predict_ai_index
    score = predict_ai_index({
        "family": "glm",
        "parameters": "32B",
        "release_date": "2025-12-01",
        "reasoning": true,
    })
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODELS_DEV_CACHE = Path.home() / ".hermes" / "models_dev_cache.json"
OUTPUT_FILE = Path(__file__).parent / "arch_scores.json"

# ── Architecture baselines ────────────────────────────────────────────────
# Base AI Index by model family, calibrated against known AA scores.
# These are starting points that get adjusted by size, recency, and features.

FAMILY_BASELINES = {
    # Verified from AA cache (RECALIBRATED 2026-06-19)
    "minimax": {"base_ai": 44.4, "size_scale": "linear", "note": "MiniMax-M3, dropped from 54.7"},
    "deepseek": {"base_ai": 40.3, "size_scale": "log", "note": "V4 Flash, dropped from 46.5"},
    "mimo": {"base_ai": 40.1, "size_scale": "linear", "note": "V2.5, dropped from 49.0"},
    "nemotron": {"base_ai": 37.8, "size_scale": "log", "note": "Ultra 550B, dropped from 47.7"},
    "qwen": {"base_ai": 39.6, "size_scale": "log", "note": "3.6-Plus, dropped from 50.0"},
    "gemma": {"base_ai": 29.4, "size_scale": "linear", "note": "4-31B, dropped from 39.2"},
    "glm": {"base_ai": 40.2, "size_scale": "log", "note": "5.1 (40.2). 5.2 is 51.1 but PAID"},
    "kimi": {"base_ai": 42.8, "size_scale": "log", "note": "K2.6, dropped from 53.9"},
    "stepfun": {"base_ai": 29.7, "size_scale": "log", "note": "3.7 Flash (29.7, 398 TPS)"},
    "llama": {"base_ai": 42.0, "size_scale": "log", "note": "estimated from public benchmarks"},
    "claude": {"base_ai": 70.0, "size_scale": "log", "note": "Anthropic top tier"},
    "gpt": {"base_ai": 68.0, "size_scale": "log", "note": "OpenAI top tier"},
    "gemini": {"base_ai": 65.0, "size_scale": "log", "note": "Google top tier"},
    "grok": {"base_ai": 55.0, "size_scale": "log", "note": "xAI estimated"},
    "mistral": {"base_ai": 48.0, "size_scale": "log", "note": "estimated"},
    "cohere": {"base_ai": 35.0, "size_scale": "linear", "note": "estimated"},
    "stepfun": {"base_ai": 45.0, "size_scale": "log", "note": "user says punches above weight"},
    "yi": {"base_ai": 44.0, "size_scale": "log", "note": "estimated"},
    "internlm": {"base_ai": 43.0, "size_scale": "log", "note": "estimated"},
    "phi": {"base_ai": 40.0, "size_scale": "linear", "note": "Microsoft small models"},
}

# Size multipliers (approximate, based on scaling laws)
SIZE_MULTIPLIERS = {
    # Small models (< 10B)
    "1b": 0.55, "3b": 0.60, "7b": 0.65, "8b": 0.67, "9b": 0.68,
    # Medium models (10B-40B)
    "12b": 0.72, "14b": 0.74, "27b": 0.80, "30b": 0.82, "32b": 0.83,
    # Large models (40B-100B)
    "40b": 0.85, "70b": 0.90, "72b": 0.91, "8b": 0.67,
    # XL models (100B+)
    "110b": 0.95, "120b": 0.96, "200b": 0.98, "253b": 0.99,
    "405b": 1.00, "550b": 1.02, "600b": 1.03, "1t": 1.05,
}


def parse_params(params_str: str | None) -> float | None:
    """Parse parameter count string to billions."""
    if not params_str:
        return None
    params_str = str(params_str).lower().strip()
    # Handle "32B", "32b", "32B-A3B" (MoE), etc.
    match = re.match(r'(\d+\.?\d*)\s*([bmtk])', params_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2)
        if unit == 't':
            return num * 1000
        if unit == 'b':
            return num
        if unit == 'm':
            return num / 1000
        if unit == 'k':
            return num / 1000000
    # Handle "32B-A3B" MoE format — use total params
    match = re.match(r'(\d+\.?\d*)b.*?(\d+\.?\d*)b', params_str)
    if match:
        return float(match.group(1))
    return None


def get_size_multiplier(params_b: float | None) -> float:
    """Get size multiplier from parameter count."""
    if params_b is None:
        return 0.80  # Default for unknown size
    if params_b >= 400:
        return 1.00
    if params_b >= 200:
        return 0.98
    if params_b >= 100:
        return 0.95
    if params_b >= 70:
        return 0.90
    if params_b >= 40:
        return 0.85
    if params_b >= 30:
        return 0.82
    if params_b >= 20:
        return 0.78
    if params_b >= 14:
        return 0.74
    if params_b >= 12:
        return 0.72
    if params_b >= 8:
        return 0.67
    if params_b >= 7:
        return 0.65
    if params_b >= 3:
        return 0.60
    return 0.55


def recency_adjustment(release_date: str | None) -> float:
    """Adjust score based on release date. Newer models tend to be better."""
    if not release_date:
        return 0.0
    try:
        dt = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_old = (now - dt).days
        if days_old < 30:
            return 3.0   # Very new — boost
        if days_old < 90:
            return 2.0   # Recent — small boost
        if days_old < 180:
            return 1.0   # Somewhat recent
        if days_old < 365:
            return 0.0   # Year old — neutral
        return -2.0      # Old — slight penalty
    except Exception:
        return 0.0


def reasoning_adjustment(is_reasoning: bool) -> float:
    """Reasoning models typically score higher on intelligence benchmarks."""
    return 2.0 if is_reasoning else 0.0


def multimodal_adjustment(has_vision: bool) -> float:
    """Multimodal models may trade off some text intelligence."""
    return -1.0 if has_vision else 0.0


def predict_ai_index(model_info: dict) -> dict:
    """
    Predict AI Index from model metadata.

    Args:
        model_info: dict with keys like family, parameters, release_date,
                    reasoning, attachment (vision), etc.

    Returns:
        dict with predicted_ai, confidence, breakdown
    """
    family = (model_info.get("family") or model_info.get("model_family") or "").lower()
    params_str = model_info.get("parameters") or model_info.get("params") or model_info.get("size")
    release_date = model_info.get("release_date") or model_info.get("created_at")
    is_reasoning = model_info.get("reasoning", False)
    has_vision = model_info.get("attachment", False) or model_info.get("vision", False)

    # Find family baseline
    baseline_info = None
    for fam_key, fam_data in FAMILY_BASELINES.items():
        if fam_key in family or family.startswith(fam_key):
            baseline_info = fam_data
            break

    if baseline_info is None:
        # Unknown family — conservative estimate
        return {
            "predicted_ai": 30.0,
            "confidence": "low",
            "breakdown": {
                "reason": f"unknown family '{family}'",
                "base": 30.0,
            },
            "model_info": model_info,
        }

    base = baseline_info["base_ai"]
    params_b = parse_params(params_str)
    size_mult = get_size_multiplier(params_b)
    recency = recency_adjustment(release_date)
    reasoning = reasoning_adjustment(is_reasoning)
    multimodal = multimodal_adjustment(has_vision)

    predicted = base * size_mult + recency + reasoning + multimodal
    predicted = max(5.0, min(100.0, predicted))

    # Confidence based on data availability
    confidence = "medium"
    if params_b and release_date:
        confidence = "high"
    elif params_b or release_date:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "predicted_ai": round(predicted, 1),
        "confidence": confidence,
        "breakdown": {
            "family": family,
            "base_ai": base,
            "params_b": params_b,
            "size_multiplier": round(size_mult, 3),
            "recency_adjustment": recency,
            "reasoning_adjustment": reasoning,
            "multimodal_adjustment": multimodal,
            "family_note": baseline_info.get("note", ""),
        },
        "model_info": model_info,
    }


def scan_models_dev() -> list[dict]:
    """Scan models.dev cache and predict AI Index for all models."""
    if not MODELS_DEV_CACHE.exists():
        print(f"No models.dev cache at {MODELS_DEV_CACHE}")
        return []

    cache = json.loads(MODELS_DEV_CACHE.read_text())
    results = []

    for provider_key, provider_data in cache.items():
        if not isinstance(provider_data, dict):
            continue
        models = provider_data.get("models", {})
        for model_id, model_data in models.items():
            if not isinstance(model_data, dict):
                continue

            prediction = predict_ai_index(model_data)
            prediction["model_id"] = model_id
            prediction["provider"] = provider_key
            results.append(prediction)

    # Sort by predicted AI
    results.sort(key=lambda x: -x["predicted_ai"])
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Conditional Scoring Engine")
    parser.add_argument("--scan", action="store_true", help="Scan models.dev cache")
    parser.add_argument("--model", help="Predict for specific model ID")
    parser.add_argument("--family", help="Predict for a model family")
    parser.add_argument("--list-families", action="store_true", help="List known families")
    args = parser.parse_args()

    if args.list_families:
        print("\nKnown model families and baselines:")
        for fam, data in sorted(FAMILY_BASELINES.items()):
            print(f"  {fam:15s} — AI baseline: {data['base_ai']:.1f} — {data['note']}")
        print()
        return

    if args.family:
        result = predict_ai_index({"family": args.family})
        print(json.dumps(result, indent=2))
        return

    if args.scan:
        results = scan_models_dev()
        print(f"\nScanned {len(results)} models from models.dev cache")
        print(f"\nTop 20 by predicted AI Index:")
        for r in results[:20]:
            conf = r["confidence"][:1].upper()
            print(f"  [{conf}] {r['predicted_ai']:5.1f}  {r['model_id']:40s}  ({r['provider']})")

        # Save to file
        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_count": len(results),
            "predictions": {r["model_id"]: r for r in results},
        }
        OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\nSaved to {OUTPUT_FILE}")
        return

    # Default: show usage
    parser.print_help()


if __name__ == "__main__":
    main()
