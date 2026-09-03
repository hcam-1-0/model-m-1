# Phase 2.5 Sentinel-Compatible Lab Implementation

<!-- markdownlint-disable MD013 -->

Status: online catalogue integration and bounded one-camera playback validated;
G8 multi-camera external scale remains closed.

## Implemented Boundary

Phase 2.5 is a first-round compatibility lab, not an H-CAM product runtime. It
uses accepted Phase 2 APIs where useful but remains under
`hcam.labs.sentinel`; the product application, future analytics pipeline, and
future operator dashboard do not import or depend on it.

The default runtime reads the public Sentinel sandbox catalogue and can open
one ephemeral online preview. It contains no Government/private data,
recording, download, screenshot, frame export, analytics, camera control, or
deployment authority. The generated media system remains an offline fallback.

## Online Sentinel Runtime

- Catalogue: exact public `https://live.corp8.cloud/api/ingest` endpoint.
- Current observation: 30 records and 30 advertised-live entries, within a
  fixed 50-slot lab holder.
- `lab1highadapter`: 30 connection ceiling and four preview sessions.
- `lab2lowadapter`: four connection ceiling and one preview session.
- Both profiles expose the same current catalogue and retain each camera's
  native advertised quality and media type.
- Browser path: validated HLS source plus the required non-secret
  `cookieCheck=1` bootstrap, FFmpeg stream-copy, isolated MediaMTX, loopback
  WHEP.
- Relay lifetime: 60 seconds, renewed by the browser before expiry with bounded
  reconnect attempts.
- Storage: catalogue/state metadata on F drive; online media remains in process
  memory/network buffers and is never written to disk.
- Validation: Camera 23 produced advancing H.264 video at 1280x720 in Chromium.

Direct public RTSP and WHEP ports were unreachable from this laptop, so the HLS
fallback is the validated browser route. That is an environment result, not a
claim that direct transports are absent.

## Components

| Component | Implementation | Result |
| --- | --- | --- |
| Catalogue models | `models.py` | Bounded normalization, exact transport policy, unknown-value handling, semantic hashes |
| Catalogue simulator | `simulator.py`, `fixtures.py` | 0/12/30/50 profiles and deterministic mutation scenarios |
| Catalogue adapter | `adapter.py` | Read-only HTTP(S), ETag, no redirects/proxies, response/record bounds, retries, typed auth |
| Lab adapter profiles | `lab_adapters.py` | Same online catalogue with high 30/4 and low 4/1 connection/preview limits; generated fallback keeps 50/30 and 12/4 shapes |
| Durable lab state | `store.py` | Standalone SQLite/WAL sources, refreshes, snapshots, no-delete memberships, rollback, recovery |
| Generated media | `media.py`, `accelerators.py` | 50 unique H.264/HEVC fixtures with codec, geometry, rate, quality, GOP, timing diversity, and probe-enforced browser-safe H.264 |
| Stream publication | `publisher.py` | Live 30/4 RTSP/TCP publisher reconciliation with identical fixture quality and 50-camera capacity |
| Timing and faults | `timing.py`, `faults.py`, `fault_proxy.py` | PTS evidence, epochs, bounded retry, F1-F7 allowlisted faults |
| Online relay | `hls_relay.py`, `whep_proxy.py`, `standby.py` | Exact-policy HLS stream-copy to loopback WHEP, direct-WHEP proxy option, and no-media inherited-worker heartbeat |
| Test dashboard | `dashboard.py`, `static/` | Shared high/low switch, same live Sentinel inventory, one auto-selected live feed, lease renewal, bounded reconnect, and no locator exposure |
| Transport policy | `transports.py` | RTSP/TCP default and default-off WHEP inference receiver contract |
| Deployment | `compose.phase2-5*.yaml`, `mediamtx.phase2-5*.yml` | Online and generated gateways, CPU/NVIDIA/VAAPI fallback options, private services, recording disabled |
| Lifecycle runner | `tools/phase2_5_lab.py` | Prepare, doctor, media, config, start, verify, fault, stop, and cleanup |
| Evidence verifier | `tools/phase2_5_evidence.py` | Offline package digest, fixture hashes, safety checks, optional runtime checks |

