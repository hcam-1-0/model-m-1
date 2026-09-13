# P4.5 Investigation Timeline And Evidence Implementation Plan

Status date: 2026-09-05

Status: non-effective implementation design. Owner decisions, reconciled
planning acceptance, and a separate exact start authorization are pending.

## Objective

Extend the accepted P4.0 generated-only timeline placeholders into a
deployment-oriented but still generated-only investigation chronology and
evidence-reference subsystem. Prove immutable history, reference integrity,
typed provenance, deterministic correction propagation, review/disposition,
non-destructive merge/reopen, policy-bound retention and holds, simulated
deletion evidence, and reference-only export manifests without real evidence,
media, investigations, legal decisions, operational actions, or deployment.

## Frozen P4.5 Weight

P4.5 retains the accepted Phase 4 weight of 15 points:

| Item | Points | Completion rule |
| --- | ---: | --- |
| P4.5-A | 4 | Typed append-only timeline, V1 compatibility, multi-clock chronology, immutable revisions, idempotent commands, and reconstruction pass |
| P4.5-B | 4 | Evidence references, integrity assessments, provenance/derivation graph, correction/retraction closure, and source-without-copying guards pass |
| P4.5-C | 3 | Review, disposition, non-destructive merge, reopen, correction propagation, audit, and outbox workflows pass |
| P4.5-D | 2 | Policy-reference retention, separate hold overlays, simulated deletion evidence, and purpose-bound reference-only export manifests pass |
| P4.5-E | 2 | Reproducible generated-only evidence, PostgreSQL/security validation, limitations, and exact owner acceptance are recorded |

No partial item receives credit. Planning earns zero implementation points.
Current P4.5 is **0/15 (0.0000%)** and Phase 4 remains **70/100 (70.00%)**.

Technical completion before owner acceptance can reach P4.5 13/15
(86.6667%) and Phase 4 83/100 (83.00%). Exact validation/evidence completion
adds one P4.5-E point, reaching 14/15 (93.3333%) and Phase 4 84/100 (84.00%).
Exact owner acceptance adds the final point, reaching P4.5 15/15 (100.0000%)
and Phase 4 85/100 (85.00%).

## Non-Negotiable Boundary

The first implementation tier is:

- generated-only and non-issuable;
- reference-only, with no source fetch or media/document copy;
- default-off and production-forbidden;
- no legal/admissibility/custody/authenticity conclusion;
- no hard-coded retention period or hold/deletion/export authority;
- no real hold activation, deletion, export delivery, or source verification;
- no real investigations, providers, credentials, private/Government data,
  cameras, media, models, inference, actions, containers, Kubernetes,
  deployment, or remote Git unless separately authorized.

## Proposed Delivery Sequence

### W1: V2 Contracts And Deterministic Fixtures

Implement closed V2 contracts for timeline aggregates/revisions/entries,
temporal assertions, evidence references/integrity assessments, provenance,
reviews, corrections/retractions, impact sets, relationships, reconstruction,
retention/hold evaluation, deletion receipts, and export manifests.

Generate deterministic scenarios including:

- ordered, delayed, missing-time, skewed, and backdated entries;
- supporting, contradicting, stale, missing, unavailable, mismatch, and
  unverifiable evidence;
- multi-input derivation, revisions, delegated agents, and partial provenance;
- duplicate commands, delivery retries, correction chains, merge/reopen,
  overlapping holds, deletion residuals, and incomplete exports;
- hostile unknown fields, oversized/deep graphs, prohibited content, URLs,
  paths, credentials, media bytes, personal identifiers, and operational verbs.

Required evidence:

- strict unknown-field, value, size, count, depth, fanout, chronology, ID,
  version, and digest bounds;
- fixed-seed byte-for-byte regeneration and cross-process canonical digests;
- recursive prohibited-input guard and non-issuable namespace proof;
- no fixture copied from an external source or real person/investigation.

### W2: Persistence, Migration, And V1 Compatibility

Add a future migration after `0016_reference_integrations`. Preserve accepted
V1 tables and rows while adding the V2 stores in the contract catalog. Replace
or neutralize destructive timeline-parent cascade behavior for authoritative V2
history. Register all new tables with database reset/test infrastructure.

Required evidence:

- upgrade from accepted head, downgrade/upgrade cycle, and clean install;
- deterministic V1-to-V2 read projection without stronger integrity claims;
- unique sequence/revision/semantic/delivery identities and restrictive FKs;
- application department checks plus forced PostgreSQL RLS on every scoped
  table; runtime role cannot own tables, bypass RLS, or be superuser;
- SQLite remains an explicit single-writer development boundary;
- no update/delete product permission on immutable rows.

### W3: Timeline Command Kernel And Reconstruction

Implement a pure policy/command kernel and bounded persistence service for:

