# P3.4 Geometry And Event Primitives Plan

Status: planning complete; technical decisions `D-P3.4-001` through
`D-P3.4-004` accepted; `D-P3.4-START` authorized; final acceptance pending.

Planning authority: `D-P3.4-PLAN-AUTH`.

Accepted dependency: P3.3 under `D-P3.3-ACCEPTANCE` for package digest
`0BE4154E28A4D1A18AC8DA9F8D018CDBEB18F0457DDD1ECC2109D60A956ACA96`.

## Objective

Convert accepted anonymous, stream-local P3.3 track lifecycle observations into
deterministic image-space line, zone, dwell, and occupancy analytic events. The
milestone establishes geometry and event primitives for later authorized work;
it does not identify an entity, correlate cameras, or generate an operational
alert.

## Planning Boundary

P3.4 planning defines:

- immutable normalized geometry and rule versions;
- robust predicates, anchor, boundary, direction, and hysteresis semantics;
- typed line, zone, dwell, and occupancy state machines;
- event-time ordering, schedules, lateness, replay, and idempotency;
- persistence, outbox, API, RBAC, audit, observability, retention, and limits;
- deterministic generated-only scenarios and acceptance evidence;
- exact dependency, source, license, SBOM, and rollback gates.

This planning package does not authorize implementation, dependency changes,
migrations, APIs, workers, generated inference execution, cameras, media,
external data, identity, ReID, cross-camera linkage, watchlists, alerts,
autonomous action, deployment, P3.5, or remote Git actions.

## Existing Foundation

P3.4 reuses rather than replaces:

- `GeometryDefinitionV1`, normalized line and simple-polygon validation, and
  IANA schedule fields;
- accepted P3.3 lifecycle v2 with stream, camera, assignment, tracker epoch,
  class, bounding box, sequence, UTC timestamps, and lineage;
- analytic event envelope fields, where `alert_state` remains `not_evaluated`;
- department scoping, assignment revisions, RBAC, ETags, audit, retention, and
  transactional outbox;
- P3.3 serial stream lanes and generated-only, default-off,
  production-forbidden activation controls.

The existing geometry helper remains useful for input validation but is not
promoted into a general topology implementation.

## Architecture

```text
Visual rule authoring + constrained CEL
        |
        v
Typed AST compiler + approval ----> PostGIS authoritative geometry/rule store
        |                                      |
        +------ approved WKB/JSON/AST/digests -+
                                               |
                                               v
                                      Immutable worker cache
                                               |
                                               v
Accepted P3.3 lifecycle v2
        |
        v
Scope + epoch + sequence gate
        |
        v
Bounded event-time reorder buffer ----> late/conflict audit outcome
        |
        v
Visible track anchor extraction
        |
        v
STRtree candidate preselection
        |
        v
Exact geometry predicates
        |
        v
Per-track/per-rule state machines
        |
        +--> current bounded evaluator state
        +--> append-only typed analytic event
        +--> transactional outbox record
        |
        v
Generated C10 evidence export
```

One serial evaluator lane exists per assignment and stream. No state or event
identity crosses a stream, camera, tracker epoch, department, or assignment
boundary.

## Geometry Engine

`D-P3.4-001` selects a hybrid architecture. PostgreSQL/PostGIS is authoritative
for approved geometry persistence, validation, version history, spatial
indexing, and administrative queries. Exact Shapely 2.1.2 is the real-time
worker predicate candidate over immutable locally cached geometry. Per-track
evaluation does not require a database round trip.

Under `D-P3.4-START`, before installation the implementation package must bind:

- exact PostgreSQL/PostGIS image or package version, artifact URL, SHA-256, and
  platform tag;
- exact Shapely wheel version, URL, SHA-256, and platform tag;
- bundled or linked GEOS versions and compatibility evidence for both paths;
- PostGIS, Shapely, GEOS, NumPy, and all transitive runtime licenses;
- deterministic lockfile, SBOM, third-party notices, and vulnerability review;
- Python 3.12 CI and current developer-interpreter compatibility;
- a fallback/rollback path that disables P3.4 without changing P3.3.

