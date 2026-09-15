# P4.6 Owner Decisions And Reconciliation

Status date: 2026-09-05

Status: all twelve P4.6 design decisions are recorded and effective for
planning reconciliation only. They do not authorize implementation, tests,
migrations, dependencies, runtime, signal backends, processes, containers,
Kubernetes, hardware or capacity execution, backup/restore, scanners, network,
real data, models, operational actions, deployment, or remote Git.

Owner: `mayank-admin`

Planning predecessor: `P4.6-PLANNING-R0`, SHA-256
`6DD1D92BCF98A36DF398E981A435180FABFF3D4CD2D4E19D11657A5ABF8FDAE5`.

## Recorded Selection

```text
D-P4.6-001: C
D-P4.6-002: A
D-P4.6-003: A and also if possible then add C
D-P4.6-004: A
D-P4.6-005: A
D-P4.6-006: A
D-P4.6-007: A
D-P4.6-008: A
D-P4.6-009: A
D-P4.6-010: A
D-P4.6-011: C
D-P4.6-012: C
```

The phrase "if possible then add C" is a binding architecture-capability
request, not permission to activate option C's one-pipeline authority model as
written. Option A remains authoritative. The reconciled design adds a disabled
unified search/index projection fed only by sanitized lane-specific
projections. It does not combine authoritative stores, access rules, retention,
deletion, audit, evidence, or security authority.

## Reconciled Profile

| Decision | Planning binding |
| --- | --- |
| `D-P4.6-001:C` | Existing Prometheus remains authoritative; add a governed low-cardinality registry and default-off typed OpenTelemetry-compatible adapters |
| `D-P4.6-002:A` | Validated W3C Trace Context plus opaque H-CAM correlation ID, disabled baggage by default, and no authorization semantics |
| `D-P4.6-003:A+[guarded C capability]` | Independent operational, security, audit, and evidence lanes remain authoritative; add a disabled sanitized unified search projection |
| `D-P4.6-004:A` | User-journey and service-class objectives with evidence-gated targets, explicit unknowns, and controlled budget/degradation decisions |
| `D-P4.6-005:A` | Central closed sanitized failure registry with bounded domain extensions and non-retryable unknowns |
| `D-P4.6-006:A` | Domain-owned database jobs remain authoritative under shared worker resilience conformance and a disabled future broker adapter |
| `D-P4.6-007:A` | Hierarchical revisioned kill switches and degradation controls with deny precedence and mandatory-control protection |
| `D-P4.6-008:A` | Independent application authorization and PostgreSQL forced-RLS policy oracles with privileged and cross-scope negatives |
| `D-P4.6-009:A` | Canonical internal supply-chain bundle with deterministic SPDX, CycloneDX, and SLSA projections and explicit unknowns |
| `D-P4.6-010:A` | Restore-first tiered recovery, dependency order, integrity evidence, and target/observed RPO/RTO separation |
| `D-P4.6-011:C` | Capability-aware laptop/GPU/server/Kubernetes profiles plus generated C1/C10/C50 latency, balanced, and throughput methodology |
| `D-P4.6-012:C` | Platform-neutral immutable placement plans, first-class standalone execution contract, and optional version-gated Kubernetes adapter |

## D-P4.6-001: Prometheus With Portable Typed Adapters

Option C is selected as written. Current Prometheus metrics and the protected
metrics endpoint remain compatible. A central registry governs names, units,
types, histogram boundaries, allowed labels, label values, ownership,
cardinality budgets, stability, and deprecation.

Typed OpenTelemetry-compatible metric, span, and log envelopes may be added
only under a later exact start package. Exporters remain default off and
require a separately authorized exact destination, trust profile, credentials,
data policy, resource budget, retry/loss policy, and deployment profile. No
vendor, collector, endpoint, or external telemetry service is selected here.

## D-P4.6-002: W3C Trace Context And Opaque Correlation

Option A is selected as written. H-CAM validates bounded `traceparent` and
`tracestate`, propagates one opaque independent correlation ID through API,
outbox, event, and worker boundaries, and starts a new local root when incoming
context is malformed or disallowed.

Trace context is untrusted routing metadata. It cannot grant a role, department
scope, purpose, provider, model, camera, evidence, operational action, or
network capability. Baggage is disabled by default. Sampling cannot suppress
authoritative audit or evidence records.

## D-P4.6-003: Independent Lanes With Guarded Unified Search

Option A is authoritative. The following remain independently governed:

- metrics and traces as non-authoritative operational telemetry;
- operational logs for service, queue, dependency, and lifecycle behavior;
- security logs for authentication, authorization, integrity, abuse, policy,
  and tamper signals;
- audit records as authoritative attributable control history;
- evidence records as authoritative provenance/integrity history.

