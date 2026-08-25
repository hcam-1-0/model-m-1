# P3.4 Owner Decision Packet

Status: five owner decisions pending.

Planning authority: `D-P3.4-PLAN-AUTH`.

Accepted dependency: P3.3 under `D-P3.3-ACCEPTANCE`, package digest
`0BE4154E28A4D1A18AC8DA9F8D018CDBEB18F0457DDD1ECC2109D60A956ACA96`.

This packet presents the decisions required before any P3.4 implementation.
Accepting decisions `D-P3.4-001` through `D-P3.4-004` freezes the technical
baseline. It does not start implementation unless `D-P3.4-START` is also
accepted explicitly.

## D-P3.4-001: Geometry Engine And Precision

### Recommended Option

Approve `shapely_2_1_2_with_exact_geos_and_license_binding`.

The implementation would use exact Shapely 2.1.2 for validated two-dimensional
predicates, prepared geometry, and immutable `STRtree` candidate selection. The
exact wheel, bundled GEOS version, transitive dependencies, hashes, platform
compatibility, licenses, SBOM entries, and notices must be captured before the
dependency is added. No download is authorized by this planning decision.

The H-CAM coordinate model remains normalized image space. A fixed decimal
precision grid may be used only after validation proves that the geometry
remains valid and non-empty. Geometry that collapses, self-intersects, leaves
the normalized range, or changes type after precision reduction is rejected.

### Why This Is Recommended

- DE-9IM-backed predicates give explicit interior, boundary, and exterior
  semantics.
- Prepared geometry and `STRtree` support bounded repeated evaluation without
  turning the database into the per-frame execution engine.
- A pinned library is safer than growing the current validation helper into a
  topology engine.
- Exact version, GEOS, license, and hash binding preserves supply-chain review.

### Alternatives

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| Hand-written predicates | No new runtime dependency | Robust polygon topology, boundary cases, and maintenance become H-CAM's responsibility |
| PostGIS evaluation | Strong durable spatial platform | Adds database round trips and coupling to a latency-sensitive stream-local state machine |
| Defer geometry engine | No dependency decision now | Blocks reliable line, zone, dwell, and occupancy implementation |

### Owner Response

- Accept: `Accept D-P3.4-001 recommended option.`
- Change: specify the engine, exact version, precision policy, and review gates.
- Defer: `Defer D-P3.4-001.`

## D-P3.4-002: Spatial And Event Semantics

### Recommended Option

Approve `versioned_anchor_hysteresis_and_typed_event_state_machines`.

Geometry definitions remain immutable, versioned normalized lines or simple
polygons. A separate immutable `GeometryRuleV1` binds one geometry version to
an event type, class filter, anchor policy, schedule, thresholds, boundary
policy, and hysteresis parameters. Changing any behavior creates a new rule
version and configuration digest.

The default track anchor is the bottom-center of the latest visible bounding
box. `bbox_center` is permitted only as an explicit rule setting. Each event
kind has a typed state machine:

| Event kind | Required behavior |
| --- | --- |
| `line.crossing` | Stable opposite sides outside a deadband, finite line-segment crossing, direction, and rearm distance |
| `zone.entry` | Outside-to-inside transition through outer/inner hysteresis; no event for initial inside state by default |
| `zone.exit` | Inside-to-outside transition through hysteresis and the configured boundary policy |
| `zone.dwell.threshold_met` | Event-time accumulation while inside, bounded occlusion grace, exactly one event per stay |
| `zone.occupancy.threshold_entered` | Aggregate visible in-zone count crosses upward through a threshold |
| `zone.occupancy.threshold_exited` | Aggregate count crosses downward through a reset threshold |

Boundary touch, collinearity, jitter within the deadband, and track lifecycle
loss do not silently become crossings. `lost` pauses bounded dwell continuity;
`ended`, epoch reset, assignment stop, and schedule close terminate state with a
bounded reason and do not manufacture spatial exit events.

### Why This Is Recommended

- The rule version records every semantic choice used to produce an event.
- Hysteresis prevents repeated events from small tracker jitter at a boundary.
- Typed state machines are easier to test and audit than a generic predicate
  expression language.
- Bottom-center better approximates ground contact for people and vehicles
  while preserving image-space limitations.

### Alternatives

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| Center anchor only | Simpler | Less stable for ground-oriented zones and line crossings |
| Raw predicate per frame | Minimal state | Boundary jitter creates duplicate and contradictory events |
| General rule-expression DSL | Broad future flexibility | Larger security, validation, and explainability surface before core semantics are proven |
| Emit exit on lost/end | Easy state cleanup | Falsely claims a spatial transition that was not observed |

### Owner Response

- Accept: `Accept D-P3.4-002 recommended option.`
- Change: specify anchor, boundary, initial-state, hysteresis, or event-kind
  changes.
- Defer: `Defer D-P3.4-002.`

## D-P3.4-003: Event Time, Schedules, Replay, And Deduplication

### Recommended Option

Approve
`event_time_sequence_ordering_bounded_lateness_and_deterministic_replay`.

P3.4 would evaluate P3.3 lifecycle observations by tracker epoch,
`source_sequence`, and UTC event timestamp. Wall-clock arrival time is used for
operations and metrics, never for spatial truth. One serial lane per stream and
assignment keeps state deterministic.

Each lane uses a bounded reorder buffer of at most 64 lifecycle inputs and at
most two seconds of event-time lateness. The watermark is the greatest observed
event time minus the approved lateness. Inputs at or behind the committed
watermark are recorded as late and cannot mutate closed state or events.
Conflicting duplicates fail closed and reset the evaluator epoch.

