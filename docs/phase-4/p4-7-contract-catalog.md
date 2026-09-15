# P4.7 Planning Contract Catalog

Status: proposed, non-effective, no implementation authority

## Contract Principles

1. H-CAM canonical contracts remain authoritative. OpenAPI, AsyncAPI,
   CloudEvents, Arazzo, RFC 8785, PROV, and SLSA-shaped documents are optional
   projections unless separately accepted.
2. Every P4.7 record is generated-only, default-off, production-forbidden,
   bounded, versioned, and strict about unknown fields.
3. Scenario orchestration uses accepted service boundaries and cannot write
   repositories or database tables directly.
4. Identifiers are non-issuable, manifest-derived, department-scoped, and
   separate by purpose.
5. Logical time, source order, receipt order, durable order, correction order,
   and observation order are retained rather than collapsed.
6. Pass, fail, skipped, incomplete, unsupported, stale, and unknown are
   distinct. Only all-mandatory-pass can close a weighted item.
7. Evidence identity and integrity never imply evidentiary truth, legality,
   accuracy, identity confirmation, conformance, or operational readiness.
8. Phase 5 action availability is informative; server authorization remains
   authoritative.

## Proposed Canonical Contracts

| Contract ID | Purpose | Authority |
| --- | --- | --- |
| `hcam.acceptance.scenario-manifest.v1` | Immutable scenario identity, fixture inventory, logical clock, seed, namespaces, steps, assertions, and bounds | Canonical P4.7 scenario definition |
| `hcam.acceptance.scenario-fixture-set.v1` | Exact generated inputs and expected semantic outcomes | Canonical fixture inventory |
| `hcam.acceptance.scenario-step.v1` | One bounded call, event observation, assertion, or control transition | Canonical workflow step |
| `hcam.acceptance.scenario-run.v1` | Attempt lifecycle, environment class, source identity, started/finished state, and terminal result | Canonical run record |
| `hcam.acceptance.step-observation.v1` | Sanitized request/event/result metadata and chronology for one step | Canonical observation record |
| `hcam.acceptance.assertion-result.v1` | Independent schema, policy, chronology, integrity, redaction, replay, or accessibility assertion | Canonical assertion result |
| `hcam.acceptance.replay-comparison.v1` | Normalized comparison of two clean generated runs | Canonical determinism evidence |
| `hcam.acceptance.side-effect-ledger.v1` | Proof that only allowlisted generated local effects occurred and external effects remained zero | Canonical side-effect boundary |
| `hcam.acceptance.evidence-index.v1` | Acyclic artifact inventory with hashes, roles, provenance, completeness, and verification state | Canonical evidence index |
| `hcam.acceptance.claim-register.v1` | Scoped claims, evidence class, support, freshness, limitations, and decision state | Canonical claim authority |
| `hcam.acceptance.limitation-register.v1` | Known limitation identity, affected claims, severity, mitigation, owner, and closure gate | Canonical limitation authority |
| `hcam.acceptance.operations-runbook.v1` | Generated preflight, execution, verification, failure, resume, cleanup, and evidence steps | Canonical non-operational runbook |
| `hcam.acceptance.reconstruction-manifest.v1` | Expected final chronology and derivation traversal from generated source to timeline | Canonical reconstruction oracle |
| `hcam.handoff.http-operation.v1` | Phase 5 HTTP operation semantics, auth, scope, concurrency, pagination, errors, and examples | Canonical HTTP handoff |
| `hcam.handoff.event-operation.v1` | Event type, producer/consumer, ordering, correlation, schema, delivery, and replay semantics | Canonical event handoff |
| `hcam.handoff.workflow.v1` | Consumer journey with API/event steps, dependencies, success/failure criteria, and outputs | Canonical workflow handoff |
| `hcam.handoff.ui-state.v1` | Backend fact to visible state, action availability, recovery, freshness, and accessibility behavior | Canonical UI-state handoff |
| `hcam.handoff.ui-action.v1` | Command availability, confirmation, required role/scope/reason/ETag, terminal and conflict behavior | Canonical action handoff |
| `hcam.handoff.accessibility-requirement.v1` | Applicable criterion, component, keyboard/focus/status/error behavior, evidence state, and limitation | Canonical accessibility handoff |
| `hcam.handoff.compatibility.v1` | Producer and consumer versions, change classification, supported window, deprecation, and migration evidence | Canonical compatibility authority |
| `hcam.phase4.closeout.v1` | Exact P4.7 evidence binding, weighted completion, limitations, owner acceptance, and closed future gates | Canonical Phase 4 closeout |

