# Phase 2.5 Backlog And Owner Decisions

<!-- markdownlint-disable MD013 -->

Status: public Sentinel catalogue and one-camera preview implemented; G8
multi-camera external scale and exact-package owner acceptance remain pending.

## Implementation Synchronization

`D-P2.5-START` was authorized after this backlog was drafted. The owner's later
clarification keeps Phase 2.5 as an isolated technical-round lab:
it may exercise stable product contracts, but the product must not depend on the
lab. Product database migrations, product RBAC/API integration, PostgreSQL job
workers, analytics, and deployment remain outside this package. A later owner
correction authorized the exact public Sentinel catalogue plus bounded,
zero-retention browser preview; it did not authorize private/authenticated
access or multi-camera scale.

| Epic | Current first-round status | Remaining or intentionally deferred work |
| --- | --- | --- |
| E1 Contract and fixtures | Implemented | Final evidence digest |
| E2 Catalogue storage and jobs | Lab-local source, refresh, snapshot, membership, history, and SQLite WAL records implemented | Product migrations, PostgreSQL workers, leases, and product scheduler deferred |
| E3 Adapter and reconciliation | Bounded adapter, normalization, durable candidate promotion, rollback, tombstone, and recovery implemented | Product RBAC, department APIs, and product endpoint reconciliation deferred |
| E4 Generated compatibility lab | Implemented for 50 unique fixtures, 30 active by default | Runtime acceptance evidence |
| E5 Timing and faults | PTS contract, epochs, F1-F7 controls, reconnect policy, and Phase 3 handoff implemented | Runtime fault evidence |
| E6 Security and operations | Exact generated-network rules, typed providers, bounds, redaction, cleanup, and evidence verifier implemented | External private-CA execution and product observability integration deferred |
| E7 Controlled external validation | G6 metadata and G7 one-camera smoke executed | G8 multi-camera ramp remains closed |
| E8 Closure | Implementation validation and documentation synchronized | Exact package digest, commit, and owner acceptance |

## Planning Progress

| Item | Status | Evidence |
| --- | --- | --- |
| Official integration guide intake | Complete | `official-sentinel-sandbox-notes.md` |
| Public environment mapping | Complete | `live-corp8-public-environment-notes.md` |
| Separate adapter identity | Confirmed direction | `sentinel_sandbox_catalog_v1` |
| Relationship to accepted Phase 2 | Drafted | `plan.md` |
| Generated lab topology and scenarios | Drafted | `lab-topology-and-test-matrix.md` |
| Adapter data/API contract | Drafted | `catalog-adapter-contract.md` |
| Security and validation gates | Drafted | `security-and-validation-gates.md` |
| Owner choices | Complete | D-P2.5-001 through D-P2.5-008 selected |
| Exact implementation package | Local validation complete | Exact digest, commit, and owner acceptance pending |
| Live metadata/media validation | One-camera smoke complete | G8 remains closed; G9 acceptance pending |

## Implementation Backlog

The numbered backlog below is retained as the complete design record. The table
above is authoritative for the generated-only first-round package; unchecked
product-grade items are deferred, not silently treated as complete.

### Epic P2.5-E1: Contract And Fixtures

- `P2.5-001` Define versioned catalogue input and normalized schemas.
- `P2.5-002` Add generated 0/12/50-record valid fixtures.
- `P2.5-003` Add unknown, duplicate, malformed, hostile URL, and oversized
  fixtures.
- `P2.5-004` Add canonical ordering and semantic fingerprint tests.
- `P2.5-005` Add exact source/transport role vocabulary.

Evidence: P2.5-G1 report.

### Epic P2.5-E2: Catalogue Storage And Jobs

- `P2.5-010` Add source, refresh, snapshot, and membership migrations.
- `P2.5-011` Add typed repository and service boundaries.
- `P2.5-012` Add queued refresh lifecycle, lease, retries, and deduplication.
- `P2.5-013` Add retention and stable-snapshot observation windows.
- `P2.5-014` Add PostgreSQL concurrent-worker and SQLite single-worker tests.

Evidence: migration and P2.5-G2 concurrency reports.

### Epic P2.5-E3: Adapter And Reconciliation

- `P2.5-020` Implement `sentinel_sandbox_catalog_v1` bounded client.
- `P2.5-021` Implement normalization and safe failure mapping.
- `P2.5-022` Implement diff, durable tombstone, and recovery state.
- `P2.5-023` Implement durable automatic apply, candidate promotion, rollback,
  ETag, and reason.
- `P2.5-024` Reconcile `inference`, `preview`, and `fallback` endpoints.
- `P2.5-025` Add RBAC, department isolation, audit, and `no-store` tests.

Evidence: P2.5-G2 API and reconciliation report.

### Epic P2.5-E4: Generated Compatibility Lab

