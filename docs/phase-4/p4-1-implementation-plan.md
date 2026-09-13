# P4.1 Correlation Foundation Implementation Plan

Status date: 2026-09-04

Planning status: prepared; implementation is not authorized until the owner
accepts the exact `P4.1-START-R0` package digest.

## 1. Objective

P4.1 turns bounded, generated Phase 3 event envelopes into deterministic,
evidence-linked correlation hypotheses. It establishes the ingestion,
deduplication, ordering, windowing, Adaptive Multi-Engine Correlation (AMEC),
hypothesis revision, persistence, replay, and read-only operator-support
foundations needed by later Phase 4 work.

P4.1 is not a video analytics stage. It consumes structured events only. It
does not process frames, load models, call external providers, create alerts,
dispatch resources, or perform enforcement.

## 2. Frozen Progress Boundary

The accepted Phase 4 work breakdown assigns 15 of 100 Phase 4 points to P4.1:

| Work item | Points | Completion rule |
| --- | ---: | --- |
| P4.1-A: ingress, validation, deduplication, partitioning, and ordering | 4 | Every acceptance and regression gate for the item passes |
| P4.1-B: bounded AMEC correlation and deterministic replay | 5 | Every acceptance and regression gate for the item passes |
| P4.1-C: canonical hypotheses, uncertainty, evidence, and revisions | 4 | Every acceptance and regression gate for the item passes |
| P4.1-D: evidence package and exact owner acceptance | 2 | Exact evidence is sealed and separately accepted by the owner |

Progress remains **10/100 Phase 4 points (10.00%)** and **0/15 P4.1 points
(0.00%)** while this plan is prepared. Technical completion can earn at most
13/15 P4.1 points. The final 2 points require a separate exact owner acceptance
of the completed evidence package.

## 3. Binding Inputs

P4.1 must preserve and implement the accepted planning decisions:

- `D-P4.0-001:A+B`: a bounded evidence-first hypothesis graph is canonical;
  flat groups are digest-bound, rebuildable read projections.
- `D-P4.0-002:A+C+D`: AMEC has a mandatory deterministic lane plus typed
  optional probabilistic, temporal-graph, model-first-shadow, and ensemble
  lanes. Optional output is evidence, never authority.
- `D-P4.0-003:A`: later rule authoring uses visual graphs, typed temporal
  nodes, and constrained CEL. P4.1 may consume only fixed generated correlation
  profiles and must not implement the P4.2 compiler or evaluator.
- `D-P4.0-004:A+B+C`: police-intelligence output remains mandatory-review;
  lower-consequence automation and autonomous dispatch are not activated.
- `D-P4.0-006:A`: confidence, calibration, contradiction, uncertainty,
  abstention, and human confirmation remain separate concepts.
- `D-P4.0-007:A`: PostgreSQL/PostGIS, department isolation, append-only
  evidence, typed provenance, revisions, and transactional outbox semantics are
  retained.
- `D-P4.0-008:A`: data-class retention and later hold policy remain explicit;
  P4.1 must not invent operational retention or legal-hold authority.

The existing Phase 3 `stream_event_outbox` is a read-only input boundary.
P4.1 does not change its schema, publication state, camera relationships, or
producer behavior.

## 4. Non-Goals And Prohibitions

P4.1 does not include:

- model, checkpoint, dataset, artifact, inference, accelerator, or benchmark
  work;
- camera, ONVIF, Sentinel, stream, frame, image, snapshot, recording, playback,
  or media access;
- real, private, personal, biometric, vehicle-owner, case, watchlist,
  Government, or police data;
- external reference-provider transport, credentials, network egress, lookup,
  or raw response storage;
- P4.2 rule authoring, visual graph compilation, CEL execution, rule approval,
  or operational activation;
- P4.3 alert creation, lifecycle, notification, escalation, dispatch, or
  enforcement;
- P4.4 provider integration, P4.5 case/timeline workflows, or P4.6 deployment;
- production, cloud, Kubernetes, pilot, release, or remote Git activity.

## 5. Target Architecture

```text
generated Phase 3 event fixture / read-only outbox projection
    -> closed ingress validation and department resolution
    -> canonical envelope digest and durable receipt
    -> duplicate/conflict/late/gap classification
    -> deterministic department/profile/key partition
    -> bounded event-time window and explicit watermark
    -> mandatory deterministic CPU lane
    -> typed optional lane results or explicit unavailable states
    -> deterministic arbitration with hard policy vetoes
    -> canonical evidence graph and hypothesis revision
    -> rebuildable flat projection
    -> read-only, department-scoped API projection
```