- create timeline, append entry, lifecycle change, and disposition revision;
- monotonic sequence assignment under concurrent writers;
- semantic/delivery idempotency and conflict detection;
- dual event-time/record-sequence views;
- reconstruct at exact aggregate revision or trusted record-time cutoff;
- show later-known corrections/retractions as a separate overlay;
- report missing, denied, partial, unavailable, and inconsistent closure.

Aggregate revision, immutable entry, audit action, and outbox event commit in one
transaction. Import, startup, and read paths produce no worker or network side
effects.

### W4: Evidence Registry, Integrity, And Provenance

Implement reference registration without resolution/fetch, append-only
simulated integrity assessments, typed entity/activity/agent graph, and bounded
provenance queries.

Required evidence:

- locator cannot become identity and cannot carry a URL/path/credential in the
  generated tier;
- integrity state is separate from authenticity, custody, availability,
  provenance completeness, and legal status;
- graph enforces same department, exact versions, unique IDs, allowed relation
  endpoints, causal constraints, cycle policy, and resource bounds;
- algorithm and canonicalization profile are explicit with no silent fallback;
- corrections create new entities and links; source bytes are never stored.

### W5: Correction, Retraction, Review, Merge, And Reopen

Implement append-only commands and durable impact jobs:

- record correction/retraction against an exact target version;
- calculate bounded deterministic impact closure;
- revise affected hypotheses, alerts, timeline projections, searches, reviews,
  and export manifests idempotently;
- report pending/partial/blocked/failed/complete propagation;
- add attributable review and disposition revisions;
- merge through relationships/canonical aliases without deletion;
- reopen by explicit revision without erasing prior close/disposition.

Workers use PostgreSQL `FOR UPDATE SKIP LOCKED`, leases, deadlines, bounded
retries, abandoned-work recovery, dead letters, and per-timeline serialization.
Policy, authorization, integrity, schema, scope, and graph failures do not retry.

### W6: Retention, Hold, Deletion, And Export Simulation

Implement contracts and generated simulation only:

- resolve immutable retention policy references and produce advisory
  evaluations with no built-in duration;
- model proposed/active/released/expired/superseded hold revisions while keeping
  hold authority and access independent;
- dry-run exact deletion intents and produce generated per-target receipts with
  residual-state reporting and `universal_deletion_proven: false`;
- prepare reference-only export previews/manifests with purpose, recipient
  class, policy, source closure, inclusion/exclusion reasons, corrections,
  contradictions, integrity states, and canonical digest;
- leave signature, trusted timestamp, BagIt payload, ERS, delivery, real hold,
  and real deletion adapters absent/default-denied.

Required evidence:

- missing policy, policy conflict, active hold, unknown dependency, stale
  authorization, and classification excess stop closed;
- hold never adds read permission and merge cannot evade a hold;
- deletion simulation never accesses storage or source references;
- export excludes source bytes, URLs, paths, credentials, personal identifiers,
  case narratives, and unauthorized fields;
- incomplete or unresolved closure remains visible and cannot be labeled
  complete/certified.

### W7: APIs, Observability, Security, And Evidence

Add bounded generated-only API surfaces and control-plane health:

- department, role, purpose, reason, and ETag enforcement;
- no-store responses for investigation/evidence reads;
- pagination and bounded graph/reconstruction/export closure;
- low-cardinality metrics for commands, conflicts, entries, graph outcomes,
  correction lag, impact backlog, integrity states, retention/hold outcomes,
  deletion simulations, and export outcomes;
- traces with sanitized operation IDs and no source/user/timeline/evidence IDs
  as metric labels;
- separate audit/security/operational/investigation/evidence data classes;
- transactional outbox, replay, recovery, and duplicate-delivery validation.

Seal generated fixtures, source/contracts, migrations, OpenAPI, focused/full
test results, coverage, PostgreSQL results, package artifacts, dependency lock,
known limitations, and exact changed paths in a reproducible evidence package.

## Proposed Permissions

Exact names are subject to owner selection and start-package reconciliation:

- `investigation.viewer`, `investigation.editor`, `investigation.reviewer`;
- `evidence.reference.viewer`, `evidence.reference.registrar`;
- `evidence.integrity.viewer`, `evidence.integrity.assessor`;
- `evidence.provenance.viewer`;
- `investigation.correction.editor`, `investigation.merge.editor`;
- `records.retention.viewer`, `records.retention.evaluator`;
- `records.hold.viewer`, with mutation permissions absent in generated Tier A;
- `records.deletion.viewer`, with execution permission absent;
- `evidence.export.viewer`, `evidence.export.preparer`, with delivery absent.

Administrator status alone does not imply evidence, hold, deletion, or export
authority. Production role mapping remains a deployment policy decision.

## Access Matrix Baseline

