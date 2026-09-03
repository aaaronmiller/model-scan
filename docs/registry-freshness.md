# Registry Freshness and Staleness (C3)

**When a consumer must refresh:** at the start of a substantial orchestration run, and on material runtime evidence such as quota exhaustion, provider failure, sustained rate limiting, model unavailability, or resumption of a long-lived workflow.

## Per-field freshness

Every field in `registry/schema.json` that carries data has a corresponding entry in the binding's `freshness` map:

```json
"freshness": {
  "quota_state": {"observed_at": "2026-09-02T00:00:00Z", "source": "cpa-manager-plus", "expires_at": "2026-09-02T06:00:00Z"},
  "provider_health": {"observed_at": "2026-09-02T00:00:00Z", "source": "health-runner"}
}
```

- `observed_at` — ISO datetime when the value was last observed
- `source` — which producer observed it (e.g. `cpa-manager-plus`, `management-api`, `probe`, `models.dev`)
- `expires_at` — optional; when absent the value is considered fresh until superseded. When present and `now >= expires_at`, the field is stale.

A field that is absent reports absent (no key). A field that is unknown reports `"unknown"` as value; it may still carry a freshness stamp explaining how the unknown was determined.

## Consumer behavior

- **Fresh path:** resolver ranks among `fresh_survivors` (bindings with no expired freshness stamps on floor-relevant fields).
- **Degraded path:** if `fresh_survivors` is empty but `stale_survivors` exist, resolver returns `resolved_with_degradation` with `degradation_notice: "stale_registry: ..."` (gate 5). The caller must verify freshness before relying on ranking.
- **Blocked vs unavailable:** staleness never produces `routing_blocked`; it produces degradation. Quota exhaustion or provider failure observed at runtime should trigger a refresh and re-resolve.

## Which fields expire?

- `quota_state` — typically expires at the provider's reset boundary or after a short TTL (e.g. 5m for rate-limit headroom).
- `provider_health` — short TTL (minutes) because health is volatile.
- Static facts (`context_limit`, `modalities`, `tool_capability`) — no `expires_at`; refreshed on registry rebuild / provider catalog refresh.

No field defaults to a fabricated value when stale; unknown is reported as `"unknown"`.
