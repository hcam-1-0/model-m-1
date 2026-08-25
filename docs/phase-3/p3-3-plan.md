# P3.3 Per-Camera Tracking Plan

Status: planning complete; owner entry decisions and implementation start are
pending.

Planning authority: `D-P3.3-PLAN-AUTH`.

Accountable owner: `mayank-admin`. Separate-person review is optional under
`DR-0026`; exact artifact, license, provenance, validation, security, rollback,
audit, and owner-acceptance evidence remain mandatory.

## Objective

Add deterministic anonymous multi-object tracking over ordered H-CAM Tier A
detection observations from exactly one camera stream. The tracker will create
ephemeral local track lifecycles that downstream P3.4 geometry can consume,
while making cross-camera association structurally impossible.

P3.3 is an association and lifecycle milestone. It does not identify a person or
vehicle and does not authorize real media.

## Current Dependency State

P3.2 accepted a default-off, generated-input, CPU-only detector path. It provides
normalized observations, lineage, assignment controls, transactional outbox,
retention, and fail-closed behavior.

The accepted P3.2 evidence contains one deterministic generated image case whose
approved result has zero candidates. That proves runtime plumbing, not a stable
multi-frame observation sequence or tracking quality. P3.3 must therefore keep
two evidence lanes separate:

| Lane | Input | What it can prove |
| --- | --- | --- |
| Component | Deterministic generated structured detections and ground truth | Association, lifecycle, resets, resource bounds, and metric correctness |
| Integration | Accepted P3.2 observation contracts and persistence | Contract compatibility, ordering, deduplication, retention, and outbox behavior |

Neither lane proves performance on real CCTV footage.

## Authorized Planning Scope

- `TRK-R0` ByteTrack-style association behind an H-CAM tracker interface;
- generated-only, stream-local sequence and ground-truth design;
- lifecycle, epoch, ordering, reset, retention, and overload contracts;
- persistence, outbox, API, RBAC, audit, metrics, and deployment-boundary plans;
- exact source, license, hash, SBOM, parity, and evaluation evidence gates;
- tests for all approved Tier A classes and failure modes;
- owner decision and exit-acceptance packets.

## Not Authorized

- implementation, migration, or dependency edits;
- source, package, model, or dataset downloads;
- camera, stream, image, video, file-path, URL, or media-byte inputs;
- Sentinel or ONVIF media use;
- public, private, or Government datasets;
- appearance embeddings, face features, gait, ReID, plate identity, global
  identity, or cross-camera association;
- watchlists, owner lookup, criminality or sensitive-trait inference;
- operational alerts, autonomous actions, enforcement, pilot, or deployment;
- remote Git actions.

## Architecture

```text
Generated scenario registry
        |
        v
Ordered normalized observations
        |
        v
Stream partition + ordering gate
        |
        v
TRK-R0 association adapter
        |
        v
Lifecycle state machine + epoch controller
        |
        +--> tracker epoch metadata
        +--> current anonymous track state
        +--> append-only lifecycle records
        +--> transactional outbox
        |
        v
Generated evaluation export --> pinned TrackEval oracle
```

The runtime must have one serial execution lane per assignment and stream. State
cannot be shared between lanes. Dynamic cross-stream batching is prohibited.

## Tracker Interface

The proposed `StreamLocalTracker` contract accepts one immutable batch with:

- department, assignment, camera, and stream scope;
- tracker epoch and configuration digest;
- strictly increasing source sequence and UTC observation time;
- normalized bounding box, exact Tier A class, confidence, and observation ID;
- model and processing lineage already produced by the detection boundary.

It returns lifecycle transitions and a bounded state summary. It never accepts
pixels, media locators, arbitrary metadata, embeddings, names, registration
records, or a cross-stream entity key.

The implementation must be replaceable. `TRK-R0` is a versioned artifact behind
the interface, not embedded into API or database semantics.

## Association Policy

Proposed defaults for owner approval:

| Policy | Proposed value | Reason |
| --- | --- | --- |
| Association family | ByteTrack two-stage motion/IoU association | Selected `TRK-R0`; no appearance model |
| Class behavior | Independent exact-class partitions | Prevent person/vehicle or vehicle-subclass joins |
| High-confidence threshold | Inherit assignment threshold, frozen in tracker configuration | Keeps detector/tracker junction explicit |
| Low-confidence floor | 0.10, configurable only in an approved profile | Matches the method's second-stage intent without accepting arbitrary noise |
| First-stage match threshold | 0.80 IoU-cost threshold proposal | Must be tuned only on approved generated evidence |
| Second-stage match threshold | 0.50 IoU-cost threshold proposal | Mirrors the pinned reference behavior subject to parity evidence |
| New-track threshold | High threshold plus 0.10, capped at 1.0 | Prevent low-score boxes from creating new tracks |
| Lost timeout | 3 seconds and at most 30 sampled frames | Time-aware bound for sparse or variable sampling |
| Minimum confirmation | Two visible observations except an explicit single-frame test profile | Reduces one-frame noise |
| Interpolation | Disabled | Avoid creating unobserved boxes in P3.3 |
| ReID or appearance | Forbidden | Preserves anonymous stream-local scope |

Thresholds are configuration, not claims. Every approved configuration receives
a canonical digest and cannot change while an assignment is active.

## Epoch And Ordering Contract

An epoch is the maximum interval in which a track handle may be reused. A new
epoch is mandatory after:

- process or worker restart because P3.3 does not restore active tracker state;
- assignment activation after pause, block, failure, or disable;
- stream reconnect or source-generation change;
- camera, stream, assignment version, model, taxonomy, tracker, pipeline, or
  tracker-configuration change;
- non-monotonic sequence, duplicate sequence with different content, timestamp
  regression, or a gap beyond the approved discontinuity limit;
- queue overflow, resource exhaustion, or internal state corruption.

Every active or lost track is deterministically ended before the old epoch
closes. The reset reason is a bounded enum. The first safe batch starts a new
epoch. No track is re-associated across epochs.

Replay of the same sealed generated run must return the existing outputs and
must not mutate tracker state or duplicate events.

## Lifecycle Contract

The existing `TrackPayloadV1` remains immutable. P3.3 should introduce a
versioned lifecycle contract rather than silently changing it. The proposed v2
payload contains:

- compound scope and ephemeral `track_id` plus `tracker_epoch`;
- `started`, `updated`, `lost`, or `ended` state;
- bounded transition reason;
- first, latest, and last-visible timestamps and sequences;
- latest observation reference, exact class, age, visible count, and missed
  count;
- tracker, pipeline, taxonomy, and configuration versions;
- retention class and processing lineage.

It explicitly excludes names, identities, embeddings, appearance features,
media, plate text, owner records, and cross-camera references. Event IDs and
track handles are deterministic hashes over approved local scope and contain no
meaning outside the stream epoch.

Transition rules:

| Current | Input | Next | Emission |
| --- | --- | --- | --- |
| absent | confirmed high-confidence association | started | one start event |
| started/updated | matched observation | updated | one update event |
| started/updated | temporary unmatched interval | lost | one lost transition |
| lost | matched before timeout | updated | one recovery update |
| lost | timeout | ended | one timeout end event |
| any live state | epoch reset | ended | one reset end event |
| ended | any input in same epoch | rejected | no resurrection |

## Generated Sequence Suite

`DATA-TRK-GEN-R0` is proposed as a code-generated structured-observation suite.
It contains no images or video. Each scenario has a schema version, seed,
generator digest, exact ordered observations, exact ground truth, expected
transitions, and a canonical content digest.

Required deterministic scenarios:

| Group | Cases |
| --- | --- |
| Basics | empty, one object, delayed confirmation, normal end |
| Tier A coverage | person, bicycle, motorcycle, car, bus, truck, unknown |
| Association | two crossing objects, parallel objects, size change, jitter, duplicate box |
| Confidence | high-to-low occlusion recovery, low-only noise, confidence boundary values |
| Occlusion | short occlusion recovery, timeout after long occlusion, reappearance after end |
| Ordering | duplicate replay, conflicting duplicate, skipped sequence, out-of-order frame, timestamp regression |
| Epochs | pause/resume, reconnect, worker restart, assignment change, tracker-config change |
| Isolation | interleaved streams, interleaved cameras, identical local counters in separate epochs |
| Overload | maximum detections, maximum live tracks, queue overflow, timeout, malformed box |
| Determinism | repeated run, process-independent digest, stable event ordering |

