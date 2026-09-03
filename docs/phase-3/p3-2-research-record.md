# P3.2 Controlled Research Record

Status: `D-P3.2-001 owner_authorized`; P3.2 implementation remains blocked.

Authorized: 2026-08-24 by `mayank-admin`.

## Authorization

The owner authorized broader research and clarified the scope as controlled
model/dataset downloads and offline experiments. The machine record is
[`p3-2-research-authorization.json`](../../contracts/phase-3/p3-2-research-authorization.json).

This authorization permits exact, manifested public artifacts to be placed in
an external quarantine; hash, size, provenance, license, lineage, and SBOM
research; and CPU-only offline experiments on generated or separately
license-cleared public inputs.

It does not authorize P3.2 product implementation, `D-P3.2-START`, training,
fine-tuning, cameras, Sentinel, streams, media, Government/private/scraped data,
identity or watchlists, operational alerts, pilots, deployment, or remote Git
actions.

## Storage And Transfer Controls

- machine research root: `F:\h cam\research-cache\phase-3\p3-2`;
- per-artifact limit: 512 MiB;
- cumulative artifact limit: 2 GiB;
- exact manifested HTTPS URLs and revalidated redirect hosts only;
- environment proxies, URL credentials, non-HTTPS sources, and unlisted hosts
  are rejected;
- downloads use a partial file, bounded streaming, SHA-256, and an atomic final
  rename;
- artifact binaries, package environments, and experiment outputs stay outside
  Git; and
- downloaded code and archives are not executed or extracted.

## First Research Candidate

`DET-R0-ONNX-UPSTREAM-0.1.1RC0` is the official pre-generated
`yolox_tiny.onnx` release asset linked by the upstream ONNX Runtime demo. The
upstream records 416x416 input, 5.06 million parameters, 6.45 GFLOPs, and COCO
mAP 32.8. Those are upstream discovery claims, not H-CAM results.

The repository is Apache-2.0, but no separate weight-specific license statement
has been established. Therefore acquisition and offline research are allowed,
while artifact promotion under `D-P3.2-002` remains blocked.

Observed quarantine identity:

- bytes: `20219662`;
- SHA-256: `427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`;
- artifact ID: `DET-R0-ONNX-UPSTREAM-0.1.1RC0`; and
- status: research-only, not approved for H-CAM.

## Dataset Position

`DATA-GEN-R0` uses only deterministic programmatic arrays. It can support model
loading, shape, output, failure, and runtime smoke checks. It cannot support an
accuracy, fairness, representativeness, or deployment claim.

`DATA-PUB-R0` remains blocked. No public dataset may be downloaded until one
exact compact source has passed license, image-level provenance, privacy,
retention, redistribution, integrity, and relevance review. This avoids
implicitly treating a large benchmark or mixed-license image corpus as approved.

## Offline Experiment Evidence

The quarantined artifact passed ONNX full validation and ran twice through an
isolated Python 3.14.6 environment using ONNX 1.22.0, ONNX Runtime 1.29.0, and
NumPy 2.5.2. The environment is derived from the binary-only, hash-locked
[`p3-2-research-requirements.lock`](../../contracts/phase-3/p3-2-research-requirements.lock).

Both observations used three runs and produced the same output SHA-256:
`3562559CAD2DCD1AD0A15C74E3425A371B1725BA5574CDADF5FDB375FE3A519C`.
The model exposed one `tensor(float)` input named `images` with shape
`[1,3,416,416]` and one output named `output` with shape `[1,3549,85]`. Its ONNX
IR version is 6 and its `ai.onnx` opset is 11. Only `CPUExecutionProvider` was
enabled, fallback was disabled, and Python socket access was denied while the
session loaded and ran.

Observed three-run means were approximately 117.41 ms and 116.31 ms on the
developer laptop. These are discovery timings, not a benchmark, SLO, acceptance
threshold, or deployment claim. No postprocessing, boxes, labels, accuracy,
media, or real-world quality was evaluated.

`pip-audit` 2.10.1 reported no known vulnerabilities in the eight-package
research dependency lock on 2026-08-24. This is a point-in-time dependency
inventory result, not a model-security or supply-chain approval.

Microsoft Defender Antivirus also completed a custom scan of the exact ONNX
file with signature version `1.457.312.0`; no threat detection for the model was
reported. This is point-in-time malware evidence, not proof that a model is safe
or free of parser, model-behavior, or supply-chain risk.

The machine-readable result is
[`p3-2-research-evidence.json`](../../contracts/phase-3/p3-2-research-evidence.json).

## Commands

Acquire one manifested artifact:

```powershell
uv run --locked python tools/phase32_research_acquire.py `
  --artifact-id DET-R0-ONNX-UPSTREAM-0.1.1RC0
```

Run the experiment only from an isolated research environment containing
`onnx`, `onnxruntime`, and `numpy`:

```powershell
F:\h cam\research-cache\phase-3\p3-2\venv\Scripts\python.exe `
  tools/phase32_offline_experiment.py --runs 3
```

Results are structural research evidence only. No boxes, labels, detections,
media, or accuracy result are persisted.
