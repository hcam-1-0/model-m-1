# P4.7 Final Acceptance And Phase 5 Handoff Implementation Plan

Status: proposed, non-effective, implementation not authorized

## Objective

Complete Phase 4 with a deterministic generated-only demonstration that
traverses accepted Phase 3 and Phase 4 service contracts, produces independently
checkable evidence and limitations, and hands Phase 5 a stable consumer contract
for APIs, events, workflows, UI states, actions, errors, accessibility, and
degradation. P4.7 does not build the Phase 5 UI and does not prove operational
readiness.

## Frozen Weight And Current Progress

| Item | Weight | Current earned | Completion condition |
| --- | ---: | ---: | --- |
| P4.7-A Controlled generated end-to-end demonstration | 2 | 0 | Accepted portfolio executes twice deterministically through accepted service boundaries; all mandatory scenarios/assertions pass; zero prohibited effects |
| P4.7-B Evidence index, limitations, claims, and operations pack | 1 | 0 | Acyclic digest-bound evidence, complete claim/limitation registers, runbook, reconstruction, and unsupported-claim checks pass |
| P4.7-C Phase 5 API/event/workflow/UI-state handoff | 1 | 0 | Canonical catalogues, optional projections, compatibility matrix, examples, UI/accessibility states, and consumer checks pass |
| P4.7-D Final Phase 4 owner acceptance | 1 | 0 | Owner accepts exact technical commit, evidence package, handoff digest, limitations, and closed future gates |

Current exact progress:

- P4.7: **0/5 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 4: **95/100 (95.00%)**, change **+0.00 percentage points**.
- Planning and research completeness: **100.0000%**, awarding **0 product
  points**.
- Technical ceiling before exact owner acceptance: P4.7 **4/5 (80.0000%)** and
  Phase 4 **99/100 (99.00%)**.
- After exact P4.7 acceptance: P4.7 **5/5 (100.0000%)** and Phase 4
  **100/100 (100.00%)**.

Frozen items receive no partial credit.

## Preconditions

Implementation may begin only after:

1. the owner selects D-P4.7-001 through D-P4.7-012 explicitly;
2. selections are reconciled into a non-effective P4.7 planning package;
3. the owner accepts the exact reconciled planning-package SHA-256;
4. a bounded start package freezes exact paths, dependencies, fixtures,
   scenario counts, bounds, tests, evidence, and prohibited actions;
5. the owner accepts that exact start-package SHA-256.

P4.6 acceptance remains the immutable predecessor. A P4.7 start package cannot
rewrite an accepted Phase 0 through P4.6 artifact to make a new check pass.

## Proposed Delivery Sequence

### W1: Canonical Contracts And Static Guardrails

Proposed work:

- implement the canonical contracts listed in the P4.7 contract catalogue;
- define strict enums, bounds, generated-only flags, identity classes, logical
  time, chronology, assertion families, evidence states, claim states,
  limitation states, compatibility classes, and UI states;
- reject extra fields, unsafe strings, unbounded collections, real-data-shaped
  identifiers, credentials, locators, media references, and operational flags;
- define a static source policy rejecting socket, HTTP client, provider,
  subprocess, camera/media, model, container, Kubernetes, deployment, and
  direct persistence access from the P4.7 package;
- snapshot canonical contracts before orchestration code exists.

Evidence: schema catalogue, contract snapshots, prohibited-import scan,
generated boundary vectors, and source-policy result.

### W2: Generated Fixture And Scenario Portfolio

Proposed work:

- materialize one narrative scenario and the selected mandatory variants using
  non-issuable generated identifiers;
- bind exact input hashes, accepted rule/provider/review/control revisions,
  logical clock, seed, identifier namespace, source order, expected semantic
  outcomes, and allowed variance;
- build a fixture linter for prohibited identifiers, payload shapes, locators,
  media, credentials, hidden wall-clock values, and unbound randomness;
- define pairwise negative fixtures for role/scope, ETag, idempotency,
  chronology, stale state, malformed contracts, and unknown versions.

Evidence: fixture manifest, per-file hashes, generated-data attestation,
scenario inventory, and expected-outcome catalogue.

### W3: Bounded Scenario Engine And Adapters

Proposed work, only if later authorized:

- implement a typed scenario state machine with strict step allowlist;
- use a deterministic logical clock and identifier provider;
- implement an in-process generated adapter that calls accepted application
  service boundaries without direct repository/database writes;
- implement read-only comparison adapters for the local HTTP/event projections;
- enforce maximum steps, records, bytes, attempts, logical duration, output
  files, and zero network/external-process effects;
- retain only normalized generated observations required by evidence.

No external workflow engine, broker, telemetry backend, provider, camera,
model, process, container, or Kubernetes dependency is introduced.

