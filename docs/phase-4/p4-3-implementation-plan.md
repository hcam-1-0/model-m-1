# P4.3 Alert Lifecycle And Orchestration Implementation Plan

Status date: 2026-09-04

Planning status: research and composite owner decisions reconciled. An exact
digest-bound P4.3 start authorization remains pending. This plan is
non-effective and authorizes no implementation or runtime action.

## 1. Objective

P4.3 will transactionally create at most one generated, non-operational,
mandatory-review proposed alert from an accepted P4.2 matched evaluation
revision. It will then provide deterministic, attributable lifecycle,
assignment, suppression, escalation, merge, correction, review, budget, timer,
and recovery behavior.

P4.3 is an internal alert-review workflow foundation. It is not a notification,
dispatch, enforcement, external-integration, camera/media, model, dataset,
operational pilot, or deployment milestone.

The selected extended profile also prepares a generated-only system-health
automation lane, a future workflow-executor adapter, configurable review quorum,
and an isolated sanitized Sentinel-lab metadata ingress contract. These are
bounded architecture/test capabilities, not real integrations or operational
authority.

## 2. Frozen Progress Boundary

The accepted Phase 4 work breakdown assigns 15 of 100 Phase 4 points to P4.3:

| Work item | Points | Completion rule |
| --- | ---: | --- |
| P4.3-A: deterministic proposed-alert creation and deduplication | 4 | At-least-once replay, semantic equivalence, correction, collision, rollback, and PostgreSQL concurrency evidence all pass |
| P4.3-B: full alert lifecycle and optimistic concurrency | 5 | Transition matrix, independent workflow dimensions, actor/reason/ETag/RBAC/audit/outbox, merge, correction, and reconstruction tests all pass |
| P4.3-C: routing, authority, suppression, escalation, SLA, and overload policy | 4 | Mandatory-review baseline, denied authority escalation, budgets, incident collapse, timers, leases, recovery, and overload tests all pass |
| P4.3-D: evidence and owner acceptance | 2 | Exact reproducible evidence, lifecycle recovery drill, and separate owner acceptance all pass |

Current accepted progress remains **40/100 Phase 4 points (40.00%)** and
**0/15 P4.3 points (0.0000%)**. Planning earns no frozen points. Technical
completion can earn at most 13/15 P4.3 points, raising Phase 4 to 53/100. Exact
P4.3 owner acceptance adds the final 2 points, producing 15/15 P4.3 and 55/100
Phase 4.

## 3. Decision Gate

The owner selected all seven decisions:

- `D-P4.3-001`: proposed-alert identity and deduplication;
- `D-P4.3-002`: lifecycle and workflow shape;
- `D-P4.3-003`: authority-class runtime boundary;
- `D-P4.3-004`: alert budgets and incident collapse;
- `D-P4.3-005`: timers, SLA, and escalation execution;
- `D-P4.3-006`: review decisions and corrections;
- `D-P4.3-007`: validation and runtime envelope.

The selected profile is `A / A / A+B / A / A+C+D / A+C / A+C`, reconciled in
[P4.3 owner decisions](p4-3-owner-decisions.md). A separate
`P4.3-START-R0` package must bind its paths, inputs, limits, tests, stop
conditions, and digest. Implementation begins only after exact
`D-P4.3-START` acceptance.

## 4. Binding Inputs

P4.3 must preserve:

- accepted Phase 4 planning package `P4-PLANNING-R2`, SHA-256
  `B8F4371A8DDD350F44321E70F5FB8CEE0DD27299A26082A40460086E80DDEA63`;
- `D-P4.0-004:A+B+C`, `D-P4.0-007:A`, and `D-P4.0-008:A`;
- accepted P4.0 alert contracts, tables, forced-RLS boundaries, revision model,
  read-only API surface, and transactional outbox;
- accepted P4.1 generated event, hypothesis, correction, chronology,
  department-isolation, replay, and bounded persistence semantics;
- accepted P4.2 evidence package SHA-256
  `A10CEAF5742A59EA54373ED5494A99A73F94FCD9D268C20C5752D753805320CA`;
