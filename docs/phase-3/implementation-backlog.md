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
`D-P3.5-004` approve the recommended `A/A/A/A` baseline. Exact quarantine
research for seven external artifacts is authorized under
`D-P3.5-ARTIFACT-RESEARCH`; acquisition, hashes, passive inspection, artifact
SBOM, model cards, and Defender scan are complete and the exact packet is owner
accepted. `D-P3.5-RUNTIME-RESEARCH` authorizes the isolated dependency closure;
the exact Python wheel closure, SBOM, license metadata, vulnerability audit,
Defender scan, and guarded import evidence are complete. Final digest-bound
`D-P3.5-START` is effective with status
`implementation_authorized_generated_only_staged`. It permits only the exact
generated-only local packages and five loadable artifacts listed in the start
record, using the reviewed external Paddle runtime with zero network access.
Training, Tesseract execution, cameras/media, real/private/Government data,
public APIs, persistent plate text, deployment, P3.6, and remote Git remain
prohibited.

Implementation progress:

- `P35-W1`: `validated_complete`. Immutable seed-only request, ephemeral token,
  and default-off execution-policy contracts are tracked. The visible
  `SYN-XXXX-XXXX` namespace, recursive prohibited-input validation, bounded
  parsing, value-redacted failures, and plate-text persistence denial have
  deterministic snapshots and negative tests.
- No generator, OCR adapter, model loader, API, migration, worker, or storage
  path was introduced in W1.
- `P35-W3`: `validated_complete`. Domain-separated SHA-256 generation now emits
  bounded non-issuable tokens ephemerally from independent split namespaces.
  A digest-bound 20-entry manifest freezes contract/development/validation/final
  test assignments, reserves final-test-only logical generator/font holdouts,
  and persists neither token text nor a token-derived commitment.
- W3 includes 20-run exact replay, collision, leakage, tampering, count,
  default-off, split separation, and zero-retention tests. It does not render a
  plate, load a font/model/artifact, run OCR, or add an API/storage path.
- `P35-W4`: `validated_complete`. A bounded procedural frame, sealed region,
  model-free `GT-PLATE-R0` result, and axis-aligned ephemeral crop pass focused,
  full-suite, contract-drift, readiness, lint, and package-build validation.
- W4 loads no model, weight, font, OCR runtime, camera, media, or external
  input. `PLATE-D0`, W2, persistence, APIs, and deployment remain blocked or
  separate future work under the existing start allowlist.
- `P35-W5`: `validated_generated_baseline`. The exact reviewed `OCR-L0` and
  `OCR-L1` archives are safely extracted only under the external `E:` runtime.
  A code-defined renderer, strict ephemeral raw-output contracts, isolated
  network-denied Paddle workers, 12-sample development/validation evaluation,
  and 20-run deterministic replay are implemented. Tracked evidence contains
  only identifier-free aggregates and opens no final-test sample.
- W5 observed 7/12 exact raw matches for L0 and 9/12 for L1. Both candidates
  observed 0/3 exact matches on two-line crops. These values are baseline
  evidence only; quality thresholds, promotion, normalization, consensus,
  real-data evaluation, and deployment remain undecided or prohibited.
- `P35-W6`: `validated_generated_baseline`. Exact `OCR-D0`, `FONT-D0`, and
  `FONT-G0` are revalidated at every external run. A closed standalone-grapheme
  vocabulary, three degradation slices, strict script router, isolated
  network-denied worker, and aggregate-only evidence are implemented.
- W6 observed 10/12 exact Devanagari matches: 4/4 clean, 3/4 low contrast, and
  3/4 downscaled. Both fonts rendered 12/12 and replayed deterministically for
  20/20 runs. Gujarati OCR and Tesseract execution stayed at zero because
  `OCR-G0` and `OCR-G1` remain blocked. No quality or promotion decision follows
  from these generated results.