- `P2.5-030` Extend Phase 2 Compose, MediaMTX, and runner with named baseline,
  compatibility, and full-fidelity profiles.
- `P2.5-031` Add generated catalogue simulator.
- `P2.5-032` Add bounded H.264/HEVC profile publishers.
- `P2.5-033` Add 12-camera compatibility, 30-camera default, and 50-camera
  capacity seeders.
- `P2.5-034` Add protected HLS and loopback/private WHEP validation.
- `P2.5-035` Add preflight, lifecycle, evidence, and cleanup runner.

Evidence: P2.5-G3 and G5 reports.

### Epic P2.5-E5: Timing And Faults

- `P2.5-040` Add PTS observation contract and tests.
- `P2.5-041` Add connection and discontinuity epochs.
- `P2.5-042` Add F1-F7 deterministic scenarios.
- `P2.5-043` Add bounded exponential reconnect and jitter tests.
- `P2.5-044` Add Phase 3 media/timestamp handoff contract.

Evidence: P2.5-G4 report.

### Epic P2.5-E6: Security And Operations

- `P2.5-050` Add exact catalogue egress rules and private-CA handling.
- `P2.5-051` Add typed catalogue credential provider, initially fail closed.
- `P2.5-052` Add byte/record/request/connection/bandwidth ceilings.
- `P2.5-053` Add redaction tests and zero-retention assertions.
- `P2.5-054` Add metrics, alerts, audit actions, and events.
- `P2.5-055` Add global kill switch and cleanup-failure detection.

Evidence: P2.5-G3-G5 security and operations reports.

### Epic P2.5-E7: Controlled External Validation

- `P2.5-060` Capture organizer terms, host, auth, load, and retention answers.
- `P2.5-061` Prepare exact metadata-only manifest for G6.
- `P2.5-062` Execute G6 only after explicit authorization.
- `P2.5-063` Prepare exact one-camera zero-retention manifest for G7.
- `P2.5-064` Execute G7 only after explicit authorization.
- `P2.5-065` Prepare/execute G8 only after independent G7 acceptance.

Evidence: exact accepted manifests and sanitized G6-G8 reports.

### Epic P2.5-E8: Closure

- `P2.5-070` Run complete regression, coverage, packaging, and clean-source
  checks.
- `P2.5-071` Produce reproducible evidence manifest and package digest.
- `P2.5-072` Synchronize Phase 2, Phase 3, Phase 7, README, and backlog docs.
- `P2.5-073` Record residual risks and organizer dependencies.
- `P2.5-074` Obtain `D-P2.5-ACCEPTANCE` for the exact commit/package.

Evidence: P2.5-G9 acceptance packet.

## Owner Decisions

### Decision Status

| Decision | Status | Current direction |
| --- | --- | --- |
| D-P2.5-001 | Selected | B: modify Phase 2 directly with protected baseline profile |
| D-P2.5-002 | Selected | A: dedicated catalogue records |
| D-P2.5-003 | Selected | D: 50 unique high-quality fixtures, 30 active by default |
| D-P2.5-004 | Selected | B: durable automatic apply of every accepted snapshot |
| D-P2.5-005 | Selected | D: dual-role WHEP with RTSP as default inference |
| D-P2.5-006 | Selected | A: typed catalogue/media credential providers |
| D-P2.5-007 | Selected | D when permitted, otherwise A |
| D-P2.5-008 | Selected | D: durable no-delete tombstone and automatic recovery |

### D-P2.5-001: Lab Relationship

#### A. Additive compatibility overlay

Keep the accepted Phase 2 50-stream lab unchanged and introduce a separate
Phase 2.5 Compose/MediaMTX overlay. This preserves prior evidence and gives the
new lab a clear meaning.

#### B. Modify Phase 2 directly with a protected baseline (selected)

Extend the existing Compose, MediaMTX, seeder, publisher, runner, and evidence
flow. Preserve the original one-source 50-path test as the named `baseline`
profile and require explicit compatibility/full-fidelity profiles for new
behavior. Historical evidence remains valid for its commit, and every new
change must rerun baseline regression evidence.

#### C. External standalone repository

Strong isolation, but duplicates contracts and complicates CI and handoff.

Recorded decision: **B**.

### D-P2.5-002: Catalogue Persistence

#### A. Dedicated source/refresh/snapshot/membership records (selected)

Preserves provenance, history, diff, grace, and reconciliation without
overloading stream endpoints.

This creates four focused record groups:

- source configuration and authorization boundary;
- every refresh job and safe outcome;
- deduplicated semantic catalogue history; and
- durable camera membership/recovery state.

It uses more migrations and repository code, but supports automatic apply,
rollback, audit, no-delete behavior, and reliable reappearance recovery.

#### B. Store only the latest response on a source row

