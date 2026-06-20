#!/usr/bin/env python3
"""
User Sentiment Pipeline — scrapes X/Reddit for empirical "feels like" model comparisons.

Collects real user opinions about models, tagged by region and context.
Used to validate the "magic" factor that benchmarks don't capture.

Usage:
    python3 scoring/sentiment.py                    # scrape all targets
    python3 scoring/sentiment.py --model deepseek   # one model
    python3 scoring/sentiment.py --summary          # show collected data
    python3 scoring/sentiment.py --add "DeepSeek V4 Flash feels way better than Nemotron" --model deepseek
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "sentiment_data.json"

# ── Target models for sentiment collection ────────────────────────────────
TARGET_MODELS = {
    "minimax-m3": {"search_terms": ["minimax m3", "minimax-m3", "MiniMax M3"], "aliases": ["minimax"]},
    "deepseek-v4-flash": {"search_terms": ["deepseek v4 flash", "deepseek-v4-flash", "DeepSeek Flash"], "aliases": ["deepseek", "flash"]},
    "mimo-v2.5": {"search_terms": ["mimo v2.5", "mimo-v2.5", "MiMo V2.5", "xiaomi mimo"], "aliases": ["mimo", "xiaomi"]},
    "nemotron-3-ultra": {"search_terms": ["nemotron ultra", "nemotron-3-ultra", "nvidia nemotron"], "aliases": ["nemotron", "nvidia"]},
    "qwen-3.6": {"search_terms": ["qwen 3.6", "qwen-3.6", "qwen3.6", "qwen plus"], "aliases": ["qwen", "alibaba"]},
    "glm-5.2": {"search_terms": ["glm 5.2", "glm-5.2", "zhipu glm", "chatglm"], "aliases": ["glm", "zhipu", "chatglm"]},
    "kimi-k2.6": {"search_terms": ["kimi k2.6", "kimi-k2.6", "moonshot kimi"], "aliases": ["kimi", "moonshot"]},
    "gemma-4": {"search_terms": ["gemma 4", "gemma-4", "google gemma"], "aliases": ["gemma", "google"]},
    "stepfun": {"search_terms": ["stepfun", "step fun", "step-1"], "aliases": ["stepfun", "step"]},
    "claude": {"search_terms": ["claude 4", "claude-4", "anthropic claude"], "aliases": ["claude", "anthropic"]},
}

# ── Sentiment signals ────────────────────────────────────────────────────
POSITIVE_SIGNALS = [
    r"love (?:it|this|the|how)",
    r"(?:way |much )?better (?:than|then|vs|compared)",
    r"(?:just |actually )?(?:works?|gets? shit done|does the job)",
    r"impressive|amazing|excellent|fantastic|great",
    r"(?:fast|quick|snappy) (?:and|but|responsive)",
    r"my (?:go.?to|favorite|preferred|daily driver)",
    r"magic|feels? (?:right|good|natural|smart)",
    r"understands? (?:me|context|what I need)",
    r"(?:no |fewer )?(?:loops|retries|hallucinations?)",
]

NEGATIVE_SIGNALS = [
    r"(?:hate|suck|terrible|awful|worst) (?:it|this|at|with)",
    r"(?:much |way )?worse (?:than|then|vs|compared)",
    r"(?:keeps? |always |constantly )?(?:looping|retrying|asking|hallucinating)",
    r"slow|laggy|sluggish|unresponsive",
    r"(?:not |doesn't |never )?(?:understand|follow|get|handle)",
    r"confused|confusing|unreliable|inconsistent",
    r"(?:too |overly )?(?:verbose|chatty|wordy|long)",
    r"dropped (?:connection|response|context)",
    r"(?:fails? |failing |broken )",
]

NEUTRAL_SIGNALS = [
    r"(?:decent|okay|fine|alright|acceptable)",
    r"(?:mixed |hit.or.miss|inconsistent|varies)",
    r"(?:sometimes |occasionally )?(?:good|bad|works|fails)",
    r"(?:not bad|nothing special|average)",
]

# ── Region detection ─────────────────────────────────────────────────────
REGION_PATTERNS = {
    "china": [r"中文", r"cn\b", r"中国", r"大陆", r"国内"],
    "europe": [r"\beu\b", r"\buk\b", r"german|french|spanish|italian"],
    "us": [r"\bus\b", r"\busa\b", r"american", r"silicon valley"],
    "india": [r"\bindia\b", r"\bin\b", r"hindi"],
    "japan": [r"日本", r"japan", r"jp\b"],
    "korea": [r"한국", r"korea", r"kr\b"],
}


def detect_region(text: str) -> str:
    """Detect likely geographic region from text content."""
    text_lower = text.lower()
    for region, patterns in REGION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return region
    return "unknown"


def classify_sentiment(text: str) -> dict:
    """Classify text sentiment toward a model."""
    text_lower = text.lower()
    pos = sum(1 for p in POSITIVE_SIGNALS if re.search(p, text_lower))
    neg = sum(1 for n in NEGATIVE_SIGNALS if re.search(n, text_lower))
    neu = sum(1 for n in NEUTRAL_SIGNALS if re.search(n, text_lower))

    total = pos + neg + neu
    if total == 0:
        sentiment = "neutral"
        confidence = 0.0
    elif pos > neg and pos > neu:
        sentiment = "positive"
        confidence = pos / total
    elif neg > pos and neg > neu:
        sentiment = "negative"
        confidence = neg / total
    else:
        sentiment = "mixed"
        confidence = 0.3

    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "positive_signals": pos,
        "negative_signals": neg,
        "neutral_signals": neu,
    }


def load_data() -> dict:
    """Load existing sentiment data."""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {
        "collected_at": None,
        "model_sentiments": {},
        "raw_entries": [],
    }


def save_data(data: dict):
    """Save sentiment data."""
    data["collected_at"] = datetime.utcnow().isoformat() + "Z"
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"  Saved to {DATA_FILE}")


def add_entry(data: dict, text: str, model_key: str = None, source: str = "manual",
              url: str = None, region: str = None):
    """Add a sentiment entry."""
    # Auto-detect model if not specified
    if model_key is None:
        text_lower = text.lower()
        for mk, minfo in TARGET_MODELS.items():
            for term in minfo["search_terms"]:
                if term.lower() in text_lower:
                    model_key = mk
                    break
            if model_key:
                break

    if model_key is None:
        model_key = "unknown"

    # Classify sentiment
    sentiment = classify_sentiment(text)
    detected_region = region or detect_region(text)

    entry = {
        "text": text[:500],
        "model": model_key,
        "source": source,
        "url": url,
        "region": detected_region,
        "sentiment": sentiment["sentiment"],
        "confidence": sentiment["confidence"],
        "positive_signals": sentiment["positive_signals"],
        "negative_signals": sentiment["negative_signals"],
        "collected_at": datetime.utcnow().isoformat() + "Z",
    }

    data["raw_entries"].append(entry)

    # Aggregate per model
    if model_key not in data["model_sentiments"]:
        data["model_sentiments"][model_key] = {
            "total_entries": 0,
            "positive": 0,
            "negative": 0,
            "mixed": 0,
            "neutral": 0,
            "regions": {},
            "magic_mentions": 0,
            "key_phrases": [],
        }

    ms = data["model_sentiments"][model_key]
    ms["total_entries"] += 1
    ms[sentiment["sentiment"]] = ms.get(sentiment["sentiment"], 0) + 1
    ms["regions"][detected_region] = ms["regions"].get(detected_region, 0) + 1

    # Track "magic" mentions
    if re.search(r"magic|feels? (?:right|good|natural)|just gets? shit done", text.lower()):
        ms["magic_mentions"] += 1

    return entry


def show_summary(data: dict):
    """Print summary of collected sentiment data."""
    print("\nSentiment Data Summary")
    print("=" * 70)

    total = len(data.get("raw_entries", []))
    print(f"Total entries: {total}")
    print(f"Models tracked: {len(data.get('model_sentiments', {}))}")
    print()

    for model, ms in sorted(data.get("model_sentiments", {}).items(),
                            key=lambda x: -x[1].get("total_entries", 0)):
        total = ms["total_entries"]
        pos = ms.get("positive", 0)
        neg = ms.get("negative", 0)
        magic = ms.get("magic_mentions", 0)

        pos_pct = (pos / total * 100) if total > 0 else 0
        neg_pct = (neg / total * 100) if total > 0 else 0

        bar_len = 30
        pos_bar = int(pos_pct / 100 * bar_len)
        neg_bar = int(neg_pct / 100 * bar_len)
        bar = "█" * pos_bar + "░" * (bar_len - pos_bar - neg_bar) + "▒" * neg_bar

        print(f"  {model:25s}  {total:4d} entries  {bar}  +{pos_pct:.0f}%/-{neg_pct:.0f}%  ✨{magic}")

        if ms.get("regions"):
            regions = ", ".join(f"{r}:{c}" for r, c in sorted(ms["regions"].items(), key=lambda x: -x[1]))
            print(f"  {'':25s}  regions: {regions}")
    print()


def main():
    parser = argparse.ArgumentParser(description="User Sentiment Pipeline")
    parser.add_argument("--model", help="Filter by model")
    parser.add_argument("--summary", action="store_true", help="Show summary")
    parser.add_argument("--add", help="Add a text entry")
    parser.add_argument("--source", default="manual", help="Source of entry")
    parser.add_argument("--url", help="Source URL")
    parser.add_argument("--region", help="Override region")
    args = parser.parse_args()

    data = load_data()

    if args.summary:
        show_summary(data)
        return

    if args.add:
        entry = add_entry(data, args.add, args.model, args.source, args.url, args.region)
        print(f"Added entry for {entry['model']}: {entry['sentiment']}")
        save_data(data)
        return

    # Default: show what we have
    print("\nUser Sentiment Pipeline")
    print("=" * 60)
    print("\nCollects real user opinions about models from social media.")
    print("\nUsage:")
    print('  python3 scoring/sentiment.py --add "DeepSeek feels better than Nemotron" --model deepseek-v4-flash')
    print("  python3 scoring/sentiment.py --summary")
    print("\nTarget models:")
    for key, info in TARGET_MODELS.items():
        terms = ", ".join(info["search_terms"][:2])
        print(f"  {key:25s} — search: {terms}")

    show_summary(data)


if __name__ == "__main__":
    main()
