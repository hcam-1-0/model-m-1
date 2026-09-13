# Phase 5 Operator Application Implementation Plan

Status: P5.0 through P5.7 complete and owner accepted; Phase 5 complete

## Objective

Deliver a secure, accessible, modular H-CAM operator application that consumes
accepted platform contracts across command, operations, camera/live,
intelligence/review, investigation/evidence, administration, and security
workflows. The plan preserves a functionally complete low-resource mode and
adds bounded higher-density behavior for capable workstations.

## Frozen Phase 5 Weights

| Subphase | Weight | Completion condition |
| --- | ---: | --- |
| P5.0 Product, UX, contracts, and architecture | 8 | Exact roles, journeys, portal topology, design/accessibility/security contracts, gap plan, dependencies, generated fixtures, and start package are implemented, validated, and owner accepted |
| P5.1 Shared application foundation | 12 | Independently buildable app shell, design system, typed API/session/state/error/event foundations, localization, observability, and generated test harness meet all gates |
| P5.2 Command and situational awareness | 12 | Generated command overview, bounded GIS layers, workload/coverage/degradation states, drill-down, and accessible alternatives meet all gates |
| P5.3 Camera and live monitoring workspace | 16 | Camera/stream/capability workflows and authorized generated-media playback adapters, layouts, admission, teardown, and degraded modes meet all gates |
| P5.4 Intelligence, alerts, and human review | 15 | Hypothesis/run/graph/rule/candidate/alert/review/quorum/lifecycle workflows preserve uncertainty, concurrency, and mandatory human authority |
| P5.5 Investigation and evidence | 15 | Timeline/reconstruction/correction/relationship/evidence/integrity/provenance/preview workflows preserve chronology and source-reference boundaries |
| P5.6 Administration, security, and operations | 10 | Accepted configuration and read-only governance surfaces enforce least privilege, lane separation, auditability, and unavailable-capability rules |
| P5.7 Quality, scale, and final acceptance | 12 | Cross-portal E2E, accessibility, browser, localization, responsive, performance, security, resilience, compatibility, build, and exact owner acceptance evidence passes |

Total: **100 points**. Frozen items receive no partial product credit. Any
scope or weight change requires an explicit rebaseline before reporting a new
percentage.

## Current Exact Progress

- Planning authority: **1/1 (100.0000%)**.
- Repository and handoff inventory: **1/1 (100.0000%)**.
- Official primary-source research: **1/1 (100.0000%)**.
- P5.0 planning package: **accepted** as `P5.0-PLANNING-R2`.
- P5.0 start package: **owner-authorized** at exact SHA-256
  `66F40E71B2E96F2C61C267EF5A14CD709692A0C389AC23560651BC2B9C38B7F8`.
- P5.0 generated-only technical implementation: complete at commit `8d6ff70`.
- P5.0 evidence package: sealed and exactly owner accepted.
- P5.0 product: **8/8 (100.0000%)**, change **+12.5000 percentage points**.
- P5.1 technical implementation: complete at commit `394e9d2`; exact exit
  acceptance effective.
- P5.1 product: **12/12 (100.0000%)**, change **+12.5000 percentage points**
  from its technical cap.
- P5.2 technical implementation and exact exit acceptance: W1-W8 complete.
- P5.2 product: **12/12 (100.0000%)**, change **+8.3333 percentage points**
  from the 91.6667% technical-cap state.
- P5.3 implementation, evidence sealing, and exact exit acceptance: W1-W8
  complete against technical commit `9d1604a62e4823644064e26d3b11771f8ae526fa`.
- P5.3 product: **16/16 (100.0000%)**, change **+9.3750 percentage points**
  from the 90.6250% technical-cap state.
- P5.4 W1-W8: technically complete and exactly owner accepted against technical
  commit `fc5b7f9aa682b68c83e53c558e8c08bf35ee7480` and evidence-seal commit
  `841f6da340e9bf28ea71b6c1da734f96c97499aa`.
- P5.4 product: **15/15 (100.0000%)**, change **+6.6667 percentage points**
  from the 93.3333% technical-cap state.