Evidence: adapter equivalence, direct-persistence denial, source-boundary scan,
step lifecycle tests, and bounded output inventory.

### W4: Layered Assertions And Replay

Proposed work:

- validate schemas and fixture/source identity before running any step;
- validate auth, department, reason, RLS parity, ETags, idempotency, chronology,
  rules, candidates, review/quorum, lifecycle, evidence, corrections,
  reconstruction, signals, failure/recovery, redaction, and side-effect absence;
- run every mandatory scenario twice from a clean generated state;
- compare canonical semantic digests under the selected normalization profile;
- keep every assertion family visible; no aggregate-only output;
- fail on skip, unknown, incomplete, unaccounted loss, prohibited effect, or
  optional projection presented as canonical.

Evidence: per-step observations, per-family assertion results, replay
comparison, side-effect ledger, loss accounting, and aggregate result.

Completion of W1 through W4 and every P4.7-A condition earns **2/2 P4.7-A
points**, moving P4.7 from 0% to **40.0000%** and Phase 4 from 95% to **97.00%**.

### W5: Evidence, Claims, Limitations, And Operations Pack

Proposed work:

- create an acyclic evidence index bound to the exact source commit and every
  required component hash;
- generate claim and limitation registers from typed canonical records;
- prohibit unsupported readiness, accuracy, scale, legal, evidentiary,
  compliance, conformance, accessibility, and production statements;
- create a generated-only preflight, execution, verification, failure, resume,
  cleanup, reconstruction, and evidence-sealing runbook;
- document residual risks and the qualifying evidence required to revisit each
  limitation;
- optionally generate RFC 8785, PROV, and SLSA-shaped projections, each with
  independent status and no automatic claim.

Evidence: complete component inventory, acyclic graph verification, claim-to-
evidence coverage, limitation-to-claim coverage, mutation negatives, runbook
static validation, and human-readable evidence review.

Completion earns **1/1 P4.7-B point**, moving P4.7 from 40% to **60.0000%** and
Phase 4 from 97% to **98.00%**.

### W6: Phase 5 Consumer Handoff

Proposed work:

- inventory every accepted Phase 4 list, detail, command, health,
  reconstruction, and operations surface;
- define canonical HTTP operation contracts with auth/scope/reason, ETag,
  idempotency, pagination, ordering, freshness, errors, examples, events, and
  action availability;
- define event operations with producer, consumer intent, schema, ordering,
  partitioning, occurrence/delivery/correlation/causation, replay, correction,
  timeout, and unknown-version behavior;
- define generated consumer journeys and explicit async completion criteria;
- generate pinned OpenAPI, AsyncAPI, CloudEvents, and Arazzo projections only
  for formats selected by owner decision;
- define every Phase 5 loading, empty, partial, stale, degraded, denied,
  conflict, failure, recovery, correction, and success state;
- bind keyboard, focus, accessible name/role/value, status announcement, error,
  non-color, target, contrast, and reduced-motion requirements;
- publish version, compatibility, deprecation, migration, and consumer-test
  rules.

Evidence: canonical handoff digest, projection equivalence, operation/event/
workflow/UI cross-reference coverage, generated examples, compatibility
mutation tests, and accessibility-requirement completeness. No UI is built.

Completion earns **1/1 P4.7-C point**, moving P4.7 from 60% to **80.0000%** and
Phase 4 from 98% to **99.00%**.

### W7: Technical Evidence Seal And Final Owner Gate

Proposed work:

- run focused and full generated/static suites required by the accepted start
  package;
- verify accepted historical readiness from Phase 0 through P4.6;
- verify one migration head and exact dependency lock, if P4.7 introduces no
  accepted migration or dependency change;
- seal source commit, package components, canonical component digest, test and
  coverage results, limitations, claims, handoff digest, and explicit
  non-authorizations;
- prepare a non-effective exact `D-P4.7-ACCEPTANCE` proposal.

Technical sealing alone earns no P4.7-D point. Exact owner acceptance earns the
final **1/1 point**, moving P4.7 from 80% to **100.0000%** and Phase 4 from 99%
to **100.00%**.

Phase 5 planning remains blocked until a separate explicit owner decision even
after Phase 4 reaches 100%.

## Proposed Source Boundaries

Exact paths are intentionally deferred to a future start package. The likely
ownership shape is:

```text
app/hcam/acceptance/                 canonical P4.7 contracts and generated engine
fixtures/phase4/p4-7/                non-issuable generated scenarios and outcomes
contracts/phase-4/p4-7/              canonical snapshots, handoff, evidence, acceptance
docs/phase-4/                        research, decisions, runbooks, limitations, review
tests/test_phase47_*.py               generated/static contract and scenario validation
tools/phase47_readiness.py            bounded verifier and evidence sealer
```

