# Phase 3 Decision Register

Phase 2 decisions DR-0006 through DR-0013 remain active. This register begins
at DR-0014 and does not silently alter accepted earlier decisions.

Owner decision: `D-P3.0-001` accepted on 2026-08-24 against Phase 3 package
digest `57D2F541C4AA9AB8988A5DF7FC228DA4047BF471B64AD704BDB478308FDC3898`.
This accepts the planning baseline and the five proposed decisions below. It did
not itself authorize implementation to start; the later explicit instruction
`start to build on phase 3` opened only the bounded P3.0 gate.

Owner authorization: `D-P3.1-001` recorded on 2026-08-24. It completes P3.1
planning and authorizes only the generated-only implementation scope in
[`p3-1-authorization.json`](../../contracts/phase-3/p3-1-authorization.json).
It does not accept P3.1 implementation or authorize downloads, inference,
cameras/media, P3.2, pilots, or deployment.

Owner acceptance: `D-P3.1-ACCEPTANCE` recorded on 2026-08-24 against package
digest `956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618`.
It accepts the generated-only P3.1 evidence and documented limitations. It does
not authorize P3.2 or any excluded data, artifact, runtime, media, camera, or
deployment activity.

## Decisions

### DR-0014: Anonymous Analytics Boundary

Status: inherited baseline.

Phase 3 produces observations, stream-local tracks, and analytic events. It
does not produce identities, cross-camera entities, watchlist matches,
Government-data matches, or operational alerts.

Reason: preserves the accepted roadmap boundary and prevents detection output
from becoming an ungoverned policing decision.

### DR-0015: Synthetic-First Media And Data

Status: inherited baseline.

Initial development and CI use generated, synthetic, team-consented, or
explicitly authorized and license-reviewed media. Sentinel remains metadata
only. No reachable CCTV feed is assumed authorized for analytics or training.

Reason: authorization and provenance are prerequisites, not later cleanup.

### DR-0016: Contract-First Runtime Isolation

Status: accepted under `D-P3.0-001` on 2026-08-24.

H-CAM owns normalized observation/event contracts and a runtime adapter API.
DeepStream, Triton, ONNX Runtime, OpenVINO, model families, trackers, and OCR
engines remain replaceable implementations behind those contracts.

Reason: permits measured hardware-specific optimization without leaking vendor
types into the product domain.

### DR-0017: Portable Reference Before Acceleration

Status: accepted under `D-P3.0-001` on 2026-08-24.

Build one deterministic CPU reference path, proposed as ONNX Runtime CPU when
export parity succeeds, before selecting accelerated production candidates.
Compare accelerators against frozen inputs, outputs, metrics, and manifests.

Reason: keeps CI and development reproducible and gives performance experiments
a behavioral baseline.

### DR-0018: No Raw-Media Persistence By Default

Status: inherited baseline with Phase 3 extension.

Analytics workers process media in memory and emit bounded derived metadata.
Frame, crop, clip, and video persistence is disabled until a separate evidence,
retention, access, chain-of-custody, and authorization design is approved.

Reason: data minimization lowers privacy, breach, and storage risk.

### DR-0019: Immutable Model/Dataset Lineage

Status: accepted under `D-P3.0-001` on 2026-08-24.

Every emitted observation resolves to immutable model, pipeline, taxonomy, and
policy versions. Dataset/model versions have manifests and digests; mutable
aliases never replace the resolved version in evidence.

Reason: model results cannot be reproduced, audited, or rolled back without
complete lineage.

### DR-0020: Risk-Tiered Capability Promotion

Status: accepted under `D-P3.0-001` on 2026-08-24.

Tier A foundation analytics share the Phase 3 gate. Tier B scenario analytics
need capability-specific data and policy approval. Tier C high-consequence
hypotheses need separate decision records and human-response analysis.

Reason: capability risk and false-positive consequences differ materially.

### DR-0021: At-Least-Once Stream-Partitioned Events

