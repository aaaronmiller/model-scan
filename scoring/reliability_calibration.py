#!/usr/bin/env python3
"""
Reliability Calibration — cross-references model scores with real API error rates.

Reads Hermes logs and model-scan probe data to compute reliability scores.
Used to adjust model rankings based on real-world failure rates.

Usage:
    python3 scoring/reliability_calibration.py              # analyze all
    python3 scoring/reliability_calibration.py --model deepseek  # one model
    python3 scoring/reliability_calibration.py --summary    # quick summary
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERMES_LOGS = Path.home() / ".hermes" / "logs"
MODEL_SCAN_DB = Path.home() / ".config" / "model-scan" / "model_scan.db"
OUTPUT_FILE = Path(__file__).parent / "reliability_scores.json"

# Error patterns to look for in logs
ERROR_PATTERNS = [
    (r"rate.?limit|429|too many requests", "rate_limit"),
    (r"503|service.?unavailable|overloaded", "service_unavailable"),
    (r"502|bad.?gateway", "bad_gateway"),
    (r"timeout|timed.?out|deadline.?exceeded", "timeout"),
    (r"connection.?error|connect.?refused|econnrefused", "connection_error"),
    (r"401|unauthorized|invalid.?key|authentication", "auth_error"),
    (r"400|bad.?request|invalid.?request", "bad_request"),
    (r"500|internal.?server.?error", "internal_error"),
    (r"context.?length|token.?limit|too.?long", "context_overflow"),
    (r"model.?not.?found|unknown.?model", "model_not_found"),
]


def parse_log_file(log_path: Path) -> list[dict]:
    """Parse a Hermes log file for model usage and errors."""
    entries = []
    try:
        text = log_path.read_text(errors="replace")
    except Exception:
        return entries

    # Look for model references and errors
    for line in text.split("\n"):
        if not line.strip():
            continue

        # Try to extract model name
        model_match = re.search(r'"model"\s*:\s*"([^"]+)"', line)
        model = model_match.group(1) if model_match else None

        # Check for errors
        for pattern, error_type in ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                entries.append({
                    "model": model or "unknown",
                    "error_type": error_type,
                    "line": line[:200],
                    "file": str(log_path),
                })
                break

    return entries


def analyze_probe_data() -> dict:
    """Analyze reliability from model-scan probe data."""
    if not MODEL_SCAN_DB.exists():
        return {}

    conn = sqlite3.connect(str(MODEL_SCAN_DB))
    conn.row_factory = sqlite3.Row

    try:
        # Get latest scan's probe results
        rows = conn.execute("""
            SELECT model_id, provider,
                   tps, latency_s, reliability_pct,
                   error_count, total_probes
            FROM models
            WHERE scan_id = (SELECT MAX(scan_id) FROM scans)
            AND total_probes > 0
        """).fetchall()
    except Exception:
        conn.close()
        return {}

    conn.close()

    results = {}
    for row in rows:
        model_id = row["model_id"]
        total = row["total_probes"] or 1
        errors = row["error_count"] or 0
        success_rate = ((total - errors) / total) * 100 if total > 0 else 0

        results[model_id] = {
            "provider": row["provider"],
            "tps": row["tps"],
            "latency_s": row["latency_s"],
            "reliability_pct": row["reliability_pct"],
            "probe_success_rate": round(success_rate, 1),
            "total_probes": total,
            "error_count": errors,
        }

    return results


def compute_reliability_score(error_count: int, total_calls: int, error_types: dict) -> dict:
    """Compute a 0-100 reliability score from error data."""
    if total_calls == 0:
        return {"score": 50.0, "confidence": "none", "reason": "no data"}

    base_rate = (total_calls - error_count) / total_calls * 100

    # Weight errors by severity
    severity_weights = {
        "rate_limit": 0.3,        # Temporary, recoverable
        "service_unavailable": 0.4,
        "bad_gateway": 0.4,
        "timeout": 0.5,           # Annoying but not fatal
        "connection_error": 0.6,
        "auth_error": 1.0,        # Fatal — model won't work
        "bad_request": 0.2,       # Usually client error
        "internal_error": 0.7,
        "context_overflow": 0.3,  # Can be worked around
        "model_not_found": 1.0,   # Fatal
    }

    weighted_errors = sum(
        count * severity_weights.get(etype, 0.5)
        for etype, count in error_types.items()
    )
    severity_rate = weighted_errors / total_calls * 100 if total_calls > 0 else 0

    score = base_rate - severity_rate * 0.5
    score = max(0.0, min(100.0, score))

    confidence = "high" if total_calls >= 100 else "medium" if total_calls >= 20 else "low"

    return {
        "score": round(score, 1),
        "confidence": confidence,
        "base_success_rate": round(base_rate, 1),
        "severity_penalty": round(severity_rate * 0.5, 1),
        "total_calls": total_calls,
        "error_count": error_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Reliability Calibration")
    parser.add_argument("--model", help="Analyze specific model")
    parser.add_argument("--summary", action="store_true", help="Quick summary")
    parser.add_argument("--logs", help="Specific log directory")
    args = parser.parse_args()

    print("\nReliability Calibration")
    print("=" * 60)

    # 1. Analyze probe data
    probe_data = analyze_probe_data()
    if probe_data:
        print(f"\nProbe data: {len(probe_data)} models with probe results")
    else:
        print("\nNo probe data available in model-scan DB")

    # 2. Analyze Hermes logs
    log_dir = Path(args.logs) if args.logs else HERMES_LOGS
    log_errors = defaultdict(lambda: defaultdict(int))
    log_total = defaultdict(int)

    if log_dir.exists():
        log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.jsonl"))
        print(f"Scanning {len(log_files)} log files in {log_dir}...")
        for lf in log_files[:50]:  # Limit to avoid long runtime
            for entry in parse_log_file(lf):
                model = entry["model"]
                log_errors[model][entry["error_type"]] += 1
                log_total[model] += 1
        print(f"  Found errors in {len(log_errors)} models")
    else:
        print(f"No log directory at {log_dir}")

    # 3. Combine and output
    all_models = set(list(probe_data.keys()) + list(log_errors.keys()))
    results = {}

    for model in sorted(all_models):
        probe = probe_data.get(model, {})
        errors = dict(log_errors.get(model, {}))
        total_errors = sum(errors.values())
        total_calls = max(probe.get("total_probes", 0), log_total.get(model, 0))

        reliability = compute_reliability_score(total_errors, total_calls, errors)

        results[model] = {
            "reliability_score": reliability["score"],
            "confidence": reliability["confidence"],
            "probe_data": probe,
            "log_errors": errors,
        }

    if args.model:
        matches = {k: v for k, v in results.items() if args.model.lower() in k.lower()}
        if matches:
            for model, data in matches.items():
                print(f"\n{model}:")
                print(f"  Reliability score: {data['reliability_score']:.1f}/100")
                print(f"  Confidence: {data['confidence']}")
                if data['probe_data']:
                    print(f"  Probe success rate: {data['probe_data'].get('probe_success_rate', 'N/A')}%")
                if data['log_errors']:
                    print(f"  Log errors: {data['log_errors']}")
        else:
            print(f"\nNo data for model matching '{args.model}'")
        return

    if args.summary:
        print(f"\nReliability Summary ({len(results)} models):")
        print(f"{'Model':50s} {'Score':>6s} {'Conf':>5s}")
        print("-" * 65)
        for model, data in sorted(results.items(), key=lambda x: -x[1]["reliability_score"]):
            print(f"  {model:48s} {data['reliability_score']:5.1f}  {data['confidence']:>5s}")
    else:
        # Save full results
        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_count": len(results),
            "scores": results,
        }
        OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\nSaved reliability scores to {OUTPUT_FILE}")

        # Show top/bottom
        if results:
            sorted_results = sorted(results.items(), key=lambda x: -x[1]["reliability_score"])
            print(f"\nMost reliable:")
            for model, data in sorted_results[:5]:
                print(f"  {data['reliability_score']:5.1f}  {model}")
            print(f"\nLeast reliable:")
            for model, data in sorted_results[-5:]:
                print(f"  {data['reliability_score']:5.1f}  {model}")


if __name__ == "__main__":
    main()
