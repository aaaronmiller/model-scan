# Gateway deployment runbook

Everything up to this point is built and tested. The steps below are the ones
deliberately **not** performed automatically, because each is a credential
change, a deployment action, or a policy choice that the project's own
checkpoint rules reserve for a human.

Run `python3 gateway_cli.py preflight` at any point to see current state.

---

## Step 1. Decide the spend-history store

`general_settings.disable_spend_logs` is `false` in `hermes-gateway.yaml`, which
asks for persistence, but `DATABASE_URL` is unset.

**Option A, no database.** Set `disable_spend_logs: true` in the config. The
gateway runs, and spend accounting comes from `spend_ledger.py` via the callback
in `gateway_bridge.py` rather than from LiteLLM's own store. Fewest moving
parts, and the quota pipeline does not depend on a database.

**Option B, PostgreSQL.** Set `DATABASE_URL`. Gives LiteLLM native spend logs
and keys, at the cost of running a database on a machine with 7.6 GB of RAM that
crashed three times on 2026-07-29.

Option A is the smaller step and does not block anything in the quota pipeline.

## Step 2. Create the master key

`general_settings.master_key` resolves from `LITELLM_MASTER_KEY`, which is
unset. This is the single reason the proxy does not start.

It is a locally generated secret for a localhost-bound proxy, not a provider
credential. Generate one and export it in the shell profile that starts the
gateway:

```bash
python3 -c "import secrets; print('sk-local-' + secrets.token_urlsafe(32))"
```

Then add to the profile, replacing the placeholder with the generated value:

```bash
export LITELLM_MASTER_KEY='sk-local-REPLACE_ME'
```

Do not commit it. Do not reuse a provider key here.

## Step 3. Start the gateway

```bash
~/.litellm/venv/bin/litellm --config ~/.litellm/hermes-gateway.yaml --port 4000
```

Confirm it is up without spending anything:

```bash
python3 gateway_cli.py preflight
```

The `gateway listening` check should flip to OK.

## Step 4. Wire the spend and quota callback

In `hermes-gateway.yaml` under `litellm_settings`, register the bridge so every
completed request records its cost and any rate-limit headers:

```yaml
litellm_settings:
  success_callback: ["gateway_bridge.litellm_success_callback"]
```

The module must be importable by the gateway process, so start it with
`PYTHONPATH=/home/cheta/code/model-scan`.

This is what converts seeded estimates into measured readings. Until it is
wired, budget windows remain estimates and `utilization` reports 100 percent
projected waste, which is currently accurate.

## Step 5. Publish redirects

With a routing snapshot and a ladder-rank file:

```bash
python3 gateway_cli.py publish \
  --snapshot /path/to/routing_snapshot.json \
  --ranks    /path/to/ladder_ranks.json \
  --out      ~/.litellm/gateway-overrides.json
```

This writes `model_list` entries mapping each vendor model to its resolved
target. It does **not** edit the live config. Merge it deliberately, then
restart the gateway.

Verify before merging:

```bash
python3 gateway_cli.py resolve --snapshot ... --ranks ...
```

Slots showing `(vendor default)` have no qualifying candidate and will pass
through to Anthropic untouched. That is correct behaviour, not a failure.

## Step 6. Confirm the loop is closed

After some real traffic:

```bash
python3 gateway_cli.py refresh
python3 gateway_cli.py utilization
```

`refresh` should now show `source=live` for providers that emit rate-limit
headers, and `utilization` should show a non-zero `spent` with `projected_waste`
falling below 100 percent. That is the evidence the quota loop is actually
closed rather than merely wired.

---

## What remains a policy decision, not a step

- **Which paid accounts are in scope.** The per-role split from the 2026-05-20
  directive says primary and delegated slots may spend, but not which accounts
  are permitted. Nine slots are currently on a cost basis and will use whatever
  the snapshot offers them.
- **Stack adoption.** Whether to add the OpenTelemetry, Prometheus, and Grafana
  layer. Grafana has prior recorded intent; Kong and CrewAI have none.
- **Reserve policy.** Slot reserves are currently set by judgment, from 0.10 on
  architecture slots to 0.20 on multi-day autonomy. Real traffic should replace
  those with measured values.

## Rollback

Nothing in this runbook modifies existing behaviour until step 5 is merged and
the gateway is restarted.

To roll back: remove the merged `model_list` entries and restart. Clients
continue to reach the vendor directly. The quota pipeline files under
`~/.config/model-scan/` are inert data and can be left in place or deleted
without affecting routing.
