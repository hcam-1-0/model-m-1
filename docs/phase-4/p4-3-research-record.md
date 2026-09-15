# P4.3 Alert Lifecycle And Orchestration Research Record

Status date: 2026-09-04

Status: primary-source research complete and owner decisions reconciled for
planning. No P4.3 implementation, alert creation, worker execution, external
workflow engine, Sentinel access, rule activation, notification, dispatch,
deployment, or remote Git action is authorized.

## Research Question

P4.3 must turn an accepted, generated-only P4.2 `matched` rule-evaluation
revision into at most one non-operational proposed-alert aggregate, then support
an attributable human-review lifecycle under retries, concurrency, correction,
overload, and recovery. The research focused on deterministic identity,
orthogonal lifecycle semantics, durable timers, queue safety, department
isolation, bounded telemetry, and human oversight.

## Findings

### 1. Delivery identity and alert identity solve different problems

The [CloudEvents 1.0.2 specification](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)
requires a producer's `source` plus `id` to identify a distinct event and allows
a retransmitted duplicate to retain the same identity. That is useful for
transport redelivery, but it does not define H-CAM's domain-level meaning of
"the same proposed alert."

H-CAM therefore needs two separately stored keys:

- a delivery idempotency key for one P4.2 evaluation-revision delivery; and
- a semantic deduplication key for the alert occurrence represented by that
  evaluation, rule version, output, scope, partition, and grouping context.

The first prevents one message from being applied twice. The second prevents
equivalent deliveries or replay paths from creating duplicate aggregates. A
correction appends a new source/evidence revision to the same occurrence when
its stable occurrence key is unchanged; it does not overwrite history.

### 2. Lifecycle state must not absorb every workflow dimension

A single status enum that combines acknowledgement, assignment, suppression,
escalation, merge, correction, and review disposition creates ambiguous and
irreversible transitions. P4.3 should use one small lifecycle state machine and
separate append-only records for orthogonal concerns:

- lifecycle: `proposed`, `acknowledged`, `under_review`, `confirmed`,
  `dismissed`, `resolved`, and `closed`;
- assignment: queue, assignee, transfer, and release;
- suppression: reason, policy version, scope, and expiry;
- escalation: level, reason, target, and deadline breach;
- merge: source-to-canonical relationship without deletion;
- correction/retraction: immutable evidence and projection revisions;
- review decision: actor, reason, policy, evidence digest, and resulting
  disposition.

Reopen is an attributable transition back to `under_review`. Escalation changes
priority/routing metadata, not factual confidence or review disposition.
Confirmation means only that an authorized reviewer accepted the alert for the
configured workflow; it never establishes legal identity, guilt, threat, or an
enforcement instruction.

### 3. Severity, priority, confidence, certainty, and disposition are distinct

The [OASIS Common Alerting Protocol 1.2](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html)
keeps urgency, severity, and certainty as separate dimensions. H-CAM should use
that separation as design evidence while retaining its own internal schema:

- severity describes potential impact;
- priority describes queue handling order;
- confidence describes source/model/evaluator support;
- disposition describes the human-review outcome;
- chronology confidence describes temporal reliability;
- authority class determines what transitions and side effects are permitted.

P4.3 does not claim CAP conformance. H-CAM proposed alerts are internal
review-workflow records, not public-warning messages.

### 4. Human oversight must be explicit and measurable