The engine performs two-dimensional predicates only. The coordinate model is
normalized image-space, with finite decimal values in `[0, 1]`. There is no
coordinate reference system, camera calibration, homography, physical distance,
speed, route, or GIS claim.

Geometry validation must reject:

- fewer than two distinct line points or fewer than three polygon vertices;
- zero-length lines, zero-area polygons, self-intersections, invalid rings, and
  non-finite or out-of-range coordinates;
- duplicate adjacent points after canonicalization;
- precision reduction that empties, splits, collapses, or changes the geometry
  type;
- geometry whose canonical representation exceeds the approved contract size.

Canonical geometry JSON uses stable key order, decimal representation, vertex
order, and SHA-256 digest. Canonical WKB and the normalized JSON digest bind the
PostGIS row and worker cache to one approved immutable version. Invalid geometry
is rejected, not silently repaired. A generated dual-engine suite must fail on
predicate, boundary, precision, serialization, or engine-version drift.

## Rule Contract

P3.4 introduces a separate `GeometryRuleV1` rather than overloading geometry.
The planned fields are:

- department, assignment, stream/camera scope;
- immutable rule ID, version, status, and canonical configuration digest;
- exact geometry ID and version;
- event kind and exact Tier A class filter;
- anchor policy: `bottom_center` default or explicit `bbox_center`;
- boundary policy and initial-state policy;
- line direction, deadband, and rearm parameters where applicable;
- zone inner/outer hysteresis parameters;
- dwell threshold and bounded occlusion grace where applicable;
- occupancy enter and reset thresholds where applicable;
- optional schedule version and IANA time zone;
- effective timestamps, retention class, creator, approver, and audit reason.

Rules cannot contain arbitrary executable expressions, SQL, code, URLs, media,
identity fields, external lookup instructions, or alert actions. Rule type
determines a closed schema; irrelevant fields are rejected.

## Visual Rule Graph And Constrained CEL

`D-P3.4-002` selects a visual rule graph compiled into an immutable, versioned,
typed H-CAM AST. The AST composes approved spatial and temporal nodes; it is the
canonical persisted and executed representation. The visual document is an
authoring projection and cannot independently change runtime behavior.

Typed H-CAM nodes own state for crossing, entry, exit, presence, dwell,
occupancy, ordered sequence, bounded `within`, `for_at_least`, cooldown, and
repeat-limit semantics. Constrained CEL evaluates stateless Boolean conditions
over a closed typed context containing approved class, confidence, direction,
schedule, count, and prior typed-node results.

The control plane must parse, type-check, allowlist functions, estimate static
cost, enforce depth/node/window limits, canonicalize the checked AST, and bind a
digest before approval. Workers execute only that approved representation.

CEL has no coordinate, SQL, network, file, environment, secret, external
lookup, camera-control, alert, or enforcement access. Loops, recursion,
mutation, arbitrary functions, dynamic code, user extensions, and runtime
compilation of unapproved text are prohibited. An exact CEL implementation,
source, artifact, license, hash, conformance profile, and SBOM binding remain
implementation evidence gated by `D-P3.4-START`.

## Anchor Semantics

For a latest visible normalized bounding box `(x1, y1, x2, y2)`:

```text
bottom_center = ((x1 + x2) / 2, y2)
bbox_center   = ((x1 + x2) / 2, (y1 + y2) / 2)
```

Only `started` and `updated` lifecycle transitions with a valid latest
observation can produce a spatial sample. A recovery from `lost` arrives as an
`updated` sample. `lost` and `ended` do not synthesize an anchor.

Changing anchor policy changes the rule version and digest. The event stores
the rule version and causal lifecycle reference, not an unbounded trajectory.

## Line-Crossing State Machine

For a directed finite line from `A` to `B`, the signed side of point `P` is the
two-dimensional cross product `(B-A) x (P-A)`. The result is classified as
positive, negative, or deadband according to the approved normalized tolerance.

