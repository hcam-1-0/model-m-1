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
All 11 accepted P3.1 candidate records remain blocked and every numeric
threshold is `proposal_only`. `D-P3.2-001` separately authorized controlled
public-artifact quarantine and offline research; it did not alter the accepted
P3.1 package or itself authorize P3.2 implementation. The later exact P3.2
records do not modify this historical package.

The baseline is bound to clean implementation commit
`be7749d4315f46a49370b65f14c6e583e51a0c6e`. This is not a new authorization or
an authorization for later work. Accountable-owner P3.1 exit acceptance is
recorded in `D-P3.1-ACCEPTANCE`; P3.1 is accepted.

## P3.2 Entry Decision Status

The [P3.2 entry decision packet](p3-2-entry-decision-packet.md) records the
ordered, fail-closed owner decisions. The
[P3.2 start authorization](p3-2-start-authorization.md) is now
`owner_authorized` for the exact generated-only local CPU scope; this starts but
does not complete P3.2.

`D-P3.2-001` was authorized by `mayank-admin` on 2026-08-24 for controlled
model/dataset downloads and offline experiments. The exact controls and
continuing exclusions are in the
[P3.2 controlled research record](p3-2-research-record.md).

- `D-P3.2-002`: `owner_approved_restricted` for exact artifact
  `DET-R0-ONNX-UPSTREAM-0.1.1RC0` and its SHA-256 only;
- `D-P3.2-003`: `owner_approved_generated_only` for `DATA-GEN-R0`, with no
  public dataset, real media, or accuracy claims;
- `D-P3.2-004`: `owner_approved_cpu_reference` for the exact pinned ONNX Runtime
  CPU preprocessing, decoder, mapping, parity, and resource contract; and
- `D-P3.2-START`: `owner_authorized` for the named generated-only work packages,
  expiring 2026-09-24.

The authorized research pass acquired one exact 20,219,662-byte ONNX artifact
with SHA-256
`427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`.
Two generated-input CPU observations produced the same output digest. Immutable
license and algorithm evidence, a model card, SPDX inventory, generated-only
dataset record, runtime contract, and exact start record now bind that research
to the authorized scope. They do not establish accuracy, fairness,
representativeness, model promotion, media access, or deployment readiness.

| Decision | Evidence required | Blocks |
| --- | --- | --- |
| Exact `S1`-`S4` source use | Consent/license, provenance, privacy, retention, hash, and owner record | Any non-generated P3.1 input |
| Exact portfolio artifacts | Commit, checkpoint, weight/model/data license, lineage, hash, model card, SBOM, and owner approval | P3.2/P3.3/P3.5 |
| Portfolio champion and fallback | Frozen H-CAM baseline, slice/resource/downstream results, owner approval, and ADR | Promotion/deployment |
| CPU reference runtime exit | Generated end-to-end parity and clean-machine implementation smoke | P3.2 exit |
| Target accelerator/lab hardware | Reproducible hardware manifest | Runtime/model performance gates |
| Numeric accuracy and latency gates | Frozen baseline and operator/risk needs | Model promotion |
| Metadata retention | Data classification and operational purpose | Persistence |
| Artifact/model registry | Security, operations, access, and complexity review | P3.7 |

### DR-0031: Exact Generated-Only CPU Detection Slice

Status: accepted under `D-P3.2-ACCEPTANCE` on 2026-08-25.

The only activatable P3.2 assignment is the exact `DET-R0` artifact, approved
Tier A taxonomy, generated-data policy, ONNX Runtime CPU contract, and
`generated_only` scope. The runtime is default-off, forbidden in production,
and model bytes remain outside Git and packages. Inputs are created server-side
from bounded seeds and consumed through short-lived memory leases. Only
normalized anonymous metadata and transactional outbox events persist.

Reason: an exact digest-bound activation contract prevents the generic P3.0
assignment API from becoming an implicit model, data, or deployment
authorization. See [P3.2 implementation](p3-2-implementation.md).

### DR-0032: Generated-Only Anonymous Stream-Local Tracking

Status: accepted under `D-P3.3-ACCEPTANCE` on 2026-08-25.

P3.3 adapts the motion/IoU association structure of exact pinned ByteTrack
source behind an H-CAM-owned tracker interface. Inputs are sealed generated
structured Tier A observations. Tracks are scoped to one stream and epoch, with
no appearance features, identity, ReID, plate data, cross-camera key, media, or
external dataset. Runtime activation is default-off and production-forbidden.