- P5.5 planning: **8/8 (100.0000%)**, change **+100.0000 percentage points**;
  owner decisions **12/12 (100.0000%)**, change **+100.0000 percentage
  points**, and product **15/15 (100.0000%)**, change **+6.6667 percentage
  points** from its technical cap.
- Exact `D-P5.5-ACCEPTANCE` is effective and completes P5.5 only.
- P5.6 planning: **8/8 (100.0000%)**, owner decisions **12/12 (100.0000%)**,
  and product **10/10 (100.0000%)**, change **+10.0000 percentage points**
  from its technical cap.
- Phase 5 product: **88/100 (88.0000%)**, change **+1.0000 percentage point**
  from the P5.6 technical-cap state.
- Exact `D-P5.6-ACCEPTANCE` is effective and completes P5.6 only.
- P5.7 product: **12/12 (100.0000%)**, change **+8.3333 percentage points**
  from its technical cap.
- Phase 5 product: **100/100 (100.0000%)**, change **+12.0000 percentage
  points** from the previously accepted state and **+1.0000 percentage point**
  from the P5.7 technical-cap state.
- Exact `D-P5.7-ACCEPTANCE` is effective and completes P5.7 and Phase 5 only.

Planning and research award no product points.

## Preconditions For Any Implementation

1. Owner selects `D-P5.0-001` through `D-P5.0-012`. **Complete.**
2. Selections are reconciled into a non-effective planning package.
   **Complete.**
3. Owner accepts that exact planning package and SHA-256. **Complete.**
4. A P5.0 start package freezes exact implementation paths, dependencies,
   versions, generated fixtures, commands, resource bounds, changed historical
   checks, evidence, and stop conditions. **Complete as a non-effective
   proposal.**
5. Owner authorizes the exact start package. **Complete.**
6. Every required producer-contract gap used by the slice is accepted or the
   corresponding feature remains blocked.

No framework recommendation or planning document satisfies these conditions.

## P5.0 Product, UX, Contracts, And Architecture

### P5.0-A Canonical UI Contracts

Proposed implementation:

- portal, route, view, panel, action, field, filter, sort, pagination, query,
  event, command, state, error, focus, keyboard, localization, capability,
  telemetry, and compatibility contracts;
- strict bounds and unknown-field policy;
- links to producer operation/event and schema versions;
- generated examples with non-issuable identifiers;
- static prohibition of real data, media, locators, tokens, secrets, and
  operational actions.

Completion evidence: schema catalogue, generated boundary vectors, contract
snapshots, producer-coverage matrix, and prohibited-field scan.

### P5.0-B Information Architecture And Journeys

- final portal topology and navigation;
- role and capability matrix;
- route and safe URL-state contract;
- the camera-to-live, alert-review, review-to-investigation,
  correction/reconstruction, degradation, and session-expiry journeys;
- loading through recovery behavior for every view;
- low-resource, enhanced, and control-room workspace projections.

Completion evidence: route inventory, journey state machines, action/role
matrix, content model, and generated walkthroughs.

### P5.0-C Design And Accessibility Foundation

- semantic tokens and themes;
- component interaction specifications;
- density, responsive, multi-monitor, zoom, and localization behavior;
- WCAG 2.2 AA target matrix and APG-informed keyboard/focus contracts;
- map, graph, timeline, data-grid, and media alternatives.

Completion evidence: token contracts, component acceptance matrix, automated
static checks, and explicit future manual-evidence requirements.

### P5.0-D Security And Architecture Seal

- accepted frontend architecture and dependency proposal;
- BFF/session, CSRF, CSP, browser storage, event, telemetry, GIS, and media
  boundaries;
- threat-model control mapping;
- exact implementation sequence and dependency graph;
- P5.0 evidence package and owner acceptance.

Technical completion earned **7/8** and exact evidence acceptance earned the
final point. P5.0 is **8/8 (100.0000%)** and Phase 5 is **8/100 (8.0000%)**.

## P5.1 Shared Application Foundation

