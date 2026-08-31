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

Status: historical planning checkpoint authorized under `D-P3.5-PLAN-AUTH`;
implementation was pending here and was later restrictedly authorized under
DR-0041.

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

At this checkpoint, `D-P3.5-001` through `D-P3.5-004` selected option `A` and
`D-P3.5-ARTIFACT-RESEARCH` permitted only seven exact external artifacts to
enter a non-runtime quarantine. Final start authority was still absent. The
subsequent restricted authorization is recorded in DR-0041.

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
authority. At this checkpoint final `D-P3.5-START` remained separate; DR-0041
records its later restricted resolution.

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

The initial `B:\hcam-research-quarantine` top-level creation was denied before
any package or network action. A second attempt under `B:\hcam-scan-temp`
reached dependency resolution but was stopped before a complete wheelhouse or
installation after the owner identified `B:` as RaiDrive Google Drive and
prohibited its use. The active local root is now
`E:\h-cam-research-cache\phase-3\p3-5-runtime`; no authority was widened.

### DR-0040: P3.5 Restricted Runtime Research Evidence

Status: historical evidence checkpoint; evidence complete and subsequently
bound by final digest-bound start approval in DR-0041.

The authorized CPython 3.12.13 research resolved exactly four direct package
roots into a 67-wheel binary closure outside Git. The offline installation has
67 distributions and 185 native files. `pip check` passed, the vulnerability
audit found zero known vulnerabilities, and Microsoft Defender reported no
threats. Guarded imports loaded only the four declared packages, blocked one
IPv6 socket attempt, and performed no successful network access. No OCR
constructor, artifact extraction/loading, inference, generation, training,
media, dataset, product implementation, or deployment action occurred.

The repository retains a 319-component CycloneDX 1.6 SBOM, complete package
license metadata, external evidence hashes, and explicit legal-review and
Tesseract limitations. `B:` is RaiDrive Google Drive and must not be used; the
validated quarantine is under `E:\h-cam-research-cache`. Runtime evidence is
complete. At this checkpoint every SBOM component remained runtime-unauthorized
and the early `D-P3.5-START` statement remained non-effective. DR-0041 records
the later owner review that bound the clean package digest and exact restricted
implementation authority.

### DR-0041: P3.5 Digest-Bound Generated-Only Start

Status: approved and effective.

On 2026-08-26, `mayank-admin` supplied final `D-P3.5-START` after the four
technical decisions, exact artifact acceptance, restricted runtime evidence,
and clean-source package were complete. The authorization binds package digest
`915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D`
at repository checkpoint `1edfd0a13208d9b359cc5e563bbc406bba214e26`.

The decision authorizes only enumerated local generated-only work. `OCR-L0`,
`OCR-L1`, and `OCR-D0` may be safely extracted and loaded for generated-only
Paddle inference. `FONT-G0` and `FONT-D0` may be loaded only for deterministic
generated rendering. The exact reviewed CPython 3.12.13 runtime may be used from
its local wheelhouse with zero network access. `OCR-G0` and `OCR-G1` remain
blocked because the exact Tesseract 5 engine and native SBOM are unresolved.

No download, repository dependency or container change, training, `PLATE-D0`,
public API, persistent plate text, camera/media/Sentinel/ONVIF access,
real/private/Government data, identity, watchlist, alert, deployment, P3.6, or
remote Git action is authorized. This is a start gate, not P3.5 acceptance.

### DR-0042: P3.5 W9 Closure Scope Proposal

Status: Option A approved and effective under `D-P3.5-W9-START`.

The validated W1-W8 dependency is repository head
`b282f1bf45e38bcdfd49f976e974ce92e9d5f08b`, package digest
`96A35F98059918181FD59687BA96A4283ED9885BAD7D34FE1915D6288174C3DF`,
and W8 evidence SHA-256
`58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124`.

The effective `D-P3.5-START` allowlist does not enumerate the broader W9
resource, packaging, and rollback work. The packet therefore offered narrow
generated-only closure (A, recommended), exact-runtime revalidation (B), a
larger generated benchmark requiring a second execution plan (C), or deferral
(D).

On 2026-08-27, `mayank-admin` supplied `D-P3.5-W9-START: A`. The authorization
binds proposal SHA-256
`62B711EAF2C1EDD21CBCD07751D9A30EF6FA61C11E9ECB190CE6614FE67AB796`,
planning digest
`9BCC9E9C068E03E94E5461AABDE3B50A4766498406643EE253AF66ECAD8A9B7B`,
and repository head `6d546fbe1a074e4090fa6d006a67421a27746afe`. It permits only
the exact Option A actions and paths with zero network, external-runtime, model,
font, final-test, camera/media, persistence, deployment, P3.6, or remote Git
authority. W10 remains separate.

### DR-0043: P3.5 W9 Generated-Only Closure Evidence

Status: technically validated; subsequently accepted through W10.

The closure checker consolidates seven W1-W8 evidence groups, executes two
deterministic 10,000-observation generated-contract stress replays, closes and
abstains all 2,208 results per replay, reaches the exact 256-state ceiling, and
records four fail-closed overload results. Default-off and socket-denial checks
pass. No model, font, artifact, external runtime, final-test split, camera,
external input, accepted value, operational event, or retained text/identifier
value is used.

An isolated offline source build produces one wheel and one sdist. Archive
inspection rejects unsafe entries and model/weight/trained-data/font/image/video
payloads, retains only aggregate counts and cryptographic digests, and leaves
the generated archives untracked. No application or database rollback is
needed. W10 clean-source evidence and explicit owner acceptance were completed
under DR-0044.

### DR-0044: P3.5 W10 Immutable Package Acceptance

Status: accepted under `D-P3.5-W10-ACCEPTANCE`.