- accepted P4.2 canonical component digest
  `635642E579ECD712271E6F86E42F594BA912047E30DB95C716D212C81B83ACBC`;
- P4.2 immutable rule compilation, evaluation/revision identity, generated-only
  flags, evidence digests, partitioning, correction, replay, and typed
  `propose_review_candidate` output;
- current local accepted checkpoint commit
  `1e6673be5fc684f6607794b6e6b462f5905850a6`;
- no-store API responses, attributable audit, optimistic concurrency, forced
  PostgreSQL RLS, SQLite single-worker limitation, and production-denial
  controls.

## 5. Non-Goals And Prohibitions

P4.3 does not authorize or implement:

- cameras, ONVIF, Sentinel, streams, frames, images, recordings, playback, or
  any media access;
- model, dataset, checkpoint, artifact, inference, training, accelerator, or
  benchmark activity;
- real, private, personal, biometric, vehicle-owner, case, watchlist,
  Government, police, or operational data;
- rule activation, active camera analytics, operational alerts, or production
  background startup;
- email, SMS, push, webhook, radio, CAD, provider, dispatch, enforcement, or
  physical action;
- external credentials, network egress, provider destinations, or arbitrary
  configuration;
- a claim that human confirmation establishes identity, guilt, threat, legal
  fact, or enforcement authority;
- container startup, Kubernetes, cloud, production, deployment, release, or
  remote Git activity.

## 6. Target Architecture

```text
accepted P4.2 matched evaluation revision
    -> source/version/digest/authority revalidation
    -> delivery idempotency receipt
    -> canonical semantic occurrence identity
    -> hierarchical budget decision
       -> route normally
       -> loss-accounted incident collapse
       -> explicit suppression record
    -> one proposed alert aggregate
    -> append-only proposal/lifecycle revision
    -> audit record + transactional outbox

authorized human/API command
    -> department + RBAC + reason + If-Match
    -> transition/policy/evidence validation
    -> aggregate projection update
    -> append-only workflow records
    -> audit record + timer changes + transactional outbox

bounded timer worker
    -> ordered due-row lease claim
    -> aggregate/policy/version revalidation
    -> SLA breach or escalation request only
    -> append-only event + audit + outbox

generated system-health record
    -> immutable system_health domain validation
    -> bounded_automation policy
    -> route, duplicate suppression, or synthetic health resolution only

separate Phase 2.5 lab
    -> sanitized metadata envelope
    -> generated/default-off LabEvaluationIngressAdapter
    -> normal P4.2 contract and digest validation

PostgreSQL timer truth
    -> bounded local executor
    -> generated external-executor simulator
    -> future default-off WorkflowExecutionAdapter
```

## 7. Identity And Concurrency

The recommended implementation uses:

- delivery key: exact source plus P4.2 evaluation revision identity;
- semantic key: canonical department/rule/output/scope/partition/grouping/
  occurrence identity independent of delivery mechanics;
- deterministic alert ID derived from a versioned namespace and semantic key;
- a canonical-material digest stored beside the key to detect impossible hash
  collisions or canonicalizer drift;
- unique department-scoped constraints for delivery receipts and semantic keys;
- optimistic aggregate version for every user mutation;
- append-only revision sequence and command-idempotency uniqueness;
- one transaction for aggregate, revisions, decisions, audit, budgets/timers,
  and outbox rows.

At-least-once replay must return the prior receipt. Concurrent semantically
equivalent commands must converge on one alert. A same-key/different-material
case fails closed and raises a sanitized integrity signal.

## 8. Lifecycle And Orthogonal Workflow

The proposed lifecycle states are `proposed`, `acknowledged`, `under_review`,
`confirmed`, `dismissed`, `resolved`, and `closed`. The exact transition matrix
is in the contract catalog.

Independent records represent:

- assignment and queue transfer;
- explicit suppression and expiry;
- escalation level, target, and SLA breach;
- review decisions and overrides;
- merge/canonical-incident relationships;
- source/evidence correction, supersession, and retraction;
- timer intents and budget decisions.

