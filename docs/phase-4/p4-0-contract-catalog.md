# P4.0 Contract Catalog

Status: implemented for local generated-only validation; runtime remains disabled.

## Contract Boundary

P4.0 introduces closed Pydantic v2 contracts for hypotheses, evidence,
adaptive-lane results, rules, proposed alerts, provider metadata, blocked
queries, timeline entries, review decisions, retention holds, and operator UI
state. Unknown fields are rejected. Every durable document is bounded to 64
KiB of canonical JSON and receives a deterministic SHA-256 identity.

Chronology records occurrence, observation, receipt, durable recording, and
optional correction as distinct UTC timestamps. Geographic metadata is WGS84
GeoJSON with bounded points or closed polygons. Provenance identifies an opaque
source, producing activity, attributable agent, policy, transaction, and
generated-only status without claiming formal W3C PROV conformance.

The hypothesis graph is authoritative. The flat projection is explicitly
versioned and digest-bound so a future read model cannot introduce conclusions
that do not exist in the source graph. Evidence roles include supporting,
contradicting, missing, stale, superseding, and retracting observations.

## Authority And Privacy

All police-intelligence contracts use `mandatory_review`, `operational=false`,
and `generated_only=true`. `future_autonomous_action` is rejected. Bounded
system-health metadata is allowed only for generated records and is not an
alert or enforcement authority.

The guardrail walker rejects identity, biometric, sensitive-trait, guilt,
intent, vehicle-owner, watchlist-identity, credential, code, SQL, arbitrary
destination, raw-provider, and locator fields at any nesting depth. It also
enforces depth, node-count, and byte limits before persistence.

## Control Plane

The API can create draft rules and disabled generated provider metadata when
the test-only feature flag is explicitly enabled. It can list or retrieve
rules, providers, hypotheses, proposed alerts, and timelines. Rule status may
move from draft to validated or retired, but validation does not execute the
rule. Every mutation requires an authenticated typed role, department scope,
an operator reason, and optimistic `If-Match` for updates.

P4.0 has no correlation executor, rule evaluator, provider transport, alert
lifecycle worker, notification, dispatch, scheduler, or deployment path.

## Persistence

Revision `0012_intelligence_control_plane` creates ten new stores and reuses
the existing transactional stream outbox for unpublished rule-change records.
SQLite is limited to single-process generated development. PostgreSQL applies
application filters plus forced row-level security on every new
department-scoped table. Database constraints preserve generated-only,
nonoperational, disabled-provider, and absent-credential invariants.

Machine-readable snapshots are in `contracts/phase-4/intelligence-contracts.json`,
`contracts/phase-4/openapi.json`, and `contracts/phase-4/database.json`.
