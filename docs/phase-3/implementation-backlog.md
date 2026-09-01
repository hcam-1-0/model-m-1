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
The metadata planning proposal is owner accepted through
`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE`.
No artifact was downloaded; acquisition remains blocked on exact eligible
local storage, an exact scanner binding, a regenerated R1 package, and explicit
owner authority.
`P36-U0A` is complete: P3.6 ownership and vocabulary are bound to the Phase -1
shared contracts at `hcam-protos` merge `d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8`,
deployment merge `71095fe89d2b711e4982ddc0130fcaedda8703e7`, and canonical base digest
`sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf`.
This passes `P36-G0A` without changing G1, G2, G4, or G5.
`P36-U3` now has a sealed, non-executable `portable_cpu` R0 proposal under
package digest
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.
The non-executable planning proposal is owner accepted. Exact unresolved
values, generated validation, the `owned_gpu_lab` inventory, and a
capacity-target decision remain pending, so `P36-G2` stays blocked.
The inventory/admission gap is sealed under package digest
`CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.
It proves the historical R0 record is not the shared Phase -1 inventory shape
and its four recommended `A/A/A/A` owner policy choices are accepted. No R1
recollection is authorized.
The exact minimized R1 authorization proposal is now sealed under package
digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`.
`D-P3.6-INVENTORY-R1-AUTH` accepted that exact digest. The single authorized
local read-only attempt succeeded, is consumed, and produced a sanitized,
shared-schema-valid R1. No reusable collector was implemented. The R1 is a
factual input only; it does not make a profile resolver-eligible or change the
blocked state of `P36-G2`.
The exact R1-to-portable admission gap is now sealed under package digest
`471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`.
It records 22 remaining gaps, proves that only one of seven resolver input kinds
is currently represented by R1, and presents four independent owner choices.
`mayank-admin` accepted the recommended `A/A/A/A` planning policies against the
exact package digest. The acceptance is non-effective and does not change any
collection, profile, execution, or implementation gate.
The follow-on exact compatibility and deterministic generated C1 validation
proposal is sealed under package digest
`9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A`.
`mayank-admin` accepted the four U3C choices as `A/A/A/A` planning policy.
The acceptance remains non-effective and grants no
execution, acquisition, validation, implementation, or activation authority.
The follow-on portable R1 supply-chain prerequisite package is sealed under
digest
`496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
`mayank-admin` accepted the five U3D choices as `A/A/A/A/A` planning policy.
The acceptance is non-effective: it binds no storage path or scanner and grants
no query, write probe, acquisition, inspection, execution, validation,
implementation, or activation authority.
The owner then supplied `F:` as a candidate volume. The exact non-effective
`F:\HCAM-Quarantine` storage-attestation and read-only scanner-binding package
is sealed under digest
`9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`.
The owner accepted it as `D-P3.6-U3E-BINDING-R0-AUTH`, and its single attempt
was consumed. Volume/path checks passed, the broad-write ACL gate failed, the
atomic probe was skipped, and the empty root was removed. U3F remediation
decisions are now sealed under digest
`9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`;
the owner selected `D-P3.6-U3F-001` through `006` as `A/A/A/A/A/A`. The
resulting U3G authorization package was sealed under digest
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
The owner exactly authorized that digest and the attempt is consumed. It failed
closed at exact DACL verification, skipped the probe, removed the empty root,
retained no probe content, and could not obtain a usable Defender product
version. Candidate hashing and WinVerifyTrust were skipped. No retry is
authorized.
Planning-only U3H analysis now records Microsoft-documented automatic
`Synchronize` behavior for allow ACEs and PowerShell compatibility-remoting
behavior as confidence-qualified hypotheses rather than retroactive U3G facts.
Its six owner choices are sealed under digest
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
The recommended `A/A/A/A/A/A` policy normalizes `Modify | Synchronize`,
separates DACL tuple classifications, uses native Windows PowerShell scalar
projection with a trust-gated Defender fallback, splits future storage and
Defender attempts, and requires a reviewable runner proposal. Selections are
now explicitly accepted as `A/A/A/A/A/A` under acceptance SHA-256
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`.
They authorize preparation only of non-effective runner and storage-only
proposals and grant no action or implementation authority.
Those outputs are now sealed separately. The U3I runner implementation proposal
has digest
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`;
the U3J storage R2 planning proposal has digest
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.
Both requested owner statements are accepted. The U3I contract-only runner and
generated harness are implemented and sealed under implementation-package
digest
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`.
All twenty generated vectors and four structural checks pass; PowerShell parser
validation has zero errors, but the runner was not executed and all machine
handlers remain unimplemented. U3J is still not an execution package. No
runtime execution, retry, or machine action is authorized. The implementation
package is owner accepted, and its non-effective runtime-binding package was
sealed under digest
`37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`
and `D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH` was consumed by one exact read-only
attempt. The attempt succeeded and sealed
evidence SHA-256
`4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`;
owner evidence acceptance is recorded as
`D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` under acceptance SHA-256
`F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E`.
The final U3K preparation package is sealed under SHA-256
`4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`,
but it remains a historical placeholder-runner package. The ten machine
handlers were subsequently implemented and accepted as source and
generated/static evidence only; a fresh runtime binding, newly sealed
executable U3K package, and separate digest-bound storage authorization remain
required before any machine action.

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
- [portable CPU profile proposal R0](p3-6-portable-cpu-profile-proposal.md);
- [sealed non-executable portable CPU package](../../contracts/phase-3/p3-6-portable-cpu-profile-package.json); and
- [inventory and admission gap R0](p3-6-inventory-admission-gap.md);
- [sealed inventory-admission owner package](../../contracts/phase-3/p3-6-inventory-admission-package.json); and
- [minimized R1 authorization proposal](p3-6-inventory-r1-authorization-proposal.md);
- [sealed non-effective R1 authorization package](../../contracts/phase-3/p3-6-inventory-r1-authorization-package.json); and
- [completed one-time R1 collection record](p3-6-inventory-r1-collection.md);
- [consumed owner authorization](../../contracts/phase-3/p3-6-inventory-r1-authorization.json);
- [sanitized shared-schema R1](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json);
- [bounded R1 collection evidence](../../contracts/phase-3/p3-6-inventory-r1-collection-evidence.json); and
- [portable CPU R1 admission gap](p3-6-portable-r1-admission-gap.md);
- [sealed non-effective portable R1 admission package](../../contracts/phase-3/p3-6-portable-r1-admission-package.json); and
- [accepted portable R1 `A/A/A/A` policy decisions](../../contracts/phase-3/p3-6-portable-r1-owner-decisions.json); and
- [portable compatibility and generated C1 proposal](p3-6-portable-compatibility-validation-proposal.md);
- [sealed non-authorizing portable compatibility package](../../contracts/phase-3/p3-6-portable-compatibility-validation-package.json); and
- [accepted portable compatibility U3C `A/A/A/A` policy decisions](../../contracts/phase-3/p3-6-portable-compatibility-validation-owner-decisions.json); and
- [portable R1 supply-chain prerequisite proposal](p3-6-portable-r1-supply-chain-prerequisite-proposal.md);
- [sealed non-authorizing portable R1 prerequisite package](../../contracts/phase-3/p3-6-portable-r1-supply-chain-prerequisite-package.json); and
- [accepted portable R1 supply-chain U3D `A/A/A/A/A` policy decisions](../../contracts/phase-3/p3-6-portable-r1-supply-chain-prerequisite-owner-decisions.json); and
- [F: quarantine and scanner binding R0 authorization proposal](p3-6-quarantine-scanner-binding-r0-authorization-proposal.md);
- [sealed non-effective U3E authorization package](../../contracts/phase-3/p3-6-quarantine-scanner-binding-r0-authorization-package.json); and
- [consumed U3E result](../../contracts/phase-3/p3-6-quarantine-scanner-binding-r0-result.json);
- [U3F quarantine remediation R1 decision proposal](p3-6-quarantine-remediation-r1-proposal.md);
- [sealed non-effective U3F decision package](../../contracts/phase-3/p3-6-quarantine-remediation-r1-decision-package.json); and
- [accepted U3F `A/A/A/A/A/A` owner decisions](../../contracts/phase-3/p3-6-quarantine-remediation-r1-owner-decisions.json);
- [U3G quarantine remediation R1 authorization proposal](p3-6-quarantine-remediation-r1-authorization-proposal.md);
- [sealed non-effective U3G authorization package](../../contracts/phase-3/p3-6-quarantine-remediation-r1-authorization-package.json); and
- [consumed U3G authorization](../../contracts/phase-3/p3-6-quarantine-remediation-r1-authorization.json);
- [sanitized U3G result](../../contracts/phase-3/p3-6-quarantine-remediation-r1-result.json);
- [bounded U3G evidence](../../contracts/phase-3/p3-6-quarantine-remediation-r1-evidence.json); and
- [human U3G attempt record](p3-6-quarantine-remediation-r1-attempt.md);
- [U3H quarantine failure analysis R2 decision proposal](p3-6-quarantine-failure-analysis-r2-proposal.md);
- [sealed non-effective U3H decision package](../../contracts/phase-3/p3-6-quarantine-failure-analysis-r2-decision-package.json);
- [accepted U3H planning choices](../../contracts/phase-3/p3-6-quarantine-failure-analysis-r2-owner-decisions.json);
- [U3I transaction runner R0 implementation proposal](p3-6-quarantine-transaction-runner-r0-implementation-authorization-proposal.md);
- [sealed non-effective U3I runner package](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-authorization-package.json);
- [accepted U3I implementation authorization](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-authorization.json);
- [U3I generated/static implementation evidence](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-evidence.json);
- [sealed U3I implementation package](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-package.json);
- [accepted U3I implementation evidence](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json);
- [U3I runtime-binding R0 authorization proposal](p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-proposal.md);
- [sealed non-effective runtime-binding package](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-package.json);
- [U3J storage R2 authorization proposal](p3-6-quarantine-storage-r2-authorization-proposal.md);
- [sealed non-effective U3J storage proposal package](../../contracts/phase-3/p3-6-quarantine-storage-r2-authorization-proposal-package.json);
- [accepted U3J storage planning design](../../contracts/phase-3/p3-6-quarantine-storage-r2-proposal-acceptance.json);
- [P3.6 planning acceptances R0](p3-6-planning-acceptances.md); and
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

