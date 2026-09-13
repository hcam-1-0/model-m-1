# P4.4 Authorized Reference Integrations Decision Packet

Status date: 2026-09-05

Status: options prepared; no P4.4 owner selections or implementation authority
are recorded. Recommendations are not decisions. `Continue`, silence, or partial
answers do not select an option.

## Decision Method

Each decision must be answered by ID and option. Compatible combinations may be
selected explicitly. Incompatible combinations require a written reconciliation
before the planning package can be accepted.

The recommended profile maximizes future enterprise capability while keeping
the first executable P4.4 package generated-only, no-secret, default-off,
production-forbidden, and unable to contact any real provider.

## D-P4.4-001: Provider Composition

### A. One generic runtime-configured connector

Use one HTTP/JSON connector configured with URL, auth, request mapping, and
response mapping.

Benefits: smallest initial adapter surface and fast onboarding.

Risks: configuration becomes executable authority; one malformed profile can
create arbitrary egress, credential confusion, schema drift, or an accidental
real-provider connection. This conflicts with the accepted P4.0 boundary unless
configuration is heavily constrained.

### B. Fully custom service for every provider

Build an independent adapter/service for every provider with no shared
transport kernel.

Benefits: strongest provider-specific isolation and simple local reasoning.

Risks: duplicated authentication, retries, metrics, field policy, redaction,
and lifecycle logic; inconsistent security fixes; higher operational cost.

### C. Shared typed kernel plus immutable manifests and provider-specific adapters

Use one shared policy, lifecycle, query, validation, observability, and
persistence kernel. Each provider has a statically registered adapter and an
immutable compiled manifest that binds operations, schemas, destination, auth,
purpose, fields, freshness, resources, and revocation.

Benefits: reusable enterprise architecture with provider-specific semantics;
generic transport remains powerless; consistent security and audit; a future
provider requires code/manifest review and explicit authorization.

Risks: more initial contract work and strict adapter conformance tests.

**Recommended.**

### D. Separate integration gateway platform

Move all providers behind a dedicated external gateway and expose only one
internal H-CAM protocol.

Benefits: strong egress centralization and organizational separation at scale.

Risks: creates a new platform, deployment, identity, availability, and trust
boundary; excessive for generated P4.4; still needs typed H-CAM contracts.

## D-P4.4-002: Generated Transport Validation Tier

### A. In-process generated provider only

Exercise provider policy, queries, malformed outputs, matching, revocation, and
recovery entirely in memory without sockets.

Benefits: deterministic, fast, no network authorization, no TLS ambiguity.

Risks: does not validate HTTP framing, redirects, content encoding, timeouts,
connection behavior, or TLS identity.

### B. Loopback HTTP/TLS simulator only

Use a bound local simulator to exercise the transport surface.

Benefits: stronger transport evidence.

Risks: slower, more environment-sensitive, requires separate loopback/network
authorization, and can distract from policy correctness.

### C. Contract/static validation only

Define envelopes and validate source shape without executing an adapter.

Benefits: smallest scope.

Risks: insufficient end-to-end evidence for P4.4 generated acceptance.

### D. Staged A plus separately authorized B

Use the in-process provider as mandatory deterministic evidence. Add a separate
loopback HTTP/TLS conformance harness only under an explicit later start scope,
and never make loopback evidence a substitute for policy tests.

Benefits: complete logical coverage now and bounded transport coverage when
authorized; cleanly separates no-network and network-bearing evidence.

Risks: two harnesses and explicit equivalence tests are required.

**Recommended.** The present planning authorization does not authorize B.

## D-P4.4-003: Authentication And Secret Model

### A. Closed typed auth profiles with opaque per-attempt secret leases

Define `none_generated`, `api_key_header`, `oauth2_client_credentials`,
`oauth2_mtls`, `mutual_tls`, `private_key_jwt`, and provider-profiled RFC 9421
message signatures. Bind each to provider/version/operation/purpose/audience.
Resolve opaque secret references per attempt through a fail-closed provider.

Tier A implements only `none_generated` and an unconfigured provider; other
types are contracts for future separately authorized providers.

Benefits: rotation without restart, least privilege, no fallback, no raw secret
storage, and broad future compatibility.

Risks: more discriminated contracts and provider-specific implementation work.

**Recommended.**

### B. Environment variables or local files

Benefits: simple development setup.

Risks: weak rotation, broad process visibility, accidental logs/backups, path
confusion, and unsuitable enterprise lifecycle. Not recommended as a primary
architecture.

