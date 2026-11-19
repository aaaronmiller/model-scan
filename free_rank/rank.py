"""Group free routes into models, attach benchmark evidence, score and tier them.

The formula, with every constant in ``config.json``:

1. Per model and benchmark, one value. Independent results win: per source the best
   matched configuration, then the median across sources. With no independent result, the
   median of publisher-reported results times ``publisher_discount``.
2. Per benchmark, normalise across the ranked pool (``normalisation``).
3. score = (sum of w*c*x + k*prior) / (sum of w*c + k) + context bonus, where w is the
   benchmark weight, c is 1 for independent and ``publisher_confidence`` for publisher-only
   evidence, x the normalised value, k ``shrinkage_weight`` and prior ``shrinkage_prior``.
   Missing benchmarks add nothing to either sum, so they shrink the score toward the prior
   instead of counting as zero. Evidence = sum of w*c.
   With ``family_weights`` set, steps 3's mean is taken per benchmark family and the
   family means are mixed by those fixed weights.
4. Tier = the first tier whose minimum share of the top score, minimum evidence and tool
   requirement the model meets. Limit tags (rate caps, promotions, data sharing) are reported, not scored.
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict

from . import load_config
from .discovery import Route
from .matcher import best_matches, match

CFG = load_config()


class Model:
    def __init__(self, routes: list[Route]):
        self.routes = sorted(routes, key=lambda r: (r.gateway, r.route_id))
        self.identities = [i for r in self.routes for i in r.identities]
        self.observations: list[dict] = []
        self.values: dict[str, dict] = {}
        self.score = None
        self.evidence = 0.0
        self.breakdown: list[dict] = []
        self.tier = None
        self.reason = ""

    @property
    def key(self) -> str:
        return self.routes[0].key()

    @property
    def label(self) -> str:
        # The display name the catalogues give, shortest first (free suffixes vary).
        names = sorted({r.name for r in self.routes}, key=len)
        return names[0]

    @property
    def kind(self) -> str:
        kinds = {r.kind for r in self.routes}
        return "chat" if "chat" in kinds else sorted(kinds)[0]

    @property
    def tools(self) -> bool:
        return any(r.tools for r in self.routes)

    @property
    def context(self) -> int | None:
        vals = [r.context for r in self.routes if r.context]
        return max(vals) if vals else None

    @property
    def tags(self) -> dict:
        out = {}
        for r in self.routes:
            for k, v in r.tags.items():
                out.setdefault(k, []).append(f"{r.gateway} {r.route_id}: {v}")
        return out


def group_routes(routes: list[Route]) -> list[Model]:
    """Union routes whose catalogue identities match (same release on several gateways)."""
    parent = list(range(len(routes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            if routes[i].route_id == routes[j].route_id or match(routes[i].identities, routes[j].identities):
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i, r in enumerate(routes):
        groups[find(i)].append(r)
    return sorted((Model(g) for g in groups.values()), key=lambda m: m.key)


def attach_identity_observations(models: list[Model], observations: list[dict]) -> dict:
    """Give each model the source variants that match it at its strongest identity level."""
    by_source = defaultdict(lambda: defaultdict(list))
    variant_ids = {}
    for ob in observations:
        by_source[ob["source"]][ob["variant"]].append(ob)
        variant_ids[ob["variant"]] = ob["identities"]
    log = {}
    for source, variants in by_source.items():
        candidates = {v: variant_ids[v] for v in variants}
        for m in models:
            keys, evidence = best_matches(m.identities, candidates)
            if not keys:
                continue
            log.setdefault(m.key, {})[source] = {k: list(evidence[k][1:]) for k in keys}
            if source.startswith("aa-") and source != "aa-coding-agents":
                # One AA configuration per model: the matched variant with the highest index.
                keys = [max(keys, key=lambda k: (variants[k][0].get("variant_index") or -1, len(variants[k])))]
            for k in keys:
                m.observations.extend(variants[k])
    return log


def attach_route_observations(models: list[Model], observations: list[dict], live_hosts: dict) -> None:
    """Evidence-file records keyed by route. A host already read live for a model is skipped."""
    by_route = {r.key(): m for m in models for r in m.routes}
    seen = set()
    for ob in observations:
        m = by_route.get(ob["route"])
        if not m:
            continue
        if ob["host"] in live_hosts.get(m.key, set()):
            continue
        # The same record is repeated for every route of a release; count it once.
        sig = (m.key, ob["benchmark"], ob["host"], ob["setting"], ob["value"], ob.get("benchmark_name"))
        if sig in seen:
            continue
        seen.add(sig)
        m.observations.append(ob)


def _value(obs: list[dict]) -> tuple[float, bool, list[dict]]:
    """(value, independent, the observations used) for one model and benchmark."""
    indep = [o for o in obs if o["independent"]]
    pool = indep or obs
    per_source = defaultdict(list)
    for o in pool:
        per_source[o["host"] if o["source"] == "evidence-file" else o["source"]].append(o)
    best = [max(v, key=lambda o: o["value"]) for v in per_source.values()]
    value = statistics.median(o["value"] for o in best)
    if not indep:
        value *= CFG["scoring"]["publisher_discount"]
    return value, bool(indep), best


def _normalise(values: dict[str, float]) -> dict[str, float]:
    method = CFG["scoring"]["normalisation"]
    xs = list(values.values())
    hi, lo = max(xs), min(xs)
    if method == "ratio_to_max":
        return {k: (v / hi if hi > 0 else 0.0) for k, v in values.items()}
    if method == "minmax":
        return {k: ((v - lo) / (hi - lo) if hi > lo else 1.0) for k, v in values.items()}
    if method == "zscore":
        mu = statistics.mean(xs)
        sd = statistics.pstdev(xs) or 1.0
        return {k: 0.5 * (1 + math.erf((v - mu) / sd / math.sqrt(2))) for k, v in values.items()}
    raise ValueError(f"unknown normalisation {method!r}")


def ranked(m: Model) -> str | None:
    """Why a model is left out of the ranking, or None when it is ranked."""
    if m.kind not in CFG["ranked_kinds"]:
        return f"interface is {m.kind}, not a tool-using chat model"
    if "router" in m.tags:
        return "router: picks among other models, so one rank would hide the routing"
    return None


def score(models: list[Model]) -> None:
    sc = CFG["scoring"]
    pool = [m for m in models if ranked(m) is None]
    for m in models:
        by_bench = defaultdict(list)
        for o in m.observations:
            by_bench[o["benchmark"]].append(o)
        m.values = {}
        for b, obs in by_bench.items():
            value, indep, used = _value(obs)
            m.values[b] = {"raw": value, "independent": indep, "used": used}
    norm = {}
    for b in CFG["benchmarks"]:
        vals = {m.key: m.values[b]["raw"] for m in pool if b in m.values}
        if vals:
            norm[b] = _normalise(vals)
    lo_ctx, hi_ctx = math.log2(sc["context_floor_tokens"]), math.log2(sc["context_full_tokens"])
    for m in models:
        reason = ranked(m)
        if reason:
            m.reason = reason
            continue
        num = den = 0.0
        m.breakdown = []
        for b, spec in CFG["benchmarks"].items():
            if b not in m.values:
                continue
            v = m.values[b]
            c = 1.0 if v["independent"] else sc["publisher_confidence"]
            x = norm[b][m.key]
            num += spec["weight"] * c * x
            den += spec["weight"] * c
            m.breakdown.append({"benchmark": b, "family": spec["family"], "raw": round(v["raw"], 3),
                                "independent": v["independent"], "normalised": round(x, 4),
                                "weight": spec["weight"], "confidence": c,
                                "contribution": round(spec["weight"] * c * x, 4),
                                "sources": [{"value": o["value"], "host": o["host"], "setting": o["setting"],
                                             "url": o["url"], "date": o["date"]} for o in v["used"]]})
        ctx = m.context
        ctx_x = 0.0
        if ctx:
            ctx_x = min(1.0, max(0.0, (math.log2(ctx) - lo_ctx) / (hi_ctx - lo_ctx)))
        k, prior = sc["shrinkage_weight"], sc["shrinkage_prior"]
        m.evidence = den
        families = sc.get("family_weights")
        if families:
            # Each family is shrunk on its own, then the families are mixed by fixed weights,
            # so a pile of general benchmarks cannot stand in for missing coding evidence.
            m.family_scores = {}
            for fam, fw in families.items():
                rows = [b for b in m.breakdown if b["family"] == fam]
                fn = sum(b["contribution"] for b in rows)
                fd = sum(b["weight"] * b["confidence"] for b in rows)
                m.family_scores[fam] = round((fn + k * prior) / (fd + k), 4)
            base = sum(families[f] * v for f, v in m.family_scores.items()) / sum(families.values())
        else:
            base = (num + k * prior) / (den + k)
        m.score = base + sc["context_bonus_weight"] * ctx_x
        m.context_component = round(sc["context_bonus_weight"] * ctx_x, 4)
        m.base = base
    placed = [m for m in models if m.score is not None and m.evidence >= CFG["tiers"]["unplaced_below_evidence"]]
    top = max((m.score for m in placed), default=0.0)
    for m in models:
        if m.score is not None:
            m.tier = assign_tier(m, top)


def assign_tier(m: Model, top: float):
    """Tier cut-offs are fractions of the best placed score, so they survive a change of
    normalisation or weights without retuning."""
    tiers = CFG["tiers"]
    if m.evidence < tiers["unplaced_below_evidence"]:
        m.reason = "no matched benchmark evidence"
        return None
    m.score_of_top = m.score / top if top else 0.0
    for t in tiers["thresholds"]:
        if m.score_of_top >= t["min_score_of_top"] and m.evidence >= t["min_evidence"] and (m.tools or not t["requires_tools"]):
            return t["tier"]
    return tiers["thresholds"][-1]["tier"]
