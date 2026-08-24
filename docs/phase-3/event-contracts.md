# Analytics Event Contracts

Status: the P3.0 baseline is implemented as machine-validated Pydantic schemas,
deterministic JSON Schema snapshots, and generated fixtures. The tracked files
under `contracts/phase-3/` are authoritative; examples below remain explanatory.

## Existing Contract Alignment

Phase 2 already persists outbox rows with `event_id`, `event_type`,
`schema_version`, `stream_id`, `camera_id`, `occurred_at`, and `payload`.
Phase 3 keeps this envelope, adds `partition_key=stream_id` to delivered
documents, and validates analytics-specific payload contracts. The assignment
control plane now writes `hcam.analytics.model.deployment.changed.v1` rows in the
same transaction as assignment revisions and audit evidence. A future shared
event package may generalize the table name, but compatibility with existing
stream events must be preserved.

## Common Rules

- IDs are opaque stable strings; consumers must not parse business meaning from
  them.
- Times are UTC RFC 3339 values with explicit precision and clock source.
- Coordinates are normalized to `[0,1]`; source dimensions remain available
  for deterministic conversion.
- Confidence is a number in `[0,1]` and never appears without model identity.
- Model, pipeline, taxonomy, postprocessor, and policy versions are immutable.
- Payloads must not contain raw frames, crops, stream credentials, source URLs,
  face templates, person embeddings, or Government data.
- New optional fields may be added to a schema version. Removing, renaming, or
  changing field meaning requires a new major event version.

## Observation Created

Event type: `hcam.analytics.observation.created.v1`

An observation is one model output for one object candidate in one source
frame. It is not an alert, identity, or assertion of fact.

```json
{
  "observation_id": "obs_01...",
  "stream_id": "str_01...",
  "camera_id": "cam_01...",
  "observed_at": "2026-08-21T10:15:30.120Z",
  "processed_at": "2026-08-21T10:15:30.168Z",
  "source": {"sequence": 4812, "width": 1920, "height": 1080},
  "pipeline": {"id": "vehicle-baseline", "version": "1"},
  "model": {"id": "detector-a", "version": "sha256:..."},
  "taxonomy_version": "hcam.objects.v1",
  "class": {"id": "vehicle.car", "confidence": 0.91},
  "bbox": {"x": 0.22, "y": 0.35, "width": 0.18, "height": 0.24},
  "quality": {"blur": null, "occlusion": "partial"},
  "retention_class": "derived.analytics.standard",
  "review_state": "unreviewed"
}
```

`model.version` resolves to an immutable registry record; an alias such as
`candidate` or `champion` is never placed in an event as the effective version.

## Track Updated

Event type: `hcam.analytics.track.updated.v1`

Track events provide lifecycle changes, not per-frame duplication. The proposed
states are `started`, `updated`, `ended`, and `lost`.

```json
{
  "track_id": "trk_01...",
  "tracker_epoch": "epoch_01...",
  "stream_id": "str_01...",
  "camera_id": "cam_01...",
  "state": "updated",
  "observed_at": "2026-08-21T10:15:31.120Z",
  "class_id": "vehicle.car",
  "latest_observation_id": "obs_01...",
  "age_frames": 31,
  "visible_frames": 26,
  "tracker": {"id": "tracker-a", "version": "sha256:..."}
}
```

The tuple `stream_id + tracker_epoch + track_id` is the full scope. Consumers
must not link a track across epochs or cameras.

## Analytic Event Created

Event type: `hcam.analytics.event.created.v1`

An analytic event is the deterministic result of applying a versioned spatial
or temporal rule to observations or local tracks.

```json
{
  "analytic_event_id": "aevt_01...",
  "stream_id": "str_01...",
  "camera_id": "cam_01...",
  "event_kind": "zone.entry",
  "observed_at": "2026-08-21T10:15:31.120Z",
  "track_refs": ["epoch_01...:trk_01..."],
  "rule": {"id": "loading-zone", "version": 4},
  "geometry_ref": {"id": "zone-7", "version": 2},
  "confidence": 0.88,
  "review_state": "unreviewed",
  "alert_state": "not_evaluated"
}
```

`alert_state` makes the Phase 3/4 boundary visible. Phase 3 cannot set it to an
operational alert decision.

## Model Deployment Changed

Event type: `hcam.analytics.model.deployment.changed.v1`

The event records an approved assignment transition. It contains registry IDs
and immutable hashes, not model bytes or credentials.

Required fields:

- assignment ID and department;
- stream ID and capability;
- previous and new model/pipeline versions;
- lifecycle state and safe reason code;
- actor or service principal, change reason, approval record ID;
- occurrence time and effective time.

## ANPR Extension

ANPR stays an observation extension rather than a vehicle identity. It records:

- plate-region observation ID;
- OCR engine and normalization versions;
- ranked text alternatives and per-alternative confidence;
- country/format hypothesis only when the approved model supports it;
- `review_state`, with unreviewed as the default;
- retention and masking policy.

Owner details, registration records, watchlist state, and database match results
are prohibited in Phase 3 events.

## Delivery Semantics

- Delivery is at least once; consumers deduplicate by `event_id`.
- `stream_id` is the default partition key.
- Producers preserve stream-local ordering where sequence data exists, but no
  global ordering is promised.
- Consumers tolerate late data and record the chosen lateness window.
- Redelivery cannot create a second domain observation or event.
- Dead-letter handling stores sanitized metadata and reason codes, never media.
- Event payload size is bounded; oversized output is rejected and counted.

## Contract Verification

The P3.0 implementation proves:

- required/optional fields and numeric bounds;
- unknown-field compatibility and major-version rejection policy;
- deterministic serialization and representative golden fixtures;
- PII/credential negative tests;
- duplicate, out-of-order, late, malformed, and oversized event behavior;
- producer and consumer compatibility in CI.

Run the reviewed snapshot check with:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py check
```

Snapshot rewrites are intentionally blocked unless the accountable owner explicitly runs
the writer with `--acknowledge-reviewed-change`. Contract snapshots contain no
models, media, camera locators, credentials, or Government data.
