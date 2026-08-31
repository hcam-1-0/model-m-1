# `live.corp8.cloud` Public Environment Notes

<!-- markdownlint-disable MD013 -->

Status: read-only public-surface research for Phase 2.5 planning.

Reviewed: 2026-08-28 (Asia/Kolkata).

User-supplied entry points:

- [control room](https://live.corp8.cloud/);
- [camera 18 page](https://live.corp8.cloud/camera/18); and
- the previously reviewed official [Sentinel integration guide](https://sentinel.gujarat.gov.in/resource).

These notes record an observed public environment. They do not establish that
`live.corp8.cloud` is a production Government system, that it is operated by a
particular organization, or that H-CAM is authorized to consume its media.
Organizer confirmation remains required before treating it as the official
Sentinel sandbox integration target.

## Research Boundary

The assessment was intentionally limited to:

- exact public pages supplied by the user;
- exact public metadata endpoints referenced by those pages and scripts;
- page-linked JavaScript and CSS assets;
- standard `robots.txt`, `sitemap.xml`, and `security.txt` locations;
- passive DNS, certificate-transparency, and TLS observations; and
- a real browser run with every HLS, progressive-media, WHEP, and Cloudflare
  telemetry request intercepted before navigation.

The assessment did not:

- authenticate or attempt to bypass authentication;
- guess credentials, enumerate accounts, or submit forms;
- brute-force paths, camera IDs, hosts, or subdomains;
- scan ports or services;
- call a gateway control or publication API;
- connect to RTSP port `8554` or WHEP port `8889`;
- retrieve an HLS manifest, segment, progressive-video byte, frame, image, or
  recording;
- run `ffprobe`, a decoder, analytics, inference, or tracking; or
- retain a copy of a live response body as a fixture.

The API data below is a written observation only. It must not become a static
camera registry because the official guide identifies the catalogue as the
current authority.

## Executive Findings

1. The host exposes a public `CCTV Control Room` page and 30 public camera
   metadata records.
2. It implements the official guide's `/api/ingest` catalogue and publishes
   RTSP, WHEP, and HLS transport metadata.
3. It also retains the older dashboard contract: `/api/cameras`,
   `/api/cameras/{id}/state`, `/stream/{id}`, and preparation status.
4. The two catalogue endpoints returned the same ordered set of 30 camera IDs
   during this observation.
5. All 30 records reported `live` and `rtsp` delivery, but media reachability
   was deliberately not tested. A catalogue status is not proof that a stream
   can be decoded.
6. Nineteen records reported zero or empty technical metadata. H-CAM must map
   these values to unknown, not to a measured zero-width, zero-fps stream.
7. The browser client prefers live HLS, falls back to VOD HLS, and finally uses
   progressive MP4. It exposes the RTSP URL as the AI-ingest value but does not
   use RTSP in the browser.
8. The dashboard remains on its four-second preparation polling path while
   `/api/prepare/status` returns `done: false`, even though all camera records
   report live.
9. The camera page retries aggressively when both HLS and progressive media
   fail. H-CAM must not copy this browser retry behavior into its ingestion
   adapter; the official guide requires bounded exponential backoff.
10. The observed host can support the planned `sentinel_sandbox_catalog_v1`
    contract, but it does not justify replacing or repointing the existing
    `sentinel_reference_v1` adapter.

## Host And Network Observations

### DNS And Edge

The known host resolved through Cloudflare during the assessment:

| Record | Observed value |
| --- | --- |
| `live.corp8.cloud` A | `104.21.59.42`, `172.67.213.199` |
| `live.corp8.cloud` AAAA | `2606:4700:3032::ac43:d5c7`, `2606:4700:3035::6815:3b2a` |
| `corp8.cloud` NS | `eoin.ns.cloudflare.com`, `frida.ns.cloudflare.com` |
| `corp8.cloud` TXT | `v=spf1 -all` |

Cloudflare addresses identify the public reverse-proxy edge, not the origin
server. They must not be used as an origin allowlist.

A bounded HTTPS request to the certificate-disclosed root
`https://corp8.cloud/` returned Cloudflare status 525 during the same review,
while `https://live.corp8.cloud/` returned 200. The root domain therefore must
not be treated as an equivalent application or fallback host.

### Passive Subdomain Evidence

CertSpotter returned seven certificate records whose DNS names contained only:

- `corp8.cloud`; and
- `*.corp8.cloud`.

The wildcard proves that additional names may exist, but it does not disclose
any concrete subdomain. No concrete host besides the user-supplied `live` name
was discovered or contacted. Active subdomain guessing was not performed.

### TLS Observation

A normal TLS connection to the public HTTPS service produced:

| Property | Observed value |
| --- | --- |
| Certificate subject | `CN=corp8.cloud` |
| Issuer | `Let's Encrypt YE1` |
| Valid from | `2026-07-14T07:18:03Z` |
| Valid until | `2026-10-12T07:18:02Z` |
| SHA-1 thumbprint | `8FB67F5FF9BD0049D276A81237367F6C9D180BE1` |
| Negotiated protocol in this client | TLS 1.2 |
| Negotiated cipher suite | `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256` |

This is a dated observation, not certificate pinning material. H-CAM must use
normal hostname and trust-chain validation rather than pinning this short-lived
certificate or Cloudflare IP addresses.

## Public HTTP Surface

### Pages

| Path | Status | Content type | Approximate bytes | Purpose |
| --- | ---: | --- | ---: | --- |
| `/` | 200 | `text/html; charset=utf-8` | 986 | 30-camera control-room grid |
| `/camera/18` | 200 | `text/html; charset=utf-8` | 1,590 | single-camera player shell |
| `/robots.txt` | 200 | text | 1,836 | Cloudflare-managed crawler policy |
| `/sitemap.xml` | 404 | HTML | not retained | no sitemap at the standard path |
| `/.well-known/security.txt` | 404 | HTML | not retained | no security contact at the standard path |

`HEAD` returned 405 for the tested application page. A future metadata adapter
should use a bounded `GET`; it should not assume that `HEAD` is a valid health
probe.

### Robots And Content Signals

The public `robots.txt` allows the generic user agent and publishes:

```text
Content-Signal: search=yes,ai-train=no,use=reference
```

It separately disallows several named crawler and model-training agents. This
assessment uses the site only as a direct integration reference and does not
use its content for model training.

### Response Headers

The sampled pages and JSON endpoints were served by Cloudflare. The API camera
list included `Cache-Control: no-store`; the other sampled responses did not
publish an equivalent cache directive.

The sampled responses did not include:

- `Content-Security-Policy`;
- `Strict-Transport-Security`;
- `X-Frame-Options`;
- `X-Content-Type-Options`;
- `Referrer-Policy`;
- `Permissions-Policy`; or
- `Access-Control-Allow-Origin`.

This is a header inventory, not a vulnerability conclusion. In particular,
the lack of an observed CORS allow-origin header means a third-party browser
origin should not assume it can call the catalogue directly. H-CAM should use
its controlled server-side adapter and its own UI-facing API.

## Linked Client Assets

The HTML linked only the following first-party application assets plus the
Cloudflare Insights beacon:

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `/static/dashboard.js` | 3,311 | `50A748A4ADD54DAA4BC5FA6C9BFC0F807C01D83120D23580EBF3A403A8F3B697` |
| `/static/camera.js` | 10,002 | `B55F3C30BFE2F702D31E0B7A4EEFED5FA1E33540E5183409119B29D30B5BC8BE` |
| `/static/style.css` | 5,573 | `5BBAA7238C18CAEB6E77629F0FFFA9B76003A4FE052DEAA20D6A42EB4DD77F15` |
| `/static/vendor/hls.min.js` | 413,952 | `484054E8CD03D3F6D1781FB7F402BDC318D8A4C527F933A95C624E27CC9A9470` |

The assets reported a common `Last-Modified` value of
`2026-08-21T12:26:49Z`. Hashes are evidence for this observation only and must
not be used as a long-term compatibility or integrity contract.

## Public Metadata APIs

### Endpoint Inventory

| Endpoint | Observed purpose | Response root | Cache observation |
| --- | --- | --- | --- |
| `GET /api/ingest` | official-style current catalogue | `{ "cameras": [...] }` | no explicit cache directive observed |
| `GET /api/cameras` | dashboard/legacy enriched catalogue | `{ "cameras": [...], "catalog": ... }` | `no-store` |
| `GET /api/prepare/status` | media preparation progress | `{ "done": false, "cameras": [] }` | no explicit cache directive observed |
| `GET /api/cameras/18/state` | current camera/player state | one camera-state object | no explicit cache directive observed |

All four sampled API endpoints returned 200 without credentials on the review
date. This describes only the public behavior observed at that time; it does
not grant permission to access media or imply that authentication will remain
absent.

### `/api/ingest` Camera Fields

Each observed camera object contained:

```text
id
number
name
location
codec
live
width
height
fps
bitrate_kbps
bits_per_pixel
rtsp_url
webrtc_url
hls_live_url
```

This matches the official integration guide's high-level catalogue contract.
The exact URLs returned by this endpoint should remain authoritative. H-CAM
must not synthesize transport URLs from the observed patterns.

### `/api/cameras` Additional Fields

The dashboard catalogue added:

```text
status
delivery
container
duration
remote_transcode
detail
```

These are useful compatibility hints, but they are outside the minimal
official `/api/ingest` contract and should be normalized through an optional
legacy extension rather than required by `sentinel_sandbox_catalog_v1`.

### `/api/cameras/{id}/state` Additional Fields

The sampled camera 18 state added player/timeline information:

```text
stream_url
hls_url
timezone
drift_tolerance
offset
slot_offset
slot_seconds
loop
wall_time
server_epoch
```

These fields support the current browser's synchronized loop playback. They
must not silently become the inference clock. The official guide requires
analytics to use media PTS/RTP timestamps.

## Camera 18 Sample

The camera page supplied by the user resolved to this sanitized metadata on
the review date:

| Property | `/api/ingest` or state value |
| --- | --- |
| ID | `18` |
| Name | `Camera 18` |
| Location | `18 Rajkot CCTV` |
| Status | `live` |
| Delivery | `rtsp` |
| Codec | unknown/empty |
| Container | `mp4` in the legacy state |
| Geometry | unknown (`0 x 0` in the source response) |
| FPS | unknown (`0` in the source response) |
| Bitrate | unknown (`0` in the source response) |
| RTSP | `rtsp://live.corp8.cloud:8554/stream/18` |
| WHEP | `http://live.corp8.cloud:8889/stream/18/whep` |
| HLS live | `/live/stream/18/index.m3u8` |
| Progressive fallback | `/stream/18` |
| VOD HLS | absent/null |
| Time zone | `Asia/Kolkata` |
| Drift tolerance | 5 seconds |
| Loop | `true` |
| Slot duration | 43,200 seconds (12 hours) |
| Remote transcode | `false` |

No URL in this table was used to retrieve media. The RTSP and WHEP values use
explicit non-HTTPS schemes and ports. They therefore require exact network,
certificate/authentication, browser mixed-content, and organizer-policy review
before any future connection test.

## Volatile 30-Camera Catalogue Snapshot

This table records public metadata at one instant. `Unknown` means the source
returned an empty codec or zero geometry/rate/bitrate. It does not mean that
the live media lacks those properties.

| ID | Public location label | Codec | Container | Resolution | FPS | Kbps | Remote transcode |
| ---: | --- | --- | --- | --- | ---: | ---: | --- |
| 1 | 01 Chiman bhai Bridge | unknown | mp4 | unknown | unknown | unknown | no |
| 2 | 02 Janpath | unknown | mp4 | unknown | unknown | unknown | no |
| 3 | 03 O.N.G.C. Office | unknown | mp4 | unknown | unknown | unknown | no |
| 4 | 04 Paldi Circle | unknown | mp4 | unknown | unknown | unknown | no |
| 5 | 05 Visat teen Rasta | unknown | mp4 | unknown | unknown | unknown | no |
| 6 | 06 Timbavadi gate-Junagadh | HEVC | avi | 1920x1080 | 25.00 | 1,923 | yes |
| 7 | 07 hero-showroom-gir-somnath | unknown | mp4 | unknown | unknown | unknown | no |
| 8 | 08 majewadi-gate-junagadh | unknown | mp4 | unknown | unknown | unknown | no |
| 9 | 09 new-bypass-near-by-circle-junagadh-2 | unknown | mp4 | unknown | unknown | unknown | no |
| 10 | 10 char-chowk-road-2-junagadh | unknown | mp4 | unknown | unknown | unknown | no |
| 11 | 11 dolatpara-junagadh | unknown | mp4 | unknown | unknown | unknown | no |
| 12 | 12 Tri Mandir Adalaj Tollnaka | unknown | mp4 | unknown | unknown | unknown | no |
| 13 | 13 CN Vidhyalaya | H.264 | mkv | 1920x1080 | 12.50 | 902 | yes |
| 14 | 14 Delight | H.264 | mkv | 1920x1080 | 12.50 | 980 | yes |
| 15 | 15 Suvidha park | H.264 | mkv | 1920x1080 | 12.50 | 690 | yes |
| 16 | 16 Visat P2 | H.264 | mkv | 1920x1080 | 12.50 | 961 | yes |
| 17 | 17 Rajkot Bus Port CCTV | HEVC | mp4 | 1920x1080 | 24.98 | 671 | yes |
| 18 | 18 Rajkot CCTV | unknown | mp4 | unknown | unknown | unknown | no |
| 19 | 19 KHAPARIA GRAM PANCHAYAT, TALUKA GANDEVI, DISTRICT NAVSARI | unknown | mp4 | unknown | unknown | unknown | no |
| 20 | 20 Mohanpura | unknown | mp4 | unknown | unknown | unknown | no |
| 21 | 23 Patan Dethali Char Rasta | unknown | mp4 | unknown | unknown | unknown | no |
| 22 | 28 BK Mervada tran Rasta | HEVC | avi | 1920x1080 | 25.00 | 2,091 | yes |
| 23 | 30 kheram | H.264 | mp4 | 1280x720 | 25.00 | 4,001 | no |
| 24 | 33 dehgam | unknown | mp4 | unknown | unknown | unknown | no |
| 25 | 34 dhanori | unknown | mp4 | unknown | unknown | unknown | no |
| 26 | 35 TANKAL | HEVC | mp4 | 2560x1440 | 13.35 | 2,411 | yes |
| 27 | 36 bilimora | H.264 | mp4 | 1280x960 | 24.86 | 1,112 | no |
| 28 | 37 bilimora | unknown | mp4 | unknown | unknown | unknown | no |
| 29 | 38 bilimora | H.264 | mp4 | 1280x960 | 24.78 | 907 | no |
| 30 | Gandhidham Rambaugh p2 | unknown | mp4 | unknown | unknown | unknown | no |

Snapshot distribution:

| Dimension | Distribution |
| --- | --- |
| Records | 30 |
| Status | live: 30 |
| Delivery | RTSP: 30 |
| Codec | H.264: 7, HEVC: 4, unknown: 19 |
| Container | MP4: 24, MKV: 4, AVI: 2 |
| Unknown geometry | 19 |
| `remote_transcode=true` | 8 |

The `container` values describe source or compatibility metadata and must not
be confused with the live RTSP/RTP transport selected for inference.

## Browser Behavior

### Control Room

The dashboard JavaScript:

1. fetches `/api/prepare/status` and then `/api/cameras`;
2. renders one link per camera as `/camera/{id}`;
3. starts with a four-second polling interval; and
4. changes to a 30-second interval only after `prepDone` becomes true.

During the browser check, the page rendered all 30 live camera cards with no
console error. Because `/api/prepare/status` returned:

```json
{"done":false,"cameras":[]}
```

the page performed another state/list pair after four seconds. If `done`
remains false, each open dashboard client will continue that request cadence.

### Camera Player

The camera JavaScript follows this order:

1. live HLS through hls.js;
2. native live HLS when supported;
3. VOD HLS through hls.js;
4. native VOD HLS when supported; and
5. progressive `stream_url` fallback.

Its live hls.js configuration uses low-latency mode, a two-segment live-sync
target, a six-segment maximum-latency target, an eight-second buffer target,
and a 20-second maximum buffer.

The player also:

- reads the camera ID from the page path;
- fetches `/api/cameras/{id}/state` with `no-store`;
- shows `rtsp_url` as the AI-ingest line;
- derives display synchronization from server epoch and slot offset;
- adjusts playback rate to `1.05` when behind and `0.95` when ahead;
- uses 30 seconds as its hard resync threshold;
- updates the on-screen clock every 250 ms;
- evaluates soft playback sync every three seconds;
- refreshes state/resyncs every five minutes;
- delays a buffering overlay by 600 ms;
- retries a state-fetch failure after five seconds; and
- retries the progressive fallback after three seconds when media errors.

### Blocked-Media Browser Evidence

Before loading either page, the browser context installed routes that returned
local synthetic responses for:

```text
**/live/stream/**
**/stream/**
**/*/whep*
**/cdn-cgi/**
```

The first three returned a local 451 marker; Cloudflare telemetry returned a
local 204. The browser then:

- rendered the dashboard from public page/API metadata;
- navigated to `/camera/18`;
- fetched camera 18 state;
- attempted HLS and progressive fallback only against the local interceptors;
- displayed `RECONNECTING` and `Re-establishing feed...`; and
- produced expected 451 console errors from those local blocked routes.

Across the eight-second camera observation, the client repeatedly fetched the
state endpoint and retried the two blocked media paths. No request reached an
RTSP or WHEP service and no media response reached the browser.

This proves the public UI wiring and fallback order. It does not prove stream
reachability, codec support, decoder startup, timing, or scene-discontinuity
behavior.

## Relationship To Existing H-CAM Adapters

### What Appears Compatible

The host combines both contracts already identified in H-CAM planning:

| Capability | Legacy reference contract | Official guide contract | Observed here |
| --- | --- | --- | --- |
| camera list | `/api/cameras` | `/api/ingest` | both |
| per-camera state | `/api/cameras/{id}/state` | not specified | present |
| RTSP URL | not central to Phase 0 probe | catalogue field | present |
| WHEP URL | not central to Phase 0 probe | catalogue field | present |
| live HLS URL | state-derived | catalogue field | present |
| progressive fallback | `/stream/{id}` | discouraged as integration path | present |
| loop/player timing | state fields | media PTS required | both concepts, different roles |

This is evidence that a normalized H-CAM stream contract can support both
sources without degrading existing features. It is not evidence that the two
environments have identical ownership, stability, authentication, or policy.

### Required Separation

Keep:

- `sentinel_reference_v1` for the existing Phase 0 reference behavior; and
- `sentinel_sandbox_catalog_v1` for `/api/ingest` and its returned transport
  metadata.

Do not:

- repoint the Phase 0 probe to this host;
- make `/api/cameras/{id}/state` mandatory for the official adapter;
- rely on `container`, `offset`, or `slot_seconds` for AI ingest;
- turn empty/zero technical properties into valid decoder settings;
- construct URLs from camera IDs; or
- copy browser fallback and retry policy into the backend.

## Adapter And Pipeline Requirements Added By This Observation

### Catalogue Normalization

The planned adapter should:

- fetch only the exact allowlisted `/api/ingest` URL;
- enforce response timeout, byte limit, camera-count limit, and schema version;
- preserve the source camera ID as an external identifier;
- map empty strings and non-positive technical values to unknown;
- distinguish advertised status from independently observed transport health;
- retain the exact returned transport URL only in a redacted, bounded runtime
  object;
- validate each URL's scheme, hostname, port, and approved address before use;
- reject credentials embedded in URLs;
- disable environment proxies and redirects; and
- expose a sanitized catalogue fingerprint for change detection.

### Transport Selection

Use distinct transport roles:

- RTSP/TCP: inference ingest, only after a separately authorized smoke test;
- HLS: approved fallback or operator preview, not the primary AI clock;
- WHEP: browser preview only unless a later decision expands its role; and
- progressive MP4: compatibility-only browser fallback, not an ingestion API.

### Timing And Stream State

The pipeline must preserve:

- source PTS/RTP timestamps;
- a connection epoch;
- a discontinuity epoch;
- explicit unknown nominal FPS;
- observed decoder properties after startup;
- bounded reconnect state and reason; and
- advertised status separately from actual health.

The legacy state fields can help a browser display a loop, but they cannot
replace PTS-based analytics timing.

### Retry And Load Control

The observed browser is optimized for one human viewer and retries quickly.
The backend needs stricter behavior:

- exponential reconnect backoff around 2, 4, 8, 16, then 30 seconds;
- random jitter and reset only after stable recovery;
- one active connection attempt per camera;
- global and per-host connection ceilings;
- catalogue refresh independent of stream reconnect;
- a circuit breaker for repeated authorization or policy failures;
- prompt decoder/socket cleanup; and
- low-cardinality metrics without camera IDs or URLs as labels.

### Generated Lab Coverage

The local Phase 2.5 lab should reproduce this metadata contract while adding
the official guide's difficult stream behavior:

1. 30-camera dynamic catalogue fixture with unknown metadata cases;
2. H.264 and HEVC sources;
3. 720p, 960p, 1080p, and 1440p geometry examples;
4. 12.5, approximately 13.35, approximately 24.8, and 25 fps declarations;
5. source metadata that requires remote-transcode flags;
6. live HLS present with VOD HLS absent;
7. temporary advertised-live/transport-unreachable mismatch;
8. variable PTS intervals and startup GOP burst;
9. missing initial keyframe and delayed decoder recovery;
10. supervised disconnect and bounded reconnect;
11. hard loop-boundary discontinuity; and
12. changing catalogue membership without synthesized IDs or URLs.

Use generated labels rather than copying public location names into permanent
test fixtures.

## Risks And Open Questions

### Integration Risks

- Public metadata can change without a versioned schema.
- The catalogue can advertise live while a transport is unavailable.
- Nineteen records currently lack usable technical properties.
- Returned RTSP and WHEP endpoints use separate ports and non-HTTPS schemes.
- WHEP over plain HTTP may conflict with browser mixed-content policy when an
  H-CAM UI is served over HTTPS.
- HEVC support varies across browsers, decoders, hardware, and licensing
  environments.
- `remote_transcode` is not defined by the official guide and should remain an
  optional vendor extension.
- Fast dashboard and camera retry loops could multiply load when many clients
  are open.
- Public location labels are operational metadata and should not be copied into
  generated fixtures, metrics, or public logs.

### Questions Requiring Organizer Confirmation

1. Is `live.corp8.cloud` the authorized Sentinel sandbox host for this team?
2. Is the public unauthenticated catalogue intentional and within challenge
   terms?
3. Are RTSP, WHEP, HLS, and progressive paths all authorized for team use, or
   only selected transports?
4. What are the per-team request, connection, bandwidth, and concurrency
   limits?
5. Should `/api/cameras` and per-camera state be treated as supported contracts
   or internal UI endpoints?
6. What is the meaning and lifecycle of `remote_transcode`?
7. How should clients interpret a live record with unknown technical metadata?
8. Is plain-HTTP WHEP expected to be used from an HTTPS browser, or is another
   TLS endpoint supplied after authentication?
9. Is `done: false` the intended steady state for the RTSP-backed catalogue?
10. Are screenshots, short in-memory frame buffers, derived metadata, and
    support logs permitted, and under what retention policy?
11. Is there a published security contact or approved route for responsibly
    reporting environment issues?
12. Which hostnames and addresses should be used for a production-quality
    allowlist when Cloudflare addresses can change?

## Phase 2.5 Decision Impact

This research strengthens the existing plan rather than changing its core
direction:

- continue with a new `sentinel_sandbox_catalog_v1` adapter;
- keep the adapter catalogue-only and read-only by default;
- first implement and validate the contract against generated local fixtures;
- model unknown metadata and dynamic membership explicitly;
- use a shared internal stream contract so existing backend features are not
  degraded;
- require separate authorization before the first live transport connection;
- begin any later live validation with one camera, RTSP/TCP, bounded time,
  zero retention, and a kill switch; and
- never infer deployment, Government-data, recording, analytics, or camera
  control authority from this public metadata assessment.

## Evidence Limitations

- This is a point-in-time observation and can become stale.
- No media path was reached, so codec and transport claims are catalogue
  advertisements only.
- Passive certificate data cannot enumerate wildcard subdomains.
- Cloudflare hides origin identity and origin network details.
- Missing headers or metadata do not by themselves prove a security defect.
- Public reachability does not equal legal or contractual authorization.
- The official relationship between `sentinel.gujarat.gov.in` and
  `live.corp8.cloud` remains an inference until confirmed by the organizer.

Recheck the official guide, catalogue contract, access terms, and host identity
immediately before implementation or any controlled-live test.

## Controlled Runtime Update - 2026-08-28

After the research snapshot above, the owner directed the isolated Phase 2.5
dashboard to use this public sandbox. Current implementation evidence is:

- `/api/ingest` returned 30 records, all advertised live at the observation;
- high and low profiles normalized the same camera membership;
- direct RTSP port 8554 and WHEP port 8889 were unreachable from this laptop;
- exact returned HLS over HTTPS was usable with the site's non-secret
  `cookieCheck=1` bootstrap;
- Camera 23 played as advancing H.264 1280x720 video after stream-copy into a
  dedicated loopback WHEP gateway; and
- the 60-second relay lease renewed successfully without writing media files.

This does not resolve the official-host relationship inference recorded above,
and it does not authorize credentials, hidden endpoints, downloads, recording,
multi-camera scale, analytics, Government/private data, or deployment.