## Generated Fallback Profiles

`lab1highadapter` remains the full-fidelity default: 50 catalogue records, 30
active feeds, and all 50 unique generated fixtures. It is not downgraded for a
lower-resource laptop. `lab2lowadapter` exposes 12 records and four active
feeds while reusing the exact same encoded fixtures. It reduces concurrency,
not codec, resolution, FPS, bitrate, timing, or source quality.

In online mode both lab profiles share one bounded Sentinel catalogue history;
their difference is local resource policy, not camera content. Generated
fallback keeps separate source histories. The future main product adapter
remains outside `hcam.labs.sentinel` and does not depend on either lab profile.
See [the three-adapter architecture](three-adapter-architecture.md).

## Selected Decision Mapping

### D-P2.5-001: Lab Relationship

The Phase 2 Compose baseline is extended through an additive Phase 2.5
overlay. The later owner clarification is authoritative: lab-local state and
UI stay separate, and no product module depends on the lab.

### D-P2.5-002: Dedicated Catalogue Records

The lab has dedicated source, refresh, snapshot, membership, and event tables
in `catalog.db`; online mode uses the separate `sentinel-online-catalog.db`.
This is intentionally not a product migration. Existing lab databases are
migrated additively when fields such as `observed_health` appear.

### D-P2.5-003: Fifty Unique High-Quality Fixtures

Fifty deterministic MP4 fixtures are generated and FFprobe-validated. Thirty
are active by default; C31-C50 are capacity holders. The set includes H.264,
HEVC, 720p through 1440p, fractional rates, VFR, different GOPs, quality
settings, and per-camera visual identities. Encoding uses a validated host or
container accelerator; publication is lossless stream-copy remux. H.264
fixtures explicitly disable B-frames and FFprobe must confirm
`has_b_frames=0`, because MediaMTX WHEP rejects H.264 streams containing
B-frames. HEVC remains in the compatibility set but is not presented as a
browser-compatible WHEP preview.

### D-P2.5-004: Durable Automatic Apply

Every accepted snapshot is applied automatically. Unchanged observations
deduplicate by fingerprint. Changed endpoints are staged, health-gated, and
promoted or rolled back. Mass-change anomalies, duplicate identities, hostile
URLs, malformed values, and oversized input are rejected before apply.

### D-P2.5-005: WHEP Roles

Browser preview uses protected WHEP. RTSP/TCP remains the default inference
transport. A server-side WHEP inference receiver contract exists behind
`HCAM_PHASE2_5_WHEP_INFERENCE_ENABLED`, but it is unconfigured and default-off;
Phase 2.5 never decodes analytics frames. Only one inference transport can be
selected by the contract at a time. Preview eligibility is derived from the
generated fixture's observed FFprobe evidence, not the deliberately imperfect
advertised catalogue codec. Incompatible profiles are disabled in the test UI
and rejected by the playback endpoint.

After publisher and catalogue readiness, the test dashboard automatically opens
the first compatible active generated camera. Operators can switch the live feed
from the inventory or stop it explicitly. Stopping a feed or changing adapters
deletes the short-lived WHEP session, closes the browser peer connection, and
retains no media.

### D-P2.5-006: Typed Credentials

Catalogue and media credential providers are separate typed boundaries.
Generated mode needs no credentials. Bearer/basic catalogue credentials are
resolved on every request from a constrained development provider. Missing
providers, invalid references, traversal, symlinks, and malformed documents
fail closed without exposing secret values.

### D-P2.5-007: External Progression

The owner's later correction authorized this branch to connect the test
dashboard to the public Sentinel sandbox. G6 metadata and a G7 one-camera,
zero-retention browser smoke have therefore been executed. G8 multi-camera
external scale, credentials, private hosts, and deployment remain closed.

### D-P2.5-008: Never Delete Missing Cameras

Absent catalogue records move through `missing` and durable `tombstoned`
states. Memberships and last-known metadata remain. A later observation
recovers the same H-CAM camera identity automatically.

