# Phase 3: AI Analytics

Status: P3.0 accepted under `D-P3.0-001` on 2026-08-24. P3.1 data-and-
evaluation-foundation planning is authorized under `D-P3.1-001`, and its
technical evidence is implemented with zero verifier failures. Clean-source
regeneration is complete, and P3.1 is accepted under `D-P3.1-ACCEPTANCE`.
P3.2 is accepted under `D-P3.2-ACCEPTANCE`. P3.3 generated-only, anonymous,
stream-local tracking is accepted under `D-P3.3-ACCEPTANCE`. P3.4 planning is
authorized under `D-P3.4-PLAN-AUTH`; technical decisions `D-P3.4-001` through
`D-P3.4-004` are accepted, and bounded generated-only local implementation is
authorized under `D-P3.4-START`. Implementation and technical evidence are
complete and accepted under `D-P3.4-ACCEPTANCE`. P3.5 synthetic-ANPR planning
is authorized under `D-P3.5-PLAN-AUTH`; its recommended `A/A/A/A` technical
baseline is approved, and exact seven-artifact quarantine research is
authorized under `D-P3.5-ARTIFACT-RESEARCH`. Exact hashes, passive inspection,
artifact SBOM, and Defender scan are complete and owner accepted.
`D-P3.5-RUNTIME-RESEARCH` authorized the isolated dependency review; its exact
runtime evidence, SBOM, license inventory, vulnerability audit, Defender scan,
and network-denied imports are complete. `D-P3.5-START` is now effective only
for the exact generated-only, default-off,
zero-network local implementation allowlist. All broader media,
identity, correlation, alerting, and deployment work remains unauthorized.

Phase 2 was accepted on 2026-08-21. Phase 3 planning defines how H-CAM will
turn authorized video into anonymous, versioned, reviewable observations and
per-camera events. It deliberately stops before identity matching, cross-camera
correlation, watchlists, Government database access, alerts, cases, or
autonomous enforcement.

## Planning Package

