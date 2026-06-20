#!/usr/bin/env python3
"""
Paper Benchmark Extractor — extracts benchmark tables from model release papers.

Target models: Kimi K2.6, GLM 5.2, Qwen 3.7, MiniMax M3
Output: scoring/paper_benchmarks_data.json

Usage:
    python3 scoring/paper_benchmarks.py              # extract all
    python3 scoring/paper_benchmarks.py --model kimi  # extract one
    python3 scoring/paper_benchmarks.py --list        # show available data
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime

DATA_FILE = Path(__file__).parent / "paper_benchmarks_data.json"

# ── Known benchmark sources ────────────────────────────────────────────────
# These are the models we need to find papers for and the benchmarks to extract.
# Format: model_name -> { paper_url, arxiv_id, benchmarks_to_extract }

TARGET_MODELS = {
    "kimi-k2.6": {
        "full_name": "Kimi K2.6",
        "creator": "Moonshot AI",
        "arxiv_id": None,  # Will be filled by research
        "paper_url": None,
        "known_benchmarks": [
            "MMLU", "MMLU-Pro", "GPQA", "HumanEval", "MBPP",
            "MATH", "AIME", "LiveCodeBench", "SWE-bench",
            "BFCL", "Terminal-Bench", "Arena ELO",
        ],
    },
    "glm-5.2": {
        "full_name": "GLM 5.2",
        "creator": "Zhipu AI",
        "arxiv_id": None,
        "paper_url": None,
        "known_benchmarks": [
            "MMLU", "MMLU-Pro", "GPQA", "HumanEval", "MBPP",
            "MATH", "AIME", "LiveCodeBench", "SWE-bench",
            "BFCL", "Arena ELO",
        ],
    },
    "qwen-3.7": {
        "full_name": "Qwen 3.7",
        "creator": "Alibaba",
        "arxiv_id": None,
        "paper_url": None,
        "known_benchmarks": [
            "MMLU", "MMLU-Pro", "GPQA", "HumanEval", "MBPP",
            "MATH", "AIME", "LiveCodeBench", "SWE-bench",
            "BFCL", "Arena ELO",
        ],
    },
    "minimax-m3": {
        "full_name": "MiniMax M3",
        "creator": "MiniMax",
        "arxiv_id": None,
        "paper_url": None,
        "known_benchmarks": [
            "MMLU", "MMLU-Pro", "GPQA", "HumanEval", "MBPP",
            "MATH", "AIME", "LiveCodeBench", "SWE-bench",
            "BFCL", "Arena ELO",
        ],
    },
}

# ── Benchmark normalization ────────────────────────────────────────────────
# Maps various benchmark names to canonical forms
BENCHMARK_ALIASES = {
    "mmlu_pro": "MMLU-Pro",
    "mmlu-pro": "MMLU-Pro",
    "mmlu": "MMLU",
    "gpqa_diamond": "GPQA-Diamond",
    "gpqa": "GPQA",
    "humaneval": "HumanEval",
    "human_eval": "HumanEval",
    "mbpp": "MBPP",
    "mbpp_plus": "MBPP+",
    "math": "MATH",
    "math_500": "MATH-500",
    "aime_2024": "AIME-2024",
    "aime_2025": "AIME-2025",
    "aime": "AIME",
    "livecodebench": "LiveCodeBench",
    "live_code_bench": "LiveCodeBench",
    "swe_bench": "SWE-bench",
    "swe-bench": "SWE-bench",
    "swe-bench-verified": "SWE-bench-Verified",
    "bfcl": "BFCL",
    "terminal-bench": "Terminal-Bench",
    "terminal_bench": "Terminal-Bench",
    "arena_elo": "Arena ELO",
    "chatbot_arena": "Arena ELO",
    "scicode": "SciCode",
}


def normalize_benchmark(name: str) -> str:
    """Normalize benchmark name to canonical form."""
    key = name.lower().strip().replace(" ", "_").replace("-", "_")
    return BENCHMARK_ALIASES.get(key, BENCHMARK_ALIASES.get(name.lower().strip(), name))


def normalize_score(value) -> float | None:
    """Normalize a score to 0-100 scale if possible."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().rstrip("%").rstrip("×")
        try:
            value = float(value)
        except ValueError:
            return None
    # Some benchmarks are already 0-100, some are 0-1
    if 0 < value <= 1.0:
        return value * 100
    if 0 <= value <= 100:
        return value
    return value  # Pass through for scores > 100 (ELO etc.)


