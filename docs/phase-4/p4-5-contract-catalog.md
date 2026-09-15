# P4.5 Investigation Timeline And Evidence Contract Catalog

Status date: 2026-09-05

Status: non-effective contract design. Names and fields are proposed for owner
decision and later exact start authorization. No product contract is changed by
this document.

## Compatibility Position

The P4.0 `TimelineEntryV1`, `InvestigationTimeline`, `TimelineEntry`, list API,
and migration `0012_intelligence_control_plane` remain historical accepted
inputs. P4.5 proposes additive V2 contracts and a future migration after current
head `0016_reference_integrations`.

V1 rows remain readable through a deterministic legacy projection. New writes
use V2 after explicit authorization. No V1 field is reinterpreted to claim
stronger evidence, provenance, custody, or legal status than it originally
carried.

## Aggregate Model

### `InvestigationTimelineV2`

One case-neutral, department-scoped investigation workspace:

- `timeline_id`, contract version, department, classification, purpose policy;
- current aggregate revision and monotonic next sequence;
- lifecycle: `open`, `under_review`, `disposed`, or `closed`;
- separately recorded disposition: `undetermined`, `supported`, `not_supported`,
  `inconclusive`, `referred`, or a future policy-defined code;
- canonical timeline alias after merge without deleting source aggregates;
- owner/assignment references, created/updated chronology, and policy digest;
- `generated_only: true`, `operational: false`, `identity_state:
  not_established` in the first implementation tier.

Lifecycle, disposition, integrity, evidence completeness, and alert state are
orthogonal. Closing a timeline does not confirm a hypothesis, establish an
identity, release a hold, delete records, or authorize an export.

### `TimelineAggregateRevisionV1`

Append-only snapshot for each aggregate mutation:

- `revision_id`, timeline, revision number, predecessor revision;
- command semantic ID and delivery ID;
- previous and new lifecycle/disposition/alias values;
- actor/service agent, role, reason, purpose, policy, and transaction;
- canonical snapshot digest and recorded time.

### `TimelineEntryV2`

An immutable chronological assertion or activity record:

- `entry_id`, timeline, department, aggregate sequence, contract version;
- closed `entry_family` and discriminated typed payload;
- asserted occurrence chronology and trusted record chronology;
- zero or more typed evidence/provenance references;
- actor/service attribution, delegated role, reason, purpose, policy;
- semantic identity, predecessor/superseded/retracted links where applicable;
- canonical content digest and retention policy reference;
- visibility/completeness state without mutable content.

Entries are never updated or deleted through product APIs. A later entry changes
interpretation or lifecycle; it does not change prior bytes.

## Entry Families

The V2 closed taxonomy contains:

| Family | Meaning | Required payload identity |
| --- | --- | --- |
| `source` | Register or assess a source/evidence reference | evidence entity version |
| `event` | Record an accepted immutable event version | event ID and digest |
| `hypothesis` | Record creation, revision, expiry, or retraction | hypothesis and revision IDs |
| `alert` | Record proposed-alert and lifecycle revision | alert and revision IDs |
| `operator_observation` | Attributable human observation, explicitly not a source fact | observation ID |
| `review` | Attributable review decision or correction | review decision ID |
| `action_record` | Record an action that occurred elsewhere; never execute it | external action receipt/reference |
| `correction` | Correct a prior assertion with reason and impact scope | correction ID and target version |
| `retraction` | Withdraw reliance without deleting history | retraction ID and target version |
| `disposition` | Record timeline disposition revision | disposition revision ID |
| `merge` | Link timelines and select a canonical alias | merge activity ID |
| `reopen` | Reopen a closed/disposed timeline | reopen activity ID |
| `retention` | Record policy evaluation only | evaluation ID |
| `hold` | Record separately authorized hold lifecycle | hold ID and revision |
| `deletion` | Record deletion request/outcome/residual state | deletion job/receipt ID |
| `export` | Record manifest preparation/approval/outcome | export manifest/version ID |

Each family has a discriminated payload with `extra=forbid`. Generic free-form
event JSON is not an alternative entry contract.

## Chronology Contracts

### `TemporalAssertionV1`

- `source_occurred_at`: optional source-asserted time;
- `source_observed_at`: optional source-asserted observation time;
- `received_at`: trusted H-CAM ingress time;
- `recorded_at`: trusted durable transaction time;
- `effective_at`: time a review/correction/disposition is effective in H-CAM;
- `time_basis`: `source_clock`, `hcam_clock`, `operator_asserted`, or `unknown`;
- `precision`: `exact`, `millisecond`, `second`, `minute`, `interval`, or
  `unknown`;
