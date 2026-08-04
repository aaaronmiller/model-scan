from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import slot_resolver as sr

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def candidate(
    api_model: str,
    provider: str,
    *,
    fitness: float = 50.0,
    price: float | None = 0.0,
    tools: bool = True,
    vision: bool = False,
) -> dict:
    return {
        "model_id": api_model.split("/")[-1],
        "provider": provider,
        "api_model": api_model,
        "fitness": fitness,
        "price_blended": price,
        "has_tools": tools,
        "has_vision": vision,
    }


def slot(*candidates: dict, label: str = "Primary", eval_mode: str = "free") -> dict:
    return {
        "label": label,
        "eval_mode": eval_mode,
        "best": candidates[0] if candidates else None,
        "candidates": list(candidates),
    }


def quota(remaining: float, *, reset_in_hours: float | None = 4.0, source: str = "live") -> dict:
    state: dict = {"remaining_fraction": remaining, "source": source}
    if reset_in_hours is not None:
        state["reset_at"] = (NOW + timedelta(hours=reset_in_hours)).isoformat().replace("+00:00", "Z")
    return state


# ------------------------------------------------------------- core behaviour


def test_exhausted_provider_is_skipped_before_a_request_is_made():
    """The whole point: reroute at resolution, not after a rejection."""
    res = sr.resolve_slot(
        "R1_primary",
        slot(candidate("groq/a", "groq", fitness=90), candidate("openrouter/b", "openrouter", fitness=60)),
        {"groq": quota(0.0), "openrouter": quota(0.8)},
        now=NOW,
    )
    assert res.resolved
    assert res.chosen["api_model"] == "openrouter/b"
    assert [e.reason for e in res.excluded] == [sr.EXCLUDED_QUOTA_EXHAUSTED]
    assert res.mode == sr.MODE_QUOTA_AWARE


def test_among_free_candidates_highest_fitness_wins():
    res = sr.resolve_slot(
        "R1_primary",
        slot(candidate("p/low", "p", fitness=10), candidate("p/high", "p", fitness=95)),
        {"p": quota(0.9)},
        now=NOW,
    )
    assert res.chosen["api_model"] == "p/high"


def test_cheaper_provider_beats_more_fit_expensive_one():
    res = sr.resolve_slot(
        "R1_primary",
        slot(
            candidate("paid/strong", "paid", fitness=99, price=10.0),
            candidate("free/ok", "free", fitness=70, price=0.0),
        ),
        {},
        now=NOW,
    )
    assert res.chosen["api_model"] == "free/ok"


def test_fallback_chain_is_ordered_and_includes_chosen():
    res = sr.resolve_slot(
        "R1_primary",
        slot(
            candidate("a", "pa", fitness=10),
            candidate("b", "pb", fitness=90),
            candidate("c", "pc", fitness=50),
        ),
        {},
        now=NOW,
    )
    assert [c["api_model"] for c in res.fallback_chain] == ["b", "c", "a"]
    assert res.fallback_chain[0] is res.chosen


def test_resolution_is_deterministic_across_repeated_calls():
    args = (
        "R1_primary",
        slot(candidate("x", "p", fitness=50), candidate("y", "p", fitness=50)),
        {"p": quota(0.5)},
    )
    first = sr.resolve_slot(*args, now=NOW)
    second = sr.resolve_slot(*args, now=NOW)
    assert [c["api_model"] for c in first.fallback_chain] == [
        c["api_model"] for c in second.fallback_chain
    ]


def test_ties_break_stably_by_api_model():
    res = sr.resolve_slot(
        "R1_primary",
        slot(candidate("zzz", "p", fitness=50), candidate("aaa", "p", fitness=50)),
        {},
        now=NOW,
    )
    assert [c["api_model"] for c in res.fallback_chain] == ["aaa", "zzz"]


# ------------------------------------------------------------- exclusions