## Scenario Manifest

`hcam.acceptance.scenario-manifest.v1` should contain:

- `scenario_id`, `scenario_version`, `title`, `purpose`, and `evidence_class`;
- source commit, accepted predecessor package digests, migration head, contract
  catalogue digests, and feature-gate expectations;
- generated fixture-set identity and per-file SHA-256 values;
- deterministic seed, logical epoch, time zone, step quantum, identifier
  namespace, source sequence, tie-break rule, and normalization profile;
- required principals, departments, roles, reasons, capability flags, rule
  revisions, provider revisions, review policies, and control revisions;
- ordered step DAG with no cycles, bounded branches, bounded retries, expected
  terminal states, and explicit timeout semantics;
- mandatory assertion families, optional projections, required evidence paths,
  allowed variance, and prohibited side effects;
- maximum record count, byte size, duration, attempts, events, hypotheses,
  candidates, alerts, reviews, timeline entries, signals, and output artifacts;
- explicit `generated_only=true`, `operational=false`,
  `production_allowed=false`, and `network_allowed=false`.

The manifest cannot contain a credential, locator, camera ID, person or vehicle
identity, real plate, media path, provider destination, case identifier, or
free-form evidence payload.

## Demonstration Portfolio

The proposed minimum portfolio has one narrative scenario and eight mandatory
variants. Owner decision D-P4.7-002 can change the exact portfolio before any
implementation starts.

| Scenario | Required semantic path | Required terminal evidence |
| --- | --- | --- |
| S00 Golden narrative | Generated event -> correlation -> rule match -> proposed alert -> generated candidate review -> mandatory alert review -> lifecycle -> investigation timeline -> evidence reference -> reconstruction -> operations projection | Every mandatory stage succeeds, no external side effect, exact chronology and reconstruction digest |
| S01 Non-match/abstention | Valid event that does not satisfy the rule and ambiguous candidate evidence | No alert confirmation, explicit no-match/abstain state, no silent loss |
| S02 Duplicate/replay | Repeated delivery with same occurrence and idempotency identities | One semantic occurrence, replay receipt, no duplicate downstream aggregate |
| S03 Late/conflicting event | Bounded late event and contradictory generated observation | Deterministic conflict/late policy, revised hypothesis, visible uncertainty |
| S04 Authorization/isolation denial | Wrong role, wrong generated department, absent reason, and stale ETag | Exact sanitized denial/conflict results, zero cross-scope observation or mutation |
| S05 Reference degradation | Disabled/stale generated provider and timed-out generated query | Candidate state remains unknown/abstained, visible degradation, no identity conclusion |
| S06 Review/lifecycle denial | Insufficient quorum and invalid transition | Proposed alert remains unconfirmed; immutable denial/review history |
| S07 Correction/retraction | Accepted generated correction affects hypothesis, alert, and timeline | Append-only propagation, prior state retained, reconstruction reflects both revisions |
| S08 Worker/recovery degradation | Generated retryable failure, lease recovery, circuit/degradation projection | Bounded retry, one terminal result, loss accounting, explicit degraded/recovered state |

Pairwise contract cases should supplement this portfolio for combinations that
are unsafe or expensive to express in one narrative. A mandatory scenario may
not be skipped merely because a pairwise test covers one of its assertions.

## Step And Observation Model

Each `scenario-step` should define exactly one kind:

- `command`: invoke an accepted service/API command with typed principal,
  department, reason, idempotency, and ETag inputs;
- `query`: read a bounded list/detail/health/reconstruction projection;
- `event_input`: submit one accepted generated Phase 3 event;
- `event_observation`: await one exact event type and correlation/causation
  relation within logical-time bounds;
- `control`: apply a generated-only accepted control revision through its
  service boundary;
- `clock_advance`: advance only the scenario logical clock;
- `assertion`: evaluate one named semantic invariant;
- `checkpoint`: seal a bounded normalized state projection.

