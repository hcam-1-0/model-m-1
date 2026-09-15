# P4.7 Final Acceptance And Phase 5 Handoff Threat Model

Status: planning-only, non-effective

## Purpose

This threat model covers the proposed P4.7 generated demonstration,
deterministic replay, evidence and claims package, operations pack, Phase 5
HTTP/event/workflow/UI-state handoff, compatibility policy, and final Phase 4
acceptance gate. It does not authorize implementation, execution, final
acceptance, or Phase 5 work.

## Protected Assets

- Integrity of accepted Phase 0 through P4.6 contracts, history, evidence, and
  owner decisions.
- Generated fixture identity, logical time, deterministic ordering, expected
  outputs, and replay comparability.
- Department isolation, role checks, reason requirements, ETags, idempotency,
  and mandatory-review behavior across the scenario.
- Distinction among source facts, hypotheses, candidates, proposed alerts,
  reviews, actions, corrections, evidence references, and operational signals.
- Completeness and integrity of scenario results, evidence indexes, claim and
  limitation registers, operations records, and handoff artifacts.
- Consumer-visible HTTP, event, workflow, command, error, pagination,
  freshness, degradation, and UI-state semantics.
- Accessibility requirements and safe operator action availability.
- Boundary between final Phase 4 acceptance and any later Phase 5 authority.

## Trust Boundaries

1. Generated fixture author to scenario manifest.
2. Scenario manifest to logical clock, identifier, ordering, and seed provider.
3. Scenario orchestrator to accepted Phase 3 event ingress.
4. Each Phase 4 service boundary to the next service, event, or projection.
5. Domain state to transactional outbox and generated event observation.
6. API authentication to department and role authorization.
7. Mutable commands to ETag, reason, idempotency, and lifecycle enforcement.
8. Generated reference provider to candidate and review-handoff state.
9. Evidence references to provenance, integrity, correction, and reconstruction.
10. Operational signals to health and degradation projections.
11. Raw observations to normalized assertions and aggregate scenario result.
12. Scenario result to evidence index, claims, limitations, and acceptance.
13. Canonical H-CAM contracts to OpenAPI, AsyncAPI, CloudEvents, Arazzo, PROV,
    or other interoperability projections.
14. Phase 4 handoff producer to Phase 5 consumer and UI designer.
15. P4.7 final acceptance to a separately authorized Phase 5 planning gate.

## Actors

- P4.7 fixture author, implementation engineer, evidence preparer, owner, and
  future Phase 5 consumer.
- Generated scenario orchestrator, logical clock, identifier provider,
  assertion engine, projection generator, evidence packager, and verifier.
- Existing correlation, rule, alert, reference, investigation, operations,
  audit, security, and outbox components.
- Accidental developer, compromised fixture, malformed generated event,
  over-permissive adapter, stale contract, nondeterministic dependency,
  incomplete verifier, and unsupported-claim author.

## Threat Matrix