- `P35-W7`: `validated_generated_contract_fixture`. Raw-preserving NFC
  derivation, Unicode extended-grapheme metrics, candidate-local identity
  calibration fixtures, and mandatory abstention are implemented under exact
  CPython `3.12.13`, Unicode `15.0.0`, and `regex==2026.7.19` semantics.
- W7 canonical evidence is identifier-free and aggregate-only. It records
  20/20 deterministic replay, one blocked socket attempt, zero model execution,
  zero external text/media/real-registration input, zero persisted raw or
  normalized text/graphemes/identifiers, and zero operational acceptance.
- W7 does not approve a numeric quality threshold or model promotion. It adds
  no API, worker, migration, database, lookup, alert, camera/media, or deployment
  path. W7 did not execute consensus or alter its canonical evidence.
- `P35-W8`: `validated_generated_contract_fixture`. Bounded consensus is keyed
  only by anonymous `stream_id`, `tracker_epoch`, and `track_id`; it never groups
  by plate text. Each state closes at five observations or two seconds, and each
  stream is capped at 256 active states with fail-closed overload behavior.
- W8 canonical evidence SHA-256 is
  `58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124`.
  It records 20/20 deterministic replay, 281 bounded operations, 269 closed and
  abstained results, duplicate/out-of-order rejection, zero stream/epoch/track
  merges, zero accepted values, and zero persisted plate text or identifiers.
- W8 does not invent minimum-support or margin thresholds. Both remain unset,
  every result is a mandatory abstention, and no API, worker, migration,
  database, alert, camera/media, operational, or deployment path is added.
- `P35-W9`: `validated_generated_only_closure`. `mayank-admin` authorized
  Option A with `D-P3.5-W9-START: A`, bound to planning digest
  `9BCC9E9C068E03E94E5461AABDE3B50A4766498406643EE253AF66ECAD8A9B7B`.
  The closure consolidates seven W1-W8 evidence groups, runs two deterministic
  10,000-observation model-free stress replays, verifies default-off/network
  denial and zero retention, and inspects offline wheel/sdist contents.
- W9 adds no application, migration, dependency, lockfile, container, API,
  worker, database, persistence, camera/media, external runtime, model, alert,
  deployment, P3.6, or remote Git path. Its generated archives are untracked.
- `P35-W10`: `accepted`. Clean-source validation passed and `mayank-admin`
  supplied `D-P3.5-W10-ACCEPTANCE` for immutable package digest
  `4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`
  at commit `1611922b4f410aa0cdbce369e4f3c8838f53e19f`, with W9 evidence
  SHA-256 `A64ACE72ED33E0734D87D43A871BB1FB73B593296A681771600C3A1F42899E55`.
  This closes P3.5 only and grants no P3.6 or broader authority.

Artifact preparation status: proposal R0 records eight recommended artifact
slots, immutable source metadata, and bounded sizes. Seven external slots are
present in quarantine with exact evidence. `OCR-L0`, `OCR-L1`, `OCR-D0`,
`FONT-G0`, and `FONT-D0` are authorized only for their exact generated-only
uses. `OCR-G0`, `OCR-G1`, the Tesseract engine, `PLATE-D0`, training, and any
unlisted execution remain blocked.

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

Planning status: authorized under `D-P3.6-PLAN-AUTH`. Read-only primary-source
research, the detailed plan, five-choice owner packet, and machine-readable
entry gates are complete. `D-P3.6-001` through `D-P3.6-005` and the dynamic
capability-profile policy are accepted; `P36-G3` is passed. Model-family
promotion, exact hardware/runtime/artifact/workload manifests, artifact
authority, runtime execution, implementation, containers/Kubernetes actions,
deployment, media/data access, and remote Git remain blocked.
The received `D-P3.6-START` statement is recorded as non-effective intent; it
does not change these blockers or start an executable work package.
`P36-U1` sanitized inventory is complete under
`D-P3.6-INVENTORY-R0-AUTH`, but it supplies only one input to G2.
`P36-U2` exact official model metadata and a three-artifact fail-closed R0
proposal are sealed under package digest
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.
No artifact was downloaded; acquisition remains blocked on exact eligible
local storage, an exact scanner binding, a regenerated R1 package, and explicit
owner authority.
`P36-U0A` is complete: P3.6 ownership and vocabulary are bound to the Phase -1
shared contracts at `hcam-protos` merge `d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8`,
deployment merge `71095fe89d2b711e4982ddc0130fcaedda8703e7`, and canonical base digest
`sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf`.
This passes `P36-G0A` without changing G1, G2, G4, or G5.