def test_each_exclusion_reason_is_reported():
    res = sr.resolve_slot(
        "R7_vision",
        slot(
            candidate("blocked/m", "blocked"),
            candidate("notools/m", "pa", tools=False),
            candidate("novision/m", "pb", vision=False),
            candidate("good/m", "pc", vision=True),
        ),
        {},
        blocklist=["blocked"],
        require_tools=True,
        require_vision=True,
        now=NOW,
    )
    reasons = {e.reason for e in res.excluded}
    assert sr.EXCLUDED_BLOCKLISTED in reasons
    assert sr.EXCLUDED_NO_TOOLS in reasons
    assert sr.EXCLUDED_NO_VISION in reasons
    assert res.chosen["api_model"] == "good/m"


def test_unresolved_identity_is_excluded_not_crashed():
    res = sr.resolve_slot(
        "R1_primary",
        slot({"api_model": "", "provider": "", "fitness": 90, "price_blended": 0.0,
              "has_tools": True, "has_vision": False, "model_id": "x"},
             candidate("ok/m", "p")),
        {},
        now=NOW,
    )
    assert res.chosen["api_model"] == "ok/m"
    assert any(e.reason == sr.EXCLUDED_UNRESOLVED_IDENTITY for e in res.excluded)


def test_unknown_price_excluded_only_under_budget_policy():
    s = slot(candidate("unpriced/m", "p", price=None), candidate("priced/m", "q", price=1.0),
             eval_mode="cost_basis")
    lenient = sr.resolve_slot("R1", s, {}, now=NOW)
    strict = sr.resolve_slot("R1", s, {}, require_known_price=True, now=NOW)
    assert lenient.chosen["api_model"] == "unpriced/m"  # treated as nominal 0
    assert strict.chosen["api_model"] == "priced/m"
    assert any(e.reason == sr.EXCLUDED_UNKNOWN_PRICE for e in strict.excluded)


def test_unhealthy_provider_is_excluded():
    res = sr.resolve_slot(
        "R1",
        slot(candidate("down/m", "down", fitness=99), candidate("up/m", "up", fitness=10)),
        {},
        provider_health={"down": False, "up": True},
        now=NOW,
    )
    assert res.chosen["api_model"] == "up/m"
    assert any(e.reason == sr.EXCLUDED_PROVIDER_UNHEALTHY for e in res.excluded)


# ------------------------------------------------------------- degraded paths


def test_missing_quota_degrades_to_static_ranking_not_failure():
    res = sr.resolve_slot("R1", slot(candidate("a/m", "a", fitness=80)), None, now=NOW)
    assert res.resolved
    assert res.mode == sr.MODE_STATIC
    assert any("static" in n for n in res.notes)


def test_malformed_quota_state_is_ignored_rather_than_trusted():
    res = sr.resolve_slot(
        "R1",
        slot(candidate("a/m", "a")),
        {"a": {"remaining_fraction": "not-a-number"}},
        now=NOW,
    )
    assert res.resolved
    assert res.mode == sr.MODE_STATIC


def test_empty_slot_reports_empty_not_crash():
    res = sr.resolve_slot("R1", slot(), {}, now=NOW)
    assert not res.resolved
    assert res.mode == sr.MODE_EMPTY


def test_all_excluded_yields_unresolved_with_reasons():
    res = sr.resolve_slot(
        "R1",
        slot(candidate("a/m", "a"), candidate("b/m", "b")),
        {"a": quota(0.0), "b": quota(0.0)},
        now=NOW,
    )
    assert not res.resolved
    assert len(res.excluded) == 2
    assert "UNRESOLVED" in res.explain()


# ------------------------------------------------------------- expiry pricing


