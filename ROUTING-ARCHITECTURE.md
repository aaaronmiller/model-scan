# Model selection, fallback, and quota: how it works

Status as of 2026-07-30. Marks what is **built and tested**, what is
**designed only**, and what is **unresolved**.

---

## The one-sentence version

A request names a Claude model and effort level; that pair selects a **tier**;
the tier's candidate list is filtered for eligibility, priced against **current
quota**, and ordered; the winner is substituted transparently; the response's
cost and rate-limit headers feed back into the quota state that priced it.

---

## Data flow

```
REQUEST                                   FEEDBACK
   |                                          ^
   v                                          |
[1] slot_grid      model+effort -> tier       |
   |                                          |
   v                                          |
[2] candidates     from routing snapshot      |
   |                                          |
   v                                          |
[3] hard filters   eligibility, not ranking   |
   |                                          |
   v                                          |
[4] pricing        quota -> effective cost    |
   |                                          |
   v                                          |
[5] ordering       deterministic, explainable |
   |                                          |
   v                                          |
[6] fallback chain best first                 |
   |                                          |
   v                                          |
[7] redirect       harness never knows        |
   |                                          |
   +--> request sent --> response ------------+
                         cost + headers
                         [8] spend_ledger
                         [9] quota_meter
                         [10] adaptive_limiter
```

---

## Selection

### [1] `slot_grid.py` — what was asked for

**Purpose.** Turn a harness-visible request into a routing identity.

**Function.** A constrained harness such as Claude Code can only name vendor
models, but every request carries a model **and** an effort level. That pair is
the unit, not the model: the same family at `low` and at `max` differ in cost,
latency, and capability. Two independent sources agree on this. MRIS 2.3 states
the atomic routing identity is provider plus model id plus effort plus feature
configuration. The classifier archive states effort names are not equivalent
across models and each must be calibrated separately.

Fifteen pairs collapse to **four tiers**, matching what `claude-code-proxy`
already implements:

| Family | Tier | Proxy env keys |
| --- | --- | --- |
| haiku | `SMALL` | `SMALL_MODEL`, `SMALL_ENDPOINT`, `SMALL_API_KEY`, ... |
| sonnet | `MIDDLE` | `MIDDLE_*` |
| opus | `BIG` | `BIG_*` |
| fable | `XBIG` | `XBIG_*` |

An unrecognised model returns no tier and the request **passes through to the
vendor untouched**. Silence is the correct behaviour for something we do not
understand.

Each slot also carries:

- `min_rank`, a capability **floor** on the classifier ladder (1 = most capable,
  18 = cheapest). A floor, not a target.
- `eval_mode`, `free` or `cost_basis`, per the recovered 2026-05-20 directive:
  auxiliary selections use free, primary and delegated use a cost basis.
- `reserve_fraction`, larger for long-horizon slots so multi-day work does not
  begin on a window about to reset.

### [2] Candidates

**Purpose.** Supply what could serve this tier.

**Function.** Read from the routing snapshot's `slots`, each a ranked candidate
list with `api_model`, `provider`, `fitness`, `price_blended`, `has_tools`,
`has_vision`. Produced offline by Model Scan. **Scoring never runs on the
request path**; the gateway binds a published snapshot.

### [3] Hard filters — eligibility, not preference

**Purpose.** Remove what cannot serve, before anything is ranked.

**Function.** Each rejection records a reason, so any selection can be
explained:

| Reason | Meaning |
| --- | --- |
| `unresolved_identity` | no usable `api_model` or `provider` |
| `blocklisted` | provider or model on the snapshot blocklist |
| `requires_tools` / `requires_vision` | slot needs a capability the candidate lacks |
| `price_unknown_under_budget_policy` | unpriced under a budget policy |
| `provider_unhealthy` | provider marked inaccessible |
| `below_capability_floor` | known ladder rank worse than the slot's floor |
| `not_free_under_free_eval_mode` | priced candidate in a free-only slot |
| `quota_exhausted` | no remaining capacity |

Two deliberate asymmetries:

- A candidate whose rank is **unknown** is not excluded by a floor. Refusing to
  route on missing evidence would strand slots, and the meter's principle is to
  fail to unknown rather than fabricate.
- A candidate whose **price** is unknown **is** excluded from a free-only slot.
  Spending by accident is worse than declining.

### [4] Pricing — where quota enters selection