- `clock_state`: `trusted`, `bounded_skew`, `untrusted`, or `unknown`;
- optional bounded interval and declared skew estimate.

The contract enforces known causal order such as receive no later than durable
record. It does not require an untrusted source occurrence to precede receive.
Views expose both event-time and record-sequence ordering.

### `CausalLinkV1`

Typed relation between exact immutable versions:

- `causes`, `responds_to`, `corrects`, `retracts`, `supersedes`, `reviews`,
  `merges`, `reopens`, `exports`, or `invalidates`;
- source and target version IDs;
- activity, agent, policy, transaction, and recorded chronology;
- same-department and graph-validity proof.

## Evidence Contracts

### `EvidenceReferenceV2`

An immutable reference envelope, not source content:

- `evidence_id` and immutable `evidence_version_id`;
- `source_system_ref`, `source_object_ref`, and optional source version token;
- source type from a closed registry;
- content/profile identity: digest algorithm, digest, byte length when known,
  media/document profile when known, and canonicalization profile if derived;
- reference role: `supports`, `contradicts`, `contextualizes`, `missing`,
  `stale`, `supersedes`, `retracts`, or `unavailable`;
- locator class and opaque resolver reference, never a credential-bearing URL;
- temporal assertion and provenance entity ID;
- data class, retention policy reference, purpose constraints, and owner system;
- `reference_only: true` in the first implementation tier.

The database never treats a locator as identity. A locator may resolve to a
different version and therefore create a new evidence version or mismatch
assessment.

### `EvidenceIntegrityAssessmentV1`

Append-only result of one bounded verification activity:

- expected identity and observed identity;
- resolution state: `not_attempted`, `resolved`, `unavailable`, `denied`, or
  `unknown`;
- verification state: `not_assessed`, `verified`, `mismatch`, or
  `unverifiable`;
- provenance completeness: `complete`, `partial`, `inconsistent`, `unknown`;
- verifier service/version, algorithm/profile, policy, activity, and time;
- bounded sanitized reason and no source content.

`verified` means the performed comparison matched under the named profile. It
does not mean authentic, admissible, complete, legally certified, or in custody.

### `EvidenceEntityV1`

Common immutable entity projection:

- entity identity/version/type and canonical digest;
- source or derived classification;
- creation/generation activity;
- attribution and policy;
- availability, invalidation, correction, and retention references;
- no mutable display label in the integrity identity.

## Provenance Contracts

### `ProvenanceNodeV2`

Closed kinds:

- `entity`: event, evidence version, hypothesis revision, alert revision,
  timeline entry, review, action receipt, correction, deletion receipt, or
  export manifest;
- `activity`: ingestion, validation, correlation, lookup, review, correction,
  retraction, merge, reconstruction, retention evaluation, hold transition,
  deletion, or export;
- `agent`: operator, H-CAM service/version, external organization reference, or
  generated fixture agent.

### `ProvenanceEdgeV2`

Closed relations inspired by W3C PROV:

- `used`, `generated`, `derived_from`, `attributed_to`, `associated_with`,
  `acted_on_behalf_of`, `informed_by`, `revision_of`, `primary_source_of`,
  `invalidated_by`, `quoted_from`, plus H-CAM-specific `supports`,
  `contradicts`, `corrects`, `retracts`, and `included_in_export`;
- exact source/target version, role, activity, chronology, department, policy,
  and edge digest.

### `ProvenanceBundleV1`

- bundle ID/version, root entity, purpose, department, policy;
- bounded nodes/edges and continuation cursor;
- closure mode: `direct`, `ancestors`, `descendants`, `correction_closure`, or
  `export_closure`;
- completeness: `complete`, `bounded`, `partial`, or `inconsistent`;
- canonical digest and generated time.

The first implementation does not claim W3C PROV validity or interchange
conformance. It maintains a documented mapping and H-CAM-specific constraints.

## Correction And Reconstruction Contracts

### `CorrectionCommandV1`

- exact target entity/version and asserted replacement or status;
- correction type: factual, chronology, attribution, classification,
  interpretation, link, or integrity assessment;
- actor, role, reason, purpose, authority, policy, ETag, semantic/delivery IDs;
- no mutation of the target.

### `CorrectionImpactSetV1`

Deterministic bounded closure over:

- hypotheses and hypothesis projections;
- alerts and lifecycle projections;
- timelines and entries;
- reviews/dispositions relying on the target;
- search/index projections;
- export manifests and reconstruction bundles.

Every target records `pending`, `revised`, `unaffected`, `blocked`, or `failed`
with a typed reason. Partial completion remains visible.

