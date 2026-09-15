# P4.4 Authorized Reference Integrations Implementation Plan

Status date: 2026-09-05

Status: non-effective implementation design. Owner decisions, reconciled
planning acceptance, and a separate exact start authorization are pending.

## Objective

Extend the inert P4.0 provider/query boundary into a complete generated-only
reference-integration subsystem. It should prove provider governance, query
policy, generated catalogues, response minimization, deterministic candidate
ranking, abstention, human-review handoff, revocation, recovery, and evidence
without real providers, credentials, network access, real data, models, media,
operational actions, deployment, or remote Git.

## Frozen P4.4 Weight

P4.4 retains the accepted Phase 4 weight of 15 points:

| Item | Points | Completion rule |
| --- | ---: | --- |
| P4.4-A | 4 | Typed provider, transport, secret, destination, purpose, field, freshness, resource, and control contracts pass generated security tests |
| P4.4-B | 4 | Generated non-issuable catalogue, immutable snapshots, bounded query workflow, minimization, freshness, and recovery pass |
| P4.4-C | 4 | Deterministic matching, per-signal evidence, contradiction, calibration, abstention, review handoff, replay, and correction pass |
| P4.4-D | 2 | Provider lifecycle, hierarchical kill switches, revocation race drill, audit/outbox, and no-leak telemetry pass |
| P4.4-E | 1 | Exact reproducible generated-only evidence and separate owner acceptance are recorded |

No partial item receives credit. Planning earns zero implementation points.
Current P4.4 is **0/15 (0.0000%)** and Phase 4 remains **55/100 (55.00%)**.

Technical completion before owner acceptance can reach P4.4 14/15
(93.3333%) and Phase 4 69/100 (69.00%). Exact P4.4-E acceptance reaches P4.4
15/15 (100.0000%) and Phase 4 70/100 (70.00%).

## Proposed Delivery Sequence

### W1: Contracts And Generated Fixtures

Deliver additive V2 provider/query contracts and the P4.4 contracts listed in
the catalogue. Generate deterministic, non-issuable provider manifests,
catalogue snapshots, records, query intents, hostile responses, normalized
records, candidates, freshness states, circuits, and revocation scenarios.

Required evidence:

- strict unknown-field, type, version, size, depth, array, and string bounds;
- recursive denial of URL, credential, raw provider, identity, biometric,
  owner, watchlist, code, SQL, media, dispatch, and enforcement fields;
- canonical serialization and stable SHA-256 identities across processes;
- generated namespace cannot overlap allowed real identifier patterns;
- no fixture is copied from a website, provider, dataset, or real person.

### W2: Provider Policy Compiler

Implement the shared typed kernel that resolves one immutable provider version,
operation, purpose, field projection, destination/auth/trust profile,
freshness/resource/retention policy, and control state into a compiled query
plan.

Required evidence:

- runtime URL, header, method, path, schema, query language, auth, or fallback
  cannot enter through API or provider data;
- every referenced version exists, is same-department where applicable, is
  effective, and contributes to the plan digest;
- stale versions, missing policy, generated/real confusion, incompatible
  adapter capability, and revoked state fail closed;
- plan identity distinguishes semantic idempotency from delivery identity;
- compilation has deterministic CPU and memory bounds.

### W3: Generated Provider And Optional Transport Conformance Boundary

Implement a statically registered in-process generated provider with no socket,
secret, filesystem, subprocess, environment, dynamic import, or startup side
effect. It supports typed generated read operations and fault injection for
partial, malformed, oversized, slow, stale, contradictory, unavailable, and
revoked responses.

If the owner selects D-P4.4-002:D, prepare but do not execute a separately
gated loopback HTTP/TLS conformance harness. Any loopback execution must be
explicitly included in the future start authorization. No external host or DNS
access is permitted.

Required evidence:

- adapter registry is closed and duplicate kinds fail startup validation;
- transport receives only compiled envelopes;
- redirects, proxies, arbitrary destinations, credential values, and provider-
  driven follow-up requests are absent;
- in-process and future loopback result classifications have equivalent
  contract behavior;
- import and test collection perform no query or worker action.

### W4: Catalogue, Queries, Jobs, And Freshness