**Purpose.** Express quota state as a cost the ranker can use.

**Function.** Two terms, because one alone is insufficient.

**Multiplicative, `opportunity_cost()`.** Scales nominal price by expiry
urgency. Capacity approaching reset with work queued becomes *cheaper*, because
unused capacity has no salvage value. Exhausted returns infinity. An unknown
reading returns nominal unchanged, so ignorance never makes a provider look
attractive.

**Additive, `depletion_penalty()`.** Survives a zero price. This exists because
of a real bug: free candidates have nominal cost zero, and zero scaled by
anything is zero, so quota state had **no effect at all** on the entire
authorized free tier. A nearly-exhausted provider won on fitness and would have
failed mid-request.

The additive term models **rejection risk, not thrift**. It is zero above a
headroom threshold of 0.25 and rises quadratically below it. A half-full window
carries no meaningful risk and must not be penalised, or a provider with **no
quota data at all** would outrank a healthy measured one and ignorance would
become an advantage.

### [5] Ordering

```
(effective_cost, rank_key, -fitness, api_model)
```

- **cost** ascending.
- **rank_key** implements *cheapest-adequate*: among candidates already clearing
  the floor, prefer the **weakest qualifying** one. Taking the strongest spends
  scarce high-capability quota on trivial work, the "strong models used for
  trivial tasks" failure MRIS names.
- **fitness** breaks remaining ties.
- **api_model** makes ordering stable, so identical inputs always produce
  identical output.

---

## Fallback

### [6] The chain

**Purpose.** Recover from failure without re-deciding.

**Function.** Resolution emits an **ordered chain** of survivors, best first.
`chosen` is simply the head. Walking the chain is availability fallback; it is
**never** quality escalation. The plan requires those kept distinct, and this is
where that separation lives.

Two fallback mechanisms exist, at different times:

| | Trigger | When | Where |
| --- | --- | --- | --- |
| **Reactive** | request failed | after a rejection | LiteLLM cascade, circuit breaker, cooldown |
| **Proactive** | quota low | before sending | `slot_resolver` |

The second is the point of the quota work. Exhaustion is knowable *before*
failure, so a candidate near zero is passed over at resolution time. That
converts a recovered error into an avoided one.

Degradation is graded, never fatal:

- no quota data: static ranking, recorded in `notes`
- malformed quota: ignored rather than trusted
- all candidates excluded: unresolved, with reasons
- unresolved slot: **omitted** from the redirect table, so the caller keeps its
  existing vendor configuration rather than routing into nothing

### [7] Redirect

**Purpose.** Apply the decision without the harness knowing.

**Function.** `{vendor_model: actual_model}`. For a constrained harness the
gateway substitutes transparently. For an open harness (Codex, Kilo, OMP) the
same resolver output is bound directly in settings. **One resolver, two delivery
modes** — if redirection logic lived inside the Claude Code path, the open
harnesses would grow a second divergent implementation.

The proxy already proves the mechanism for one slot: a request for
`claude-3-5-haiku-20241022` is served Nemotron.

---

## Quota

Three metering shapes, because providers genuinely differ. Modelling one as
another produces confident wrong numbers.

| Shape | Example | Remaining is | Resets |
| --- | --- | --- | --- |
| **Budget window** | OpenCode Go, 12 USD / 5h | budget minus spend **in the current window** | yes, on a period |
| **Pre-paid balance** | Google, OpenAI, Anthropic 20 USD | initial minus **all spend ever** | **no** |
| **Rate-limited** | Kilo, OpenRouter free | not computable in advance | rolling |

A pre-paid balance modelled as a window would report itself **full again every
five hours**. Hence `CreditBalance` is a separate type from `BudgetWindow`, and
it carries no `reset_at` unless the credit genuinely expires.

### [8] `spend_ledger.py` — what we spent

**Purpose.** Turn estimates into measurements.

**Function.** Append-only JSONL. Windows are fixed periods anchored to an epoch,
not trailing averages, because providers reset on a boundary. Mismatched units
are ignored rather than summed. Corrupt or truncated lines are skipped, so a
crash costs at most one line.

Token-count estimates are **excluded as a spend source**. That source documents
severe undercount; a caller records the cost it actually incurred or records
nothing.

`utilization()` reports `pace` and `projected_waste` — not just what is left,
but whether the current burn rate will leave capacity to expire unused. That is
what "use every quota" actually needs.