Each lane retains its own schema, storage, access, purpose, retention-policy
reference, export policy, deletion policy, availability requirement, and
failure behavior. An ordinary log cannot substitute for audit or evidence.

### Guarded C Capability: `UnifiedSignalSearchProjection`

The architecture may define
`hcam.operations.unified-signal-search-projection.v1` as a disabled, derived,
read-only capability. Its purpose is to offer one safe operations/security
search surface without turning one log pipeline into the source of truth.

The projection must enforce all of these controls:

- source adapters accept only allowlisted sanitized projection contracts;
- raw operational/security messages, raw audit records, evidence records,
  payloads, media, identities, case data, secrets, destinations, hostnames,
  addresses, stack traces, and unrestricted text are rejected;
- every indexed field retains source lane, policy revision, freshness,
  department/platform scope, classification, and source-reference identity;
- a query is evaluated independently against every involved lane's role,
  purpose, scope, field, time, and export policy;
- cross-lane joins are denied by default and require a named bounded query
  profile; correlation identifiers are not authorization;
- one lane's retention, hold, deletion, or outage cannot be overridden by the
  unified index;
- stale, partial, redacted, deleted-at-source, inaccessible, and unavailable
  states remain visible;
- search results are non-authoritative and cannot create an audit record,
  evidence assertion, alert, action, identity, or enforcement decision;
- index deletion does not claim source deletion, and source deletion creates a
  tombstone/withdrawal projection without retaining prohibited content;
- no backend, index engine, pipeline, credential, connection, or runtime
  activation is selected or authorized by this decision.

The first generated-only implementation may define this contract, generated
lane projections, policy checks, deterministic query fixtures, and disabled
adapter interfaces if the later start package includes them exactly. A real
central backend or cross-lane operational search requires separate security,
privacy, retention, infrastructure, runtime, network, and deployment approval.

## D-P4.6-004: Evidence-Gated Service Objectives

Option A is selected as written. Objectives combine user-journey and
service-class views. Availability, correctness, freshness, latency, durability,
and recovery remain distinct indicators. Good, valid, bad, unknown, and
excluded events are explicit and replayable.

Production target values, burn thresholds, release policy, automatic
degradation, RPO, and RTO remain unset. Generated values may validate contract
math but cannot become defaults or claims. Any later target requires named
evidence class, minimum samples, data-quality rule, owner, expiry, review,
rollback, and permitted reactions.

## D-P4.6-005: Closed Sanitized Failure Registry

Option A is selected as written. Every API, worker, event, log, metric, and
operator projection maps failures to a stable domain code, class, retry
disposition, safe public status, bounded allowlisted parameters, operator
action reference, and taxonomy revision.

Unknown failures map to `internal_unclassified`, fail closed, and do not retry
by default. HTTP status and exception class are mappings, not the taxonomy.
Raw exceptions, queries, credentials, URLs, paths, identities, media, provider
responses, and security material cannot become safe parameters.

## D-P4.6-006: Domain Jobs With Shared Resilience Conformance

Option A is selected as written. Existing domain queue tables, result stores,
and transactional outbox boundaries remain authoritative. P4.6 standardizes
lease duration, heartbeat, clock-skew allowance, retry allowlists, backoff,
jitter, cooldown, maximum attempts, dead letters, idempotency, late-commit
denial, shutdown, abandonment recovery, and low-cardinality metrics.

A shared conformance suite must test every in-scope worker without moving it to
a universal queue. PostgreSQL `SKIP LOCKED` remains restricted to queue claims.
A disabled external-broker adapter contract may be planned, but no broker,
connection, credential, callback, container, or deployment is selected.

## D-P4.6-007: Hierarchical Fail-Closed Controls

Option A is selected as written. Kill switches and degradation controls are
immutable revisions at platform, department, service, capability, and adapter
scope. Deny wins; a child cannot weaken a parent; stale or invalid policy fails
closed; activation, expiry, supersession, and rollback are attributable and
audited.

Security, department isolation, audit, evidence integrity, and other mandatory
controls cannot be degraded. Optional layer bypass must be explicit in output
provenance. A switch can deny an otherwise authorized capability but can never
grant one.

## D-P4.6-008: Application And PostgreSQL Isolation Oracles

Option A is selected as written. Application authorization and PostgreSQL RLS
are independent controls and independent generated test oracles. New
department-scoped P4.6 tables require forced RLS and explicit policy behavior.

The later test matrix must cover ordinary roles, cross-department attempts,
unset/malformed context, table owners, superusers, `BYPASSRLS`, absent policy,
pooled-connection scope reset, prepared queries, transaction retry,
referential-integrity behavior, and race-sensitive policy expressions.
SQLite cannot be cited as PostgreSQL RLS evidence.

## D-P4.6-009: Canonical Supply-Chain Bundle

