# P4.4 Authorized Reference Integration Contract Catalogue

Status date: 2026-09-05

Status: proposed contract design only. Names, fields, and bounds are planning
targets and are not executable contracts.

## Contract Rules

All proposed P4.4 contracts preserve the existing Phase 4 rules:

- UTF-8 JSON with canonical sorted-key compact serialization and SHA-256
  identity;
- unknown fields rejected and recursively bounded documents;
- generated-only, non-operational, default-off, production-forbidden baseline;
- department scope, actor, purpose, policy, chronology, provenance, retention,
  and version are explicit;
- credentials, raw provider data, unrestricted queries, arbitrary destinations,
  identity assertions, code, SQL, media locators, and operational actions are
  prohibited;
- recommendations do not make contracts effective; implementation requires a
  later start package.

P4.4 versions rather than mutates `ReferenceProviderV1` and
`ReferenceQueryV1`. Existing P4.0 records remain readable as inert historical
definitions.

## Proposed Core Contracts

### `ReferenceProviderV2`

Purpose: immutable provider-version aggregate and lifecycle projection.

Required planning fields:

- `provider_id`, `provider_key`, `provider_version`, `department`;
- `provider_class`: `generated_reference` only in Tier A;
- `adapter_kind`: closed registry value;
- `manifest_digest`, `operation_catalog_digest`, `purpose_policy_digest`;
- `destination_policy_digest`, `auth_profile_digest`, `trust_profile_digest`;
- `freshness_policy_digest`, `resource_policy_digest`, `retention_class`;
- `lifecycle_state`, `runtime_health`, `switch_version`;
- `owner_id`, `approved_by`, `created_at`, `effective_at`, `retired_at`;
- `generated_only=true`, `operational=false`, `identity_authority=false`.

Tier-A lifecycle: `draft -> validated -> approved_generated ->
enabled_generated -> suspended|revoked|retired`. Real-provider lifecycle values
are reserved but impossible to reach under P4.4 generated-only constraints.

### `ProviderManifestV1`

Purpose: one canonical definition joining every policy needed to compile a
query plan.

It contains only typed IDs, versions, operation keys, policy references, schema
digests, capability bounds, and compatibility versions. It contains no URL,
secret value, query template, executable code, SQL, arbitrary header, or remote
schema reference. Maximum 64 operations, 32 purposes, 128 field definitions,
and 64 KiB canonical bytes are proposed.

### `ProviderOperationV1`

Purpose: define one named read-only operation.

Fields include operation key/version, adapter operation, request/response schema
digests, safe/idempotent classification, allowed query signals, allowed result
fields, maximum request/response bytes, deadline, page/result count, matching
eligibility, and freshness policy. Tier A permits read-only generated operations
only. Method, path template, query keys, and headers are compiled internal
metadata, never query inputs.

### `ProviderPurposePolicyV1`

Purpose: bind a documented use to the smallest allowed provider operation and
field projection.

Fields include purpose code/version, provider and operation versions,
department eligibility, requester permissions, allowed query signals, required
and allowed result fields, derived-field preferences, maximum frequency,
retention class, review requirement, freshness requirement, and expiry. An
unapproved field fails the request instead of being silently ignored.

### `ProviderDestinationPolicyV1`

Purpose: represent an exact future transport route without exposing arbitrary
runtime configuration.

Planned fields are scheme, service identity, exact port, address authorization
mode, exact path-template ID, method allowlist, query-key allowlist, trust
profile reference, redirect policy fixed to deny, environment-proxy policy
fixed to deny, DNS revalidation policy, maximum connections, and policy digest.
Tier A uses `transport_absent` or separately authorized `generated_loopback`.
No credential-bearing URI, wildcard host, suffix rule, userinfo, fragment, or
response-derived location is allowed.

### `ProviderTrustProfileV1`

Purpose: bind verified TLS behavior.

Fields include trust mode, CA-bundle reference, expected service identity,
minimum TLS policy profile, certificate constraint reference if separately
required, validity/revocation policy, version, and digest. There is no
`verify=false` field. The generated in-process provider uses `not_applicable`;
loopback HTTP requires a separate non-production authorization.

### `ProviderAuthProfileV1`