Priority, severity, confidence, chronology confidence, disposition, and
authority class remain separate. No score or timer can create a human
disposition. Reopen appends a transition and requires a reason, policy, actor,
expected version, and evidence/source binding.

## 9. Authority And Routing

The selected P4.3 profile accepts `mandatory_review` for generated police-
intelligence alerts and a separately typed `bounded_automation` class only for
synthetic `system_health` records. Authority/domain are immutable and no input,
rule, queue, severity, priority, timer, or configuration may reclassify one lane
as the other. `future_autonomous_action` remains a hard-denied value.

Routing policy may choose a generated review queue, assignment suggestion,
priority, suppression record, incident-collapse target, SLA deadline, or
escalation request. It cannot:

- confirm or dismiss an alert;
- establish identity, guilt, threat, or legal fact;
- contact an external provider;
- send a notification or dispatch request;
- command a camera, vehicle, device, or person;
- invoke arbitrary code or network access.

The system-health lane is limited to generated route, duplicate suppression,
and synthetic health resolution. It has no police-intelligence input, human-
subject field, provider, notification, dispatch, enforcement, or device-control
capability.

## 10. Budgets And Incident Collapse

Immutable policies define bounded windows for rule-version, department,
review-queue, and system-lab scopes. Evaluation order and tie-breaking are
canonical. Each candidate produces exactly one append-only budget outcome:

- `route` creates or updates its semantic alert normally;
- `collapse` links occurrence accounting to one deterministic canonical group;
- `suppress_recorded` creates a visible suppression/budget record.

All outcomes preserve occurrence count, first/last occurrence time,
representative evidence references, full evidence-set or omitted-evidence
digest, policy version, and safe reason. Budget exhaustion never confirms,
dismisses, drops, or deletes an alert.

## 11. Durable Timers And Recovery

Timers are versioned database intents. The worker wakes by wall clock but must
revalidate stored event-time basis, due instant, aggregate version, lifecycle,
authority, and policy before acting. Allowed effects are bounded reminder,
`sla_breached`, or `escalation_requested` records.

PostgreSQL workers claim an ordered queue with `FOR UPDATE SKIP LOCKED`, bounded
leases, attempts, and recovery. SQLite remains one worker and cannot satisfy
multi-worker evidence. Expired leases become reclaimable; stale timers are
durable no-ops with reason codes. No timer produces an external side effect.

PostgreSQL remains authoritative under every executor mode. P4.3 includes a
bounded local executor, a generated external-executor simulator, and a typed
future `WorkflowExecutionAdapter`. No real workflow engine, dependency,
credential, endpoint, network call, container, or deployment is included.

## 12. Work Packages

### P4.3-W1: Decision reconciliation and exact start package

The owner selections and bounded composite interpretation are recorded.
Reconcile the contract catalog, implementation plan, threat model,
migration/API outline, path allowlist, limits, and test gates. Seal
`P4.3-START-R0`; obtain separate exact `D-P4.3-START` acceptance.

### P4.3-W2: Historical verification transition

Preserve all accepted P4.0-P4.2 artifacts and package digests. Add a
hash-bound historical verifier transition so P4.2 readiness is evaluated from
its accepted technical commit/evidence while the current schema head advances.
No historical artifact may be rewritten.

### P4.3-W3: Contracts and generated fixtures

Implement strict proposal, V2 aggregate/lifecycle, assignment, suppression,
escalation, review, merge, correction, timer, budget, command-receipt, outbox,
quorum, system-health automation, workflow-adapter, lab-ingress, and RFC 9457
problem contracts. Add deterministic positive, negative, metamorphic,
collision, replay, correction, overload, cross-lane, adapter, and abuse
fixtures.

### P4.3-W4: Proposal and identity service

Implement P4.2 revision revalidation, canonical occurrence material, semantic
and delivery keys, deterministic alert IDs, idempotent command receipts,
same-key/different-material denial, and at-least-once replay behavior. Keep the
service internal; add no public create-alert endpoint.

### P4.3-W5: Lifecycle and review service