Add generated catalogue manifests and immutable snapshots, then implement
purpose-bound query intents, compiled plans, semantic dedupe, durable jobs,
attempts, response receipts, normalization, minimized caching, explicit
freshness, bounded leases/retries, circuits, and cancellation.

Required evidence:

- request fields are the exact policy subset and response fields are minimized
  before persistence;
- raw response has zero durable retention and disposal is recorded;
- duplicate delivery and semantic replay do not duplicate provider effects;
- query-ID collision with different material fails;
- stale/expired/partial/unknown states stay visible and cannot appear fresh;
- retry only occurs for allowlisted transient and safe/idempotent operations;
- PostgreSQL workers claim jobs consistently with `SKIP LOCKED` only for queue
  rows; SQLite rejects concurrent-worker mode;
- queue, page, result, byte, decompression, deadline, cost, and retry bounds
  fail explicitly without silent data loss.

### W5: Candidate Matching And Review Handoff

Implement deterministic field-specific normalization and comparisons,
per-signal evidence, contradiction, minimum evidence, bounded ranking,
deterministic ties, top-candidate separation, generated calibration matrices,
and explicit abstention.

Required evidence:

- exact, normalized, approximate, missing, invalid, stale, and contradictory
  signal goldens;
- candidate order is reproducible across process/hash seeds;
- one fuzzy signal cannot produce an accepted identity;
- ambiguous ties, low separation, insufficient evidence, stale source,
  contradiction, provider degradation, and bounds produce abstention;
- top-K and per-candidate signal counts are bounded;
- every candidate and set has `identity_state=not_established`;
- human-review API projection shows evidence and limitations without raw
  provider values outside approved fields;
- synthetic calibration is labeled non-operational and cannot provide a real-
  world accuracy or fairness claim.

### W6: P4.1/P4.3 Integration Boundary

If D-P4.4-008:C is selected, add two independently switchable generated-only
entry paths: manual purpose-bound query and P4.1 generated-hypothesis
enrichment. Candidate sets append typed supporting, contradicting, missing, or
stale evidence revisions through existing contracts.

Required evidence:

- no direct P4.3 lifecycle mutation or alert confirmation route exists;
- correction/retraction creates new attributable evidence revisions;
- query/candidate replay cannot duplicate hypothesis effects;
- provider outage or abstention remains visible and does not suppress the
  original hypothesis;
- mandatory review and authority class remain unchanged;
- independent feature switches default off and production configuration rejects
  generated execution.

### W7: Governance, Revocation, Audit, And Observability

Implement immutable provider versions, generated lifecycle, durable
hierarchical control state, circuit health, revocation barrier, protected audit,
transactional outbox, and low-cardinality metrics.

Required evidence:

- every lifecycle/control mutation requires permission, department, reason,
  expected version, actor, audit, revision, and outbox record;
- global/provider/department/operation/purpose switches are checked before
  queue, claim, secret resolution, adapter, normalization, matching, and commit;
- revocation blocks new work/retries, cancels queued work, quarantines late
  results, and invalidates active cache use without deleting history;
- concurrent revocation and completion has one deterministic outcome;
- metrics/logs/traces/errors/outbox contain no provider values, query values,
  candidate values, destination, hostname, secret reference, or credential;
- canary secret/value tests prove redaction occurs before formatting.

### W8: Security, Compatibility, Evidence, And Acceptance

Run the complete generated security and recovery matrix, preserve P4.0-P4.3
history, validate migration cycles, seal contract/OpenAPI/database snapshots,
build distributable artifacts offline, and prepare a non-effective exact owner
acceptance statement.

The future P4.4 start package must explicitly bind a narrow historical
compatibility transition for `tools/phase43_readiness.py` and
`tests/test_phase43_readiness.py`. The transition may recognize the accepted
P4.3 commit from a later allowlisted P4.4 branch and exclude only exact P4.4
planning/implementation paths from the P4.3 acceptance-sync comparison. It
must continue validating the accepted P4.3 branch, implementation commit,
artifact hashes, migration, changed-path allowlist, evidence, and owner
acceptance from immutable Git objects. No historical P4.3 artifact may be
rewritten, and the transition requires exact path and pre-edit hash bindings.

Required evidence:

- focused P4.4 branch coverage target at least 90%; security-critical policy,
  redaction, destination, revocation, and authority branches fully exercised;
