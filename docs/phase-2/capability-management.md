# ONVIF Capability Management

This subsystem maintains a read-only inventory of explicitly configured ONVIF
devices. It is separate from FFprobe stream-health checks. It does not perform
WS-Discovery, scan networks, move cameras, change configuration, fetch images,
or record video.

## Camera Configuration

An ONVIF stream can define:

| Field | Meaning |
|---|---|
| `management_locator` | Exact credential-free device-service HTTP(S) URL |
| `onvif_auth_mode` | `none`, `wsse_password_digest`, `http_digest`, or `wsse_and_http_digest` |
| `secret_ref` | Opaque credential reference; required for authenticated modes |
| `capability_refresh_enabled` | Explicit opt-in for scheduled refresh; defaults to `false` |
| `capability_due_at` | Next scheduler eligibility time |

Endpoint writes retain Phase 2 department scope, `camera.editor` authorization,
`X-HCAM-Reason`, audit, ETag, and optimistic-lock behavior. URLs cannot contain
credentials, query parameters, or fragments. When `management_locator` is
absent, the deprecated media-only discovery contract remains available.

## Read-Only Query Flow

For a configured device service, the engine queries only:

1. `GetDeviceInformation`
2. `GetSystemDateAndTime`
3. `GetServices`
4. Media `GetServiceCapabilities`
5. Media `GetProfiles`

The engine validates the configured device URL before use and independently
revalidates every returned service URL before contacting it. It normalizes
device identity, firmware, device-clock offset, advertised namespaces, media
features, and at most 64 profiles. Optional unsupported operations become
warnings and a `partial` result. Discovery fails only when no trusted device or
media capability data can be obtained.

Every SOAP response is streamed into a bounded buffer. Environment proxies and
redirects are disabled. TLS verification is always enabled; a private CA can be
selected with `HCAM_ONVIF_CA_BUNDLE`. Raw XML, profile credentials, and
credential-bearing URLs are never returned or persisted.

Each request resolves the exact authorized hostname once, validates every DNS
answer against the rule and private-address policy, and connects to one pinned
approved IP address. The original hostname is retained in the HTTP `Host`
header and TLS SNI, so certificate verification remains bound to camera
identity without allowing the HTTP client to perform a second DNS lookup. A
real synthetic TLS server test verifies the private CA, hostname, SNI, and
pinned-address path together.

## Authentication and Secrets

`CameraSecretProvider` resolves a username and password on every attempt so a
rotation applies without restarting workers. The default provider is
`unconfigured` and fails closed. The `file` provider is limited to development
or private-lab use and is forbidden when `HCAM_ENVIRONMENT=production`.

For the file provider, `secret_ref` resolves below `HCAM_CAMERA_SECRET_ROOT`.
The resolved target must remain inside that root and be a regular JSON file.
Reads are capped at 16 KiB plus one detection byte, so growth between metadata
inspection and reading fails closed. Symlink traversal outside the resolved
root is rejected. Its exact shape is:

```json
{"username":"camera-user","password":"camera-password"}
```

Credentials are excluded from database rows, URLs, responses, audit records,
metrics, logs, exception messages, and object representations. A production
deployment must supply an approved provider implementation backed by its secret
manager before authenticated cameras are enabled.

WS-Security uses a fresh nonce and UTC `Created` value with UsernameToken
PasswordDigest for each request. HTTP Digest is delegated to official `httpx`.
The combined mode applies both mechanisms explicitly.

## Refresh Lifecycle

Manual refreshes have priority over scheduled refreshes. A stream can have only
one active job; an existing queued/running job is returned with
`deduplicated=true`. If simultaneous requests race while creating that job, the
database uniqueness constraint selects one winner and the losing request
re-reads and returns it instead of surfacing a conflict. A completed attempt
starts a 60-second manual cooldown measured from `finished_at`; `queued_at` is
used only as a compatibility fallback when an older terminal row has no finish
timestamp.

