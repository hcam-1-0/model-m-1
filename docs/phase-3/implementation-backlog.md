# Phase 3 Implementation Backlog

Status: P3.0 is accepted. P3.1 planning and bounded generated-only
implementation authorization are complete under `D-P3.1-001`. P3.1 technical
evidence is implemented with zero verifier failures, and its clean-source rerun
is complete. Accountable-owner exit acceptance is recorded under
`D-P3.1-ACCEPTANCE`. Every later milestone remains subject to its applicable
gates.

## Six-Person Ownership Model

| Role | Primary responsibility in Phase 3 |
| --- | --- |
| Lead/system architect | Contracts, boundaries, ADRs, integration, acceptance evidence |
| Computer-vision engineer | Dataset, detector, tracker, OCR, offline evaluation |
| Backend engineer | Assignments, metadata, outbox, APIs, audit, migrations |
| Frontend/operator engineer | Evaluation/review surface and human-factors evidence only when scheduled |
| Infrastructure engineer | Runtime adapters, GPU/CPU lab, containers, observability, load/recovery |
| Data/GIS/quality engineer | Annotation QA, zones/lines, benchmark slices, reproducibility |

Every item has one accountable owner. Separate-person review is optional for
model promotion, operational geometry, datasets, and deployment; the accountable
owner may review and approve their own work. Security/privacy, provenance,
license, validation, rollback, and audit evidence remain mandatory.

## P3.0: Contracts And Guardrails

Dependencies: approved planning package.

Deliverables:

- formal versioned schemas for assignments and the four event contracts;
- shared taxonomy and geometry/time conventions;
- runtime adapter interfaces and generated deterministic fixtures;
- prohibited-field validation and redaction policy;
- analytics package boundaries and migration design;
- threat model and misuse cases converted into executable tests.

Exit evidence: schema compatibility tests, golden fixtures, negative privacy
tests, ADR approval, migration review, and no model/media dependency in CI.

Implemented across the first two P3.0 slices:

- assignment and four event contracts with immutable lineage and UTC/bounds
  validation;
- deterministic schema and golden-fixture generation;
- strict producer and forward-compatible consumer parsing;
- prohibited field/value checks and a 64 KiB event limit;
- executable Phase 3/4 alert-boundary checks;
- CI contract-drift enforcement and focused branch coverage above 90%;
- draft taxonomy hierarchy with cycle, uniqueness, owner-approval, and
  prohibited-purpose controls;
- normalized line and simple-polygon zone definitions with non-degeneracy,
  self-intersection, boundary, weekly schedule, and overlap checks; and
- a contract-only runtime protocol, short-lived opaque input leases, bounded
  batches, safe failure codes, guarded output scope, and an unconfigured
  fail-closed implementation;
- durable stream/capability assignments and immutable revision history;
- an additive Alembic migration plus current-schema readiness checks;
- department-scoped viewer/editor APIs with reason headers, ETags, and
  optimistic locking;
- audited create/update/failure paths and validated deployment-change events in
  the transactional outbox; and
- additive Phase 3 OpenAPI/database snapshots while preserving Phase 2 history;
- PostgreSQL upgrade/drift/downgrade/restore and assignment integration
  evidence;
- sanitized request-validation responses that never echo rejected values; and
- identifier-free metrics, a Grafana control-plane dashboard, and bounded
  Prometheus alerts; and
- a machine-readable P3.0 readiness verifier with structured contract checks,
  deterministic documentation hashing, offline validation, strict mode, and
  four ordered evidence-backed owner gates.

P3.0 is accepted. Remaining work belongs to later runtime/media milestones and
retains its technical, security, privacy, provenance, license, validation,
rollback, and audit gates. Separate-person review is disabled for model
promotion, operational geometry, datasets, and deployment. No executable
inference runtime is part of P3.0.

## P3.1: Data And Evaluation Foundation

Dependencies: P3.0 contracts.

Planning status: complete and authorized under `D-P3.1-001`.

Implementation status: `accepted`. See the
[P3.1 plan](p3-1-plan.md), [authorization](p3-1-authorization.md),
[planning readiness report](p3-1-readiness-report.md), and
[implementation readiness report](p3-1-implementation-readiness-report.md), and
[owner acceptance](p3-1-acceptance.md).

Deliverables:

- dataset/model card schemas and immutable manifest format;
- generated detection, tracking, zone/line, and synthetic-plate fixtures;
- annotation guide, taxonomy, validation, split/leakage checks, and QA workflow;
- offline metric harness with machine-readable reports;
- immutable model-selection manifest for `DET-R0`, `DET-E1`, `DET-B1`,
  `DET-A1`, `TRK-R0`, and the script-specific OCR candidates;
- first measured baseline and proposed numeric accuracy/performance gates;
- metadata-only license/provenance research dossier for candidate code and
  artifacts, with every unresolved artifact-level blocker preserved.

Implemented evidence: six canonical contract families, 28 tracked artifacts,
seven generated suites, 11 blocked candidate manifests, annotation-QA and split
reports, hand-computable metric goldens, CI drift enforcement, and a complete
evidence index.

P3.1 exit evidence is complete. Numeric thresholds remain proposal-only; no
model promotion gate is approved by P3.1.

P3.1 direct input remains limited to deterministic `S0` generated metadata and
programmatic assets. `D-P3.2-001` separately authorized manifested artifact
quarantine and offline research. The later
[P3.2 start authorization](p3-2-start-authorization.md) now permits the exact
generated-input CPU implementation while cameras, real media, public datasets,
accuracy claims, training, deployment, and broader inference remain blocked.

## P3.2: Portable Detection Pipeline

Dependencies: P3.0 and P3.1; approved detector artifact.

Entry status: `implementation_authorized_generated_only`. The
[P3.2 entry decision packet](p3-2-entry-decision-packet.md) records the completed
entry audit. `D-P3.2-001` through `D-P3.2-004` are evidence-bound, and the
[P3.2 start authorization](p3-2-start-authorization.md) permits only the exact
generated-input, local/CI, ONNX Runtime CPU work packages.

Implementation status: `accepted`. The exact generated-only CPU slice is built,
validated, and accepted under `D-P3.2-ACCEPTANCE`. The accepted P3.1
candidate record stays historically blocked and the later exact artifact
approval remains separate. Public or real-media datasets, accuracy claims,
cameras, training, GPU/networked inference, deployment, artifact redistribution,
and remote Git actions remain prohibited.

Deliverables:

- deterministic generated-frame adapter boundary with no Phase 2 media access;
- `DET-R0` YOLOX-Tiny through the ONNX Runtime CPU reference adapter, or a
  replacement approved through a revised decision record;
- detector preprocessing, inference, postprocessing, taxonomy mapping;
- observation normalization, persistence/outbox, assignment lifecycle;
- C1 synthetic end-to-end path and component observability.

Exit evidence for the authorized slice: source-algorithm parity, deterministic
generated end-to-end evidence, fault injection, redaction, resource-limit tests,
clean-machine packaging, and a digest-bound owner acceptance. A frozen accuracy
report and real-media benchmark require separate future data authorization.

## P3.3: Per-Camera Tracking

Dependencies: stable P3.2 observations.

Implementation status: `accepted` under `D-P3.3-ACCEPTANCE`. The generated-only
stream-local tracker, lifecycle v2,
persistence, APIs, retention, observability, evaluation, and fail-closed
resource controls are implemented and accepted against the immutable package
digest. P3.4 is separately accepted under `D-P3.4-ACCEPTANCE`.

Deliverables:

- `TRK-R0` ByteTrack association behind the stream-local tracker contract,
  with explicit epochs and lifecycle events;
- discontinuity/restart/configuration-change behavior;
- bounded tracker state and overload handling;
- sequence evaluation and HOTA/IDF1 reports.

Exit evidence: no cross-camera linkage, deterministic lifecycle fixtures,
occlusion/reconnect tests, and approved tracking metrics.

## P3.4: Geometry And Event Primitives

Dependencies: P3.3 tracks and approved geometry contracts.

Planning status: authorized under `D-P3.4-PLAN-AUTH`; primary-source research,
technical planning, and the owner decision packet are complete. The owner
accepted `D-P3.4-001` hybrid PostGIS/Shapely geometry, `D-P3.4-002` visual typed
rule graph with constrained CEL, `D-P3.4-003` balanced deterministic time, and
`D-P3.4-004` bounded PostgreSQL/PostGIS persistence. Generated-only local
implementation was authorized under `D-P3.4-START`. Implementation and
technical evidence are complete and accepted under `D-P3.4-ACCEPTANCE` for the
immutable package digest. The PostGIS image deployment block remains open.

Deliverables:

- versioned normalized lines, polygons, schedules, and direction semantics;
- line crossing, zone entry/exit, occupancy, and dwell-time evaluator;
- analytic-event outbox and deduplication;
- geometry validation and configuration audit.

