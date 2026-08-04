from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import slot_grid as sg
import slot_resolver as sr

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_grid_has_fifteen_slots_with_unique_ids():
    assert len(sg.SLOTS) == 15
    assert len({s.slot_id for s in sg.SLOTS}) == 15


def test_every_family_and_effort_pair_is_present_once():
    pairs = [(s.family, s.effort) for s in sg.SLOTS]
    assert len(pairs) == len(set(pairs))
    assert ("haiku", "medium") in pairs
    for effort in ("low", "medium", "high", "xhigh"):
        assert ("sonnet", effort) in pairs
    for effort in ("low", "medium", "high", "xhigh", "max"):
        assert ("opus", effort) in pairs
        assert ("fable", effort) in pairs


def test_capability_floor_is_monotonic_within_a_family():
    """More effort must never mean a weaker floor."""
    for family in ("sonnet", "opus", "fable"):
        slots = [s for s in sg.SLOTS if s.family == family]
        slots.sort(key=lambda s: sg.EFFORT_ORDER.index(s.effort))
        ranks = [s.min_rank for s in slots]
        assert ranks == sorted(ranks, reverse=True), f"{family} floors not monotonic: {ranks}"


# ------------------------------------------------------------- lookup


@pytest.mark.parametrize(
    "model,effort,expected",
    [
        ("claude-opus-5", "high", "S08_opus_high"),
        ("claude-sonnet-5", "low", "S02_sonnet_low"),
        ("claude-fable-5", "max", "S15_fable_max"),
        ("claude-haiku-4-5-20251001", None, "S01_haiku"),
    ],
)
def test_real_vendor_ids_resolve(model, effort, expected):
    slot = sg.slot_for(model, effort)
    assert slot is not None and slot.slot_id == expected


def test_family_matching_survives_version_changes():
    assert sg.slot_for("claude-opus-4-8-20260101", "medium").slot_id == "S07_opus_medium"
    assert sg.slot_for("anthropic/claude-sonnet-9", "high").slot_id == "S04_sonnet_high"


def test_unknown_model_returns_none_so_request_passes_through():
    assert sg.slot_for("gpt-5.5", "high") is None
    assert sg.slot_for("", "high") is None
    assert sg.slot_for(None, "high") is None  # type: ignore[arg-type]


def test_haiku_collapses_any_effort_to_one_slot():
    for effort in ("low", "medium", "high", "xhigh", "max", None, "nonsense"):
        assert sg.slot_for("claude-haiku-4-5", effort).slot_id == "S01_haiku"


def test_sonnet_max_maps_to_xhigh_since_the_grid_has_no_sonnet_max():
    assert sg.slot_for("claude-sonnet-5", "max").slot_id == "S05_sonnet_xhigh"


def test_unknown_effort_falls_back_to_medium_rather_than_failing():
    assert sg.slot_for("claude-opus-5", "banana").slot_id == "S07_opus_medium"
    assert sg.slot_for("claude-opus-5", None).slot_id == "S07_opus_medium"


# ------------------------------------------------------------- integration


def test_alias_table_feeds_redirect_map_end_to_end():
    aliases = sg.alias_table(
        [("claude-opus-5", "high"), ("claude-haiku-4-5", None), ("gpt-5.5", "high")]
    )
    assert aliases == {"claude-opus-5": "S08_opus_high", "claude-haiku-4-5": "S01_haiku"}
    assert "gpt-5.5" not in aliases, "unknown vendor models must pass through untouched"

    resolutions = {
        "S08_opus_high": sr.Resolution(
            slot_id="S08_opus_high",
            label="Opus high",
            chosen={"api_model": "opencode-go/deepseek-v4-pro", "provider": "opencode-go"},
        ),
        "S01_haiku": sr.Resolution(slot_id="S01_haiku", label="Haiku", chosen=None),
    }
    table = sr.redirect_map(resolutions, aliases)
    assert table == {"claude-opus-5": "opencode-go/deepseek-v4-pro"}
    assert "claude-haiku-4-5" not in table, "unresolved slot must keep vendor default"


def test_requirements_are_shaped_for_the_resolver():
    reqs = sg.requirements_for_slots()
    assert set(reqs) == {s.slot_id for s in sg.SLOTS}
    assert reqs["S15_fable_max"]["reserve_fraction"] == 0.20
    assert reqs["S02_sonnet_low"]["reserve_fraction"] == 0.0
    assert reqs["S01_haiku"]["require_tools"] is True


