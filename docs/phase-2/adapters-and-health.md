# Adapters and Health Worker

## Adapter Contract

Stored locators are credential-free and limited to explicit HTTP(S), HLS, and
RTSP(S) schemes. The worker defaults to loopback destinations. Every non-loopback
host must appear exactly in `HCAM_STREAM_PROBE_ALLOWED_HOSTS`; wildcards are
rejected. This prevents an authorized endpoint record from silently becoming
an unrestricted server-side request primitive.

Supported Phase 2 adapters:

- `rtsp`, `hls`, and `http`: direct FFprobe metadata inspection;
- `legacy`: compatibility endpoint created from Phase 1 camera records;
- `synthetic`: controlled lab RTSP path;
- `onvif`: explicit SOAP `GetStreamUri` against the local simulator only.

There is no LAN scan, WS-Discovery, camera provisioning, PTZ control, firmware
management, or production secret-manager adapter in this phase.

## FFprobe Controls

- exec-form argument list with `shell=False` and closed stdin;
- 8-second default process and network timeout;
- 100 ms analysis window and 32 KiB probe size;
- 1 MiB stdout/stderr safety ceiling;
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
