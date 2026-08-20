#!/usr/bin/env python3
"""model-scan's consumer-facing model selection API.

Recovered purpose
-----------------
From intent archaeology on `code-model-scan`, the recorded intent is that
model-scan is called BY other programs and returns the models that caller
should use:

  "Make model-scan discover changing provider models, assess role fitness using
   capability and availability evidence" (seen twice)
  "Figure out how to integrate model-scan into claude-code-proxy ... for model
   selection integration"
  "Add a way to define which selections are free and which use a cost basis:
   primary model, delegated model, and primary fallbacks use cost basis while
   auxiliary models use free option"
  "Set up multiple providers so the same model can fallback to a different
   provider if there are issues"

So the interface is: `--consumer <name>` in, a config-shaped answer out. Each
consumer gets the shape it can actually apply.

    model_roles_api.py --consumer hermes       model + fallback_providers + auxiliary roles
    model_roles_api.py --consumer omp          modelRoles + retry.fallbackChains
    model_roles_api.py --consumer claude-code  per-agent Anthropic tier mapping
    model_roles_api.py --consumer codex        orchestrator model + fallbacks
    model_roles_api.py --consumer proxy        tier -> model routing table
    model_roles_api.py --tiers                 the price-band tier table itself

Capability and price come from the ARDF Pareto frontier via `ardf_roles.py`.
This module adds the tier segmentation and the per-consumer shaping.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import ardf_roles

CHEATSHEET = ardf_roles.CHEATSHEET


# --------------------------------------------------------------------------
# Tier definition
# --------------------------------------------------------------------------
# Derived from the observed price-per-task distribution over the 48 models in
# the ARDF cheatsheet that carry both a capability and a price, on 2026-08-20.
#
# The proposed bands were: executor floor to $1, $1-2, $2-5, $5+. The data says
# adjust in three places:
#
#   1. $5+ is EMPTY. The most expensive model on record is Claude Fable 5 (max)
#      at $3.14. Keep the band as a guard so a future price rise is visible,
#      but expect it to stay empty.
#   2. "executor floor to $1" is far too wide: it holds 41 of 48 models and
#      spans capability 39 to 60. It splits naturally at about $0.05, where
#      the subscription-covered executors sit, and again at $0.20.
#   3. $2-$5 holds only two models and BOTH are dominated by something cheaper.
#      It is a trap band, not a tier. See DOMINATED below.
TIERS = [
    # (name, low_exclusive, high_inclusive, what it is for)
    ("executor",      0.0,   0.05, "bulk execution; subscription-covered, effectively free"),
    ("executor-plus", 0.05,  0.20, "near-frontier capability still at cents per task"),
    ("frontier-entry", 0.20, 1.00, "the first genuinely expensive step; judgement work"),
    ("frontier-high", 1.00,  2.00, "top capability available; reserve for hard calls"),
    ("premium",       2.00,  5.00, "check DOMINATED before using; usually a mistake"),
    ("ultra",         5.00,  1e9,  "empty as of 2026-08-20; guard band"),
]

# Configurations that cost MORE and deliver LESS than a named alternative.
# Selecting one of these is always wrong. Keyed by the dominated config.
DOMINATED = {
    "Claude Opus 5 (max)": (
        "Claude Opus 5 (xhigh)",
        "cap 61.13 at $2.34 versus cap 61.90 at $1.80: cheaper AND more capable",
    ),
    "Claude Fable 5 (max)": (
        "Claude Opus 5 (xhigh)",
        "cap 60.02 at $3.14 versus cap 61.90 at $1.80",
    ),
}


def harvest_all_models(path: Path = CHEATSHEET) -> dict[str, tuple[float, float]]:
    """Every model in the cheatsheet carrying both capability and task price.

    Reads all tables, not only the strict frontier, because the tier question
    is about the whole field. Keeps the cheapest observation per model.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    seen: dict[str, tuple[float, float]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        cap = price = name = None
        for i, c in enumerate(cells):
            if cap is None and i >= 2 and re.fullmatch(r"\d+\.\d+", c):
                cap = float(c)
            m = re.fullmatch(r"\$([\d.]+)", c.replace(",", ""))
            if m and price is None and cap is not None:
                price = float(m.group(1))
        for c in cells:
            if re.search(r"[A-Za-z]", c) and not c.startswith("$") \
               and c not in ("YES", "no") and len(c) > 3:
                name = c
                break
        if name and cap and price and price > 0:
            if name not in seen or seen[name][1] > price:
                seen[name] = (cap, price)
    return seen


def tier_of(price: float) -> str:
    for name, lo, hi, _ in TIERS:
        if lo < price <= hi:
            return name
    return "unclassified"


def build_tiers() -> dict[str, list[dict]]:
    models = harvest_all_models()
    out: dict[str, list[dict]] = {t[0]: [] for t in TIERS}
    for name, (cap, price) in models.items():
        entry = {"name": name, "capability": cap, "task_price": price}
        if name in DOMINATED:
            better, why = DOMINATED[name]
            entry["dominated_by"] = better
            entry["why"] = why
        out[tier_of(price)].append(entry)
    for lst in out.values():
        lst.sort(key=lambda e: -e["capability"])
    return out


# --------------------------------------------------------------------------
# Consumer shaping
# --------------------------------------------------------------------------
def _roles() -> dict:
    frontier = ardf_roles.parse_frontier()
    available = ardf_roles.load_available()
    rows = ardf_roles.routable(frontier, available)
    return ardf_roles.assign(rows)


def _pick(assign: dict, role: str, n: int = 1) -> list[str]:
    return [r["route"] for r in assign.get(role, [])[:n]]


def _dedupe(routes: list[str]) -> list[str]:
    """Preserve order, drop repeats.

    Roles overlap by design: `primary` and `fallback` both draw from the same
    frontier, so concatenating their picks yields duplicates. A fallback chain
    containing the same model twice retries the failed model instead of
    failing over.
    """
    seen, out = set(), []
    for r in routes:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def consumer_hermes(assign: dict) -> dict:
    """Shape for ~/.hermes/config.yaml."""
    aux = _pick(assign, "auxiliary", 3)
    return {
        "model": {"default": "gpt-5.6-sol", "provider": "openai-codex",
                  "note": "main model is pinned by standing policy, not by the frontier"},
        "fallback_providers": [
            {"provider": r.split("/")[0], "model": r.split("/", 1)[1]}
            for r in _dedupe(_pick(assign, "primary", 3) + _pick(assign, "fallback", 3))
        ],
        "delegation": {"model": _pick(assign, "delegated")[0]},
        "auxiliary_default": aux[0] if aux else None,
        "auxiliary_fallback_chain": _dedupe(aux[1:]),
    }


def consumer_omp(assign: dict) -> dict:
    """Shape for ~/.omp/agent/config.yml modelRoles and retry.fallbackChains."""
    return {
        "modelRoles": {
            "default": _pick(assign, "orchestration")[0],
            "slow": _pick(assign, "primary")[0],
            "plan": _pick(assign, "primary")[0],
            "smol": _pick(assign, "minutiae")[0],
            "commit": _pick(assign, "minutiae")[0],
        },
        "retry": {"fallbackChains": {
            "default": _pick(assign, "orchestration", 3),
            "smol": _pick(assign, "minutiae", 3),
            "slow": _pick(assign, "primary", 3),
        }},
    }


def consumer_claude_code(assign: dict) -> dict:
    """Shape for ~/.claude/agents/*.md frontmatter.

    HARD CONSTRAINT, verified against the Claude Code documentation on
    2026-08-20: a subagent's `model:` field accepts ONLY Anthropic values. The
    aliases sonnet, opus, haiku and fable, a full Claude model id, or inherit.
    There is no provider-prefixed form, so a Claude Code agent CANNOT name
    deepseek, GLM, MiMo or Kimi.

    Twelve agent files previously claimed otherwise and silently ran full-price
    Anthropic models. So this consumer returns a TIER-to-Anthropic-model map,
    not third-party routes, and names the non-Anthropic equivalent only as a
    comment for the human.
    """
    return {
        "constraint": "model: accepts only sonnet|opus|haiku|fable|claude-*|inherit",
        "agents": [
            {"tier": "minutiae", "model": "haiku",
             "use_for": "titles, classification, one-liners"},
            {"tier": "executor", "model": "sonnet",
             "use_for": "bulk execution",
             "cheaper_equivalent_outside_claude_code": _pick(assign, "delegated")[0]},
            {"tier": "frontier-entry", "model": "opus",
             "use_for": "orchestration, review, judgement"},
            {"tier": "frontier-high", "model": "claude-opus-5",
             "use_for": "irreversible decisions",
             "warning": "Claude Opus 5 (max) is DOMINATED by (xhigh): "
                        "cap 61.13 at $2.34 versus cap 61.90 at $1.80. Prefer xhigh."},
        ],
        "note": "For non-Anthropic execution, do not use a subagent. Delegate "
                "headlessly: omp -p --model <provider>/<model>.",
    }


def consumer_codex(assign: dict) -> dict:
    return {
        "orchestrator": _pick(assign, "orchestration")[0],
        "executor": _pick(assign, "delegated")[0],
        "fallbacks": _dedupe(_pick(assign, "fallback", 3)),
    }


def consumer_proxy(assign: dict) -> dict:
    """Tier to route table for claude-code-proxy."""
    tiers = build_tiers()
    return {
        "tiers": {
            name: [e["name"] for e in tiers[name][:5]]
            for name, _, _, _ in TIERS if tiers[name]
        },
        "routes": {role: _dedupe(_pick(assign, role, 3)) for role in
                   ("orchestration", "primary", "delegated", "fallback",
                    "auxiliary", "minutiae")},
        "never": list(ardf_roles.NEVER),
    }


CONSUMERS = {
    "hermes": consumer_hermes,
    "omp": consumer_omp,
    "claude-code": consumer_claude_code,
    "codex": consumer_codex,
    "proxy": consumer_proxy,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--consumer", choices=sorted(CONSUMERS))
    ap.add_argument("--tiers", action="store_true", help="print the tier table")
    args = ap.parse_args()

    if args.tiers or not args.consumer:
        tiers = build_tiers()
        total = sum(len(v) for v in tiers.values())
        print(f"ARDF price-per-task tiers  ({total} models with capability and price)")
        print(f"Source: {CHEATSHEET}\n")
        for name, lo, hi, purpose in TIERS:
            entries = tiers[name]
            hi_s = "and up" if hi > 1e8 else f"${hi:g}"
            print(f"=== {name}  (>${lo:g} to {hi_s})  {len(entries)} models ===")
            print(f"    {purpose}")
            if not entries:
                print("    EMPTY")
            for e in entries[:6]:
                flag = ""
                if "dominated_by" in e:
                    flag = f"   DOMINATED by {e['dominated_by']}"
                print(f"      cap {e['capability']:>6.2f}  ${e['task_price']:<9.5g} "
                      f"{e['name'][:46]}{flag}")
            print()
        return 0

    print(json.dumps(CONSUMERS[args.consumer](_roles()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