The [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
and its [Playbook](https://airc.nist.gov/airmf-resources/playbook/) emphasize
defined oversight roles, accountable decisions, audit histories, overrides,
response timing, exceptions, and escalation records. This supports the already
accepted `D-P4.0-004:A+B+C` boundary:

- all police-intelligence alerts remain `mandatory_review`;
- generated bounded automation cannot establish identity, threat, guilt, or
  enforcement;
- future autonomous action remains absent or hard-disabled;
- every disposition, override, suppression, escalation, merge, correction, and
  policy exception is attributable and auditable.

### 5. PostgreSQL row security and queue locking have narrow roles

The [PostgreSQL row-security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
states that enabling row security without an applicable policy produces a
default-deny posture, while table owners normally bypass row security unless
force-row-security and role controls are applied. P4.3 must retain application
department checks plus forced RLS, test owner/superuser/`BYPASSRLS` boundaries,
and prohibit cross-department joins and mutation.

The [PostgreSQL `SELECT` documentation](https://www.postgresql.org/docs/current/sql-select.html)
warns that `SKIP LOCKED` presents an inconsistent view and is appropriate for
queue-like consumers, not general truth reads. P4.3 may use it only to claim
timer/outbox/worker rows with deterministic ordering. Alert reads, review
decisions, and lifecycle reconstruction must use consistent transactional
queries.

### 6. Durable timers are intents, not hidden state transitions

SLA deadlines and scheduled escalation should be stored as versioned timer
intents with event-time basis, policy version, due instant, state, lease,
attempt, and idempotency key. A worker may claim a due timer and append a
bounded `sla_breached` or `escalation_requested` event. It may not confirm,
dismiss, resolve, close, dispatch, or invoke an external provider.

Replaying the same event and timer history must produce the same alert
projection. Wall-clock time may decide when a worker wakes up, but it cannot be
the unrecorded source of business truth.

### 7. Overload handling must preserve meaning instead of dropping alerts

P4.3 should combine hierarchical budgets with deterministic incident-level
collapse:

- per rule version;
- per department;
- per review queue;
- system-wide generated-lab ceiling.

When a budget is exceeded, the engine records an explicit budget decision and
either routes the candidate normally, links it to a canonical incident-group
aggregate, or records bounded suppression. It preserves counts, time range,
representative evidence references, omitted-evidence digest, policy version,
and reason. Drop-oldest, silent eviction, and automatic confirmation are
prohibited.

### 8. API failures need typed, bounded, non-sensitive responses

[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) defines Problem Details
and permits problem-type-specific extension members while requiring clients to
ignore extensions they do not recognize. P4.3 should use stable problem types
for invalid transition, stale ETag, duplicate command, budget denial, authority
denial, and department denial. Responses may include bounded safe codes and
current version, but not raw payloads, evidence values, policy internals,
identities from another department, SQL, or exception text.

### 9. Observability conventions must be pinned and low-cardinality

The [OpenTelemetry messaging semantic conventions](https://opentelemetry.io/docs/specs/semconv/messaging/)
are still marked Development in semantic conventions 1.44.0. P4.3 may use
their producer/consumer/process concepts, but must pin the adopted mapping and
must not claim a stable convention. The
[OpenTelemetry event conventions](https://opentelemetry.io/docs/specs/semconv/general/events/)
also distinguish occurrence time from observation time.

Planned telemetry labels are limited to bounded values such as transition,
outcome, authority class, budget level, timer outcome, and safe reason code.
Alert IDs, actors, departments, rule IDs, evidence IDs, dedupe keys, free text,
locations, and digests are not metric labels. Detailed audit records remain
department-scoped and access-controlled.

## Selected Predecessor Baseline

The following are already accepted and are not reopened by P4.3 planning:

1. `D-P4.0-004:A+B+C`: tiered authority with mandatory review as the
   police-intelligence baseline and autonomous action hard-disabled.
2. `D-P4.0-007:A`: PostgreSQL/PostGIS, application authorization plus forced
   RLS, append-only evidence/revisions, and transactional outbox.
3. `D-P4.0-008:A`: retention by data class with a separately authorized hold
   overlay.
4. P4.0 `AlertAggregateV1`, `AlertLifecycleEventV1`, `Alert`, and
   `AlertRevision` are accepted additive foundations.
5. P4.2 emits generated-only, non-operational evaluation revisions and a typed
   `propose_review_candidate` output. It does not create alerts.

## Planning Conclusions

P4.3 should use:

- deterministic semantic identity plus delivery idempotency;
- an orthogonal aggregate rather than a state explosion;
- append-only lifecycle, review, routing, suppression, escalation, merge, and
  correction records;
- optimistic concurrency for user mutations and unique constraints for
  machine idempotency;
- database-backed timer intents and transactional outbox publication;
- hierarchical budgets with explicit, loss-accounted incident collapse;
- mandatory-review-only police-intelligence behavior;
- generated-only, default-off, production-forbidden validation.

## Owner-Selected Extensions

The owner selected the minimal recommended architecture plus these bounded
extensions:

- generated-only system-health `bounded_automation`, isolated from mandatory-
  review police-intelligence alerts;
- a future external-workflow adapter and hybrid executor shape while retaining
  PostgreSQL as authoritative timer/business truth;
- configurable distinct-reviewer quorum over append-only decisions;
- an isolated Sentinel-lab metadata compatibility adapter that cannot directly
  access Sentinel, cameras, streams, media, credentials, or network resources.

The exact reconciliation is recorded in
[P4.3 owner decisions](p4-3-owner-decisions.md). The next gate is a separate
digest-bound start package; these planning decisions do not authorize
implementation.