| ID | Threat | Failure mode | Required planning control |
| --- | --- | --- | --- |
| T-01 | Foundation bypass | Demonstration writes repositories or database rows directly and avoids service/API rules | Canonical step allowlist, service-boundary adapters, projection equivalence tests, no direct persistence steps |
| T-02 | Happy-path theater | One successful narrative hides denial, conflict, retry, correction, or degradation failures | Layered portfolio with required negative and recovery scenarios and no aggregate pass on skipped cases |
| T-03 | Nondeterministic clock | Wall time changes ordering, expiry, timers, freshness, or digests | Manifest-bound logical clock, explicit time zones, monotonic sequence, no implicit `now` |
| T-04 | Random identity drift | UUIDs or random seeds make clean runs incomparable | Manifest-derived namespace, seed, deterministic identifiers, and allowed-variance registry |
| T-05 | Ordering ambiguity | Equal timestamps or asynchronous delivery alter outcomes | Source sequence, observation time, receipt time, durable time, tie-break rule, and replay order |
| T-06 | Fixture substitution | A scenario runs with different fixtures than the sealed manifest | Per-file hashes, exact inventory, schema dialect, size/count bounds, and pre/post identity verification |
| T-07 | Real-data contamination | Fixture or output contains a real person, plate, camera, owner, case, or evidence identifier | Non-issuable synthetic namespaces, prohibited-pattern scan, source allowlist, and zero real-data authority |
| T-08 | Operational side effect | Generated scenario emits a notification, dispatch, control, provider, network, camera, or enforcement action | In-process generated adapters, default-off production prohibition, network denial, side-effect ledger requiring zero external effects |
| T-09 | Cross-department crossover | One step observes or mutates another generated department | Per-step principal/scope binding, negative isolation cases, RLS parity, and scoped output checks |
| T-10 | Review bypass | Proposed alert advances without required attributable human-review simulation | Mandatory generated reviewer role, quorum result, immutable review record, denied autonomous transition |
| T-11 | Candidate promoted to identity | Generated reference candidate is treated as confirmed identity | Candidate/identity type separation, abstention and contradiction scenarios, explicit human disposition requirement |
| T-12 | Lifecycle shortcut | Invalid alert or investigation transition is accepted | Revisioned state machines, allowed-from/allowed-to assertions, ETag conflict cases, append-only history |
| T-13 | Duplicate side effect | Replay or retry creates duplicate hypotheses, alerts, reviews, timeline entries, or outbox events | Semantic identity plus delivery idempotency, effect ledger, duplicate/replay scenarios |
| T-14 | Correction erasure | Correction rewrites prior events, evidence, decisions, or exports | Append-only revision graph, impact propagation, old/new visibility, reconstruction assertion |
| T-15 | Silent loss | Budget collapse, pagination, timeout, or dead letter omits work without evidence | Loss accounting, cursor completeness, terminal outcome inventory, no pass with unknown count |
| T-16 | Stale-state pass | Old candidate, rule, control, objective, or handoff snapshot is treated as current | Freshness fields, source revision binding, invalidation rules, stale scenario with explicit degraded result |
| T-17 | Aggregate masks layer failure | Final result is pass while one assertion family failed or skipped | Independent schema, policy, chronology, integrity, redaction, replay, and accessibility result sets |
| T-18 | Self-referential digest | Evidence package includes its own changing digest or ambiguous normalization | Acyclic component graph, explicit canonicalization, ordered inventory, detached package digest |
| T-19 | Verifier coupled to producer | The same faulty logic produces and accepts evidence | Frozen expected invariants, independent structural verifier, negative mutation fixtures, digest checks |
| T-20 | Missing evidence becomes pass | Absent, unreadable, stale, or unsupported artifact is omitted | Completeness enum, expected inventory, `unknown`/`incomplete` fail closed, explicit skip reasons |
| T-21 | Unsupported claim | Generated evidence is described as operational, accurate, compliant, conformant, scalable, or production-ready | Machine-readable claim registry, evidence class, prohibited-term checker, owner-reviewed limitations |
| T-22 | Projection drift | OpenAPI, AsyncAPI, Arazzo, CloudEvents, or PROV projection disagrees with canonical H-CAM semantics | Canonical source, versioned projection mappings, round-trip/semantic comparison, non-conformance label |
| T-23 | Event correlation collision | Consumer matches the wrong event, command, or scenario run | Typed occurrence ID, delivery ID, correlation ID, causation ID, scenario ID, and department scope separation |
| T-24 | False async completion | Workflow marks success when message send succeeds but processing or review has not completed | Explicit terminal observation, correlation match, timeout, success criteria, and durable outcome assertion |
| T-25 | Error disclosure | Problem details or UI errors expose raw exceptions, paths, identifiers, evidence, or security state | Closed problem types, safe parameters, size bounds, redaction before serialization, generic unknown failure |
| T-26 | Lost update | Phase 5 command contract omits ETag or handles conflict as success | Strong ETag/`If-Match`, 412 mapping, refresh/retry UX, immutable command receipt |
| T-27 | Pagination inconsistency | List pages duplicate, omit, or reorder records during changes | Stable sort key, opaque cursor, snapshot/freshness semantics, bounded page size, end/completeness state |
| T-28 | UI authority inflation | UI enables an action the principal, scope, state, or runtime gate does not allow | Server-authoritative action availability plus client denial handling; hidden buttons are not authorization |
| T-29 | Hidden degraded state | UI shows normal when data is stale, partial, delayed, disabled, or unavailable | Typed status/degradation banner, freshness, source coverage, unavailable actions, assistive announcement |
| T-30 | Alert fatigue or focus theft | Routine updates interrupt operators or overwhelm assistive technology | Severity and interruption policy, deduplication, non-modal status by default, alert dialog only for bounded confirmations |
| T-31 | Keyboard/focus trap | Dense list, grid, modal, or correction workflow is not operable without pointer input | Component-specific keyboard contract, visible focus, focus return, escape/cancel rules, native controls where possible |
| T-32 | Color-only meaning | Severity, confidence, status, or correction is conveyed only by color | Text/icon/shape semantics, accessible names, contrast and non-color assertions |
| T-33 | Compatibility surprise | Phase 5 consumer silently breaks after schema, enum, path, or event change | Change classification, version policy, contract snapshots, consumer matrix, deprecation and migration record |
| T-34 | Runbook cannot reconstruct | Operations pack lacks prerequisites, expected outputs, stop conditions, or cleanup | Typed runbook steps, preflight, bounded outputs, failure taxonomy, resume/cleanup and evidence checklist |
| T-35 | Acceptance overreach | P4.7 acceptance silently authorizes Phase 5 or operational use | Separate decisions, explicit non-authorizations, exact package digest, no inherited runtime authority |