Option A is selected as written. One internal typed inventory represents
source revision, dependencies, artifacts, licenses, vulnerability observations,
provenance, build inputs, policy results, freshness, exceptions, and unknowns.
Deterministic SPDX, CycloneDX, and SLSA projections derive from that inventory.

`not_observed`, `unknown`, `stale`, `failed`, `not_applicable`, and `verified`
remain distinct. No vulnerability finding is not proof of safety. No standard
conformance, SLSA level, signature, or attestation claim is made until all
requirements have exact evidence and separate acceptance.

## D-P4.6-010: Restore-First Recovery

Option A is selected as written. Recovery plans classify database, object,
configuration, contract, secret-reference, signing-key-reference, audit, and
evidence dependencies and define an ordered restore and integrity sequence.

A successful backup job is not recoverability evidence. Target RPO/RTO and
observed RPO/RTO remain separate. The initial generated tier may simulate
manifests, corruption, interruption, missing dependencies, restore order,
integrity outcomes, and cleanup state; it cannot execute a real backup,
restore, deletion, filesystem change, or recovery drill.

## D-P4.6-011: Dynamic Profiles And C1/C10/C50

Option C is selected as written. One contract set supports conservative
developer-laptop, owned-GPU-lab, server-node, and Kubernetes-node-class
profiles. Profiles describe coarse capability classes and mandatory policy,
not machine identity. Capability states distinguish declared, observed,
attested, stale, unsupported, and unknown.

Generated C1, C10, and C50 scenarios represent one, ten, and fifty synthetic
stream-equivalent metadata/event workloads. Each supports latency, balanced,
and throughput modes and records latency, throughput, backlog, saturation,
loss, recovery, resources, data quality, completion, and limitations. No
scenario claims real-camera, model, GPU, server, cluster, city, or production
capacity.

Optional AI or acceleration lanes may be explicitly bypassed when unsupported,
with provenance and stable output contracts. Mandatory security, isolation,
audit, evidence, and resource controls make a profile ineligible rather than
silently degraded.

## D-P4.6-012: Platform-Neutral Placement

Option C is selected as written. A pure deterministic policy maps service
requirements to an immutable placement plan. Standalone execution remains a
first-class target. A future optional Kubernetes adapter consumes the same
plan and may project requests/limits, affinity, topology spread, disruption
policy, NetworkPolicy intent, device-plugin resources, or Dynamic Resource
Allocation only when the target cluster version, driver, and enforcement
capabilities are declared and accepted.

Kubernetes is not a product dependency and is not activated by configuration
presence. The application does not inspect or configure hardware directly.
Automatic placement remains advisory/default-off until separately authorized,
and no adapter can bypass security, network, provenance, resource, or kill-
switch constraints.

## Reconciled Architecture

```text
Existing domain services and stores
    -> governed Prometheus registry
       -> typed default-off OTel-compatible adapters
    -> validated W3C trace + opaque correlation context
    -> independent operations/security/audit/evidence lanes
       -> disabled sanitized UnifiedSignalSearchProjection
    -> typed failures + SLI/SLO/budget/degradation state
    -> domain-owned durable jobs + shared resilience conformance
    -> hierarchical kill switches and circuit state
    -> application authorization + PostgreSQL forced-RLS assurance
    -> canonical supply-chain evidence bundle
    -> restore-first recovery plans and generated drill evidence
    -> capability profiles + C1/C10/C50 methodology
    -> immutable placement plan
       -> first-class standalone adapter
       -> optional version-gated Kubernetes adapter
```

## Initial Generated Tier

The first separately authorized implementation should use generated,
non-issuable contracts and fixtures only. It may include the authoritative
selected profile and the guarded unified-search contract if the exact start
package names those paths and tests.

The guarded capability remains disabled and powerless:

- no central backend, index, process, service, connection, credential, or
  deployment;
- no raw source log, audit record, evidence record, media, identity, case,
  provider, topology, secret, or Government/private data;
- no shared authority, access, retention, hold, deletion, or export policy;
- no operational alert, action, dispatch, enforcement, or autonomous decision.

## Progress And Remaining Gate

The planning/research gate remains **100.0000%**. The owner decision gate is
now **12/12 (100.0000%)**, change **+100.0000 percentage points**. Reconciled
package preparation becomes **1/1 (100.0000%)** when the exact R1 digest is
sealed. These planning gates award no weighted product points:

- P4.6 remains **0/10 (0.0000%)**, change **+0.0000 percentage points**;
- Phase 4 remains **85/100 (85.00%)**, change **+0.00 percentage points**.

The non-effective, digest-bound `P4.6-PLANNING-R1` package must be accepted
exactly by the owner before one non-effective `P4.6-START-R0` package may be
prepared. Implementation cannot begin until that later start package is also
accepted exactly.
