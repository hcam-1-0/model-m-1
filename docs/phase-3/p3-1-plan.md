# P3.1 Data And Evaluation Foundation Plan

Status: planning complete and authorized for implementation under
`D-P3.1-001` on 2026-08-24.

Accountable owner: `mayank-admin`.

Review mode: `accountable_owner_review_sufficient`. Separate-person review is
optional and non-blocking. Evidence requirements remain mandatory.

## Objective

P3.1 creates the reproducible data and evaluation foundation required before
any detector, tracker, OCR component, or runtime can be implemented or compared.
It turns dataset, artifact, annotation, fixture, metric, and evaluation claims
into immutable machine-readable records.

P3.1 does not select a production champion and does not implement inference.

## Dependencies

- P3.0 status is `accepted` with zero technical failures and zero manual gates.
- The owner-approved emitted taxonomy is person, bicycle, motorcycle, car, bus,
  truck, and unknown.
- P3.0 event, geometry, runtime-adapter, lineage, privacy, and fail-closed
  contracts remain authoritative.
- DR-0016, DR-0017, DR-0019, DR-0020, DR-0021, DR-0022, and DR-0026 remain in
  force.

## Authorized Scope

P3.1 implementation may create:

- immutable dataset, fixture, annotation, model-candidate, evaluation-run, and
  metric-report schemas;
- deterministic generated metadata fixtures and small programmatically
  generated synthetic assets with no external source material or real-person
  likeness;
- detection, stream-local tracking, line/zone, occupancy, dwell, and
  synthetic-plate ground-truth fixtures;
- annotation instructions, normalization rules, validators, QA reports, and
  split/leakage checks;
- an offline metric harness over generated fixtures;
- metadata-only candidate records for the selected model portfolio;
- source, license, provenance, and security research records without downloading
  datasets or model artifacts; and
- clean-machine reproducibility, evidence indexing, and owner-approval records.

## Not Authorized

P3.1 authorization does not permit:

- external dataset, model, checkpoint, weight, font-pack, or binary download;
- training, fine-tuning, export, inference, decoding, or GPU execution;
- Sentinel video, live CCTV, physical cameras, Government data, private data,
  scraped media, or unreviewed internet content;
- team-created media until its exact consent, purpose, retention, and source
  record is separately owner approved;
- persistence of raw camera frames, crops, clips, or video;
- face recognition, person re-identification, cross-camera identity, sensitive
  traits, watchlists, owner lookup, predictive policing, or autonomous action;
- operational alerts, real-camera validation, pilot use, production deployment,
  or statewide-scale claims; or
- P3.2 detector implementation or activation of P3.0 assignments.

## Source Tiers

| Tier | Source | P3.1 state | Entry requirement |
| --- | --- | --- | --- |
| `S0` | Generated metadata and deterministic programmatic assets | Authorized | Generator version, seed, template digest, intended use, and no-external-input proof |
| `S1` | Team-created media | Planning only | Consent, purpose, subject/plate handling, retention, access, and deletion record |
| `S2` | Public datasets or fonts | Research only | Exact source/version, license text, provenance, allowed uses, privacy, redistribution, hash plan, and owner approval before download |
| `S3` | Public model code or artifacts | Research only | Exact repository commit/artifact, code/weight/data license, lineage, model card, security review, hash plan, and owner approval before download |
| `S4` | Owned private-lab camera media | Prohibited in P3.1 | New explicit camera/media authorization and isolated protocol |
| `S5` | Sentinel, Government, police, scraped, or third-party private data | Prohibited | Outside P3.1; no implicit approval path |

CI must use `S0` only and must not require network access, a GPU, or secrets.

## Contract Package

P3.1 will define the following versioned records.

### DatasetManifestV1

Required fields:

- immutable dataset ID, semantic version, manifest digest, status, and purpose;
- source tier, source identity, collection/generation method, authorization, and
  license record;
- content inventory by type, class, slice, sequence, and split without local
  paths or media bytes;
- taxonomy, annotation schema, transformation lineage, and parent manifests;
- sensitive-data classification, retention, access, deletion, and export rules;
- split method, group keys, duplicate/leakage results, known gaps, and exclusions;
- owner approval record, timestamps, and expiry/review date.

### FixtureManifestV1

Required fields:

- fixture suite ID/version/digest and deterministic generator identity;
- seeds, template/configuration digests, expected contracts, and expected
  failures;
- class/slice/scenario coverage and declared omissions;
- generated-only assertion and prohibited-source assertion;
- canonical file inventory and per-file hashes.