Scheduled refresh is opt-in and runs every 24 hours with deterministic
per-stream jitter of up to two hours in either direction. Cached capability
data becomes stale after 36 hours. Transient failures receive at most three
total attempts, with approximately 30-second and two-minute retry delays plus
jitter. Authorization, policy, unsupported, and configuration failures are not
retried. A running job can be reclaimed after its 90-second lease expires.
After every terminal outcome, the worker removes terminal refresh jobs and
non-current capability versions whose last observation is older than 90 days.
The newest snapshot for each stream is always retained, even when stale, so an
inactive camera keeps its last known inventory.
Jobs whose stream is disabled or unexpectedly absent are terminalized before
network access with cleared leases, a sanitized failure audit, retention
processing, and a processed-work result so an invalid backlog drains without
an unnecessary worker poll delay.
Manual and scheduled queue creation are both committed with
`stream.capability_refresh.queue` audit events. Reclaiming an expired lease
commits a separate `stream.capability_refresh.lease_recovered` event before
the replacement worker performs network activity. If either audit write fails,
the queue or lease transaction rolls back and no ONVIF request is attempted.

PostgreSQL workers claim rows with `FOR UPDATE SKIP LOCKED`. SQLite is supported
only with one capability worker. Run a worker with:

```powershell
hcam capability-worker --poll-seconds 5
hcam capability-worker --once
```

Jobs and change snapshots are retained for 90 days. Stable normalized JSON is
fingerprinted with SHA-256. Observation timestamps and device-clock variance do
not affect the fingerprint. An unchanged observation updates the original
snapshot's last-observed time; a changed fingerprint creates history and emits
`hcam.stream.capabilities.changed.v1`.

## API

| Method | Path | Result |
|---|---|---|
| `POST` | `/streams/{stream_id}/capability-refreshes` | `202`, `Location`, lifecycle state, active-job reuse flag |
| `GET` | `/capability-refreshes/{refresh_id}` | Safe status, attempts, times, reason, completeness, snapshot ID |
| `GET` | `/streams/{stream_id}/capabilities` | Latest sanitized snapshot and freshness |
| `GET` | `/streams/{stream_id}/capability-snapshots` | Paginated stable-change history |
| `POST` | `/streams/{stream_id}/capabilities/discover` | Deprecated synchronous compatibility contract |

Queue requests require department access, `camera.editor` or administrator,
and `X-HCAM-Reason`. Inventory reads require `camera.viewer`. A cooldown returns
`429` with `Retry-After`; an active job is reused instead of duplicated.

The deprecated synchronous route uses the same authenticated discovery,
egress, and cache engine. It commits a `capability_discover_sync` operation row
and requested audit event, linked by a unique operation ID, before any camera
request. Success atomically stores the snapshot, marks the operation successful,
and creates the terminal audit event. Failure marks the operation failed with a
bounded reason code. If terminal persistence fails, the transaction rolls back,
leaving the operation pending and no snapshot that could imply unaudited
success; the API returns a sanitized audit-unavailable failure.

## Deployment Boundary

`HCAM_ONVIF_EGRESS_RULES_FILE` must contain version 1 JSON rules with an exact
scheme, hostname/IP, port, and approved CIDR list. Wildcards and public,
multicast, link-local, unspecified, reserved, credential-bearing, unapproved,
ambiguous, non-ASCII host, or DNS-rebound destinations are rejected. HTTP
requires both a matching rule and `HCAM_ONVIF_LAB_HTTP_ENABLED=true`, and is
forbidden in production.

Application checks supplement rather than replace firewall, routing, and
production egress policy. H-CAM does not claim ONVIF conformance. That claim
requires completing the formal ONVIF conformance process for an exact release.

The disposable Compose rule includes Docker's private IPv4 and unique-local
IPv6 ranges because Docker Desktop can publish both addresses for the exact
`onvif-simulator` hostname. Production rules should use the smallest approved
device subnets and ports available.