On 2026-08-27, `mayank-admin` accepted the immutable 99-file P3.5 package at
commit `1611922b4f410aa0cdbce369e4f3c8838f53e19f`, package digest
`4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`,
and W9 evidence SHA-256
`A64ACE72ED33E0734D87D43A871BB1FB73B593296A681771600C3A1F42899E55`.
The verifier reconstructs the historical package directly from Git before
accepting the binding; additive governance records do not rewrite the accepted
digest.

The decision closes only P3.5's generated-only, zero-retention, default-off
synthetic ANPR slice. It does not authorize Tesseract/Gujarati OCR execution,
`PLATE-D0`, final-test access, quality promotion, cameras/media, real or
Government data, identity, cross-camera linkage, operational actions,
deployment, remote Git actions, P3.6, or later work.

### DR-0045: P3.6 Planning And Primary-Source Research Authorization

Status: planning and research only authorized under `D-P3.6-PLAN-AUTH`.

On 2026-08-27, `mayank-admin` authorized planning and read-only primary-source
research for P3.6 Runtime Acceleration and Scheduling. The baseline is accepted
P3.5 package digest
`4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`
at commit `1611922b4f410aa0cdbce369e4f3c8838f53e19f`; the planning branch began at
repository head `c0cb82b32f3ec399b64668da4600540c88b8c25e`.

The authority permits local documentation/contracts, current public official
documentation reads, a runtime/scheduling plan, and owner decision options. It
explicitly prohibits downloads, runtime execution, GPU/hardware testing,
containers, deployment, camera/media/data access, implementation, remote Git,
and P3.7 or later work.

### DR-0046: P3.6 Recommended Runtime And Scheduling Baseline

Status: `D-P3.6-001` through `D-P3.6-005` accepted by `mayank-admin` on
2026-08-29.

Primary-source research supports a staged portfolio: ONNX Runtime CPU behavior
reference, OpenVINO-first exact Intel evaluation, TensorRT/DeepStream only on
approved NVIDIA hardware after model promotion, and Triton only after a
measured shared-serving trigger. The proposed scheduler uses typed node
capabilities, hard authorization/compatibility/capacity admission, leased
placements, node-local bounded queues, stateless detector batching, stream-local
state isolation, and explicit degradation.

The proposed evidence policy separates model selection from runtime selection
and separates `CONTRACT`, `INFER`, and `PIPE` claims. It binds compiled
artifacts to exact model, build, runtime, precision, hardware, driver, OS,
configuration, SBOM, provenance, benchmark, and rollback evidence. The proposed
hardware strategy uses `LAB-LAPTOP-01` only for later CPU/Intel feasibility and
requires a separately approved capacity target for C10/C50 or NVIDIA claims.

The owner selected the staged evidence-driven portfolio, typed fail-closed
scheduler, two-funnel conjunctive evidence, immutable compatibility bundle,
and owned-lab-then-capacity-target strategy. Kubernetes is accepted only as an
optional execution backend beneath H-CAM admission. Runtime automatic placement
is advisory only inside admitted bounds. Balanced, Throughput, and Latency are
switchable ranking/evidence views that cannot bypass hard gates.

Exact models, datasets, hardware, runtimes, dependencies, containers, numeric
gates, execution, implementation, and deployment remain blocked.

### DR-0047: P3.6 Dynamic Capability Profile Policy

Status: accepted planning baseline; exact manifests pending.

One application and one contract set will support `portable_cpu`,
`local_accelerated`, and `capacity_target` profiles. Profiles may adapt bounded
concurrency, stateless detector batches, sampling within an approved floor,
optional enrichment, preview quality/rate, queues, workers, and reservations.
They cannot weaken authorization, security, event semantics, quality, lineage,
audit, privacy, retention, failure behavior, rollback, or benchmark honesty.

Automatic profile selection is limited to fresh immutable node inventory and
exact validated compatibility bundles. The first exact current-laptop,
accelerated-laptop, and C10/C50 capacity manifests remain blocked by `P36-G2`.
No dashboard, scheduler, Kubernetes, runtime, or hardware action is authorized
by this planning policy.

### DR-0048: P3.6 Start Statement Received Before Hard Gates

Status: recorded non-effective start intent.

On 2026-08-29, `mayank-admin` supplied `continue D-P3.6-START`. The statement
is explicit intent to continue P3.6, but the accepted gate policy prevents it
from authorizing undisclosed implementation or execution. `P36-G1` remains
blocked by the incomplete model-family comparison, `P36-G2` by missing exact
machine/runtime/workload profiles, and `P36-G4` by missing digest/source/path-
bound artifact research authority. No executable package digest exists.

The statement therefore permits no new executable action. Existing
planning-only authority remains effective, and an ordered unblock plan now
defines sanitized inventory, exact model proposal, capability manifests, and a
later immutable start package. `P36-G5` remains blocked until the owner accepts
that final exact digest.

### DR-0049: LAB-LAPTOP-01 Sanitized Inventory R0

Status: authorized, completed, and sealed; no execution claim.

On 2026-08-29, `mayank-admin` authorized sanitized read-only OS, hardware,
display-driver, and already-installed runtime inventory on logical node
`LAB-LAPTOP-01`. The collection excluded personal and network identifiers and
performed no network, install, download, model, inference, performance, stress,
thermal, container, Kubernetes, media/data, deployment, or remote Git action.

The sealed JSON record has SHA-256
`0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F`.
It establishes Windows 10 Pro x64, Intel i5-8365U 4C/8T, 8 GiB RAM, Intel UHD
620, no observed discrete NVIDIA accelerator, and less than seven percent free
space on every observed fixed volume. It makes no OpenVINO, GPU, inference,
latency, throughput, decoder, C1/C10/C50, container, or deployment claim.

