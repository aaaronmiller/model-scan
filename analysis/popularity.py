"""
Popularity Metric — Community adoption signal for LLM models.

Fetches HuggingFace download counts and normalizes to 0-100.
Provides a "Community Trust" signal independent of benchmark scores.
"""
from __future__ import annotations

import json
import httpx
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "model-scan"
CACHE_FILE = CONFIG_DIR / "popularity_cache.json"

# HuggingFace repo paths for known models
HF_MODELS: dict[str, str] = {
    "deepseek-v4-flash": "deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-v4-pro": "deepseek-ai/DeepSeek-V4-Pro",
    "qwen3.6-plus": "Qwen/Qwen3.6-Plus",
    "qwen3.5-plus": "Qwen/Qwen3.5-Plus",
    "minimax-m2.5": "MiniMaxAI/MiniMax-M2.5",
    "minimax-m2.7": "MiniMaxAI/MiniMax-M2.7",
    "kimi-k2.5": "moonshotai/Kimi-K2.5",
    "kimi-k2.6": "moonshotai/Kimi-K2.6",
    "glm-5.1": "THUDM/GLM-5.1",
    "glm-5-turbo": "THUDM/GLM-5-Turbo",
    "mimo-v2.5-pro": "XiaomiMiMo/MiMo-V2.5-Pro",
    "mimo-v2.5": "XiaomiMiMo/MiMo-V2.5",
    "nemotron-3-super-120b-a12b": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
    "llama-3.3-70b-instruct": "meta-llama/Llama-3.3-70B-Instruct",
    "llama-4-scout": "meta-llama/Llama-4-Scout-17B-16E",
    "llama-3.1-8b-instant": "meta-llama/Llama-3.1-8B",
    "llama-3.1-70b-instruct": "meta-llama/Llama-3.1-70B",
    "mixtral-8x7b-32768": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "deepseek-v3": "deepseek-ai/DeepSeek-V3",
}


def refresh(silent: bool = False) -> dict[str, Any]:
    """Fetch all HF stats, normalize to 0-100, cache, return scores."""
    scores: dict[str, Any] = {}
    for model_id, hf_path in HF_MODELS.items():
        try:
            r = httpx.get(f"https://huggingface.co/api/models/{hf_path}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                scores[model_id] = {
                    "downloads": d.get("downloads", 0),
                    "likes": d.get("likes", 0),
                }
                if not silent:
                    print(f"  ✓ {model_id}: {d['downloads']:,} dl, {d['likes']} likes")
        except Exception:
            pass

    if scores:
        max_dl = max(s["downloads"] for s in scores.values())
        for mid in scores:
            scores[mid]["popularity"] = round(scores[mid]["downloads"] / max_dl * 100, 1)

    cache = {"fetched_at": datetime.now().isoformat(), "scores": scores}
    CACHE_FILE.write_text(json.dumps(cache, indent=2))
    if not silent:
        print(f"\n  ✓ Cached {len(scores)} popularity scores")
    return scores


def load() -> dict[str, dict]:
    """Load cached popularity scores."""
    if not CACHE_FILE.exists():
        refresh(silent=True)
    try:
        return json.loads(CACHE_FILE.read_text()).get("scores", {})
    except Exception:
        return {}


def for_model(model_id: str) -> float | None:
    """Get popularity score (0-100) for a model by fuzzy matching."""
    data = load()
    mid = model_id.lower()
    if mid in data:
        return data[mid].get("popularity")
    for key, val in data.items():
        if key in mid or mid in key:
            return val.get("popularity")
    return None


def provenance_tag(model_id: str) -> str:
    """Return provenance emoji tag: 📥 Community = has HF data, — = unknown."""
    score = for_model(model_id)
    if score is None:
        return "—"
    if score >= 80:
        return "📥🔥"
    return "📥"


if __name__ == "__main__":
    refresh()