A crossing is emitted only when:

1. the prior stable point is outside the deadband on one side;
2. the new stable point is outside the deadband on the opposite side;
3. the segment between those two stable points crosses the finite configured
   line segment under the approved boundary semantics;
4. the track-rule state is armed for that direction;
5. both points belong to the same stream, assignment, rule version, and tracker
   epoch.

Touching an endpoint, moving along the line, remaining within the deadband, or
jumping across the infinite extension outside the finite segment emits no
crossing. Direction is `a_to_b` or `b_to_a` from the signed-side transition.
After emission, rearm requires movement to the configured stable distance from
the line; jitter cannot repeatedly trigger the same crossing.

## Zone Entry And Exit State Machine

Each polygon rule derives an inner acceptance region and an outer retention
region from the approved hysteresis distance. Geometry validation must reject a
configuration whose inner region collapses or whose outer region leaves the
normalized policy boundary.

Planned states are `unknown`, `outside`, `inside`, and `grace_lost`.

- The first stable sample initializes state. By default, a track first observed
  inside does not emit an entry.
- Outside becomes inside only after the anchor satisfies the inner predicate.
- Inside remains inside while the anchor is covered by the outer region.
- Inside becomes outside only after it clears the outer region.
- The rule's boundary policy explicitly chooses inclusive `covers` behavior or
  exclusive `contains` behavior.
- A schedule close, epoch reset, assignment stop, or track end closes state with
  a bounded reason and emits no manufactured exit.

Entry and exit events are transition events, not per-frame presence events.

## Dwell State Machine

Dwell starts at the first accepted inside event-time sample. It accumulates
event time, not worker wall time. Temporary `lost` state pauses observation but
preserves the stay only within an approved grace period. A recovered update
inside the outer region continues the same stay; grace expiry or recovery
outside closes it.

Exactly one `zone.dwell.threshold_met` event is emitted per state cycle when the
threshold is reached. Continued presence does not repeat it. Exit, end, reset,
schedule close, rule replacement, and retention cleanup close the cycle with a
bounded reason.

The event records threshold, effective dwell duration, causal sequence, rule
version, and state-cycle ID. It does not claim continuous visual observation
during an occlusion.

## Occupancy State Machine

Occupancy counts currently accepted visible in-zone states for one rule, stream,
epoch, and exact class filter. The count is recomputed deterministically after
each ordered transition. Lost tracks are excluded unless an approved bounded
grace policy explicitly retains them; the recommended default is visible-only.

An upward transition emits `zone.occupancy.threshold_entered` when count reaches
the enter threshold. A downward transition emits
`zone.occupancy.threshold_exited` when count reaches the lower reset threshold.
The two thresholds implement aggregate hysteresis. The event is not emitted on
every count change.

Simultaneous updates use deterministic lifecycle-event ordering. The resulting
event records the final count and causal ordered batch, but no identity list or
trajectory.

## Typed Event Contract

The planned analytic payload v2 retains the envelope and adds a closed typed
payload. Event kinds are:

- `hcam.analytics.line.crossing.v1`;
- `hcam.analytics.zone.entry.v1`;
- `hcam.analytics.zone.exit.v1`;
- `hcam.analytics.zone.dwell.threshold_met.v1`;
- `hcam.analytics.zone.occupancy.threshold_entered.v1`;
- `hcam.analytics.zone.occupancy.threshold_exited.v1`.

Every event includes:

- deterministic event ID and occurred-at UTC event time;
- department, assignment, camera, stream, and tracker epoch;
- anonymous local track reference, except aggregate occupancy events;
- geometry and rule IDs, exact versions, and configuration digests;
- event-kind-specific bounded values and direction where applicable;
- causal lifecycle ID and source sequence or ordered causal batch digest;
- detector, tracker, taxonomy, pipeline, evaluator, and rule lineage;
- retention class and `alert_state: not_evaluated`.