| Document | Purpose |
| --- | --- |
| [Product scope](product-scope.md) | Goals, users, boundaries, outputs, and Phase 4 handoff |
| [Architecture](architecture.md) | Control plane, analytics data plane, failure behavior, and deployment shapes |
| [Analytics catalog](analytics-catalog.md) | Ordered capability tiers and risk-specific entry gates |
| [Event contracts](event-contracts.md) | Versioned observation, track, analytic-event, and deployment contracts |
| [Taxonomy, geometry, and runtime contracts](taxonomy-geometry-runtime-contracts.md) | Draft class hierarchy, normalized geometry/time, and fail-closed adapter boundary |
| [Model portfolio](model-portfolio.md) | Role-based detector, tracker, OCR, ANPR candidates and promotion funnel |
| [Runtime and deployment](runtime-and-deployment.md) | Portable baseline, candidate accelerators, capacity tiers, and selection criteria |
| [Data and model governance](data-and-model-governance.md) | Dataset provenance, annotation, model registry, promotion, rollback, and drift |
| [Security, privacy, and safety](security-privacy-and-safety.md) | Threats, prohibited functions, controls, and human-review policy |
| [Validation and benchmarks](validation-and-benchmark-plan.md) | Accuracy, latency, resilience, slice, and scale evidence |
| [Implementation backlog](implementation-backlog.md) | Ordered work packages, ownership, dependencies, and exit evidence |
| [Decision register](decision-register.md) | Inherited constraints, proposed decisions, and unresolved ADRs |
| [Research references](research-references.md) | Primary-source technology and governance references |
| [Acceptance checklist](acceptance-checklist.md) | Planning and future implementation gates |
| [Owner review](owner-review.md) | Review questions and explicit authorization language |
| [Build and test](build-and-test.md) | P3.0 implementation scope, evidence, and remaining gates |
| [Assignment control plane](assignment-control-plane.md) | Durable fail-closed assignments, APIs, audit, revisions, and outbox |
| [P3.0 readiness report](readiness-report.md) | Machine-verifiable evidence and explicit owner gates |
| [P3.0 owner decisions](p3-0-owner-decisions.md) | Accepted G1-G4 and accountable-owner review policy for later gates |
| [P3.1 plan](p3-1-plan.md) | Generated-only contracts, fixtures, QA, metrics, work packages, risks, and exits |
| [P3.1 hardware profile](p3-1-hardware-profile.md) | Developer baseline and prohibited performance claims |
| [P3.1 authorization](p3-1-authorization.md) | Human owner authorization and explicit non-authorization |
| [P3.1 readiness report](p3-1-readiness-report.md) | Evidence-backed planning gates and pending implementation exits |
| [P3.1 implementation readiness](p3-1-implementation-readiness-report.md) | Accepted implementation evidence, validation results, and package digest |
| [P3.1 owner acceptance](p3-1-acceptance.md) | Digest-bound `D-P3.1-ACCEPTANCE` record and continuing exclusions |
| [P3.2 entry decision packet](p3-2-entry-decision-packet.md) | Completed entry decisions, exact evidence bindings, and continuing boundaries |
| [P3.2 controlled research record](p3-2-research-record.md) | Authorized public-artifact research controls, quarantine, and offline experiment boundary |
| [P3.2 start authorization](p3-2-start-authorization.md) | Generated-only CPU implementation work packages and explicit non-authorizations |
| [P3.2 implementation](p3-2-implementation.md) | Exact activation contract, runtime, generated execution, persistence, APIs, retention, and evidence |
| [P3.2 implementation readiness](p3-2-implementation-readiness-report.md) | Final tests, PostgreSQL, packaging, dependency audit, generated E2E, and owner gate |
| [P3.3 plan](p3-3-plan.md) | Anonymous stream-local lifecycle, evidence, resource, and safety design |
| [P3.3 implementation](p3-3-implementation.md) | Exact tracker adaptation, generated scenarios, persistence, API, and boundaries |
| [P3.3 implementation readiness](p3-3-implementation-readiness-report.md) | Validation results, package digest, and final owner gate |
| [P3.3 owner acceptance](p3-3-acceptance.md) | Exact-digest `D-P3.3-ACCEPTANCE` record and continuing exclusions |
| [P3.4 planning authorization](p3-4-planning-authorization.md) | Exact planning-only owner authorization and prohibited actions |
| [P3.4 research record](p3-4-research-record.md) | Primary-source geometry, time, idempotency, and testing research |
| [P3.4 plan](p3-4-plan.md) | Geometry, event state, replay, persistence, resource, and generated-validation design |
| [P3.4 owner decision packet](p3-4-decision-packet.md) | Four technical decisions and separate implementation-start gate |
| [P3.4 owner decisions](p3-4-owner-decisions.md) | Accepted hybrid geometry, visual/CEL rules, time, and persistence selections |
| [P3.4 start authorization](p3-4-start-authorization.md) | Exact generated-only local implementation boundary and continuing exclusions |
| [P3.4 planning readiness](p3-4-planning-readiness-report.md) | Machine-verified package digest, technical checks, and manual gates |
| [P3.4 implementation](p3-4-implementation.md) | Hybrid geometry, constrained rules, deterministic events, persistence, APIs, and boundaries |
| [P3.4 third-party notices](p3-4-third-party-notices.md) | Exact direct dependencies, licenses, native runtimes, and vulnerability boundary |
| [P3.4 implementation readiness](p3-4-implementation-readiness-report.md) | Tests, coverage, migrations, packaging, Docker evidence, deployment block, and acceptance binding |
| [P3.4 backlog recovery](p3-4-backlog-recovery.md) | Interrupted-work handoff, reproduced defects, repair scope, validation, and remaining backlog |
| [P3.4 owner acceptance](p3-4-acceptance.md) | Exact-digest `D-P3.4-ACCEPTANCE` record and continuing exclusions |
| [P3.5 planning authorization](p3-5-planning-authorization.md) | Planning-only owner authorization and prohibited implementation actions |
| [P3.5 research record](p3-5-research-record.md) | Current primary-source OCR, Unicode, rule, font, and synthetic-data findings |
| [P3.5 artifact review proposal](p3-5-artifact-review-proposal.md) | Metadata-only eight-artifact proposal, quarantine blockers, and zero download authority |
| [P3.5 owner decisions](p3-5-owner-decisions.md) | Approved `A/A/A/A` technical baseline and continuing non-authorization |
| [P3.5 artifact research authorization](p3-5-artifact-research-authorization.md) | Exact seven-artifact quarantine allowlist and safety controls |
| [P3.5 exact artifact review evidence](p3-5-artifact-review-evidence.md) | Hashes, passive inspection, Defender scan, license evidence, and runtime blocks |
| [P3.5 exact artifact review acceptance](p3-5-artifact-review-acceptance.md) | Digest-bound owner acceptance and continuing non-authorization |
| [P3.5 artifact model cards](p3-5-artifact-model-cards.md) | Intended generated-only OCR roles and explicit limitations |
| [P3.5 runtime review proposal](p3-5-runtime-review-proposal.md) | Proposed Python 3.12 dependency research and unresolved Tesseract engine |
| [P3.5 runtime research authorization](p3-5-runtime-research-authorization.md) | Restricted external Python dependency review and prohibited runtime actions |
| [P3.5 runtime research evidence](p3-5-runtime-research-evidence.md) | Exact wheel closure, SBOM, licenses, audit, Defender scan, guarded imports, and remaining blocks |
| [P3.5 generated-only start authorization](p3-5-start-authorization.md) | Digest-bound generated-only work, five loadable artifacts, exact runtime, zero network actions, and continuing blocks |
| [P3.5 W1 contracts and guardrails](p3-5-w1-contracts-guardrails.md) | Seed-only request, visible non-issuable token policy, prohibited-input guard, zero retention, and deterministic snapshots |
| [P3.5 W3 deterministic generator and sealed splits](p3-5-w3-generator-splits.md) | Domain-separated ephemeral tokens, independent seed namespaces, token-free split manifest, final-test freeze, and logical holdouts |
| [P3.5 W4 ground-truth localization and crop](p3-5-w4-ground-truth-crop.md) | Procedural generated frame, sealed region, model-free localization, bounded ephemeral crop, and pixel-free evidence |
| [P3.5 plan](p3-5-plan.md) | Synthetic corpus, localization, OCR, normalization, consensus, privacy, and evidence design |
| [P3.5 owner decision packet](p3-5-decision-packet.md) | Four technical choices and separate implementation-start gate |
| [P3.5 planning readiness](p3-5-planning-readiness-report.md) | Historical machine-verified planning boundary and then-pending owner gates |
| [P3.5 start intent](p3-5-start-intent.md) | Historical early `D-P3.5-START` statement and why it was initially non-effective |