Planning R1, start package `P5.1-START-R0`, and evidence package
`P5.1-EVIDENCE-PACKAGE-R0` are owner accepted. W1 through W8 are complete at
technical commit `394e9d2`. Product progress is **12/12 (100.0000%)** and
Phase 5 reached **20/100 (20.0000%)** at P5.1 acceptance. P5.2 planning,
all twelve owner decisions, planning acceptance, start authorization, bounded
generated-only implementation, validation, evidence sealing, and exact exit
acceptance are now complete. P5.2 is **12/12 (100.0000%)** and Phase 5 is
**32/100 (32.0000%)**. P5.3 planning and exact start authorization are
complete; bounded generated-only product implementation is active.

### Planned Work

- workspace, package manager, lockfile, and independently buildable portal
  entries;
- shared shell, routing, session, department context, error boundaries, and
  application state banners;
- design tokens and core accessible components;
- typed contract/API client and safe problem mapping;
- server-state cache with operation-specific retry/freshness rules;
- event invalidation interface with polling simulator;
- localization keys and English/Gujarati/Hindi generated catalogues;
- client capability resolver and safe-minimum fallback;
- low-cardinality client observability contract;
- generated mock service from accepted API contracts;
- unit, component, accessibility-static, contract, and browser smoke harness.

### Exit Criteria

- all portal entries build independently;
- no portal-to-portal imports;
- all network calls pass through the typed client;
- all blocked destinations and persistent storage APIs fail static policy;
- every core component passes keyboard/focus/state tests;
- no protected field enters URL, storage, log, or telemetry fixtures;
- low-resource profile remains functionally complete;
- exact dependency, license, SBOM, vulnerability, bundle, and provenance
  evidence is recorded within later authority.

The technical implementation earns 10.5 points. Exact acceptance earns the
final 1.5 points and reaches Phase 5 **20/100 (20.0000%)**.

## P5.2 Command And Situational Awareness

Planning package `P5.2-PLANNING-R1`, start package `P5.2-START-R0`, and
evidence package `P5.2-EVIDENCE-PACKAGE-R0` are owner accepted. W1 through W8
are complete against technical commit `6b1a649bd6855efbdcfb6b7c79d708981077864b`.
Product progress is **12/12 (100.0000%)** and Phase 5 is **32/100 (32.0000%)**.

### Planned Work

- operations/degradation summary;
- review, alert, investigation, camera, and stream workload projections;
- bounded 2D map with camera and generated intelligence layers;
- coverage and health aggregates;
- timeline/time-window controls;
- drill-down to authoritative lists;
- map table/list alternative;
- safe empty/partial/stale/degraded/denied/failure/recovery states;
- future shift-handoff placeholder blocked until its contract exists.

### Exit Criteria

- every aggregate exposes source window, freshness, completeness, and drill-
  down definition;
- map viewport and feature bounds pass generated scale tests;
- map failure leaves lists usable;
- no client-only operational threat score or identity conclusion;
- keyboard, zoom, non-color, contrast, and reduced-motion evidence passes.

Acceptance earns Phase 5 points **21 through 32**, reaching **32.00%**.

## P5.3 Camera And Live Monitoring Workspace

Planning authority, all twelve owner choices, reconciled planning acceptance,
exact `D-P5.3-START`, implementation, validation, evidence sealing, and exact
`D-P5.3-ACCEPTANCE` are effective. W1 through W8 are complete against technical
commit `9d1604a62e4823644064e26d3b11771f8ae526fa`. P5.3 is **16/16 (100.0000%)**
and Phase 5 reached **48/100 (48.0000%)** before P5.4.

### Planned Sequence

1. Camera catalogue/detail, stream health, probe, and capability views using
   generated metadata only.
2. Browser-safe stream projection that excludes locator and secret material.
3. Playback-session client and synthetic media simulator only after separate
   generated-media authority.
4. HLS adapter and browser/codec matrix.
5. Provisional WebRTC/WHEP low-latency adapter with version pin and fallback.
6. Profile-based multi-tile admission, quality, reconnect, and teardown.
7. Workspace layout persistence only after its storage contract is accepted.

### Exit Criteria