Each observation records safe metadata only: scenario, step, attempt, logical
time, operation/event/contract type, status/reason code, revision, count,
freshness, degradation, canonical digest, and assertion links. Raw exceptions,
headers, request/response payloads, credentials, locators, identities, evidence
content, SQL, paths, and environment material are prohibited.

## Identity And Chronology

The following identifiers remain distinct:

| Identity | Meaning |
| --- | --- |
| `scenario_id` | Immutable scenario definition |
| `scenario_run_id` | One execution attempt derived from scenario and attempt ordinal |
| `fixture_id` | Generated input identity |
| `occurrence_id` | Semantic source occurrence |
| `delivery_id` | One delivery attempt |
| `operation_id` | HTTP/service command or query identity |
| `correlation_id` | Diagnostic relationship among operations/messages |
| `causation_id` | Immediate causal predecessor |
| `aggregate_id` | Hypothesis, alert, candidate set, or timeline aggregate |
| `revision_id` | Immutable state revision |
| `evidence_id` | Evidence reference or package component identity |

Required chronology fields include `source_at`, `observed_at`, `received_at`,
`recorded_at`, logical sequence, correction effective time, and durable order
where the accepted upstream contract supplies them. The scenario manifest must
state which fields are fixed, derived, monotonic, or allowed to vary.

## Assertion Model

Each assertion result includes assertion ID/version, family, mandatory flag,
input references, expected semantic condition, observed normalized value,
status, safe reason code, evaluator version, and evidence link. Required
families are:

- schema and bounds;
- fixture and source identity;
- authentication, role, department, purpose, reason, and RLS parity;
- chronology, ordering, causation, and correction;
- semantic identity, deduplication, and idempotency;
- rule revision and deterministic evaluation;
- candidate uncertainty, contradiction, calibration, and abstention;
- mandatory review, quorum, lifecycle, and ETag concurrency;
- evidence-reference integrity, provenance, and reconstruction;
- failure, retry, lease, circuit, degradation, and loss accounting;
- signal separation, redaction, and prohibited-field absence;
- side-effect absence and zero network/process/container activity;
- replay equivalence;
- HTTP/event/workflow projection compatibility;
- UI-state completeness and accessibility requirement coverage.

An aggregate result is `passed` only when all mandatory scenarios and all
mandatory assertion families pass, no required artifact is absent, no
prohibited effect is observed, and both replay runs have equivalent normalized
digests. `skipped`, `unknown`, and `incomplete` are non-passing.

## Evidence, Claim, And Limitation Model

The evidence index is a directed acyclic graph. Component roles include source,
authorization, fixture, schema, contract, scenario, observation, assertion,
result, replay, API projection, event projection, workflow projection, UI-state
handoff, accessibility matrix, operations runbook, limitation, claim,
validation, and acceptance proposal.

Every component requires path, media type, byte length, SHA-256, canonicalization
method, producer, source commit, generated-only state, provenance parents,
verification status, and retention class. The index itself is sealed only after
all components and must not include its own digest as an input component.

Claims use `proposed`, `supported_generated_only`, `unsupported`, `unknown`, or
`withdrawn`. They cannot use `operational`, `production_ready`, `compliant`,
`conformant`, `accurate`, `scalable`, or `legally_admissible` without a later
schema and evidence class explicitly authorizing those meanings.

Limitations require severity, affected contract/scenario/claim, consequence,
current mitigation, evidence gap, future qualifying evidence, owner, review
date, and status. A limitation can remain open at Phase 4 closeout when the
claim is correspondingly bounded and the owner explicitly accepts it.

## Phase 5 HTTP Handoff

Each handed-off HTTP operation requires:

- canonical operation ID, method, path, purpose, audience, and feature gate;
- auth role, department scope, reason, ETag, idempotency, audit, and no-store
  requirements;
- request and response schema versions, examples using generated identifiers,
  body/page/count/depth bounds, sort keys, cursor and snapshot semantics;
- success, accepted, empty, partial, stale, disabled, denied, not-found,
  conflict, validation, rate/budget, timeout, unavailable, and unknown states;
- RFC 9457-compatible safe problem projection with stable problem type and no
  sensitive detail;
- links to related events, list/detail views, commands, UI states, and
  deprecation/compatibility policy.

The handoff describes existing accepted surfaces. It does not add public P4.7
routes or authorize Phase 5 to invoke unavailable or disabled operations.

## Event And Workflow Handoff