The full historical ByteTrack runtime is rejected. TrackEval is used only as a
pinned evidence oracle, and SciPy supplies the runtime assignment solver. Exact
source manifests, license notices, generated parity reports, SBOM, PostgreSQL
evidence, and final package binding are accepted under the exact historical
package digest. P3.4, real media,
deployment, and remote Git actions are not authorized by this decision.

### DR-0033: P3.4 Geometry And Event Planning Baseline

Status: accepted under `D-P3.4-ACCEPTANCE` for the immutable generated-only
implementation package.

P3.4 planning uses accepted anonymous stream-local P3.3 lifecycle v2 as its only
observation dependency. The recommended baseline uses normalized image-space
geometry, a separately versioned rule contract, explicit anchor and boundary
semantics, hysteresis-backed line/zone/dwell/occupancy state machines, UTC event
time, IANA schedules, bounded lateness, deterministic event IDs, transactional
outbox, inherited short retention, and sealed generated C10 evidence.

On 2026-08-25, `mayank-admin` accepted `D-P3.4-001` through `D-P3.4-004`.
The selected baseline uses authoritative PostgreSQL/PostGIS geometry with exact
Shapely 2.1.2 as the worker candidate, a visual rule graph compiled to typed
temporal nodes and constrained CEL, the balanced deterministic time policy, and
bounded PostgreSQL/PostGIS state with transactional outbox and C10 evidence.

`D-P3.4-START` was authorized by `mayank-admin` on 2026-08-25 against planning
digest `E3D0D0DEB5AE20D68AF6A5CE72229BDC63AE55B4200C7E2A011CFA834AFBEBF0`.
It permits local generated-only implementation and exact dependency evidence.
It grants no final acceptance, camera/media/data access, identity, cross-camera
linkage, Government matching, operational alerting, deployment, P3.5, or remote
Git action.

The implemented package now passes generated C10 replay, SQLite/PostGIS
migration, full-suite coverage, packaging, audit, and Docker/Compose evidence.
The PostGIS image has unresolved critical/high findings and remains explicitly
deployment-blocked. On 2026-08-26, `mayank-admin` accepted
`D-P3.4-ACCEPTANCE` for package digest
`11CCD757E2308F56EE5912B70861B8A977DBD8B7CEE8DBD434265A28988EF8AF` at
repository checkpoint `092127fcdefa74a0264b9f02d4eee87db3a6c6b8`. This does
not authorize P3.5 or waive any continuing boundary.

### DR-0034: P3.5 Synthetic ANPR Planning Baseline

Status: planning authorized under `D-P3.5-PLAN-AUTH`; technical baseline
approved; artifact research authorized;
implementation remains pending.

P3.5 planning is independently authorized on the accepted P3.4 package. The
recommended design uses a deterministic procedural corpus with visibly
non-issuable `SYN` tokens, a dedicated generated plate-region detector role,
PP-OCRv6 small/medium Latin candidates, a Devanagari PP-OCRv5 auxiliary lane,
and Tesseract Gujarati fast/best auxiliary lanes. No exact artifact is approved.

Raw OCR remains immutable. NFC, UAX #29 grapheme segmentation, closed
normalization rules, calibrated alternatives, explicit abstention, and bounded
stream-local consensus are derived stages. Gujarati and Devanagari cannot
rewrite or increase confidence in the core Latin registration-mark result.

The recommended reference preserves the P3.0 zero-retention plate-text policy:
no text table, search, event, outbox value, API, log, metric label, cache,
export, or backup. Only identifier-free aggregate generated evidence may be
persisted. Synthetic evidence cannot support a real-CCTV accuracy, legal,
operational, or deployment claim.

`D-P3.5-001` through `D-P3.5-004` now select option `A`. The separate
`D-P3.5-ARTIFACT-RESEARCH` decision permits only seven exact external artifacts
to enter a non-runtime quarantine. `D-P3.5-START` remains the explicit final
owner gate. No extraction, dependency, generation, training, inference,
product code, camera, media, real plate, owner/Government record, alert,
deployment, P3.6, or remote Git action is authorized.

### DR-0035: Early P3.5 Start Intent

Status: received but not effective.

On 2026-08-26, `mayank-admin` supplied the exact identifier
`D-P3.5-START`. The statement arrived before `D-P3.5-001` through
`D-P3.5-004` were selected and before exact model, font, dictionary, generator,
dependency, runtime, artifact, and network-action manifests were prepared.

The statement is preserved as start intent with empty artifact and network
allowlists. It grants no implementation authority. A final confirmation must
bind the four selected decisions and the exact reviewed packet digest before
any acquisition, dependency change, generation, inference, or product work.