def load_existing_data() -> dict:
    """Load existing paper benchmark data."""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {"extracted_at": None, "models": {}}


def save_data(data: dict):
    """Save paper benchmark data."""
    data["extracted_at"] = datetime.utcnow().isoformat() + "Z"
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"  Saved to {DATA_FILE}")


def extract_from_text(model_key: str, text: str, data: dict) -> dict:
    """
    Extract benchmark scores from raw text (paper text, web page, etc.).
    Uses regex patterns to find benchmark tables and score patterns.
    """
    if model_key not in data["models"]:
        data["models"][model_key] = {
            "full_name": TARGET_MODELS[model_key]["full_name"],
            "creator": TARGET_MODELS[model_key]["creator"],
            "benchmarks": {},
            "sources": [],
        }

    model_data = data["models"][model_key]
    found = {}

    # Pattern: "BenchmarkName: XX.X%" or "BenchmarkName: XX.X"
    for pattern in [
        r'([A-Za-z][A-Za-z0-9\-+]+)\s*[:=]\s*(\d+\.?\d*)\s*%',
        r'([A-Za-z][A-Za-z0-9\-+]+)\s*[:=]\s*(\d+\.?\d*)',
        r'\|\s*([A-Za-z][A-Za-z0-9\-+]+)\s*\|\s*(\d+\.?\d*)\s*\|',
    ]:
        for match in re.finditer(pattern, text):
            bench_name = normalize_benchmark(match.group(1))
            score = normalize_score(match.group(2))
            if score is not None and bench_name in [normalize_benchmark(b) for b in TARGET_MODELS[model_key]["known_benchmarks"]]:
                if bench_name not in found or score > found[bench_name]:
                    found[bench_name] = score

    # Merge into model data
    for bench, score in found.items():
        if bench not in model_data["benchmarks"] or score > model_data["benchmarks"][bench].get("score", 0):
            model_data["benchmarks"][bench] = {
                "score": score,
                "source": "paper_extract",
                "extracted_at": datetime.utcnow().isoformat() + "Z",
            }

    return model_data


def list_models():
    """Show available models and their extraction status."""
    data = load_existing_data()
    print("\nPaper Benchmark Extraction Status")
    print("=" * 60)
    for key, info in TARGET_MODELS.items():
        model_data = data.get("models", {}).get(key, {})
        benchmarks = model_data.get("benchmarks", {})
        n_benchmarks = len(benchmarks)
        n_known = len(info["known_benchmarks"])
        status = f"{n_benchmarks}/{n_known} benchmarks" if benchmarks else "NOT EXTRACTED"
        arxiv = info.get("arxiv_id") or "unknown"
        print(f"  {info['full_name']:20s} — {status:25s} — arxiv: {arxiv}")
        if benchmarks:
            for b, v in sorted(benchmarks.items()):
                print(f"    {b:25s} = {v['score']:.1f}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Paper Benchmark Extractor")
    parser.add_argument("--model", help="Extract specific model (kimi, glm, qwen, minimax)")
    parser.add_argument("--list", action="store_true", help="Show extraction status")
    parser.add_argument("--text", help="Extract from raw text file")
    parser.add_argument("--url", help="Fetch and extract from URL")
    args = parser.parse_args()

    if args.list:
        list_models()
        return

    data = load_existing_data()

    if args.text:
        text = Path(args.text).read_text()
        model_key = args.model or "unknown"
        if model_key not in TARGET_MODELS:
            print(f"Unknown model: {model_key}. Use: {', '.join(TARGET_MODELS.keys())}")
            sys.exit(1)
        extract_from_text(model_key, text, data)
        save_data(data)
        return

    if args.url:
        print(f"URL fetching not yet implemented. Download the paper and use --text.")
        sys.exit(1)

    # Default: show what we have and what's missing
    print("\nPaper Benchmark Extractor")
    print("Usage:")
    print("  1. Download paper PDFs/text for target models")
    print("  2. python3 scoring/paper_benchmarks.py --model kimi --text paper.txt")
    print("  3. python3 scoring/paper_benchmarks.py --list")
    print()
    print("Target models:")
    for key, info in TARGET_MODELS.items():
        print(f"  {key:20s} — {info['full_name']} ({info['creator']})")
    print()

    list_models()


if __name__ == "__main__":
    main()
