# Phase 4 Product Scope

Status: proposed planning baseline; not owner accepted and not authorized for
implementation.

## Mission

Phase 4 converts trusted Phase 3 analytic events and separately authorized
reference facts into explainable, reviewable intelligence hypotheses and
proposed alerts. It gives operators the provenance, uncertainty, workflow, and
audit trail needed to decide what deserves attention while preserving human
authority over operational decisions.

Phase 4 is the intelligence and workflow layer between analytics and the Phase
5 operator applications. It is not a face-recognition system, a predictive
policing system, or an autonomous dispatch or enforcement engine.

## Primary Users

| User | Need |
| --- | --- |
| Control-room operator | Prioritized proposed alerts with source, time, reason, confidence, and limitations |
| Supervisor | Queue health, escalation, assignment, acknowledgement, override, and closure controls |
| Investigator | Chronological facts, hypotheses, evidence references, reviewer decisions, and provenance |
| Intelligence analyst | Bounded event correlation, rule versions, link explanations, and uncertainty |
| Integration administrator | Default-off provider configuration, credential references, health, and revocation |
| Security/data reviewer | Department isolation, access evidence, retention, deletion, and abuse monitoring |
| Platform engineer | Stable contracts, replay, idempotency, queues, observability, and recovery |
| Accountable owner | Explicit risk choices, promotion gates, accepted evidence, and kill-switch authority |

## Required Baseline Capabilities

- consume only validated Phase 3 event versions through the transactional
  outbox/event-consumer boundary;
- deduplicate, order, and group late or repeated events without manufacturing a
  global order;
- preserve source occurrence time, producer observation time, platform receive
  time, durable record time, and correction time as separate typed values;
- correlate events by explicit time, location, stream, camera, class, rule, and
  authorized reference keys;
- validate spatial inputs against one declared coordinate-reference contract and
  reject invalid, ambiguous, unbounded, or unauthorized geometries;
- preserve every contributing event ID, producer lineage, rule version, policy
  version, and uncertainty value;
- emit a `correlation_hypothesis`, not an identity fact;
- compile visual rules into versioned typed temporal graphs with constrained
  CEL limited to a closed host-provided context;
- support deterministic simulation and non-alerting shadow evaluation before a
  rule version can become active;
- create proposed alerts with deterministic keys and a complete lifecycle;
- support acknowledgement, assignment, suppression, escalation, resolution,
  reopen, and false-positive/duplicate dispositions;
- enforce department scope, least privilege, reason-required mutations,
  optimistic concurrency, immutable audit history, and database-level row
  isolation as defense in depth;
- provide typed, revocable, default-off integration adapters whose credentials
  are resolved through secret references;
- treat any reference-data result as a candidate match until an authorized
  human completes the required review;
- create an append-only investigation timeline containing facts, hypotheses,
  actions, and corrections as distinct record types;
- record provenance as versioned entities, activities, agents, derivations, and
  integrity references without claiming formal standards conformance;
- expose sanitized low-cardinality metrics, bounded failures, recovery controls,
  alert-volume budgets, incident-level collapse, and a system-wide kill switch.

## Capability Tiers

### Tier A: Generated Intelligence Foundation

- generated Phase 3 analytic-event ingestion;
- deterministic single-stream and multi-stream event grouping without entity
  identity;
- canonical evidence-first hypothesis graphs with rebuildable flat event-group
  projections for simple clients;
- deterministic CPU correlation plus contract-ready optional probabilistic,
  temporal-graph learned, and ensemble lanes that remain inactive until their
  own implementation and promotion gates pass;
- temporal rule evaluation and proposed-alert lifecycle;
- generated simulation and shadow-mode evaluation with zero operational alert
  delivery;
- synthetic reference-provider adapter with invented, non-issuable records;
- append-only investigation timeline and evidence-reference provenance;
- generated replay, concurrency, isolation, retention, and failure evidence.

Tier A is the only implementation tier eligible for the first Phase 4 start
proposal.

Tier A performs no real or external reference integration. Provider contracts,
the generic transport envelope, and generated simulators exist to prove a
fail-closed boundary, not to authorize a destination or credential.

### Tier B: Owned-Lab Operational Evaluation

- owned and authorized lab event producers;
- operator queue and reviewer workflow evaluation;
- declared alert-volume, latency, suppression, and recovery benchmarks;
- controlled integrations using organization-owned synthetic or test records;
- usability and human-factors evidence with trained participants.

