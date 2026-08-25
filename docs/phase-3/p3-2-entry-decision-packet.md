# P3.2 Entry Decision Packet

Status: `implementation_authorized_generated_only`

Prepared: 2026-08-24

Accountable owner: `mayank-admin`

Scope: completed entry-decision audit and exact start-authorization boundary.

## Current Position

P3.0 and P3.1 are accepted. `D-P3.2-001` through `D-P3.2-004` now have
evidence-bound owner outcomes, and `D-P3.2-START` authorizes only the named
generated-input, local/CI, CPU reference implementation. This
does not complete P3.2, promote a deployment model, establish accuracy, or
authorize media access.

The exact reference is `DET-R0-ONNX-UPSTREAM-0.1.1RC0`, YOLOX-Tiny at 416
input through ONNX Runtime 1.29.0 `CPUExecutionProvider`, with SHA-256
`427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`.
The accepted P3.1 candidate metadata remains immutable and blocked as a
historical record; the later, exact restricted approval is separate.

## Entry Invariants

The P3.2 start remains valid only while every invariant below is true:

- the owner approves the exact P3.2 scope and non-authorization boundaries;
- one exact detector artifact is identified by immutable version and SHA-256;
- code, weight, model, and training-data terms are reviewed separately;
- artifact provenance, training lineage, model card, and SBOM are recorded;
- one exact evaluation source is approved with purpose, consent or license,
  provenance, retention, access, deletion, and leakage controls;
- the CPU reference runtime and export/parity method are fixed;
- numeric quality and resource thresholds remain proposal-only until measured;
- media access, cameras, Government/private data, alerts, pilots, and deployment
  remain separately blocked; and
- an explicit `D-P3.2-START` record authorizes implementation after the earlier
  decisions are complete.

No decision approves an unresolved placeholder, repository name, model family,
mutable URL, latest release, or unverified weight file.

## Entry Decisions

### D-P3.2-001: Planning And Research Boundary

The owner authorized broader research, clarified as controlled model/dataset
downloads and offline experiments. The exact scope and controls are recorded in
[`p3-2-research-authorization.json`](../../contracts/phase-3/p3-2-research-authorization.json)
and summarized in the
[`P3.2 controlled research record`](p3-2-research-record.md).

Required record:

- exact allowed evidence activities;
- exact prohibited activities;
- network and storage boundaries;
- accountable owner;
- expiry or review date; and
- statement that research completion is not implementation authorization.

Current state: `owner_authorized` for controlled research. Its original
research-only effect remains intact; the later start record supersedes it only
for the exact generated-only implementation work packages.

### D-P3.2-002: Exact Detector Artifact

The planned first candidate is `DET-R0`. Its exact restricted approval records
the following for one immutable artifact:

- candidate ID and intended role;
- source repository and immutable source revision;
- exact checkpoint/export filename and immutable source location;
- SHA-256 calculated after an authorized acquisition;
- code license, weight/model license, notices, and redistribution constraints;
- training datasets and lineage to the available level of evidence;
- model card and known limitations;
- dependency/SBOM and vulnerability review;
- export toolchain, opset, preprocessing, postprocessing, and taxonomy mapping;
- quarantine and rollback procedure; and
- an owner decision that names the exact artifact digest.

Current state: `owner_approved_restricted`. The model approval, model card, SPDX
inventory, exact source revision, official source hashes, artifact digest, and
accepted limitations are recorded in
[`p3-2-model-approval.json`](../../contracts/phase-3/p3-2-model-approval.json).
Local generated-only use is approved; redistribution remains prohibited and
publisher-reported COCO lineage is not an H-CAM accuracy result.

### D-P3.2-003: Evaluation Dataset And Generated Fixtures

The initial P3.2 path should keep deterministic P3.1 generated fixtures for
contract and failure testing. Those fixtures cannot prove real-world detector
quality. A separate source is required for any accuracy claim.

Options, in order of current risk:

1. Continue generated-only C1 integration testing. This can validate pipeline
   behavior but cannot authorize accuracy, promotion, or deployment claims.
2. Approve bounded `S1` team-owned media under an exact consent, purpose,
   retention, access, deletion, and audit record.