## Generated Profiles And Scenarios

Catalogue modes:

- `compatibility`: 12 active records;
- `low`: 12 records with four advertised live for `lab2lowadapter`;
- `default`: 50 records with 30 advertised live; and
- `capacity`: 50 advertised-live records.

Catalogue scenarios:

- `base`, `empty`, `reordered`, `new`, `offline`, and `updated`;
- `missing`, `duplicate`, `hostile`, `malformed`, and `unknown`; and
- `endpoint` and `codec` semantic changes.

Media faults are exactly `F1` through `F7`. Each request requires the
`generated-only` confirmation, one generated camera, and a 1-30 second bound.
The command file lives in lab state and the F6 RTSP proxy is private to
Compose. No control port is published to the host.

## Storage

Source files remain in Git. Generated MP4 files, SQLite state, fault commands,
and evidence belong under a configurable local state root. Mayank's current
workspace uses:

```powershell
$env:HCAM_PHASE2_5_STATE_ROOT = 'F:\h cam\runtime-storage\phase2-5'
```

`stop` removes generated MP4 files and their transient media manifest while
retaining catalogue metadata and sanitized evidence. The evidence builder
copies only metadata and SHA-256 values before cleanup; it never retains media.

## Runtime Safety

- MediaMTX recording is disabled globally.
- RTSP publication and inference use TCP only.
- PostgreSQL, RTSP, simulator, MediaMTX API/metrics, and fault proxy remain
  private to Compose.
- The additive Phase 2.5 overlay uses the repository's pinned PostGIS image
  because the current Alembic head includes accepted geometry migrations; the
  protected Phase 2 baseline Compose file remains unchanged.
- Dashboard, HLS, and WHEP bind to host loopback only.
- The WHEP HTTP endpoint plus UDP and TCP ICE listeners are mapped to host
  loopback; TCP is a Docker/NAT fallback, and the browser reports connected
  only after the peer connection does.
- Returned destinations require exact scheme, host, port, and path rules.
- Redirects and environment proxies are disabled.
- WHEP uses short-lived playback authorization headers, never query tokens.
- The browser accepts WHEP session `Location` values only from the configured
  origin and session path prefix.
- H.264 fixture validation rejects any B-frame-bearing stream before startup.
- Metrics and events use bounded categories and omit locators and secrets.
- The online test dashboard identifies itself as `sentinel-sandbox` and reports
  `government_data=false`, `recording=false`, and `analytics=false`.
- Dashboard adapter switching is durable, exact-ID only, and changes publisher
  concurrency without changing generated media quality.

## Validation Commands

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py config --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py start --skip-media-prepare --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py verify --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py stop --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

Use `--prepare-generated-fallback` and the generated-media/evidence commands
only when the offline fallback profile is intentionally required.

## Validation Evidence - 2026-08-28

- Repository test collection: 1,091 tests.
- Result: 1,083 passed; eight PostgreSQL integration tests skipped because
  `HCAM_POSTGRES_TEST_URL` was not configured.
- Combined branch coverage: 90%, satisfying the repository gate.
- Focused post-fix check: 22 tests passed without SQLite resource warnings.
- Ruff, JavaScript syntax, and `git diff --check`: passed.
- Package build: `hcam_core-0.2.0.tar.gz` and
  `hcam_core-0.2.0-py3-none-any.whl` built successfully.
- Docker: default online and explicit `generated-fallback` Compose
  configurations validated; online stack healthy.
- Browser high/low/high flow: same 30 records, exact 30/4 and 4/1 resource
  limits, Camera 23 H.264 1280x720 playback, successful lease replacement,
  zero console errors, and no mobile horizontal overflow.

The only general warning is the existing FastAPI TestClient recommendation to
move from `httpx` to `httpx2`. It is dependency-level deprecation output, not a
Phase 2.5 runtime failure.

See [the teammate runbook](teammate-laptop-runbook.md) for accelerator-specific
commands and [the Phase 3 handoff](phase3-media-timestamp-handoff.md) for the
stable future-consumer contract.