- no raw camera, ONVIF, RTSP, locator, secret, or long-lived token reaches the
  browser;
- no recording, snapshot, download, print, export, or background persistence;
- single and multi-view state machines pass expiry, denial, stall, reconnect,
  profile downgrade, logout, and scope-change tests;
- frame and player containers retain stable dimensions;
- synthetic C1/C4/C10 profile evidence is recorded on declared hardware only;
- no claim about real-camera compatibility or operational latency.

Acceptance earns Phase 5 points **33 through 48**, reaching **48.00%**.

Technical validation earned points **33 through 46.5**. Exact exit acceptance
earned the remaining 1.5 points, reaching **48.0000%**, without starting P5.4.

## P5.4 Intelligence, Alerts, And Human Review

Technical implementation and validation are complete at commit
`fc5b7f9aa682b68c83e53c558e8c08bf35ee7480`. Exact `D-P5.4-ACCEPTANCE` is
effective for the sealed evidence package. W1-W8 earn **15/15 (100.0000%)**;
Phase 5 is **63/100 (63.0000%)**. P5.5 remains closed.

### Planned Work

- hypothesis and correlation-run queues;
- graph, spatial projection, revisions, and rule explanation;
- proposed-alert list/detail/lifecycle;
- candidate-set uncertainty, contradiction, and abstention;
- mandatory review and quorum;
- reason, ETag, idempotency, conflict, and resubmission flow;
- correction and event-driven refresh;
- accessible graph and list/table alternatives.

### Exit Criteria

- source observation, hypothesis, candidate, alert, review, and lifecycle are
  visually and semantically distinct;
- no score is presented as identity or guilt;
- conflicts never auto-resubmit;
- events only invalidate and HTTP state confirms results;
- every denied/partial/stale/degraded/corrected state passes generated tests;
- no notification, dispatch, enforcement, or external action exists.

Acceptance earns Phase 5 points **49 through 63**, reaching **63.00%**.

Technical evidence earned points **49 through 62**. Exact exit acceptance
earned point **63** and completed P5.4 without starting P5.5.

## P5.5 Investigation And Evidence

Exact `D-P5.5-PLAN-AUTH` is effective. Official primary-source research,
architecture, workflows, contract-gap analysis, threat analysis, dependency
evaluation, owner options, and the bounded implementation plan are complete.
Owner decisions are selected as `A/A/A/A/A/A/A/A/A/A/A/A`; exact
`D-P5.5-PLANNING-R1-ACCEPTANCE` and exact `D-P5.5-START` are effective. The
bounded local generated-only product implementation is technically complete
at commit `b0ecf20dcaf36aae9856b3802d037656f0b053e7`. Evidence package
SHA-256 is
`9E580AC0302C5F7368C21E884945DB0FAD94442A0D20B8179AAEE8AD4C099EDA`;
canonical component digest is
`78ACB49CD110D2643688DAA05A6F1D1515C0FA6BE2EF9858C4315EB5A4D426A8`.
Exact `D-P5.5-ACCEPTANCE` is effective. Product progress is **15/15
(100.0000%)** and Phase 5 is **78/100 (78.0000%)**. Exact
`D-P5.6-PLAN-AUTH` opens P5.6 planning only; the P5.6 planning set is complete,
all twelve owner decisions are selected as `A/A/A/A/A/A/A/A/A/A/A/A`, and
exact `D-P5.6-PLANNING-R1-ACCEPTANCE` is effective. The non-effective bounded
start package is accepted under exact `D-P5.6-START`.

### Implemented Work

- timeline list/detail and typed entry forms;
- durable order and event-time views;
- reconstruction through revision;
- corrections, retractions, reviews, and relationships;
- evidence reference list/detail, integrity, and provenance;
- generated hold/retention/deletion/export preview views;
- source-resolution, media, legal-policy, deletion, and export actions remain
  unavailable.

### Exit Criteria

- prior and current states remain linked and visible;
- correction propagation and reconstruction are deterministic;
- no source evidence is copied or rendered;
- integrity is never presented as truth or legal admissibility;
- timeline virtualization preserves focus, reading order, and bounded page
  navigation;
