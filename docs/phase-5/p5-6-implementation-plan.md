# P5.6 Bounded Implementation Plan

Status date: 2026-09-10

Status: proposed only; owner decisions, reconciled acceptance, and exact start authorization pending

## Goal

Build generated-only, functionally complete Admin Center, Security Center, and
Platform Operations workspaces over accepted H-CAM contracts without adding a
real administrative mutation, secret, provider, telemetry, scanner, recovery,
camera, model, infrastructure, container, Kubernetes, or deployment path.

## Entry Gates

Implementation may begin only after:

1. all twelve `D-P5.6-001` through `D-P5.6-012` decisions are explicit;
2. a reconciled P5.6 planning package is generated and validated;
3. the owner accepts that exact planning package and digest;
4. a separate start package binds exact inputs, changed paths, dependencies,
   fixtures, test counts, runtime bounds, stop conditions, and prohibitions;
5. the owner explicitly accepts the exact start package.

Planning authorization alone does not satisfy these gates.

## Frozen Product Weight

| Workstream | Purpose | Product points |
| --- | --- | ---: |
| P5.6-W1 | Shared administration/security/operations contracts and fixtures | 1.5 |
| P5.6-W2 | Admin Center governance and approval experience | 1.5 |
| P5.6-W3 | Security Center posture, access, audit, and compliance experience | 1.5 |
| P5.6-W4 | Platform Operations health, queues, SLO, recovery, and topology experience | 1.5 |
| P5.6-W5 | Authorization, SoD, concurrency, redaction, and non-effective control safety | 1.25 |
| P5.6-W6 | Cross-portal handoffs, accessibility, localization, and dynamic profiles | 0.75 |
| P5.6-W7 | Threat, dependency, build, browser, compatibility, and regression validation | 1.0 |
| P5.6-W8 | Evidence sealing and exact owner acceptance | 1.0 |
| Total | P5.6 | 10.0 |

Technical implementation is capped at **9/10 (90.0000%)**. The final
**1/10 (10.0000%)** requires exact owner acceptance of the sealed P5.6
evidence package. Planning and decision selection award no product points.

Current state remains P5.6 **0/10 (0.0000%)** and Phase 5 **78/100
(78.0000%)**.

## W1: Shared Contracts And Fixtures

Proposed future packages:

- `admin-contracts`: organization, department, identity, roles, capabilities,
  policy, change request, approval, configuration, provider, feature, profile,
  and retention projections;
- `security-contracts`: posture, access assurance, denial, session/auth,
  audit-reference, compliance, exception, attestation, and supply-chain
  projections;
- `operations-contracts`: service, dependency, queue, worker, storage,
  database, event bus, media edge, AI runtime, SLO, budget, degradation,
  maintenance, recovery, capacity, and topology projections;
- `governance-domain`: typed lifecycle, revision, validation, comparison,
  impact, SoD, and safe action-state functions;
- `platform-operations-domain`: health, freshness, completeness, unknown,
  dependency, and recovery view functions;
- `admin-security-operations-fixtures`: exact generated C1/C10/C50 and hostile
  cases.

Contract requirements:

- strict versioned discriminated unions;
- bounded strings, arrays, graph nodes/edges, windows, page sizes, and totals;
- opaque identifiers and references;
- source, observation/record time, freshness, completeness, revision, ETag,
  policy revision, limitations, and allowed actions;
- typed safe problem details;
- no credential, secret value, token, raw log body, private record, media,
  model artifact, or executable instruction field;
- schema rejection for unknown command fields and dangerous URL shapes.

## W2: Admin Center

Implement generated pages for:

1. overview;
2. organizations and departments;
3. users, memberships, sessions, and access reviews;
4. roles, permissions, capability matrix, and SoD;
5. policy and administrative change requests;
6. cameras and streams governance;
7. integrations, providers, and opaque secret refs;
8. feature flags, configuration, and kill-switch history;
9. resource profiles, model lanes, and deployment profiles;
10. retention policy projections.

All change workflows terminate in generated non-effective receipts or explicit
unavailable states. No Apply, Reveal, Test Connection, Rotate, Deploy, Execute,
Delete, Restore, Activate, or Direct Control command exists.

## W3: Security Center

Implement generated pages for:

1. security posture;
2. access assurance and RLS parity;
3. denied and anomalous activity;
4. privileged activity and break-glass unavailable state;
5. session and authentication posture;
6. immutable audit-reference explorer;
7. policies, exceptions, attestations, and evidence refs;
8. supply-chain inventory, SBOM, license, vulnerability, and provenance;
9. provider, destination, and secret-reference posture;
10. disabled future SOC handoff.

Security language must remain qualified. No event, score, denial, finding,
integrity observation, or missing finding is shown as attack, identity,
criminality, guilt, compliance, safety, or proof.

## W4: Platform Operations

Preserve all P5.3 Operations camera/live pages. Add a separate Platform
Operations route family for:

1. overview;
2. services and dependencies;
3. queues, workers, retries, leases, dead letters, and circuits;
4. database, storage, event bus, caches, and media edge;
5. AI runtime, scheduler, model-lane, profile, bypass, and saturation;
6. SLO, SLI, error budgets, and data quality;
7. degradation and kill-switch effective projections;
8. maintenance, backup, restore evidence, and disaster-recovery previews;
9. C1/C10/C50 capacity evidence;
10. standalone, GPU-lab, server, and Kubernetes topology projections.

