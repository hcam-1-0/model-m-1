# P3.6 Exact Model Artifact Research Proposal R0

Status: prepared, non-authorizing, and blocked on exact storage and scanner
bindings.

Machine-readable records:

- [official-source evidence ledger](../../contracts/phase-3/p3-6-model-artifact-research-sources.json);
- [fail-closed acquisition proposal](../../contracts/phase-3/p3-6-model-artifact-research-proposal.json).

## Purpose And Authority

This package completes the metadata-only part of `P36-U2` under
`D-P3.6-PLAN-AUTH`. It identifies exact upstream checkpoint objects for
`DET-E1`, `DET-B1`, and `DET-A1` and defines the controls that a later,
separately authorized quarantine acquisition would require.

The research used current official repository files, release metadata,
documentation, model-repository metadata, and metadata-only object headers.
No model, source archive, dependency, dataset, container, or artifact payload
was downloaded. No checkpoint was loaded, unpickled, imported, exported,
converted, scanned, or executed. No inference, benchmark, hardware test,
implementation, camera/media/data access, deployment, or remote Git action was
performed.

This R0 package is not an acquisition authorization. It is intentionally
non-executable because the exact quarantine root and exact scanner invocation
are unresolved.

## Exact Candidate Objects

| Candidate | Exact object | Bytes | Upstream identity | Current state |
| --- | --- | ---: | --- | --- |
| `DET-E1` | `dfine_n_coco.pth` | 15,489,558 | D-FINE release `dfinev1.0`, GitHub asset `204585647` | Unacquired; publisher digest and checkpoint-specific license review unresolved |
| `DET-B1` | `rf-detr-small.pth` | 386,045,550 | RF-DETR `1.9.4`, GCS generation `1753220474114031`, MD5 `fb37061c1af7bace359c91b723a8d5c1` | Unacquired and unapproved |
| `DET-A1` | `rf-detr-large-2026.pth` | 135,954,129 | RF-DETR `1.9.4`, GCS generation `1769071352867281`, MD5 `5cb72153541cbcb9aa6efa26222acc75` | Unacquired and unapproved |

The exact cumulative native-checkpoint size is `537,489,237` bytes. The old
RF-DETR `rf-detr-large.pth` object is explicitly excluded; the selected Large
candidate is the current `rf-detr-large-2026.pth` object referenced by the
stable `1.9.4` registry.

All three selected files are native PyTorch `.pth` checkpoints. They must be
treated as pickle-bearing, potentially executable serialized content. A future
acquisition step may hash, scan, and passively inspect them, but it must never
load or unpickle them.

## DET-E1: D-FINE-N

The official D-FINE model zoo reports D-FINE-N at 42.8 COCO AP, 4 million
parameters, 7 GFLOPs, and 2.12 ms under its publisher benchmark conditions:
TensorRT 10.4.0, FP16, batch one, and NVIDIA T4. Those values are upstream
claims, not H-CAM measurements and not evidence for the current Intel laptop,
the collaborator GPU laptop, C1, C10, or C50.

The reviewed official configuration binds the model to a `640 x 640` input and
COCO 2017's 80 categories. The exact source revision recorded for this review
is `956d1709314c2c6a4df6f34de232054578a7449f`. The linked checkpoint is the
GitHub release asset `204585647`, 15,489,558 bytes, in the D-FINE storage
release tagged `dfinev1.0`.

The source repository is Apache-2.0. However, the reviewed release metadata
does not supply a separate checkpoint license statement or publisher digest.
The proposal therefore does not treat the checkpoint license as resolved.
Any later review must retain exact license evidence, compute an H-CAM SHA-256,
and leave promotion blocked until the artifact disposition is accepted.

The official export script loads the `.pth` checkpoint with `torch.load` and
documents ONNX opset 16 with `labels`, `boxes`, and `scores` outputs. That is
future integration metadata only. This package does not authorize the source,
dependencies, checkpoint loading, or export.

## DET-B1 And DET-A1: RF-DETR 1.9.4

The proposal pins RF-DETR stable release `1.9.4` at revision
`9b009fa928d6218320439803d1da01869a85c072`; it does not pin the moving
`develop` branch.

The official RF-DETR material reports these publisher benchmarks:

| Candidate | Input | AP50 | AP50:95 | Latency | Parameters |
| --- | ---: | ---: | ---: | ---: | ---: |
| `DET-B1` Small | `512 x 512` | 72.1 | 53.0 | 3.5 ms | 32.1 M |
| `DET-A1` Large | `704 x 704` | 75.1 | 56.5 | 6.8 ms | 33.9 M |

The latency figures are publisher results for TensorRT FP16, batch one, on an
NVIDIA T4. They are not H-CAM evidence and cannot select a champion or establish
performance on any H-CAM profile.

The official project designates Nano through Large weights, including both
selected candidates, as Apache-2.0. Exact license evidence must still accompany
each acquired artifact and its ML-BOM entry.

RF-DETR's official COCO checkpoints represent COCO's 80 categories using a
sparse 90-slot label space. Release `1.9.4` records a post-processing issue:
official sparse-ID COCO checkpoints require `background_class_id=None`; the
default `-1` causes incorrect decoding. A future integration must bind this
value explicitly and prove numerical parity before any benchmark or promotion.

