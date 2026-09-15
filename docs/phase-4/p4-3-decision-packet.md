# P4.3 Alert Lifecycle And Orchestration Decision Packet

Status date: 2026-09-04

Status: owner decisions recorded and reconciled for planning. The selections
are not implementation authorization. See
[P4.3 owner decisions](p4-3-owner-decisions.md).

## How To Decide

The original options remain below as the decision audit. The owner selected the
reconciled composite profile `A / A / A+B / A / A+C+D / A+C / A+C`.

## D-P4.3-001: Proposed-Alert Identity And Deduplication

### A. Semantic identity plus delivery idempotency (recommended)

Create a deterministic semantic occurrence key from department, immutable rule
compilation/version, output code, accepted scope, partition/grouping context,
and stable P4.2 occurrence material. Store a separate delivery key for each
source evaluation revision. Derive the alert ID from the semantic key. Use
database uniqueness and transactional receipts to make replay and concurrent
delivery converge on one aggregate.

Benefits: prevents both transport duplicates and domain duplicates; supports
correction without destructive rewrite; deterministic across process restarts.
Cost: requires explicit canonical identity contracts and collision tests.

### B. Delivery event identity only

Deduplicate only by the P4.2 evaluation/revision ID. Simple, but semantically
equivalent events generated through another replay or correction path could
create multiple alerts.

### C. Time-window fingerprint only

Hash rule, subject, and a coarse time bucket. Easy to aggregate, but boundary
conditions can merge distinct incidents or split one incident. Clock and
window changes weaken replay stability.

### D. Probabilistic similarity deduplication

Use similarity scoring to decide whether an alert already exists. Flexible,
but nondeterministic, difficult to audit, and inappropriate as the canonical
identity mechanism. It could later be an advisory merge suggestion only.

## D-P4.3-002: Lifecycle And Workflow Shape

### A. Orthogonal aggregate with a small lifecycle state machine (recommended)

Use lifecycle states `proposed`, `acknowledged`, `under_review`, `confirmed`,
`dismissed`, `resolved`, and `closed`. Store assignment, suppression,
escalation, merge, correction/retraction, and review decisions as separate
append-only dimensions. Reopen returns an attributable terminal record to
`under_review` without deleting history.

Benefits: clear transition invariants; avoids state explosion; each workflow
dimension can evolve independently; accurate audit reconstruction. Cost: read
projections must combine several typed records.

### B. One comprehensive status enum

Encode states such as assigned, suppressed, escalated, merged, corrected, and
reopened directly in one enum. Simple list filtering, but combinations become
ambiguous and transitions grow combinatorially.

### C. Event log without a canonical aggregate projection

Treat all workflow changes as events and rebuild on every read. Flexible, but
adds operational and migration complexity before H-CAM has an event-store
platform and makes optimistic concurrency harder to communicate.

### D. Ticket-style mutable row

Update one alert row and keep only generic audit text. Fastest to build, but
cannot satisfy immutable reasoning, correction, evidence, or deterministic
reconstruction requirements.

## D-P4.3-003: Authority-Class Runtime Boundary

### A. Mandatory-review runtime only; other classes represented and denied (recommended)

P4.3 implements generated-only `mandatory_review` alerts. Contracts may name
`bounded_automation` and `future_autonomous_action`, but every runtime and API
attempt to use them fails closed. This proves authority separation without
activating a more permissive lane.

### B. Add generated system-health bounded automation now

Also implement auto-route, duplicate suppression, and auto-resolution for
generated machine-health records. This is compatible with the accepted P4.0
concept, but broadens P4.3 state/action testing and creates a second domain.

### C. Implement a general authority-policy interpreter

Use one configurable interpreter for all classes. Flexible, but configuration
errors could create silent escalation and the current milestone has no approved
operational policy source.

### D. Implement all authority classes including future autonomous action

Rejected for the baseline. It would conflict with accepted planning, require a
separate legal/safety/operational program, and create an enforcement path.

## D-P4.3-004: Alert Budgets And Incident Collapse

