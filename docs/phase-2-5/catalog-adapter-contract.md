# `sentinel_sandbox_catalog_v1` Adapter Contract

<!-- markdownlint-disable MD013 -->

Status: contract implemented for generated fallback and the public Sentinel
sandbox catalogue; product integration remains deferred as recorded in
`backlog-and-owner-decisions.md`.

## Current Online Application

Both `lab1highadapter` and `lab2lowadapter` consume the same exact public
`/api/ingest` source through this contract. The current 30 records are not
truncated in low mode. The profiles apply different local connection/preview
ceilings while preserving normalized camera IDs, media metadata, and returned
transport roles. Exact locators stay internal and are never returned by the
dashboard API.

## Identity And Separation

The new adapter identity is:

```text
sentinel_sandbox_catalog_v1
```

It is separate from:

- `sentinel_reference_v1`, the Phase 0 public reference probe;
- direct `rtsp`, `hls`, and `http` stream adapters;
- the Phase 2 `synthetic` adapter; and
- ONVIF device and media capability management.

The adapter consumes a camera catalogue. It is not itself a media decoder or
an ONVIF management client.

## Responsibilities

The adapter owns:

- bounded retrieval of one configured `/api/ingest` catalogue;
- schema validation and normalization;
- source-level snapshot fingerprints and change history;
- mapping external camera identities to H-CAM registry identities;
- validation and classification of returned transport URLs;
- previewing adds, updates, missing records, and endpoint changes;
- applying an explicitly authorized reconciliation plan;
- refresh lifecycle, audit, metrics, and safe failure codes; and
- a sanitized handoff to stream health and playback services.

It does not own:

- video decoding or AI inference;
- transport health conclusions;
- generated or real frame retention;
- camera/VMS discovery or control;
- Government database integration;
- operator playback authorization; or
- production deployment policy.

## Source Configuration

A catalogue source should contain:

| Field | Purpose |
| --- | --- |
| `catalog_source_id` | H-CAM identifier, not derived from hostname |
| `adapter_kind` | Fixed to `sentinel_sandbox_catalog_v1` |
| `catalog_locator` | Credential-free exact HTTP(S) `/api/ingest` URL |
| `secret_ref` | Optional opaque credential-provider reference |
| `auth_mode` | Explicit supported mode, never inferred |
| `department_scope` | Registry and RBAC boundary |
| `enabled` | Master refresh gate, default false |
| `auto_apply` | Explicit source gate; selected Sentinel source applies every accepted snapshot |
| `refresh_interval_seconds` | Bounded configuration, recommended 60 seconds |
| `max_response_bytes` | Recommended 1 MiB |
| `max_camera_records` | Recommended 500 for Phase 2.5 |
| `missing_grace_observations` | Recommended 3 |
| `missing_grace_seconds` | Recommended 300 seconds |

The phase limit of 500 is intentionally larger than the expected 30-camera
working set and 50-camera safety capacity, but is not an 80,000-camera
production design.
Statewide scale requires pagination, partitioning, and a separate capacity
decision in Phase 6.

## Accepted Input Shape

The public evidence currently shows:

```json
{
  "cameras": [
    {
      "id": "18",
      "number": 18,
      "name": "Camera 18",
      "location": "Generated location",
      "codec": "h264",
      "live": true,
      "width": 1920,
      "height": 1080,
      "fps": 25.0,
      "bitrate_kbps": 2000,
      "bits_per_pixel": 0.03,
      "rtsp_url": "rtsp://catalog-approved-host:8554/stream/18",
      "webrtc_url": "http://catalog-approved-host:8889/stream/18/whep",
      "hls_live_url": "/live/stream/18/index.m3u8"
    }
  ]
}
```

This example is generated and contains no actual Government record or stream.

### Required Fields

- root `cameras` array;
- non-empty unique `id` convertible to a bounded external identifier;
- boolean `live`; and
- at least one usable, policy-approved transport URL for a connectable record.

### Optional Fields

- `number`, `name`, and `location`;
- `codec`;
- `width` and `height`;
- `fps`, `bitrate_kbps`, and `bits_per_pixel`; and
- any of `rtsp_url`, `webrtc_url`, and `hls_live_url`.

Unknown optional properties should be ignored but counted through a bounded
schema-warning code. Unknown fields must not be reflected into database columns
or logs without an explicit contract update.

## Normalization Rules

### Identity

- Scope uniqueness by `(catalog_source_id, external_camera_id)`.
- Preserve external ID exactly after whitespace and length validation.
- Never use array order or `number` as identity.
- Generate an independent H-CAM camera ID.
- Preserve the H-CAM identity when source labels or URLs change.

### Text

- Trim only permitted surrounding whitespace.
- Reject control characters and invalid Unicode.
- Bound ID, name, and location lengths.
- Treat location as an untrusted display label, not verified GIS coordinates.
- Do not place source labels in metrics.

### Technical Properties

