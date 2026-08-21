# Model Scan implementation backtranslation audit

Date: 2026-08-15

## Verdict

PASS for the current MS-003, MS-005, MC-002, and local API tasks. The offline
suite passes 240 tests. The read-only API harness passes 48 checks. No live
provider, route, credential, or Gateway configuration changed.

This is an in-session reconstruction audit. The same session read the upstream
requirements and design before implementing the downstream files, so this is
not a blind or independent backtranslation.

## Reconstructed downstream contract

The implementation describes Model Scan as an advisory evidence producer:

1. ARDF publishes research evidence and policy through a hash-bound export.
2. Model Scan joins exact provider, model, harness, endpoint, and effort
   identities with published and task-attributed evidence.
3. Evidence content cannot attest to its own hash or validator result. A
   separate manifest binds content, schema, canonicalization, and validator.
4. Exact zero price stays zero. Unknown price stays unknown. Positive-log cost
   calibration cannot consume zero.
5. Role recommendations require typed fixtures, hard gates, adequate samples,
   confidence intervals, current evidence, and an exact evidence hash.
6. Provider catalog discovery does not prove callable, reachable, or
   policy-eligible state.
7. Gateway applies routing policy. Model Scan cannot emit an executable route
   or config patch.

## Surface map

| Downstream surface | Upstream obligation | Result |
| --- | --- | --- |
| `evidence_contract.py` and two schemas | MS-003 content, manifest, joins, custody, exact zero, abstention | CONFIRMED |
| `ardf_export.py` | Immutable ARDF input and field-by-field migration | CONFIRMED |
| `role_evaluation.py` | MS-005 typed roles, per-call telemetry, statistics, abstention, hash pin | CONFIRMED |
| `source_adapter.py` | MC-002 provenance, state semantics, freshness, retry, quarantine, change events | CONFIRMED |
| `api/main.py` | Current 15-slot view and fail-closed preview | CONFIRMED |
| `README.md` | Advisory-only authority boundary | CONFIRMED after correction |

## Findings

No critical or high drift remains in the named task scope.

### MEDIUM: live role winners are intentionally absent

The code validates fixture evaluation and statistical comparison, but it does
not claim current real-world role winners. No provider benchmark traffic was
authorized or run. This is an explicit abstention, not lost intent. A future
evidence-collection run needs named providers, cost authority, fixed fixtures,
and an isolated output version.

### MEDIUM: the current database is historical at the slot boundary

The latest local database contains legacy `R*` incumbents. The API still makes
the historical model evidence inspectable, but it serves the 15 code-owned
`S*` definitions and returns `status: abstain` for config preview. This matches
the fail-closed requirement and prevents stale recommendations from appearing
current.

### LOW: no automatic archive action

The Model Scraper package remains preserved. Its unique adapter behavior now
exists as a dependency-light Model Scan module with passing tests. Deleting or
archiving the old checkout needs an exact archive target and a separate
authorization. This is consistent with the MC-002 non-goal.

## Remediation result

- Corrected ARDF's row-count metadata to 2,839.
- Removed the unscoped global executor capability floor.
- Defined nine authoritative ARDF files while allowing supporting provenance
  files outside the immutable export.
- Rebuilt and validated ARDF without network access.
- Replaced the API's legacy slot projection with the current 15-slot contract.
- Replaced the vacuous tier and CORS checks with decisive assertions.
- Corrected the README's routing and configuration authority claims.

## Continue or pause

Close the four named implementation tasks. Do not generate live role winners,
apply a Gateway route, or archive Model Scraper from this audit. Those actions
need their own evidence or authority gate.
