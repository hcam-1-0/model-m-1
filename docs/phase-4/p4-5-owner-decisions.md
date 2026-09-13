# P4.5 Owner Decisions And Reconciliation

Status date: 2026-09-05

Status: all ten P4.5 design decisions are recorded and effective for planning
reconciliation only. They do not authorize implementation, evidence/source
access, legal case management, PROV conformance, retention periods, holds,
deletion, exports, real investigations, data, runtime, deployment, or remote
Git.

Owner: `mayank-admin`

Planning predecessor: `P4.5-PLANNING-R0`, SHA-256
`B9BA1BB488EA631577AA78D97E190956B67C686C96C261AE641ACAA14C0C04A0`.

## Recorded Selection

```text
D-P4.5-001: A and try to do D as well
D-P4.5-002: A
D-P4.5-003: A
D-P4.5-004: A and try to add C
D-P4.5-005: A
D-P4.5-006: A
D-P4.5-007: A
D-P4.5-008: A
D-P4.5-009: A
D-P4.5-010: A
```

`Try to do` and `try to add` are binding architecture-capability requests, not
permission to activate incompatible options as written. The selected A controls
remain authoritative. The reconciled design provides guarded typed extension
surfaces for D-P4.5-001:D and D-P4.5-004:C without turning P4.5 into a legal
case-management system or claiming formal W3C PROV conformance.

## Reconciled Profile

| Decision | Planning binding |
| --- | --- |
| `D-P4.5-001:A+[D capability]` | Case-neutral dual-clock/sequence timeline remains canonical; add a disabled typed bridge for future authorized case systems |
| `D-P4.5-002:A` | Closed entry families, discriminated payloads, immutable versions, and typed causal links |
| `D-P4.5-003:A` | Immutable source-reference envelopes with separate append-only resolution, integrity, availability, preservation, and provenance states |
| `D-P4.5-004:A+[C capability]` | H-CAM constrained PROV-inspired graph remains canonical; add a derived disabled PROV interchange projection and generated mapping tests |
| `D-P4.5-005:A` | Append-only corrections/retractions with bounded durable impact propagation and visible partial state |
| `D-P4.5-006:A` | Orthogonal review/disposition/lifecycle state, non-destructive merge aliases, and explicit reopen revisions |
| `D-P4.5-007:A` | Immutable retention-policy references and separately authorized scoped hold overlays that never grant access |
| `D-P4.5-008:A` | Exact deletion intents/receipts, per-target outcomes, explicit residuals, and no universal-deletion claim |
| `D-P4.5-009:A` | Purpose-bound reference-only canonical manifests first; payload/signature/timestamp/BagIt/ERS profiles stay separately gated |
| `D-P4.5-010:A` | Bounded PostgreSQL/RLS append-only stores, restrictive links, outbox, generated-only APIs, and deterministic validation |

## D-P4.5-001: Case-Neutral Timeline With Guarded D Capability

Option A is authoritative. H-CAM owns a case-neutral investigation timeline,
not a statutory case or records-management system. It preserves two views:

1. event-time chronology using source occurrence/observation time and explicit
   precision, trust, skew, and unknown states;
2. trusted record chronology using receive time, durable record time, immutable
   aggregate revision, and monotonic sequence.

Lifecycle, disposition, evidence integrity, hypothesis confidence, alert state,
hold state, and export state remain independent.

### Guarded D capability: `CaseManagementBridgeContract`

The architecture may define a disabled, typed bridge that can later project an
H-CAM timeline into an authorized case-management profile or associate it with
an opaque external case reference. The bridge is an interoperability boundary,
not a second source of truth.

The bridge must preserve these controls:

- H-CAM timeline and entry identities remain stable and immutable;
- an external case reference is opaque, versioned, department/purpose scoped,
  and never becomes the timeline primary key;
- external case state cannot silently change H-CAM lifecycle, disposition,
  evidence integrity, retention, hold, deletion, export, review, or access;
- every future import or export uses an immutable mapping profile, exact source
  version, idempotent command, actor/service, reason, policy, and audit/outbox;
- conflicting mappings, stale external versions, cross-department references,
  missing authority, and unknown fields fail closed;
- the generated tier uses only non-issuable bridge fixtures and no socket,
  provider, credential, case identifier, narrative, person, media, or real data.

The first P4.5 implementation may define and statically validate this contract
only if the later start package includes it. It may not connect to a case
system, implement legal case workflow, import/export case data, or assert legal
status. Real activation requires separate legal/policy, data, integration,
secret, destination, runtime, and deployment authorization.

## D-P4.5-002: Closed Timeline Semantics

Option A is selected as written. Source, event, hypothesis, alert, operator
observation, review, action record, correction, retraction, disposition, merge,
reopen, retention, hold, deletion, and export families use discriminated closed
schemas. A generic free-form event cannot substitute for an authoritative
entry.

An action entry records an action reported as having occurred elsewhere; it is
not authority for H-CAM to execute that action. Facts, operator observations,
hypotheses, reviews, and actions remain distinguishable in storage and UI
contracts.

## D-P4.5-003: Reference Identity And Independent Integrity State

Option A is selected as written. Evidence identity binds an immutable source
system/object/version reference and named content/profile identity. Resolution,
digest verification, availability, provenance completeness, preservation,
signature/timestamp, and legal assessment remain independent append-only
states.

A matching digest means only that the observed bytes matched the expected
digest under the named algorithm/profile at the recorded assessment. It does
not establish source authenticity, custody, completeness, admissibility,
certification, or identity. Source media and documents remain external by
default.

## D-P4.5-004: H-CAM Provenance With Guarded C Capability

