# Phase 4 Entry Decision Packet

Status: composite owner choices recorded in
[the owner decision record](owner-decisions.md); separate planning acceptance
and implementation authorization remain pending. Selecting decisions does not
itself authorize implementation.

## D-P4.0-001: Intelligence Relationship Model

### A. Evidence-first bounded hypothesis graph (recommended)

Create time-bounded correlation hypotheses linking immutable event and
reference evidence. Store positive, contradicting, missing, and stale evidence;
keep `identity_state: not_established`; support expiry, supersession, and
retraction. Cross-camera feasibility may use versioned topology, time, and
approved geometry, but never a local track ID or proximity as identity. This
gives strong investigation value without claiming persistent identity.

### B. Flat event groups only

Group related event IDs without graph edges or uncertainty. This is simpler but
limits explanations, contradiction handling, and later investigation tooling.

### C. Persistent entity-resolution graph

Attempt durable cross-camera identities. This is not recommended for the
baseline because Phase 3 intentionally provides no ReID or identity evidence,
and it materially increases privacy, false-association, retention, and legal
risk. It would require a separate future phase and dedicated authorization.

### D. Custom model

Owner supplies exact semantics, identity boundary, retention, and acceptance
evidence.

## D-P4.0-002: Correlation Engine

### A. Deterministic temporal core with optional advisory ranking (recommended)

Use typed windows and predicates for eligibility, then optionally rank eligible
hypotheses using a versioned statistical component. Hard rules, provenance,
abstention, and human review cannot be bypassed by ranking.

### B. Rules only

Use deterministic rules with no statistical ranking. This is easiest to audit
but may create inefficient operator queues when many valid candidates exist.

### C. Model-first correlation

Let a learned model decide relationships. This is not recommended without a
dedicated dataset, calibration, bias, explainability, drift, and rollback
program.

### D. Adaptive Multi-Engine Correlation

Combine a mandatory deterministic temporal-spatial lane, an optional
probabilistic factor-graph lane, a temporal-graph learned candidate lane, and an
optional high-resource ensemble lane through typed arbitration. Every lane
preserves lineage, calibration, contradiction, missing evidence, and abstention.
Capability profiles can add lanes on GPU or cluster hardware without changing
the hypothesis or authority contract. The full research design is documented in
[Adaptive Multi-Engine Correlation Research](adaptive-correlation-research.md).

## D-P4.0-003: Rule Authoring And Expression Policy

### A. Reuse visual graph, typed temporal nodes, and constrained CEL (recommended)

Extend the accepted P3.4 architecture. Stateful behavior stays in closed typed
nodes; CEL evaluates stateless predicates over a closed context. Parse,
type-check, cost-check, canonicalize, approve, shadow-test, and version before
activation. Shadow results remain visibly non-operational and immutable rollback
activates a prior version.

### B. Typed nodes without CEL

Maximizes predictability but requires code changes for every new stateless
condition.

### C. General-purpose scripting

Offers flexibility but introduces arbitrary code, non-determinism, secret and
network risk, and unsafe resource use. It is not recommended.

### D. Custom rule system

Owner defines language, sandbox, resource bounds, versioning, and audit model.

## D-P4.0-004: Alert Authority And Human Review

### A. Proposed alerts with mandatory attributable review (recommended)

The engine creates only proposed alerts. Authorized humans acknowledge,
confirm, dismiss, merge, escalate, resolve, and correct them. No state triggers
autonomous physical action. Independent severity, priority, confidence, and
disposition fields plus bounded alert-volume budgets prevent one score or an
overloaded queue from silently changing authority.

### B. Human review only for high-severity alerts

Lower-priority alerts could proceed automatically. This creates ambiguous
authority and is not recommended before real-world false-positive evidence and
legal policy exist.

### C. Autonomous alert confirmation and dispatch

Not recommended and outside the baseline scope. This would require a distinct
governance, safety, integration, and operational authorization program.

### D. Custom review policy

Owner defines exact transitions, actor roles, actions, and exceptions.

## D-P4.0-005: Reference And Watchlist Integration

### A. Generated provider first; every real provider separately gated (recommended)

Build a typed, default-off adapter using non-issuable generated records. Each
future real provider requires its own purpose, legal/organizational authority,
data contract, fields, secrets, destinations, retention, audit, testing,
revocation, and acceptance package.