The data plane is default-off. It can run only through the bounded generated
fixture harness under a non-production configuration. Application startup does
not automatically consume events or start a worker.

## 6. Work Packages

### P4.1-W1: Historical Verification Transition

P4.0 evidence is already accepted and must remain historically verifiable after
P4.1 changes the live source files.

The current P4.0 readiness tool compares accepted component hashes with the
current working tree. That correctly protected P4.0 before acceptance but would
incorrectly freeze those files forever. P4.1 therefore performs one narrow,
tested transition:

1. Keep the P4.0 evidence, package, acceptance, implementation commit, and
   component digests immutable.
2. Verify P4.0 implementation components from accepted commit
   `2e35bd28aa33c2ebed6fa0bd6486fb26a7d9655d`, using local Git objects only.
3. Continue verifying immutable package and acceptance records in the current
   tree.
4. Fail closed if the accepted commit, path, object, package digest, component
   hash, or acceptance binding is absent or mismatched.
5. Add regression tests proving that authorized P4.1 evolution does not
   invalidate P4.0 and that altered historical objects or bindings fail.

This transition changes the verification reference, not the accepted P4.0
evidence. It cannot rewrite, reseal, or weaken any historical record.

### P4.1-W2: Closed Event Ingress

Implement a typed `CorrelationIngressEvent` adapter over generated Phase 3
event envelopes and read-only `StreamEventOutbox` projections.

Ingress responsibilities:

- accept only declared H-CAM event types and schema versions;
- reject unknown fields, invalid identifiers, invalid UTC timestamps,
  non-finite numbers, forbidden content, and envelopes above 64 KiB;
- resolve department through the registered stream and camera relationship;
- reject absent, blank, conflicting, or cross-department scope;
- preserve `occurred_at`, `observed_at`, `received_at`, `recorded_at`, and
  `corrected_at` as distinct fields when the source contract provides them;
- canonicalize the bounded envelope and compute a versioned SHA-256 digest;
- derive a typed partition key from department, fixed generated profile, and
  declared correlation dimensions;
- classify every accepted or rejected input with a low-cardinality reason;
- retain no credentials, URLs, frame data, arbitrary source payload, or
  unrestricted text.

An event ID previously recorded with the same canonical digest is an idempotent
duplicate and produces no second domain effect. The same event ID with a
different digest is a conflict, is retained as a sanitized conflict outcome,
and cannot enter a correlation window.

### P4.1-W3: Ordering, Partitions, And Windows

Ordering uses event time and explicit source information. It never creates a
global order that the producer did not provide.

The implementation must provide:

- deterministic partition keys and canonical key digests;
- monotonic per-partition receipt sequence;
- explicit maximum observed event time and watermark;
- configurable, bounded allowed lateness;
- deterministic fixed, tumbling, or session-test windows selected by a closed
  generated profile;
- visible classifications for on-time, late-accepted, late-rejected, gap,
  duplicate, conflict, future-skewed, and implausibly-old events;
- exact replay using original event, profile, schema, clock, partition, and
  window versions;
- no silent event drop, state eviction, key overflow, or watermark advance;
- PostgreSQL worker claims with `FOR UPDATE SKIP LOCKED` and explicit leases;
- an enforced SQLite single-worker development boundary.

Initial hard bounds:

| Boundary | Default | Maximum |
| --- | ---: | ---: |
| Envelope bytes | n/a | 65,536 |
| Events per explicit batch | 100 | 1,000 |
| Active partitions per worker | 32 | 128 |
| Active windows per partition | 32 | 256 |
| Accepted events per window | n/a | 4,096 |
| Window duration | 60 seconds | 15 minutes |
| Allowed lateness | 30 seconds | 5 minutes |
| Future clock skew | 5 seconds | 30 seconds |
| Worker lease | 30 seconds | 90 seconds |
| Generated retry attempts | 1 | 3 |

Limit exhaustion stops or degrades the affected generated partition with a
typed outcome. It does not allocate unbounded memory or silently discard work.

### P4.1-W4: Adaptive Multi-Engine Correlation

Define one closed lane protocol with typed capability, input, output, resource,
lineage, calibration, and failure contracts.

The lane registry contains:

- `deterministic_cpu`: executable and mandatory for P4.1 generated fixtures;
- `probabilistic`: contract and explicit unavailable state only;
- `temporal_graph`: contract and explicit unavailable state only;
- `model_first_shadow`: contract and explicit unavailable state only;
- `uncertainty_ensemble`: contract plus generated lane-result arbitration
  fixtures only.

