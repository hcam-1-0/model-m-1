# Data And Model Governance

## Data Entry Rule

No media enters Phase 3 merely because it is technically reachable. Each
dataset requires an owner, lawful/authorized purpose, provenance, license or
authorization record, allowed uses, retention, access policy, and deletion
procedure before download, annotation, training, or evaluation.

Allowed initial sources are:

- programmatically generated scenes and plates;
- team-created media with documented consent and purpose;
- public datasets after license, provenance, geography, bias, and redistribution
  review;
- private-lab media from an owned and authorized isolated camera under a
  separate test protocol.

Sentinel live video, Government data, police records, scraped footage, and
unreviewed internet video are excluded.

## Dataset Registry Record

Every immutable dataset version records:

- dataset ID, semantic version, content manifest, and manifest digest;
- owner, steward, approver, purpose, capabilities, and risk tier;
- source and collection method, dates, geography, and camera conditions;
- license/authorization document and allowed/prohibited uses;
- sensitive-data classification and whether people or plates are present;
- storage location, encryption, access group, retention, and deletion date;
- label taxonomy and annotation-tool/export versions;
- train/validation/test split method and leakage controls;
- known gaps, imbalance, ambiguity, and excluded slices;
- annotation QA method and measured agreement/error rate;
- transformations and lineage to parent datasets.

Dataset bytes, frames, annotations containing sensitive media, and credentials
must not be committed to Git. Git stores schemas, manifests without sensitive
paths, generated test fixtures, and documentation only.

## Split And Leakage Policy

- Freeze the test set before model selection.
- Split by source scene, sequence, camera, and capture session where applicable,
  not by random adjacent frames.
- Keep near-duplicate frames and tracks in one split.
- Keep synthetic generation seeds and templates partitioned when they could
  leak exact appearances.
- Record every test-set access and prohibit tuning directly against final test
  results.
- Maintain a small contract fixture set separately from accuracy benchmarks.

## Annotation System

The annotation schema, not the UI tool, is authoritative. CVAT is a candidate
because it supports video tracks and interpolation, but exports must be
normalized and versioned.

Required annotation behavior:

- controlled class and attribute taxonomy;
- bounding-box, occlusion, truncation, visibility, and ignore-region rules;
- track continuity and split/merge guidance;
- plate region and transcription rules for synthetic/authorized ANPR;
- scenario event start/end definitions;
- annotator identity or pseudonymous ID, timestamps, tool version, and review;
- double annotation or expert adjudication on a risk-based sample;
- automated geometry, class, sequence, and orphan-track validation.

An annotation guide and calibration exercise must exist before labeling at
scale.

## Model Registry Record

Every immutable model version records:

- model ID, task/capability, source, architecture/family, and artifact digest;
- license and use restrictions for code, weights, training data, and exports;
- training code commit, environment lock, parameters, random seeds, and run ID;
- dataset versions and exact split manifests;
- input, preprocessing, output, taxonomy, and postprocessing contracts;
- hardware/runtime/precision compatibility and export-parity results;
- complete metric report, slice report, robustness tests, and known failures;
- model card, intended use, prohibited use, risk tier, and expiry/review date;
- artifact signature, dependency/model bill of materials, and security scan;
- approvals, deployment history, rollback target, and retirement state.

Mutable aliases such as `candidate`, `shadow`, and `champion` are pointers for
workflow convenience. The deployed assignment and every emitted event record
the resolved immutable version.

## Promotion Gates

A model/pipeline combination can move to a controlled lab only when:

1. data, license, and purpose reviews pass;
2. artifacts and build lineage are complete and verifiable;
3. contract and export-parity tests pass;
4. frozen accuracy and slice reports meet owner-approved targets;
5. resource, latency, overload, and recovery tests pass on declared hardware;
6. security, privacy, misuse, and human-review controls pass;
7. rollback is rehearsed and previous versions remain available;
8. the accountable owner signs the record after confirming technical, data,
   security, and product evidence. Separate specialty approvers are optional.

The same accountable owner may own, review, and approve dataset and model
records. Provenance, license, privacy, security, retention, deletion, quality,
and reproducibility evidence remain mandatory and cannot be waived by combining
roles.

Production promotion is not part of initial Phase 3 authorization.

## Experiment Reproducibility

An evaluation report must be reproducible from:

- immutable dataset and annotation manifests;
- immutable model artifact and source commit;
- locked Python/native dependencies and container digest;
- deterministic seeds where supported;
- declared hardware and runtime profile;
- versioned preprocessing, postprocessing, thresholds, tracker, and rules;
- exact evaluation command and metric implementation version.

Nondeterministic kernels or runtime differences must be declared with repeated
runs and tolerance bounds.

## Drift And Monitoring

Phase 3 plans monitoring in three layers:

- **input drift:** resolution, codec, brightness, blur, scene, object size, and
  class-frequency changes without storing raw frames in metrics;
- **output drift:** class/confidence/count distributions and invalid output
  rates;
- **quality drift:** periodic authorized reviewed samples or synthetic canaries
  compared with reference labels.

Drift signals do not trigger automatic retraining or promotion. They open a
review, may suspend a capability, and require fresh governance and evaluation.

## Rollback And Retirement

- Assignments change by audited version switch, never artifact mutation.
- Rollback restores model, pipeline, taxonomy, thresholds, and tracker/rule
  configuration as one compatible unit.
- Retirement prevents new assignments while preserving lineage and evidence.
- Data and artifacts are deleted only under retention and legal-hold policy;
  deletion is recorded and independently verifiable.
