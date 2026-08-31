# Phase 2.5 To Phase 3 Media And Timestamp Handoff

<!-- markdownlint-disable MD013 -->

Status: generated-only contract; Phase 3 remains separate and paused.

## Purpose

This document defines what a future Phase 3 decoder or inference scheduler may
consume from the Phase 2.5 lab. It does not authorize model inference, media
access, analytics, or deployment.

## Stable Contract

For each stream session, the future consumer receives:

- stable H-CAM stream identity and anonymous generated camera identity;
- selected transport role, with RTSP/TCP as the default inference path;
- advertised codec, geometry, nominal FPS, bitrate, and live state;
- observed codec, geometry, rate, and transport health when probed;
- source PTS for every decoded frame or packet;
- `connection_epoch`, incremented after a successful reconnection;
- `discontinuity_epoch`, incremented after an explicit timestamp reset or hard
  loop boundary; and
- safe reason codes for connection, authorization, policy, timeout, codec, and
  discontinuity failures.

## Time Rules

1. Use media PTS/RTP time as the event-time basis.
2. Do not derive elapsed time from frame-arrival rate or catalogue FPS.
3. Require positive monotonic PTS within one discontinuity epoch.
4. Do not silently rewrite a genuine PTS gap into constant-rate timing.
5. Invalidate transient track, dwell, line-crossing, and temporal-rule state at
   every discontinuity epoch.
6. Never join state across connection epochs without a future explicit policy.
7. Keep inference sampling rate independent from source FPS and PTS.

## Transport Rules

- `rtsp_tcp` is the normal inference transport.
- WHEP is always available as a browser preview role when the generated path
  is healthy.
- Server-side WHEP inference is default-off and requires an explicitly
  configured receiver plus the `HCAM_PHASE2_5_WHEP_INFERENCE_ENABLED` gate.
- A camera may have only one active inference transport at a time.
- HLS/WHEP preview success must not hide RTSP inference failure.
- Credentials are resolved per attempt through a typed provider and never
  appear in frame metadata, logs, metrics, or event payloads.

## Recovery Rules

- Retry uses bounded exponential backoff with deterministic jitter and a
  30-second ceiling in the generated lab contract.
- A fault affects only its selected stream; unrelated publishers continue.
- Advertised `live` state and observed transport health remain separate.
- Missing catalogue membership never deletes identity. A recovered record
  resumes the same H-CAM camera mapping.

## Resource And Retention Rules

- The lab may prepare up to 50 unique generated fixtures and activate 30 by
  default.
- Generated media is disposable and excluded from Git.
- Frame payloads, crops, thumbnails, clips, and screenshots are not retained.
- Timing evidence contains only counts, deltas, epochs, hashes, and safe result
  categories.
- No real person, vehicle, plate, location, or Government record enters this
  handoff.

## Example Sanitized Observation

```json
{
  "stream_id": "str_generated",
  "transport": "rtsp_tcp",
  "pts_seconds": 12.438,
  "connection_epoch": 2,
  "discontinuity_epoch": 1,
  "advertised_live": true,
  "observed_health": "online",
  "codec": "h264",
  "width": 1920,
  "height": 1080,
  "retained_frames": 0
}
```

This example is a contract illustration, not a persisted event and not Phase 3
implementation authority.