Optional lanes do not load models or artifacts in P4.1. Generated lane-result
fixtures may exercise arbitration but cannot masquerade as runtime inference.

The deterministic lane must:

- sort and group only by canonical typed keys;
- enforce window, chronology, class, stream, tracker epoch, and spatial-policy
  boundaries;
- treat local track identifiers as local to one stream and tracker epoch;
- produce supporting, contradicting, missing, stale, superseding, and
  retracting evidence roles;
- emit exact candidate and abstention outcomes with stable canonical digests;
- reproduce byte-identical canonical results across process orderings and
  supported database backends.

The arbitrator must:

- require a valid deterministic result before accepting any optional proposal;
- preserve every lane's availability, version, lineage, and result;
- prevent optional lanes from overriding deterministic prohibitions;
- preserve contradiction and disagreement instead of averaging them away;
- keep confidence, uncertainty, data quality, freshness, and calibration
  separate;
- abstain on insufficient evidence, unsupported capability, policy mismatch,
  conflict, exhausted bounds, or unsafe ambiguity;
- never assert identity, guilt, intent, sensitive traits, or predicted criminal
  risk.

### P4.1-W5: Canonical Hypotheses And Revisions

The canonical output is a bounded evidence graph. A hypothesis includes:

- opaque ID and deterministic hypothesis key;
- department, generated profile, schema, engine, and policy versions;
- window start/end, watermark, completeness, and chronology quality;
- all contributing, contradicting, missing, stale, superseding, and retracting
  evidence references;
- lane availability, lane results, calibration method, disagreements, and
  lineage;
- confidence and uncertainty as separate bounded values;
- an explicit abstention state and reason;
- canonical graph JSON, graph digest, projection version, and projection digest;
- created, observed, corrected, superseded, retracted, and recorded chronology
  where applicable;
- `mandatory_review`, `operational=false`, and `generated_only=true` invariants.

Flat groups are derived only from the canonical graph. They contain no new
edge, score, identity, or conclusion and can always be rebuilt from the graph
plus the exact projection version.

Corrections, supersession, expiry, and retraction append a hypothesis revision
and new typed graph edges. They never rewrite prior evidence, prior revisions,
or source event receipts.

### P4.1-W6: Persistence And Concurrency

Migration `0013_correlation_foundation` extends the P4.0 schema additively. It
uses the existing `correlation_runs`, `correlation_hypotheses`, and
`hypothesis_evidence_refs` stores and adds:

1. `correlation_event_receipts` for canonical event identity, deduplication,
   conflict/late classification, and bounded sanitized payloads.
2. `correlation_partition_checkpoints` for partition version, sequence,
   watermark, bounded state counters, and optimistic concurrency.
3. `correlation_window_events` for immutable event-to-run membership and
   ordering.
4. `correlation_lane_results` for typed per-lane availability, output, lineage,
   calibration, and digest.
5. `correlation_hypothesis_revisions` for append-only state, graph, projection,
   correction, supersession, and retraction history.

The migration relaxes only the P4.0 hard-block constraints on
`correlation_runs` needed for generated P4.1 states. It retains
`generated_only=true`, `operational=false`, mandatory review, bounded values,
and no provider/alert behavior.

Every new department-scoped table receives application scope filtering and
forced PostgreSQL row-level security. Transactions atomically persist receipt,
window membership, run state, hypothesis revision, evidence references, and
any generated non-operational domain event. SQLite remains a single-process
development backend and cannot claim multi-worker support.

### P4.1-W7: Runtime Boundary, API, And Observability

The generated correlation runtime is a bounded application service and test
harness, not a deployed daemon.

- `HCAM_P41_GENERATED_CORRELATION_ENABLED` defaults to `false` and is rejected
  in production.
- No worker starts at application startup.
- The harness accepts only repository-owned generated JSON fixtures.
- There is no public event-ingestion, correlation-start, replay, or correction
  mutation endpoint in P4.1.
- Existing read-only hypothesis APIs may expose bounded graph, projection,
  revision, and run status after department/RBAC/no-store checks.
- P4.1 emits no alert and invokes no P4.2+ behavior.
- Low-cardinality metrics cover receipt outcomes, queue/run outcomes, duration,
  lateness, abstention reasons, lane availability, lease recovery, and bounded
  resource exhaustion.
