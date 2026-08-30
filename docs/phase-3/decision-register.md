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

## Decisions Explicitly Deferred

- production accelerator/runtime and GPU fleet;
- exact Kubernetes or other production-orchestrator topology and deployment;
- Tier B/C implementation order;
- persistent evidence media;
- cross-camera correlation or person/vehicle identity;
- Government databases, watchlists, owner records, and alert policy;
- statewide procurement, capacity, data residency, and production SLOs.

Deferred means unapproved, not implicitly allowed.
