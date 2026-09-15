# P4.5 Investigation Timeline And Evidence Decision Packet

Status date: 2026-09-05

Status: options prepared; no P4.5 owner selections, reconciled planning
acceptance, or implementation authority are recorded. Recommendations are not
decisions. `Continue`, silence, or a partial answer selects nothing.

## Decision Method

Answer every decision by ID and option. Multiple options may be selected only
where the choice explicitly says they are compatible. Any custom combination
must be reconciled into a new non-effective planning package before start
authorization can be prepared.

The recommended profile is `A/A/A/A/A/A/A/A/A/A`. It maximizes auditability,
reconstruction, evidence integrity, privacy, and future enterprise capability
while keeping the first implementation generated-only, reference-only,
default-off, non-operational, and unable to delete or export real data.

## D-P4.5-001: Timeline Aggregate And Ordering

### A. Case-neutral aggregate with dual event-time and record-sequence views

Use a department-scoped timeline aggregate with monotonic sequence and immutable
revisions. Preserve source occurrence/observation time separately from trusted
receive/record time. Expose both views and explicit unknown/skew states.

Benefits: reconstructable even with delayed or untrusted clocks; compatible
with P4.0; does not force H-CAM to become a legal case-management system.

Risks: operators must understand that event order and record order can differ.

**Recommended.**

### B. Sort all entries only by source event time

Benefits: simple visual timeline.

Risks: source clock skew, correction, backdating, missing time, and late arrival
can reorder history and invent causality. Not recommended.

### C. Sort only by database insertion sequence

Benefits: deterministic and easy to audit.

Risks: loses operational event chronology and makes delayed observations hard
to interpret.

### D. Adopt a full legal case aggregate now

Benefits: one system for investigation and formal case management.

Risks: introduces unapproved legal workflow, data, terminology, retention, and
integration scope. Outside P4.5 baseline.

## D-P4.5-002: Timeline Entry Semantics

### A. Closed typed families with discriminated payloads and causal links

Use source, event, hypothesis, alert, operator observation, review, action
record, correction, retraction, disposition, merge, reopen, retention, hold,
deletion, and export families. Each has a strict schema and exact immutable
source versions.

Benefits: prevents fact/inference/action confusion, enables safe UI rendering,
and supports deterministic reconstruction and policy.

Risks: more contracts and migrations; new types require versioned releases.

**Recommended.**

### B. Keep the five P4.0 entry types unchanged

Benefits: smallest implementation.

Risks: cannot faithfully distinguish event, alert, action, retraction, merge,
reopen, hold, deletion, or export chronology.

### C. One generic event type with free-form JSON

Benefits: maximum flexibility.

Risks: semantic drift, hidden data, weak validation, unsafe UI assumptions, and
poor reconstruction. Prohibited for authoritative history.

### D. Event-sourcing framework owns all H-CAM state

Benefits: unified history model.

Risks: broad platform rewrite and coupling beyond P4.5. Not justified now.

## D-P4.5-003: Evidence Identity And Integrity

### A. Immutable reference envelope plus append-only multi-state assessments

Identity binds source system/object/version, digest algorithm/value, size and
profile when known. Resolution, integrity verification, provenance completeness,
availability, and preservation states remain independent. Media stays external
by default.

Benefits: prevents a hash from becoming a false authenticity claim; preserves
history when a source changes or becomes unavailable; supports algorithm agility.

Risks: more explicit unknown/partial states and verifier records.

**Recommended.**

### B. Digest and URL only

Benefits: simple and familiar.

Risks: URL is mutable; digest lacks source/version/profile/context; authenticity,
availability, custody, and admissibility can be misrepresented.

### C. Copy every source object into H-CAM evidence storage

Benefits: local availability and simpler verification.

Risks: duplicates media/private data, expands custody and retention obligations,
and violates the reference-without-copying baseline.

### D. Trust the upstream source without local assessment

Benefits: minimal storage and compute.

Risks: substitution, drift, unavailable evidence, and unverifiable exports.

## D-P4.5-004: Provenance And Derivation Graph