### C. Encrypted credentials in the H-CAM database

Benefits: one persistence system.

Risks: the application and database become a credential vault; key management,
rotation, auditing, backup, and breach impact expand substantially.

### D. Unconstrained plugin-defined authentication

Benefits: maximum provider flexibility.

Risks: arbitrary headers/code, inconsistent redaction, and security bypass.

## D-P4.4-004: Destination And TLS Trust Enforcement

### A. Exact compiled route plus application and network egress policy

Bind exact scheme, service identity, port, address policy, path-template ID,
method, query/header slots, trust profile, redirect denial, proxy denial, DNS
revalidation, and connection budgets. Require verified HTTPS and RFC 9525
service identity for future real providers. Require defense-in-depth network
egress controls before deployment.

Benefits: strongest protection against SSRF, DNS rebinding, redirect abuse,
proxy leakage, and provider confusion.

Risks: operational DNS/CDN changes require controlled provider versioning.

**Recommended.**

### B. Exact hostname with path-prefix allowlist

Benefits: easier operations.

Risks: insufficient for multi-address resolution, rebinding, alternate ports,
redirects, proxies, and trust-bundle confusion.

### C. Domain-suffix allowlist

Benefits: flexible for provider subdomains.

Risks: ownership changes and attacker-controlled subdomains can bypass intent.
Not recommended.

### D. Runtime URL with TLS verification

Benefits: fastest configuration.

Risks: TLS does not make an unauthorized destination authorized; allows SSRF
and policy bypass. Prohibited.

## D-P4.4-005: Catalogue Persistence And Freshness

### A. Dedicated normalized catalogue snapshots and minimized result cache

Store generated catalogue manifests, immutable snapshots, normalized
purpose-minimized records, explicit freshness assessments, and cache entries
keyed by department/provider/version/purpose/operation/fields/query/policies.
Keep raw provider bodies at zero durable retention.

Permit policy-authorized stale advisory display with a visible stale state, but
never treat stale or expired data as current or identity-confirming.

Benefits: reproducible matching, change history, offline generated tests,
explicit staleness, and bounded storage.

Risks: more tables and retention/reconciliation logic.

**Recommended.**

### B. Query-through with no catalogue or result persistence

Benefits: minimum storage and lower retained-data risk.

Risks: poor replay/reconstruction, provider load, and no durable freshness or
candidate evidence.

### C. Cache raw provider responses

Benefits: easy debugging and reprocessing.

Risks: excessive fields, sensitive leakage, schema ambiguity, and retention
burden. Prohibited for Tier A.

### D. Event-source every provider field and response

Benefits: maximal history.

Risks: multiplies sensitive data and complexity. Not justified before exact
real-provider governance.

## D-P4.4-006: Query Orchestration And Resilience

### A. Durable bounded jobs with typed leases, retries, circuits, and budgets

Persist semantic query identity, attempt records, leases, deadlines, bounded
retry classes, provider/department/purpose concurrency and cost budgets,
durable circuit state, cancellation, quarantine, and recovery. Only read-only
generated operations execute in Tier A.

Benefits: deterministic at-least-once behavior, multi-worker readiness,
revocation safety, and observable degradation.

Risks: more state-machine and PostgreSQL concurrency tests.

**Recommended.**

### B. Synchronous request-response only

Benefits: simple API and fewer tables.

Risks: weak timeout/recovery behavior and ties operator latency to provider
availability.

### C. In-memory background queue

Benefits: simple asynchronous behavior.

Risks: loses work and revocation state on restart; unsuitable for evidence.

### D. External workflow engine

Benefits: mature retries and scheduling.

Risks: new dependency and deployment boundary; outside current authorization.

## D-P4.4-007: Candidate Matching And Calibration

### A. Deterministic field-specific evidence with bounded ranking and abstention

Use versioned normalizers and comparison methods per field. Preserve exact,
compatible, approximate, missing, stale, invalid, and contradicting outcomes.
Require minimum evidence, top-candidate separation, deterministic ties, bounded
top-K, generated calibration matrices, explicit no-match/ambiguous/abstain, and
mandatory review. Keep `identity_state=not_established`.

Benefits: explainable, testable, CPU-portable, contradiction-aware, and safe
under incomplete evidence.

Risks: generated calibration cannot select operational thresholds.

**Recommended.**

### B. Exact matching only