It excludes media, snapshots, clips, raw trajectories, embeddings, identity,
plate text, owner information, watchlist results, cross-camera IDs, risk score,
criminality inference, and enforcement action. Creating an analytic event is
not issuing an alert.

## Event Time And Ordering

The ordering key is tracker epoch plus `source_sequence`. UTC observation time
is the event timestamp. Processing and database timestamps are operational
metadata only.

Each evaluator lane has:

- maximum 64 buffered lifecycle inputs;
- maximum two seconds of allowed event-time lateness;
- watermark equal to maximum observed event time minus allowed lateness;
- deterministic order by source sequence, event time, lifecycle event ID;
- fail-closed handling for a repeated sequence with different canonical input;
- explicit audit/metric outcomes for duplicates, late inputs, gaps, conflicts,
  overflow, and resets.

An exact duplicate is idempotently ignored. An input at or behind the committed
watermark cannot revise emitted events or closed state. A conflicting duplicate,
timestamp regression beyond policy, or overflow closes the evaluator run and
requires a new epoch before more events can be emitted.

## Schedule Semantics

Schedules are immutable weekly interval versions with an IANA time zone.
Evaluation converts the UTC event timestamp through `zoneinfo`. The `fold`
result is retained in diagnostic evidence so daylight-saving repetition is
reproducible.

Rules are inactive outside schedule windows. Opening a schedule initializes
state from the first stable sample without backfilling missed events. Closing a
schedule ends current state with `schedule_closed`; it does not create a spatial
exit. Schedule changes require a new rule version and evaluator reset.

## Deterministic Replay And Idempotency

The canonical event ID hashes:

```text
department | assignment | stream | tracker_epoch | rule_version |
event_kind | state_cycle_id | causal_sequence_or_batch_digest
```

Canonical separators, encoding, field order, and hash algorithm are contract
fields. A unique database constraint owns idempotency. Event insertion and
transactional outbox insertion occur in one transaction. PostgreSQL uses a
unique constraint and `ON CONFLICT`; SQLite remains a single-worker development
boundary and must produce the same logical result.

Replaying a sealed generated run must produce the same ordered event JSON and
hash across processes. Replay must not increment occupancy, extend dwell,
duplicate outbox messages, or resurrect closed state.

## Persistence Plan

The authorized additive migration design may create:

| Store | Purpose | Principal constraints |
| --- | --- | --- |
| `analytics_geometries` | Authoritative PostGIS geometry and canonical normalized representation | Immutable versions, validity constraint, normalized non-geographic policy, GiST administration index |
| `analytics_geometry_rules` | Immutable typed AST, checked CEL, versions, and canonical digests | Closed nodes/functions, approved geometry version, static cost, one status transition path |
| `analytics_geometry_evaluator_runs` | Stream/assignment/epoch execution boundary | One open run per scope, bounded close reason, exact configuration digest |
| `analytics_track_rule_states` | Current bounded state machine snapshot | Composite local scope, optimistic/versioned updates, no trajectory or identity |
| `analytics_events` | Append-only typed events | Deterministic unique event ID, causal references, retention class |
| existing outbox | Publish typed events | Inserted transactionally with event |

Retention cleanup deletes current state, events, and corresponding outbox
records consistently. Geometry and rule definitions retain only approved
configuration and audit metadata; derived operational metadata follows P3.3:
standard at most 168 hours and restricted at most 24 hours.

## API And Control Plan

P3.4 reuses the assignment control plane. Planned APIs are limited to geometry
and visual-rule authoring/versioning, compile/type-check preview, approval,
assignment binding, generated-scenario execution, and department-scoped reads.
There is no arbitrary observation, coordinate-stream, media, URL, file-path,
camera, alert, or action-submission API.

Mutations require department scope, `camera.editor` or `platform.admin`,
`If-Match` for mutable control records, and `X-HCAM-Reason`. Reads require
department scope and existing role policy. Approval, activation, disable, and
retirement transitions are audited. APIs return sanitized bounded reason codes,
not internal geometry-engine exceptions.

