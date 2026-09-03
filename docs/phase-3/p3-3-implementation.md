# P3.3 Generated-Only Stream-Local Tracking Implementation

Status: implemented and validated; exact package acceptance remains pending.

Authorization: `D-P3.3-WORK-AUTH`.

Scope: `phase3.p3_3.generated_only_stream_local_anonymous_tracking`.

## Result

P3.3 adds deterministic anonymous multi-object tracking over server-generated
structured Tier A observations. It associates observations only within one
camera stream and one tracker epoch. It does not consume pixels, images, video,
camera URLs, media bytes, external datasets, appearance embeddings, names,
plates, identities, or cross-camera keys.

The runtime is disabled by default, forbidden in production, and reachable only
through an approved generated-scenario endpoint after a P3.3 assignment passes
the existing RBAC, department, reason, lifecycle, and activation checks.

## Frozen Source Boundary

The selected algorithm family is an H-CAM adaptation of ByteTrack source at:

- commit `d1bf0191adff59bc8fcfeaa0b33d3d1642552a99`;
- acquired archive SHA-256
  `A04446567EBD13BB611849029222CD4EDCC9EC009BD6F1E92FA5F4281C95359C`;
- selected-source digest
  `sha256:12bb7ce90e1089a1e160d5a15cd0c268f27a3083e4df37aef2cd042ae1160438`;
- MIT license, reproduced in the P3.3 third-party notice.

The H-CAM runtime does not install or execute the historical ByteTrack detector,
Torch, OpenCV, LAP, visualization, training, media, or ReID stack. It adapts the
motion/IoU association structure and Kalman component behind an H-CAM-owned
interface. SciPy `linear_sum_assignment` is the reviewed assignment solver.

TrackEval is an evidence-time oracle only:

- commit `12c8791b303e0a0b50f753af204249e622d0281a`;
- archive SHA-256
  `435F0E6D865918332155F8104A98A04D50C2C3DE5B985B96C8A71A0F5B62A0AC`;
- no TrackEval package or optional dataset dependency is in the runtime.

## Runtime Architecture

```text
approved scenario id + seed + UTC start
                  |
                  v
sealed generated observation sequence
                  |
                  v
one bounded lane per stream
                  |
                  v
exact-class two-stage motion/IoU association
                  |
                  v
epoch + anonymous track lifecycle controller
                  |
       +----------+----------+
       |          |          |
       v          v          v
   run state   track state  lifecycle v2 outbox
```

The process-local lane store permits at most 32 active lanes, 64 queued requests
per stream, and 1,000 ms queue age. A frame permits at most 300 observations,
and each exact-class partition permits at most 512 tracks. Resource exhaustion
fails the run closed with a bounded reason code.

Tracker state is not restored after restart. A restart, discontinuity, sequence
or timestamp regression, reconnect, assignment change, or explicit close ends
the old epoch and prevents local track-number reuse from becoming identity.

## Association And Lifecycle

Tier A classes remain independent partitions:

- `object.person`;
- `vehicle.bicycle`;
- `vehicle.car`;
- `vehicle.motorcycle`;
- `vehicle.bus`;
- `vehicle.truck`;
- `object.unknown`.

The lifecycle contract is `hcam.analytics.track.lifecycle.v2`. Transitions are
`started`, `updated`, `lost`, and `ended`, with bounded reasons and immutable
tracker, pipeline, taxonomy, configuration, stream, epoch, sequence, and
observation lineage. Track IDs are deterministic ephemeral local references,
not identity records.

## Persistence

Migration `0010_generated_tracking` adds:

- `analytics_tracking_runs` for bounded generated execution evidence;
- `analytics_tracker_epochs` for reset and discontinuity boundaries;
- `analytics_tracks` for latest anonymous local state;
- `analytics_track_lifecycle` for append-only lifecycle evidence.

Lifecycle records and `hcam.analytics.track.lifecycle.v2` outbox records are
committed in the same transaction. Idempotent run IDs bind the assignment,
scenario, seed, generated input digest, approved pipeline, policy, and
configuration, so replay returns the existing result. Standard generated
metadata expires after 168 hours; restricted metadata remains bounded to 24
hours. No media, locator, path, identity, embedding, plate, watchlist, or global
entity column exists in these tables.

## API Surface

The generated test surface contains five operations:

- `POST /analytics-assignments/{assignment_id}/generated-tracking-runs`;
- `GET /analytics-tracking-runs/{run_id}`;
- `GET /analytics-tracking-runs/{run_id}/epochs`;
- `GET /analytics-tracking-runs/{run_id}/tracks`;
- `GET /analytics-tracking-runs/{run_id}/lifecycle`.

The create request accepts only an approved scenario ID, bounded seed, and UTC
start time. There is no endpoint for arbitrary observations or media. Execution
requires `camera.editor` or administrator access, department scope, an audit
reason, an activated exact P3.3 assignment, and the explicit local test setting.
Read APIs preserve department isolation.

## Generated Evaluation

The sealed scenarios are `single-object`, `two-crossing`, `short-occlusion`,
`long-occlusion`, `all-tier-a`, `discontinuity`, and fail-closed `overload`.
They exercise all Tier A classes, exact-class isolation, occlusion recovery,
track termination, discontinuity epochs, deterministic replay, and bounds.

Measured generated evidence:

| Gate | Result |
| --- | --- |
| Challenge HOTA | `0.9773391812865496` |
| Challenge IDF1 | `1.0` |
| All-class golden HOTA / IDF1 | `1.0 / 1.0` |
| Per-class minimum HOTA / IDF1 | `1.0 / 1.0` |
| Short-occlusion recovery | `1.0` |
| TrackEval HOTA / IDF1 maximum difference | `0.0 / 0.0` |
| ByteTrack Kalman component maximum difference | `2.710505431213761e-20` |
| Overload behavior | fail closed |

These values establish deterministic generated-fixture behavior only. They are
not real-CCTV accuracy, fairness, identity, capacity, latency, pilot, or
deployment claims. Full historical ByteTrack runtime parity is explicitly not
claimed.

## Observability And Safety

Metrics use bounded labels for operation, outcome, transition, state, and reset
reason. Camera, stream, assignment, track, actor, locator, model, and
configuration values are not labels. Audit records cover execution and state
changes. Validation-error responses remain value-redacted.

The deterministic CycloneDX SBOM contains the audited locked runtime set. The
dependency audit reports zero known vulnerabilities at evidence time. Exact
source manifests and license notices remain separate from runtime packages.

## Continuing Boundaries

P3.3 does not authorize physical cameras, Sentinel or ONVIF media, external
datasets, public/private/Government data, biometrics, face recognition, ReID,
cross-camera association, plate or owner lookup, watchlists, operational alerts,
autonomous action, enforcement, pilot, production, P3.4, or remote Git actions.

Final completion requires a clean committed package, a canonical package digest,
and explicit `D-P3.3-ACCEPTANCE` from `mayank-admin` for that exact digest.