- Camera, stream, department, user, hypothesis, event, partition, and payload
  values are prohibited metric labels.
- Logs, audit events, and exceptions contain typed reason codes, not raw event
  payloads.

### P4.1-W8: Evidence And Acceptance

Prepare immutable snapshots, fixtures, test reports, a known-limitations
register, a reproducible evidence package, and a separate owner acceptance
proposal. Evidence must distinguish generated/static, SQLite, and cached local
PostgreSQL/PostGIS results and cannot imply operational validation.

## 7. Implementation Layout

The planned correlation module is isolated below
`app/hcam/intelligence/correlation/`:

```text
correlation/
  __init__.py
  bounds.py
  contracts.py
  ingress.py
  ordering.py
  lanes.py
  deterministic.py
  arbitration.py
  hypotheses.py
  persistence.py
  runtime.py
  worker.py
  metrics.py
```

The exact start package owns the authoritative path allowlist. No listed path
is created or changed before start authorization.

## 8. Test Matrix

### Contract And Ingress Tests

- valid versions and event types;
- unknown fields, malformed IDs, invalid times, NaN/infinity, oversized and
  forbidden payloads;
- missing or conflicting camera/stream/department scope;
- canonical JSON and digest stability;
- same-ID/same-digest duplicate and same-ID/different-digest conflict;
- no raw payload in reason codes, logs, metrics, or exceptions.

### Time And Window Tests

- in-order, reordered, late, duplicate, conflict, gap, future-skewed, and old
  events;
- watermark and boundary equality goldens;
- fixed/tumbling and generated session-window cases;
- daylight-saving and timezone inputs normalized without losing source
  metadata;
- maximum partition/window/event bounds and visible exhaustion;
- deterministic replay under shuffled delivery.

### Correlation And Hypothesis Tests

- deterministic lane exact goldens;
- missing/contradicting/stale evidence and mandatory abstention;
- optional lane unavailable, degraded, disagreeing, and generated fixture
  results;
- deterministic veto cannot be overridden;
- confidence and uncertainty remain separate;
- graph/projection equivalence and digest binding;
- expiry, supersession, correction, and retraction preserve history;
- no identity, guilt, intent, sensitive-trait, or predictive-risk assertion.

### Persistence And Security Tests

- SQLite `0012 -> 0013 -> 0012 -> 0013` cycle and schema drift;
- PostgreSQL/PostGIS constraints, forced RLS, cross-department denial, worker
  claims, lease expiry, and concurrent workers;
- transaction rollback and idempotency after injected failures;
- SQLite second-worker rejection;
- malformed or over-limit stored JSON rejection;
- read API RBAC, department isolation, pagination, no-store, and redaction;
- production configuration rejection and absence of public runtime mutations.

### Regression And Evidence Tests

- all P4.0 accepted package and acceptance bindings remain exact;
- historical P4.0 source verification uses accepted commit `2e35bd28`;
- all accepted Phase 3 snapshots and migrations remain byte-exact;
- focused and full test suites, Ruff, build, dependency checks, migration
  checks, readiness, and clean-source evidence pass;
- new or materially changed P4.1 modules achieve at least 90 percent actual
  branch coverage.

## 9. Delivery Sequence

1. Implement and validate the P4.0 historical-verifier transition.
2. Add closed contracts, bounds, canonical ingress, and negative tests.
3. Add migration `0013`, repositories, forced RLS, and migration tests.
4. Add partition, watermark, window, deduplication, conflict, and replay logic.
5. Add the deterministic lane, optional lane contracts, and arbitration.
6. Add canonical graph/projection, evidence roles, and revision behavior.
7. Add the default-off generated harness, read-only projections, and metrics.
8. Run SQLite and cached PostgreSQL/PostGIS validation, full regression,
   coverage, build, and evidence sealing.
9. Stop at 13/15 P4.1 points and request exact owner evidence acceptance.

Implementation may use at most eight bounded source/test/evidence remediation
cycles under one accepted start package. Any scope, immutable-history,
dependency, data, network, security, migration, or eight-cycle failure stops
closed and requires a new package.

## 10. Exit Criteria

P4.1 technical completion requires all P4.1-A, P4.1-B, and P4.1-C acceptance
criteria to pass from a clean local checkout. It reaches 13/15 P4.1 points and
23/100 Phase 4 points at that point.

P4.1 completes only after the owner accepts the exact final evidence package.
That acceptance reaches 15/15 P4.1 points and 25/100 Phase 4 points. It does
not authorize P4.2 or any operational use.
