"""
Cross-influence modifier functions for multi-axis scoring.

Each modifier takes a base score + model data, returns (new_score, trace).
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable

from . import ModifierTrace


# ── Utility ───────────────────────────────────────────────────────────

def _months_before(date_str: str | None, now: datetime | None = None) -> int:
    """Months between date_str and now (approximate)."""
    if not date_str:
        return 0
    if now is None:
        now = datetime.now()
    try:
        if len(date_str) == 7:  # YYYY-MM
            d = datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) >= 10:  # YYYY-MM-DD
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        else:
            return 0
        return (now.year - d.year) * 12 + (now.month - d.month)
    except ValueError:
        return 0


# ── Modifier type: a function that takes (base_score, model_dict, cache) → (new_score, trace) ──

ModifierFn = Callable[[float, dict, dict], tuple[float, ModifierTrace]]


# ═══════════════════════════════════════════════════════════════════════
# INTELLIGENCE MODIFIERS
# ═══════════════════════════════════════════════════════════════════════

def mod_knowledge_cutoff(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Recent knowledge = higher raw intelligence. Linear decay."""
    kc = m.get("knowledge", "")
    age = _months_before(kc)
    delta = max(-8, min(5, 4 - 0.3 * age))
    return base + delta, ModifierTrace("kc_age", f"knowledge cutoff {kc or '?'} ({age}mo)", base, delta, base + delta)


def mod_release_recency(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Newer architectures benefit from improved training. Gentler decay."""
    rd = m.get("release_date", "")
    age = _months_before(rd)
    delta = max(-8, min(8, 5 - 0.25 * age))
    return base + delta, ModifierTrace("rel_recency", f"released {rd or '?'} ({age}mo ago)", base, delta, base + delta)


def mod_reasoning(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Reasoning capability adds intelligence bonus."""
    has_reas = m.get("has_reasoning", False) or m.get("reasoning", False)
    if has_reas:
        delta = 5.0
        return base + delta, ModifierTrace("reasoning", "has reasoning capability", base, delta, base + delta)
    return base, ModifierTrace("reasoning", "no reasoning", base, 0, base)


def mod_context_window(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Larger context enables more complex reasoning. Logarithmic, capped."""
    ctx = m.get("context_window", 0) or m.get("ctx_k", 0) or 0
    if ctx <= 0:
        return base, ModifierTrace("ctx_window", "unknown context", base, 0, base)
    delta = max(-3, min(5, 2 * math.log2(ctx / 32768)))
    return base + delta, ModifierTrace("ctx_window", f"{ctx//1024}K context", base, delta, base + delta)


def mod_multimodal(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Multimodal breadth adds intelligence bonus."""
    mods = m.get("modalities", []) or []
    count = len([x for x in mods if x != "text"])
    delta = min(8, count * 2.5)
    if delta > 0:
        return base + delta, ModifierTrace("multimodal", f"{count} extra modalities", base, delta, base + delta)
    return base, ModifierTrace("multimodal", "text only", base, 0, base)


# ═══════════════════════════════════════════════════════════════════════
# SPEED MODIFIERS
# ═══════════════════════════════════════════════════════════════════════

def mod_reasoning_penalty(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Reasoning models have hidden thinking latency."""
    has_reas = m.get("has_reasoning", False)
    if has_reas:
        delta = -12.0
        return base + delta, ModifierTrace("reas_penalty", "reasoning overhead", base, delta, base + delta)
    return base, ModifierTrace("reas_penalty", "no reasoning", base, 0, base)


def mod_free_tier_penalty(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Free tiers have rate limits and queuing."""
    is_free = m.get("is_free", False) or m.get("free_only", False)
    if is_free:
        delta = -8.0
        return base + delta, ModifierTrace("free_penalty", "free tier rate limits", base, delta, base + delta)
    return base, ModifierTrace("free_penalty", "paid tier", base, 0, base)


# ═══════════════════════════════════════════════════════════════════════
# AGENTIC MODIFIERS
# ═══════════════════════════════════════════════════════════════════════

def mod_structured_output(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Structured output is critical for reliable tool calls."""
    has_so = m.get("structured_output", False)
    if has_so:
        delta = 8.0
        return base + delta, ModifierTrace("struct_output", "supports structured output", base, delta, base + delta)
    return base, ModifierTrace("struct_output", "no structured output", base, 0, base)


def mod_max_output_tokens(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Longer output enables multi-turn tool chains."""
    max_out = m.get("max_output", 0) or m.get("max_out", 0) or 4096
    delta = max(-3, min(6, 2 * math.log2(max_out / 8192)))
    return base + delta, ModifierTrace("max_output", f"{max_out//1024}K max output", base, delta, base + delta)


# ═══════════════════════════════════════════════════════════════════════
# CODING MODIFIERS
# ═══════════════════════════════════════════════════════════════════════

def mod_context_coding(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """Context window is critical for coding (holding codebase context)."""
    ctx = m.get("context_window", 0) or m.get("ctx_k", 0) or 0
    if ctx <= 0:
        return base, ModifierTrace("ctx_coding", "unknown context", base, 0, base)
    delta = max(-4, min(6, 2 * math.log2(ctx / 65536)))
    return base + delta, ModifierTrace("ctx_coding", f"{ctx//1024}K context for code", base, delta, base + delta)


def mod_benchmark_verified(base: float, m: dict, cache: dict) -> tuple[float, ModifierTrace]:
    """SWE-bench Verified bonus — direct coding signal."""
    swe = m.get("benchmark_swe_verified", None) or cache.get("swe_verified", {}).get(m.get("model_id", ""), {}).get("score")
    if swe and swe > 0:
        delta = min(12, swe * 0.15)  # 80% SWE-V = +12
        return base + delta, ModifierTrace("swe_verified", f"SWE-V {swe:.0f}%", base, delta, base + delta)
    return base, ModifierTrace("swe_verified", "no SWE data", base, 0, base)