- Normalize `h264`, `H.264`, and equivalent accepted spellings to `h264`.
- Normalize `h265`, `H.265`, and `hevc` to `hevc`.
- Map empty codec to unknown.
- Map non-positive width, height, FPS, bitrate, and bits-per-pixel to unknown.
- Preserve fractional FPS as a decimal/float observation, not an integer.
- Keep advertised values separate from later probed/observed values.

### Dynamic Media Adaptation

- Never apply a global codec, geometry, FPS, bitrate, container, or quality
  assumption to the catalogue.
- Build each camera's normalized media plan from its own advertised properties
  and transport set.
- When advertised properties are unknown, create the endpoint with unknown
  capability state and let the bounded probe/decoder determine observed values.
- Select decoder/parser behavior per observed codec and profile.
- Preserve source aspect ratio through explicit scale/pad policy rather than
  distorting every stream to one geometry.
- Keep source FPS/PTS separate from any later inference sampling rate.
- Classify RTSP as preferred inference, HLS as preview/fallback, and WHEP as
  preview plus optional feature-gated inference under selected D-P2.5-005.
- Permit only one active analytics transport per camera at a time and support
  controlled transport failover without duplicate detections.
- Treat 30 as the expected active set and 50 as tested capacity, while accepting
  any bounded catalogue count up to the configured source limit.

### Live State

- Store `advertised_live` from the catalogue.
- Do not map it directly to H-CAM `healthy`.
- Let the existing stream worker derive observed health.
- Expose both states to callers and events.

### URLs

- Resolve a relative HLS URL only against the configured catalogue origin.
- Do not synthesize RTSP or WHEP URLs from camera ID patterns.
- Reject user information, fragments, unsupported schemes, and unapproved
  scheme/host/port/address combinations.
- Treat query strings as potentially secret-bearing and reject or handle them
  only through an explicitly accepted short-lived-URL design.
- Revalidate every URL before every connection attempt.

## Proposed Persistence Boundary

New catalogue concerns should not be overloaded into `stream_endpoints` alone.
The proposed additive records are:

### `stream_catalog_sources`

Source configuration, department scope, auth reference, refresh settings,
enabled/auto-apply gates, latest accepted snapshot, latest applied snapshot,
and rollback pointer.

### `stream_catalog_refreshes`

Queued/running/succeeded/failed lifecycle, requester, reason, attempts, lease,
safe failure code, byte/record counts, timestamps, and resulting snapshot.

### `stream_catalog_snapshots`

Canonical sanitized normalized metadata, stable SHA-256 fingerprint,
observation window, completeness, warning counts, and source revision hints.
Exact credential-bearing URLs must not enter canonical history.

### `stream_catalog_memberships`

Mapping from source/external camera identity to H-CAM camera identity, current
advertised state, first/last seen, consecutive missing observations, recovery
state, latest applied snapshot, and last known transport set. Membership rows
are durable and are never deleted by catalogue reconciliation.

### Existing `stream_endpoints`

One camera may receive named endpoints:

- `inference`: RTSP/TCP and primary when approved;
- `preview`: WHEP for browser preview when supported; and
- `fallback`: HLS for approved preview/network fallback.

The unique `(camera_id, name)` constraint already supports these roles. The
existing endpoint health, leases, FFprobe, playback, outbox, and optimistic
locking remain authoritative after reconciliation.

## Snapshot Fingerprint

The stable fingerprint should include:

- normalized source-scoped external IDs;
- advertised live state;
- normalized technical properties;
- transport roles and sanitized URL components; and
- semantic record ordering by external ID.

It should exclude:

- retrieval timestamp;
- response ordering;
- secret values, tokens, cookies, and credential query strings;
- transient request IDs; and
- health observations produced outside the catalogue.

Identical semantic catalogues should reuse the current snapshot observation
window without emitting a change event.

## Reconciliation Workflow

```text
queue refresh
  -> retrieve bounded response
  -> validate and normalize
  -> fingerprint and store sanitized snapshot
  -> compute diff against last applied snapshot
  -> enforce source and change-anomaly policy
  -> transactionally stage accepted snapshot
  -> upsert durable registry mapping and candidate endpoints
  -> health-gated candidate promotion or rollback
  -> audit and outbox events
```

Rules:

- Only one active refresh per source.
- Only one automatic apply operation runs per source/snapshot.
- Automatic apply uses the source version and snapshot fingerprint to prevent
  stale or duplicate application.
- Every schema-valid and policy-valid snapshot is staged durably before apply.
- Additions create bounded candidate endpoints and enter `recovering`; they do
  not become primary until a health-gated promotion succeeds.
- URL changes create a versioned candidate while the last healthy endpoint
  remains available. Failed promotion rolls back automatically.
- A missing observation moves membership toward `missing`; it never deletes a
  camera, membership, endpoint, audit row, or history.
- Missing records become inactive tombstones after the accepted grace rule.
  The catalogue worker continues checking for reappearance.