`P36-U1` is complete. `P36-G2` remains blocked pending exact portable
runtime/workload bounds, the accelerated-laptop inventory, the capacity target,
and owner-approved profile manifests.

### DR-0050: P3.6 Exact Model Artifact Research Proposal R0

Status: metadata research complete; sealed non-authorizing proposal pending
owner review; acquisition blocked.

Under `D-P3.6-PLAN-AUTH`, current official-source metadata was recorded for the
exact proposed `DET-E1` D-FINE-N, `DET-B1` RF-DETR Small, and `DET-A1` RF-DETR
Large-2026 native checkpoints. The three objects have a cumulative expected
size of `537,489,237` bytes. The sealed R0 planning-package digest is
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.

No model, source, dependency, dataset, container, or artifact payload was
downloaded. No checkpoint was loaded, unpickled, imported, exported, converted,
scanned, or executed. Publisher performance is recorded only as an upstream
claim and does not select a champion, fallback, runtime, or hardware profile.

The package is fail closed: the physical quarantine root and scanner command
are unresolved. Volume `B:` remains owner prohibited, and observed fixed
volumes `C:`, `E:`, and `F:` are ineligible under the current free-space policy.
`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` can accept only the planning record.
`D-P3.6-MODEL-RESEARCH-R1-AUTH` is not issuable until exact storage and scanner
bindings are added to a new digest-bound R1 package. `P36-G1`, `P36-G2`,
`P36-G4`, and `P36-G5` remain blocked.

### DR-0051: P3.6 Alignment To Phase -1 Shared Contracts

Status: aligned planning baseline; `P36-G0A` passed with execution gates
unchanged.

The completed Phase -1 baseline is now authoritative for sanitized node
inventory, deterministic profile resolution, model/runtime compatibility,
workload placement, typed pipeline composition, adaptive-selection evidence,
rollback, and deployment profile classes. P3.6 remains responsible for
detector runtime candidates, candidate-specific parity, generated benchmark
workloads, and `CONTRACT`/`INFER`/`PIPE` evidence.

The alignment binds `hcam-protos` merge
`d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8`, `hcam-deployment` merge
`71095fe89d2b711e4982ddc0130fcaedda8703e7`, and deployment base digest
`sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf`.
Historical `local_accelerated` maps to `owned_gpu_lab`. Historical
`capacity_target` is an evidence target resolving to `standalone_server` or
`kubernetes_cluster`, not another profile. Balanced/Throughput/Latency are
resolver objectives; C1/C10/C50 are generated evidence tiers.

The five accepted P3.6 selections remain unchanged. This planning alignment
does not accept the R0 model proposal and authorizes no acquisition,
implementation, runtime, hardware test, Kubernetes action, deployment, media,
data, or remote Git operation. `P36-G1`, `P36-G2`, `P36-G4`, and `P36-G5`
remain blocked.

### DR-0052: P3.6 Portable CPU Profile Proposal R0

Status: sealed non-executable planning proposal pending owner review under
`D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE`.

Under `D-P3.6-PLAN-AUTH`, the authorized sanitized `LAB-LAPTOP-01` inventory,
accepted P3.2 CPU behavior reference, exact Phase -1 shared/deployment
revisions, and current official ONNX Runtime configuration guidance were
combined into one conservative `portable_cpu` proposal. The sealed package
digest is
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.

The proposal permits one assignment, one worker operation, batch one, one
in-flight inference request, and a bounded two-item queue only as planning
values. Thread spinning, memory arenas, CPU/RAM reservations, queue age,
sampling floor, workload duration/repetitions/seeds, numeric thresholds,
dependency closure, and artifact state remain unresolved. The profile is not
resolver-eligible and the historical P3.2 smoke duration is not P3.6
performance evidence.

Owner acceptance can accept only the planning record. It does not pass
`P36-G2` or authorize downloads, installation, model loading, inference,
hardware tests, implementation, Kubernetes, camera/media/data access,
deployment, or remote Git. `P36-G1`, `P36-G2`, `P36-G4`, and `P36-G5` remain
blocked.

### DR-0053: P3.6 Inventory And Admission Contract Gap R0

Status: exact planning gap sealed; four owner policy selections pending; no
inventory recollection authority.

The accepted historical `LAB-LAPTOP-01` R0 inventory remains immutable, but it
does not conform to the Phase -1
`hcam.platform.node-capability-inventory/v1alpha1` contract. It lacks an exact
shared schema discriminator, opaque snapshot ID, `valid_until`, structured
provenance trust and collector version, normalized capability states,
scheduler/container fields, exact shared redaction declaration, and a separate
trust-zone policy digest. It cannot become admission evidence through
retimestamping or projection.

The gap and owner decision packet are sealed under SHA-256
`CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.
Pending `D-P3.6-U3A-001` through `D-P3.6-U3A-004` select canonical R1 strategy,
freshness, provenance/trust binding, and expiry behavior. The recommended
planning choices are `A/A/A/A`.

Selections do not authorize recollection. A separate exact
`D-P3.6-INVENTORY-R1-AUTH` package is required afterward. `P36-G2` remains
blocked, and no implementation, runtime, hardware test, model, Kubernetes,
camera/media/data, deployment, or remote Git authority is granted.

### DR-0054: P3.6 Planning Package And Inventory Policy Acceptances

Status: portable profile planning, inventory policy `A/A/A/A`, and model
metadata planning accepted by `mayank-admin` on 2026-08-30.

`D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE` accepts the non-executable portable
CPU package digest
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.
The profile remains ineligible because fresh inventory, exact runtime/resource/
workload values, compatibility evidence, and generated validation are absent.

`D-P3.6-U3A-001` through `D-P3.6-U3A-004` select `A/A/A/A` against inventory
package digest
`CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.
R0 is preserved; a new shared-schema R1 uses a maximum 24-hour window plus
early invalidation, observed local provenance plus a separate generated-only
trust digest, and fail-closed new-admission behavior on expiry. No R1
collection is authorized by these policy selections.