Purpose: closed discriminated union for authentication behavior.

Planned variants are `none_generated`, `api_key_header`,
`oauth2_client_credentials`, `oauth2_mtls`, `mutual_tls`, `private_key_jwt`, and
`http_message_signature`. Each variant fixes allowed parameters, secret kinds,
audience/scope behavior, covered request components, rotation policy, and
redaction rules. Tier A implements only `none_generated` plus an unconfigured
fail-closed future provider.

### `SecretReferenceV1`

Purpose: opaque pointer to a future credential managed outside H-CAM.

Fields include reference ID, provider kind, expected secret kind, provider and
auth-profile bindings, version policy, owner, state, and expiry metadata. It
contains no path, environment variable name, secret value, token, key,
certificate bytes, or provider-returned identifier.

### `SecretLeaseMetadataV1`

Purpose: sanitized metadata for one secret-resolution outcome.

Fields include lease ID, provider/auth/operation bindings, issued/expiry times,
rotation generation, outcome, and safe reason code. The actual lease material
is process-local, non-serializable, non-loggable, zero-durable-retention, and
outside this contract.

## Query Workflow Contracts

### `ReferenceQueryIntentV2`

Purpose: accepted user/system request before provider execution planning.

Fields include query ID, delivery ID, department, provider/version, operation,
purpose, requested field projection, typed generated query signals, requester,
reason, chronology, and generated marker. It contains no URL, auth material,
free-form query language, provider payload, identity assertion, or raw media.

Proposed bounds: 16 signals, 32 requested fields, 256 characters per generated
token, 8 KiB request body, and one provider operation per intent.

### `CompiledReferenceQueryPlanV1`

Purpose: immutable executable input for a future adapter/transport.

The plan binds canonical intent digest, provider manifest/version, operation,
purpose, field, destination, auth, trust, freshness, resource, and retention
digests; semantic query key; attempt policy; expected schemas; and expiry. It
contains destination/auth handles only as opaque internal references. The
worker revalidates every binding before claim and before result commit.

### `ReferenceQueryJobV1`

Purpose: durable at-least-once workflow state.

States: `queued`, `running`, `succeeded`, `partial`, `abstained`, `failed`,
`cancelled`, `blocked`, and `quarantined`. Fields include semantic and delivery
keys, priority class, not-before/deadline, attempt and lease counters, claimed
policy/switch versions, terminal reason, candidate-set reference, chronology,
and aggregate version.

Proposed defaults: one active job per semantic key, 60-second dedupe/cooldown
floor, no more than three attempts, 60-second lease, bounded jitter, one page by
default, and hard local policy ceilings. Exact values remain an owner decision.

### `ReferenceQueryAttemptV1`

Purpose: append-only sanitized attempt record.

Fields include attempt ID/number, worker class, adapter kind, auth mode,
request/response byte counts, duration bucket, safe transport outcome, HTTP
status class where relevant, retry decision, circuit transition, receipt digest,
and timestamps. It excludes URLs, hostnames, query values, headers, bodies,
credentials, provider IDs as metric labels, exception text, stdout, and stderr.

### `ProviderRequestEnvelopeV1`

Purpose: bounded adapter output accepted only by the powerless transport.

Fields are compiled destination-plan ID, operation key, method, path-template
ID plus typed slots, allowlisted query/header slots, content type, canonical
body bytes/digest, timeout, response limit, and idempotency metadata. The
transport rejects any value not provably derived from the compiled plan.

### `ProviderResponseReceiptV1`

Purpose: prove receipt and validation without retaining raw material.

Fields include request/attempt IDs, response digest, byte count, media type,
status class, receipt time, validation outcome, schema digest, normalization
digest, and disposal confirmation. Raw headers and body have zero durable
retention in Tier A.

## Generated Catalogue And Normalization

### `GeneratedReferenceCatalogueManifestV1`

Purpose: bind a deterministic, non-issuable fixture catalogue.

Fields include catalogue ID/version, generator version, seed digest, record
count, supported operation/field profiles, non-issuable namespace policy,
prohibited-pattern scan result, canonical content digest, created time, and
generated-only markers. No source dataset or downloaded sample is allowed.

### `GeneratedReferenceRecordV1`