Planning records:

- [planning authorization](p3-6-planning-authorization.md);
- [primary-source research](p3-6-research-record.md);
- [detailed plan](p3-6-plan.md);
- [owner decision packet](p3-6-decision-packet.md);
- [accepted owner decisions](p3-6-owner-decisions.md);
- [dynamic capability profiles](p3-6-capability-profiles.md);
- [Phase -1 shared-contract alignment](p3-6-phase-minus-1-alignment.md);
- [non-effective start intent](p3-6-start-intent.md);
- [prerequisite unblock plan](p3-6-unblock-plan.md);
- [LAB-LAPTOP-01 sanitized inventory](p3-6-inventory-lab-laptop-01-r0.md); and
- [exact model artifact research proposal](p3-6-model-artifact-research-proposal.md);
- [sealed non-authorizing model proposal package](../../contracts/phase-3/p3-6-model-artifact-research-package.json); and
- [machine-readable entry gates](../../contracts/phase-3/p3-6-entry-gates.json).

Deliverables:

- `P36-W0`: `complete`; planning/research package, owner choices, and dynamic
  profile policy are recorded;
- `P36-W1`: model-family comparison (`DET-R0/E1/B1/A1`) and promoted
  champion/fallback before runtime tuning;
- `P36-W2`: model-independent node, runtime, scheduler, lease, queue, and
  evidence contracts;
- `P36-W3`: controlled OpenVINO feasibility on exact owned Intel hardware;
- `P36-W4`: TensorRT and optional DeepStream feasibility on exact approved
  NVIDIA hardware;
- `P36-W5`: Triton evaluation only after a measured shared-serving trigger;
- `P36-W6`: deterministic placement, admission, reservations, leases,
  reconciliation, and department/data-zone isolation;
- `P36-W7`: stateless detector batching, stream-local state isolation, bounded
  queues, fairness, backpressure, and degradation;
- `P36-W8`: layered `CONTRACT`/`INFER`/`PIPE` C1/C10/C50 benchmark matrix on
  declared generated workloads and exact hardware;
- `P36-W9`: artifact/runtime/driver/container SBOM, provenance, vulnerability,
  resilience, and rollback evidence;
- `P36-W10`: selected runtime ADR, immutable compatibility bundle, limitations,
  and owner acceptance.

Exit evidence: signed benchmark manifests, cost/complexity comparison,
reference-versus-accelerator and downstream parity, deterministic placement and
admission evidence, C1/C10/C50 bounded-load results or a narrower explicit
claim, degradation behavior, driver/container security review, supply-chain
provenance, rollback, exact package digest, and owner acceptance.

Remaining gated backlog requires exact owner decisions and separate authority:

- obtain owner review of the non-authorizing R0 model-proposal package;
- bind an eligible exact local quarantine root and exact scanner invocation,
  then regenerate a digest-bound R1 acquisition proposal;
- resolve exact model-family artifacts/data and complete `P36-G1`;
- prepare and approve exact shared `portable_cpu` and `owned_gpu_lab` machine,
  OS, driver, runtime, precision, decoder, resource, and generated-workload
  manifests for `P36-G2`;
- select `standalone_server` or `kubernetes_cluster` for any future C10/C50
  capacity target; do not create a separate `capacity_target` profile;
- prepare bounded acquisition/research manifests for any external artifacts,
  dependencies, drivers, or containers;
- prepare a digest-bound `D-P3.6-START` proposal. Do not execute it by
  implication from a planning, architecture choice, or earlier broad start
  statement.

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
