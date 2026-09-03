# Structured Review V(5,3,1) — Resolution Semantics

**Date:** 2026-09-02
**Scope:** Four-outcome totality + floor-before-cost ordering (Phase 2 council requirement)
**Settings:** V(5,3,1) — 5 personas, 3 rounds, 1 converged output. Probes between rounds verified claims against current code/schema.

## Reviewers

1. **Formal methods** — totality, exhaustiveness, dead states
2. **Adversarial routing** — can a floor be inverted to buy a cheaper route?
3. **Operator UX** — are the four outcomes distinguishable under stress?
4. **Privacy & safety** — does the resolver leak or coerce on privacy floors?
5. **Calibration / cost** — does accepted-result cost ever masquerade as a floor?

## Round 1 — critiques

1. *Formal:* The spec's "resolved plus degradation notice" is not a distinct terminal state — it's `resolved` with an attached notice. The four-outcome claim holds only if `resolved_with_degradation` is treated as a separate outcome in the type system, not as a wrapper. **Require enum tagging.**
2. *Adversarial:* The draft allowed `provider_health` as a floor ("prefer healthy"). That collapses a ranking signal into a floor, permitting cost to override health under scarcity. Health must stay a ranking tiebreaker, never a floor — except `down` (unreachable) which is a true availability block, not a preference.
3. *Operator:* `routing_policy_unavailable` vs `routing_blocked` are hard to tell apart: both say "try something else." Need distinct `reason` + `safe_default` semantics: `policy_unavailable` means "no lane binding exists or all failed hard floors but data was complete"; `blocked` means "I cannot decide because a required fact is missing or a required harness is absent." Keep the names, clarify in code.
4. *Privacy:* `privacy_allow_paid: False` was optional (None = allow). Default must be "allow" to avoid over-blocking, but a request that *doesn't* declare privacy should not silently route to `paid` when `free` exists at equal capability. Clarify: privacy is a floor only when declared; otherwise it is a cost preference encoded in price_class ranking, not a block.
5. *Calibration:* `accepted_result_cost` could indirectly encode a capability floor if `measured_task_class_performance` were folded into cost (e.g. low capability -> high retry -> high cost). That would make cost defeat a capability floor by ranking, violating C2. **Require decomposition:** floors filter first, then cost ranks survivors *without* re-injecting capability.
6. *Formal (extra, collapsed):* Staleness handling introduced a non-total path: fresh survivors empty + stale survivors present -> degradation, but if `allow_stale=False` and stale only, should that be `resolved_with_degradation` or `blocked`? Current draft chooses degradation, which is correct per C3: staleness is declared, not inferred as absence. Must document the choice.

## Round 2 — re-review of drafted resolver

**Changes applied before round 2:**

- Outcome enum explicitly four-valued (`resolved`, `resolved_with_degradation`, `routing_policy_unavailable`, `routing_blocked`). No wrapper type.
- `_fails_floor` separated from ranking; `resolve()` filters by floors (including harness eligibility) before sorting by `accepted_result_cost`. Verified: reordering the two blocks in source swaps verdict on a crafted fixture (cheap but below capability floor vs dear but above) — probe CONFIRMED inversion impossible when floors run first.
- Health removed from `_fails_floor`; it ranks after cost (healthy first among equal-cost ties, but never eliminates). `down` stays as `provider_health` but elimination for `down` is via ranking penalty + future admission control, not a floor — documented as deliberate to avoid conflating reachability with preference. (Revisit if a lane requires hard availability.)
- Privacy floor semantics documented in `FloorSpec` docstring: only active when `privacy_allow_paid is False`.
- `accepted_result_cost` audited: it does NOT read `measured_task_class_performance`, so capability cannot leak into cost. Probe: `grep` confirms no reference to performance inside `cost.py`.
- Staleness: `fresh_survivors` vs `stale_survivors` split with `request.allow_stale` gate; all-stale pool resolves with `resolved_with_degradation` + notice, not `blocked`. Documented in resolver docstring.

**Verdicts:** 4 ACCEPT, 1 ACCEPT-WITH-CHANGE (adversarial: "prove with property test, not just code review").

## Round 3 — convergence

**Ship-blocker from round 2:** "prove, don't assert" floor-before-cost. Resolution: add property test `test_floor_before_cost_property` that generates random registries/requests, asserts no floor-violating winner is ever returned. Test included in `tests/test_resolver_property.py`.

**Arbiter:** No open ship-blockers. The property test is the acceptance proof for C2; the council record is the design proof. One residual dissent preserved below.

## Resulting changes (to resolver + cost + docs)

- `resolver/resolver.py` outcome enum is four-valued; harness eligibility folded into floor phase.
- `resolver/cost.py` kept capability-free; constant table exposed for audit.
- `docs/council-resolution-semantics.md` (this file) becomes the resolution-semantics decision record.

## Preserved dissent (not resolved, boundary for revisit)

**Adversarial reviewer dissent:** `provider_health == "down"` should be a hard elimination (availability floor), not a ranking penalty. The current design will still surface a `down` binding as winner if it is the only fresh survivor with the cheapest cost, relying on downstream admission control to reject it. That is safe but wasteful: the resolver knows reachability and could fail faster. Revisit after one month of health data — if `down` bindings ever win, promote `down` to a hard floor (Council boundary per A2 §6: admission control ownership).

*If no council dissent had existed, this section would say so plainly.*
