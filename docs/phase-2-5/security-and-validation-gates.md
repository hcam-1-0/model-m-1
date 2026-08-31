# Phase 2.5 Security And Validation Gates

<!-- markdownlint-disable MD013 -->

Status: generated gates G1-G5 are implemented; G6 public metadata and a G7
one-camera zero-retention smoke were validated on the public Sentinel sandbox.
G8 multi-camera external scale remains closed.

## Safety Baseline

The new lab and adapter inherit all accepted Phase 2 controls. Phase 2.5 may
make network access more specific but must not make it broader by default.

## Data Classification

| Class | Example | Phase 2.5 treatment |
| --- | --- | --- |
| Generated metadata | Local catalogue fixtures | Allowed in Git when reviewed |
| Generated media | FFmpeg test patterns | Ephemeral only; never committed |
| Public integration metadata | Public catalogue schema and counts | Bounded live retrieval; sanitized metadata/state only |
| Organizer sandbox metadata | Authenticated catalogue | Separate authorization and retention rule |
| Public organizer sandbox media | Simulated-live CCTV feeds | One selected preview; no download; zero retention |
| Production CCTV/Government data | Real operational systems | Prohibited |

Public reachability does not change the classification or grant media access.

## Network Policy

Every external destination requires an exact rule containing:

- environment;
- adapter identity;
- scheme;
- hostname or literal IP;
- port;
- approved resolved addresses or CIDRs;
- TLS/private-CA requirements;
- permitted path prefix;
- purpose; and
- expiry/review date.

Rules:

- no wildcards;
- no redirects;
- environment proxies disabled;
- DNS resolution validated for every attempt;
- public, private, loopback, link-local, and multicast destinations handled by
  explicit, different policies;
- HTTP allowed only in generated/private lab under an exact lab flag;
- verified HTTPS required for external catalogue access when available;
- RTSP forced to TCP for the Sentinel inference role;
- no arbitrary destination from a returned URL; and
- production requires infrastructure egress enforcement in addition to
  application validation.

## Credential Policy

- The generated lab uses no external credentials.
- Authentication mode is explicit and defaults to fail closed.
- Credentials resolve through a typed provider on every request.
- Tokens, passwords, cookies, and API keys never enter URLs, database rows,
  logs, metrics, audit context, exceptions, fixtures, or evidence.
- Secret rotation takes effect without worker restart.
- Development file secrets remain constrained to an approved root, regular
  files, size limits, traversal protection, and no symlink escape.
- Production requires an approved external secret manager.
- CAPTCHA or interactive login is never automated or bypassed.

## Catalogue Request Bounds

Recommended defaults:

| Control | Default |
| --- | ---: |
| Connect/read timeout | 20 seconds total |
| Maximum response | 1 MiB |
| Maximum camera records | 500 |
| Maximum redirects | 0 |
| Active refreshes per source | 1 |
| Global concurrent catalogue requests | 4 |
| Minimum scheduled interval | 30 seconds |
| Recommended interval | 60 seconds plus jitter |
| Job lease | 90 seconds |
| Attempts | 3 total |

The implementation must stop reading as soon as the byte limit is exceeded.
It must not buffer an unbounded response and reject it only afterward.

## Media Connection Bounds

Generated lab:

- compatibility tier: up to 12 active paths;
- operational tier: 30 unique generated paths;
- capacity tier: 50 unique generated paths using prepared fixtures/remux;
- fault tier: up to 4 scenario paths; and
- no media retention.

Controlled external validation:

- metadata gate: zero media connections;
- first smoke: one camera, one client, recommended 60 seconds;
- subset gate: maximum four cameras, recommended five minutes;
- no 50-camera external run without a new explicit authorization;
- no automatic connection to every catalogue record;
- no retry faster than accepted exponential backoff;
- immediate global kill switch; and
- unconditional cleanup on success, failure, timeout, or interruption.

## Retention

Generated durable evidence may contain:

- schema and scenario versions;
- normalized non-sensitive technical properties;
- counts, durations, safe result codes, and hashes;
- resource measurements; and
- zero-retention and cleanup assertions.

It must not contain:

- media, frames, clips, screenshots, thumbnails, or audio;
- exact external stream URLs;
- credentials, cookies, tokens, or authorization headers;
- public/official camera location labels in generated fixtures;
- face, plate, person, or vehicle observations; or
- raw FFmpeg/FFprobe stderr from external streams.

External raw response bodies remain in memory only unless a separately accepted
sanitized snapshot policy applies. Any authenticated organizer rule overrides
this draft and must be reviewed before access.

## Observability

Proposed low-cardinality metrics:

- catalogue refresh queue depth by status/source type;
- refresh outcome and duration by safe result category;
- records accepted/rejected by bounded reason category;
- semantic catalogue changes by change type;
- reconciliation operation outcomes;
- advertised-live versus observed-health aggregate counts;
- active connection and reconnect delay buckets;
- first-packet/first-frame latency buckets in authorized decode tests;
- discontinuity count; and
- secret-provider and egress-policy failures.

Do not use camera IDs, external IDs, URLs, hostnames, location labels, users, or
secret references as metric labels.

Proposed alerts:

- catalogue refresh backlog;
- stale catalogue inventory;
- repeated authorization/policy/schema failure;
- advertised-live/observed-offline divergence above threshold;
- reconnect storm or connection-ceiling rejection;
- unexpected recorder/file creation;
- worker lease recovery spike; and
- cleanup or kill-switch failure.

## Audit Actions

At minimum:

```text
stream_catalog.source.create
stream_catalog.source.update
stream_catalog.refresh.queue
stream_catalog.refresh.complete
stream_catalog.refresh.fail
stream_catalog.reconciliation.preview
stream_catalog.reconciliation.apply
phase2_5.lab.start
phase2_5.lab.fault
phase2_5.lab.stop
phase2_5.external.metadata_test
phase2_5.external.media_test
```