Production activation is rejected at settings validation. Generated execution
accepts only a sealed scenario ID, bounded seed, run sequence, UTC start time,
and approved rule-profile ID. The server constructs all lifecycle inputs.

## Resource Limits

Initial planned ceilings are:

- 64 active geometry/rule versions per assignment;
- 16 spatial candidate rules per track transition after `STRtree` selection;
- 16,384 live track-rule states per stream;
- 64 reorder inputs and two seconds lateness per stream;
- 300 input observations per frame, 512 tracks per class, 32 active lanes, 64
  queued batches, and one-second queue age inherited from P3.3;
- bounded geometry JSON, vertices, schedule intervals, dwell thresholds, and
  audit reasons according to contract validation;
- no silent eviction: a hard limit ends the evaluator run with a bounded reason
  and emits no partial analytic result.

The implementation must measure candidate count, state count, buffer depth, and
evaluation duration before freezing a latency gate. It must not claim city-scale
or real-camera performance from generated evidence.

## Failure And Reset Policy

An evaluator reset is mandatory after:

- tracker epoch change, assignment version change, rule or geometry version
  change, stream reconnect, source-generation change, or worker restart;
- sequence conflict, excessive lateness, timestamp regression, queue overflow,
  state limit, geometry-engine failure, persistence conflict, or corrupted
  state;
- schedule close, assignment pause/disable/block, or production-boundary
  violation.

All live state closes before the old evaluator run closes. Reset reasons are a
bounded enum. No analytic event is inferred from the reset itself. A new run
cannot reuse a state-cycle ID from the old run.

## Observability And Audit

Low-cardinality metrics are planned for:

- input, duplicate, late, conflict, gap, and overflow outcomes;
- active lanes, reorder depth, candidate count, and state count;
- evaluation duration by event-kind family and result;
- created/deduplicated events and outbox outcomes;
- geometry validation failures, schedule transitions, resets, and retention;
- generated-suite runs and deterministic replay failures.

Metric labels cannot include department, camera, stream, assignment, rule,
geometry, track, user, locator, class free text, coordinates, or event IDs.
Logs and audit records use bounded reason enums and opaque references. Audit
captures actor, action, scope, exact versions, reason, outcome, and timestamp,
not media or unbounded state payloads.

## Generated C10 Validation Suite

`DATA-GEO-EVT-GEN-C10` is a proposed code-generated structured lifecycle suite.
It contains no image, video, model, external dataset, personal data, or camera
locator. Every case records schema version, generator version, seed, exact
ordered inputs, expected state transitions, expected typed events, and canonical
content digest.

Required groups:

| Group | Required cases |
| --- | --- |
| Geometry | valid/invalid lines, convex/concave polygons, self-intersection, precision collapse, normalized bounds |
| Anchors | bottom-center, center, degenerate box rejection, policy version change |
| Line | both directions, no crossing, endpoint touch, collinear movement, deadband jitter, finite-segment miss, jump, rearm |
| Zone | entry, exit, boundary inclusive/exclusive, initial inside, concave region, jitter, rule replacement |
| Dwell | threshold before/at/after, one-shot, short and expired occlusion, exit, end, reset, schedule close |
| Occupancy | upward/downward thresholds, aggregate hysteresis, simultaneous transitions, class filters, lost tracks |
| Time | event versus arrival order, time-zone conversion, DST gap/fold, schedule open/close |
| Replay | exact duplicate, conflicting duplicate, bounded reorder, late after watermark, 20 identical replays |
| Isolation | interleaved streams, cameras, departments, assignments, epochs, identical local handles |
| Lifecycle | started, updated, recovered, lost, ended, timeout, reset, no resurrection |
| Overload | rule, candidate, state, buffer, geometry-size, queue-age, and persistence failure limits |
| Retention | standard/restricted expiry, event/outbox consistency, no prohibited fields |

Exact hand-computable goldens are the primary oracle. Shapely cannot validate
itself. Independent arithmetic cases, DE-9IM expectations, and canonical event
JSON are reviewed. Hypothesis rule-based state machines generate transition
sequences and assert invariants after each step.