### `ReconstructionRequestV1` And `ReconstructionManifestV1`

Reconstruct one timeline at an exact aggregate revision or trusted record time:

- requested cutoff, purpose, actor, policy, and authorization;
- exact entries and entity versions visible at cutoff;
- later corrections/retractions optionally shown as a separate known-later
  layer, never folded silently into the historical view;
- missing, unavailable, unverifiable, bounded, and denied references;
- canonical manifest digest and reproducibility result.

## Review, Disposition, Merge, And Reopen

### `InvestigationReviewDecisionV1`

- exact target type/version;
- decision: `supported`, `not_supported`, `inconclusive`, `needs_more_evidence`,
  `abstain`, `correct`, or `retract`;
- actor/service, role, reason, purpose, policy, and chronology;
- source closure and contradiction acknowledgement;
- immutable supersession chain for corrections.

### `TimelineDispositionRevisionV1`

Disposition is append-only and does not mutate evidence or confirm identity. It
requires expected aggregate revision, role, reason, policy, purpose, and exact
review/evidence closure.

### `TimelineMergeV1`

- exact source timeline revisions and canonical target timeline;
- non-destructive aliases and relationship direction;
- deduplicated entry projections retain original timeline/sequence identity;
- conflict report for department, purpose, classification, retention, hold,
  access, or evidence mismatch;
- cycles, self-merge, cross-department merge, and destructive delete denied.

### `TimelineReopenV1`

- expected closed/disposed revision, new revision, actor, role, reason, policy;
- link to new information/correction when applicable;
- prior disposition remains visible; reopen does not release holds or undo an
  export.

## Retention And Hold Contracts

### `RetentionPolicyReferenceV1`

- immutable policy ID/version/digest and owner organization;
- data/record class, trigger type, jurisdiction/policy scope, effective range;
- schedule expression supplied by an authorized policy source;
- review requirement, action classes, and conflict behavior;
- no built-in P4.5 duration or legal conclusion.

### `RetentionEvaluationV1`

- target entity/version, class, policy version, trigger facts;
- evaluated at, eligible at when policy computes it, and next review;
- hold summary, dependency summary, outcome, and typed reason;
- `advisory_only: true` and `execution_authorized: false` in the generated tier.

### `HoldOverlayV1`

- hold ID/revision and exact target closure or policy-defined query snapshot;
- `proposed`, `active`, `released`, `expired`, or `superseded` lifecycle;
- authority reference, requester/approver roles, purpose, reason, policy;
- start, review, optional expiry, release, and correction chronology;
- impact limited to retention/disposition eligibility; no added read permission.

No hold activation/release is implemented under planning authorization.

## Deletion Evidence Contracts

### `DeletionIntentV1`

- exact target versions/storage classes, retention evaluation, hold snapshot;
- authority, actor, reason, purpose, policy, expected state, and dry-run plan;
- no wildcard path, raw SQL, arbitrary locator, or unknown storage target.

### `DeletionReceiptV1`

- intent and attempt IDs, executor identity/version, started/completed times;
- per-target method class and outcome: `deleted`, `already_absent`, `blocked`,
  `failed`, `not_supported`, or `residual_reported`;
- verification method/result, known backup/cache/export residuals, exceptions;
- prior receipt, correction/retraction, audit/outbox, and canonical digest;
- explicit `universal_deletion_proven: false`.

The generated tier simulates planning and outcomes only. It cannot delete data.

## Export Contracts

### `EvidenceExportRequestV1`

- purpose, recipient class, department, timeline/revision, requested profile;
- requested closure, field projection, classification ceiling, expiry;
- actor, role, reason, policy, authorization, semantic/delivery identity;
- `include_source_payloads: false` in the default profile.

### `EvidenceExportManifestV1`

- immutable export ID/version and request binding;
- exact timeline, entry, entity, evidence, review, correction, retraction,
  deletion, and provenance versions;
- deterministic inclusion/exclusion ledger with reason codes;
- integrity algorithm/canonicalization profile, per-item digests, root digest;
- completeness, unresolved contradiction, unavailable source, and residual
  state;
- producer agent/activity, generated time, policy, purpose, recipient class;
- optional empty slots for separately authorized signature, trusted timestamp,
  BagIt payload, and long-term evidence record profiles;
- `reference_only: true`, `contains_source_media: false`, and
  `legal_certification: none` in the first implementation.

An export preview, manifest approval, delivery, and recipient receipt are
separate append-only states. No P4.5 baseline directly sends an export.

## Command And Delivery Contracts

Every mutation command includes:

- department, purpose, actor/service and role;
- `X-HCAM-Reason` equivalent and policy/authorization references;
- expected aggregate revision or target content digest;
- semantic command identity and delivery identity;
- bounded request timestamp/deadline;
- generated-only and non-operational markers.

Receipts distinguish `accepted`, `duplicate`, `conflict`, `denied`, and
`invalid`. Same semantic ID with different canonical content is a conflict.

## Planned Persistence

The additive PostgreSQL design proposes:

| Store | Purpose |
| --- | --- |
| `investigation_timeline_revisions` | Append-only aggregate state history |
| `timeline_entries_v2` | Immutable discriminated chronology entries |
| `evidence_entities` | Immutable source/derived entity versions |
| `evidence_integrity_assessments` | Append-only verification outcomes |
| `provenance_nodes` | Typed entity/activity/agent versions |
| `provenance_edges` | Typed immutable relationships |
| `investigation_reviews` | Attributable review revisions |
| `correction_impacts` | Durable propagation closure and outcomes |
| `timeline_relationships` | Merge/alias/reopen relationships |
| `retention_evaluations` | Advisory policy evaluation history |
| `hold_overlays` | Separately controlled hold lifecycle |
| `deletion_intents` | Authorized or generated dry-run plans |
| `deletion_receipts` | Per-target outcome and residual evidence |
| `evidence_export_manifests` | Purpose-bound immutable export versions |
| existing audit log | Separate security/administrative accountability |
| existing outbox | Atomic domain-event publication |

All department-scoped stores require application authorization and forced
PostgreSQL row security. Runtime roles may not own tables, bypass RLS, or be
superusers. Timeline/evidence foreign keys use restrictive behavior; the current
V1 parent `ON DELETE CASCADE` must not become a deletion path.

## Planned API Families

- `GET/POST /investigation-timelines` for generated aggregate creation/read;
- `GET/POST /investigation-timelines/{id}/entries` for append-only V2 entries;
- `GET /investigation-timelines/{id}/revisions` and `/reconstruction`;
- `POST /investigation-timelines/{id}/reviews`, `/dispositions`, `/merge`, and
  `/reopen`;
- `GET/POST /evidence-references` for reference registration/read without fetch;
- `GET /evidence/{id}/provenance` and `/integrity-assessments`;
- `POST /corrections` and `GET /corrections/{id}/impacts`;
- retention evaluation, hold, deletion, and export endpoints in generated
  simulation mode only if separately included in the future start package.

Sensitive responses use `Cache-Control: no-store`. Reads require department,
role, and purpose. Mutations require reason and expected revision. Pagination,
graph closure, export item count, and reconstruction range are bounded.

## Domain Events

Proposed outbox events are versioned and sanitized:

- `hcam.investigation.timeline.created.v1`;
- `hcam.investigation.timeline.entry-appended.v1`;
- `hcam.investigation.timeline.lifecycle-changed.v1`;
- `hcam.investigation.timeline.merged.v1`;
- `hcam.investigation.timeline.reopened.v1`;
- `hcam.evidence.reference-registered.v1`;
- `hcam.evidence.integrity-assessed.v1`;
- `hcam.evidence.correction-recorded.v1`;
- `hcam.evidence.correction-propagated.v1`;
- `hcam.evidence.retention-evaluated.v1`;
- `hcam.evidence.hold-state-changed.v1`;
- `hcam.evidence.deletion-outcome-recorded.v1`;
- `hcam.evidence.export-manifest-created.v1`.

Events contain opaque IDs, versions, outcomes, and policy references, not media,
source bodies, locators, credentials, personal data, case narratives, or
unrestricted payloads.

## Bounds And Failure Rules

Future exact numeric limits must be sealed in the start package. The architecture
requires bounded entries per request, string/payload size, evidence references
per entry, nodes/edges/depth/fanout per graph, correction closure, merge depth,
reconstruction range, export items/bytes, worker lease, retry count, and query
page size.

Authorization, scope, policy, integrity mismatch, schema, digest conflict,
provenance inconsistency, hold conflict, and prohibited-content failures do not
retry. Transient persistence conflicts retry only through bounded idempotent
commands. Partial reconstruction and unavailable sources are typed results, not
silent success.

## Generated-Only Contract

Initial fixtures use deterministic non-issuable IDs, synthetic clock sequences,
empty source payloads, inert opaque resolver references, simulated integrity
outcomes, and generated agents. Recursive guards deny real identifiers, names,
plates, phone/email/address fields, credentials, URLs, paths, media bytes,
documents, model output, operational commands, dispatch, and enforcement.