No new public API route, migration, runtime dependency, external adapter,
frontend application, container, Kubernetes manifest, deployment definition,
or CI network integration is presumed by this plan.

## Validation Matrix

| Area | Required future validation |
| --- | --- |
| Authorization | Exact plan/start packages, accepted P4.6 predecessor, closed P4.7/Phase 5 gates before authorization |
| Contracts | Strict versions, enum/bound coverage, unknown-field denial, canonical snapshots, generated-only flags |
| Fixtures | Non-issuable identities, exact hashes, no real-data patterns, no media/locator/credential fields, deterministic source |
| Scenario | Step allowlist, acyclic graph, bounds, no direct persistence, no external effect, all mandatory variants |
| Determinism | Logical clock/IDs/seeds/order, clean-state replay, normalized digest equality, allowed-variance audit |
| Security | Role/scope/reason/RLS parity, stale ETag, idempotency, cross-department denial, safe errors, redaction |
| Intelligence | Deduplication, late/conflict, rule revision, abstention, contradiction, review/quorum, lifecycle denial |
| Evidence | Append-only correction, provenance DAG, integrity, reconstruction, no source resolution or media copy |
| Operations | Failure taxonomy, retry/lease/circuit/degradation, loss accounting, zero real backend, zero operational claim |
| Package | Acyclic complete index, exact source/component hashes, independent mutation negatives, no self-digest |
| Claims | Every claim supported and bounded; every limitation linked; prohibited claims rejected |
| HTTP | Operation IDs, auth/scope, ETag/idempotency, pagination/order/freshness, RFC 9457-safe problems, examples |
| Events | Schema/version, producer/intent, ordering, delivery, correlation/causation, corrections, unknown versions |
| Workflow | Explicit inputs, dependencies, async completion, failure, timeout, and terminal evidence |
| UI | All data/action/degradation states linked to backend facts; unavailable actions remain unavailable |
| Accessibility | Keyboard, focus, status, names/roles/values, errors, non-color, target, contrast, reduced motion, unknown evidence |
| Compatibility | Change classification, supported consumers, deprecation, migration, mutation detection, security changes |
| Regression | Full repository suite, historical readiness, package build, dependency and migration integrity as authorized |

## Evidence Package Requirements

The future P4.7 evidence package must bind:

- exact planning, decisions, reconciled acceptance, and start authorization;
- accepted P4.6 predecessor and historical readiness results;
- source commit and complete changed-path inventory;
- contracts, fixtures, expected outcomes, scenario engine, adapters, assertions,
  runbook, and verifier hashes;
- two-run deterministic replay evidence for every mandatory scenario;
- explicit counts for inputs, steps, outputs, assertions, skips, unknowns,
  retries, failures, drops, side effects, and retained artifacts;
- claims, limitations, residual risks, and unsupported-claim results;
- HTTP/event/workflow/UI/accessibility/compatibility handoff digest;
- test, coverage, lint, compile, package, dependency, migration, and historical
  compatibility results required by the accepted start package;
- explicit generated-only, default-off, production-forbidden, zero-real-data,
  zero-media, zero-network, zero-operational-action, and non-deployment limits.

## Stop Conditions

Stop and require a new explicit owner decision if implementation would:

- change an accepted Phase 0 through P4.6 semantic or evidence artifact;
- add a dependency, migration, route, broker, external engine, network client,
  provider, model, media path, process, container, or Kubernetes execution not
  named by the accepted start package;
- use direct persistence access as demonstration evidence;
- access real, Government, police, private, biometric, vehicle, owner,
  registration, watchlist, investigation, case, or evidence data;
- produce an operational alert, notification, dispatch, enforcement, identity
  conclusion, or autonomous action;
- weaken mandatory review, department isolation, RLS, ETag, idempotency,
  provenance, correction, redaction, or zero-retention boundaries;
- represent unknown, skipped, incomplete, stale, or failed evidence as pass;
- claim standards conformance, accessibility compliance, operational
  readiness, production capacity, legal admissibility, or real-world accuracy;
- authorize Phase 5 planning, implementation, deployment, or remote Git by
  implication.

## Required Gate Sequence

1. Owner decisions D-P4.7-001 through D-P4.7-012.
2. Non-effective reconciled planning package.
3. Exact owner acceptance of reconciled planning SHA-256.
4. Non-effective bounded P4.7 start package.
5. Exact owner start authorization.
6. Generated-only implementation and validation.
7. Technical commit and independently checkable evidence package.
8. Exact owner P4.7/Phase 4 acceptance.
9. Separate Phase 5 planning authorization, if the owner chooses to proceed.