- all preview-only controls state their non-operative status.

Acceptance earned Phase 5 points **64 through 78**, reaching **78.00%**.
Technical evidence earned points **64 through 77**. Exact owner acceptance
earned point **78** and completed P5.5.

## P5.6 Administration, Security, And Operations

Exact `D-P5.6-PLAN-AUTH` is effective. Official primary-source research,
three-portal architecture, workflows, 48 producer gaps, 72 threats, dependency
evaluation, twelve owner options, and the eight-workstream bounded plan are
complete. Planning is **8/8 (100.0000%)** and owner decisions are **12/12
(100.0000%)**. The bounded generated-only implementation and validation are
technically complete at commit `8c3645f1d91b6d444a63d5534a322ba181a931f1`.
Exact `D-P5.6-ACCEPTANCE` is effective. P5.6 is **10/10 (100.0000%)**, change
**+10.0000 percentage points** from its technical cap, and Phase 5 is **88/100
(88.0000%)**, change **+1.0000 percentage point** from the P5.6 technical-cap
state.

See the [detailed P5.6 plan](p5-6-implementation-plan.md),
[reconciled R1 plan](p5-6-reconciled-planning-r1.md), and
[current status R26](current-status-r26.md). Exact reconciled planning
acceptance and `P5.6-START-R0` are effective. See the generated-only
[implementation](p5-6/implementation.md), [validation](p5-6/validation.md),
[evidence](p5-6/evidence.md), and [exit proposal](p5-6/acceptance-proposal.md).

### Implemented Work

- read-only operations, security, objectives, budgets, degradation, recovery,
  capacity, supply-chain, and control views;
- accepted camera/stream/rule/provider configuration surfaces where contracts
  exist;
- audit and identity administration placeholders remain blocked pending APIs;
- role/action separation and attributable change previews;
- compatibility, stale evidence, disabled features, and kill-switch state;
- unified search remains a derived, minimized, disabled capability unless
  separately accepted.

All listed capabilities are generated, non-effective projections. No backend
producer, real administrative mutation, secret operation, telemetry backend,
scanner, recovery action, infrastructure control, or deployment was added.

### Exit Criteria

- operational, security, audit, and evidence lanes remain visibly separate;
- read-only is the default;
- unavailable management domains cannot be activated in client code;
- privileged commands require exact current server capability, reason, ETag,
  confirmation, and accepted outcome;
- no real provider, credential, scanner, backup, restore, cluster, model, or
  deployment control exists.

Acceptance earns Phase 5 points **79 through 88**, reaching **88.00%**.

## P5.7 Quality, Scale, And Final Acceptance

Planning is complete under exact `D-P5.7-PLAN-AUTH`, and exact
`D-P5.7-PLANNING-R1-ACCEPTANCE` is effective. The frozen detailed plan
is in [`p5-7-implementation-plan.md`](p5-7-implementation-plan.md), supported
by the [quality architecture](p5-7-quality-architecture.md), [validation
portfolio](p5-7-validation-portfolio.md), [gap matrix](p5-7-contract-gap-matrix.md),
[threat model](p5-7-threat-model.md), and [decision packet](p5-7-decision-packet.md).
It proposes eight workstreams totaling 12 points and 2,048 generated contract,
journey, accessibility, localization, browser, scale, resilience, security,
and supply-chain cases. Exact `D-P5.7-START` makes `P5.7-START-R0` effective
for the bounded generated-only implementation, loopback validation, evidence,
stop-condition, and closed-gate scope. Existing dependency, backend, real-data,
operational, deployment, and remote-Git gates remain closed.

Workstreams W1 through W7 are technically complete at **11/12 (91.6667%)**.
The accepted Investigation and Evidence compatibility amendments close the
discovered accessible-landmark, compact-width, and adaptive-contrast defects.
Installed Edge passes 392/392 checks across eight portals and seven viewports;
the complete frontend and Python regressions pass under the documented local
environment limitations. The evidence graph and non-effective release manifest
are sealed in `P5.7-EVIDENCE-PACKAGE-R0`.