## Non-Negotiable Boundary

Phase 3 may process only synthetic, generated, or explicitly authorized and
license-reviewed media. The Sentinel reference site remains metadata-only and
must not become a training-data or video-ingestion source.

Phase 3 track IDs are anonymous and scoped to one stream and one tracker epoch.
They are not identities. Face recognition, person re-identification,
cross-camera identity, watchlists, vehicle-owner lookup, and Government data
matching remain out of scope.

## Phase 3 Outcome

The intended outcome is a reproducible analytics subsystem that can:

1. consume a controlled internal stream or authorized test clip;
2. run a declared, immutable model version;
3. emit bounded, versioned observations and per-camera track updates;
4. evaluate configured line and zone rules;
5. preserve model, pipeline, timing, confidence, and review provenance;
6. degrade safely under overload or dependency failure; and
7. prove behavior with synthetic tests and benchmark evidence.

The role-based evaluation portfolio in `model-portfolio.md` is selected for
planning. No exact artifact, champion model, runtime, dataset, infrastructure,
evaluation, media processing, or deployment is approved merely because this
planning package or the P3.0 contract code exists.

## Current Implementation

The model-independent `hcam.analytics` package defines the assignment contract,
four analytics event envelopes, bounded canonical serialization, immutable
lineage fields, prohibited-data inspection, producer/consumer compatibility
rules, draft taxonomy and geometry definitions, weekly time windows, a guarded
runtime adapter protocol, and deterministic generated fixtures. The P3.0
control plane now persists assignments and immutable revisions, exposes scoped
RBAC/ETag APIs, records audit evidence, and emits validated deployment-change
metadata through the existing transactional outbox. CI rejects unreviewed
analytics, OpenAPI, or migrated-database contract drift. Request-validation
errors omit rejected values, and identifier-free metrics, a Grafana dashboard,
and Prometheus alerts expose blocked-state, revision, outbox, and failure health.