Tier B requires separate lab, data, runtime, and participant authorization. It
does not authorize Government or private operational data.

### Tier C: Governed External Integration Candidate

- one explicitly approved external provider and exact data contract;
- legal purpose, controller/processor roles, fields, retention, deletion,
  access, audit, incident response, and revocation approved before connection;
- provider-specific accuracy, stale-data, false-match, outage, and abuse tests;
- production-like but non-enforcement pilot with mandatory human confirmation.

Every provider enters Tier C independently. Approval for one provider does not
authorize another provider, a new data class, or broader lookup purposes.

## Explicit Non-Goals

- face recognition, biometric templates, or sensitive-attribute inference;
- persistent person re-identification or automatic cross-camera identity;
- predictive policing, criminality scoring, intent inference, or individual
  risk scores;
- treating plate OCR, object class, color, route, or proximity as identity;
- automatic wanted-person, vehicle-owner, registration, case, or Government
  database queries without a provider-specific authorization;
- autonomous alert confirmation, dispatch, detention, enforcement, or evidence
  conclusion;
- model-first candidate proposal acting as model authority or bypassing
  deterministic scope, policy, geometry, contradiction, or review checks;
- silent rule changes, unbounded correlation windows, or unrestricted query
  expressions;
- treating wall-clock receipt order as proof of event order or silently
  repairing ambiguous timestamps and invalid geometry;
- copying video, frames, crops, documents, or source records into an alert by
  default;
- indefinite metadata retention or deletion that bypasses an authorized hold;
- claiming legal, evidentiary, accuracy, security, scale, or deployment
  conformance from generated tests.

## Intelligence Semantics

Phase 4 keeps four categories separate:

1. **Observation:** probabilistic Phase 3 model output.
2. **Analytic event:** deterministic result of a spatial or temporal analytic
   primitive.
3. **Correlation hypothesis:** a versioned explanation that multiple inputs
   may be related under a declared rule and window.
4. **Proposed alert:** a workflow object requesting human attention.

An operator decision is recorded separately from all four. Corrections append a
new decision or disposition; they never rewrite the original source evidence.

## Human Authority

- Every proposed alert starts `pending_review` unless it is a synthetic test.
- Shadow evaluations are visibly non-operational and cannot enter a reviewer or
  dispatch queue.
- Priority and confidence are separate: priority expresses operational routing,
  while confidence expresses evidence strength.
- The system may recommend routing and escalation but cannot assert guilt,
  ownership, identity, or required police action.
- A reviewer sees supporting and contradicting evidence, missing inputs,
  confidence, freshness, source quality, and rule limitations.
- Confirmation, dismissal, merge, escalation, closure, reopen, and correction
  require an attributable actor or authorized service, reason code, timestamp,
  and policy version.
- Corrections and retractions propagate to derived hypotheses, proposed alerts,
  timelines, exports, and indexes through append-only revisions; prior evidence
  remains reconstructable.
- High-consequence capabilities require a stricter policy and cannot inherit a
  lower-tier approval.
- The architecture may define class-scoped bounded automation for generated and
  system-health workflows and reserve a future autonomous-action boundary, but
  neither can confirm or dispatch a police-intelligence alert under Phase 4.

## Data Boundary

The initial implementation may contain only generated, non-issuable records and
derived metadata. It must not contain real plate numbers, owner records,
Government identifiers, case details, biometric data, images, clips, or source
credentials.

Future data use requires a data-class record that defines purpose, lawful and
organizational authority, source, allowed fields, role access, residency,
retention, deletion, hold behavior, export policy, and incident response.
Legal and policy owners must also record the applicable law, commencement state,
organizational instruction, electronic-record procedure, and unresolved legal
questions. Architecture documentation is not legal authorization.

## Success Definition

Phase 4 is complete only when Tier A contracts and implementation are accepted,
correlation and alert replay are deterministic, duplicate delivery cannot
duplicate alerts, department boundaries hold under adversarial tests, every
hypothesis and decision is explainable from immutable lineage, generated
reference matches are abstention-capable, lifecycle and recovery drills pass,
spatial and time-boundary contracts pass adversarial tests, shadow rules cannot
create operational alerts, correction propagation is reconstructable, and a
complete Phase 5 operator-contract handoff is accepted.

No visual demonstration, model score, rule count, or API count is sufficient by
itself.