### A. W3C PROV-inspired typed entity/activity/agent graph with H-CAM constraints

Use immutable versioned nodes and closed typed edges, plus same-department,
uniqueness, causal, cycle, depth, fanout, and traversal bounds. Maintain a PROV
mapping but make no conformance claim.

Benefits: expressive provenance, attributable derivation, future interchange,
and correction/export closure without a new graph database.

Risks: graph validation and bounded traversal are non-trivial.

**Recommended.**

### B. Flat `source_ref` fields on every record

Benefits: simple queries.

Risks: cannot represent multi-input derivation, activity, agent, correction,
delegation, contradiction, or export lineage.

### C. Full native PROV implementation and conformance now

Benefits: maximum standards fidelity.

Risks: larger scope, serialization/interchange obligations, and H-CAM domain
relations still need extensions. Premature.

### D. Dedicated graph database

Benefits: natural traversal and visualization.

Risks: new operational store, consistency boundary, backup/security system, and
deployment complexity. PostgreSQL is sufficient for bounded P4.5 graphs.

## D-P4.5-005: Correction, Retraction, And Propagation

### A. Append correction/retraction entities plus durable impact closure

Never mutate the target. Compute a bounded deterministic affected set and create
idempotent jobs for hypotheses, alerts, timelines, search projections, reviews,
and export manifests. Expose pending, partial, blocked, failed, and complete.

Benefits: preserves what was known and relied on; makes stale downstream state
visible; supports replay and accountability.

Risks: workers and impact-state reconciliation add complexity.

**Recommended.**

### B. Update the incorrect record in place and add an audit line

Benefits: simple current view.

Risks: original decision bytes and derivation disappear; audit cannot reliably
reconstruct every affected projection. Not acceptable.

### C. Append correction but update projections opportunistically

Benefits: less worker infrastructure.

Risks: silent partial propagation and inconsistent operator/export views.

### D. Recompute all intelligence globally after every correction

Benefits: conceptually complete.

Risks: unbounded, resource-heavy, and unnecessary; unrelated state may change.

## D-P4.5-006: Review, Disposition, Merge, And Reopen Workflow

### A. Orthogonal versioned workflows with non-destructive merge aliases

Keep lifecycle, disposition, review, confidence, integrity, and evidence
completeness separate. Require ETags, exact permissions, purpose, reason, policy,
and atomic revision/outbox. Merge creates relationships and canonical aliases;
reopen appends a new revision.

Benefits: accurate semantics, concurrency safety, reversible projections, and
full history.

Risks: more UI states and conflict handling.

**Recommended.**

### B. One status enum for everything

Benefits: small schema.

Risks: `closed`, `confirmed`, `verified`, `held`, and `exported` become falsely
interchangeable.

### C. Physically merge rows and delete the source timeline

Benefits: simple current list.

Risks: destroys identity, sequence, access, retention, and provenance history.

### D. Never allow merge or reopen

Benefits: smallest risk surface.

Risks: real investigation correction and duplicate-work workflows cannot be
represented; operators create informal workarounds.

## D-P4.5-007: Retention Classes And Hold Overlays

### A. Immutable policy references plus separately authorized scoped holds

Every record has a data/record class and immutable policy version. Policies own
triggers, schedules, review, and eligible actions. Holds are separate versioned
overlays that affect deletion eligibility only and never grant access. P4.5
ships no real periods and activates no holds.

Benefits: policy change is traceable; no legal period is hidden in code; hold
conflicts and over-retention are visible.

Risks: requires an organizational policy source and approval workflow later.

**Recommended.**

### B. Hard-code periods by table

Benefits: fast implementation.

Risks: legal/policy drift, mixed record classes, untraceable change, and unsafe
deletion. Prohibited.

### C. Retain everything indefinitely

Benefits: no accidental deletion.

Risks: privacy, security, cost, policy, and discovery exposure; not a neutral
default.

### D. Let operators choose dates per record

Benefits: flexible.

Risks: inconsistent, unauthorized, and unauditable policy decisions.