## Acceptance Evidence

Implementation exit, if later authorized, requires:

- exact dependency/source hashes, lockfile, SBOM, licenses, notices, and
  vulnerability evidence;
- generated-suite manifest and canonical digest;
- exact logic agreement of 1.0 on sealed hand-computable goldens;
- zero duplicate events and identical canonical event hashes across 20 replays;
- property/state-machine tests with recorded profile and seed;
- SQLite compatibility and concurrent PostgreSQL migration/idempotency evidence;
- branch coverage of at least 90 percent for the P3.4 evaluator boundary;
- resource-limit, failure, reset, retention, audit, RBAC, and redaction tests;
- clean-source regeneration, package manifest, canonical package digest, and
  explicit owner acceptance of that exact digest.

Generated C10 evidence proves contract logic and deterministic execution only.
It does not prove real-camera accuracy, operational utility, performance at
scale, legal approval, or deployment readiness.

## Delivery Sequence

1. Completed: preserve accepted decisions `D-P3.4-001` through `D-P3.4-004` and
   record explicit `D-P3.4-START` authorization.
2. Acquire and audit the exact geometry dependency; generate lock, SBOM,
   notices, and source evidence.
3. Add immutable contracts, fixtures, canonicalization, and generated C10
   scenario definitions.
4. Add geometry predicates and typed state machines behind a default-off,
   production-forbidden interface.
5. Add event-time lane, deterministic replay, persistence migration,
   transactional outbox, and retention.
6. Add bounded APIs, RBAC, audit, metrics, and failure controls.
7. Run focused, property, PostgreSQL, packaging, clean-source, and full-suite
   validation; freeze the exact evidence package.
8. Present the exact digest and limitations for separate owner acceptance.

Each step fails closed. Later steps do not inherit authorization from planning
or from a prior technical decision.

## Principal Risks And Controls

| Risk | Planned control |
| --- | --- |
| Boundary jitter creates repeated events | Deadband, inner/outer hysteresis, rearm, exact goldens |
| Geometry numerical collapse | Canonical precision validation and reject-on-collapse |
| Arrival order changes event truth | Event-time lane, source sequence, watermark, deterministic replay |
| Retry duplicates events | Deterministic event IDs, unique constraint, transaction and outbox |
| State grows with tracks times rules | Candidate index, explicit per-transition and per-stream ceilings |
| Track loss becomes false exit | Close state with reason; never infer unobserved spatial movement |
| Schedule ambiguity | UTC event time, IANA `zoneinfo`, fold evidence, versioned schedules |
| New dependency adds supply-chain risk | Exact artifacts, hashes, licenses, SBOM, lock, vulnerability review |
| PostGIS and Shapely disagree | Canonical geometry binding, pinned engines, generated parity suite, fail-closed activation |
| DSL permits unsafe or expensive work | Typed AST, constrained CEL, allowlist, static cost and hard execution ceilings |
| Analytic events become alerts implicitly | `alert_state: not_evaluated`, no alert/action API, separate future gate |
| Generated evidence is overstated | Explicit claim boundary and separate real-data/deployment authorization |

## Entry Gates

The owner accepted the four technical decisions on 2026-08-25:

1. `D-P3.4-001`: hybrid Shapely worker plus authoritative PostGIS geometry;
2. `D-P3.4-002`: visual rule graph, typed temporal nodes, constrained CEL;
3. `D-P3.4-003`: balanced deterministic ordering and lateness default;
4. `D-P3.4-004`: bounded PostgreSQL/PostGIS state, outbox, retention, C10.

P3.4 generated-only implementation is authorized by `D-P3.4-START`. Final
acceptance remains separately gated by clean-source exact-digest evidence.

The machine-readable source is
[`p3-4-entry-gates.json`](../../contracts/phase-3/p3-4-entry-gates.json), and the
record is in [P3.4 owner technical decisions](p3-4-owner-decisions.md).