`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` accepts metadata-only package digest
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.
No candidate artifact may be downloaded, loaded, scanned, converted, exported,
executed, compared, or promoted until exact storage/scanner bindings and a
separate R1 authority exist.

`P36-G1`, `P36-G2`, `P36-G4`, and `P36-G5` remain blocked. These decisions
authorize no inventory query, acquisition, inference, hardware test,
implementation, Kubernetes action, media/data access, deployment, or remote
Git action.

### DR-0055: P3.6 Minimized Inventory R1 Authorization Package R0

Status: exact non-effective owner-authorization package sealed on 2026-08-30;
owner acceptance was pending at seal and is resolved in `DR-0056`.

Package digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`
binds a five-file research, trust-policy, collector-specification,
authorization-proposal, and owner-review package. It proposes one local-only
attempt on logical node `LAB-LAPTOP-01` within 24 hours of exact owner
acceptance, with 10-second action bounds and a 60-second transaction bound.

The proposed action set requests only minimized local Windows OS, CPU, and
memory CIM fields plus metadata-only default Python, installed `onnxruntime`
distribution, and FFmpeg version families. It forbids remote CIM, network,
storage, display/GPU, device identifiers, environment/path enumeration,
container/Kubernetes/scheduler contact, model/runtime imports, inference,
media, benchmark, and hardware tests. Unobserved instruction-set,
accelerator, container, scheduler, and runtime-compatibility facts remain
explicit `unknown` values.

The bound trust snapshot digest is
`E76D0C56476A98AADDBC7880AD75858B5B61D45CE95802E3FB39557E226C6106`.
It describes an owned-local, network-denied, generated-only context and grants
no admission or execution authority. A failed collection attempt would require
new authorization. Historical R0 remains unchanged.

The package itself authorizes nothing. At sealing, no collector was implemented,
no machine query had run, and no R1 or collection evidence existed. The owner
later accepted the exact digest and the single bounded attempt completed under
the separate acceptance record described by `DR-0056`. All profile,
runtime/model, hardware, accelerator, container, Kubernetes, camera/media/data,
deployment, and remote Git prohibitions remain.

### DR-0056: P3.6 Inventory R1 One-Time Authorization And Result

Status: accepted and completed on 2026-08-30; the single attempt is consumed.

`mayank-admin` accepted `D-P3.6-INVENTORY-R1-AUTH` against package digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`.
One local read-only attempt ran inside the bound 24-hour authorization window
and produced a sanitized shared-schema R1 with SHA-256
`FB061C906D1CE5F7FE3B32B70F6CA5134C486F474E2618B23884466C2E58C76F`.
Its bounded collection evidence has SHA-256
`3658758FCC7342B7865C7C0FD340FD408B38562BB1D365B757A74C8B6347FA72`.
The exact pinned shared-schema validation passed, raw command output was not
persisted, no network access was used, and no reusable collector was created.

The R1 record is valid only through `2026-08-31T17:57:26.397Z` under the
accepted maximum 24-hour freshness policy. It remains a factual input and does
not establish runtime compatibility, accelerator/container/scheduler support,
resource capacity, generated workload evidence, profile admission, placement,
or activation. Therefore `P36-G2` remains blocked. Another attempt requires a
new explicit authorization; no retry or continuing collection authority exists.

See [the authorized collection record](p3-6-inventory-r1-collection.md) for the
complete bindings, outputs, gate effect, and continuing prohibitions.

### DR-0057: P3.6 Portable CPU R1 Admission Gap R0

Status: exact non-effective owner-decision package sealed on 2026-08-30;
the four selections were pending at seal and are resolved in `DR-0058`.

Package digest
`471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`
binds the R1-to-portable admission gap, four-choice owner packet, and human
review document. It reconciles the sanitized R1 and accepted portable CPU R0
proposal with exact Phase -1 inventory, compatibility, resolver, placement,
adaptive-evidence, and deployment-profile contracts.

R1 satisfies only the capability-inventory input. The exact authorization,
policy, compatibility, workload, pipeline, and capacity inputs remain missing
or planning-only. The package records 22 gaps and recommends:

- `D-P3.6-U3B-001 A`: just-in-time digest-bound inventory refresh after the
  other admission inputs are sealed;
- `D-P3.6-U3B-002 A`: strict seven-input fail-closed resolver admission;
- `D-P3.6-U3B-003 A`: a complete immutable compatibility bundle; and
- `D-P3.6-U3B-004 A`: a deterministic generated-only `CONTRACT` plus C1
  `INFER` validation matrix with balanced as the default objective.

The package is planning only. It does not authorize a new inventory attempt,
artifact/dependency acquisition, profile admission or activation, runtime/model
execution, hardware testing, containers/Kubernetes, cameras/media/data,
implementation, deployment, or remote Git. `P36-G2` remains blocked, and owner
acceptance cannot be inferred from `continue` or another decision.

See [the portable R1 admission gap](p3-6-portable-r1-admission-gap.md).

### DR-0058: P3.6 Portable R1 Admission Policies Accepted

Status: `A/A/A/A` planning-policy selections accepted by `mayank-admin` on
2026-08-31 local date against package digest
`471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`.

The accepted policies are:

- `D-P3.6-U3B-001 A`: preserve R1 as immutable historical evidence after
  expiry and request a just-in-time, separately authorized, digest-bound refresh
  only after the other admission inputs are sealed;
- `D-P3.6-U3B-002 A`: require all seven fresh, valid, content-addressed resolver
  inputs and fail closed on unknown, missing, invalid, or stale evidence;