No live telemetry backend, queue, process, storage, database console, broker,
camera, model runtime, backup, cluster, or infrastructure command is added.

## W5: Safety And Governance

Implement and test:

- RBAC plus constrained ABAC projection and default-deny behavior;
- organization and department scope propagation;
- server capability required for every route, query, detail, and command;
- static/dynamic SoD and self-approval denial;
- strong ETag, entity revision, policy revision, idempotency, conflict
  comparison, and explicit reconsideration;
- step-up-required but unavailable state;
- no automatic consequential-command retry;
- draft field minimization and teardown on logout/context change;
- secret/token/private-data redaction at contract, display, problem, audit, and
  telemetry boundaries;
- signal-lane separation;
- non-operative labels and absence of executor adapters;
- unsupported-claim checks.

## W6: Handoffs, Accessibility, And Profiles

- capability-filtered navigation and deep-link denial;
- exact Admin <-> Security <-> Operations <-> Command handoffs with refetch;
- focus return, route title, breadcrumbs, loading/error summary, and keyboard
  workflows;
- table/list equivalents for every chart, tree, matrix, graph, and topology;
- reflow, zoom, target size, focus-visible/not-obscured, reduced-motion, and
  screen-reader status behavior;
- translatable descriptions with stable identifiers and reason codes;
- narrow, desktop, wide, and multi-monitor layouts;
- low-resource, enhanced, control-room, GPU-lab, server, and Kubernetes
  profile rendering equivalence;
- authority, truth, scope, and security invariance across every profile.

## W7: Validation

### Frozen generated cases

Exactly **1,120** generated contract cases are proposed:

| Family | Cases |
| --- | ---: |
| Organization, identity, membership, role, capability, and session | 176 |
| Policy, administrative changes, approval, SoD, ETag, and idempotency | 192 |
| Camera/stream, provider, secret-ref, feature, config, profile, and retention | 176 |
| Security posture, denials, audit refs, compliance, exceptions, and attestations | 160 |
| Supply chain, service health, queues, workers, circuits, and degradation | 160 |
| SLO, budgets, storage, recovery, maintenance, capacity, and topology | 128 |
| Cross-department, hostile input, redaction, overclaim, and signal separation | 80 |
| Accessibility, handoff, state, and cross-profile equivalence | 48 |
| Total | 1,120 |

### Workload layers

- **C1:** one department/service/configuration domain for deterministic basic
  behavior;
- **C10:** ten departments/services with mixed conflict, stale, partial,
  denied, and degraded states;
- **C50:** fifty departments/services/configuration records with cursor
  pagination, bounded aggregates, tables, and profile adaptation.

These are UI and contract workloads, not hardware or production capacity
tests.

### Test layers

- schema and generated vector tests;
- pure domain-function tests;
- component and route-state tests;
- department, role, purpose, SoD, deep-link, and teardown tests;
- ETag, revision, idempotency, conflict, event-gap, and refetch tests;
- redaction, hostile input, bounded output, and unsupported-claim tests;
- all visual/table semantic equivalence tests;
- loopback-only browser tests for keyboard, focus, reflow, responsive, profile,
  multi-monitor, denial, stale, partial, failure, and recovery states;
- all portal type checks/builds using the existing lockfile;
- dependency, lockfile, SBOM, migration, accepted-history, and changed-path
  checks;
- complete repository regression.

### Environment limitations

Evidence must explicitly record whether PostgreSQL, browser matrix, local
runtime, vulnerability refresh, hardware profile, container, Kubernetes,
backup/restore, and production environment validation were not run. Missing
environment validation cannot be represented as passed.

## W8: Evidence And Acceptance

Seal:

- implementation and evidence commit identities;
- exact component list, bytes, SHA-256, and canonical digest;
- dependency, lockfile, SBOM, and source boundary;
- generated-case manifest and results;
- focused, all-portal, browser, compatibility, and repository regression
  results;
- 48 producer gaps and 72-threat coverage;
- claims and limitations;
- exact progress transition from 78/100 to the technical cap and then, only
  after owner acceptance, to 88/100.

## Stop Conditions

Future work must stop closed on:

- any unapproved path, dependency, lockfile, migration, route, or producer;
- any network, provider, camera, media, map/tile, model, artifact, Government,
  private, identity, credential, or secret access;
- any real administrative mutation, operational action, telemetry, scan,
  backup, restore, recovery, infrastructure, container, Kubernetes, or
  deployment execution;
- any client-authoritative permission, cross-department leakage, self-approval,
  secret/raw-log retention, executor path, or unsupported claim;
- generated case count, security, accessibility, compatibility, build,
  regression, immutable-history, evidence, or digest failure;
- any remote Git action not separately and explicitly authorized.

## Delivery Sequence

1. W1 contracts, domains, fixtures, and generated cases.
2. W2 Admin Center pages and generated governance workflows.
3. W3 Security Center pages and assurance workflows.
4. W4 Platform Operations pages while preserving P5.3 camera operations.
5. W5 security, SoD, concurrency, redaction, and non-effective controls.
6. W6 handoffs, accessibility, localization, responsive layouts, and profiles.
7. W7 complete layered validation and bounded remediation.
8. W8 evidence seal, exact acceptance proposal, and owner gate.

This plan is non-effective. It authorizes no implementation action.