Option A is authoritative. H-CAM owns a bounded graph of immutable entities,
producing/using activities, accountable agents, and closed typed relations.
Same-department, uniqueness, allowed-endpoint, ordering, cycle, depth, fanout,
size, and traversal constraints are H-CAM policy and remain mandatory.

### Guarded C capability: `ProvInterchangeProjectionV1`

The architecture may define a derived interchange projection for a documented
subset of W3C PROV concepts:

- entity, activity, and agent;
- used, wasGeneratedBy, wasDerivedFrom, wasAttributedTo, wasAssociatedWith,
  actedOnBehalfOf, wasInformedBy, wasRevisionOf, hadPrimarySource,
  wasInvalidatedBy, and wasQuotedFrom;
- H-CAM roles, bundles, contract/profile versions, and unmapped domain edges.

The projection must be deterministic, versioned, immutable, purpose-bound, and
linked to the exact H-CAM bundle digest. Unsupported or lossy mappings remain
explicit. The H-CAM graph remains authoritative; importing a PROV bundle cannot
create or mutate an investigation record.

The initial generated tier may include:

- a closed mapping table and versioned projection contract;
- deterministic generated projection fixtures;
- static/canonicalization/round-trip-within-supported-subset tests;
- explicit `conformance_state: not_claimed` and `import_enabled: false`.

It may not include an external PROV bundle, dynamic RDF/JSON-LD/XML/PROV-N
parser, network vocabulary resolution, formal conformance-suite execution, or
a conformance claim. Full native PROV support remains a future separately
scoped capability requiring profile selection, implementation, independent
validation, and exact owner acceptance.

## D-P4.5-005: Corrections And Retractions

Option A is selected as written. A correction or retraction creates a new
immutable entity and typed relation to an exact target version. A bounded
deterministic impact set drives idempotent propagation to hypotheses, alerts,
timelines, reviews, search projections, and export manifests.

Pending, partial, blocked, failed, and complete propagation are visible. A
correction never edits the target or hides what a reviewer previously knew or
did.

## D-P4.5-006: Review, Disposition, Merge, And Reopen

Option A is selected as written. Review, lifecycle, disposition, confidence,
integrity, and evidence completeness are orthogonal. Mutations require exact
role, department, purpose, reason, policy, expected revision, idempotency, audit,
and transactional outbox.

Merge creates immutable relationships and a canonical alias while retaining
every source timeline and sequence. Reopen creates a new aggregate revision and
does not erase prior close/disposition, release a hold, or revoke an export.

## D-P4.5-007: Retention And Hold Overlay

Option A is selected as written. Retention uses immutable organization-owned
policy references and does not hard-code a period. A hold is a separately
authorized, attributable, bounded overlay affecting deletion eligibility only.
It never grants access or changes evidence meaning.

The generated tier may simulate proposed and evaluated states but cannot select
a legal period, activate/release a hold, or perform disposition.

## D-P4.5-008: Honest Deletion Evidence

Option A is selected as written. Deletion uses exact per-target intents and
receipts with policy/hold snapshot, authority, method class, executor, outcome,
verification, exception, and known backup/cache/export residuals.

Every receipt states `universal_deletion_proven: false`. Generated P4.5 may
simulate outcomes only and cannot access or delete storage.

## D-P4.5-009: Reference-Only Export First

Option A is selected as written. The canonical export is an immutable,
purpose/recipient-bound reference manifest with exact versions,
inclusion/exclusion reasons, corrections, contradictions, integrity states,
producer activity/agent, canonical digest, and visible completeness.

Source payloads are denied in the initial profile. Signature, trusted timestamp,
BagIt payload, long-term evidence-record, delivery, and recipient-receipt
profiles remain separate future gates.

## D-P4.5-010: PostgreSQL, RLS, And Generated Validation

Option A is selected as written. Additive append-only stores use restrictive
relationships, semantic/delivery idempotency, optimistic concurrency,
application scope checks, forced PostgreSQL row security, transactional outbox,
bounded workers, no-store APIs, and low-cardinality telemetry.

Generated fixtures are deterministic and non-issuable. They include no real
names, persons, vehicles, case identifiers, Government/private records,
locators, credentials, paths, URLs, media, documents, model output, or
operational commands.

## Reconciled Architecture

```text
Case-neutral H-CAM timeline (authoritative)
    -> immutable typed entries + dual chronology
    -> immutable evidence-reference versions
       -> independent integrity/availability/provenance assessments
    -> H-CAM entity/activity/agent provenance graph (authoritative)
       -> derived disabled PROV interchange projection
    -> correction/retraction impact closure
    -> review + disposition + non-destructive merge/reopen
    -> retention-policy references + separate hold overlays
    -> simulated deletion intents/receipts + residual state
    -> purpose-bound reference-only export manifests
    -> disabled typed case-management bridge
```

## Initial Generated Tier

The first separately authorized implementation should include the canonical A
profile and may include source-only/generated contracts and tests for the two
guarded capabilities. Both capability surfaces remain disabled and powerless:

- `CaseManagementBridgeContract`: no external case system, case data, legal
  workflow, credential, or network;
- `ProvInterchangeProjectionV1`: generated projection only, no external import,
  dynamic parser, vocabulary lookup, conformance suite, or conformance claim.

No guarded capability can weaken append-only history, department/purpose
authorization, evidence-state separation, reference-only handling, retention
policy, hold independence, deletion honesty, or export minimization.

## Remaining Gate

The ten owner decisions are complete for planning. The non-effective,
digest-bound `P4.5-PLANNING-R1` package is prepared for exact owner acceptance.
The owner must separately accept its exact SHA-256 before a non-effective
`P4.5-START-R0` package may be prepared. Implementation cannot begin until that
later start package is also accepted exactly.