- `D-P3.6-U3B-003 A`: require the complete immutable compatibility bundle,
  including supply-chain, pipeline, security, fallback, and rollback records;
  and
- `D-P3.6-U3B-004 A`: require a predeclared deterministic generated-only
  `CONTRACT` plus C1 `INFER` matrix, with balanced as the default objective.

R1 was still within its accepted 24-hour validity window at acceptance, but it
represents only the capability-inventory resolver input. The other six inputs
and all 22 evidence gaps remain unresolved, so `portable_cpu` is not
resolver-eligible and `P36-G2` remains blocked.

This acceptance grants no new inventory attempt, reusable collector,
artifact/dependency acquisition, profile resolution/admission/activation,
runtime/model execution, hardware testing, containers/Kubernetes,
cameras/media/data, implementation, deployment, or remote Git authority.

Machine-readable acceptance:
[`p3-6-portable-r1-owner-decisions.json`](../../contracts/phase-3/p3-6-portable-r1-owner-decisions.json).

### DR-0059: Portable compatibility and generated C1 policies accepted

Status: accepted as non-effective planning policy on 2026-08-31.

The planning-only compatibility package is sealed under SHA-256
`9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A`.
It specifies an exact conservative ONNX Runtime CPU candidate, a deterministic
generated-only `CONTRACT` plus C1 `INFER` matrix, hard safety gates separated
from later calibration and held-out validation, and an immutable five-revision
compatibility-bundle lifecycle.

The package presents four independent pending choices:

- `D-P3.6-U3C-001 A`: deterministic low-contention CPU runtime candidate;
- `D-P3.6-U3C-002 A`: bounded generated `CONTRACT` plus C1 `INFER` matrix;
- `D-P3.6-U3C-003 A`: hard safety gates followed by separately authorized
  calibration and held-out validation; and
- `D-P3.6-U3C-004 A`: immutable `R0` through `R4` compatibility lifecycle.

`mayank-admin` accepted `D-P3.6-U3C-001` through `004` as `A/A/A/A` against
the exact package digest. The acceptance record SHA-256 is
`FECF3EF71F5A7550871C91BF3A58BFA9D279A88C312A4E96019EC2457821CA77`.
These planning choices grant no artifact or dependency acquisition, runtime/model import,
inference, calibration, benchmark, hardware testing, inventory retry,
profile admission or activation, implementation, containers/Kubernetes,
cameras/media/data, deployment, or remote Git authority. `P36-G2` remains
blocked.

Machine-readable acceptance:
[`p3-6-portable-compatibility-validation-owner-decisions.json`](../../contracts/phase-3/p3-6-portable-compatibility-validation-owner-decisions.json).

### DR-0060: Portable R1 supply-chain prerequisite policies accepted

Status: accepted as non-effective planning policy on 2026-08-31.