Status: accepted under `D-P3.0-001` on 2026-08-24.

Analytics reuse the transactional outbox pattern, deduplicate by event ID, and
partition by stream ID. Stream-local ordering is preserved where source
sequence exists; no global ordering is promised.

Reason: aligns with the current platform and makes duplicates, late data, and
failure recovery explicit.

### DR-0022: Role-Based Model Portfolio

Status: selected for planning by explicit owner instruction on 2026-08-24;
implementation and artifacts remain unauthorized.

Phase 3 evaluates a portfolio rather than declaring one universal model:
YOLOX-Tiny is the portable reference, D-FINE-N the low-compute challenger,
RF-DETR-S the balanced detector candidate, RF-DETR-L the accuracy detector
candidate, and ByteTrack the anonymous per-camera tracker. OCR is split between
PP-OCRv6 small/medium for supported Latin text, PP-OCRv5 Devanagari mobile for
Devanagari, and Tesseract `guj` fast/best for Gujarati. Plate localization uses
a dedicated model derived from the promoted H-CAM detector family and approved
synthetic or authorized data.

Reason: "best" depends on hardware, latency, quality slice, script, license,
and operational cost. A fixed portfolio enables fair evidence while preserving
the runtime and model replacement boundaries in DR-0016/DR-0017.

Non-authorization: this decision does not approve a checkpoint, model or
dataset download, training, inference, implementation, real-camera data,
restricted analytics, champion model, runtime, pilot, or deployment.

### DR-0023: Owner-Approved Minimal Tier A Scope

Status: owner approved under P3-G1 on 2026-08-24; separate review not required.

The emitted class set is person, bicycle, motorcycle, car, bus, truck, and
unknown. The approved capabilities are object detection, stream-local tracking,
line crossing, zone entry/exit, occupancy, and dwell duration using the existing
normalized geometry and schedule semantics. Site-specific geometry and every
model/dataset mapping remain owner-approved artifacts with mandatory evidence.

Synthetic ANPR, Tier B/C analytics, identity, sensitive traits, watchlists,
Government matching, operational alerts, and autonomous enforcement are not
included.

### DR-0024: Synthetic-Lab Derived-Metadata Policy

Status: owner approved under P3-G2 on 2026-08-24; separate review is not
required and executable enforcement remains pending.

The policy uses data-class-specific retention from zero to 90 days, restricted
access for event-level observations and local tracks, identifier-free metrics,
daily deletion, bounded backup retention, delete-before-access restore, no raw
media, no exports, no plate-text persistence, and no training reuse without a
new purpose approval. It applies only to the synthetic lab.

The accountable owner is `mayank-admin`. `mahin-eleveted`, role `member`, remains
an optional reviewer whose sign-off is not required.

### DR-0025: Accountable-Owner Self-Review For P3-G4

Status: accepted on 2026-08-24; P3-G4 complete.

`mayank-admin` explicitly accepted P3.0 as main developer and team lead after
reporting that `mahin-eleveted` was unavailable. The owner then removed the
P3-G4 restriction on team-lead self-review. Accountable-owner evidence review is
sufficient for this bounded milestone, and separate reviewer sign-off is
optional.

Reason: reviewer availability must not block the bounded P3.0 milestone after
the accountable owner has reviewed its machine-verifiable evidence and accepted
the documented limitations.

### DR-0026: Accountable-Owner Review For Later Phase 3 Gates

Status: accepted on 2026-08-24.

Mandatory separate-person review is disabled for model promotion, operational
geometry, datasets, and deployment. `mayank-admin` may own, review, and approve
those records. Optional peer or specialist review remains allowed but cannot
block the accountable-owner decision.

This combines approval roles only. Exact artifact identity, license,
provenance, privacy, security, validation, benchmark, rollback, audit, and
explicit deployment-authorization evidence remain mandatory.

### DR-0027: Manifest-First Generated P3.1 Foundation

Status: accepted under `D-P3.1-001` on 2026-08-24.

