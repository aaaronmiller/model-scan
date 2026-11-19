"""Compare the formula's tiers and order with a hand-made reference tier list.

The reference is a Markdown file with ``## Tier N`` sections (and an ``Unplaced`` section)
whose entries name gateway route ids in backticks. Entries are matched to the formula's
models by route id only. This module is comparison code: it reads the reference, it never
feeds the ranking.
"""
from __future__ import annotations

import itertools
import re
from pathlib import Path


def parse_reference(path: Path) -> list[dict]:
    entries, tier, position = [], None, 0
    for line in path.read_text().splitlines():
        head = re.match(r"^##\s+(Tier\s+(\d+)|Unplaced)", line)
        if head:
            tier = int(head.group(2)) if head.group(2) else None
            position = 0
            continue
        if not line.strip().startswith(("-", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            continue
        ids = re.findall(r"`([^`]+)`", line)
        name = re.search(r"\*\*([^*]+)\*\*", line)
        if not ids or not name:
            continue
        position += 1
        entries.append({"name": name.group(1), "tier": tier, "position": position, "route_ids": ids})
    return entries


def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = _rank(a), _rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def kendall(a: list[float], b: list[float]) -> float:
    """Kendall tau-b."""
    conc = disc = ta = tb = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        da, db = a[i] - a[j], b[i] - b[j]
        if da == 0 and db == 0:
            continue
        if da == 0:
            ta += 1
        elif db == 0:
            tb += 1
        elif (da > 0) == (db > 0):
            conc += 1
        else:
            disc += 1
    denom = ((conc + disc + ta) * (conc + disc + tb)) ** 0.5
    return (conc - disc) / denom if denom else 0.0


def compare(models: list, reference: list[dict]) -> dict:
    by_route = {}
    for m in models:
        for r in m.routes:
            by_route.setdefault(r.route_id, m)
    rows = []
    for e in reference:
        found = {by_route[i].key for i in e["route_ids"] if i in by_route}
        m = next((by_route[i] for i in e["route_ids"] if i in by_route), None)
        rows.append({"name": e["name"], "ref_tier": e["tier"], "ref_position": e["position"],
                     "model": m.key if m else None, "split_across_models": len(found) > 1,
                     "tier": m.tier if m else None, "score": m.score if m else None,
                     "evidence": m.evidence if m else None, "reason": m.reason if m else "route not discovered"})
    ordered = [r for r in rows if r["ref_tier"] in (1, 2)]
    both = [r for r in ordered if r["score"] is not None and r["tier"] is not None]
    # Reference order: Tier 1 positions, then Tier 2 positions. Lower is better.
    ref_order = [(r["ref_tier"] - 1) * 100 + r["ref_position"] for r in both]
    formula = [-r["score"] for r in both]
    placed_in_order = sorted(both, key=lambda r: -r["score"])
    same_tier = sum(1 for r in rows if r["tier"] == r["ref_tier"])
    t1_ref = {r["name"] for r in rows if r["ref_tier"] == 1}
    t1_formula = {r["name"] for r in rows if r["tier"] == 1}
    return {
        "models_compared": len(both),
        "kendall_tau": kendall(ref_order, formula) if len(both) > 1 else None,
        "spearman_rho": spearman(ref_order, formula) if len(both) > 1 else None,
        "tier_agreement": f"{same_tier}/{len(rows)}",
        "tier_agreement_fraction": same_tier / len(rows) if rows else None,
        "tier1_same_set": t1_ref == t1_formula,
        "tier1_missing": sorted(t1_ref - t1_formula),
        "tier1_extra": sorted(t1_formula - t1_ref),
        "formula_order_t1_t2": [r["name"] for r in placed_in_order],
        "reference_order_t1_t2": [r["name"] for r in sorted(ordered, key=lambda r: ((r["ref_tier"] - 1) * 100 + r["ref_position"]))],
        "disagreements": [r for r in rows if r["tier"] != r["ref_tier"]],
        "rows": rows,
    }