### B. Generic adapter with runtime configuration

One generic HTTP/SQL adapter is faster initially but can turn configuration
into an authorization bypass and weakens provider-specific validation.

### C. Direct Government integration in P4.0

Not available under current authority. It risks exposing operational data and
credentials before governance and synthetic behavior are proven.

### D. No reference integration in Phase 4

Defer all providers. Correlation and alert workflows remain useful but do not
exercise the challenge's cross-reference architecture.

## D-P4.0-006: Candidate Match Semantics

### A. Multi-signal candidates with calibration, abstention, and human confirmation (recommended)

Return ranked candidates with per-signal evidence, freshness, uncertainty,
contradictions, and an explicit no-match/insufficient-evidence state. A
candidate never becomes identity from one fuzzy value.

### B. Exact-match only

Simple and conservative, but brittle to OCR and source-data variation and may
miss legitimate candidates.

### C. Single combined match score

Easy to display but hides why a result ranked highly and encourages operators
to treat unlike uncertainties as one truth score.

### D. Custom semantics

Owner supplies signals, thresholds, calibration, abstention, and reviewer
requirements.

## D-P4.0-007: Persistence And Evidence Model

### A. PostgreSQL/PostGIS aggregates plus transactional outbox and append-only evidence (recommended)

Use PostgreSQL for alert/correlation concurrency, PostGIS for approved spatial
relationships, application authorization plus forced row security for department
isolation, immutable effective-time and system-time revisions, W3C-inspired
typed provenance for hypotheses and timelines, and the existing transactional
outbox for state-change events. Store references and digests rather than copying
media or unrestricted source records.

### B. Event log only

Maximizes append-only history but requires projections for every operational
read and raises recovery complexity for the first implementation.

### C. Mutable current-state records only

Simpler reads but insufficient for attributable investigation and correction
history.

### D. Custom persistence

Owner defines consistency, replay, spatial, audit, and recovery guarantees.

## D-P4.0-008: Retention, Hold, And Deletion Baseline

### A. Data-class retention with separately authorized hold overlay (recommended)

Every record has a retention class. A narrowly scoped, attributable hold may
pause deletion for specified evidence; releasing it resumes policy. Generated
Tier A uses short bounded metadata retention and no raw media. Real periods
remain unresolved until policy owners approve them.

### B. One retention duration for all intelligence data

Operationally simple but fails to distinguish alerts, audit, provider queries,
evidence, and generated test data.

### C. Indefinite retention

Not recommended because it maximizes privacy, security, cost, and correction
risk.

### D. Immediate deletion after alert closure

Minimizes storage but can destroy required audit and correction history.

## Original Recommended Selection

`D-P4.0-001:A`, `D-P4.0-002:A`, `D-P4.0-003:A`, `D-P4.0-004:A`,
`D-P4.0-005:A`, `D-P4.0-006:A`, `D-P4.0-007:A`, and `D-P4.0-008:A`.

## Recorded Composite Selection

The owner selected `D-P4.0-001:A+B`, `D-P4.0-002:A+C+D`,
`D-P4.0-003:A`, `D-P4.0-004:A+B+C`, `D-P4.0-005:A+B+D`,
`D-P4.0-006:A`, `D-P4.0-007:A`, and `D-P4.0-008:A` on 2026-09-03.

The combinations are bound by [the owner decision record](owner-decisions.md):
the hypothesis graph is canonical with a flat read projection; AMEC contains
deterministic and model-first research modes; police-intelligence alerts use
mandatory human review while more permissive modes remain class-scoped or
future-gated; and provider contracts/generated simulation are prepared without
any current real or external integration.

## Separate Acceptance And Start Gates

The owner may now accept this planning baseline as `D-P4-PLAN-ACCEPTANCE`. That
permits preparation of a bounded P4.0 implementation authorization package
only.

Executable work requires a later exact `D-P4.0-START` statement bound to the
reviewed package digest and allowlisted paths. It should initially permit only
generated data, default-off controls, local tests, documentation, and local
checkpoint commits. It must continue to prohibit external providers,
credentials, Government/private data, cameras/media, operational activation,
autonomous action, deployment, and remote Git.