Remaining gated backlog requires separate planning and exact later authority:

- retain exact accepted implementation package SHA-256
  `79F29A6828DDBBE5E0967C4498C753DD19D547714CF8934AEFD93A9D6299B3D7`
  and acceptance-record SHA-256
  `06085F3E296B450204FC0E8171314581F40853A11B0AA74161238C390A05B631`;
- retain exact
  `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE` as acceptance of
  source and generated/static evidence only;
- retain the resulting U3M source-only harness implementation authorization
  package SHA-256
  `F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`;
- retain exact
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE` and its
  acceptance-record SHA-256
  `25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9`;
- retain the separate non-effective U3N package SHA-256
  `E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E`
  and obtain exact `D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH`
  before any generated-validation or fresh-runtime-binding attempt;
- retain immutable `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH`
  source-authorization proposal package SHA-256
  `EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311`
  as historical provenance;
- preserve the completed three-source architecture, 64-vector generated Python
  verifier, compatibility tests, and exact sealed source/evidence hashes;
- preserve the proposal's `CreateDirectoryW` exclusive security-at-create
  correction and reject any managed existing-directory return as proof of
  attempt ownership;
- do not parse or import the PowerShell modules, repeat runtime observation
  after the consumed one-attempt authority, or execute `pwsh.exe` or the runner;
- regenerate a future executable U3K package only after accepted handler
  implementation and a current runtime binding; only that future package may
  become eligible for separate `D-P3.6-U3K-STORAGE-R2-AUTH`;
- prepare the Defender-only proposal only after storage evidence is accepted;
  that later attempt also requires separate digest-bound authority;
- treat U3G package digest
  `C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`
  as consumed evidence, not authority to query or modify `F:`, change an ACL,
  query/hash/trust-check or run Defender, use ModelScan, install, acquire,
  execute, validate, implement, admit, or activate anything;
- resolve exact model-family artifacts/data and complete `P36-G1`;
- resolve the accepted portable CPU proposal's exact runtime, resource,
  workload, dependency, artifact, evidence, and activation blockers for
  `P36-G2`;
- treat the completed R1 attempt as consumed, keep R0 immutable, and require a
  new explicit digest-bound authorization before any future collection after
  expiry or invalidation;
- prepare and approve the exact shared `owned_gpu_lab` machine, OS, driver,
  runtime, precision, decoder, resource, and generated-workload manifest;
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

## P3.6 U3M/U3N Current Backlog

- **Complete:** Consume
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH` against
  `F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`.
