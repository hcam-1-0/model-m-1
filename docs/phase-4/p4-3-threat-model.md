# P4.3 Alert Lifecycle And Orchestration Threat Model

Status date: 2026-09-04

Status: owner-selected planning profile reconciled; no implementation or
runtime authorization.

## Assets

- alert identity and immutable lifecycle history;
- human review decisions and role snapshots;
- evidence/source/policy digests and provenance;
- department isolation and authorization context;
- assignment, suppression, escalation, merge, correction, timer, and budget
  records;
- aggregate versions, idempotency receipts, audit records, and outbox events;
- operational safety boundary preventing notification, dispatch, enforcement,
  and autonomous action.

## Trust Boundaries

1. P4.2 generated evaluation revision to internal P4.3 proposal service.
2. API gateway/RBAC context to department-scoped lifecycle service.
3. Lifecycle service to PostgreSQL aggregate, revisions, audit, timers, budgets,
   and transactional outbox.
4. Worker claim boundary for timers/outbox and their bounded leases.
5. Outbox publication boundary to an internal event bus; no external provider
   is in P4.3 scope.
6. Read projections to future operator UI; P4.3 plans API support only.
7. Optional local timer executor to a generated external-executor simulator and
   a future default-off workflow adapter contract.
8. Optional sanitized Phase 2.5 lab metadata envelope to the P4.2-compatible
   ingress adapter; there is no direct Sentinel/camera/media trust boundary.

## Threats And Required Controls

### Duplicate or conflicting creation

Threat: retries, replay, concurrent workers, or semantically equivalent source
events create multiple alert aggregates.

Controls: separate delivery and semantic keys; canonical identity; deterministic
alert ID; unique constraints; transaction-scoped command receipt; concurrency
and collision tests; correction appends rather than recreates when occurrence
identity is unchanged.

### Lost update or forged transition

Threat: two reviewers mutate the same version, a client skips a required state,
or a request forges actor/department data.

Controls: server-derived actor and department; RBAC; mandatory `If-Match` and
reason; strict transition matrix; aggregate version column; transactionally
consistent revision/audit/outbox; no actor supplied by untrusted payload.

### Authority escalation

Threat: a rule, policy, severity, timer, or class change turns a proposed alert
into an autonomous action.

Controls: police-intelligence permits only `mandatory_review`; generated
`bounded_automation` permits only separately typed synthetic `system_health`;
authority/domain cannot mutate or inherit; no provider/notification/dispatch
ports; timer cannot decide disposition; confirmation cannot encode identity,
guilt, threat, or enforcement; `future_autonomous_action` is hard-denied; and
startup/production configuration denies P4.3 runtime unless a later exact gate
is effective.

The generated system-health lane adds domain-confusion risk. Required controls
include immutable domain/class fields, separate policy/contract types, no shared
rule output with police intelligence, and cross-lane negative tests at API,
service, persistence, and outbox layers.

### Cross-department access

Threat: API joins, worker claims, merge targets, dedupe keys, or direct database
queries reveal or mutate another department's records.

Controls: department in every key and foreign-key relationship; application
scope checks; forced PostgreSQL RLS; non-owner runtime role; owner/superuser/
`BYPASSRLS` safeguards; same-department merge constraints; negative API and
direct-SQL tests.

### Evidence or policy drift

Threat: a review decision is recorded against evidence, rule, or policy that
changed between read and commit.

Controls: bind source evaluation revision, evidence-set digest, policy version,
and expected aggregate version; reverify in transaction; fail closed on stale
or missing input; append corrections and reopen rather than rewriting decisions.

### Quorum capture, self-approval, or deadlock

Threat: one reviewer fills multiple slots, unauthorized roles vote, evidence
changes between votes, or universal quorum leaves routine work permanently
blocked.

Controls: immutable bounded quorum policy; distinct actor constraint; role and
department snapshot; evidence/policy/aggregate-version binding per vote;
duplicate/stale vote denial; explicit disagreement/timeout outcomes; one-reviewer
default; no automatic approval when quorum is incomplete.

### Silent suppression or overload loss

Threat: high volume causes records to be dropped, hidden, or auto-confirmed.

Controls: hierarchical budgets; no drop action; explicit route/collapse/
suppressed-recorded outcomes; preserved counts/time range/representative
evidence/omitted digest; bounded queue and storage alerts; overload goldens.

### Timer replay, theft, or stale action

Threat: duplicate timer execution, abandoned leases, clock changes, or an old
timer mutates a new aggregate version.

