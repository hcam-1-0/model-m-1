# Phase 4 Acceptance Checklist

Status: planning baseline prepared; all owner and implementation gates below
remain pending unless marked complete.

## Planning Baseline

- [x] Phase 3 closeout and event boundary verified at commit `3ca0436`.
- [x] Phase 4 mission, users, tiers, non-goals, and success definition drafted.
- [x] Correlation, rule, alert, provider, evidence, API, storage, and operations
  architecture drafted.
- [x] Frozen 100-point work breakdown and exact progress method recorded.
- [x] Eight owner decisions with A-D options and recommendations prepared.
- [x] Current primary-source technical references recorded.
- [x] Roadmap synchronized to the Phase 3 closeout and Phase 4 planning state.
- [x] `D-P4.0-001` through `D-P4.0-008` selected by the owner and reconciled as
  composite choices in the exact owner decision record.
- [ ] `D-P4-PLAN-ACCEPTANCE` recorded.
- [ ] Exact P4.0 implementation package prepared, reviewed, and digested.
- [ ] Exact `D-P4.0-START` authorization recorded.

## P4.0 Contracts And Guardrails

- [ ] Correlation-hypothesis and evidence-reference schemas are executable.
- [ ] Occurrence, observation, receive, durable-record, and correction times are
  distinct, bounded, and deterministic under replay.
- [ ] The versioned GeoJSON/API and PostGIS storage contract rejects invalid,
  ambiguous, oversized, or unauthorized geometry and transforms.
- [ ] Provenance entities, activities, agents, derivations, and integrity
  references are typed without claiming formal W3C PROV conformance.
- [ ] Alert aggregate, lifecycle, and domain-event schemas are executable.
- [ ] Rule, provider, query, timeline, review, and retention schemas are
  executable.
- [ ] Canonical serialization and deterministic generated fixtures pass.
- [ ] Strict-producer/compatible-consumer and major-version rules pass.
- [ ] Media, credentials, biometric, unrestricted provider, Government, and
  identity-assertion fields fail negative tests.
- [ ] Department scope, permissions, ETags, reasons, audit, and no-store
  behavior pass.
- [ ] PostgreSQL row security is forced and tested as defense in depth; product
  roles cannot own protected tables or use superuser/`BYPASSRLS` privileges.
- [ ] Default-off and production-forbidden activation is enforced.
- [ ] P4.0 evidence and owner acceptance are recorded.

## P4.1 Correlation Foundation

- [ ] Ingress validates Phase 3 envelopes, event versions, size, and policy.
- [ ] At-least-once duplicates cannot duplicate domain effects.
- [ ] Partition, event-time, watermark, lateness, gap, and conflict semantics
  pass exact goldens.
- [ ] Windows and per-key state are bounded with no silent eviction.
- [ ] The deterministic CPU lane passes exact replay, while every optional AMEC
  lane has typed inputs, outputs, availability, lineage, and resource bounds.
- [ ] Model-first mode can only propose candidates and cannot bypass
  deterministic prohibitions or run outside generated shadow evaluation.
- [ ] The hypothesis graph is canonical; flat groups are digest-bound,
  rebuildable projections with no additional conclusions.
- [ ] Hypotheses contain positive, contradicting, missing, and stale evidence.
- [ ] Confidence and uncertainty are versioned and cannot establish identity.
- [ ] Expiry, supersession, retraction, and correction preserve history.
- [ ] Replay is deterministic across processes and concurrent PostgreSQL
  workers.
- [ ] P4.1 owner acceptance is recorded.

## P4.2 Rule Authoring And Evaluation

- [ ] Visual documents compile to one canonical typed AST.
- [ ] Typed temporal nodes cover the approved sequence and aggregate semantics.
- [ ] CEL context, variables, functions, types, cost, depth, and size are closed.
- [ ] CEL has no network, file, SQL, secret, camera, dispatch, or enforcement
  access.
- [ ] Rule versions, digests, approvals, schedules, and rollback are immutable.
- [ ] Shadow rules are visibly non-operational and cannot create operational
  alerts, contact unauthorized providers, or change routing.
- [ ] Generated temporal, schedule, DST, replay, abuse, and overload tests pass.
- [ ] P4.2 owner acceptance is recorded.

## P4.3 Alert Lifecycle And Orchestration