Purpose: one invented record used to exercise matching and field policy.

Record categories may simulate generic person-of-interest, vehicle,
registration, permit, ticket, case-reference, and watchlist-like workflows, but
use reserved tokens rather than realistic identifiers or names. Each record
contains only generated record ID, typed non-issuable signals, derived
attributes, effective interval, status, source revision, and generated marker.

### `NormalizedReferenceRecordV1`

Purpose: minimized adapter-independent projection used by matching.

Fields include opaque generated record reference, provider/snapshot/version,
purpose-approved normalized signals, derived assertions, source status,
chronology, freshness, provenance, and integrity digest. It cannot contain
fields absent from the purpose policy even if the provider returned them.

### `ReferenceCatalogueSnapshotV1`

Purpose: immutable set identity and change history.

Fields include snapshot ID, provider/catalogue version, record count, operation
and field profile, first/last observation time, content digest, previous
snapshot reference, change reason, completeness, and generated marker.
Unchanged observations deduplicate by stable fingerprint; chronology variance
does not create a content change.

## Freshness And Resilience Contracts

### `ReferenceFreshnessPolicyV1`

Fields include maximum source age, fresh lifetime, optional stale-advisory
window, expired behavior, negative-cache lifetime, clock-skew allowance,
required timestamp sources, and policy version. Stale advisory is visibly typed
and cannot satisfy a freshness-required match or identity review.

### `ReferenceFreshnessAssessmentV1`

Fields include provider-effective, observed, received, fresh-until,
stale-until, and expired-at times; state `fresh|stale_advisory|expired|unknown`;
clock confidence; policy digest; and safe reason. Unknown is not fresh.

### `ProviderResourcePolicyV1`

Fields include request/response/decompression limits, deadline, page/result/
candidate ceilings, query/match operation budgets, rate, concurrency, cost
units, retry schedule, lease, queue cap, and overload behavior. Every dimension
has both a provider value and a platform hard ceiling.

### `ProviderCircuitStateV1`

Fields include provider/version/operation scope, state
`closed|open|half_open`, failure-window counts, opened time, probe lease,
next-probe time, policy version, and aggregate version. It contains no raw
failure details and is durable for consistent multi-worker behavior.

### `ProviderControlStateV1`

Purpose: hierarchical kill-switch and revocation barrier.

Fields include scope `global|provider|department|operation|purpose`, state
`enabled_generated|paused|revoked`, version, effective time, actor, reason,
policy, and barrier sequence. Every workflow stage must prove it observed the
current barrier before committing output.

### `ProviderRevocationEventV1`

Fields include provider/version, switch scope/version, actor, reason, effective
time, cancelled/blocked/quarantined counts, invalidated cache count, audit and
outbox IDs, and generated marker. Historical records remain immutable.

## Candidate Contracts

### `ReferenceMatchSignalV1`

Purpose: explain one signal comparison.

Fields include signal type, normalization version, comparison method,
observation quality, outcome `exact|compatible|approximate|missing|stale|
contradicting|invalid`, bounded contribution, reason code, source evidence
references, chronology, and policy digest. Values themselves are omitted from
general telemetry and public provenance.

### `ReferenceCandidateV1`

Fields include candidate ID, generated record reference, rank, deterministic
ranking value, evidence sufficiency, contradiction state, freshness state,
signal results, policy version, and `identity_state=not_established`. A candidate
cannot carry alert, guilt, threat, dispatch, or enforcement authority.

Proposed bounds: at most 16 signals per candidate and 20 returned candidates.
Candidate rank is stable under exact ties using canonical record identity.

### `ReferenceCandidateSetV1`

Fields include candidate-set ID/version, query and provider versions,
normalization/match/calibration policy digests, candidate count, top-candidate
separation, completeness, source and freshness state, disposition
`candidates|no_match|insufficient_evidence|ambiguous|contradictory|stale|
provider_unavailable|abstained`, chronology, provenance, and integrity digest.

Every disposition remains mandatory-review. `candidates` does not mean match or
identity.

### `GeneratedMatchCalibrationV1`

Purpose: record deterministic synthetic behavior, not operational performance.