3. Approve an exact `S2` public dataset after license, provenance, privacy,
   representativeness, redistribution, integrity hash, and retention review.

`S4` private-camera media requires a separate camera/media authorization. `S5`
Sentinel, Government, police, scraped, and private third-party data remains
prohibited.

Current state: `owner_approved_generated_only` for `DATA-GEN-R0`, recorded in
[`p3-2-dataset-approval.json`](../../contracts/phase-3/p3-2-dataset-approval.json).
No public or real-media evaluation dataset is approved, and no accuracy,
fairness, representativeness, or readiness claim is available.

### D-P3.2-004: CPU Reference And Export Contract

The approved reference is ONNX Runtime CPU with no silent execution-provider
fallback. Its contract records:

- exact Python/runtime/package versions and lock evidence;
- declared input shape, color order, normalization, resize, and padding;
- declared output tensors, confidence interpretation, NMS, and taxonomy map;
- deterministic or bounded-nondeterministic behavior policy;
- timeout, memory, batch, image-size, output-count, and malformed-output limits;
- source-to-export parity method and tolerance;
- clean-machine smoke procedure; and
- fail-closed behavior when the artifact or runtime is absent.

Current state: `owner_approved_cpu_reference`, recorded in
[`p3-2-runtime-approval.json`](../../contracts/phase-3/p3-2-runtime-approval.json).
The exact versions, BGR/NCHW preprocessing, upstream-source parity hashes,
decoder, class mapping, fallback policy, and fail-closed limits are fixed.

### D-P3.2-START: Explicit Implementation Start

This is the final entry decision. It may be recorded only after
`D-P3.2-001` through `D-P3.2-004` have evidence-backed outcomes. It must name
the authorized work packages, exact artifact and dataset records, runtime,
hardware profile, expiry, non-authorizations, and exit gates.

Current state: `owner_authorized`. The exact generated-only authorization is in
[`p3-2-start-authorization.json`](../../contracts/phase-3/p3-2-start-authorization.json)
and summarized by the
[`P3.2 start authorization`](p3-2-start-authorization.md). It expires on
2026-09-24 and does not complete P3.2.

## Machine Verification

The exact evidence-bound start state is recorded in
[`p3-2-entry-gates.json`](../../contracts/phase-3/p3-2-entry-gates.json).
Validate it without changing state:

```powershell
uv run --locked --extra dev python tools/phase32_entry_readiness.py
uv run --locked --extra dev python tools/phase32_entry_readiness.py --json
```

A valid default or `--strict` run exits `0` while reporting
`implementation_authorized_generated_only`, zero failures, and zero manual
entry gates. CI proves the exact owner records, digests, expiry,
model/data/runtime scope, and continuing prohibitions. It does not prove P3.2
implementation or exit acceptance.

## Completed Entry Sequence

1. `D-P3.2-001` authorized manifested quarantine and offline research.
2. The exact artifact and immutable upstream evidence were acquired and hashed.
3. `D-P3.2-002` approved only that artifact for restricted local use.
4. `D-P3.2-003` approved deterministic generated inputs only.
5. `D-P3.2-004` fixed the CPU reference and export/parity contract.
6. `D-P3.2-START` authorized the named generated-only implementation packages.

## Evidence That Does Not Satisfy Entry

The following are discovery evidence only:

- upstream accuracy or latency tables;
- a repository-level open-source license by itself;
- an unverified release asset or mutable download URL;
- a model-family name without exact weights and digest;
- synthetic fixture success presented as real-world accuracy;
- camera compatibility or ONVIF capability records;
- P3.1 acceptance; and
- a general instruction to continue.

## Continuing Non-Authorization

No physical camera, ONVIF media, Sentinel stream, public dataset, or real,
team-owned, private, Government, police, or scraped media is authorized. The
records do not authorize uncontrolled downloads, training, fine-tuning, model
modification, GPU or networked inference, identity, watchlists, owner lookup,
sensitive-trait or criminality inference, operational alerts, autonomous action,
pilots, deployment, production claims, model redistribution, or remote Git
actions. Numeric accuracy thresholds remain `proposal_only`, and P3.2 exit
still requires separate digest-bound owner acceptance.