- [ ] Proposed-alert IDs and dedupe keys are deterministic.
- [ ] Redelivery and concurrent workers cannot create duplicate alerts.
- [ ] Every lifecycle transition has allowed actors, reasons, ETags, and events.
- [ ] Priority, severity, confidence, and disposition remain separate.
- [ ] Suppression, escalation, timers, merge, reopen, and correction are
  deterministic.
- [ ] Per-rule, department, queue, and system alert budgets plus incident-level
  collapse preserve counts and representative evidence under overload.
- [ ] No lifecycle state or rule can directly trigger enforcement.
- [ ] Police-intelligence alerts are `mandatory_review`; generated or
  system-health automation cannot reclassify them, and future autonomous action
  remains absent or hard-disabled.
- [ ] Transactional aggregate/outbox consistency and recovery drills pass.
- [ ] P4.3 owner acceptance is recorded.

## P4.4 Authorized Reference Integrations

- [ ] Generated provider uses only invented, non-issuable records.
- [ ] Typed secret-provider and exact-destination policies fail closed.
- [ ] Credentials and raw provider material never enter APIs, database rows,
  logs, metrics, audit, evidence, or exceptions.
- [ ] Request and response type, size, timeout, concurrency, TLS, redirect,
  proxy, and field policies pass.
- [ ] Freshness, outage, partial, malformed, unauthorized, and revocation states
  are explicit.
- [ ] Candidate matching is calibrated, contradiction-aware, and can abstain.
- [ ] Human confirmation is required; one candidate cannot establish identity.
- [ ] No external provider is contacted under Tier A.
- [ ] The generic transport envelope accepts no arbitrary runtime destination,
  credential, query, or response schema and is tested only with local generated
  simulators.
- [ ] P4.4 generated-only owner acceptance is recorded.

## P4.5 Investigation Timeline And Evidence

- [ ] Facts, hypotheses, reviews, actions, and corrections are distinct types.
- [ ] Timeline entries are append-only and attributable.
- [ ] Evidence references include immutable source identity and integrity state.
- [ ] Corrections never rewrite source evidence or prior decisions.
- [ ] Retractions and corrections create attributable downstream revisions for
  affected hypotheses, alerts, timelines, exports, and indexes.
- [ ] Retention classes, hold overlay, deletion proof, and access audit pass.
- [ ] Export is purpose bound, authorized, integrity protected, and audited.
- [ ] Media is referenced, not copied, by default.
- [ ] P4.5 owner acceptance is recorded.

## P4.6 Operations, Security, And Scale

- [ ] Low-cardinality metrics contain no sensitive identifiers.
- [ ] Traces, operational logs, security logs, audit, and evidence are separated.
- [ ] Queue lease, retry, dead-letter, circuit-breaker, and recovery tests pass.
- [ ] Department isolation and cross-scope access tests fail closed.
- [ ] Application authorization and direct database row-security tests agree,
  including forced-policy and privileged-role misuse cases.
- [ ] Rule, event, provider, and timeline abuse cases pass.
- [ ] Dependency, artifact, license, SBOM, and vulnerability evidence is sealed.
- [ ] Kill switches and backup/restore drills pass.
- [ ] Generated C1/C10/C50 evidence records exact hardware and limitations.
- [ ] P4.6 owner acceptance is recorded.

## P4.7 Final Acceptance And Phase 5 Handoff

- [x] Generated end-to-end event, hypothesis, alert, review, and timeline
  scenario is reproducible.
- [x] Evidence index and known-limitations register are complete.
- [x] Operator API contracts, list/detail states, commands, errors,
  accessibility, and degradation states are handed to Phase 5.
- [x] No claim exceeds generated-only evidence.
- [x] Owner accepts the exact P4.7 evidence package and completes Phase 4.

Phase 5 planning requires a separate explicit owner authorization after Phase
4 acceptance; it is not implied by this checklist.

## Gates Outside This Baseline

- [ ] Real provider purpose and organizational/legal authority.
- [ ] Applicable Indian legal commencement, exemptions, electronic-record
  procedure, retention, and evidentiary requirements reviewed by authorized
  legal and policy owners.
- [ ] Exact provider fields, destination, credentials, retention, and incident
  response.
- [ ] Owned-lab participant, runtime, event source, and data authorization.
- [ ] Operational alert activation and control-room policy.
- [ ] Dispatch or enforcement integration.
- [ ] Government/private data, camera/media, production, and deployment.

These are intentionally open future gates, not evidence that the generated
Tier A plan is incomplete.