Fewer tables and faster initial coding. It cannot reliably answer what changed,
which snapshot created an endpoint, whether a missing camera reappeared, or
which version should be restored after a bad update.

#### C. Directly upsert stream endpoints without catalogue records

Fastest prototype because every refresh immediately writes endpoints. It loses
source history and makes no-delete recovery, idempotency, and rollback difficult
to prove.

Recorded decision: **A**.

### D-P2.5-003: Generated Media Strategy

#### A. Eight bounded profiles plus fan-out and serial fault tiers

Provides real codec/timing diversity without requiring 50 simultaneous
encoders on the laptop.

#### B. Fifty unique encoders simultaneously

Maximum live-generation diversity and the highest continuous CPU/GPU load.
Startup is slower, codec availability is hardware-dependent, and one overloaded
laptop can create artificial packet loss that looks like a stream defect.

#### C. One source reused for all 50 paths

Already proven in Phase 2 and does not close the compatibility gap.

#### D. Fifty unique high-quality fixtures with parallel remux (selected)

Generate 50 unique synthetic clips once during `prepare`, using high-quality
H.264/HEVC profiles, visible camera/frame markers, mixed geometry, and controlled
PTS patterns. During the run, stream-copy/remux each fixture in real time to its
own path. This provides unique high-quality camera flows and fast, stable runtime
without spending encoder resources on every frame. Preparation and temporary
disk use are resource-heavy, and dedicated fault publishers remain necessary
for dynamic PTS/restart scenarios.

Recorded decision: **D**. Prepare 50 unique fixtures, activate 30 by default,
and keep 20 deterministic capacity holders for the 50-camera gate. The adapter
must derive each camera's codec, geometry, rate, quality, and transport behavior
dynamically from catalogue and observed metadata.

### D-P2.5-004: Catalogue Reconciliation

#### A. Preview/manual apply outside lab; automatic in generated lab

Balances technical-round speed with enterprise safety and auditability.

#### B. Durable automatic apply of every accepted snapshot (selected)

Every schema-valid, policy-valid, non-anomalous snapshot is durably staged and
applied transactionally. New or changed endpoints begin as candidates, pass
network validation and bounded health checks, then promote automatically. The
last healthy version remains the rollback target. Invalid, hostile, oversized,
ambiguous, or anomalous snapshots fail closed and do not change active streams.

#### C. Never reconcile automatically or through API

Safest but too manual for a dynamic 50-camera technical round.

Recorded decision: **B**, with staging, idempotency, candidate health gates,
append-only history, circuit breaking, and automatic rollback required.

### D-P2.5-005: WHEP Scope

#### A. Browser preview only; RTSP/TCP remains inference

Matches the official guide and keeps the AI ingest contract focused.

#### B. WHEP as a second inference transport

Allows a server-side WebRTC/WHEP receiver to feed decoded frames to AI with low
latency. It adds ICE, DTLS/SRTP, session lifecycle, codec negotiation, packet
loss recovery, and a second timing implementation.

#### C. Defer all WHEP testing

Reduces work but leaves an official preview path unvalidated.

#### D. Dual-role WHEP with RTSP as default inference (selected)

Use WHEP for browser preview and implement an optional server-side WHEP
inference adapter behind a default-off feature gate. RTSP/TCP remains the normal
inference path. Only one transport feeds a camera's analytics session at a time,
and both normalize into the same PTS/discontinuity contract.

Recorded decision: **D**. WHEP supports browser preview and optional
feature-gated server inference; RTSP/TCP remains the default AI ingest path.

### D-P2.5-006: Authentication Strategy

#### A. Typed provider; select live mode after confirmation (selected)

Use opaque `secret_ref` values and resolve credentials for each request. Keep
separate catalogue and media credentials because `/api/ingest`, RTSP, HLS, and
WHEP may use different mechanisms. Supported modes are added only from official
documentation. Rotation works without restarting workers, and missing/expired
credentials fail closed with sanitized reason codes.

#### B. Assume no authentication because current metadata is public

Fastest setup, but it binds architecture to one current public observation. It
cannot safely handle a later token, private technical-round host, or separate
stream credentials.

#### C. Automate browser login/session extraction

Reject: conflicts with service integration, CAPTCHA boundaries, and secret
handling requirements.

It also couples backend operation to CAPTCHA, CSRF, browser cookies, and UI
changes. It should only be reconsidered if organizers explicitly document an
approved non-interactive browser/session integration, which is currently absent.

Recorded decision: **A**.

### D-P2.5-007: Controlled-Live Progression

#### A. G6 metadata, G7 one camera, G8 maximum four cameras

Safest progression. Each stage pauses for evidence acceptance before the next,
which gives strong control but takes more owner interaction and time.

#### B. Connect all current catalogue cameras after metadata success

