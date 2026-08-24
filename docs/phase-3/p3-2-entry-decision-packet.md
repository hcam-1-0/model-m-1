# P3.2 Entry Decision Packet

Status: `blocked_pending_owner_decisions`

Prepared: 2026-08-24

Accountable owner: `mayank-admin`

Scope: pre-entry planning only. This packet is not P3.2 authorization.

## Current Position

P3.0 and P3.1 are accepted. The generated-only P3.1 package proves contract,
fixture, QA, split, metric, candidate-metadata, and reproducibility foundations.
It does not provide an executable detector, an authorized evaluation dataset,
an inference runtime, media access, or P3.2 approval.

The planned P3.2 reference remains `DET-R0` YOLOX-Tiny at 416 input through an
ONNX Runtime CPU adapter. That is a portfolio choice only. Its candidate record
is `blocked` because the exact checkpoint, weight license, training lineage,
model card, SBOM, artifact digest, and export contract are unresolved.

## Entry Invariants

P3.2 must remain blocked unless every invariant below is true:

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

No decision may approve an unresolved placeholder, repository name, model
family, mutable URL, latest release, or unverified weight file.

## Decisions Required

### D-P3.2-001: Planning And Research Boundary

Owner must choose whether to authorize a bounded pre-implementation evidence
pass. The recommended scope is metadata and official-document research only,
with no artifact or dataset download, inference, media, camera, or deployment.

Required record:

- exact allowed evidence activities;
- exact prohibited activities;
- network and storage boundaries;
- accountable owner;
- expiry or review date; and
- statement that research completion is not implementation authorization.

Current state: `pending`.

### D-P3.2-002: Exact Detector Artifact

The planned first candidate is `DET-R0`, but no exact artifact is eligible.
Approval requires all of the following for one immutable artifact:

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

Current state: `blocked`; five unresolved blockers are recorded for `DET-R0`.

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

Current state: generated fixtures exist; no detector evaluation dataset is
approved.

### D-P3.2-004: CPU Reference And Export Contract

The proposed reference is ONNX Runtime CPU with no silent execution-provider
fallback. Approval requires:

- exact Python/runtime/package versions and lock evidence;
- declared input shape, color order, normalization, resize, and padding;
- declared output tensors, confidence interpretation, NMS, and taxonomy map;
- deterministic or bounded-nondeterministic behavior policy;
- timeout, memory, batch, image-size, output-count, and malformed-output limits;
- source-to-export parity method and tolerance;
- clean-machine smoke procedure; and
- fail-closed behavior when the artifact or runtime is absent.

Current state: planned, not approved or implemented.

### D-P3.2-START: Explicit Implementation Start

This is the final entry decision. It may be recorded only after
`D-P3.2-001` through `D-P3.2-004` have evidence-backed outcomes. It must name
the authorized work packages, exact artifact and dataset records, runtime,
hardware profile, expiry, non-authorizations, and exit gates.

Current state: `not_authorized`.

## Machine Verification

The exact blocked state is recorded in
[`p3-2-entry-gates.json`](../../contracts/phase-3/p3-2-entry-gates.json).
Validate it without changing state:

```powershell
uv run --locked --extra dev python tools/phase32_entry_readiness.py
uv run --locked --extra dev python tools/phase32_entry_readiness.py --json
```

A valid default run exits `0` while reporting
`blocked_pending_owner_decisions`, zero technical failures, and five manual
gates. `--strict` intentionally fails while any owner gate remains pending
(the verifier returns `2`, although a command runner may expose a generic
nonzero status). CI uses the default command to prove the block is intact; CI
does not treat pending owner decisions as authorization or implementation
readiness.

## Recommended Sequence

1. Approve only `D-P3.2-001` for bounded official-source metadata research.
2. Resolve `DET-R0` evidence without downloading or executing an artifact.
3. Present the exact artifact record for `D-P3.2-002`; do not use a generic
   YOLOX or YOLOX-Tiny approval.
4. Present the exact source-governance record for `D-P3.2-003`.
5. Freeze the CPU/export contract under `D-P3.2-004`.
6. Re-audit every entry invariant and then request `D-P3.2-START`.

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

This packet does not authorize P3.2, downloads, model or dataset acquisition,
training, fine-tuning, export, inference, decoding, GPU use, cameras, Sentinel,
media, Government/private data, identity, watchlists, owner lookup, alerts,
pilots, deployment, or production claims. All candidate manifests remain
blocked and all numeric thresholds remain `proposal_only`.