| Operation | Viewer | Editor | Reviewer | Records role | Export preparer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Read scoped timeline | Yes | Yes | Yes | Purpose-bound | Purpose-bound |
| Append generated entry | No | Yes | No | No | No |
| Review/disposition | No | No | Yes | No | No |
| Correct/retract | No | Explicit | Explicit | No | No |
| Merge/reopen | No | Explicit | Explicit | No | No |
| Retention evaluation | No | No | No | Yes | No |
| Hold mutation | No | No | No | Absent in Tier A | No |
| Deletion execution | No | No | No | Absent in Tier A | No |
| Prepare reference manifest | No | No | Purpose-bound | Purpose-bound | Yes |
| Deliver export/source payload | No | No | No | No | Absent in Tier A |

Every `Yes` still requires department, purpose, classification, policy, and
record-level authorization.

## Test Matrix

### Contract And Canonicalization

- unknown/missing fields, invalid versions/IDs/enums, duplicate JSON keys;
- NaN/infinity, invalid Unicode, ordering, number/string canonicalization;
- digest/profile mismatch, algorithm unknown/deprecated, canonical drift;
- prohibited nested payload fields and output redaction.

### Timeline And Concurrency

- duplicate/redelivered/conflicting commands, sequence races, optimistic lock;
- late and out-of-order events, clock skew, unknown/interval time;
- exact-revision and record-time reconstruction, pagination stability;
- V1 read compatibility and migration cycle.

### Evidence And Provenance

- source replacement, unavailable/denied reference, mismatch/unverifiable;
- multi-input derivation, missing agent/activity, cross-scope edge;
- cycle, orphan, duplicate, invalid endpoint type, depth/fanout/size exhaustion;
- partial and inconsistent graph closure.

### Workflow And Propagation

- correction/retraction chains and conflict cycles;
- every downstream target class, partial worker failure, retry and recovery;
- review supersession, disposition conflict, merge cycle/chain, reopen race;
- alert/hypothesis historical behavior remains unchanged.

### Retention, Hold, Deletion, And Export

- missing/expired/conflicting policy, no hard-coded period;
- overlapping holds, hold release revision, hold/access independence;
- hold-versus-deletion race, exact target closure, residual copies;
- incomplete/contradictory export, unauthorized field/recipient/purpose,
  canonical manifest stability, signature/timestamp/payload profiles denied.

### Security And Operations

- API RBAC, department RLS, purpose/reason/ETag, no-store;
- direct SQL cross-department attempts and privileged-role preflight;
- malformed/oversized requests, enumeration resistance, bounded errors;
- audit/outbox atomicity, retry idempotency, dead-letter and lease recovery;
- metric/log/trace cardinality and sensitive-value scans;
- startup/import causes no runtime, source, network, storage, or worker action.

## Acceptance Evidence

P4.5 technical evidence must include:

- exact contract/openapi/migration/fixture digests and generator identity;
- clean focused tests with at least 90% branch coverage for new P4.5 modules;
- unconditional repository suite with no hidden deselection;
- PostgreSQL migration, forced-RLS, direct isolation, concurrent-writer, worker,
  and correction-propagation evidence;
- SQLite single-writer limitation evidence;
- clean Ruff, compile, build, lock consistency, dependency compatibility, and
  vulnerability review under whatever later scope authorizes them;
- deterministic reconstruction and export-manifest rerun digests;
- proof that generated fixtures contain no prohibited/issuable source data;
- explicit absence of source fetch, media copy, legal conclusions, real hold,
  real deletion, export delivery, runtime integration, and deployment;
- changed-path manifest and immutable P4.0-P4.4 predecessor verification;
- separate exact owner acceptance for P4.5-E completion.

## Stop Conditions

Stop closed if any implementation would require:

- a real source, provider, camera, media object, case, person, vehicle, private
  or Government record;
- a retention period, legal conclusion, admissibility/certification decision,
  hold activation/release, real deletion, source copy, or export delivery;
- credentials, certificates, keys, timestamp authority, network, external
  workflow engine, model, dataset, container, Kubernetes, deployment, or remote
  Git action not explicitly authorized;
- modifying an accepted P4.0-P4.4 artifact instead of an exact reviewed
  compatibility transition;
- weakening department isolation, append-only history, purpose checks,
  no-source-copy behavior, or generated-only guardrails.

## Required Authorization Sequence

1. Owner selects `D-P4.5-001` through `D-P4.5-010`.
2. Selections are reconciled into non-effective `P4.5-PLANNING-R1`.
3. Owner accepts the exact reconciled package digest.
4. A bounded generated-only `P4.5-START-R0` package is prepared.
5. Owner separately accepts the exact start-package digest.
6. Only then may implementation begin within that exact scope.

Any real-data, source-resolution, integrity verification, retention-policy,
hold, deletion, export-delivery, cryptographic-signing/timestamp, or deployment
work requires a later separate authority even after generated P4.5 acceptance.
