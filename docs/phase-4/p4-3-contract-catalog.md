# P4.3 Alert Lifecycle And Orchestration Contract Catalog

Status date: 2026-09-04

Status: owner-selected planning profile reconciled. Names and fields remain
non-effective until an exact start package is separately accepted.

## Contract Principles

1. Extend the accepted P4.0 alert foundation; do not rewrite or delete it.
2. Accept only immutable generated P4.2 rule-evaluation revisions through an
   internal service boundary.
3. Keep delivery idempotency separate from semantic alert deduplication.
4. Keep lifecycle, disposition, severity, priority, confidence, assignment,
   suppression, escalation, merge, and correction as distinct concepts.
5. Make every mutation department-scoped, attributable, reason-bound,
   optimistic-concurrency-protected, audited, and transactionally published.
6. Preserve generated-only and non-operational behavior. Police-intelligence
   remains mandatory-review; bounded automation is restricted to generated
   system-health records under a separate immutable domain/class invariant.
7. Deny notification, dispatch, enforcement, real external providers, and
   autonomous action at contract, service, persistence, configuration, and test
   layers.

## Accepted Inputs

### `hcam.p4-2.rule-evaluation.v1`

P4.3 may consume only a persisted P4.2 evaluation revision that satisfies all
of these conditions:

- `state == matched`;
- `generated_only == true`;
- `operational == false`;
- its immutable compilation, rule version, department, partition, evaluation
  digest, evidence references, and revision can be reverified;
- the source rule is approved for generated evaluation and is not suspended or
  retired;
- the output node is `propose_review_candidate` with type
  `review_candidate_nonoperational`;
- no correction/retraction supersedes the consumed revision at transaction
  time.

Pending, not-matched, suppressed, abstained, stale, unbound, or digest-drifted
evaluations cannot create a proposed alert. They produce a bounded denial or
no-op receipt.

## Planned Core Contracts

### `hcam.p4-3.proposed-alert-command.v1`

Internal command created from an accepted P4.2 evaluation revision.

Required semantic fields:

- command ID and delivery idempotency key;
- department and `mandatory_review` authority class;
- evaluation ID, revision, digest, compilation ID, rule logical ID/version,
  output code, scope digest, partition digest, grouping material digest, and
  stable occurrence key;
- proposed severity, priority, confidence, and retention class;
- bounded evidence references and complete evidence-set digest;
- generated/non-operational flags fixed to `true`/`false`;
- occurrence time and observed time;
- contract/policy/canonicalization versions.

The command contains no raw media, unrestricted event payload, free-form model
reasoning, provider credential, dispatch instruction, or enforcement action.

### `hcam.intelligence.alert.v2`

Additive successor to accepted `AlertAggregateV1`.

Planned fields:

- stable alert ID, semantic dedupe key, aggregate version, department;
- lifecycle state and independent review disposition;
- authority class fixed to `mandatory_review` in P4.3;
- severity, priority, confidence, chronology confidence, and retention class;
- canonical incident-group ID when collapsed or merged;
- current assignment, suppression, and escalation projection references;
- source evaluation/evidence revision counters and current digests;
- created, updated, last-transition, and optional closed timestamps;
- `operational=false` and `generated_only=true` invariants.

The aggregate stores current bounded projection state. Append-only records are
the reconstruction authority.

### `hcam.intelligence.alert-lifecycle-event.v2`

Append-only transition record containing:

- event ID, alert ID, department, transition ID, aggregate version;
- previous and new lifecycle state;
- previous and new disposition where applicable;
- actor ID, actor kind, role snapshot, reason code, bounded reason text;
- policy ID/version/digest and command idempotency key;
- source evaluation/evidence digest snapshot;
- occurrence and recording time;
- authority, generated-only, and non-operational invariants.

### `hcam.p4-3.alert-assignment-event.v1`

Records assignment, transfer, release, and queue changes without changing the
core lifecycle state. It binds prior/new queue and assignee references, actor,
reason, expected aggregate version, policy version, and timestamps. Assignment
does not imply acknowledgement, review, confirmation, or escalation.

### `hcam.p4-3.alert-suppression-event.v1`

Records explicit suppression state, scope, reason, start, optional expiry,
policy version, actor or bounded-system actor, occurrence count, representative
evidence references, and omitted-evidence digest. Suppression never deletes the
alert or changes its review disposition.

### `hcam.p4-3.alert-escalation-event.v1`

Records previous/new escalation level, routing target, trigger kind, SLA/timer
reference, actor, reason, policy version, and timestamps. Escalation may change
priority through a separately recorded policy decision. It cannot change
severity, confidence, disposition, authority class, or create an external
action.

### `hcam.p4-3.alert-review-decision.v1`

Records an attributable human decision:

- decision ID, alert ID, department, actor/role snapshot;
- decision type and resulting lifecycle/disposition;
- expected and resulting aggregate version;
- reason code and bounded reason text;
- exact evidence-set, source-revision, policy, and contract digests;
- override/exception indicators and required justification;
- occurrence and recording time.

Review decisions cannot assert person/vehicle identity, guilt, or enforcement
authority. Those are separate future governed records outside P4.3.

### `hcam.p4-3.review-quorum-policy.v1`

Immutable policy overlay containing policy/version/digest, department, exact
generated workflow class, decision types covered, required distinct reviewer
count, allowed roles, separation-of-duty rules, timeout, disagreement outcome,
correction behavior, and effective interval. The ordinary generated baseline
requires one reviewer. A high-impact generated policy may require a bounded
quorum. Universal or unbounded quorum is prohibited.

### `hcam.p4-3.review-quorum-vote.v1`

Append-only vote binding alert/aggregate version, policy version, reviewer and
role snapshot, decision, reason, evidence/source digests, occurrence time, and
recording time. The same actor cannot fill multiple slots. Stale, duplicate,
cross-department, unauthorized, or evidence-drifted votes fail closed. Quorum
completion appends a separate review decision; votes never mutate history.

### `hcam.p4-3.alert-merge-relation.v1`

Links a source alert to one canonical alert/incident group. It records actor,
reason, policy, expected versions, relationship revision, and source/canonical
evidence digests. The source alert remains readable and reconstructable. A
merge cannot cross departments and cannot delete lifecycle history.

### `hcam.p4-3.alert-correction-revision.v1`

Appends source correction, retraction, supersession, or evidence-set change.
It records prior/new source revisions, affected evaluation/evidence digests,
reason, actor/source, review-impact classification, and whether policy requires
reopen. It never mutates a prior lifecycle or review-decision record.

### `hcam.p4-3.alert-timer-intent.v1`

Durable bounded timer truth:

- timer ID and idempotency key;
- department, alert, aggregate version, timer kind, policy/version;
- event-time basis, due instant, state, lease, attempts, and terminal reason;
- generated/non-operational invariants.

Allowed timer kinds are bounded acknowledgement/review/SLA reminders and
escalation requests. No timer may confirm, dismiss, resolve, close, notify an
external provider, dispatch, or enforce.

### `hcam.p4-3.workflow-execution-adapter.v1`

Typed future-ready executor boundary containing adapter kind, contract version,
capability manifest, timer-intent identity, lease/version binding, request
digest, bounded outcome, and idempotency receipt. P4.3 includes only the local
executor and generated external-executor simulator. Real external adapters,
credentials, network destinations, dependencies, and deployment are absent.

The adapter can execute only already-authorized timer effects and cannot create
a new effect type, alter policy, decide disposition, or replace PostgreSQL
business truth.

### `hcam.p4-3.alert-budget-policy.v1`

Immutable generated policy containing bounded windows and limits for rule
version, department, review queue, and system-lab scopes. It defines explicit
actions `route`, `collapse`, or `suppress_recorded`; `drop` is not allowed.

### `hcam.p4-3.alert-budget-decision.v1`

Append-only result with policy/version, scope, counters before/after,
occurrence time range, action, canonical group reference, reason, representative
evidence references, omitted count/digest, and aggregate/outbox transaction
reference.

### `hcam.p4-3.alert-command-receipt.v1`

Idempotency record with command ID, source/delivery key, semantic key, outcome,
alert ID where created/reused, resulting version, safe reason code, and
timestamps. Repeated commands return the same bounded outcome without applying
the transition again.

### `hcam.p4-3.lab-evaluation-ingress.v1`

Optional isolated compatibility envelope for sanitized structured metadata
exported by a separately controlled Phase 2.5 lab. It contains contract
version, generated/sanitized declarations, source adapter profile, export ID,
P4.2-compatible evaluation payload digest, capture-free provenance, and bounded
safe fields. It cannot contain a URL, credential, frame, image, media segment,
plate/face/person value, owner record, private/Government data, or arbitrary
payload.

The adapter validates and projects the envelope into the normal P4.2 evaluation
revision boundary. It cannot create alerts directly or bypass P4.2 digest,
rule, department, evidence, and authority checks. P4.3 implements generated
fixtures and an in-process fake only; it does not import or contact the lab.

### `hcam.p4-3.system-health-automation-policy.v1`

Immutable generated-only policy for the separate `system_health` domain. It may
permit bounded route, duplicate suppression, or resolution of synthetic
machine-health records. Domain and authority are fixed at creation. The policy
cannot accept police-intelligence inputs, change authority class, contact an
external system, or produce an operational action.

## Lifecycle Matrix Proposal

The matrix is effective only if `D-P4.3-002:A` and `D-P4.3-006:A` are selected.

