# Adapters and Health Worker

## Adapter Contract

Stored locators are credential-free and limited to explicit HTTP(S), HLS, and
RTSP(S) schemes. The worker implicitly trusts only loopback IP literals. Every
hostname, including `localhost`, and every non-loopback IP must appear exactly
in `HCAM_STREAM_PROBE_ALLOWED_HOSTS`; wildcards are rejected. Unlisted hostnames
are denied without DNS resolution, closing the validate-then-resolve rebinding
window. This prevents an authorized endpoint record from silently becoming an
unrestricted server-side request primitive.

Supported Phase 2 adapters:

- `rtsp`, `hls`, and `http`: direct FFprobe metadata inspection;
- `legacy`: compatibility endpoint created from Phase 1 camera records;
- `synthetic`: controlled lab RTSP path;
- `onvif`: explicit SOAP stream resolution and authenticated, read-only device
  and media capability operations against configured service URLs.

ONVIF requests use a dedicated opener with environment proxies disabled and
HTTP redirects denied. Both the configured ONVIF URL and the returned RTSP URI
must independently pass the exact network policy.

There is no LAN scan, WS-Discovery, camera provisioning, PTZ control, firmware
management, image capture, recording, or production secret-manager adapter in
this phase.

## Camera Capability Discovery

The primary contract is the queued background API documented in
[ONVIF capability management](capability-management.md). It supports no auth,
WSSE PasswordDigest, HTTP Digest, and combined authentication. Credentials are
resolved through a typed provider on every attempt and never enter locators,
responses, logs, audit records, metrics, or database rows.

The normalized response includes media-service flags, maximum profile count,
and up to 64 configured profiles with video encoding, resolution, frame-rate
limit, audio encoding, and whether PTZ, analytics, or metadata configuration is
attached. Each SOAP response is limited to 256 KiB. Results use `no-store` and
are not persisted as authoritative camera configuration.

`POST /streams/{stream_id}/capabilities/discover` remains as a deprecated
synchronous compatibility route and now shares the normalization and snapshot
logic. A media-only endpoint remains identified as `media_only`.

This is capability discovery for one already configured device endpoint. It is
not network discovery: H-CAM does not enumerate hosts, probe address ranges, or
use WS-Discovery. Every advertised service URL is revalidated before contact.

## FFprobe Controls

- exec-form argument list with `shell=False` and closed stdin;
- 8-second default process and network timeout;
- 100 ms analysis window and 32 KiB probe size;
- execution-time 1 MiB ceiling on each stdout/stderr pipe; FFprobe is terminated
  as soon as either ceiling is exceeded;
- selected video/format fields only;
- no frame extraction and no output media file;
- normalized reason codes; raw stderr is not persisted or returned.

An unavailable FFprobe binary is a worker runtime failure. A single unreachable
camera is an endpoint result and does not terminate the worker.

## Health State Machine

| Observation | New state | Next probe |
|---|---|---|
| First success after non-healthy state | `degraded` | 10 seconds |
| Second consecutive success | `healthy` | 30 seconds |
| First or second transient failure | `degraded` | 10 seconds |
| Third transient failure | `offline` | exponential backoff |
| Continued offline failure | `offline` | up to 5 minutes |
| Authentication rejection | `unauthorized` | 5 minutes |
| Invalid config or network policy denial | `misconfigured` | 5 minutes |
| Unsupported media | `unsupported` | 5 minutes |

Every state change is committed with an outbox event in the same transaction.
The dispatcher delivers by `event_id` with at-least-once semantics and marks the
row published only after the sink succeeds. The synthetic lab uses a
metadata-only logging sink; a production event-bus adapter is intentionally not
selected in Phase 2.
The primary stream also updates the legacy camera health/codec/container
projection. Probe history is purged after seven days.

## Concurrency

PostgreSQL claims due endpoints with `FOR UPDATE SKIP LOCKED`, a worker ID, and
a bounded lease. Lost or expired leases can be reclaimed. SQLite is explicitly
single-worker only. A missing FFprobe binary releases the claim before the
runtime error is surfaced.
