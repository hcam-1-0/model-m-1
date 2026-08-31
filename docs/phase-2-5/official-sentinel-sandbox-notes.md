# Official Sentinel Sandbox Integrator-Guide Notes

Source: [Consuming the Sentinel Camera Grid](https://sentinel.gujarat.gov.in/resource)

Publisher: Government of Gujarat Home Department / Gujarat Police Innovation
Challenge 2026.

Reviewed: 2026-08-27.

Intake method: read-only retrieval of the public HTML page. No login, API call,
catalogue request, stream connection, media access, control request, or file
download was performed.

## Source Purpose

The page is an official integration reference for teams connecting to the
Sentinel sandbox. It explains:

- the live protocols and endpoint roles;
- how timing and stream delivery behave;
- example client approaches for OpenCV, GStreamer, FFmpeg/ffprobe, and NVIDIA
  DeepStream;
- common client-side failure patterns;
- a pre-submission connection checklist; and
- the information required when reporting a feed problem.

The page displays placeholders such as `<host>` and requires login to access
the live camera environment. It does not publicly reveal the actual sandbox
host, credentials, or authenticated catalogue response.

## Published Environment Contract

The guide describes each camera as a live RTP/RTSP stream rather than a video
file:

- one second of source video takes approximately one second to arrive;
- frames carry monotonic presentation timestamps (PTS);
- clients cannot seek, use byte ranges to run ahead, or accelerate playback;
- the connection should be treated like a physical operational camera feed.

### Published Protocol Roles

| Protocol | Published pattern | Intended use |
| --- | --- | --- |
| RTSP | `rtsp://<host>:8554/stream/<id>` | AI inference through OpenCV, GStreamer, FFmpeg, or DeepStream |
| WebRTC/WHEP | `http://<host>:8889/stream/<id>/whep` | Low-latency browser preview |
| HLS | `http://<host>/live/stream/<id>/index.m3u8` | Dashboards, mobile clients, and networks where RTSP is restricted |

These are documented patterns, not authority to construct URLs. The exact URLs
returned by the catalogue are authoritative.

### Catalogue Contract

The guide identifies:

```text
GET http://<host>/api/ingest
```

The response is described as containing every currently available camera with:

- camera ID;
- location;
- codec;
- live status;
- stream properties; and
- RTSP, WHEP, and HLS URLs.

The official rule is to start from the catalogue. Camera IDs and the available
set may change, so clients must not treat the URL pattern or a previously saved
camera list as the contract.

The page does not publish the exact JSON schema, authentication mechanism,
pagination behavior, error schema, refresh interval, cache policy, or rate
limits.

## Published Client Behavior

### Transport

- Force RTSP over TCP for every inference client.
- UDP may fail across NAT and corporate firewalls and partial delivery can
  resemble a model or decoder defect.
- Use HLS when port `8554` is unavailable.
- DeepStream clients should select RTP-over-TCP; the guide states that both
  H.264 and H.265 are present.

### Timing

- Do not trust a reported or declared frame rate for time-derived analytics.
- Drive timing from PTS/RTP timestamps, not frame arrival wall-clock time.
- The gateway may replay a buffered group of pictures when a client joins so
  the decoder can start at a keyframe. Initial frames may arrive faster than
  real time.
- Motion, dwell, velocity, and tracker prediction must use actual PTS deltas.
- Inter-frame intervals may vary and gaps must not automatically mean that the
  feed disconnected.

### Reconnection And Decoder Startup

- Feeds are supervised and can briefly restart.
- Reconnect with exponential backoff beginning around two seconds and capped
  around thirty seconds.
- Never reconnect in an unbounded tight loop.
- Mid-stream H.265 attachment may emit reference-picture or POC warnings until
  the next IDR/keyframe. The guide classifies these join-time warnings as
  normally self-correcting rather than immediately fatal.

### Heterogeneous Streams

- The grid mixes H.264 and H.265.
- Resolution, codec, frame rate, and bitrate vary by camera.
- Per-camera catalogue properties must drive decoder, buffer, scaling, and
  batching configuration.
- A single fixed input shape cannot be assumed across the grid without an
  explicit scale/pad policy.

### Discontinuity And State

- Each feed loops a continuous recording.
- The loop boundary creates a hard scene cut similar to a camera restart.
- Tracking, background models, and other long-lived state must detect and
  recover from the discontinuity.
- A hard cut must not silently continue an old track epoch or motion history.

### Consumption And Load

- The environment is consume-only.
- Clients must not publish/push streams or call the gateway control API.
- The guide says there is no footage-download workflow.
- The browser fallback `/stream/<id>` uses range behavior for a media player;
  plain `curl`/`wget` can produce a misleading partial file and is not the
  supported integration path.
- Every connected client receives its own stream copy. Open only the cameras
  actively being processed and close captures promptly.

## Official Pre-Submission Checklist

The guide expects teams to establish that:

- every RTSP client forces TCP;
- timing does not depend on `CAP_PROP_FPS` or frame arrival time;
- inter-frame gaps do not crash or stall the pipeline;
- reconnect with backoff is implemented and tested;
- decoder warnings at join are logged but not automatically fatal;
- the camera list and stream properties come from `/api/ingest`;
- mixed H.264/H.265 and mixed resolutions are handled; and
- behavior remains valid across a scene discontinuity.

## Support Evidence

Before reporting a feed as unavailable, the guide requires checking its current
live status in `/api/ingest`. A useful support report contains:

- camera ID;
- exact URL;
- client and version;
- UTC timestamp; and
- client-side error log.

H-CAM should redact credentials or access tokens from the exact URL and logs
before storing or sharing a support bundle.

## Difference From The Existing Sentinel Adapter

The repository currently has an older, read-only Phase 0 reference adapter for
`https://live.sentinelgujarat.in`. That observed environment and the newly
documented official sandbox must remain separate until their relationship is
confirmed.

| Concern | Existing Phase 0 reference | Official resource guide |
| --- | --- | --- |
| Base | `https://live.sentinelgujarat.in` | authenticated `<host>` not public on the page |
| Catalogue | `/api/cameras` | `/api/ingest` |
| Per-camera state | `/api/cameras/{id}/state` | not documented |
| Delivery previously observed | HLS/progressive URLs from state | RTSP, WHEP, and HLS URLs from catalogue |
| Metadata previously observed | MP4/MKV/AVI-style fields | codec, live status, stream properties, dynamic camera set |
| Client contract | metadata/state probe and lightweight ffprobe | live RTP/RTSP semantics, PTS timing, TCP, reconnect, mixed codecs |

Consequences:

- do not repoint `tools/sentinel_cctv_probe.py` to the new host;
- do not rename `/api/cameras` to `/api/ingest` inside the legacy adapter;
- do not assume old metadata fixtures represent the official sandbox;
- create a separately named and versioned official-sandbox adapter contract;
- keep each source's provenance, schema, credentials, URLs, tests, and evidence
  independent.

Confirmed adapter identities for planning:

- `sentinel_reference_v1`: existing public Phase 0 reference adapter;
- `sentinel_sandbox_catalog_v1`: planned new official `/api/ingest` catalogue
  adapter, not implemented or authorized yet.

## Phase 2.5 Lab Implications

Before any official feed is opened, the local generated lab should model:

1. a dynamic `/api/ingest`-compatible catalogue fixture;
2. RTSP-over-TCP as the preferred inference transport;
3. HLS fallback and WHEP browser-preview metadata as separate transport roles;
4. mixed H.264/H.265 sources;
5. mixed resolutions, frame rates, and bitrates;
6. PTS-based timing with variable inter-frame intervals;
7. buffered GOP/keyframe startup behavior;
8. nonfatal decoder warnings before an IDR frame;
9. supervised disconnects and exponential-backoff recovery;
10. a deterministic loop-boundary hard scene cut;
11. bounded active clients and prompt connection cleanup;
12. consume-only enforcement with no recording, download, push, or gateway
    control path.

The current 50-stream Phase 2 lab uses one generated H.264 source remuxed to 50
paths. That proves connection scale and health-state behavior, but it does not
yet prove mixed H.265, heterogeneous geometry, PTS correctness, keyframe join,
scene discontinuity, dynamic catalogue changes, WHEP, or the official adapter
contract.

## Planned Adapter Responsibilities

Phase 2.5 will create a new official-sandbox adapter. Its boundary should remain
narrow:

- authenticate through an approved credential provider without storing secrets
  in URLs, fixtures, logs, or Git;
- fetch only the documented catalogue at a controlled interval;
- validate a bounded response and normalize camera/transport metadata;
- trust returned exact stream URLs only after scheme/host/port policy checks;
- select RTSP/TCP for inference, HLS only as an approved fallback, and WHEP only
  for browser preview;
- expose PTS, discontinuity, reconnect, transport, codec, and stream-health
  metadata to the internal stream contract;
- preserve source camera IDs as external identifiers, not stable H-CAM primary
  keys;
- close idle connections and enforce per-run/global connection ceilings;
- remain read-only and provide no gateway-control or publication operation.

It should not own decoding, AI inference, tracking, recording, evidence storage,
camera control, Government database integration, or deployment policy.

## Unresolved Questions

These questions require official authenticated documentation or organizer
confirmation before an implementation or live-test decision:

1. What is the exact sandbox host and is access internet-public, VPN-restricted,
   or event-network-only?
2. Which authentication method protects `/api/ingest`, RTSP, WHEP, and HLS?
3. Are stream credentials embedded in returned URLs, sent through headers,
   cookies, short-lived tokens, or another mechanism?
4. What is the exact `/api/ingest` JSON schema, versioning policy, maximum size,
   refresh recommendation, and error contract?
5. Are catalogue URLs absolute and short-lived, and may their hosts or ports
   differ from the catalogue host?
6. What are the connection, request-rate, bandwidth, and concurrency limits per
   team/account/IP?
7. What are the sandbox availability window, maintenance policy, and expected
   reconnect frequency?
8. What H.264/H.265 profiles, levels, resolutions, frame-rate ranges, and
   bitrates occur?
9. How should a client identify a loop boundary or source restart beyond
   detecting PTS/scene discontinuity?
10. Is WHEP intended only for humans, or may automated browser tests establish
    preview availability?
11. Are HLS manifest-only checks permitted, and what caching/token rules apply?
12. What processing, screenshot, short-buffer, logging, retention, and demo
    rules apply to the sandbox footage?
13. May teams run multiple clients from separate laptops/nodes, and how is load
    attribution handled?
14. Is there an official support channel beyond the published challenge email,
    and what data must never be included in a support report?

## Safety Gates Before Live Access

The following should be mandatory for Phase 2.5:

- owner acceptance of the Phase 2.5 plan and exact test purpose;
- confirmation of official access terms and organizer authorization;
- exact host, scheme, port, authentication, and certificate policy;
- secret storage and redaction review;
- metadata-only catalogue test before any stream connection;
- exact allowlist and environment-proxy/redirect policy;
- one-camera, time-bounded RTSP/TCP smoke authorization;
- explicit no-recording/no-download/no-frame-export controls;
- connection ceiling, bandwidth budget, timeout, cleanup, and kill switch;
- PTS, reconnect, codec, discontinuity, and log-redaction validation;
- written evidence of what was accessed, when, by whom, and retained;
- separate authorization before scaling beyond one camera.

The public guide itself does not grant these authorizations.

## Planning Conclusions

- The official resource page is the best current public integration contract
  for Phase 2.5.
- The official sandbox is catalogue-driven and live-stream-oriented.
- The legacy reference adapter is useful but is not the official-sandbox
  adapter.
- Phase 2.5 will create `sentinel_sandbox_catalog_v1` as a separate adapter and
  preserve `sentinel_reference_v1` unchanged.
- Phase 2.5 should first expand the generated lab to reproduce the documented
  failure modes and heterogeneity.
- Live integration should progress through metadata-only, one-camera smoke,
  small bounded set, and only then an explicitly approved larger test.
- No implementation or live connection should begin until the unresolved host,
  authentication, usage, load, and retention rules are answered.

Recheck the source immediately before implementation because the catalogue,
login flow, endpoints, dates, and sandbox policies may change.

## Related Public-Environment Evidence

The user later supplied `https://live.corp8.cloud/` as a live environment
reference. Its public metadata surface implements `/api/ingest` alongside the
older dashboard endpoints. See the separately bounded
[`live.corp8.cloud` public environment notes](live-corp8-public-environment-notes.md).
The observed schema strengthens the planned adapter contract, but it does not
prove official ownership or authorize media access.

## Implementation Update - 2026-08-28

The owner's later correction authorized the Phase 2.5 test dashboard to connect
to the supplied public `live.corp8.cloud` sandbox. The adapter now reads the
exact `/api/ingest` catalogue and both lab profiles show its same current 30
records. A one-camera, zero-retention browser smoke succeeded through an exact
returned HLS source, ephemeral stream-copy, and loopback WHEP. This update
supersedes the earlier implementation-status statements above but not their
research limitations or safety requirements. Private/authenticated access,
multi-camera external scale, recording, Government data, analytics, and
deployment remain outside authority.