All association scenarios run per class. Multi-class scenarios verify that
exact-class partitions never associate with one another.

## Persistence Plan

An additive migration is proposed only after `D-P3.3-START`:

| Store | Purpose | Key constraints |
| --- | --- | --- |
| `analytics_tracker_epochs` | Epoch start/end and bounded reset reason | One open epoch per assignment/stream; immutable scope/config digest |
| `analytics_tracks` | Latest anonymous local track state | Composite epoch/track identity; no global identity fields |
| `analytics_track_lifecycle` | Append-only lifecycle evidence | Deterministic event ID; exact observation reference; bounded payload |
| existing outbox | Publish lifecycle v2 | Transactional with lifecycle persistence |

Live Kalman and association state remains in bounded worker memory and is not
serialized in P3.3. Restart closes the previous epoch and starts a new one. This
is less seamless than checkpoint restoration but avoids unsafe or incompatible
state resurrection.

Retention follows the approved synthetic-lab policy: standard derived metadata
at most 168 hours and restricted metadata at most 24 hours. Epoch, track,
lifecycle, and corresponding unpublished or published outbox records are deleted
consistently. No table receives media, locator, path, blob, embedding, identity,
or owner-detail columns.

## API And Control Plan

The existing assignment API remains the control plane. P3.3 proposes no API for
submitting arbitrary observations or media.

The generated-lab endpoint accepts only an approved `scenario_id`, bounded seed,
run sequence, and UTC start time. The server constructs all observations from
the sealed scenario generator. Read APIs expose run summary, epochs, anonymous
tracks, and lifecycle records within department scope.

Mutating operations require `camera.editor` or `platform.admin`, department
scope, `If-Match` where assignment state changes, and `X-HCAM-Reason`. Reads
require department scope. Audit records store actor, action, scope identifiers,
bounded reason, outcome, and version digests, never observations beyond their
opaque IDs or any media.

## Resource And Failure Boundaries

Proposed generated-lab ceilings:

- at most 300 observations per frame, inherited from P3.2;
- at most 512 active plus lost tracks per stream;
- at most 32 active generated stream lanes per worker;
- at most 64 queued batches per stream and 1,000 ms queue age;
- at most 250 ms association time per generated batch on the approved reference
  hardware, measured separately from detector latency;
- at most 256 MiB incremental tracker-worker resident memory for 32 lanes;
- no unbounded history in memory; ended tracks leave live state immediately;
- one retry only for transaction serialization, never for invalid input,
  ordering, configuration, or resource failure.

Queue age, overflow, time, memory, and state-limit breaches fail closed, close
the epoch with a bounded reason, and require a clean next epoch. They never cause
cross-stream state reuse or silent input reordering.

These ceilings are planning proposals. Measurement on the approved laptop and
CI profile must precede owner approval.

## Evaluation Plan

The evaluation package has three layers:

1. Hand-computable invariant fixtures for lifecycle, counts, resets, and basic
   association behavior.
2. Pinned upstream-parity fixtures comparing the H-CAM adaptation with the exact
   approved ByteTrack oracle.
3. Pinned TrackEval runs over canonical MOT-format exports for official HOTA,
   `DetA`, `AssA`, `LocA`, IDF1, ID precision/recall, MOTA, identity switches,
   fragmentations, mostly tracked/lost, and per-sequence results.

Reports are separated by scenario, Tier A class, density, object size,
occlusion, confidence band, discontinuity, and configuration. Aggregate scores
cannot hide a failed class or safety scenario.

Proposed gates:

| Gate | Proposed requirement |
| --- | --- |
| Determinism | Byte-for-byte identical canonical outputs across three clean runs |
| Isolation | Zero cross-stream or cross-epoch associations in all adversarial fixtures |
| Lifecycle | 100% expected transitions and reset reasons on golden fixtures |
| Basic golden quality | HOTA 1.00, IDF1 1.00, zero ID switches on noiseless fixtures |
| Challenge quality | HOTA at least 0.85 and IDF1 at least 0.90 on the approved generated challenge suite |
| Per-class floor | HOTA at least 0.80 and IDF1 at least 0.85 for every Tier A class |
| Occlusion recovery | At least 95% recovery for approved short-occlusion cases |
| Regression | No metric decrease greater than 0.02 from the sealed baseline |
| Resources | All measured ceilings met with no unbounded growth |
| Safety | Prohibited-field, input-source, production, and cross-camera tests all pass |