| From | Allowed human transition | To | Notes |
| --- | --- | --- | --- |
| none | propose | proposed | Internal generated command only; deterministic and idempotent |
| proposed | acknowledge | acknowledged | Records actor/reason; no factual disposition |
| proposed | begin review | under_review | Assignment may be separate |
| proposed | dismiss | dismissed | Attributable evidence-bound decision |
| acknowledged | begin review | under_review | No automatic confirmation |
| acknowledged | dismiss | dismissed | Attributable evidence-bound decision |
| under_review | confirm | confirmed | Workflow disposition only |
| under_review | dismiss | dismissed | Workflow disposition only |
| confirmed | resolve | resolved | Resolution reason required |
| dismissed | close | closed | Closure is administrative finalization |
| resolved | close | closed | Closure is administrative finalization |
| dismissed | reopen | under_review | New reason and aggregate version |
| resolved | reopen | under_review | New reason and aggregate version |
| closed | reopen | under_review | Policy/role gated; history retained |

All other transitions fail with a typed invalid-transition problem. Suppression,
assignment, escalation, merge, and correction are not lifecycle transitions.

## Optimistic Concurrency And Idempotency

- User/API mutations require `If-Match` for the current aggregate version and
  return a new ETag after commit.
- `X-HCAM-Reason` remains mandatory for every mutation.
- Command ID uniqueness prevents duplicate application of one request.
- Semantic-key uniqueness prevents duplicate proposed-alert creation.
- Aggregate versioning prevents lost updates.
- Append-only event sequence uniqueness prevents duplicate revisions.
- Aggregate, revisions, audit, timer/budget effects, and transactional outbox
  commit in one database transaction.
- An outbox redelivery can repeat publication but cannot repeat aggregate
  mutation.

## Planned API Surface

```text
GET  /alerts
GET  /alerts/{alert_id}
GET  /alerts/{alert_id}/history
GET  /alerts/{alert_id}/decisions
GET  /alerts/{alert_id}/routing
POST /alerts/{alert_id}/acknowledge
POST /alerts/{alert_id}/begin-review
POST /alerts/{alert_id}/confirm
POST /alerts/{alert_id}/dismiss
POST /alerts/{alert_id}/resolve
POST /alerts/{alert_id}/close
POST /alerts/{alert_id}/reopen
POST /alerts/{alert_id}/assign
POST /alerts/{alert_id}/suppress
POST /alerts/{alert_id}/unsuppress
POST /alerts/{alert_id}/escalate
POST /alerts/{alert_id}/merge
POST /alerts/{alert_id}/correct
GET  /alert-budget-policies
GET  /alert-timer-intents
```

There is no public create-alert route. Proposed-alert creation is an internal,
generated-only consumer path from accepted P4.2 evaluation revisions. No route
notifies, dispatches, enforces, contacts a provider, or activates a rule.

No public route accepts Sentinel or lab payloads. The optional lab compatibility
adapter is an internal generated harness boundary and remains disabled unless a
future separately authorized lab run supplies a sanitized envelope.

## Event Envelope

Transactional outbox events should use an H-CAM envelope compatible with the
identity principles of CloudEvents 1.0.2:

- stable `specversion`, `id`, `source`, `type`, `subject`, and `time`;
- department scope inside the protected payload and authorization context, not
  an unrestricted routing label;
- aggregate ID/version, command idempotency key, policy version, and content
  digest;
- no raw evidence values, free-form reason text, identity attributes, media,
  credentials, or provider destinations in broker headers.

P4.3 may claim envelope compatibility only after exact conformance tests; the
initial plan does not claim CloudEvents certification or complete conformance.

## Typed API Problems

Planned stable problem codes:

- `alert_transition_invalid`;
- `alert_version_stale`;
- `alert_command_duplicate`;
- `alert_authority_denied`;
- `alert_department_denied`;
- `alert_evidence_drift`;
- `alert_source_revision_stale`;
- `alert_budget_collapsed`;
- `alert_budget_suppressed`;
- `alert_timer_stale`;
- `alert_policy_unavailable`;
- `alert_runtime_disabled`.

Responses follow RFC 9457 structure and expose only bounded safe details.

## Compatibility Rules

- `AlertAggregateV1` and `AlertLifecycleEventV1` remain readable.
- Migration creates an additive V2 projection/revision shape and explicitly
  transforms the generated P4.0 `proposed` rows without fabricating decisions.
- P4.0/P4.1/P4.2 evidence, package digests, and historical source bindings are
  immutable.
- P4.2 evaluation semantics and digests remain unchanged.
- the Phase 2.5 Sentinel lab remains an independent compatibility environment;
  only a versioned sanitized metadata envelope can cross the boundary;
- PostgreSQL remains authoritative when any future external workflow executor
  is introduced;
- SQLite supports deterministic single-worker development tests only.
- PostgreSQL is required for multi-worker locking, forced RLS, and authoritative
  concurrency evidence.