### DR-0036: P3.5 Metadata-Only Artifact Proposal

Status: proposal approved for restricted quarantine research.

Proposal R0 identifies eight artifact slots for the recommended `A/A/A/A`
baseline: three Paddle recognition archives, two Gujarati Tesseract traineddata
files, two Noto fonts, and one future generated-only H-CAM plate detector.
Immutable Git revisions, Git blob identities, official URLs, observed sizes,
content types, ETags, and size ceilings are recorded where available.

At this decision checkpoint no artifact body had been downloaded and every
SHA-256 remained unresolved. Tesseract is not installed, Paddle runtime
compatibility is unproven, and no candidate is approved for execution.
`D-P3.5-ARTIFACT-RESEARCH` now permits only exact allowlisted quarantine
acquisition; it does not substitute for final digest-bound `D-P3.5-START`.

### DR-0037: P3.5 Technical Baseline And Artifact Research

Status: approved under `D-P3.5-001` through `D-P3.5-004` and
`D-P3.5-ARTIFACT-RESEARCH`.

On 2026-08-26, `mayank-admin` selected option `A` for the synthetic corpus,
detector/OCR portfolio, normalization/consensus, and privacy/evidence policy.
The same statement separately authorizes proposal-digest-bound acquisition of
exactly seven listed external artifacts into an external quarantine, with
`F:\h cam\research-cache\phase-3\p3-5` recorded as the default path.

HTTPS URLs, filenames, expected sizes, content types, cumulative size,
timeouts, no-redirect behavior, disabled environment proxies, and non-runtime
quarantine are fixed in the authorization contract. `PLATE-D0`, archive
extraction, runtime loading, dependencies, generation, training, inference,
product implementation, camera/media access, real/private/Government data,
deployment, and remote Git operations remain prohibited. Exact review evidence
and a final packet-bound `D-P3.5-START` confirmation are still required.

### DR-0038: P3.5 Exact Artifact Evidence And Runtime Research Gate

Status: artifact evidence owner accepted; restricted runtime research authorized.

All seven authorized external artifacts were acquired into an external local
quarantine. Exact sizes, SHA-256 values, Paddle HTTP identities, Git blob
identities, passive archive/font/traineddata structure checks, model cards,
CycloneDX 1.6 inventory, license evidence, and Microsoft Defender results are
recorded. No archive was extracted, and no artifact was loaded or executed.

The first `F:` attempt stopped for insufficient space without leaving a partial
file. The `B:` provider was not usable from Python during artifact acquisition;
it was rechecked successfully before runtime research. The complete artifact
evidence set is stored under `E:\h-cam-research-cache\phase-3\p3-5`; quarantine
files remain outside Git.

Runtime readiness is still incomplete. The proposed baseline is isolated
CPython 3.12.13 with metadata-only candidates `paddleocr==3.7.0`,
`paddlepaddle==3.3.1`, `Pillow==12.3.0`, and `regex==2026.7.19`. Exact wheels,
transitive dependencies, native libraries, vulnerability evidence, and the
Tesseract 5 engine are unresolved. `D-P3.5-RUNTIME-RESEARCH` is approved only
for the documented external binary-wheel closure, SBOM, scan, vulnerability,
and network-denied import checks. It grants no implementation or model-runtime
authority. Final `D-P3.5-START` remains separate.

### DR-0039: P3.5 Artifact Acceptance And Runtime Research Authorization

Status: approved; runtime research evidence pending.

`mayank-admin` accepted `P3.5-EXACT-ARTIFACT-REVIEW-R1` for exact package digest
`54B02B80169604904C9945C1C6E692500CA8AA79253EEC27A63B4C4DB00B395C`
and authorized `D-P3.5-RUNTIME-RESEARCH` under the proposal's non-runtime
boundaries. The research root is external to Git, direct package roots are
exactly pinned, source builds and repository lock changes are forbidden, and
imports must deny socket access. Reviewed OCR artifacts, Tesseract, constructors,
generation, training, inference, media/data, implementation, and deployment
remain prohibited.

## Decisions Explicitly Deferred

- production accelerator/runtime and GPU fleet;
- Kubernetes or another production orchestrator;
- Tier B/C implementation order;
- persistent evidence media;
- cross-camera correlation or person/vehicle identity;
- Government databases, watchlists, owner records, and alert policy;
- statewide procurement, capacity, data residency, and production SLOs.

Deferred means unapproved, not implicitly allowed.