### AnnotationSpecificationV1

Required fields:

- taxonomy version, annotation task, geometry semantics, attribute vocabulary,
  ignore/uncertain/occluded/truncated rules, and track lifecycle rules;
- plate region/transcription rules for generated synthetic plates only;
- import/export format version and normalization rules;
- automated validation rules, QA sample policy, adjudication policy, and error
  thresholds proposed from calibration evidence;
- owner approval record and version history.

### CandidateArtifactManifestV1

P3.1 records metadata for `DET-R0`, `DET-E1`, `DET-B1`, `DET-A1`, `TRK-R0`,
`OCR-L0`, `OCR-L1`, `OCR-D0`, `OCR-G0`, `OCR-G1`, and `PLATE-D0`.

The record contains intended role, exact source/artifact fields, license fields,
hash fields, lineage fields, supported taxonomy, runtime/export expectations,
known limits, and eligibility status. Initially unavailable values are explicit
`unresolved` blockers, never fabricated or inferred.

### EvaluationRunManifestV1

Required fields:

- run ID/time, source commit, dirty-worktree state, operator, command, and seed;
- dataset/fixture, candidate, pipeline, taxonomy, metric, and configuration
  digests;
- hardware, OS, runtime, precision, dependency lock, and container profile;
- warmup, repetitions, batch/concurrency, timeout, and resource limits;
- result artifact hashes, failed gates, warnings, and reproducibility status.

### MetricReportV1

Required fields:

- metric suite/version, population and slice definitions, sample counts, and
  confidence/uncertainty fields;
- per-class/per-slice values and aggregate values without hiding failed slices;
- invalid/abstained/missing prediction handling;
- comparison baseline, regressions, hard-gate outcomes, and machine-readable
  failure reasons;
- canonical serialization and report digest.

## Generated Fixture Matrix

| Suite | Minimum cases |
| --- | --- |
| Detection | Every approved emitted class, empty scene, unknown class, overlap, truncation, occlusion, small object, low contrast, and malformed prediction |
| Tracking | Start/update/end, occlusion, crossing tracks, duplicate detection, missed frames, discontinuity, reconnect, epoch reset, and bounded state |
| Geometry | Both line directions, touch-without-cross, boundary jitter, zone enter/exit, occupancy, dwell threshold, schedule inactive, duplicate and late input |
| Synthetic plate | Generated Latin, Devanagari, and Gujarati strings; region geometry; abstention; invalid format; alternatives; no owner or watchlist fields |
| Contract misuse | Paths, URLs, credentials, media bytes, biometric fields, owner records, Government fields, oversized payloads, and invalid hashes |

Generated fixtures must be deterministic, small enough for Git/CI, free of
secrets and external content, and reproducible from a versioned generator.

## Annotation And QA Plan

1. Freeze the taxonomy and annotation specification version used by a task.
2. Calibrate on generated examples before any authorized human labeling.
3. Validate class IDs, geometry bounds, sequence ordering, track continuity,
   orphan references, transcription vocabulary, and required attributes.
4. Record annotator or pseudonymous operator ID, tool/export version, timestamps,
   and normalization version.
5. Use risk-based duplicate annotation or adjudication when human labels are
   later authorized; accountable-owner approval is sufficient.
6. Produce a machine-readable QA report with item counts, invalid counts,
   corrected counts, disagreement/error measurements, and unresolved blockers.

No labeling at scale starts from planning authorization alone.

## Split And Leakage Plan

- Freeze final test manifests before candidate selection.
- Group sequences by generator family/seed/template and, for future authorized
  media, by source scene, camera, session, and track.
- Keep adjacent/near-duplicate frames and track fragments in one split.
- Partition synthetic templates and appearance seeds where exact appearances
  could leak.
- Detect exact digest duplicates and configured perceptual/metadata near
  duplicates once media is authorized.
- Record every final-test access; tuning against the final test set is forbidden.
- Fail validation when a required group key is absent or appears in multiple
  splits.

## Metric Harness Plan

The initial harness is offline and generated-fixture-only.

- Detection: AP/mAP inputs, precision, recall, F1, confusion matrix, duplicate
  and missed-object accounting, and calibration inputs.
- Tracking: HOTA/IDF1-compatible sequence records, identity switches,
  fragmentation, start/end delay, and epoch correctness.
- Geometry/events: precision, recall, duplicate rate, onset/termination error,
  false events per generated stream-hour, and deterministic replay.