### [9] `quota_meter.py` — what remains

**Purpose.** Publish the `provider_quota.json` the snapshot consumes.

**Function.** Pattern A parses provider rate-limit headers, the highest
precedence source. A named provider scheme is a **preference with generic
fallback**, not an exclusive filter, since providers vary in which header set
they emit.

Source precedence: live measured, then local accounting, then estimate, then
unknown. Among equals the **tightest** window binds, because the smallest
remaining fraction is what actually stops work.

Every reading carries `confidence`, `provenance`, `observed_at`,
`account_scope`, and `resource`. Scope matters because one provider can meter
several independent pools — a pre-paid balance and a free tier at the same
provider. `merge_readings` **raises** on mixed scopes rather than averaging, or
a drained balance would appear refilled by an unrelated allowance.

An unknown reading is **omitted** from the published payload, never guessed. The
shared `quotaState` contract requires `remaining_fraction` and forbids extra
properties, so a guess would be the only alternative.

### [10] `adaptive_limiter.py` — inferring what is not published

**Purpose.** Give rate-limited providers a capacity signal.

**Function.** Implements the 2026-07-05 directive: adaptive rate limiting from
server refusal codes without advance knowledge of limits. Additive-increase,
multiplicative-decrease — the control law that makes TCP congestion control
stable without knowing link capacity.

- success nudges the allowed rate up by a constant
- refusal cuts it by a factor, compounding on consecutive refusals
- the rate never climbs back above a rate already known to be refused, or it
  oscillates across the limit forever

Three constraints from the wording of the directive:

- **"without knowing limits in advance"** — inferred headroom is `None` until a
  refusal is actually observed. Inventing a ceiling before seeing one is a guess.
- **"while continuing work"** — it reports a delay and never sleeps, blocks, or
  cancels. Pacing, not stopping.
- A **transport error is not a rate signal**. Slowing for a dropped connection
  conflates unavailability with throttling.

Output is always `estimated`, never `live`, so any real provider header
overrides it through normal precedence.

---

## The objective

Recorded directive: use every quota, all the way, every day. An earlier
adjudication had **rejected** "maximize remaining quota" as a routing objective.
Both are right, and the resolution is not to pick one:

**Define cost as opportunity cost, and cheapest-adequate produces maximum
utilization on its own.** Quota that expires unused has zero salvage value, so
as reset approaches its true cost tends to zero, and a cheapest-adequate router
consumes it without being told to. The defect was never the objective; it was
pricing a use-it-or-lose-it resource as though it were durable.

Consequence: the primary engineering task is the **meter**, not a new allocator.

---

## Component summary

| File | Purpose | State |
| --- | --- | --- |
| `slot_grid.py` | request to tier, floors, eval mode, reserves | built |
| `slot_resolver.py` | filter, price, order, chain, redirect table | built |
| `quota_meter.py` | headers, windows, balances, precedence, publish | built |
| `spend_ledger.py` | spend accounting, utilization, waste projection | built |
| `adaptive_limiter.py` | AIMD inference for unmetered providers | built |
| `gateway_bridge.py` | capture in, config out, provider resolution | built |
| `gateway_cli.py` | refresh, resolve, publish, utilization, preflight | built |

188 tests. Nothing above performs network access; the gateway does.

---

## Unresolved

1. **Two tier abstractions.** The proxy's four tiers are authority. The
   fifteen-slot grid is now bound to them, but the proxy has no notion of slots
   and the grid is not yet what configures the proxy. One must become the
   configurator.
2. **`XBIG` is a partial tier.** Source binds `XBIG_MODEL`, `XBIG_ENDPOINT`,
   `XBIG_API_KEY` only. The 2026-07-06 directive asked for "reasoning, etc all
   adapted", so `XBIG_MODEL_REASONING`, `XBIG_CASCADE`, and
   `XBIG_SYSTEM_PROMPT` are missing. Tracked by `tier_gaps()`.
3. **Provider-level quota only.** `provider_quota` is keyed by provider, so the
   288-to-1 shadow-price spread *within* OpenCode Go is not representable. A
   per-model extension needs a contract change.
4. **Loop not closed in production.** The gateway runs but still serves the
   hand-written aliases and records no spend. The callback is written and not
   registered.
5. **Ladder ranks are not published.** `min_rank` enforcement needs an
   `api_model` to rank map that Model Scan does not yet emit.