P3.1 implements versioned dataset, fixture, annotation, candidate-artifact,
evaluation-run, and metric-report records before any model artifact or runtime
is used. Direct test inputs are deterministic generated metadata or small
programmatic assets with seeds, generator identity, inventory, and hashes.

Reason: claims about data, metrics, and candidates need immutable provenance and
reproducible evidence before model comparison can be trusted.

### DR-0028: Six-Tier Source Authorization

Status: accepted under `D-P3.1-001` on 2026-08-24.

`S0` generated sources are authorized. `S1` team media is planning-only and
requires an exact consent/purpose/retention record. `S2` public data/fonts and
`S3` public model code/artifacts are research-only with no downloads. `S4`
private-lab camera media requires new authorization. `S5` Sentinel, Government,
police, scraped, and private third-party data is prohibited.

Reason: source discovery is not permission to obtain or process an artifact.

### DR-0029: Grouped Immutable Splits And Leakage Failure

Status: accepted under `D-P3.1-001` on 2026-08-24.

Evaluation splits are immutable and grouped by generator family, seed, and
template. Future authorized media also groups by source scene, camera, session,
and track. Missing required group keys, digest duplicates, or groups spanning
splits fail validation. Final-test access is recorded and cannot guide tuning.

Reason: nearby frames, track fragments, and reused templates can produce false
accuracy claims when split independently.

### DR-0030: Golden Metrics Before Numeric Promotion Gates

Status: accepted under `D-P3.1-001` on 2026-08-24.

Metric implementations must match hand-computable generated goldens and report
all classes, slices, invalid inputs, abstentions, and failures. Numeric model
promotion targets remain proposals until a reproducible measured baseline is
recorded and approved by the accountable owner.

Reason: an unvalidated metric or arbitrary threshold cannot support artifact
promotion.

## P3.1 Implementation Evidence Status

The bounded `D-P3.1-001` implementation now has zero technical verifier
failures under evidence package digest
`956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618`.
All 11 candidate records remain blocked, every numeric threshold is
`proposal_only`, downloaded artifacts remain zero, and P3.2 remains blocked.

The baseline is bound to clean implementation commit
`be7749d4315f46a49370b65f14c6e583e51a0c6e`. This is not a new authorization or
an authorization for later work. Accountable-owner P3.1 exit acceptance is
recorded in `D-P3.1-ACCEPTANCE`; P3.1 is accepted.

## Decisions Required During P3.1 Or Before P3.2

The [P3.2 entry decision packet](p3-2-entry-decision-packet.md) converts these
open items into ordered, fail-closed owner records. It is planning evidence
only; `D-P3.2-START` remains `not_authorized`.

| Decision | Evidence required | Blocks |
| --- | --- | --- |
| Exact `S1`-`S4` source use | Consent/license, provenance, privacy, retention, hash, and owner record | Any non-generated P3.1 input |
| Exact portfolio artifacts | Commit, checkpoint, weight/model/data license, lineage, hash, model card, SBOM, and owner approval | P3.2/P3.3/P3.5 |
| Portfolio champion and fallback | Frozen H-CAM baseline, slice/resource/downstream results, owner approval, and ADR | Promotion/deployment |
| CPU reference runtime | Export parity and clean-machine smoke | P3.2 |
| Target accelerator/lab hardware | Reproducible hardware manifest | Runtime/model performance gates |
| Numeric accuracy and latency gates | Frozen baseline and operator/risk needs | Model promotion |
| Metadata retention | Data classification and operational purpose | Persistence |
| Artifact/model registry | Security, operations, access, and complexity review | P3.7 |

## Decisions Explicitly Deferred

- production accelerator/runtime and GPU fleet;
- Kubernetes or another production orchestrator;
- Tier B/C implementation order;
- persistent evidence media;
- cross-camera correlation or person/vehicle identity;
- Government databases, watchlists, owner records, and alert policy;
- statewide procurement, capacity, data residency, and production SLOs.

Deferred means unapproved, not implicitly allowed.