Weekly schedules use IANA time zones through Python `zoneinfo`. UTC event time
is converted to local civil time; DST folds are therefore deterministic.
Schedule close ends evaluator state with `schedule_closed`, but does not emit a
fake zone exit or line crossing.

Event IDs are deterministic hashes of department, assignment, stream, tracker
epoch, rule version, event kind, state-cycle identity, and causal sequence.
Database uniqueness plus `INSERT ... ON CONFLICT` makes replay idempotent. Event
and outbox insertion occur in one transaction.

### Why This Is Recommended

- It distinguishes event time from processing time and makes late data visible.
- A bounded buffer tolerates small local reordering without unbounded memory or
  historical state mutation.
- Deterministic identifiers support exact replay, retries, and audit.
- UTC-to-IANA conversion avoids ambiguous local input timestamps.

### Alternatives

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| Arrival-order evaluation | Very simple | Network or worker delay changes event truth and replay results |
| Unlimited late correction | Maximum historical revision | Unbounded state, mutable published events, and difficult operator audit |
| Drop every out-of-order input | Strong bound | Small recoverable reordering loses valid transitions |
| Random event UUIDs | Easy generation | Retries and replay can create duplicate events |

### Owner Response

- Accept: `Accept D-P3.4-003 recommended option.`
- Change: specify different buffer, lateness, schedule, or deduplication rules.
- Defer: `Defer D-P3.4-003.`

## D-P3.4-004: Persistence, Resources, Retention, And Validation

### Recommended Option

Approve
`bounded_state_transactional_outbox_inherited_retention_and_c10_evidence`.

The proposed implementation uses additive stores for immutable rule versions,
evaluator runs, current track-rule state, and append-only typed analytic events.
It reuses the accepted transactional outbox. No raw trajectories, bounding-box
history beyond approved causal references, images, video, identity, embeddings,
plate text, owner data, or cross-camera entity keys may be added.

Initial ceilings:

| Limit | Proposed value |
| --- | --- |
| Active geometry/rule versions per assignment | 64 |
| Candidate rules evaluated per track transition | 16 |
| Live track-rule states per stream | 16,384 |
| Reorder inputs per stream | 64 |
| Event-time lateness | 2 seconds |
| Existing P3.3 active lanes | 32 per worker |
| Existing P3.3 queued batches | 64 per stream, 1 second maximum age |
| Standard derived metadata retention | At most 168 hours |
| Restricted metadata retention | At most 24 hours |

The generated-only `C10` suite must include hand-computable goldens, all Tier A
classes, line touch/collinearity/jump/direction cases, concave and boundary zone
cases, initial-inside behavior, dwell and occlusion, occupancy concurrency,
schedule and DST transitions, duplicates, conflicting duplicates, late input,
replay, restart, epoch reset, isolation, and overload. Property/state-machine
tests supplement but do not replace exact goldens.

Exit targets are exact logic agreement of 1.0 on the sealed generated suite,
zero duplicate events, stable canonical event hashes across 20 identical
replays, no cross-stream state, and fail-closed overload behavior. Numeric
latency targets are frozen only after an approved generated baseline on the
documented reference machine; P3.4 must not invent a deployment-performance
claim.

### Why This Is Recommended

- Explicit ceilings bound memory and candidate evaluation.
- Transactional persistence preserves event/outbox consistency.
- Existing retention prevents P3.4 from silently expanding surveillance data.
- Hand-computable and stateful tests cover both exact expected results and long
  transition sequences.

### Alternatives

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| In-memory state only | Less database work | Restart, retry, and audit behavior cannot be proven |
| Store every point or full trajectory | Easier later analysis | Expands privacy, storage, retention, and correlation scope |
| Unbounded rules/states | Flexible configuration | Memory and latency exhaustion become uncontrolled |
| Set a latency SLA before baseline | Early numeric target | Produces an unsupported hardware/deployment claim |

### Owner Response

- Accept: `Accept D-P3.4-004 recommended option.`
- Change: specify persistence, limit, retention, or evidence changes.
- Defer: `Defer D-P3.4-004.`

## D-P3.4-START: Generated-Only Implementation Authorization

### Recommended Option

Authorize implementation only after decisions `D-P3.4-001` through
`D-P3.4-004` are accepted and recorded. The authorized implementation would be
limited to:

- exact dependency acquisition and supply-chain evidence for the approved
  geometry engine;
- contracts, generated fixtures, additive migration, repository, service,
  evaluator, API, RBAC, audit, metrics, and transactional outbox work defined in
  the accepted P3.4 plan;
- local generated-only tests, C10 evidence, documentation, and local checkpoint
  commits.

It would remain default-off and production-forbidden. It would not authorize
camera or media access, real or external datasets, identity, ReID, cross-camera
association, watchlists, Government database matching, operational alerts,
autonomous action, deployment, P3.5, or remote Git actions.

### Owner Response

After accepting or changing the four technical gates, the exact recommended
authorization is:

> I, mayank-admin, accept D-P3.4-001 through D-P3.4-004 as documented and
> authorize D-P3.4-START for local, default-off, production-forbidden,
> generated-only geometry and analytic-event implementation, validation,
> documentation, and local checkpoint commits. This does not authorize cameras,
> media, external data, identity, ReID, cross-camera linkage, Government
> database matching, operational alerts, autonomous action, deployment, P3.5,
> or remote Git actions.

Any shorter response must still identify `D-P3.4-START`; `continue` or acceptance
of a technical decision alone does not authorize implementation.
