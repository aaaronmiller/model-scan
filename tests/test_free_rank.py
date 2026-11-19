"""Gates for the formula-only free-model ranking (free_rank/) and ardf_roles name matching.

1. No model names, versions or route ids as literals in scoring, matching or ranking code.
2. Matcher relations: same release matches, different versions and sizes never do.
3. Discovery applies each catalogue's own free rule.
4. Scoring: missing benchmarks shrink toward the prior instead of scoring zero; publisher
   results are discounted; independent results win.
5. Agreement statistics and ardf_roles' data-derived matching and quota multipliers.

Fixtures use invented names so this file stays independent of any live catalogue.
"""
from __future__ import annotations

import io
import json
import re
import sys
import tokenize
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from free_rank import agreement, discovery, rank  # noqa: E402
from free_rank.matcher import Identity, best_matches, match, relation, tokens  # noqa: E402

GUARDED = sorted((REPO / "free_rank").glob("*.py")) + [REPO / "ardf_roles.py"]
EVIDENCE = REPO / "free_rank" / "evidence" / "l1-free-models-2026-11-19.json"

# Ordinary English words, and the bare id of a router route ("openrouter/free"); a word
# match on these is not a model literal. Full names, ids and display names are checked.
COMMON_WORDS = {"free", "router", "north", "beam", "flint", "voice", "span", "decider", "one", "particle"}


def _reference_terms() -> set[str]:
    rows = json.loads(EVIDENCE.read_text())
    terms = set()
    for r in rows:
        for key in ("canonical_name", "model_family", "gateway_display_name", "model_id"):
            if r.get(key):
                terms.add(r[key])
        mid = r["model_id"]
        terms.add(mid.split(":", 1)[0].rsplit("/", 1)[-1])
        fam = r.get("model_family") or ""
        last = fam.split()[-1] if fam else ""
        if len(last) >= 4 and last.lower() not in COMMON_WORDS:
            terms.add(last)
    return {t for t in terms if len(t) >= 3 and t.lower() not in COMMON_WORDS}


def _strings_and_comments(path: Path) -> list[tuple[int, str]]:
    out = []
    with path.open() as fh:
        for tok in tokenize.generate_tokens(fh.readline):
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                out.append((tok.start[0], tok.string))
    return out


def test_gate_no_model_names_in_ranking_code():
    terms = _reference_terms()
    assert len(terms) > 50, "reference inventory did not load"
    hits = []
    for path in GUARDED:
        text = path.read_text()
        for term in terms:
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, re.I):
                hits.append(f"{path.name}: {term!r}")
    assert not hits, "model names in ranking code: " + ", ".join(sorted(hits))


VERSION_LIKE = re.compile(r"[A-Za-z][A-Za-z0-9]*[-_ ]v?\d+\.\d+|\bv\d+\.\d+")


def test_gate_no_version_literals_in_ranking_code():
    hits = []
    for path in GUARDED:
        for line, s in _strings_and_comments(path):
            for m in VERSION_LIKE.finditer(s):
                hits.append(f"{path.name}:{line}: {m.group(0)!r}")
    assert not hits, "version-like literals in ranking code: " + ", ".join(hits)


def test_gate_name_map_is_gone():
    import ardf_roles
    assert not hasattr(ardf_roles, "NAME_TO_ID")
    assert "NAME_TO_ID = {" not in (REPO / "ardf_roles.py").read_text()


# --- matcher -------------------------------------------------------------------------------

def test_same_release_matches_across_spellings():
    a = [Identity("Zorbo 3.1 Flash", "name", "Acme Labs")]
    b = [Identity("acme-labs/zorbo-3.1-flash:free", "id", "acme-labs")]
    assert match(a, b)[1] == "compact"


def test_different_versions_never_match():
    a = tokens(Identity("acme/zorbo-3.1-flash", "id", "acme"))
    b = tokens(Identity("acme/zorbo-3.2-flash", "id", "acme"))
    assert relation(a, b) is None


def test_size_relation_only_when_one_side_has_no_size():
    named = tokens(Identity("Zorbo 2", "name", "acme"))
    sized = tokens(Identity("acme/zorbo-2-120b-a12b", "id", "acme"))
    other = tokens(Identity("acme/zorbo-2-30b-a3b", "id", "acme"))
    assert relation(named, sized) == "size"
    assert relation(sized, other) is None


def test_bare_version_left_after_vendor_strip_does_not_match():
    a = [Identity("orgone/orgone-1", "id", "orgone")]
    b = [Identity("orgtwo-1", "id", "Orgtwo")]
    assert match(a, b) is None


def test_extra_variant_word_does_not_match():
    assert relation(tokens(Identity("Zorbo 4 Flash", "name")), tokens(Identity("zorbo-4", "id"))) is None


def test_canonical_id_beats_display_name():
    target = [Identity("acme/zorbo-5-flash-1017", "canonical", "acme"), Identity("Zorbo 5 Flash", "name", "acme")]
    cands = {"new": [Identity("zorbo-5-flash-1017", "id", "acme")], "old": [Identity("Zorbo 5 Flash", "name", "acme")]}
    keys, _ = best_matches(target, cands)
    assert keys == ["new"]


# --- discovery -----------------------------------------------------------------------------

def test_opencode_free_rule_uses_own_prices():
    raw = json.dumps({"data": [
        {"id": "zorbo-free", "name": "Zorbo Free", "type": "chat", "cost": {"text": {"input": {"price": 0}, "output": {"price": 0}}},
         "capabilities": {"tools": {"supported": True}}, "limit": {"context": 131072}},
        {"id": "zorbo-paid", "name": "Zorbo", "type": "chat", "cost": {"text": {"input": {"price": 1.0}, "output": {"price": 0}}}},
    ]}).encode()
    routes = discovery.parse("opencode-zen", raw)
    assert [r.route_id for r in routes] == ["zorbo-free"]
    assert routes[0].tools and routes[0].context == 131072