def test_long_horizon_slots_carry_a_reserve_and_cheap_ones_do_not():
    """Long work must not start on a window about to reset."""
    assert sg.SLOTS_BY_ID["S15_fable_max"].reserve_fraction > 0
    assert sg.SLOTS_BY_ID["S14_fable_xhigh"].reserve_fraction > 0
    assert sg.SLOTS_BY_ID["S01_haiku"].reserve_fraction == 0.0


def test_requirements_flow_through_resolve_snapshot():
    def cand(api, prov, fit):
        return {
            "model_id": api, "provider": prov, "api_model": api, "fitness": fit,
            "price_blended": 0.0, "has_tools": True, "has_vision": False,
        }

    snapshot = {
        "slots": {
            "S15_fable_max": {
                "label": "Fable max", "eval_mode": "free", "best": None,
                "candidates": [cand("low/m", "low", 90), cand("high/m", "high", 40)],
            }
        },
        "provider_quota": {
            "low": {"remaining_fraction": 0.05,
                    "reset_at": (NOW + timedelta(hours=4)).isoformat().replace("+00:00", "Z")},
            "high": {"remaining_fraction": 0.95,
                     "reset_at": (NOW + timedelta(hours=4)).isoformat().replace("+00:00", "Z")},
        },
        "blocklist": [],
    }
    results = sr.resolve_snapshot(snapshot, requirements=sg.requirements_for_slots(), now=NOW)
    # The reserve on S15 must push the nearly-empty window down despite fitness.
    assert results["S15_fable_max"].chosen["api_model"] == "high/m"


def test_capability_floor_is_enforced_not_merely_declared():
    """Regression. The grid declared min_rank but the resolver ignored it, so a
    long-horizon slot could be served by a model far below its floor."""
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    snapshot = {
        "slots": {
            "S15_fable_max": {"label": "Fable max", "eval_mode": "free", "best": None,
                              "candidates": [cand("weak/m", "a", 95), cand("strong/m", "b", 40)]},
        },
        "provider_quota": {},
        "blocklist": [],
    }
    ranks = {"weak/m": 14, "strong/m": 1}
    results = sr.resolve_snapshot(
        snapshot, requirements=sg.requirements_for_slots(), candidate_ranks=ranks, now=NOW
    )
    res = results["S15_fable_max"]
    assert res.chosen["api_model"] == "strong/m", "floor must beat fitness"
    assert any(e.reason == sr.EXCLUDED_BELOW_CAPABILITY_FLOOR for e in res.excluded)


def test_unranked_candidate_is_not_excluded_by_a_floor():
    """Missing evidence must not strand a slot."""
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    res = sr.resolve_slot(
        "S15_fable_max",
        {"label": "x", "eval_mode": "free", "best": None, "candidates": [cand("unranked/m", "a", 50)]},
        {},
        min_rank=1,
        candidate_ranks={"someone-else/m": 9},
        now=NOW,
    )
    assert res.resolved and res.chosen["api_model"] == "unranked/m"


def test_cheap_slot_accepts_a_low_rank_candidate():
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    res = sr.resolve_slot(
        "S01_haiku",
        {"label": "Haiku", "eval_mode": "free", "best": None, "candidates": [cand("cheap/m", "a", 30)]},
        {},
        min_rank=sg.SLOTS_BY_ID["S01_haiku"].min_rank,
        candidate_ranks={"cheap/m": 15},
        now=NOW,
    )
    assert res.resolved


def test_cheapest_adequate_wins_so_strong_models_are_not_spent_on_trivial_work():
    """A cheap slot must take the weakest qualifying candidate, not the strongest.
    Otherwise scarce high-capability quota is burned on trivial tasks."""
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    res = sr.resolve_slot(
        "S01_haiku",
        {"label": "Haiku", "eval_mode": "free", "best": None,
         "candidates": [cand("strong/m", "a", 95), cand("weak/m", "b", 30)]},
        {},
        min_rank=15,
        candidate_ranks={"strong/m": 4, "weak/m": 15},
        now=NOW,
    )
    assert res.chosen["api_model"] == "weak/m", "cheapest adequate, not strongest"
    # The strong one stays available as fallback rather than being excluded.
    assert [c["api_model"] for c in res.fallback_chain] == ["weak/m", "strong/m"]