Each event operation requires canonical event type and version, producer,
consumer intent, payload schema, generated example, ordering scope,
partitioning key class, occurrence/delivery/correlation/causation semantics,
at-least-once implications, idempotency expectation, correction/retraction
behavior, timeout/freshness, redaction, and unknown-version handling.

The optional AsyncAPI projection describes channels and messages but does not
select a broker. The optional CloudEvents projection maps only approved common
attributes and cannot replace H-CAM semantic identity. The optional Arazzo
projection describes generated consumer journeys and explicit asynchronous
success criteria; sending a message alone is never evidence that a workflow
completed.

## UI State And Accessibility Handoff

Each UI state binds a backend fact to:

- stable state ID and applicable route/view/component;
- visible title and concise state text;
- severity, freshness, completeness, and degradation;
- allowed and denied actions with server-authority prerequisites;
- refresh, retry, conflict resolution, correction, or escalation path;
- loading/empty/partial/stale/degraded/denied/conflict/failure/recovery behavior;
- keyboard order, initial/returned focus, visible focus, accessible name/role/
  value, status-message behavior, error association, target-size expectation,
  contrast/non-color meaning, and reduced-motion behavior;
- localization and long-text constraints without encoding operational policy in
  presentation strings.

Routine asynchronous updates use non-interrupting status semantics. Modal alert
dialogs are reserved for bounded confirmation or critical application failure
that needs an immediate response. Police-domain proposed alerts remain domain
records and do not automatically imply an ARIA `alert` or modal interruption.

## Compatibility Contract

Changes are classified as:

- `documentation_only`;
- `additive_optional`;
- `additive_required_for_new_capability`;
- `behavioral_compatible`;
- `deprecation`;
- `breaking_schema`;
- `breaking_semantic`;
- `security_boundary_change`.

Every change records producer version, supported consumer versions, affected
HTTP/event/workflow/UI contracts, migration instructions, fallback behavior,
deprecation deadline or `unset`, evidence, and owner decision. Unknown enum
values, new required fields, changed defaults, changed authorization,
reordered chronology, narrowed pagination, and altered error semantics are not
silently classified as additive.

## Proposed Bounds

| Resource | Planning bound |
| --- | ---: |
| Scenario definitions | 32 |
| Mandatory scenarios in one acceptance portfolio | 16 |
| Steps per scenario | 256 |
| Branches per scenario | 32 |
| Attempts per scenario | 2 clean replay runs plus 1 diagnostic run only if separately allowed |
| Generated fixture files | 256 |
| Generated records per run | 10,000 |
| Assertions per run | 20,000 |
| Evidence components | 10,000 |
| Claims | 512 |
| Limitations | 512 |
| HTTP operations | 512 |
| Event operations | 512 |
| Workflows | 128 |
| UI states | 1,024 |
| Actions per UI state | 32 |
| Contract or record size | 64 KiB unless an accepted predecessor has a smaller bound |
| Aggregate generated evidence | 256 MiB planning ceiling, with zero media |
| Network, provider, camera, model, process, container, cluster effects | 0 |

These are planning ceilings, not performance targets. Owner decisions and a
later start package must freeze exact implementation values.

## Proposed Phase 5 Handoff Inventory

1. Canonical schema and contract catalogue.
2. Pinned OpenAPI projection and operation matrix.
3. Pinned event catalogue with optional AsyncAPI/CloudEvents projections.
4. Generated consumer journeys with optional Arazzo projection.
5. Authentication, RBAC, department, purpose, reason, ETag, idempotency, audit,
   and feature-gate matrix.
6. Pagination, ordering, freshness, partial-result, correction, and replay
   semantics.
7. Stable safe-failure and RFC 9457 problem mapping.
8. List, detail, command, lifecycle, timeline, evidence, operations, and
   degradation UI-state inventory.
9. Accessibility requirements and evidence-state matrix.
10. Compatibility, deprecation, versioning, and consumer test policy.
11. Generated examples and scenario traces with no real data.
12. Known limitations, unsupported claims, residual risks, and Phase 5 gates.

## Stop Conditions

Future implementation must stop if it requires direct persistence access,
real data, media, camera/provider/network/model/runtime authority, operational
actions, an unaccepted contract change, an unbounded artifact, a hidden skip,
a compliance/conformance claim, or Phase 5 authority not present in the exact
accepted start package.
