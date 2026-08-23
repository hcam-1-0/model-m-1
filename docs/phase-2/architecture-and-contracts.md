# Architecture and Contracts

## Runtime Flow

```text
synthetic publishers -> MediaMTX RTSP gateway -> FFprobe health workers
                              |
                              +-> JWT-protected, on-demand fMP4 HLS

operator -> H-CAM API -> PostgreSQL
                     -> short-lived ES256 playback token
                     -> MediaMTX JWKS contract

configured ONVIF device -> capability worker -> normalized change snapshots
                                           -> audited refresh lifecycle
                                           -> capability-change outbox event

authorized operator -> ONVIF operations -> imaging inspection / bounded events
                    -> double-gated PTZ -> per-stream lease -> automatic stop

platform admin -> bounded WS-Discovery -> exact interface and CIDR filtering
                                      -> metadata only; no returned URL contact
```

The API is the control plane. MediaMTX is the media gateway. Workers inspect
stream metadata and never persist frames. PostgreSQL owns endpoint definitions,
health projections, bounded probe history, playback session audit records, and
transactional state-change events.

## Module Boundaries

| Module | Responsibility |
|---|---|
| `hcam.streams.service` | Endpoint mutation, ETags, primary projection, audit |
| `hcam.streams.repository` | Department-scoped reads and probe history |
| `hcam.streams.probe` | Bounded FFprobe execution and media summary |
| `hcam.streams.worker` | Leases, schedules, hysteresis, history, outbox |
| `hcam.streams.outbox` | At-least-once event delivery and sink boundary |
| `hcam.streams.onvif` | Bounded stream resolution and media capability queries; no network discovery |
| `hcam.streams.onvif_operations` | Read-only imaging/events and double-gated, leased PTZ commands |
| `hcam.streams.onvif_discovery` | Admin-triggered, bounded WS-Discovery on one approved interface |
| `hcam.streams.capabilities` | Authenticated discovery, normalization, stable fingerprints, cache, API service |
| `hcam.streams.capability_worker` | Priority jobs, retries, leases, scheduling, retention |
| `hcam.streams.secrets` | Typed credential-provider boundary and private-lab file provider |
| `hcam.streams.playback` | ES256 tokens, JWKS, playback session records |
| `hcam.streams.lab` | Guarded deterministic synthetic fixtures |

## HTTP Contract

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `GET` | `/streams` | `camera.viewer` | Filtered stream inventory |
| `POST` | `/cameras/{camera_id}/streams` | `camera.editor` | Add endpoint |
| `GET` | `/streams/{stream_id}` | `camera.viewer` | Endpoint and health |
| `PATCH` | `/streams/{stream_id}` | `camera.editor` | ETag-protected update |
| `GET` | `/streams/{stream_id}/health` | `camera.viewer` | Current health |
| `GET` | `/streams/{stream_id}/probes` | `camera.viewer` | Bounded probe history |
| `POST` | `/streams/{stream_id}/probe` | `camera.editor` | Queue immediate probe |
| `POST` | `/streams/{stream_id}/capability-refreshes` | `camera.editor` | Queue audited background refresh |
| `GET` | `/capability-refreshes/{refresh_id}` | `camera.viewer` | Inspect refresh lifecycle |
| `GET` | `/streams/{stream_id}/capabilities` | `camera.viewer` | Read latest sanitized inventory |
| `GET` | `/streams/{stream_id}/capability-snapshots` | `camera.viewer` | Read paginated change history |
| `POST` | `/streams/{stream_id}/capabilities/discover` | `camera.editor` | Deprecated synchronous compatibility query |
| `POST` | `/streams/{stream_id}/onvif/imaging-inspections` | `camera.editor` | Read current imaging metadata |
| `POST` | `/streams/{stream_id}/onvif/event-pulls` | `camera.editor` | Create, pull, and terminate a bounded event subscription |
| `POST` | `/streams/{stream_id}/onvif/ptz-commands` | `camera.controller` | Execute a double-gated, bounded PTZ command |
| `POST` | `/onvif/discovery-runs` | `platform.admin` | Probe one explicitly approved isolated network |
| `POST` | `/streams/{stream_id}/playback-sessions` | `camera.viewer` | Issue 60-second HLS grant |

Mutations, capability queries, and playback grants require `X-HCAM-Reason`.
Stream updates require the quoted integer `If-Match` ETag. Access remains
department-scoped. Source locators cannot contain user information, passwords,
query strings, or fragments; credentials are referenced or mounted separately.

## Data Contracts

- `stream_endpoints`: adapter, protocol, credential-free locator, scheduling,
  lease, primary status, optimistic version.
- `stream_health_current`: one current projection per endpoint.
- `stream_probe_runs`: metadata-only history retained for seven days.
- `stream_event_outbox`: transactional `hcam.stream.health.changed.v1` events.
- `playback_sessions`: actor, path, expiry, and SHA-256 JTI hash; never token.
- `stream_capability_refreshes`: queued/running/terminal lifecycle, bounded
  lease, requester, reason, attempts, safe failure code, and snapshot link.
- `stream_capability_snapshots`: canonical normalized JSON, stable SHA-256
  fingerprint, completeness, and first/last observation times.
- `onvif_control_leases`: one short-lived movement lease per stream.
- `onvif_operation_runs`: safe parameters, actor, reason, outcome, reason code,
  request correlation, and duration for every attempted ONVIF operation.

The legacy camera stream columns remain a temporary compatibility projection.
The primary endpoint is authoritative and updates that projection.

## Decisions

- **DR-0006:** MediaMTX `1.19.3-ffmpeg`, pinned by OCI digest, is the Phase 2
  gateway because it supports RTSP ingest, on-demand fMP4 HLS, JWT/JWKS, API,
  and metrics without introducing a custom media server.
- **DR-0007:** FFprobe performs metadata-only checks in a bounded subprocess.
  H-CAM does not decode, store, or bulk-download video in this phase.
- **DR-0008:** Playback uses 60-second ES256 JWTs with exact MediaMTX `read`
  permission for `hcam/{stream_id}`. Tokens are returned once and not stored.
- **DR-0009:** Scale evidence is a disposable 50-stream synthetic lab. ONVIF is
  limited to one explicit simulator and does not use WS-Discovery.
- **DR-0010:** Adapter egress is fail-closed. Hostnames require an exact
  allowlist entry, ONVIF bypasses environment proxies and rejects redirects,
  returned stream URIs are revalidated, and FFprobe output is bounded while the
  process is running rather than after capture.
- **DR-0011:** Camera capability discovery is an explicit, audited, read-only
  query against explicitly configured device/media service URLs. It normalizes
  bounded device, service, media, and profile metadata and does not perform
  WS-Discovery, host enumeration, or camera mutation.
- **DR-0012:** Capability inventory is an opt-in background subsystem with
  stable change history, 36-hour freshness, 90-day retention, priority jobs,
  bounded retries, and reclaimable worker leases.
- **DR-0013:** Authentication uses a per-attempt secret-provider boundary and
  WSSE PasswordDigest, official `httpx` HTTP Digest, or their explicit
  combination. The local file provider is never a production secret backend.
- **DR-0014:** ONVIF operations remain default-off. Imaging and event inspection
  are read-only. PTZ requires a global gate, a per-stream administrator gate,
  `camera.controller`, an audit reason, bounded velocity/duration, a lease, and
  automatic stop for continuous movement.
- **DR-0015:** WS-Discovery is a lab-only administrator action bound to one
  exact private interface and explicit CIDRs. It accepts only private literal
  IPv4 XAddrs and never contacts a discovered address.