- A reappearing record is revalidated, staged, moved to `recovering`, and
  automatically promoted after health succeeds.
- URL changes require fresh network-policy validation.
- Partial, anomalous, ambiguous, hostile, or oversized snapshots are retained
  only as safe failed refresh evidence and are not accepted or applied.
- Apply is transactionally atomic within one department/source boundary.
- Every successful apply retains the previous applied snapshot as the rollback
  target and emits an idempotent outbox event.

## Proposed API Surface

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| POST | `/stream-catalog-sources` | `camera.editor` | Create disabled source configuration |
| GET | `/stream-catalog-sources` | `camera.viewer` | List department-scoped sources |
| GET | `/stream-catalog-sources/{id}` | `camera.viewer` | Read sanitized source state |
| PATCH | `/stream-catalog-sources/{id}` | `camera.editor` | Update settings with ETag |
| POST | `/stream-catalog-sources/{id}/refreshes` | `camera.editor` | Queue audited refresh |
| GET | `/stream-catalog-refreshes/{id}` | `camera.viewer` | Read safe lifecycle status |
| GET | `/stream-catalog-sources/{id}/snapshots` | `camera.viewer` | Paginated semantic history |
| GET | `/stream-catalog-snapshots/{id}/diff` | `camera.viewer` | Preview additions/changes/missing records |
| POST | `/stream-catalog-snapshots/{id}/apply` | `camera.editor` | Replay or recover a validated snapshot with reason and ETag |

Source enablement, configuration changes, and manual replay/rollback require
`X-HCAM-Reason`, department scope, RBAC, audit, and `no-store` responses.
Normal accepted snapshots apply automatically once the source's explicit
`auto_apply` gate is enabled.

## Refresh Behavior

- Disabled by default.
- Generated lab may opt in explicitly.
- Recommended interval: 60 seconds plus deterministic jitter up to 15 seconds.
- Minimum accepted interval: 30 seconds.
- HTTP timeout: 20 seconds.
- Retry transient network/5xx failures at approximately 30 seconds and two
  minutes, then stop.
- Do not retry authorization, policy, schema, oversized, or ambiguous-ID
  failures until configuration or source data changes.
- Recover an abandoned job after a 90-second lease.
- Manual refresh has priority but reuses an active source refresh.

## Failure Atomicity

Recommended default: reject the complete snapshot when any record has a
duplicate identity, hostile URL, invalid required field, or would exceed a
hard bound. Optional unknown fields can produce warnings and partial technical
metadata without rejecting otherwise valid records.

This avoids applying a catalogue that silently omits a camera because its URL
failed security validation.

## Authentication Contract

The official authentication method is not yet confirmed. The adapter should
depend on a typed `CatalogCredentialProvider` and fail closed when the selected
mode has no configured provider.

Potential modes requiring a later decision:

- `none` for generated lab and explicitly public metadata;
- `bearer_header` for short-lived OAuth-style tokens;
- `api_key_header` with an organizer-specified header name; or
- `session_cookie` only if the organizer documents a non-interactive service
  flow and CSRF/session requirements.

Do not automate CAPTCHA, browser login, hidden form submission, or credential
extraction. Do not store credentials in catalogue or transport URLs.

## Events

Proposed event types:

- `hcam.stream.catalog.refresh.completed.v1`;
- `hcam.stream.catalog.changed.v1` only on stable fingerprint change;
- `hcam.stream.catalog.reconciliation.applied.v1`; and
- existing endpoint and health events for resulting streams.

Payloads should carry source/snapshot/operation IDs, counts, department scope,
and safe result codes. They should not carry locators, source labels, secrets,
or camera location strings.

## Compatibility With Current Backend

Most accepted code remains reusable:

- camera registry identity and department boundaries;
- `stream_endpoints` named records and optimistic locking;
- exact locator validation and network policy;
- FFprobe metadata-only health observation;
- PostgreSQL worker leases and `SKIP LOCKED`;
- transactional outbox and audit records;
- protected HLS playback sessions; and
- low-cardinality metrics patterns.

Required additive changes are catalogue source/history models, refresh and
apply APIs, the new adapter implementation, multi-transport reconciliation,
advertised-versus-observed state, per-camera dynamic media plans, optional WHEP
inference, and timestamp/discontinuity handoff fields.

No existing feature needs to be removed or degraded.

## Adapter Acceptance

The adapter is acceptable only when:

- all fixtures and live responses are bounded before parsing/persistence;
- unknown values remain unknown until observed;
- identities and diffs are deterministic and idempotent;
- exact URLs are validated and never synthesized;
- accepted snapshots apply automatically through staging, idempotency,
  health-gated promotion, history, and rollback;
- missing records become durable inactive tombstones and automatically recover
  when they safely reappear;
- credentials and sensitive URLs are absent from durable evidence;
- existing stream health and playback behavior remains compatible; and
- generated-only tests cover every failure and reconciliation state.