### A. Hierarchical budgets plus loss-accounted deterministic collapse (recommended)

Apply per-rule, department, review-queue, and system generated-lab budgets.
Over-budget occurrences are explicitly linked to a canonical incident group or
recorded as suppressed. Preserve counts, first/last time, representative
evidence, omitted-evidence digest, policy version, and reason. Never drop
silently.

### B. Fixed queue capacity with reject-new behavior

Operationally simple, but loses semantic continuity and can hide a sustained
incident unless rejection records are themselves durably accounted.

### C. Priority queue with drop-oldest behavior

Keeps newer work visible but destroys evidence and is prohibited for the
canonical record.

### D. No budgets during P4.3

Simpler implementation, but allows one rule or department to exhaust queue and
storage resources; it fails the accepted Phase 4 overload requirement.

## D-P4.3-005: Timers, SLA, And Escalation Execution

### A. Database-backed timer intents and bounded workers (recommended)

Persist policy/version-bound due instants, deterministic IDs, state, leases,
attempts, and outcomes. Use PostgreSQL queue claiming only for due work. Timers
may append SLA-breach/escalation-routing events but cannot change factual
disposition or invoke external actions. SQLite remains single-worker test only.

### B. In-memory scheduler

Low complexity and low latency, but loses timers on restart and cannot prove
replay/recovery.

### C. External workflow engine

Strong timer and workflow features, but adds an unapproved dependency and
deployment platform before P4.6/P4.7.

### D. Hybrid database truth plus external executor

Potential future scale path. It preserves database truth but adds two
coordination systems now. It should be an adapter boundary, not the P4.3
baseline implementation.

## D-P4.3-006: Review Decisions And Corrections

### A. Append-only attributable decisions with immutable evidence binding (recommended)

Each decision binds actor, role, department, reason, policy version, expected
aggregate version, evidence-set digest, source revision, timestamps, and
resulting lifecycle/disposition. A correction appends a new revision and may
reopen; it never edits a past decision. Confirmation is a workflow disposition,
not proof of identity, guilt, threat, or authority to act.

### B. Mutable current decision plus audit log

Easy current-state reads, but the generic log may not be sufficient to prove
which evidence and policy supported each decision.

### C. Multi-reviewer quorum for every disposition

Adds separation of duties but can make routine triage unusable. Quorum may be a
future policy option for specifically approved high-impact workflows.

### D. Single-click decision without reason

Fast, but conflicts with accepted actor/reason/audit requirements and weakens
accountability.

## D-P4.3-007: Validation And Runtime Envelope

### A. Full generated-only, default-off, production-forbidden lifecycle harness (recommended)

Implement deterministic generated fixtures, local API/service tests, SQLite
single-worker tests, and optional pre-existing PostgreSQL/PostGIS validation.
No camera/media, real/private/Government data, notification provider, network
egress, dispatch, enforcement, container startup, Kubernetes, or deployment.
No public endpoint starts a persistent worker.

### B. Generated simulation plus synthetic notification sink

Adds a local no-network sink to test notification formatting. Useful later,
but belongs to P4.4/P4.6 and broadens the P4.3 boundary.

### C. Connect to the Sentinel lab

Would mix the isolated Phase 2.5 compatibility lab with the canonical Phase 4
intelligence lifecycle and is outside the accepted main-platform boundary.

### D. Begin operational pilot data validation

Rejected. It requires separate data authority, privacy, legal, retention,
security, operator, and deployment approval.

## Recommended Composite Profile

```text
D-P4.3-001: A
D-P4.3-002: A
D-P4.3-003: A
D-P4.3-004: A
D-P4.3-005: A
D-P4.3-006: A
D-P4.3-007: A
```

The original recommended profile was the highest-integrity minimal route. The
owner instead selected the extended composite profile recorded in
[the owner decision record](p4-3-owner-decisions.md). Its additional
system-health automation, workflow-adapter, quorum, and Sentinel-lab metadata
capabilities are constrained by that record. Selection authorizes planning
reconciliation only; a separate digest-bound `D-P4.3-START` statement remains
required before implementation.