The official export documentation covers ONNX opset 17 and ONNX Runtime,
OpenVINO, and TensorRT paths. TensorRT engines are machine and runtime specific.
No export or runtime path is selected or authorized by R0.

## Safetensors Companion Metadata

Official Roboflow Hugging Face model repositories expose Apache-2.0
`model.safetensors` companions:

| Candidate | Repository revision | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `DET-B1` | `3bdc465063270f99769da5a1b4c00c68bd2d439d` | 128,504,496 | `2bfab2fa5f5fcc4870e756c8dc8d2d5acca3a68ffcc0f7e84972661873eb5a1d` |
| `DET-A1` | `f62f7dd5252b61097cbace33886045816dadbde9` | 135,795,376 | `1ec604598aea748627eb5755a9989f3c80839fc7fb977a91bfba107ee76fcd7d` |

These are recorded only as safer-format metadata companions. They are not in
the proposed acquisition allowlist because equivalence to the official native
`.pth` objects has not been established. A later proposal may prefer them only
after architecture, parameter, preprocessing, post-processing, and numerical
equivalence are proven from official evidence or an authorized offline parity
evaluation.

## Fail-Closed Acquisition Design

A later R1 proposal, not this R0 record, may request authority to acquire only
the three exact native objects. It must preserve all of these controls:

1. Download one artifact at a time as a bounded stream into a `.partial` file.
2. Permit only the exact HTTPS URLs in the machine-readable proposal.
3. Disable environment proxies, credentials, wildcard hosts, and unrelated
   repository, model-hub, source, dependency, dataset, and container requests.
4. Permit the D-FINE release redirect only from `github.com` to
   `release-assets.githubusercontent.com`; permit no other redirect.
5. Abort immediately if the byte count differs from the exact expected size.
6. Verify the exact RF-DETR GCS generation and publisher MD5 identity metadata.
7. Compute and record SHA-256 for every acquired object. Publisher MD5 is only
   an object-identity check and is not the H-CAM security digest.
8. Run the exact pre-bound local scanner and passive file/pickle inspection
   without importing, unpickling, or framework-loading a checkpoint.
9. Record license, lineage, source, scanner, static-inspection, and ML-BOM
   evidence before renaming the `.partial` file.
10. Keep any failed or mismatched object quarantined until a separate exact
    cleanup authority permits deletion.

The R1 action must not download source code, dependencies, datasets,
containers, alternate weights, or model-hub companions. It must not load,
convert, export, infer, benchmark, promote, alias, or deploy a candidate.

## Storage Blocker

The logical quarantine root is `P36-QUARANTINE-ROOT-R0`; its physical path is
deliberately `null`.

Volume `B:` is prohibited by the owner because it is RaiDrive/Google Drive.
The sanitized inventory found the observed fixed volumes `C:`, `E:`, and `F:`
ineligible under the low-free-space policy. This proposal does not assign
`F:` or silently substitute another volume.

Before an R1 acquisition request can be issued, the owner must make available
an exact local, non-cloud, non-network-backed root. A fresh sanitized check must
show both at least 5 GiB free and at least 15 percent free. The R1 record must
bind the canonical physical root and each candidate's resolved quarantine path.

## Scanner Blocker

The scanner product, version, executable path, and exact command are all
`null` in R0. No scanner is assumed merely because one may be installed.

R1 must bind one exact local scanner invocation, its version evidence, exit-code
interpretation, timeout, output-redaction policy, and per-artifact result path.
It must also define a passive checkpoint inspector that does not import the
model framework or execute pickle content. Failure, timeout, missing scanner,
version drift, or ambiguous result must fail closed.

## Gate Effects

This proposal improves P3.6 readiness without passing an execution gate:

- `P36-U2` metadata proposal preparation is complete.
- `P36-G1` remains blocked because upstream metadata is not H-CAM comparison
  evidence and no champion/fallback pair is approved.
- `P36-G2` remains blocked because exact machine, runtime, provider, precision,
  decoder, resource, and generated-workload manifests are incomplete.
- `P36-G4` remains blocked because no artifact acquisition is authorized and
  storage/scanner bindings are unresolved.
- `P36-G5` remains blocked because no executable package or runtime authority
  exists.

`DET-R0` remains the previously accepted restricted P3.2 generated-only
reference. R0 does not widen its scope or promote any new candidate.

## Decisions And Next Action

`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` may accept only this planning package's
metadata, boundaries, and unresolved blockers. It grants no download,
implementation, runtime, model loading, inference, hardware test, media/data
access, container/Kubernetes action, deployment, or remote Git authority.

`D-P3.6-MODEL-RESEARCH-R1-AUTH` is not issuable now. The next bounded work is:

1. free or provide an eligible exact local quarantine root;
2. perform an authorized sanitized free-space recheck;
3. bind the exact local scanner and passive-inspection command;
4. regenerate an R1 proposal with those bindings and a new immutable digest;
5. request explicit owner acceptance of the exact R1 digest and allowlist.

Only after that separate authorization could acquisition begin. Acquisition
would still not authorize checkpoint loading, export, inference, evaluation,
promotion, implementation, or deployment.