## Mandatory Invariants

1. Every scenario input, clock value, identifier namespace, seed, policy
   revision, expected output, normalization, and allowed variance is explicit.
2. Generated fixtures use non-issuable identifiers and contain no camera,
   media, Government, police, private, biometric, owner, registration,
   watchlist, case, or evidence payload.
3. No scenario step can contact a network, provider, broker, workflow engine,
   camera, model, external process, container, cluster, or deployment target.
4. The canonical scenario uses accepted service boundaries; direct database or
   repository writes are not demonstration evidence.
5. Source occurrence identity, delivery idempotency, trace/correlation context,
   scenario-run identity, and evidence identity remain distinct.
6. Missing, skipped, stale, malformed, unverifiable, or incomplete evidence
   cannot produce pass.
7. Aggregate success requires every mandatory scenario and assertion layer to
   pass; optional projections report separately.
8. Mandatory human review remains required for police intelligence. Generated
   reviewer fixtures demonstrate contracts but grant no real authority.
9. Candidates, hypotheses, confidence, and alerts never establish identity or
   fact without the separately required review and evidence semantics.
10. Corrections and retractions append revisions and preserve prior source,
    decision, evidence, and export history.
11. HTTP mutations retain role, department, reason, ETag, idempotency, audit,
    and no-store requirements according to their accepted contracts.
12. Event ordering, correlation, causation, schema version, and delivery
    semantics are explicit for every handed-off event.
13. Canonical H-CAM contracts remain authoritative. Standards projections are
    versioned, optional, validated separately, and carry no automatic claim.
14. UI action availability is a projection of server authority and state, not
    a substitute for server enforcement.
15. Every UI state has visible text, programmatic status, keyboard/focus
    behavior, recovery action, and safe failure behavior where applicable.
16. Evidence packages are acyclic, canonically normalized, hash bound to an
    exact source commit, and independently checkable.
17. Every readiness statement is represented in the claims registry with an
    evidence class and limitations; unknown remains unknown.
18. P4.7 final acceptance closes only Phase 4. Phase 5 planning requires a new
    explicit owner authorization.

## Required Future Negative Tests

- Mutated fixture, schema, seed, clock, order, identifier namespace, policy
  revision, expected digest, or source commit stops before scenario execution.
- Direct persistence access, network socket, environment proxy, subprocess,
  provider, broker, workflow engine, camera, media, model, container, and
  Kubernetes access are denied and detected.
- Duplicate, out-of-order, late, conflicting, stale, unauthorized,
  cross-department, malformed, oversized, and unknown generated inputs produce
  their exact safe outcomes.
- Review omission, insufficient quorum, invalid role, absent reason, stale
  ETag, repeated idempotency key, invalid lifecycle transition, and open kill
  switch fail closed.
- Candidate contradiction, ambiguous candidate, no candidate, expired
  catalogue, provider-disabled state, and query timeout never confirm identity.
- Correction, retraction, merge, reopen, deletion simulation, hold conflict,
  export preview, and reconstruction preserve immutable chronology.
- Missing assertion family, skipped mandatory scenario, unaccounted loss,
  malformed evidence index, circular reference, digest mismatch, and stale
  verifier cannot result in pass.
- OpenAPI/event/workflow/UI projection mutation is detected against canonical
  contracts and cannot silently alter authority or required fields.
- UI contracts cover empty, partial, stale, degraded, denied, conflict,
  failure, recovery, and correction states as well as success.
- Keyboard-only, focus order, focus visibility, status announcement, label,
  error identification, non-color meaning, and target-size criteria are
  recorded for each applicable component; missing criteria remain incomplete.
- Final acceptance without exact evidence digest, source commit, limitation
  register, and explicit separate Phase 5 gate is rejected.

## Residual Risks

- Generated scenarios cannot prove real camera, network, model, operator,
  database-scale, hardware, accessibility-user, or incident behavior.
- In-process adapters can differ from HTTP, broker, process, or distributed
  failure semantics even when contracts match.
- Standards projections and validators can contain defects or lag current
  versions; canonical H-CAM semantics still require independent review.
- Automated accessibility checks cannot replace keyboard, screen-reader,
  low-vision, cognitive, and operator usability testing by qualified people.
- Hash integrity proves byte identity, not truth, legal admissibility,
  completeness, or safety of the represented claim.
- A consumer handoff can become stale immediately after accepted contracts
  change; compatibility monitoring and version governance remain necessary.
- Final Phase 4 acceptance cannot prove operational, production, legal,
  evidentiary, privacy, security, capacity, or deployment readiness.

These residual risks must remain visible in the claims and limitations
registers and in the Phase 5 handoff. Configuration cannot turn them into pass.