def test_capacity_about_to_expire_is_preferred_over_idle_capacity():
    """Use-it-or-lose-it must actually change the chosen candidate."""
    res = sr.resolve_slot(
        "R1",
        slot(
            candidate("slow/m", "slow", fitness=50, price=1.0),
            candidate("expiring/m", "expiring", fitness=50, price=1.0),
            eval_mode="cost_basis",
        ),
        {
            "slow": quota(0.9, reset_in_hours=20.0),
            "expiring": quota(0.9, reset_in_hours=0.05),
        },
        now=NOW,
    )
    assert res.chosen["api_model"] == "expiring/m"


def test_reserve_protection_pushes_a_low_window_down_the_chain():
    s = slot(
        candidate("low/m", "low", fitness=50, price=1.0),
        candidate("high/m", "high", fitness=50, price=1.0),
        eval_mode="cost_basis",
    )
    q = {"low": quota(0.05, reset_in_hours=4.0), "high": quota(0.90, reset_in_hours=4.0)}
    guarded = sr.resolve_slot("R1", s, q, reserve_fraction=0.30, now=NOW)
    assert guarded.chosen["api_model"] == "high/m"


# -------------------------------------------- regression: zero-price blindness


def test_free_candidate_with_depleted_quota_is_demoted():
    """Regression. Free candidates have nominal price 0, and a multiplicative
    discount on 0 is 0, so quota state used to have no effect at all and the
    highest-fitness candidate won even at 0.2 percent remaining. Caught by an
    end-to-end run, not by the unit tests, which is why this exists."""
    res = sr.resolve_slot(
        "R1_primary",
        slot(
            candidate("groq/best", "groq", fitness=95, price=0.0),
            candidate("go/ok", "opencode-go", fitness=70, price=0.0),
        ),
        {"groq": quota(0.002, reset_in_hours=0.01), "opencode-go": quota(0.83, reset_in_hours=5)},
        now=NOW,
    )
    assert res.chosen["api_model"] == "go/ok"
    assert res.fallback_chain[-1]["api_model"] == "groq/best"


def test_healthy_measured_quota_is_not_penalised_against_unknown_quota():
    """A provider with no quota data must not outrank a healthy measured one.
    Otherwise ignorance becomes an advantage."""
    res = sr.resolve_slot(
        "R1",
        slot(candidate("known/m", "known", fitness=90), candidate("silent/m", "silent", fitness=10)),
        {"known": quota(0.5)},
        now=NOW,
    )
    assert res.chosen["api_model"] == "known/m"


@pytest.mark.parametrize("remaining", [0.9, 0.5, 0.25])
def test_windows_above_headroom_carry_no_risk_penalty(remaining):
    res = sr.resolve_slot(
        "R1",
        slot(candidate("q/m", "q", fitness=90), candidate("none/m", "none", fitness=80)),
        {"q": quota(remaining, reset_in_hours=None)},
        now=NOW,
    )
    assert res.chosen["api_model"] == "q/m"


@pytest.mark.parametrize("remaining", [0.15, 0.05, 0.001])
def test_windows_below_headroom_lose_to_an_unmetered_peer(remaining):
    res = sr.resolve_slot(
        "R1",
        slot(candidate("q/m", "q", fitness=90), candidate("none/m", "none", fitness=80)),
        {"q": quota(remaining, reset_in_hours=None)},
        now=NOW,
    )
    assert res.chosen["api_model"] == "none/m"


# ------------------------------------------------------------- snapshot level


def test_resolve_snapshot_applies_per_slot_requirements():
    snapshot = {
        "slots": {
            "R1_primary": slot(candidate("a/m", "a", fitness=80)),
            "R7_vision": slot(
                candidate("novis/m", "b", fitness=99, vision=False),
                candidate("vis/m", "c", fitness=10, vision=True),
            ),
        },
        "provider_quota": {"a": quota(0.5)},
        "blocklist": [],
    }
    results = sr.resolve_snapshot(
        snapshot, requirements={"R7_vision": {"require_vision": True}}, now=NOW
    )
    assert results["R1_primary"].chosen["api_model"] == "a/m"
    assert results["R7_vision"].chosen["api_model"] == "vis/m"