Implement the selected transition matrix, orthogonal workflow records, human
review decisions, correction/reopen, merge-cycle prevention, RBAC, department
scope, reason, ETag, audit, and transactional outbox. Preserve independent
severity, priority, confidence, chronology confidence, and disposition.
Implement the single-review default plus bounded distinct-reviewer quorum
policy, append-only votes, disagreement/timeout outcomes, and stale-evidence
denial.

### P4.3-W6: Budgets, routing, and suppression

Implement immutable policy versions, hierarchical counters, deterministic
incident grouping/collapse, explicit suppression, priority/routing decisions,
no-drop accounting, and safe observability. All actions remain generated-only
and internal.
Add the separately typed generated system-health policy lane and prove that no
police-intelligence record can enter or inherit its bounded automation.

### P4.3-W7: Timer intents and bounded worker

Implement timer persistence, due-row claims, leases, retries, stale checks,
SLA/escalation events, crash recovery, and worker metrics. The harness/worker
must be default-off, production-forbidden, explicit-start only, and incapable of
external action.
Add a typed workflow-executor port and generated simulator while keeping
PostgreSQL authoritative and all real external adapters absent.

### P4.3-W8: Persistence, migration, and row security

Add migration `0015_alert_lifecycle_orchestration` only after exact start
authorization. Evolve the accepted alert foundation additively; add workflow,
receipt, budget, timer, merge, and revision stores. Apply department foreign
keys/checks, application filters, forced PostgreSQL RLS, aggregate versioning,
unique idempotency constraints, and outbox atomicity. Preserve downgrade/
upgrade compatibility and Phase 3/P4.0-P4.2 historical verification.

### P4.3-W9: API and observability

Extend read APIs and add lifecycle/workflow commands with no-store responses,
ETags, mandatory reasons, bounded pagination, typed problem responses, and
low-cardinality metrics. Add no create-alert, activate-rule, provider,
notification, dispatch, enforcement, or arbitrary-worker-start route.
Add an internal generated-only `LabEvaluationIngressAdapter` and fake for
sanitized Phase 2.5 metadata envelopes. Do not add a public lab route, direct
Sentinel client, camera/media field, network path, or lab implementation import.

### P4.3-W10: Validation, evidence, and acceptance

Run focused and generated tests, branch coverage, full regression, Ruff,
compile checks, clean fixture regeneration, migration cycles, PostgreSQL RLS/
concurrency/lease/recovery drills, SQLite restrictions, package builds,
dependency/SBOM/license/vulnerability checks, historical readiness, and clean
source validation. Seal one exact evidence package for separate P4.3 owner
acceptance.

## 13. Planned Persistence

| Store | Purpose | Principal controls |
| --- | --- | --- |
| `alerts` | Current bounded V2 projection | department semantic-key uniqueness, versioning, mandatory review, generated/non-operational checks |
| `alert_revisions` | Immutable lifecycle snapshots | alert/revision uniqueness, actor/reason/policy/evidence binding |
| `alert_command_receipts` | Delivery and command idempotency | department/source/key uniqueness, content-drift denial |
| `alert_review_decisions` | Human dispositions and overrides | append-only actor/role/reason/evidence/policy binding |
| `alert_review_quorum_policies` | Optional bounded reviewer requirements | immutable version, distinct actors, one-review default |
| `alert_review_quorum_votes` | Append-only reviewer votes | department/role/evidence/version binding, duplicate denial |
| `alert_assignment_events` | Queue/assignee changes | append-only same-department targets |
| `alert_suppression_events` | Explicit suppression history | reason, policy, scope, expiry, occurrence accounting |
| `alert_escalation_events` | SLA/routing escalation | independent of confidence/disposition/authority |
| `alert_merge_relations` | Source-to-canonical relationships | no deletion, same department, no cycles |
| `alert_correction_revisions` | Source/evidence correction | immutable prior/new digests and reopen policy |
| `alert_budget_policies` | Immutable bounded policies | versioned scopes, no drop action |
| `alert_budget_decisions` | Per-occurrence accounting | counts, times, representative evidence, omitted digest |
| `alert_timer_intents` | Durable reminders/SLA intents | versions, due time, lease, bounded attempts, stale no-op |
| `alert_workflow_execution_receipts` | Local/simulated executor idempotency | PostgreSQL truth, capability/version/lease binding |
| `system_health_automation_policies` | Generated health-only automation | immutable domain/class, bounded actions, cross-lane denial |
| `stream_event_outbox` | Transactional publication | stable event identity, retry-safe publication |