### Validation Portfolio

- deterministic generated operator journeys across all completed portals;
- component, contract, integration, end-to-end, and compatibility tests;
- WCAG 2.2 AA target matrix with automated and manual keyboard, screen-reader,
  zoom, target, contrast, motion, and error evidence;
- managed browser matrix and unsupported-browser behavior;
- English, Gujarati, Hindi, long-text, timezone, date, and number evidence;
- laptop, enhanced workstation, responsive, and multi-monitor layouts;
- interaction, long-task, map-idle, query, memory, media, and bundle budgets;
- event gap/reconnect, API degradation/recovery, session expiry, conflict, and
  profile downgrade;
- security, CSP, CSRF, XSS, storage, telemetry, dependency, SBOM, license,
  vulnerability, provenance, and reproducible build checks;
- full repository regression and Phase 0 through Phase 4 immutable readiness;
- exact claims, limitations, environment, and unsupported-feature register.

### Final Gate

Exact `D-P5.7-ACCEPTANCE` is effective for `P5.7-EVIDENCE-PACKAGE-R0`.
P5.7 is **12/12 (100.0000%)** and Phase 5 is **100/100 (100.0000%)**.
Manual accessibility and independent reproduction remain explicit limitations,
not silently completed claims. Phase 6, release, deployment, real systems/data,
operational actions, containers, Kubernetes execution, and remote Git remain
closed.

## Proposed Dependency Introduction Policy

Dependencies are introduced only when their capability is reached:

- P5.1: framework, TypeScript, build, package manager, router/query, component
  primitives, testing, lint, formatting, and accessibility test tooling;
- P5.2: selected GIS renderer and approved generated/private map fixtures;
- P5.3: selected HLS/WebRTC adapter only after generated-media authority;
- later subphases: no dependency unless the accepted feature requires it and
  license, SBOM, vulnerability, provenance, bundle, and maintenance evidence
  is complete.

No planning recommendation authorizes a download or lockfile change.

## Test Strategy

| Level | Purpose |
| --- | --- |
| Contract | Prove client types, examples, errors, bounds, and versions match canonical H-CAM contracts |
| Unit | Pure formatting, policy projection, capability, state, and reducer behavior |
| Component | Interaction, keyboard, focus, validation, state, error, and responsive behavior |
| Accessibility | Static rules plus manual keyboard, assistive technology, contrast, zoom, target, and motion |
| Integration | Generated service worker/mock server with realistic delay, partial, stale, denial, conflict, and recovery |
| Browser E2E | Critical workflows, session, navigation, events, multiple windows, profile changes, and storage absence |
| Visual | Stable desktop/laptop/tablet layouts, themes, localization, long text, high contrast, and screenshots |
| Performance | Interaction latency, long tasks, map idle, query fan-out, memory, bundle, and media admission |
| Security | Auth/session/CSRF/CSP/XSS/storage/scope/ETag/idempotency/telemetry/dependency boundaries |
| Compatibility | Producer versions, unknown fields/events, deprecation, and independently built portal packages |

Real cameras, media, providers, Government/private data, models, operational
actions, containers, Kubernetes, and deployments require separate future
authority and are not part of this validation plan by implication.

## Global Stop Conditions

Stop and require a new explicit owner decision if work would:

- modify an accepted Phase 0 through Phase 4 historical artifact to make a
  Phase 5 check pass;
- add an implementation path, dependency, route, migration, process, network
  connection, media, model, data, provider, container, Kubernetes, deployment,
  or remote Git action outside the exact current authority;
- bypass a missing producer contract with a mock in product code;
- expose a locator, secret, token, raw error, sensitive payload, or personal
  identifier to URL, storage, telemetry, or logs;
- weaken department isolation, server authorization, reason, ETag,
  idempotency, mandatory review, correction, evidence, or no-store behavior;
- mark skipped, unknown, partial, stale, degraded, unsupported, or untested
  behavior as complete;
- claim real-time, production, operational, legal, security, accessibility,
  standards, or scale readiness without the corresponding accepted evidence.