Generated metrics prove only conformance to generated scenarios. They do not
authorize or support real-world accuracy claims.

## Test Matrix

- tracker-adapter unit and source-parity tests;
- class partition, threshold boundary, box validation, and deterministic tie
  breaking;
- lifecycle state-machine and invalid-transition property tests;
- duplicate, late, gap, reset, reconnect, and restart tests;
- multi-stream isolation tests with intentionally colliding local counters;
- bounded memory, track count, batch size, queue, timeout, and overload tests;
- database constraints, transaction rollback, outbox deduplication, and
  retention tests;
- RBAC, department isolation, ETag, reason, redaction, and audit tests;
- migration upgrade, downgrade, and re-upgrade on SQLite and PostgreSQL;
- pinned TrackEval parity and report-schema tests;
- clean source build, isolated install, license notice, SBOM, dependency audit,
  full test suite, and branch coverage at least 90%;
- production-default-off and forbidden-input scans.

CI remains generated-only and network-free after dependencies are locked.

## Observability Plan

Low-cardinality metrics cover processed batches, lifecycle transitions, open
epochs, active/lost track counts, reset reasons, association duration, queue
depth, overloads, deterministic replays, outbox backlog, and retained records.

Allowed labels are bounded enums such as outcome, state, transition, reason,
and operation. Department, camera, stream, assignment, epoch, track, actor,
model, path, and configuration values are prohibited metric labels.

Synthetic-lab alerts cover repeated epoch resets, sustained queue backlog,
resource-limit breaches, lifecycle persistence failures, and unpublished outbox
growth. Alert definitions do not authorize deployment.

## Work Packages

| Package | Deliverable | Depends on |
| --- | --- | --- |
| `P33-W1` | Exact source, license, hash, SBOM, and adaptation decision records | `D-P3.3-002` |
| `P33-W2` | Generated sequence, ground-truth, export, and metric contracts | `D-P3.3-003` |
| `P33-W3` | Stream-local tracker interface, association adapter, lifecycle controller | W1, W2, `D-P3.3-004` |
| `P33-W4` | Additive persistence, outbox, retention, API, RBAC, and audit | W3 |
| `P33-W5` | Evaluation oracle, metrics, resource, security, and fault tests | W1-W4 |
| `P33-W6` | Build, clean-source evidence, digest-bound exit packet | W1-W5 |

## Delivery Sequence

1. Owner accepts the plan and exact policy proposals.
2. Freeze and approve exact ByteTrack and TrackEval source artifacts without
   downloading any dataset.
3. Authorize `D-P3.3-START` for the exact package boundary.
4. Implement generated scenario and metric contracts first.
5. Implement the stream-local adapter and lifecycle state machine.
6. Add persistence, outbox, APIs, observability, and retention.
7. Run focused, full-suite, PostgreSQL, clean-build, coverage, dependency,
   license, SBOM, resource, and fault validation.
8. Freeze the evidence manifest and obtain explicit owner acceptance.

## Exit Evidence

P3.3 is complete only when one immutable manifest binds:

- exact implementation files and clean commit or generated-only dirty-tree
  limitations;
- exact ByteTrack and TrackEval commits, acquired files, licenses, and hashes;
- dependency lock, SBOM, vulnerability and license results;
- generated suite and ground-truth digests;
- lifecycle, reset, isolation, overload, retention, API, RBAC, audit, outbox,
  migration, and deterministic replay results;
- official TrackEval HOTA/IDF1 reports and approved thresholds;
- full test and branch coverage results;
- reference hardware and resource measurements;
- explicit limitations and unchanged prohibitions;
- one canonical SHA-256 package digest accepted by `mayank-admin`.

P3.3 acceptance does not authorize P3.4, real media, public datasets,
cross-camera tracking, deployment, or remote Git actions.

## Planning Result

The plan is ready for owner decisions. Implementation remains blocked until all
four entry decisions and `D-P3.3-START` are explicitly accepted. The decision
packet provides exact response forms and does not infer approval from
"continue", silence, or acceptance of another milestone.