Implemented safety boundary: normalized image-space and anonymous stream-local
metadata only; default-off and production-forbidden. No media, external data,
identity, cross-camera linkage, Government matching, operational alerting,
deployment, or P3.5 implementation is authorized by P3.4. P3.5 planning is
separately authorized under `D-P3.5-PLAN-AUTH`.

Exit evidence complete: boundary/jitter/property tests, deterministic replay,
exact scenario logic agreement, duplicate/late-event tests, bounded C10
evidence, SQLite/PostGIS migration cycles, packaging, audit, and Docker checks.
Owner acceptance is complete under `D-P3.4-ACCEPTANCE`; container deployment
remediation remains an independent open gate.

## P3.5: Synthetic ANPR

Dependencies: accepted P3.4, existing blocked P3.1 plate/OCR candidates, and the
accepted P3.0 zero-retention plate-text policy.

Planning status: authorized under `D-P3.5-PLAN-AUTH`. Primary-source research,
the detailed plan, and owner decision packet are complete. `D-P3.5-001` through
`D-P3.5-004` remain pending. The exact `D-P3.5-START` statement was received
early and is recorded as non-effective until those decisions and exact artifact
review are complete. No artifact acquisition,
generation, training, inference, product implementation, or media/data access
is authorized.

Artifact preparation status: proposal R0 records eight recommended artifact
slots, immutable source metadata where available, bounded sizes, and current
runtime gaps. All SHA-256 values remain unresolved; acquisition and execution
remain blocked pending the four technical decisions and
`D-P3.5-ARTIFACT-RESEARCH`.

Deliverables:

- plate-region detector and OCR adapter;
- `PLATE-D0` derived only from the promoted H-CAM detector family;
- `OCR-L0/L1` for Latin, `OCR-D0` for Devanagari, and `OCR-G0/G1` for Gujarati,
  with explicit script routing and abstention;
- ranked alternatives, normalization, confidence, masking, and review state;
- zero-retention, no-access-role handling for plate text and alternatives;
- separate region/OCR/normalization evaluation.

Planned exit evidence: deterministic non-issuable synthetic provenance,
localization and raw/NFC/grapheme/end-to-end metric reports, abstention and
calibration evidence, privacy/redaction tests, zero persisted plate strings,
and proof that no owner/watchlist/Government lookup exists.

## P3.6: Runtime Acceleration And Scheduling

Dependencies: stable reference pipeline and target hardware decision.

Deliverables:

- model-family comparison (`DET-R0/E1/B1/A1`) completed before runtime tuning;
- controlled OpenVINO first on owned Intel hardware and DeepStream/TensorRT on
  approved NVIDIA hardware; Triton only after its workload trigger;
- reference-versus-accelerator numeric parity;
- node inventory, placement, admission, bounded batching, and backpressure;
- C1/C10/C50 benchmark matrix on declared hardware;
- selected runtime ADR and reproducible pinned deployment.

Exit evidence: signed benchmark manifests, cost/complexity comparison,
degradation behavior, driver/container security review, and rollback.

## P3.7: Governance, Operations, And Security Hardening

Dependencies: end-to-end Tier A pipeline.

Deliverables:

- model/dataset registry integration or approved minimal equivalent;
- approval, alias resolution, immutable deployment, suspension, retirement;
- dashboards, alerts, SLOs, runbooks, backup/recovery, and kill switch;
- authorization, department isolation, audit, retention, and deletion controls;
- adversarial media/model tests and dependency/artifact supply-chain checks.

Exit evidence: security report, audit map, restore/recovery and kill-switch
drills, stale/drift alerts, no-secret/no-media telemetry tests, and operator
runbooks.

## P3.8: Acceptance And Phase 4 Handoff

Dependencies: Tier A implementation and all prior gates.

Deliverables:

- controlled synthetic end-to-end demonstration;
- complete acceptance evidence index and known-limitations register;
- event-consumer contract pack for Phase 4;
- explicit statement that events are not alerts or identities;
- Phase 4 correlation/watchlist/governance entry questions;
- owner acceptance record.

Exit evidence: all acceptance checklist items complete, reproducible reports,
open risks explicitly accepted or resolved, and owner sign-off.

## Deferred Backlog

Tier B starts only after P3.8 unless the owner explicitly reprioritizes it with
its data/risk gates. Every Tier C capability remains a separate future proposal.
Face recognition, person re-identification, Government matching, watchlists,
and operational alerting are not Phase 3 backlog items.