The accepted P3.0 baseline itself has no geometry evaluator, decoder, model,
dataset, or media path. P3.2 now extends that baseline with an explicit,
default-off generated-only activation and execution path. It does not change
P3.0 history or introduce a camera/media path. The exact taxonomy, intended
use, metadata policy, and review roles remain owner approved.

Separate-person review is also disabled for later model promotion, operational
geometry, datasets, and deployment. The accountable owner may approve those
records, but all evidence, safety, authorization, and non-activation boundaries
remain in force.

The control-plane migration has also passed PostgreSQL 18 upgrade, schema-drift,
full downgrade-to-base, restore-to-head, and five synthetic integration tests.

P3.1 implements six immutable record families, seven generated suites,
annotation/QA and grouped split/leakage checks, hand-computable metric goldens,
11 blocked candidate records, and a deterministic 28-artifact evidence package.
Only deterministic generated metadata and programmatic assets are used. The
implementation verifier reports `accepted`: technical failures and manual gates
are zero, the clean-source gate passes, and accountable-owner acceptance is
bound to the unchanged package digest. `D-P3.2-001` authorized controlled
artifact research, and `D-P3.2-002` through `D-P3.2-004` now bind one exact
model, generated-only input source, and CPU reference contract. The
[P3.2 start authorization](p3-2-start-authorization.md) permits only the named
generated-input implementation packages. The
[P3.2 implementation](p3-2-implementation.md) now provides the verified CPU
adapter, generated execution API, normalized observation/outbox persistence,
lifecycle controls, retention, metrics, and local E2E harness. Cameras, real
media, public datasets, accuracy claims, training, deployment, artifact
redistribution, and remote Git actions remain prohibited. P3.2 is accepted under
`D-P3.2-ACCEPTANCE` for that bounded result.

P3.3 adds a default-off, production-forbidden ByteTrack-style association layer
over sealed generated structured observations. It persists explicit epochs,
anonymous stream-local tracks, lifecycle v2 records, and transactional outbox
events. Generated HOTA/IDF1 and pinned TrackEval parity pass, but no real-media,
cross-camera, identity, alerting, or deployment claim is made. The exact package
is accepted under `D-P3.3-ACCEPTANCE`.

P3.4 now implements immutable normalized geometry and rule versions,
line/zone/dwell/occupancy state machines, event-time ordering, bounded lateness,
deterministic replay, transactional events, resource ceilings, retention, and a
generated C10 validation suite. The four technical decisions select hybrid
PostGIS/Shapely geometry, a visual typed rule graph with constrained CEL, the
balanced deterministic time policy, and bounded PostgreSQL/PostGIS persistence.
The bounded implementation is technically validated under `D-P3.4-START`; it
does not have final owner acceptance and authorizes no broader capability. The
PostGIS image is blocked from deployment pending remediation and rescan.

Accepted planning snapshot digest:
`57D2F541C4AA9AB8988A5DF7FC228DA4047BF471B64AD704BDB478308FDC3898`.
Post-decision synchronization changes are recorded separately and do not alter
the scope accepted in that snapshot.