def test_snapshot_blocklist_applies_to_every_slot():
    snapshot = {
        "slots": {"R1": slot(candidate("bad/m", "bad", fitness=99), candidate("ok/m", "ok"))},
        "provider_quota": {},
        "blocklist": ["bad"],
    }
    results = sr.resolve_snapshot(snapshot, now=NOW)
    assert results["R1"].chosen["api_model"] == "ok/m"


def test_provider_health_object_shape_is_understood():
    snapshot = {
        "slots": {"R1": slot(candidate("d/m", "d", fitness=99), candidate("u/m", "u"))},
        "provider_health": {"d": {"accessible": False}, "u": {"accessible": True}},
        "blocklist": [],
    }
    results = sr.resolve_snapshot(snapshot, now=NOW)
    assert results["R1"].chosen["api_model"] == "u/m"


# ------------------------------------------------------------- redirect table


def test_redirect_map_builds_the_substitution_table():
    resolutions = {
        "R9_session_search": sr.Resolution(
            slot_id="R9_session_search",
            label="Session search",
            chosen=candidate("nvidia/nemotron", "nvidia"),
        )
    }
    table = sr.redirect_map(resolutions, {"claude-3-5-haiku-20241022": "R9_session_search"})
    assert table == {"claude-3-5-haiku-20241022": "nvidia/nemotron"}


def test_unresolved_slot_is_omitted_so_caller_keeps_static_config():
    resolutions = {"R1": sr.Resolution(slot_id="R1", label="Primary", chosen=None)}
    assert sr.redirect_map(resolutions, {"claude-opus-4-5": "R1"}) == {}


def test_explain_is_human_readable():
    res = sr.resolve_slot(
        "R1",
        slot(candidate("a/m", "a", fitness=90), candidate("b/m", "b", fitness=10)),
        {"a": quota(0.5)},
        now=NOW,
    )
    text = res.explain()
    assert "R1" in text and "a/m" in text and "fallback" in text


# ------------------------------------------- eval_mode: free vs cost basis


def test_free_slot_refuses_a_priced_candidate():
    """Recovered directive 2026-05-20: auxiliary selections use the free option.
    A free slot must refuse spend outright, not merely rank it lower."""
    res = sr.resolve_slot(
        "S01_haiku",
        slot(candidate("paid/m", "p", fitness=99, price=5.0),
             candidate("free/m", "q", fitness=10, price=0.0)),
        {},
        now=NOW,
    )
    assert res.chosen["api_model"] == "free/m"
    assert any(e.reason == sr.EXCLUDED_NOT_FREE for e in res.excluded)


def test_free_slot_treats_unknown_price_as_not_free():
    """Spending by accident is worse than declining."""
    res = sr.resolve_slot(
        "S01_haiku", slot(candidate("mystery/m", "p", price=None)), {}, now=NOW
    )
    assert not res.resolved
    assert any(e.reason == sr.EXCLUDED_NOT_FREE for e in res.excluded)


def test_cost_basis_slot_permits_spend():
    res = sr.resolve_slot(
        "S15_fable_max",
        slot(candidate("paid/m", "p", fitness=99, price=5.0), eval_mode="cost_basis"),
        {},
        now=NOW,
    )
    assert res.resolved and res.chosen["api_model"] == "paid/m"


def test_requirement_eval_mode_overrides_the_published_snapshot():
    s = slot(candidate("paid/m", "p", price=5.0), eval_mode="cost_basis")
    tightened = sr.resolve_slot("S01_haiku", s, {}, eval_mode="free", now=NOW)
    assert not tightened.resolved


def test_absent_eval_mode_does_not_restrict_anything():
    s = {"label": "x", "best": None, "candidates": [candidate("paid/m", "p", price=5.0)]}
    res = sr.resolve_slot("R1", s, {}, now=NOW)
    assert res.resolved