The planning-only prerequisite package is sealed under SHA-256
`496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
It translates the accepted portable compatibility policy into a fail-closed
storage, scanner, verdict, acquisition, and R1/R2 separation proposal without
binding a physical path, installing a scanner, acquiring an artifact, or
executing a model.

The package presents five independent choices. `mayank-admin` selected the
recommended `A/A/A/A/A` policy:

- `D-P3.6-U3D-001 A`: owner-supplied local fixed NTFS/ReFS quarantine root,
  accepted only after a separately authorized fresh threshold attestation;
- `D-P3.6-U3D-002 A`: exact Microsoft Defender, pinned ModelScan, and H-CAM
  framework-free passive inspection chain;
- `D-P3.6-U3D-003 A`: all-layer clean, supported, complete evidence with no
  manual hard-gate override;
- `D-P3.6-U3D-004 A`: sequential `.partial` acquisition, identity and hash
  verification, scanning, provenance and CycloneDX ML-BOM, then atomic seal;
  and
- `D-P3.6-U3D-005 A`: immutable passive R1 followed only by a separately
  authorized, digest-bound, network-denied, generated-only R2.

The exact owner acceptance record SHA-256 is
`F68BDE02AF96E3992A8C64F1F01A85CAC960F529946EA12FA4899D9EBFC197A9`.
The exact quarantine root, Defender version and path, pinned ModelScan
distribution and hash, and H-CAM passive inspector implementation remain
unresolved. The acceptance grants no storage query or write probe, scanner
query/install/run, artifact or dependency download, checkpoint load, runtime
execution, validation, profile admission, implementation, deployment, or
remote Git authority. `P36-G2` and `P36-G4` remain blocked.

Machine-readable package:
[`p3-6-portable-r1-supply-chain-prerequisite-package.json`](../../contracts/phase-3/p3-6-portable-r1-supply-chain-prerequisite-package.json).

Machine-readable acceptance:
[`p3-6-portable-r1-supply-chain-prerequisite-owner-decisions.json`](../../contracts/phase-3/p3-6-portable-r1-supply-chain-prerequisite-owner-decisions.json).

### DR-0061: F: quarantine and scanner binding attempt proposed

Status: accepted and consumed on 2026-08-31; failed closed with no retry
authority.

The owner supplied `F:` as the candidate volume and reported approximately 50
GB free. H-CAM proposes the isolated exact root `F:\HCAM-Quarantine`, outside
the existing `F:\h cam` project tree. The reported free space is unverified and
is not treated as attestation evidence.

The package is sealed under SHA-256
`9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`.
Accepted as `D-P3.6-U3E-BINDING-R0-AUTH`, it permitted one attempt
within 24 hours to query only bounded `F:` storage properties, create only the
exact candidate root if absent, perform and clean one 4096-byte atomic
capability probe, query bounded Defender and ModelScan metadata without running
or updating either scanner, and write three exact sanitized repository records.

The attempt observed an eligible fixed NTFS volume and safe canonical path, but
the new root inherited a broad-write ACL. It failed before the atomic probe,
removed the empty root, and retained no probe content. Defender metadata was
observed without a binary trust binding; ModelScan was unavailable and the
passive inspector remains unimplemented. No retry, current `F:` action, scanner
action, acquisition, runtime, validation, profile admission, implementation,
deployment, or remote Git authority exists. `P36-G2` and `P36-G4` remain
blocked.

Machine-readable package:
[`p3-6-quarantine-scanner-binding-r0-authorization-package.json`](../../contracts/phase-3/p3-6-quarantine-scanner-binding-r0-authorization-package.json).

### DR-0062: U3F quarantine remediation decisions accepted

Status: `A/A/A/A/A/A` planning choices accepted on 2026-08-31; no attempt or
local action authorized.

Primary-source research supports creating the absent Windows directory with a
protected explicit `DirectorySecurity` descriptor rather than inheriting and
then replacing a broad DACL. It also supports binding Defender by documented
versioned location, SHA-256, and cache-only WinVerifyTrust without executing
`MpCmdRun.exe`. ModelScan remains a separate pinned bootstrap because it is not
installed, dependency acquisition is not authorized, and current upstream
false-negative reports require generated hostile-fixture validation.

The recommended `D-P3.6-U3F-001` through `006` selection is `A/A/A/A/A/A`:
security-at-create DACL; current process `Modify` plus SYSTEM/Administrators
`FullControl`; absent root required; exact Defender path/hash/cache-only trust;
separate ModelScan bootstrap; and a future storage-plus-Defender retry only.

The package is sealed under SHA-256
`9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`.
The owner explicitly selected all six recommended options. Acceptance record
SHA-256:
`BDA7E9C6B8ACF4ECB8641B61F47A45E4E02768B58C7E3A08179507B7ABAFDF1F`.
The selections authorized preparation of a later exact action and
authorization package. They did not authorize a retry or any local action.

Machine-readable package:
[`p3-6-quarantine-remediation-r1-decision-package.json`](../../contracts/phase-3/p3-6-quarantine-remediation-r1-decision-package.json).

### DR-0063: U3G security-at-create and Defender binding attempt proposed

Status: superseded by the consumed attempt recorded in DR-0064. This entry
preserves the immutable proposal state before authorization.

The exact U3G package applies the accepted U3F choices. It requires the
candidate root to be absent, constructs a protected DACL in memory, grants the
current process `Modify` and LocalSystem/Administrators `FullControl`, creates
the directory with security already applied, verifies only sanitized DACL
booleans, and runs one cleaned 4096-byte atomic probe.

It independently permits bounded Defender status metadata, at most 64 direct
version-directory candidates, one version-matched regular non-reparse
`MpCmdRun.exe` of at most 128 MiB, SHA-256, and cache-only no-UI whole-chain
WinVerifyTrust without executing the file. ModelScan, the passive inspector,
scanner execution, updates, acquisition, models, media, implementation, and
deployment remain outside the attempt.

The package is sealed under SHA-256
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
Only an exact `D-P3.6-U3G-BINDING-R1-AUTH` statement against that digest within
24 hours can authorize one attempt. Failure consumes the authorization.

Machine-readable package:
[`p3-6-quarantine-remediation-r1-authorization-package.json`](../../contracts/phase-3/p3-6-quarantine-remediation-r1-authorization-package.json).

### DR-0064: U3G attempt consumed and failed closed

Status: accepted and consumed on 2026-08-31; no retry is authorized.

`mayank-admin` exactly accepted `D-P3.6-U3G-BINDING-R1-AUTH` against package
digest
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
The authorization was recorded before machine access and its only attempt was
consumed.

The fixed NTFS volume, capacity, exact absent path, protected-DACL construction,
and security-at-create operation passed. Post-create verification did not find
the current-process `Modify` rule in the exact semantic form required by the
package. The DACL gate failed closed, the atomic probe was skipped, the empty
attempt-created root was removed, and no probe content was retained.

The bounded Defender status operation yielded no usable normalized product
version. Candidate resolution, hashing, and cache-only WinVerifyTrust were
skipped. No Defender executable, scanner, ModelScan component, model, artifact,
media, container, or deployment action ran.

Evidence SHA-256 values:

- authorization: `12DBCEA9BB4C7AECDED5A42CCE2962CFBB689488F1B713990687DE876AC01070`;
- result: `417AB2F17C42FD6313CC2798AC055EEF75AB16F0431BE6486619C762FA253226`;
- evidence: `B1D454E1F1390C0FB7D594D80197BA87DA75B5D4216CBF9177F8883E46268B4D`.

Machine-readable result:
[`p3-6-quarantine-remediation-r1-result.json`](../../contracts/phase-3/p3-6-quarantine-remediation-r1-result.json).

Human record:
[`p3-6-quarantine-remediation-r1-attempt.md`](p3-6-quarantine-remediation-r1-attempt.md).

### DR-0065: U3H failure analysis and owner choices sealed

Status: owner selections pending; planning-only and non-effective.

The consumed U3G evidence confirms that the protected root contained exactly
three explicit rules, but the current-process `Modify` tuple did not satisfy
the exact verifier. Microsoft documents that `Synchronize` is automatically
added to allow ACEs, making `Modify | Synchronize` the leading explanation.
Because U3G intentionally retained no raw ACL, this is recorded as a
high-confidence inference rather than a retroactive fact.

The Defender projection returned no usable `AMProductVersion`. Microsoft
documents that PowerShell 7 Windows-compatibility modules use a background
Windows PowerShell 5.1 implicit-remoting session and return serialized property
snapshots. U3H therefore proposes native Windows PowerShell scalar projection
and a separate trust-gated latest-platform fallback, while treating transport
as a hypothesis until separately authorized evidence exists.

Six explicit decisions `D-P3.6-U3H-001` through `006` cover allow-mask
normalization, independent DACL tuple checks, Defender status transport,
Defender candidate fallback, attempt decomposition, and transaction-runner
reviewability. The recommended selection is `A/A/A/A/A/A`.

The immutable package SHA-256 is
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
No selection may be inferred. The package grants no runner implementation,
retry, `F:` or ACL action, Defender access, scanner use, acquisition, model,
runtime, validation, profile, deployment, or remote Git authority.

Human proposal:
[`p3-6-quarantine-failure-analysis-r2-proposal.md`](p3-6-quarantine-failure-analysis-r2-proposal.md).

Machine-readable package:
[`p3-6-quarantine-failure-analysis-r2-decision-package.json`](../../contracts/phase-3/p3-6-quarantine-failure-analysis-r2-decision-package.json).

### DR-0066: U3H failure-analysis policies accepted

Status: `A/A/A/A/A/A` accepted as non-effective planning policy on 2026-08-31.

`mayank-admin` explicitly selected `D-P3.6-U3H-001` through `006` as
`A/A/A/A/A/A` against immutable package SHA-256
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
The accepted policies require exact `Modify | Synchronize` normalization,
independent three-tuple DACL checks, native Windows PowerShell 5.1 scalar
projection, a bounded trust-gated Defender platform fallback, storage-first
attempt decomposition, and a content-hashed reviewable runner proposal.

Acceptance record SHA-256 is
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`.
It authorizes preparation only of a non-effective reviewable runner proposal
and storage-only action/authorization proposal. A Defender-only proposal may be
prepared only after storage evidence is accepted. No retry, `F:` or ACL action,
Defender query/hash/trust action, scanner action, runner implementation,
acquisition, runtime/model execution, profile activation, deployment, or
remote Git action is authorized.

