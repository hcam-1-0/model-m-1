# P3.0 Analytics Assignment Control Plane

Status: implemented, locally validated, and accepted under P3-G4 on
`codex/phase3-contracts-guardrails`.

## Purpose

The control plane records which immutable analytics pipeline configuration is
proposed for an authorized stream. It is configuration metadata only. It does
not read media, download artifacts, invoke inference, create alerts, or activate
analytics.

## Fail-Closed Invariants

Every P3.0 assignment is constrained to:

```text
desired_state   = paused
lifecycle_state = blocked
reason_code     = owner_gates_pending
```

These values are enforced independently by the request schemas, service layer,
SQLAlchemy models, and Alembic database checks. Responses also expose
`activation_eligible=false` and the blocking reasons
`runtime_unconfigured`, `taxonomy_unapproved`, and
`retention_policy_unapproved`. There is no activation endpoint.

An assignment references immutable pipeline/model digests, a taxonomy version,
policy digest, configuration digest, bounded sampling and queue-age settings,
normalized geometry versions, a derived-metadata retention class, and an
approval-record reference. It never stores model bytes, media, locators,
credentials, biometric templates, Government data, or owner records.

## Persistence

Alembic revision `0008_analytics_assignments` adds:

- `analytics_assignments`, uniquely keyed by stream and capability;
- `analytics_assignment_revisions`, with an immutable composite key of
  assignment ID and version;
- foreign keys to the existing stream and camera records;
- optimistic versioning and indexes for department/state and scoped lookup; and
- database checks for P3.0 lifecycle, confidence, sampling, queue-age, and
  retention-class bounds.

Application readiness now requires migration `0008`, both tables, and the
critical assignment columns. The migration has a tested downgrade to `0007` and
upgrade back to head.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/analytics-assignments` | Department-scoped filtered list |
| `POST` | `/streams/{stream_id}/analytics-assignments` | Create a blocked assignment |
| `GET` | `/analytics-assignments/{assignment_id}` | Read one authorized assignment |
| `PATCH` | `/analytics-assignments/{assignment_id}` | Update configuration with ETag |
| `GET` | `/analytics-assignments/{assignment_id}/revisions` | Read immutable history |

Reads require `camera.viewer`, `camera.editor`, or `platform.admin`. Mutations
require `camera.editor` or `platform.admin`, department access, and a bounded
`X-HCAM-Reason`. Unauthorized cross-department records are hidden as `404` and
lists return only the principal's scope.

Create returns `201`, `Location`, and `ETag: "1"`. Updates require an exact
quoted `If-Match` ETag. Missing, malformed, stale, conflicting, and unsafe
requests fail without changing the assignment. Material updates require a new
immutable configuration digest. All responses use `Cache-Control: no-store`.

## Transaction And Event Semantics

Each successful mutation commits the assignment, immutable revision, audit
record, and `hcam.analytics.model.deployment.changed.v1` outbox row in one
database transaction. The event is canonical-contract validated before commit,
contains only metadata, and uses the stream ID as its partition key. Consumers
remain at-least-once and must deduplicate by event ID.

Rejected service requests create sanitized failure audit records. Unsafe reason
text is replaced rather than echoed into responses or audit storage. Global
request-validation responses also omit rejected input values and validation
contexts while preserving the documented error location/type/message shape.

## Operational Visibility

The authenticated internal metrics endpoint exports identifier-free gauges for:

- total and P3.0-blocked assignments;
- retained immutable revisions;
- unpublished analytics deployment metadata; and
- recent create/update failures using only the bounded `operation` label.

The Phase 3 Grafana dashboard uses only those aggregate metrics. Prometheus
alerts detect a total-versus-blocked invariant mismatch, a sustained analytics
outbox backlog, and repeated assignment mutation failures. Metrics and alert
artifacts contain no assignment, camera, stream, actor, model, or locator label.

## Validation Evidence

The focused control-plane/migration/outbox/release suite passed 16 tests. The
complete analytics suite passed 79 tests with 94.67% branch coverage. The full
repository suite passed 504 tests with five expected PostgreSQL skips and
91.18% total coverage. Ruff, compilation, dependency checks, analytics contract
checks, Phase 3 OpenAPI/database drift checks, source distribution, and wheel
builds passed.

PostgreSQL 18 validation used a disposable loopback-only Docker container and
synthetic metadata. All five PostgreSQL integration tests passed. Alembic
upgrade, schema-drift check, downgrade to base, restore to head, second drift
check, and the post-restore integration rerun passed. The first drift check
found a missing analytics-model import in `migrations/env.py`; that defect was
fixed and is protected by the migration regression test. The container and its
volume were removed after validation.

## Remaining Gates

- P3.1 authorization permits generated-only data/evaluation foundation work;
  its implementation and acceptance exits remain pending; and
- non-generated datasets, model artifacts, runtime, decoding, inference, media
  access, and P3.2 each retain their exact evidence and authorization gates.