- **Complete:** Implement the inert validation harness, 20 contract vectors,
  64 handler vectors, Python reference/static checks, and source-only evidence.
- **Complete:** Seal implementation package
  `D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A`.
- **Complete:** Record exact
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE` under
  acceptance-record SHA-256
  `25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9`.
- **Complete:** Prepare the separate non-effective U3N generated-validation
  and fresh-runtime-binding authorization package under SHA-256
  `E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E`.
- **Owner pending:** Exact
  `D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH` against that
  package digest.
- **Not authorized:** U3N execution, U3K preparation or storage, PowerShell,
  runtime observation, machine actions, deployment, and remote Git.

### U3O validation-harness remediation backlog

- **Complete:** Record U3N as a consumed failed-closed attempt under evidence
  SHA-256
  `0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42`.
- **Complete:** Seal source analysis, bounded R1 remediation contract, owner
  proposal, and non-effective package SHA-256
  `17B2142E7F3502724C6653371556DA17F7231D6C56AB0421EC39725556EAA338`.
- **Owner pending:** Exact
  `D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-AUTH`.
- **Blocked:** R1 source/static implementation, separate implementation
  acceptance, U3P retry-package preparation, any PowerShell/runtime attempt,
  and U3K storage work.

### U3O R1 implementation result

- **Complete:** Source-only R1 harness remediation under exact U3O authority.
- **Complete:** Seal harness SHA-256
  `F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3`.
- **Complete:** Seal evidence SHA-256
  `07FF33F19A3C846E69AA8E9C1FD34F9EEBA621BEF1A2424C9173015FB4A0E695`.
- **Complete:** Seal implementation package SHA-256
  `2D9A234A3C1C29276D6D27160849E34DB7440631AC2CD97BEAA650FB48F52E8E`.
- **Complete:**
  `D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-ACCEPTANCE`.
- **Complete:** Prepare and seal the separate non-effective U3P R2 package at
  SHA-256
  `2AFD1D377A68DC35286FE73E58A2B4733BB91BD225BDDBA443472FF76F5603A3`.
- **Complete:** Record
  `D-P3.6-U3P-GENERATED-VALIDATION-RUNTIME-BINDING-R2-AUTH` and consume its
  single attempt without retry.
- **Complete:** Seal failed-closed `result_contract_invalid` evidence SHA-256
  `634674D4C50BB63AAF1A73FFEABB804AC51439002787542E76EB66627A9AD3DE`.

### U3Q R2 bootstrap-remediation backlog

- **Complete:** Analyze the zero-stdout result without inspecting retained-free
  stderr or executing PowerShell again.
- **Complete:** Define exact `$PSHOME` Utility bootstrap, seven-command local
  `NoClobber` allowlist, provenance checks, and module-independent failure JSON.
- **Complete:** Seal non-effective source-only package SHA-256
  `5EC2889439E81B9F955FE7C3864A0931466458EAFA77C5797E44B24DC9AB0B47`.
- **Complete:** Record exact
  `D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-AUTH`
  authorization and compatibility-test amendment before their changes.
- **Complete:** Implement exact-path Utility bootstrap and pass 427
  generated/static Phase 3.6 checks.
- **Complete:** Seal evidence SHA-256
  `90F3F6F42C73F573A82D1BF5C790B217F891B23D97198916A17FD436B94A8591`
  and implementation package SHA-256
  `2D59FA211DE5DFE331128F189400A28D0D30FAF1BD5C01F077EB6FECF4C236FF`.
- **Complete:** Record exact
  `D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-ACCEPTANCE`
  as acceptance record SHA-256
  `32BA42A51029920AE163866A923547CD16054D6C41ECD3C8EC5549B78FB3ED2E`.
- **Authorized:** Prepare one separate non-effective U3R planning package.
- **Blocked:** PowerShell/runtime retry, U3R execution, U3K storage, profile
  activation, deployment, and remote Git.
- **Complete:** Seal non-effective U3R R3 authorization package SHA-256
  `A912EF51629A3E73FFF2ECE7AAB8A7D3017A659F9FB75F5402A90027D4B53D98`.
- **Owner pending:** Exact
  `D-P3.6-U3R-GENERATED-VALIDATION-RUNTIME-BINDING-R3-AUTH`.
- **Blocked:** Every U3R observation or attempt, U3K, machine/storage action,
  profile activation, deployment, and remote Git.

## P3.6 U3S Dual Controller R0

- **Completed:** Sanitized U3R failure records and failure analysis.
- **Completed:** A+B/A/A/A architecture acceptance, with PowerShell as the
  authoritative Windows controller and Python as the machine-disabled oracle.
- **Completed:** Non-effective source-only implementation contract, 192-vector
  test plan, proposal, and package digest
  `3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC`.
- **Owner pending:** Exact
  `D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH`.
- **Blocked:** Source/test implementation, Python reference execution,
  PowerShell parsing/import/execution, runtime observation, U3T, U3K,
  deployment, and remote Git.

### U3S dual-controller source implementation

- **Completed:** Exact source implementation authorization and exact one-test
  compatibility amendment.
- **Completed:** Canonical contract, 192-vector manifest, PowerShell source,
  machine-disabled Python reference, and four focused test modules.
- **Validated:** 244 focused tests, 705 full P3.6 tests, and 100 percent Python
  branch coverage.
- **Sealed:** Package SHA-256
  `484A6FB71216F43A1EAF668DC59091D4FD42EF8543585BFBB588CFCDE089BE30`.
- **Owner pending:**
  `D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-ACCEPTANCE`.
- **Blocked:** PowerShell parser/runtime, Python machine access, runtime and
  manifest observation, U3T attempt, U3R retry, U3K, deployment, and remote Git.
