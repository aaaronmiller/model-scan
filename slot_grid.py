"""The slot grid: harness-visible model/effort pairs mapped to routing slots.

A constrained harness such as Claude Code can only name vendor models, but every
request still carries one of a fixed set of model-and-effort pairs. Each pair is
a routing slot. The gateway resolves the slot to whichever candidate currently
fits, and the harness never knows.

Two facts make the pair, rather than the model, the unit:

- MRIS 2.3: the atomic routing identity is provider plus canonical model id plus
  effort level plus feature configuration. A model family is not a candidate.
- The classifier archive: effort names are not equivalent across models and each
  must be calibrated separately.

``min_rank`` is the capability floor drawn from the classifier ladder, where 1
is the most capable and 18 the cheapest. It is a *floor*, not a target: a slot
may resolve to anything at or above its floor, which is what lets a free model
serve a slot whose vendor default was expensive.

This module is data plus lookup. It performs no selection and no network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

# Effort levels, ordered weakest to strongest. Names are harness-facing.
EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")

# Effort ratios published by the classifier archive, used for reasoning-budget
# derivation rather than selection.
EFFORT_RATIO: dict[str, float] = {
    "off": 0.10,
    "low": 0.20,
    "medium": 0.50,
    "high": 0.80,
    "xhigh": 0.95,
    "max": 0.95,
}


# Evaluation basis, matching the routing snapshot contract's enum.
#
# Recovered user directive, 2026-05-20: "Add a way to define which selections
# are free and which use a cost basis: primary model, delegated model, and
# primary fallbacks use cost basis while auxiliary models use free option."
#
# So the free-versus-paid decision is assigned per role, not globally. Auxiliary
# work is free-only; primary and delegated work may spend.
EVAL_COST_BASIS = "cost_basis"
EVAL_FREE = "free"

# ---------------------------------------------------------------------------
# The proxy's real tier system.
#
# `claude-code-proxy` already implements a four-tier routing identity, and it is
# the authority. Recorded user directive, 2026-07-06: "adjust the big/med/small
# settings (which map to the claude opus/sonnet/haiku models generally) to
# include an Xbig model which maps to fable ... permit a four tier system vs a
# 3 ... enable_xhigh_endpoint, reasoning, etc all adapted."
#
# Confirmed in source: `model_manager.py` maps the opus/sonnet/haiku families,
# `config_resolver.py` binds XBIG_MODEL, XBIG_ENDPOINT, XBIG_API_KEY and
# ENABLE_XBIG_ENDPOINT, and `startup_display.py` renders the tiers in order.
#
# The fifteen model-and-effort pairs are harness *inputs*. They are not fifteen
# independent routing identities. Each pair resolves to a tier plus a reasoning
# level, which is what the proxy actually configures. Treating them as separate
# slots created a second, competing abstraction alongside a system that already
# existed.
TIER_XBIG = "XBIG"
TIER_BIG = "BIG"
TIER_MIDDLE = "MIDDLE"
TIER_SMALL = "SMALL"

TIER_ORDER = (TIER_SMALL, TIER_MIDDLE, TIER_BIG, TIER_XBIG)

# Family to tier, matching the proxy's own mapping.
FAMILY_TIER: dict[str, str] = {
    "haiku": TIER_SMALL,
    "sonnet": TIER_MIDDLE,
    "opus": TIER_BIG,
    "fable": TIER_XBIG,
}

# Environment keys the proxy reads per tier. XBIG is deliberately listed with
# the same shape as the others even though the current source binds only
# MODEL, ENDPOINT and API_KEY for it. The 2026-07-06 directive asked for
# "reasoning, etc all adapted", so the missing XBIG_MODEL_REASONING,
# XBIG_CASCADE, and XBIG_SYSTEM_PROMPT keys are an incomplete implementation of
# a stated requirement rather than an intentional omission.
TIER_ENV_SUFFIXES = (
    "_MODEL",
    "_ENDPOINT",
    "_API_KEY",
    "_MODEL_REASONING",
    "_CASCADE",
    "_SYSTEM_PROMPT",
    "_SYSTEM_PROMPT_FILE",
)

# Suffixes confirmed present in source per tier, as of 2026-07-30.
TIER_ENV_IMPLEMENTED: dict[str, tuple[str, ...]] = {
    TIER_SMALL: TIER_ENV_SUFFIXES,
    TIER_MIDDLE: TIER_ENV_SUFFIXES,
    TIER_BIG: TIER_ENV_SUFFIXES,
    TIER_XBIG: ("_MODEL", "_ENDPOINT", "_API_KEY"),
}


def tier_for(model: str) -> str | None:
    """Tier a vendor model belongs to, or ``None`` if it is not a Claude family."""

    family = _family_of(model)
    return FAMILY_TIER.get(family) if family else None


def env_keys_for(tier: str, *, implemented_only: bool = False) -> list[str]:
    """The proxy environment keys for a tier.

    ``implemented_only`` returns just the keys the source currently binds, which
    is how a caller can tell a configured tier from a fully supported one.
    """

    tier = str(tier or "").strip().upper()
    if tier not in FAMILY_TIER.values():
        return []
    suffixes = TIER_ENV_IMPLEMENTED[tier] if implemented_only else TIER_ENV_SUFFIXES
    return [f"{tier}{suffix}" for suffix in suffixes]


def tier_gaps() -> dict[str, list[str]]:
    """Tier keys the directive implies but the source does not yet bind."""

    return {
        tier: [k for k in env_keys_for(tier) if k not in env_keys_for(tier, implemented_only=True)]
        for tier in TIER_ORDER
        if set(TIER_ENV_IMPLEMENTED[tier]) != set(TIER_ENV_SUFFIXES)
    }


@dataclass(frozen=True)
class Slot:
    """One routing slot: a harness model/effort pair with a capability floor."""

    slot_id: str
    family: str
    effort: str
    label: str
    min_rank: int
    task_classes: tuple[str, ...] = ()
    require_tools: bool = True
    require_vision: bool = False
    # A slot whose work is long-running should not be routed to a window that
    # may expire mid-task, so it carries a reserve.
    reserve_fraction: float = 0.0
    # ``free`` restricts the slot to zero-price candidates. ``cost_basis``
    # permits spend. Assigned per the 2026-05-20 directive above.
    eval_mode: str = EVAL_FREE
    notes: str = ""

    @property
    def is_auxiliary(self) -> bool:
        return self.eval_mode == EVAL_FREE

    @property
    def tier(self) -> str:
        """The proxy tier this pair routes through.

        The tier is the real routing identity; the slot is the harness-visible
        pair that selects a tier plus a reasoning level.
        """

        return FAMILY_TIER[self.family]

    @property
    def env_keys(self) -> list[str]:
        return env_keys_for(self.tier)


# The fifteen slots. Families and efforts are the harness-visible grid;
# min_rank and task_classes come from the classifier ladder.
SLOTS: tuple[Slot, ...] = (
    Slot(
        "S01_haiku", "haiku", "medium", "Haiku: classification and extraction",
        min_rank=15,
        task_classes=("classification", "routing", "tagging", "extraction", "moderation"),
        notes="Claude Code uses this for plan-mode auxiliary thinking.",
    ),
    Slot(
        "S02_sonnet_low", "sonnet", "low", "Sonnet low: everyday edits",
        min_rank=16,
        task_classes=("single_function_generation", "docstrings", "format_conversion"),
    ),
    Slot(
        "S03_sonnet_medium", "sonnet", "medium", "Sonnet medium: production codegen",
        min_rank=14,
        task_classes=("single_file_codegen", "test_generation", "structured_output"),
    ),
    Slot(
        "S04_sonnet_high", "sonnet", "high", "Sonnet high: bounded refactor",
        min_rank=13,
        task_classes=("tool_calling_agent_loop", "test_generation_independent"),
    ),
    Slot(
        "S05_sonnet_xhigh", "sonnet", "xhigh", "Sonnet xhigh: multi-file refactor",
        min_rank=10,
        task_classes=("multi_file_refactor_bounded",),
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S06_opus_low", "opus", "low", "Opus low: reliable structured output",
        min_rank=13,
        task_classes=("structured_output", "extraction_strict"),
    ),
    Slot(
        "S07_opus_medium", "opus", "medium", "Opus medium: code review",
        min_rank=7,
        task_classes=("code_review", "structured_tool_use", "analysis"),
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S08_opus_high", "opus", "high", "Opus high: subtle debugging",
        min_rank=5,
        task_classes=("cross_file_debugging", "multi_file_refactor", "spec_decomposition"),
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S09_opus_xhigh", "opus", "xhigh", "Opus xhigh: architecture",
        min_rank=4,
        task_classes=("architecture_design", "schema_design", "deep_analysis"),
        reserve_fraction=0.10,
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S10_opus_max", "opus", "max", "Opus max: long-horizon analysis",
        min_rank=4,
        task_classes=("architecture_design", "long_horizon"),
        reserve_fraction=0.15,
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S11_fable_low", "fable", "low", "Fable low: bounded delegate",
        min_rank=12,
        task_classes=("structured_output", "bounded_codegen"),
    ),
    Slot(
        "S12_fable_medium", "fable", "medium", "Fable medium: decomposition",
        min_rank=9,
        task_classes=("decomposition", "planning"),
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S13_fable_high", "fable", "high", "Fable high: orchestrator default",
        min_rank=3,
        task_classes=("task_graph_decomposition", "turn_sequence", "deep_decomposition"),
        reserve_fraction=0.10,
        notes="Default orchestrator effort per the classifier archive.",
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S14_fable_xhigh", "fable", "xhigh", "Fable xhigh: hardest architecture",
        min_rank=2,
        task_classes=("architecture_hard", "long_horizon_coding", "ambiguous_multi_file"),
        reserve_fraction=0.15,
        eval_mode=EVAL_COST_BASIS,
    ),
    Slot(
        "S15_fable_max", "fable", "max", "Fable max: multi-day autonomy",
        min_rank=1,
        task_classes=("long_horizon_multi_day", "whole_repo_migration", "self_validating_ops"),
        reserve_fraction=0.20,
        notes="Highest floor. Reserve is large because the work spans windows.",
        eval_mode=EVAL_COST_BASIS,
    ),
)

SLOTS_BY_ID: dict[str, Slot] = {s.slot_id: s for s in SLOTS}


def _family_of(model: str) -> str | None:
    """Infer the family from a vendor model id.

    Matches on family token so version changes do not break the mapping. A
    vendor id we do not recognise returns ``None`` rather than a guess, and the
    caller then leaves the request untouched.
    """

    token = str(model or "").strip().lower()
    if not token:
        return None
    for family in ("haiku", "sonnet", "opus", "fable"):
        if family in token:
            return family
    return None


def normalize_effort(effort: str | None, family: str) -> str:
    """Map a requested effort onto the grid, honouring per-family limits.

    Haiku has no effort axis in the grid, so any effort collapses to its single
    slot. Sonnet has no ``max`` in this grid, so ``max`` maps to ``xhigh``.
    Unknown values fall back to ``medium`` rather than failing, because refusing
    to route is worse than routing at a sane default.
    """

    value = str(effort or "").strip().lower()
    if family == "haiku":
        return "medium"
    if value not in EFFORT_ORDER:
        value = "medium"
    if family == "sonnet" and value == "max":
        return "xhigh"
    return value


def slot_for(model: str, effort: str | None = None) -> Slot | None:
    """Resolve a harness model/effort pair to a slot, or ``None`` if unknown."""

    family = _family_of(model)
    if family is None:
        return None
    normalized = normalize_effort(effort, family)
    for slot in SLOTS:
        if slot.family == family and slot.effort == normalized:
            return slot
    return None


def alias_table(requests: Iterable[tuple[str, str | None]]) -> dict[str, str]:
    """Build the ``{vendor_model: slot_id}`` map ``redirect_map`` expects.

    Pairs that do not resolve are omitted, so an unrecognised model is passed
    through to the vendor untouched rather than redirected somewhere arbitrary.
    A vendor model used with more than one effort is also omitted when those
    efforts map to different slots. LiteLLM aliases are keyed by model name
    only, so publishing one of those slots would silently redirect every other
    effort to the wrong target.
    """

    slots_by_model: dict[str, set[str]] = {}
    for model, effort in requests:
        slot = slot_for(model, effort)
        if slot is not None:
            slots_by_model.setdefault(model, set()).add(slot.slot_id)
    return {
        model: next(iter(slot_ids))
        for model, slot_ids in slots_by_model.items()
        if len(slot_ids) == 1
    }


def requirements_for_slots(slots: Iterable[Slot] | None = None) -> dict[str, dict[str, object]]:
    """Per-slot constraints in the shape ``slot_resolver.resolve_snapshot`` takes."""

    selected = tuple(slots) if slots is not None else SLOTS
    return {
        slot.slot_id: {
            "require_tools": slot.require_tools,
            "require_vision": slot.require_vision,
            "reserve_fraction": slot.reserve_fraction,
            "min_rank": slot.min_rank,
            "eval_mode": slot.eval_mode,
        }
        for slot in selected
    }


def eligible_by_rank(slot: Slot, candidate_ranks: Mapping[str, int]) -> list[str]:
    """Candidates meeting the slot's capability floor, best first.

    ``candidate_ranks`` maps ``api_model`` to a classifier ladder rank where a
    lower number is more capable. A candidate qualifies when its rank is at or
    above the floor, meaning numerically less than or equal to ``min_rank``.
    """

    qualified = [
        (rank, api_model)
        for api_model, rank in candidate_ranks.items()
        if isinstance(rank, int) and rank <= slot.min_rank
    ]
    qualified.sort()
    return [api_model for _, api_model in qualified]


def reasoning_budget(effort: str, max_tokens: int) -> int:
    """Reasoning budget from the archive's published formula.

    ``max(min(max_tokens * ratio, 128000), 1024)``. Recorded here so the ratio
    table has a single home; nothing in routing depends on it yet.
    """

    ratio = EFFORT_RATIO.get(str(effort or "").strip().lower(), EFFORT_RATIO["medium"])
    return max(min(int(max_tokens * ratio), 128_000), 1_024)


@dataclass
class GridCoverage:
    """How much of the grid a snapshot can currently serve."""

    total: int
    resolved: int
    unresolved: list[str] = field(default_factory=list)

    @property
    def fraction(self) -> float:
        return self.resolved / self.total if self.total else 0.0


def coverage(resolutions: Mapping[str, object]) -> GridCoverage:
    """Report which grid slots a resolution set actually covers.

    A partially covered grid is a normal operating state, not an error: an
    uncovered slot simply passes through to the vendor.
    """

    unresolved = [
        slot.slot_id
        for slot in SLOTS
        if not getattr(resolutions.get(slot.slot_id), "resolved", False)
    ]
    return GridCoverage(total=len(SLOTS), resolved=len(SLOTS) - len(unresolved), unresolved=unresolved)