- unconditional repository suite has zero deselection;
- SQLite migration upgrade/downgrade/upgrade and PostgreSQL forced-RLS,
  concurrent-claim, circuit, and revocation tests;
- generated catalogue/query/candidate fixtures reproduce byte-exact;
- dependency and lockfile changes absent unless separately authorized;
- source scan finds no network startup, arbitrary egress, dynamic code, raw
  secret/provider retention, identity assertion, or operational action;
- no unsupported conformance, provider, accuracy, scale, or deployment claim;
- the P4.3 historical verifier transition passes while all immutable P4.3
  hashes and acceptance checks remain byte-exact;
- evidence package and exact owner acceptance are separate gates.

## Proposed Persistence Migration

One additive migration after `0015_alert_lifecycle_orchestration` should create
P4.4 versioned provider policy, query workflow, generated catalogue, candidate,
circuit, and revocation stores. Exact table names and counts will be frozen only
after owner decisions.

Every department-scoped table receives application filtering plus forced
PostgreSQL row security. Product roles cannot own protected tables or use
superuser/`BYPASSRLS`. Foreign keys include department/provider version where
needed to prevent cross-scope joins. Queue claims use deterministic order and
`FOR UPDATE SKIP LOCKED`; ordinary reads do not.

Secret material and raw provider responses are not columns. Normalized
generated fields, digests, receipts, evidence, and history follow explicit
retention classes. Revocation never deletes audit or prior review evidence.

## Proposed Permissions

- `reference.provider.create_generated`;
- `reference.provider.validate`;
- `reference.provider.enable_generated`;
- `reference.provider.suspend`;
- `reference.provider.revoke`;
- `reference.provider.retire`;
- `reference.provider.read`;
- `reference.query.submit_generated`;
- `reference.query.read`;
- `reference.query.cancel`;
- `reference.candidate.read`;
- `reference.control.read`;
- `reference.control.manage_generated`.

No permission implies real-provider access or identity/alert authority. Real
provider administration requires a future separate permission namespace.

## Generated Fixture Matrix

The future package should include at minimum:

- 12 provider manifest/version/lifecycle cases;
- 24 purpose/field/destination/auth/trust policy cases;
- 32 query identity, dedupe, collision, cancellation, and retry cases;
- 40 malformed/oversized/deep/duplicate-key/decompression/page cases;
- 48 freshness/cache/partial/outage/circuit cases;
- 96 exact/normalized/fuzzy/missing/stale/contradictory/ambiguous/abstain match
  cases;
- 24 cross-department and role/ETag/reason cases;
- 24 revocation/kill-switch/race/recovery cases;
- 24 telemetry/redaction/problem-detail/provenance cases.

This is at least 324 deterministic scenario vectors before parameterized
boundary expansion. Counts are planning floors, not implementation evidence.

## Explicit Non-Goals

- no real Government, police, vehicle-owner, registration, ticket, case,
  watchlist, person, biometric, or private provider;
- no credentials, secret manager, token endpoint, certificate, private CA, or
  production trust configuration;
- no Sentinel, camera, ONVIF, stream, frame, image, recording, playback, or
  media access;
- no model, dataset, embedding, learned matcher, download, training, inference,
  GPU, or accelerator work;
- no operational alert, notification, dispatch, enforcement, or autonomous
  action;
- no container, Kubernetes, cloud, pilot, production, release, or deployment;
- no push, pull, fetch, PR, merge, or other remote Git action.

## Future Real-Provider Gate

Generated P4.4 acceptance does not authorize a real integration. Each provider
needs an independent package covering organizational/legal authority, purpose,
data classification, exact operations and fields, destination and trust,
authentication and secrets, rate/cost limits, retention, human workflow,
availability, incident response, revocation, owned-lab validation, operational
owner, and explicit activation acceptance.

## Stop Conditions

Stop future implementation if owner selections are incomplete, the reconciled
package is not accepted, the start package is not exact, a predecessor changes,
or any required control cannot be implemented within the authorized paths and
dependencies. Stop validation on any real-looking fixture, external connection,
credential request, sensitive data, camera/media access, operational action, or
deployment behavior.

## Next Gate

The owner must select D-P4.4-001 through D-P4.4-010. Those selections will be
reconciled and sealed as a planning package. Implementation remains prohibited
until a later exact generated-only start package is separately accepted.