Benefits: conservative and easy to audit.

Risks: brittle with OCR/transcription variation and incomplete data.

### C. One weighted fuzzy score

Benefits: simple ordering.

Risks: hides signal conflict and encourages false certainty.

### D. Learned or embedding-based matcher

Benefits: potentially stronger ranking on complex data.

Risks: requires models, datasets, calibration, fairness, drift, artifact, and
runtime authorization. Outside P4.4 Tier A.

## D-P4.4-008: Relationship To Correlation And Alerts

### A. Manual generated query workflow only

Authorized users submit a purpose-bound generated query and review candidates.
No P4.1 or P4.3 workflow can initiate or consume it automatically.

Benefits: smallest blast radius and clearest human intent.

Risks: does not prove the hackathon-relevant observation-to-reference flow.

### B. Generated hypothesis enrichment only

P4.1 generated hypotheses may emit typed reference-query intents. Candidate
sets append supporting, contradicting, missing, or stale evidence revisions.
They cannot establish identity or mutate P4.3 lifecycle state.

Benefits: proves pipeline integration while preserving authority boundaries.

Risks: requires cross-module replay/correction and overload tests.

### C. Combined A plus B, independently switchable and default-off

Support both manual generated queries and generated hypothesis enrichment under
separate permissions, purposes, budgets, and feature switches. Both terminate
in mandatory review and preserve identical candidate semantics.

Benefits: strongest usable generated demonstration and future operator support
without weakening the core pipeline.

Risks: broader generated-only implementation scope.

**Recommended.**

### D. Candidate automatically confirms or changes alerts

Prohibited. A provider candidate cannot establish identity, set disposition,
notify, dispatch, or enforce.

## D-P4.4-009: Provider Governance And Revocation

### A. Versioned lifecycle plus hierarchical durable kill switches

Use immutable provider versions and attributable transitions through draft,
validated, generated approval/enablement, suspension, revocation, and
retirement. Add global/provider/department/operation/purpose switches checked
at every workflow boundary. Revocation blocks new work/retries, quarantines
late results, invalidates cache for active use, and preserves history.

Benefits: complete governance and deterministic revocation drill.

Risks: more barrier-version and race testing.

**Recommended.**

### B. One enabled Boolean

Benefits: simple.

Risks: no approval history, scope, version, or revocation barrier.

### C. Configuration removal

Benefits: provider disappears immediately.

Risks: destroys auditability and creates races with queued work.

### D. Deployment-only disablement

Benefits: infrastructure owns provider state.

Risks: too slow and does not cover per-purpose or in-flight application state.

## D-P4.4-010: Raw Material, Audit, And Telemetry

### A. Zero durable raw response with minimized evidence and split telemetry

Validate and normalize within a bounded ephemeral buffer, persist only approved
normalized fields and response receipt digest, and discard raw material. Keep
protected department-scoped audit separate from low-cardinality operational
metrics and sanitized errors.

Benefits: strongest field minimization and smallest leakage/retention surface
while preserving reconstruction of decisions.

Risks: harder provider debugging; requires deterministic generated replay and
provider-side correlation IDs where future policy allows.

**Recommended.**

### B. Short encrypted raw-response retention

Benefits: easier debugging and re-normalization.

Risks: large sensitive-data and key-management burden. Requires separate real-
provider policy and is outside Tier A.

### C. Raw response retained only on failure

Benefits: targets debugging.

Risks: failures often contain the most sensitive or malformed content and are
the worst material to persist.

### D. Provider-configurable retention

Benefits: flexibility.

Risks: configuration can bypass minimization and retention governance.

## Recommended Profile

```text
D-P4.4-001: C
D-P4.4-002: D
D-P4.4-003: A
D-P4.4-004: A
D-P4.4-005: A
D-P4.4-006: A
D-P4.4-007: A
D-P4.4-008: C
D-P4.4-009: A
D-P4.4-010: A
```

This profile is internally coherent. It supports a rich generated laboratory
and a future enterprise integration platform without authorizing any real
provider, credential, data, network, or operational action.

## Required Next Sequence

1. Owner selects every decision by ID.
2. Selections are reconciled into one coherent, non-effective R1 plan.
3. The planning artifacts are resealed and owner accepts the exact digest.
4. A separate generated-only P4.4 start package is prepared.
5. Owner explicitly authorizes that exact start package.
6. Only then may bounded local implementation begin.

No decision in this packet authorizes implementation by itself.