def test_hard_slot_still_takes_the_only_qualifying_candidate():
    def cand(api, prov, fit):
        return {"model_id": api, "provider": prov, "api_model": api, "fitness": fit,
                "price_blended": 0.0, "has_tools": True, "has_vision": False}

    res = sr.resolve_slot(
        "S13_fable_high",
        {"label": "Fable high", "eval_mode": "free", "best": None,
         "candidates": [cand("strong/m", "a", 95), cand("weak/m", "b", 30)]},
        {},
        min_rank=3,
        candidate_ranks={"strong/m": 3, "weak/m": 15},
        now=NOW,
    )
    assert res.chosen["api_model"] == "strong/m"


def test_coverage_reports_uncovered_slots():
    resolutions = {"S01_haiku": sr.Resolution("S01_haiku", "Haiku", chosen={"api_model": "x"})}
    cov = sg.coverage(resolutions)
    assert cov.total == 15 and cov.resolved == 1
    assert "S15_fable_max" in cov.unresolved
    assert 0.0 < cov.fraction < 1.0


# ------------------------------------------------------------- helpers


def test_eligible_by_rank_applies_the_floor():
    slot = sg.SLOTS_BY_ID["S07_opus_medium"]  # floor 7
    ranks = {"strong": 3, "exact": 7, "weak": 12}
    assert sg.eligible_by_rank(slot, ranks) == ["strong", "exact"]


def test_reasoning_budget_matches_published_formula():
    assert sg.reasoning_budget("medium", 100_000) == 50_000
    assert sg.reasoning_budget("low", 100_000) == 20_000
    assert sg.reasoning_budget("max", 1_000_000) == 128_000  # clamped high
    assert sg.reasoning_budget("low", 100) == 1_024  # clamped low


# ------------------- the proxy's four-tier system is the routing authority
# Recorded directive 2026-07-06: four tiers, opus/sonnet/haiku plus an Xbig
# mapping to fable. Confirmed in claude-code-proxy source. The fifteen pairs are
# harness inputs that select a tier plus a reasoning level, not fifteen
# independent routing identities.


def test_every_slot_binds_to_a_proxy_tier():
    for s in sg.SLOTS:
        assert s.tier in sg.TIER_ORDER


def test_family_to_tier_matches_the_proxy_mapping():
    assert sg.tier_for("claude-haiku-4-5") == sg.TIER_SMALL
    assert sg.tier_for("claude-sonnet-5") == sg.TIER_MIDDLE
    assert sg.tier_for("claude-opus-5") == sg.TIER_BIG
    assert sg.tier_for("claude-fable-5") == sg.TIER_XBIG


def test_non_claude_model_has_no_tier_and_passes_through():
    assert sg.tier_for("gpt-5.5") is None
    assert sg.tier_for("") is None


def test_fifteen_pairs_collapse_to_four_tiers():
    """The grid must not be a second routing identity alongside the tiers."""
    assert len({s.tier for s in sg.SLOTS}) == 4
    assert len(sg.SLOTS) == 15


def test_env_keys_follow_the_proxy_naming():
    keys = sg.env_keys_for(sg.TIER_BIG)
    assert "BIG_MODEL" in keys and "BIG_ENDPOINT" in keys
    assert "BIG_API_KEY" in keys and "BIG_MODEL_REASONING" in keys


def test_unknown_tier_yields_no_keys():
    assert sg.env_keys_for("HUGE") == []
    assert sg.env_keys_for("") == []


def test_xbig_tier_is_recorded_as_incomplete():
    """The 2026-07-06 directive asked for 'reasoning, etc all adapted'. XBIG
    currently binds only MODEL, ENDPOINT and API_KEY, so the gap is tracked
    rather than silently treated as done."""
    gaps = sg.tier_gaps()
    assert sg.TIER_XBIG in gaps
    assert "XBIG_MODEL_REASONING" in gaps[sg.TIER_XBIG]
    # The three fully implemented tiers must not appear as gaps.
    for tier in (sg.TIER_SMALL, sg.TIER_MIDDLE, sg.TIER_BIG):
        assert tier not in gaps


def test_slot_env_keys_resolve_through_its_tier():
    assert "XBIG_MODEL" in sg.SLOTS_BY_ID["S15_fable_max"].env_keys
    assert "SMALL_MODEL" in sg.SLOTS_BY_ID["S01_haiku"].env_keys