Fields include fixture-manifest digest, matcher/policy version, scenario counts,
exact/fuzzy/contradiction/ambiguity/abstention matrices, thresholds, expected
and observed outputs, and limitation statement. It must state that synthetic
results do not establish real-world accuracy, fairness, or thresholds.

## Persistence Plan

P4.4 is expected to add versioned, department-scoped stores for:

- provider manifests, versions, operation catalogues, and lifecycle revisions;
- purpose, destination, trust, auth, freshness, resource, and control policies;
- query jobs, attempts, receipts, and semantic idempotency records;
- generated catalogue manifests, snapshots, and normalized generated records;
- candidate sets, candidates, and per-signal evidence;
- circuit state, revocation barriers, protected audit, and transactional outbox.

Secret values and raw provider responses are never persisted. Provider,
purpose, field, query, candidate, and control records use application scope plus
forced PostgreSQL RLS. SQLite remains a generated-only single-worker
development boundary. Concurrent queue, circuit, and revocation evidence
requires PostgreSQL.

## Proposed API Families

All routes remain generated-only and behind a future explicit feature flag.
Mutations require department scope, exact permission, `X-HCAM-Reason`, and
`If-Match` for mutable state. Sensitive responses use `Cache-Control: no-store`.

- `GET/POST /reference-providers`: list or create generated draft definitions;
- `GET /reference-providers/{id}`: read a sanitized provider projection;
- `POST /reference-providers/{id}/validate`: deterministic offline validation;
- `POST /reference-providers/{id}/enable-generated`: generated-only enablement;
- `POST /reference-providers/{id}/suspend|resume|revoke|retire`;
- `GET /reference-providers/{id}/health`: bounded generated health projection;
- `GET /reference-providers/{id}/catalogue-snapshots`;
- `POST /reference-queries`: submit a purpose-bound generated query;
- `GET /reference-queries/{id}`: lifecycle and safe outcome;
- `POST /reference-queries/{id}/cancel`;
- `GET /reference-queries/{id}/candidate-set`;
- `GET /reference-candidate-sets/{id}`: bounded candidate projection;
- `GET /reference-provider-controls`: sanitized switch state.

APIs never accept or return URLs, credentials, raw headers/bodies, unrestricted
provider schemas, realistic identifiers, or operational actions. There is no
route that confirms identity or mutates a P4.3 alert.

## Proposed Internal Events

- `hcam.reference.provider.versioned.v1`;
- `hcam.reference.provider.state.changed.v1`;
- `hcam.reference.provider.revoked.v1`;
- `hcam.reference.query.queued.v1`;
- `hcam.reference.query.completed.v1`;
- `hcam.reference.query.failed.v1`;
- `hcam.reference.candidate-set.ready.v1`;
- `hcam.reference.candidate-set.corrected.v1`.

Events contain opaque references, versions, digests, bounded states, and safe
reason codes only. At-least-once delivery is expected; domain effects remain
idempotent. No event is an identity assertion, alert confirmation,
notification, dispatch, or enforcement command.

## Proposed Telemetry

Metrics may label only bounded values such as adapter kind, operation class,
outcome, freshness state, retry class, circuit state, control state, match
disposition, and safe reason code. Provider IDs, departments, actors, query and
candidate IDs, record values, URLs, service identities, secret references,
policy IDs, and digests are prohibited metric labels.

Detailed query history and attribution belongs in protected department-scoped
audit records, not general logs or traces.

## Compatibility And Versioning

- P4.0 V1 provider/query documents remain valid inert history.
- P4.4 V2 documents are additive and use explicit converters/projections.
- Strict producers emit one accepted version; consumers reject unknown major
  versions and may tolerate documented optional minor fields.
- Provider, operation, schema, purpose, field, destination, auth, freshness,
  resource, match, and control versions are independently immutable but joined
  by the compiled plan digest.
- A policy change creates a new version and invalidates incompatible queued
  work. It never mutates prior query or candidate evidence.

## Acceptance Boundary

This catalogue is non-effective planning. Exact schemas, numeric bounds,
storage tables, routes, events, fixtures, and tests require owner decisions, a
reconciled planning package, and a separate start authorization. Real provider
profiles remain independently gated after generated-only P4.4 acceptance.