- Synthetic ANPR: plate-region overlap, exact normalized match, character error,
  top-k coverage, script routing, and abstention.
- System evidence: run validity, manifest completeness, reproducibility, and
  hard-gate result.

Golden reports use hand-computable fixtures. Metric implementations must be
cross-checked against those expected values before candidate evidence is valid.
No numeric promotion threshold is approved until a measured baseline exists.

## Work Packages

| ID | Work package | Primary role | Supporting roles | Exit evidence |
| --- | --- | --- | --- | --- |
| `P31-W1` | Manifest and report contracts | Lead/system architect | Backend, data/quality | Schemas, canonical fixtures, strict/compatible parsing, bounds and privacy tests |
| `P31-W2` | Deterministic generated fixtures | CV engineer | Data/quality, backend | Generator manifest, hashes, coverage matrix, generated-only proof |
| `P31-W3` | Annotation specification and validators | Data/GIS/quality | CV, frontend/operator | Guide, schema, calibration fixtures, validation and QA golden report |
| `P31-W4` | Split, duplicate, and leakage controls | Data/GIS/quality | CV, backend | Grouped split fixtures, negative leakage tests, machine report |
| `P31-W5` | Offline metric harness | CV engineer | Backend, data/quality | Golden metrics, slice reports, invalid-input and determinism tests |
| `P31-W6` | Candidate selection manifest | CV engineer | Lead, infrastructure | Metadata-only portfolio records with unresolved blockers explicit |
| `P31-W7` | License/provenance source intake | Data/GIS/quality | Lead, infrastructure | Exact-source dossiers; no downloads; owner decisions per source |
| `P31-W8` | Reproducible baseline and numeric-gate proposal | Infrastructure | CV, data/quality | Hardware/run manifest, clean-machine command, baseline, proposed gates |
| `P31-W9` | Acceptance evidence and P3.2 handoff | Lead/system architect | All roles | Evidence index, known limits, owner acceptance, explicit P3.2 blockers |

## Delivery Sequence

1. Implement W1 contracts and deterministic serialization.
2. Implement W2 generated fixtures and coverage inventory.
3. Implement W3/W4 annotation, QA, split, and leakage validators.
4. Implement W5 metrics with hand-computable golden reports.
5. Populate W6 metadata-only portfolio records.
6. Complete W7 source dossiers without downloading artifacts.
7. Run W8 generated baseline on the declared developer profile.
8. Complete W9 evidence review and request owner acceptance.

W1-W5 may proceed in parallel where contracts are stable. W6/W7 cannot mark an
artifact eligible without exact source evidence. W8 cannot run a candidate model
until that artifact and input dataset receive explicit owner authorization.

## P3.1 Acceptance Criteria

P3.1 is complete only when:

- all six contract families are versioned, bounded, canonical, and tested;
- every tracked fixture is generated, deterministic, source-safe, and hashed;
- annotation, QA, split, and leakage validators pass positive and negative
  golden cases;
- metric implementations match hand-computable golden reports;
- candidate records expose every unresolved artifact/license/data blocker;
- no test, build, or CI job downloads data/models or requires network/GPU access;
- no prohibited media, identity, credential, owner, watchlist, Government, or
  sensitive telemetry field exists;
- the developer hardware and clean-machine run are reproducible;
- the first baseline and proposed numeric gates are recorded without claiming
  promotion;
- the accountable owner accepts the evidence and limitations; and
- P3.2 remains blocked until an exact detector artifact and dataset are owner
  approved.

## Risks And Controls

| Risk | Control |
| --- | --- |
| Synthetic fixtures are too simple | Slice matrix, adversarial/negative cases, and explicit external-validity limitation |
| Hidden license mismatch | Exact artifact-level records; repository license never substitutes for weight/data terms |
| Train/test leakage | Grouped immutable splits, duplicate checks, access log, and fail-closed validator |
| Metric implementation error | Hand-computable goldens, versioned formulas, and independent library comparison where available |
| Local hardware is underpowered | Manifest the constraint; use it for correctness baselines, not statewide capacity claims |
| Review roles are combined | Preserve immutable evidence, automated checks, owner identity, reason, time, and audit record |
| P3.1 expands into inference | No weights/downloads/runtime/media authorization; P3.2 remains a separate gate |

## Authorization Result

This plan and its bounded implementation scope are authorized under
`D-P3.1-001`. Planning authorization is complete. P3.1 implementation and exit
evidence are not yet complete and must not be represented as accepted.