Fastest route to full scale but creates immediate load, makes one bad codec or
URL affect the full run, and can exceed organizer limits before H-CAM measures
baseline behavior.

#### C. Never test an organizer feed before the technical round

Avoids pre-round access risk but leaves DNS, firewall, codec, timestamp, and
authentication failures until the event.

#### D. Authorized ramp: 0, 1, 4, 16, current count, optional 50 (selected)

Use one exact authorization manifest containing all ceilings. The runner starts
with metadata, then automatically ramps through 1, 4, 16, and the current
catalogue count, expected to be 30. It reaches 50 only when the actual catalogue
and organizer authorization permit it. Every step requires passing health,
latency, bandwidth, error-rate, resource, and cleanup thresholds. Any failure
stops the ladder and closes connections.

Recorded decision: **D when organizer terms permit the ramp; otherwise A with
independent metadata, one-camera, and four-camera gates**.

### D-P2.5-008: Missing Camera Behavior

#### A. Three observations over five minutes, then propose disable

Prevents transient catalogue gaps from removing endpoints and preserves audit.

#### B. Disable after one missing response

Too sensitive to partial/transient responses.

#### C. Never disable missing records

Creates permanently stale inventory.

#### D. Durable tombstone with automatic retry and restoration (selected)

Never delete camera, membership, endpoint, snapshot, health, or audit records.
When absent from valid catalogues, mark membership `missing`, retain last-known
endpoints as inactive, and continue normal catalogue refreshes. When the record
reappears, revalidate its URLs, stage candidates, mark it `recovering`, retry
with bounded backoff, and restore active/primary status after health succeeds.
An offline stream that remains in the catalogue uses the existing health-worker
retry schedule independently of catalogue membership.

Recorded decision: **D**.

## Authorization Statements

Suggested planning acceptance:

```text
D-P2.5-PLAN-ACCEPTANCE: I, mayank-admin, accept the Phase 2.5 planning package
and decisions D-P2.5-001 through D-P2.5-008 as selected. This accepts planning
only and does not authorize implementation, external metadata/media access,
credentials, Government data, recording, analytics, or deployment.
```

Suggested implementation start, only after planning acceptance:

```text
D-P2.5-START: I authorize generated-only Phase 2.5 implementation through
P2.5-G5. External G6-G8 tests remain unauthorized. No Government data,
recording, analytics, camera control, or deployment is authorized.
```

G6, G7, and G8 must each use a later exact manifest and independent owner
authorization. `continue` does not authorize any closed gate.

## Remaining Organizer Inputs

- confirmation that the supplied host is the authorized sandbox;
- exact authentication/service-account method;
- access and availability window;
- request, connection, bandwidth, and concurrency limits;
- exact `/api/ingest` version/error/cache contract;
- permitted RTSP, WHEP, HLS, and progressive transport usage;
- media processing, screenshot, buffer, log, and retention rules;
- support/security contact and incident-reporting procedure; and
- technical-round network and laptop/server constraints.

These inputs still block authenticated/private integration and G8 scale. They
no longer block the implemented public catalogue and one-camera HLS/WHEP smoke.

## Additive Resource-Profile Backlog Record

The generated lab now has two explicitly bounded resource profiles without
changing D-P2.5-001 through D-P2.5-008:

| Item | State | Evidence requirement |
| --- | --- | --- |
| `P2.5-060` Define immutable `lab1highadapter` 50/30 profile | Implemented | Exact full-fidelity counts and no quality downgrade |
| `P2.5-061` Define immutable `lab2lowadapter` 12/4 profile | Implemented | Lower concurrency with unchanged generated fixture quality |
| `P2.5-062` Add guarded durable dashboard switch | Implemented | Exact ID, generated-only confirmation, reason, readiness wait, rollback |
| `P2.5-063` Keep future main adapter independent | Implemented boundary | Product import guard remains green |
| `P2.5-064` Validate both profiles in Docker and browser | Implemented | High, low, return-to-high, WHEP preview, desktop/mobile evidence |
| `P2.5-065` Connect both profiles to the same public Sentinel catalogue | Implemented | Same 30 camera IDs and native metadata under high and low |
| `P2.5-066` Add exact-policy HLS to local-WHEP zero-retention relay | Implemented | Stream-copy, 60-second lease, bounded reconnect, no media files |
| `P2.5-067` Validate one online feed and lease renewal | Implemented | Camera 23, H.264 1280x720, advancing browser playback |
| `P2.5-068` Execute multi-camera public ramp | Closed | Separate authority and resource evidence required |

Only `lab1highadapter` may satisfy generated full-fidelity acceptance evidence.
For online evidence, both profiles must show identical catalogue membership and
native media metadata while enforcing their separate 30/4 and 4/1 ceilings.
