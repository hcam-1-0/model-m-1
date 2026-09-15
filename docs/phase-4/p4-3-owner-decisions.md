# P4.3 Owner Decisions And Reconciliation

Status date: 2026-09-04

Status: effective for P4.3 planning reconciliation only. These selections do
not authorize implementation, runtime execution, external integration,
Sentinel access, cameras/media, operational alerts, deployment, or remote Git.

## Recorded Selection

```text
D-P4.3-001: A
D-P4.3-002: A
D-P4.3-003: A+B
D-P4.3-004: A
D-P4.3-005: A+C+D
D-P4.3-006: A+C
D-P4.3-007: A+C
```

The owner's phrases "also try to add" and "and also" are recorded as requests
to include the named capability in the architecture and bounded generated test
surface. They are not permission to activate an external system, camera/media
path, operational data path, or deployment.

## D-P4.3-001: Semantic Identity Plus Delivery Idempotency

Option A is selected as written. P4.3 will plan separate delivery and semantic
keys, deterministic alert identity, canonical-material drift detection,
department-scoped uniqueness, transactional command receipts, correction
revisions, and at-least-once/concurrency convergence.

## D-P4.3-002: Orthogonal Alert Aggregate

Option A is selected as written. The core lifecycle remains small while
assignment, suppression, escalation, merge, correction, review, budgets, and
timers remain separately typed and append-only. No workflow dimension silently
changes severity, confidence, disposition, or authority.

## D-P4.3-003: Mandatory Review Plus Bounded System-Health Automation

Options A and B are combined under strict domain separation:

- police-intelligence alerts always use `mandatory_review`;
- a generated-only `bounded_automation` lane may be implemented for synthetic
  system-health records only;
- that lane may auto-route, suppress duplicates, or resolve a synthetic
  machine-health condition within an immutable policy;
- it cannot accept police-intelligence records or establish identity, threat,
  guilt, intent, or an enforcement decision;
- it cannot notify an external provider, dispatch, control a device, or execute
  a physical action;
- authority class is immutable and cannot be inferred from severity, priority,
  rule output, queue, timer, or configuration;
- `future_autonomous_action` remains absent or hard-denied.

Generated cross-class negative tests must prove that data cannot be relabeled
or inherited into the more permissive lane.

## D-P4.3-004: Hierarchical Budgets And Loss-Accounted Collapse

Option A is selected as written. Per-rule, department, queue, and generated-lab
budgets produce only explicit route, collapse, or recorded-suppression outcomes.
Counts, time range, representative evidence, omitted-evidence digest, policy,
and reason remain reconstructable. Silent drop and automatic confirmation are
prohibited.

## D-P4.3-005: Database Truth With Pluggable Workflow Execution

Options A, C, and D are combined as a staged architecture:

1. PostgreSQL timer intents, policy versions, aggregate versions, leases,
   attempts, idempotency keys, and terminal outcomes are authoritative.
2. The P4.3 baseline includes a bounded node-local executor and generated
   executor simulator.
3. A typed `WorkflowExecutionAdapter` boundary is included for future external
   workflow engines.
4. A future hybrid deployment may use an external executor only to claim and
   execute authorized timer work while PostgreSQL remains the business source
   of truth.
5. No external workflow-engine dependency, service, credential, network call,
   installation, container, or deployment is included in P4.3.
6. Any future adapter must pass compatibility, idempotency, lease, replay,
   outage, revocation, and authority-denial tests under separate authorization.

This preserves the scalable C/D design without replacing the durable A
baseline or broadening current authority.

## D-P4.3-006: Append-Only Decisions With Configurable Quorum

Options A and C are combined through a policy overlay:

- append-only attributable evidence-bound decisions remain canonical;
- ordinary generated mandatory-review workflows default to one authorized
  reviewer;
- an immutable `ReviewQuorumPolicy` may require two or more distinct authorized
  reviewers for a generated high-impact workflow;
- a reviewer cannot satisfy multiple quorum slots, approve their own policy
  exception, or reuse a stale evidence/policy/aggregate version;
- disagreement, abstention, timeout, reassignment, policy change, and correction
  remain visible outcomes;
- quorum completion changes only the configured workflow disposition;
- no quorum result establishes identity, guilt, threat, legal fact, dispatch,
  or enforcement authority.

This adds quorum capability without forcing every routine disposition through
multiple reviewers or creating an unavailable-reviewer deadlock.

## D-P4.3-007: Generated Harness Plus Isolated Sentinel-Lab Compatibility

Options A and C are combined without coupling the canonical platform to the
Phase 2.5 lab:

- P4.3 remains generated-only, default-off, and production-forbidden;
- the main P4.3 service has no Sentinel URL, camera protocol, stream, media,
  credential, or network client;
- a typed `LabEvaluationIngressAdapter` may accept only sanitized structured
  metadata envelopes exported by the separately owned Phase 2.5 lab;
- generated contract fixtures and an in-process fake prove compatibility in
  P4.3;
- the adapter must convert an envelope into the same P4.2 evaluation-revision
  contract used by canonical P4.3 input; it cannot bypass P4.2 validation;
- main-platform code never imports the lab implementation and the lab never
  becomes a runtime dependency;
- direct Sentinel access, real website interaction, cameras, streams, images,
  recordings, private/Government data, and network validation require a
  separate explicit lab authorization and are not included in P4.3 start.

## Reconciled Architecture Profile

The selected architecture is:

```text
P4.2 evaluation revision
    -> canonical P4.3 proposal and lifecycle
       -> mandatory-review police-intelligence lane
       -> isolated generated system-health bounded-automation lane

PostgreSQL timer and policy truth
    -> bounded local executor
    -> generated external-executor simulator
    -> future default-off WorkflowExecutionAdapter

Append-only review decisions
    -> single-review default
    -> configurable distinct-reviewer quorum overlay

Separate Phase 2.5 lab
    -> sanitized metadata export boundary
    -> LabEvaluationIngressAdapter
    -> normal P4.2 contract validation
    -> no direct P4.3 Sentinel/media dependency
```

## Remaining Gate

The seven owner decisions are complete for planning. The next artifact is one
non-effective, digest-bound `P4.3-START-R0` package reconciled to this exact
profile. No implementation begins unless the owner separately accepts that
exact package as `D-P4.3-START`.