## D-P4.5-008: Deletion Evidence And Residual State

### A. Per-target deletion intent and receipt with explicit residuals

Record exact policy/hold snapshot, authority, target versions/storage classes,
method class, executor, outcome, verification, exceptions, known residuals, and
corrections. Use `universal_deletion_proven: false`. First tier is simulation
only and cannot delete.

Benefits: honest, reconstructable execution evidence; handles backups, caches,
exports, and unsupported targets without false claims.

Risks: requires storage adapters and policy integration before real execution.

**Recommended.**

### B. Store only `deleted_at`

Benefits: tiny schema.

Risks: no target, authority, method, outcome, verification, or residual detail.

### C. Cryptographic erasure claim based only on key deletion

Benefits: potentially fast for correctly designed encrypted stores.

Risks: key copies, plaintext caches, exports, backups, and external sources may
remain. Must be a method class with evidence, never a universal claim.

### D. Physically remove every lifecycle record

Benefits: minimal retained metadata.

Risks: destroys accountability and may conflict with required destruction
records. Exact retained tombstone content requires policy, not a blanket rule.

## D-P4.5-009: Export Packaging And Integrity

### A. Reference-only canonical manifest first; optional gated payload profiles

Create a purpose/recipient-bound immutable JSON manifest with exact versions,
inclusion/exclusion ledger, corrections, contradictions, integrity states,
canonical digest, and optional empty signature/timestamp/BagIt/ERS slots. Source
payload copying remains denied unless a later profile is separately authorized.

Benefits: minimizes data, supports deterministic review, and preserves an
upgrade path for signed, timestamped, BagIt, or long-term records.

Risks: a reference-only package depends on authorized source availability at
the receiving side.

**Recommended.**

### B. Always create a BagIt package containing all source files

Benefits: portable self-contained transfer.

Risks: copies media/private data, increases disclosure and custody, and requires
real export authority. Not baseline.

### C. Export a PDF report only

Benefits: easy human reading.

Risks: loses machine-verifiable lineage and precise source versions; a PDF can
be an optional rendering, not the authoritative manifest.

### D. Direct database dump

Benefits: complete internal state.

Risks: exposes unrelated departments, credentials, internal schemas, and excess
data; lacks purpose minimization. Prohibited.

## D-P4.5-010: Persistence, APIs, And Generated Validation

### A. Bounded PostgreSQL/RLS append-only stores plus transactional outbox

Use additive V2 stores, restrictive foreign keys, immutable revisions,
idempotent commands, forced row security, bounded workers, no-store APIs,
purpose-bound reads, and low-cardinality telemetry. Validate with deterministic
non-issuable generated fixtures; keep deletion/export execution default-off and
production-forbidden.

Benefits: matches accepted H-CAM architecture, supports concurrency and
reconstruction, and creates deployment-quality contracts without real data.

Risks: broad test/migration effort and PostgreSQL evidence requirement.

**Recommended.**

### B. Reuse the two P4.0 tables without additive stores

Benefits: small migration.

Risks: cannot model graph, integrity assessments, revisions, impacts, holds,
deletion receipts, or export versions safely.

### C. Store immutable JSON files in object storage only

Benefits: append-friendly and cheap.

Risks: weak transactional relationships, department query isolation,
concurrency, and correction closure.

### D. Add a distributed ledger/blockchain

Benefits: shared tamper-evidence in some multi-party designs.

Risks: does not establish source truth, authorization, privacy, custody, or
admissibility; adds governance, deletion, key, and operational complexity.
Not justified for P4.5.

## Recommended Owner Response

The complete recommended selection is:

```text
D-P4.5-001: A
D-P4.5-002: A
D-P4.5-003: A
D-P4.5-004: A
D-P4.5-005: A
D-P4.5-006: A
D-P4.5-007: A
D-P4.5-008: A
D-P4.5-009: A
D-P4.5-010: A
```

After all selections are recorded, they must be reconciled into a new
`P4.5-PLANNING-R1` package. That package still cannot authorize implementation.