Machine-readable acceptance:
[`p3-6-quarantine-failure-analysis-r2-owner-decisions.json`](../../contracts/phase-3/p3-6-quarantine-failure-analysis-r2-owner-decisions.json).

### DR-0067: U3I reviewable runner implementation proposal sealed

Status: pending exact owner implementation authorization on 2026-08-31.

The accepted U3H runner-reviewability policy produced a deliberately
non-executable plain-text source proposal, a machine-readable runtime and
static-dispatch contract, twenty generated-only contract vectors, an exact
implementation-authorization proposal, and a sealed manifest. The package
SHA-256 is
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`.

Decision `D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH` remains pending. Exact
acceptance would authorize only one reviewable runner source, one
machine-independent generated contract harness, and non-observational
implementation evidence. It would not authorize runner execution, runtime or
machine queries, `F:` access, ACL work, a storage attempt, Defender/scanners,
downloads, models, deployment, or remote Git. A later implementation-evidence
package and separate execution authorization remain mandatory.

Human proposal:
[`p3-6-quarantine-transaction-runner-r0-implementation-authorization-proposal.md`](p3-6-quarantine-transaction-runner-r0-implementation-authorization-proposal.md).

Machine-readable package:
[`p3-6-quarantine-transaction-runner-r0-implementation-authorization-package.json`](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-authorization-package.json).

### DR-0068: U3J storage R2 planning proposal sealed

Status: pending exact owner planning acceptance on 2026-08-31.

The separate storage-only R2 proposal binds exact absent-root targeting for
`F:\HCAM-Quarantine`, security at creation, exact current-process
`Modify | Synchronize` normalization, independent three-tuple and unauthorized-
principal checks, one 4096-byte generated zero-retention probe, bounded
sanitized outputs, no Defender/scanner actions, and no automatic retry. Its
sealed proposal-package SHA-256 is
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.

Decision `D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE` remains pending and is
planning-only. Even exact acceptance cannot authorize an attempt. The runner
must first be separately authorized, implemented, pass all twenty generated
vectors, receive exact source/runtime bindings, and have its implementation
evidence accepted. Only then may a new final U3K execution package be sealed
for separate `D-P3.6-U3K-STORAGE-R2-AUTH` review. No `F:`, ACL, probe, runtime,
Defender/scanner, artifact, model, deployment, or remote Git action is currently
authorized.

Human proposal:
[`p3-6-quarantine-storage-r2-authorization-proposal.md`](p3-6-quarantine-storage-r2-authorization-proposal.md).

Machine-readable package:
[`p3-6-quarantine-storage-r2-authorization-proposal-package.json`](../../contracts/phase-3/p3-6-quarantine-storage-r2-authorization-proposal-package.json).

### DR-0069: U3I implementation authority and U3J storage design accepted

Status: accepted under exact package digests on 2026-08-31.

`mayank-admin` accepted
`D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH` against package digest
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`
and `D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE` against package digest
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.

U3I permits only a reviewable contract-mode runner, a machine-independent
generated harness, generated-vector execution, and non-observational evidence.
U3J accepts only the storage design. Their acceptance-record SHA-256 values are
`CD81871C6B6F560CDC01E9D6AA919B71F9E108DEB3AEA3C04B17BAF28C60D525`
and
`6F68EB164DC662086F7444D49638FFAB95F7FF1586469BB5E5E2DC876185AAA5`.
Neither decision authorizes runner execution, runtime binding observation,
`F:` or ACL access, storage attempts, Defender/scanners, models, deployment, or
remote Git.

### DR-0070: Contract-only runner implementation evidence sealed

Status: implementation package sealed on 2026-08-31 and exactly owner accepted
on 2026-09-01.

The authorized implementation adds one PowerShell source with contract mode,
ten static action IDs, exact-plan checks, output/path/ACL/probe reference-policy
validation, and default denial. Every machine-action branch throws
`P36_MACHINE_HANDLER_NOT_IMPLEMENTED`; the source contains no drive, ACL,
Defender, scanner, runtime-inventory, or machine mutation calls.