External test audits record the accepted authorization ID, operator, UTC
window, declared camera count, transport, retention mode, and safe outcome.
They do not record exact locators or secrets.

## Validation Gates

Current synchronization: G0 is accepted; generated G1-G5 are implemented. The
owner's later connection correction permitted the exact public Sentinel
catalogue and bounded live dashboard path, so G6 and one-camera G7 execution
evidence now exist. G8 remains closed. G9 still requires final regression, an
exact package digest, and explicit owner acceptance.

### P2.5-G0: Plan Acceptance

Requires:

- accepted topology, adapter boundary, controls, backlog, and owner decisions;
- planning digest; and
- explicit statement that implementation/live access is not yet authorized.

### P2.5-G1: Offline Contract

Requires:

- generated valid, optional, unknown, malformed, duplicate, oversized, and
  hostile URL fixtures;
- parser and canonical fingerprint tests;
- no network access; and
- schema/version evidence.

### P2.5-G2: Catalogue Lifecycle

Requires:

- generated simulator;
- refresh jobs, snapshots, diff, grace, durable automatic apply, candidate
  promotion, rollback, ETag, RBAC, department, audit, events, and lease
  recovery tests; and
- deterministic PostgreSQL concurrency evidence.

### P2.5-G3: Generated Compatibility Media

Requires:

- P1-P8 generated profiles or documented supported equivalents;
- 12-camera compatibility set;
- RTSP/TCP, protected HLS, and bounded WHEP roles;
- no recording or retained media; and
- measured advertised-versus-observed properties.

### P2.5-G4: Timing And Faults

Requires:

- F1-F7 scenario evidence;
- PTS monotonicity and delta assertions;
- connection/discontinuity epochs;
- bounded reconnect; and
- independent stream recovery.

### P2.5-G5: Scale And Regression

Requires:

- existing Phase 2 50-stream gate unchanged and green;
- Phase 2.5 50-record catalogue projection;
- resource and cleanup evidence;
- complete repository regression/coverage gates; and
- no weakening of accepted safety tests.

### P2.5-G6: Public/Official Metadata Compatibility

Requires separate authorization for the exact host and endpoint, even when the
metadata is publicly reachable. It permits one bounded `/api/ingest` retrieval,
schema-only comparison, sanitized evidence, and zero media connections.

Current evidence: executed against exact
`https://live.corp8.cloud/api/ingest`; 30 records were normalized, transport
locators were retained only in the constrained internal store, and API/status
outputs were verified not to expose them.

### P2.5-G7: One-Camera External Smoke

Requires:

- G0-G6 accepted;
- organizer terms and host identity confirmed;
- exact camera selected from the current catalogue;
- 60-second leases and one selected connection at a time;
- an exact returned transport under the approved network policy;
- decode to memory/null with no frame export;
- no model inference or identity analytics;
- connection ceiling, bandwidth budget, timeout, and kill switch; and
- immediate cleanup plus owner evidence review.

Current evidence: Camera 23 was opened through its exact HLS location, copied
without transcoding into the isolated no-recording gateway, and played through
loopback WHEP at 1280x720. Playback remained live across lease renewal. No file,
frame, screenshot export, model, or analytics path was used. Direct public RTSP
and WHEP ports were unreachable from the validating laptop.

### P2.5-G8: Authorized External Ramp

Selected D-P2.5-007 uses one exact authorization manifest when organizers permit
an accelerated ramp. It progresses through metadata, 1, 4, 16, and the current
catalogue count, expected to be 30. It may reach 50 only when the catalogue
actually contains that count and organizers explicitly permit it. Every level
must satisfy health, latency, bandwidth, error-rate, resource, and cleanup
thresholds. Otherwise the plan falls back to option A with independent
authorization and acceptance after metadata, one camera, and four cameras.

Current state: not executed. Profile ceilings do not constitute multi-camera
external validation; the dashboard has opened only one online feed at a time.

### P2.5-G9: Phase Acceptance

Requires:

- accepted generated and any authorized external evidence;
- documented residual risks;
- Phase 3 timestamp/media handoff;
- Phase 7 technical-round runbook inputs; and
- owner acceptance of an exact package digest and commit.

## Test Coverage

The generated fallback and online Sentinel implementation cover:

- unit tests for normalization, bounds, URLs, credentials, and fingerprints;
- property tests for record order, duplicates, numeric edges, and text bounds;
- API tests for RBAC, department isolation, reason, ETag, pagination, and
  `no-store`;
- PostgreSQL tests for refresh/apply concurrency and lease recovery;
- synthetic HTTP tests for timeout, disconnect, oversized streaming bodies,
  invalid JSON, 4xx/5xx, and content-type mismatch;
- generated transport tests for mixed codecs and faults;
- redaction tests across logs, responses, audit, metrics, events, and evidence;
- Docker preflight, port isolation, recording-disabled, cleanup, and resource
  tests; and
- regression tests proving Phase 2 and paused Phase 3 remain unchanged.

Target branch coverage for new adapter/security code should be at least 90%,
with 100% coverage of security policy branches and failure reason mapping.

## Stop Conditions

Any external test stops immediately when:

- the host, certificate, terms, or authentication differs from the accepted
  manifest;
- a redirect, proxy, unapproved address, credential URL, or unexpected scheme
  appears;
- camera count, bytes, bandwidth, duration, or connections exceed the ceiling;
- a file, frame export, recording, or unexpected persistent artifact appears;
- logs or evidence contain a secret or unsanitized locator;
- the kill switch or cleanup cannot be proven; or
- organizer instructions conflict with this plan.

Stopping does not authorize troubleshooting outside the accepted boundary.