Controls: deterministic timer identity; event-time basis; stored due instant;
lease and attempt bounds; aggregate/policy version binding; stale-timer no-op;
idempotent terminal record; `SKIP LOCKED` only for ordered queue claims;
recovery drill after lease expiry.

### Workflow-adapter substitution or split-brain

Threat: a future external executor invents work, executes stale work, bypasses
leases, or becomes an alternative source of business truth.

Controls: PostgreSQL remains authoritative; hash-bound capability manifest;
exact timer/policy/aggregate/lease version; idempotency receipt; bounded outcome
allowlist; local generated simulator first; no real adapter/dependency/network
in P4.3; outage/revocation/split-brain tests before separate activation.

### Sentinel-lab boundary contamination

Threat: the compatibility path imports lab code, accepts a URL or media, uses
real identifiers, bypasses P4.2 validation, or makes canonical P4.3 availability
depend on the lab.

Controls: one-way typed sanitized metadata envelope; generated fixtures and
in-process fake only; no URL/credential/media/arbitrary payload fields; no main-
to-lab call; normal P4.2 contract/digest/authority validation; adapter disabled
by default; separate authorization for any future real lab validation.

### Merge laundering or history deletion

Threat: merging hides a source alert, crosses departments, or changes review
history.

Controls: merge is an append-only relationship; source remains readable;
same-department and version checks; canonical-target cycle prevention; actor/
reason/policy binding; unmerge or correction is another revision.

### Sensitive telemetry leakage

Threat: IDs, reason text, evidence values, locations, or department data enter
metrics, logs, traces, broker headers, or exceptions.

Controls: low-cardinality enums only; safe reason taxonomy; no raw payloads or
free text in telemetry; bounded RFC 9457 problems; structured audit in the
protected database; redaction tests; fail closed on serialization errors.

### Resource exhaustion

Threat: unbounded history, reason strings, evidence lists, retry storms,
high-cardinality telemetry, or merge graphs exhaust resources.

Controls: strict schema sizes/counts; bounded retries and leases; history
pagination; merge depth/cycle bounds; policy-defined retention; per-scope
budgets; deterministic incident collapse; no unbounded user expressions.

### Outbox inconsistency

Threat: an aggregate commits without an event, an event publishes before commit,
or redelivery reapplies a mutation.

Controls: aggregate/revisions/audit/outbox in one transaction; idempotent event
identity; publication leases and attempts; publication is separate from
aggregate mutation; recovery and rollback tests.

## Abuse Cases

- reuse one delivery ID with different content;
- use different delivery IDs for the same semantic occurrence;
- force a semantic-key collision with different canonical material;
- submit stale ETags or replay successful commands;
- skip directly from `proposed` to `confirmed` without permitted review path;
- use a timer to confirm, dismiss, resolve, or close;
- lower authority by relabeling police intelligence as system health;
- use one reviewer to satisfy multiple quorum slots or complete a quorum against
  stale evidence, policy, or aggregate versions;
- make an executor adapter invent an effect or treat external state as truth;
- place a URL, credential, identifier, media, private data, Government data, or
  direct-alert command in a lab envelope;
- merge into another department or create a merge cycle;
- suppress without expiry/reason/policy or hide the suppression count;
- overflow evidence, reason, pagination, merge, timer, or budget bounds;
- alter evidence or policy after review starts;
- inject CR/LF, markup, secrets, SQL, or identifiers into telemetry fields;
- activate a worker through import, startup side effect, test collection, or
  production configuration;
- expose raw audit or source payloads through an RFC 9457 error.

## Stop Conditions

Implementation or validation must stop closed if:

- any selected owner decision is missing or contradictory;
- an accepted P4.0-P4.2 artifact or source binding changes unexpectedly;
- deterministic identity cannot be proven under replay and concurrency;
- any allowed transition lacks actor, reason, expected version, policy, audit,
  revision, or outbox evidence;
- authority class can escalate or mutate;
- a timer or budget policy can change human disposition;
- overload handling loses occurrence/evidence accounting;
- cross-department access succeeds at application or database level;
- external notification/provider/dispatch/enforcement capability becomes
  reachable;
- system-health automation can consume police-intelligence input or escape its
  generated-only bounded action set;
- quorum can be completed by duplicate/stale/unauthorized reviewers;
- workflow execution can replace PostgreSQL truth or use a real external engine;
- the lab adapter can contact Sentinel, accept media/private data, bypass P4.2,
  or become a canonical runtime dependency;
- prohibited data appears in logs, metrics, traces, errors, or headers;
- PostgreSQL concurrency/RLS evidence is claimed without PostgreSQL execution;
- a dependency change, network action, model/data/media access, container,
  Kubernetes, deployment, or remote Git action would be required.