## 14. Planned API Behavior

All mutation routes require:

- authenticated department scope;
- an authorized lifecycle role;
- `If-Match` with the current alert version;
- `X-HCAM-Reason` and bounded structured command body;
- a unique idempotency key;
- current policy and evidence/source revalidation;
- immutable audit and transactional outbox records.

Success returns the new ETag and bounded projection. A repeated successful
command returns its prior receipt without reapplying. Stale version returns a
typed conflict. Cross-department access remains indistinguishable from absence
according to the existing authorization policy.

## 15. Validation Matrix

- contracts: unknown fields, invalid enums, oversized reasons/evidence,
  duplicate JSON keys, non-finite values, prohibited content, and version drift;
- identity: delivery replay, semantic equivalence, distinct occurrences,
  correction, canonicalizer version, collision sentinel, concurrent creation,
  rollback, and restart;
- lifecycle: every allowed and denied edge, independent workflow dimensions,
  reopen, terminal handling, ETags, idempotency, actor/role/reason, policy,
  evidence binding, and reconstruction;
- quorum: one-review default, distinct actors, role/department checks,
  disagreement, timeout, correction, stale evidence/policy/version, duplicate
  vote, and no self-satisfaction of multiple slots;
- authority: class mutation, system-health relabeling, timer disposition,
  automatic confirmation, provider/notification/dispatch/enforcement reachability,
  startup side effects, and production-denial negatives;
- budget: all scope levels, exact boundaries, deterministic order, collapse,
  suppression, counts, evidence digests, no drop, and overload recovery;
- timer: early/late due, stale aggregate/policy, duplicate claim, concurrent
  PostgreSQL workers, expired lease, crash recovery, attempt bound, and SQLite
  multi-worker denial;
- workflow adapter: local/simulated equivalence, capability denial,
  idempotency, stale lease, outage, revocation, split-brain, and PostgreSQL truth;
- lab compatibility: generated sanitized envelope, prohibited URL/credential/
  identifier/media/private/Government fields, P4.2 revalidation, adapter disabled,
  no network, and no canonical dependency on the Phase 2.5 lab;
- isolation: API and direct PostgreSQL cross-department read/write/merge/
  dedupe/worker negatives plus owner/superuser/`BYPASSRLS` safeguards;
- atomicity: rollback at every aggregate/revision/audit/timer/budget/outbox
  boundary; outbox redelivery without mutation replay;
- observability: low-cardinality labels, occurrence/observed time, bounded error
  codes, and no prohibited values in metrics/logs/traces/errors/headers;
- compatibility: Phase 3, P4.0, P4.1, P4.2, migration cycles, historical
  readiness, package builds, and full repository regression;
- evidence: at least 90% branch coverage for new P4.3 modules, clean generated
  fixture regeneration, exact digests, explicit PostgreSQL/runtime limitations,
  and separate owner acceptance.

## 16. Delivery Sequence

1. Owner selections are recorded and reconciled.
2. Seal a non-effective exact start package.
3. Owner accepts exact `D-P4.3-START` package digest.
4. Implement W2 historical verification transition.
5. Implement contracts/fixtures, proposal identity, lifecycle, and quorum core.
6. Implement budgets/routing/suppression, generated system-health policy, timer
   worker, workflow port/simulator, and generated lab-ingress fake.
7. Implement persistence/migration/RLS, APIs, and observability.
8. Run focused, PostgreSQL, security, compatibility, packaging, supply-chain,
   full-suite, and clean-source validation.
9. Seal exact evidence and request separate `D-P4.3-ACCEPTANCE`.

Routine local edits and generated validation may be batched only after the
exact start package is accepted and only inside its path/scope limits. Any
model/data/media, external connection, operational alert, notification,
dispatch, enforcement, container, Kubernetes, deployment, or remote Git scope
requires separate authorization and is not part of P4.3.