A Python machine-independent reference harness covers all twenty sealed
generated vectors plus authorization, source-structure, and no-access checks.
The focused result is 24 passed, Ruff passes, and PowerShell parser validation
reports zero syntax errors. The runner itself was not executed. The immutable
implementation-package SHA-256 is
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`;
source SHA-256 is
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.

`D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE` is recorded in the separate
acceptance record. It authorizes preparation only of a separate non-effective
runtime-binding proposal. Runtime observation, runner execution, U3K package
preparation, and machine access remain blocked.

Machine-readable evidence:
[`p3-6-quarantine-transaction-runner-r0-implementation-evidence.json`](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-evidence.json).

Machine-readable package:
[`p3-6-quarantine-transaction-runner-r0-implementation-package.json`](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-package.json).

### DR-0071: Contract-only runner implementation accepted

Status: accepted against the exact implementation-package digest on
2026-09-01.

`mayank-admin` explicitly supplied
`D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE` for package digest
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`.
The acceptance record SHA-256 is
`70F2EE1133648F16CA6298C25FB6C46F56AA7C88FBA97553BDD0A2F55D90C63A`.

This accepts only the contract-mode source, generated/static evidence, twenty
passing vectors, four structural checks, parser-only validation, unimplemented
fail-closed machine handlers, and documented limitations. It authorizes
preparation only of a separate non-effective runtime-binding authorization
proposal. It does not authorize runtime observation, `pwsh.exe` or runner
execution, machine handlers, U3K preparation, `F:` or ACL access, storage,
Defender/scanners, acquisition, models, deployment, or remote Git.

Machine-readable acceptance:
[`p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json`](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json).

### DR-0072: Read-only PowerShell 7 runtime-binding proposal sealed

Status: exact one-attempt authorization recorded and consumed on 2026-09-01.

The U3I acceptance produced a separate one-attempt read-only proposal for exact
`C:\Program Files\PowerShell\7\pwsh.exe` on logical node `LAB-LAPTOP-01`.
The proposal binds only canonical/non-reparse classification, a 256 MiB file
size ceiling, file and product versions, PowerShell major version 7, SHA-256,
cache-only no-UI whole-chain-excluding-root WinVerifyTrust, and the accepted
runner-source digest. It has no alternate path discovery, PATH/registry/WMI or
directory inventory, network retrieval, execution, storage, or scanner scope.

The immutable authorization-package SHA-256 is
`37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`.
Decision `D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH` authorized at most one sanitized
read-only attempt within 24 hours. The authorization was recorded before the
runtime observation and is now consumed. Runner execution and all storage or
machine actions remain blocked.

Human proposal:
[`p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-proposal.md`](p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-proposal.md).

Machine-readable package:
[`p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-package.json`](../../contracts/phase-3/p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-package.json).

### DR-0073: Exact PowerShell 7 runtime binding succeeded

Status: exact evidence accepted on 2026-09-01.

The single authorized attempt classified only the exact fixed runtime path and
its fixed parent components, read bounded version and size metadata, hashed the
exact runtime, completed cache-only no-UI whole-chain-excluding-root
WinVerifyTrust with provider state closed, and re-bound the accepted runner
source without executing either file. Runtime SHA-256 is
`362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139`;
runner-source SHA-256 remains
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.

Authorization, result, and evidence SHA-256 values are respectively
`1C3144D82EA1B41B3FBBE7E70F5BF74ED5EE5ACC709CAB272E2CBD287253648F`,
`643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7`,
and `4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`.
The exact binding remains valid through `2026-09-01T19:36:06.820Z`.

Decision `D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` accepts the exact evidence
and authorizes preparation of a separate final U3K package only; it cannot
execute the runner, access storage, query scanners, acquire artifacts, activate
a profile, deploy, or perform remote Git. The acceptance-record SHA-256 is
`F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E`.

Evidence review:
[`p3-6-quarantine-transaction-runner-r0-runtime-binding-evidence-review.md`](p3-6-quarantine-transaction-runner-r0-runtime-binding-evidence-review.md).

### DR-0074: Final U3K preparation package sealed but non-executable

Status: preparation complete; machine-handler implementation remains blocked
on 2026-09-01.

The accepted runtime binding authorized preparation of the separate final U3K
package. Package SHA-256 is
`4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`.
It binds the accepted U3J storage design, exact runner source, accepted runtime
binding, target `F:\HCAM-Quarantine`, one-attempt limit, and actions `U3K-A01`
through `U3K-A10`.

The package is deliberately non-effective. The accepted runner's ten machine
handlers still throw `P36_MACHINE_HANDLER_NOT_IMPLEMENTED`; no machine-handler
implementation or evidence has been authorized, produced, or accepted.
Therefore `D-P3.6-U3K-STORAGE-R2-AUTH` is not requestable against this package.
A future executable package requires separately authorized and accepted
handler implementation plus a current accepted runtime binding.

Human review:
[`p3-6-quarantine-storage-r2-final-u3k-authorization-proposal.md`](p3-6-quarantine-storage-r2-final-u3k-authorization-proposal.md).

Machine-readable package:
[`p3-6-quarantine-storage-r2-final-u3k-authorization-package.json`](../../contracts/phase-3/p3-6-quarantine-storage-r2-final-u3k-authorization-package.json).

## Decisions Explicitly Deferred

- production accelerator/runtime and GPU fleet;
- exact Kubernetes or other production-orchestrator topology and deployment;
- Tier B/C implementation order;
- persistent evidence media;
- cross-camera correlation or person/vehicle identity;
- Government databases, watchlists, owner records, and alert policy;
- statewide procurement, capacity, data residency, and production SLOs.

Deferred means unapproved, not implicitly allowed.
