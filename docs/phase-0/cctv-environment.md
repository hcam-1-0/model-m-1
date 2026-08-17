# Sentinel CCTV Environment Probe

This document records the safe testing environment for connecting H-CAM 2.0 to
the public Sentinel Gujarat CCTV reference site.

## Purpose

The probe is for Phase 0 environment validation. It helps us understand camera
metadata, stream availability, and format compatibility before building H-CAM
product modules.

This is not a product implementation and not a bulk data collection tool.

## Observed Reference Site

Default base URL:

```text
https://live.sentinelgujarat.in
```

Observed public endpoints:

```text
GET /api/cameras
GET /api/prepare/status
GET /api/cameras/{id}/state
GET /camera/{id}
GET /stream/{id}
```

Observed web app shape:

- Home page title: `CCTV Control Room`
- Camera page title: `CCTV Feed`
- Frontend assets: `/static/dashboard.js`, `/static/camera.js`, `/static/style.css`
- Player path: HLS.js when `hls_url` exists, otherwise progressive stream playback

Observed camera metadata fields:

- `id`
- `number`
- `name`
- `location`
- `duration`
- `codec`
- `container`
- `status`
- `delivery`
- `detail`

Observed camera state fields:

- `stream_url`
- `hls_url`
- `timezone`
- `drift_tolerance`
- `offset`
- `slot_offset`
- `slot_seconds`
- `loop`
- `wall_time`
- `server_epoch`

At the time of initial inspection, `/api/cameras` returned 31 cameras:

- Containers: `mp4`, `mkv`, `avi`
- Codecs: mostly `h264`, with AVI entries
- Status: all listed cameras were marked `live`

These values are live-site observations and can change.

## Tool

CLI:

```powershell
python tools/sentinel_cctv_probe.py metadata
python tools/sentinel_cctv_probe.py state --camera-id 1
python tools/sentinel_cctv_probe.py stream-test --camera-id 1
python tools/sentinel_cctv_probe.py snapshot
python tools/sentinel_cctv_probe.py all
```

Environment variables:

```text
SENTINEL_BASE_URL=https://live.sentinelgujarat.in
SENTINEL_PROBE_CAMERA_IDS=1,6,13,22
```

Default representative cameras:

- `1`: MP4/H264-style case
- `6`: AVI case
- `13`: MKV/H264-style case
- `22`: AVI case

## Safety Rules

- Use read-only public endpoints only.
- Do not bypass authentication, hidden endpoints, or access controls.
- Do not bulk-download CCTV footage.
- Use stream tests only for lightweight metadata compatibility checks.
- Keep probes low-rate and limited to selected camera IDs.
- Treat all Sentinel responses as external reference data, not H-CAM-owned data.
- Do not publish private footage, credentials, or sensitive operational data.

## Stream Test Behavior

`stream-test` fetches one camera state, resolves `hls_url` or `stream_url`, and
runs `ffprobe` against that URL.

The test reports:

- camera id
- live/offline status
- selected delivery path
- selected stream URL
- `ffprobe` return status
- detected stream and format metadata when available

The test does not write any video file.

## Fixtures

`snapshot` writes small JSON files under:

```text
fixtures/sentinel/
```

Generated fixtures are for local offline planning and repeatable development.
They include camera metadata and selected camera state JSON only.

## Known Risks

- The live site may be unavailable or change endpoints.
- Camera metadata and stream status can change over time.
- Mixed containers/codecs mean H-CAM must not assume MP4-only input.
- Progressive streams and HLS streams need separate handling.
- Network latency and buffering can affect live playback tests.
- Legal and authorization boundaries must remain explicit before using any
  non-public dataset, login area, or official sandbox.

## Phase 1 Implication

The first H-CAM implementation phase should include a camera registry and stream
state model compatible with the observed Sentinel shape, while keeping the
adapter isolated so future official APIs or authenticated datasets can replace
this reference source cleanly.
