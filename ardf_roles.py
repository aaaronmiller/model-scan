#!/usr/bin/env python3
"""Assign models to roles from the ARDF Pareto frontier.

This is the runtime consumer that ARDF always lacked.

The gap it closes
-----------------
ARDF computes a strict Pareto frontier of models by calibrated capability
against task price, and `calibrate.py` projects it into
`pareto-frontier-cheatsheet.md`. model-scan ships `ardf_export.py`, which
packages that data, but as of 2026-08-20 no runtime code path imported it. The
frontier was computed, published, and then read by nobody. Meanwhile role
assignments in `~/.hermes/config.yaml` and `~/.omp/agent/config.yml` were
maintained by hand.

What this does
--------------
1. Parses the strict Pareto frontier table from the cheatsheet. The cheatsheet
   is a generated projection, so it is read, never edited. Policy changes go in
   ARDF's `project-config.json` and are picked up on the next `calibrate.py`.
2. Intersects the frontier with the models actually reachable on this machine,
   from the provider registry.
3. Applies the recorded role policy and prints an assignment per role.

The role policy
---------------
Recovered from intent archaeology on this project
(`intent-archaeology/archaeology.db`, project `code-model-scan`):

  "Add a way to define which selections are free and which use a cost basis:
   primary model, delegated model, and primary fallbacks use cost basis while
   auxiliary models use free option."

So roles split into two economic classes:

  cost-basis  primary, delegated, primary fallbacks. May use a per-call model
              when the capability floor demands it.
  free        auxiliary and background roles. Restricted to zero-marginal-cost
              routes, because these fire constantly and must not accrue
              per-call charges.

Within either class the rule is the same and it is the whole point of a
frontier: take the CHEAPEST option that clears the role's capability floor.
Every frontier point is non-dominated, so once the floor is met, paying more
buys capability the role does not need.

On this machine "free" means zero marginal cost, not zero capability: a free
opencode-zen tier plus a $10 opencode-go subscription, both serving the same
aggressively priced models. Anything on opencode-go is subscription-covered and
therefore free at the margin, subject to a usage multiplier.

Usage
-----
    python3 ardf_roles.py                 human-readable table
    python3 ardf_roles.py --json          machine-readable
    python3 ardf_roles.py --explain       show why each role chose what it did
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ARDF_ROOT = Path("/home/cheta/code/ardf/ardf")
CHEATSHEET = ARDF_ROOT / "pareto-frontier-cheatsheet.md"

# Provider registry snapshot: {provider: [{id, name, vision, ...}, ...]}
AVAILABLE = Path("/home/cheta/.cache/agent-staging/available-models.json")

# Zero marginal cost is a property of the (provider, model) pair, not of the
# provider alone. The plan here is a FREE opencode-zen tier plus a $10
# opencode-go subscription:
#
#   opencode-go    every model is subscription-covered, so free at the margin.
#   opencode-zen   ONLY the *-free models. Paid zen models are never used by
#                  standing policy, and reaching for one returns
#                  401 CreditsError.
#
# Treating the whole of opencode-zen as free was the first version's bug: it
# made gpt-5.6-sol look free and let it win every role including the ones that
# must not carry per-call cost.
SUBSCRIPTION_PROVIDERS = {"opencode-go"}


def _free_at_margin(provider: str, model_id: str) -> bool:
    if provider in SUBSCRIPTION_PROVIDERS:
        return True
    if provider == "opencode-zen":
        return model_id.endswith("-free")
    return False

# ARDF names models for publication; providers use short ids. This maps the
# frontier's display names onto ids we can actually route to. Keep it small and
# explicit: a fuzzy matcher here would silently mis-route a role.
NAME_TO_ID = {
    "MiMo-V2.5": "mimo-v2.5",
    "GLM-5.2 (max)": "glm-5.2",
    "GLM-4.7-Flash (Reasoning)": None,          # not carried by our providers
    "GLM-4.7-Flash (Non-reasoning)": None,
    "Muse Spark 1.2 (xhigh, Contributor pricing)": "muse-spark-1.2-contributor",
    "GPT-5.6 Sol (xhigh)": "gpt-5.6-sol",
    "GPT-5.6 Sol (max)": "gpt-5.6-sol",
    "GPT-5.6 Luna (medium)": "gpt-5.6-luna",
    "Kimi K3 (max)": "kimi-k3",
    "Claude Opus 5 (medium)": None,             # reached through Claude Code, not a provider here
    "Claude Opus 5 (xhigh)": None,
    "GPT-5.5 (high)": None,
    "Qwen3.5 0.8B (Non-reasoning)": None,
    "Granite 4.0 H Small": None,
}

# Subscription quota is not consumed uniformly. The provider registry labels
# some models "(2x usage)", so they burn quota twice as fast for the same call.
# ARDF's task_price is a dollar figure and does not capture this, so it is
# applied on top for subscription routes.
USAGE_MULTIPLIER = {
    "deepseek-v4-flash": 2.0,
    "gpt-5.6-luna": 2.0,
}


def _effective_cost(row: dict) -> float:
    """Price used for ranking. On a subscription the scarce resource is quota."""
    mult = USAGE_MULTIPLIER.get(row.get("model_id", ""), 1.0)
    return row["task_price"] * mult


# Models never to assign, with the reason, so the exclusion is auditable.
NEVER = {
    "llama": "excluded by standing policy",
}

ROLES = [
    # (role, economic class, what it does, minimum capability)
    ("orchestration", "cost-basis", "planning, review, judgement", 55.0),
    ("primary",       "cost-basis", "the main conversation model", 50.0),
    ("delegated",     "cost-basis", "subagents doing real work", 45.0),
    ("fallback",      "cost-basis", "primary's backup chain", 40.0),
    ("auxiliary",     "free",       "vision, extraction, titling, search", 35.0),
    ("minutiae",      "free",       "titles, classification, one-liners", 0.0),
]


def parse_frontier(path: Path = CHEATSHEET) -> list[dict]:
    """Read the strict Pareto frontier table out of the generated cheatsheet."""
    if not path.exists():
        raise SystemExit(f"ARDF cheatsheet not found: {path}\n"
                         "Run calibrate.py in the ARDF project first.")
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Strict current Pareto frontier\s*$(.*?)^## ",
                  text, re.M | re.S)
    if not m:
        raise SystemExit("could not locate the frontier section in the cheatsheet")

    rows = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Tier" in line[:12]:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        try:
            capability = float(cells[4])
            price = float(cells[5].replace("$", "").replace(",", ""))
        except ValueError:
            continue
        rows.append({
            "tier": cells[0],
            "name": cells[1],
            "vendor": cells[2],
            "effort": cells[3],
            "capability": capability,
            "task_price": price,
        })
    return rows


def load_available() -> dict[str, list[str]]:
    """model id -> providers carrying it."""
    if not AVAILABLE.exists():
        raise SystemExit(f"provider registry snapshot not found: {AVAILABLE}")
    data = json.loads(AVAILABLE.read_text())
    by_id: dict[str, list[str]] = {}
    for provider, models in data.items():
        for entry in models:
            mid = entry.get("id")
            if mid:
                by_id.setdefault(mid, []).append(provider)
    return by_id


def routable(frontier: list[dict], available: dict[str, list[str]]) -> list[dict]:
    """Keep only frontier entries we can actually reach, and attach routing."""
    out = []
    for row in frontier:
        mid = NAME_TO_ID.get(row["name"], "__unmapped__")
        if mid is None:
            row["skip"] = "not carried by any configured provider"
            out.append(row)
            continue
        if mid == "__unmapped__":
            row["skip"] = "no id mapping; add one to NAME_TO_ID"
            out.append(row)
            continue
        if any(bad in mid.lower() for bad in NEVER):
            row["skip"] = NEVER[next(b for b in NEVER if b in mid.lower())]
            out.append(row)
            continue
        providers = available.get(mid, [])
        if not providers:
            row["skip"] = f"id {mid} absent from the provider registry"
            out.append(row)
            continue
        # Prefer a route that is free at the margin.
        free_routes = [p for p in providers if _free_at_margin(p, mid)]
        chosen = (free_routes or providers)[0]
        row["model_id"] = mid
        row["providers"] = providers
        row["route"] = f"{chosen}/{mid}"
        row["free_at_margin"] = bool(free_routes)
        row["skip"] = None
        out.append(row)
    return out


def assign(rows: list[dict]) -> dict[str, list[dict]]:
    usable = [r for r in rows if not r.get("skip")]
    result = {}
    for role, econ, _purpose, floor in ROLES:
        pool = [r for r in usable if r["capability"] >= floor]
        if econ == "free":
            pool = [r for r in pool if r["free_at_margin"]]
        # Highest capability first. Among the frontier every point is
        # non-dominated, so capability is the only remaining discriminator.
        # THE POINT OF A FRONTIER: buy the requirement at the lowest price.
        # Every frontier point is non-dominated, so once the capability floor
        # is met the cheapest survivor is strictly the best trade. Sorting by
        # capability instead would hand every role the most expensive model
        # and make the frontier decorative.
        pool.sort(key=lambda r: (_effective_cost(r), -r["capability"]))
        result[role] = pool[:3]
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    frontier = parse_frontier()
    available = load_available()
    rows = routable(frontier, available)
    assignments = assign(rows)

    if args.json:
        print(json.dumps({
            "source": str(CHEATSHEET),
            "frontier_points": len(frontier),
            "routable": sum(1 for r in rows if not r.get("skip")),
            "assignments": {
                role: [{"route": r["route"], "capability": r["capability"],
                        "task_price": r["task_price"], "tier": r["tier"]}
                       for r in picks]
                for role, picks in assignments.items()
            },
        }, indent=2))
        return 0

    print(f"ARDF strict Pareto frontier: {len(frontier)} points")
    print(f"Source: {CHEATSHEET}\n")

    print("Routable on this machine:")
    for r in rows:
        if r.get("skip"):
            continue
        margin = "free at margin" if r["free_at_margin"] else "per-call cost"
        mult = USAGE_MULTIPLIER.get(r["model_id"], 1.0)
        tag = f"  {mult:g}x quota" if mult != 1.0 else ""
        print(f"  {r['tier']:<3} {r['route']:<44} cap {r['capability']:>6.2f}  "
              f"${r['task_price']:<10.6g} {margin}{tag}")

    print("\nNot routable:")
    for r in rows:
        if r.get("skip"):
            print(f"  {r['name']:<46} {r['skip']}")

    print("\nRole assignments (first choice, then backups):")
    for role, econ, purpose, floor in ROLES:
        picks = assignments[role]
        if not picks:
            print(f"\n  {role:<14} [{econ}]  NO CANDIDATE at capability >= {floor}")
            continue
        print(f"\n  {role:<14} [{econ}]  {purpose}   floor cap {floor}")
        for i, r in enumerate(picks):
            marker = "->" if i == 0 else "  "
            print(f"      {marker} {r['route']:<44} cap {r['capability']:>6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