def test_kilo_requires_its_free_flag():
    raw = json.dumps({"data": [
        {"id": "acme/zorbo:free", "name": "Zorbo", "isFree": True, "pricing": {"prompt": "0", "completion": "0"}, "mayTrainOnYourPrompts": True},
        {"id": "acme/zorbo-zero", "name": "Zorbo Zero", "isFree": False, "pricing": {"prompt": "0", "completion": "0"}},
    ]}).encode()
    routes = discovery.parse("kilo", raw)
    assert [r.route_id for r in routes] == ["acme/zorbo:free"]
    assert "sharing" in routes[0].tags


def test_openrouter_needs_every_price_zero_and_marks_kind():
    raw = json.dumps({"data": [
        {"id": "acme/zorbo:free", "name": "Zorbo", "pricing": {"prompt": "0", "completion": "0", "request": "0"},
         "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}, "supported_parameters": ["tools"]},
        {"id": "acme/clip", "name": "Clip", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"input_modalities": ["text"], "output_modalities": ["video"]}},
        {"id": "acme/zorbo", "name": "Zorbo", "pricing": {"prompt": "0.000001", "completion": "0"}},
    ]}).encode()
    routes = {r.route_id: r for r in discovery.parse("openrouter", raw)}
    assert set(routes) == {"acme/zorbo:free", "acme/clip"}
    assert routes["acme/zorbo:free"].kind == "chat" and routes["acme/clip"].kind == "video"


# --- scoring -------------------------------------------------------------------------------

def _model(name, obs, context=262144):
    route = discovery.Route("opencode-zen", name, name, "chat", True, context, [Identity(name, "id")])
    m = rank.Model([route])
    m.observations = obs
    return m


def _ob(bench, value, independent=True, host="independent.example"):
    return {"benchmark": bench, "value": value, "independent": independent, "source": "fixture", "host": host,
            "url": "", "date": "", "setting": "", "variant": f"{host}:{bench}:{value}"}


def test_missing_benchmarks_shrink_toward_prior_not_zero():
    full = _model("a", [_ob("terminal_bench_4", 40), _ob("aa_intelligence", 30), _ob("swe_bench_verified", 70)])
    partial = _model("b", [_ob("terminal_bench_4", 40)])
    floor = _model("c", [_ob("terminal_bench_4", 0), _ob("aa_intelligence", 0), _ob("swe_bench_verified", 0)])
    rank.score([full, partial, floor])
    prior = rank.CFG["scoring"]["shrinkage_prior"]
    assert partial.score > floor.score
    assert partial.score < full.score
    # The partial model's absent families sit at the prior, not at zero.
    assert all(v == pytest.approx(prior) for f, v in partial.family_scores.items() if f != "agentic coding")


def test_publisher_results_discounted_and_independent_wins():
    pub = _model("p", [_ob("terminal_bench_4", 40, independent=False, host="publisher.example")])
    both = _model("q", [_ob("terminal_bench_4", 40, independent=False, host="publisher.example"), _ob("terminal_bench_4", 20)])
    rank.score([pub, both])
    assert pub.values["terminal_bench_4"]["raw"] == pytest.approx(40 * rank.CFG["scoring"]["publisher_discount"])
    assert both.values["terminal_bench_4"]["raw"] == 20 and both.values["terminal_bench_4"]["independent"]
    assert pub.evidence < both.evidence


def test_router_and_non_chat_routes_are_not_ranked():
    router = _model("r", [_ob("terminal_bench_4", 40)])
    router.routes[0].tags["router"] = "fixture"
    rank.score([router])
    assert router.score is None and "router" in router.reason


# --- agreement and ardf_roles --------------------------------------------------------------

def test_rank_correlations():
    assert agreement.kendall([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert agreement.kendall([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert agreement.spearman([1, 2, 3, 4], [1, 2, 4, 3]) == pytest.approx(0.8)


def test_reference_parser(tmp_path):
    md = tmp_path / "tiers.md"
    md.write_text("## Tier 1\n\n1. **Zorbo** · Zen `zorbo-free`\n2. **Quux** · `acme/quux:free`\n\n## Unplaced\n\n- **Blip** · `blip`\n")
    entries = agreement.parse_reference(md)
    assert [(e["name"], e["tier"], e["position"]) for e in entries] == [("Zorbo", 1, 1), ("Quux", 1, 2), ("Blip", None, 1)]


def test_ardf_usage_multipliers_come_from_registry_labels(tmp_path):
    import ardf_roles
    reg = tmp_path / "available.json"
    reg.write_text(json.dumps({"sub": [{"id": "zorbo-9", "name": "Zorbo 9 (3x usage)"}, {"id": "quux", "name": "Quux"}]}))
    assert ardf_roles.usage_multipliers(reg) == {"zorbo-9": 3.0}


def test_ardf_frontier_name_matches_registry_ids():
    import ardf_roles
    ids = {"zorbo-7.2": ["sub"], "acme/zorbo-7.2": ["router"], "zorbo-7.2-contributor": ["sub"], "zorbo-7.3": ["sub"]}
    got, _ = ardf_roles.match_ids("Zorbo 7.2 (xhigh)", "Acme", ids)
    assert got == ["acme/zorbo-7.2", "zorbo-7.2"]
    got, _ = ardf_roles.match_ids("Zorbo 7.2 (xhigh, Contributor pricing)", "Acme", ids)
    assert "zorbo-7.2-contributor" in got and "zorbo-7.3" not in got
