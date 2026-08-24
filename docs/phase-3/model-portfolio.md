# Phase 3 Model Portfolio

Status: selected for planning on 2026-08-24. This document chooses the models
that Phase 3 should evaluate. It does not approve an artifact, download,
dataset, inference run, implementation, production model, or deployment.

## Decision

H-CAM will not use one universal "best model." Phase 3 uses a role-based
portfolio so portability, low-resource operation, balanced quality, peak
accuracy, tracking, and script coverage are measured separately.

No candidate is the H-CAM champion until it passes the same frozen H-CAM
contracts, synthetic/authorized data, slice metrics, hardware manifests, and
promotion gates. Upstream benchmark scores are discovery evidence only.

## Selected Evaluation Portfolio

| ID | Role | Selected candidate | Intended use | Planning reason |
| --- | --- | --- | --- | --- |
| `DET-R0` | Portable reference | YOLOX-Tiny, 416 input, ONNX export | Deterministic CPU reference and adapter contract | Mature, comparatively small, Apache-2.0 source repository, and documented ONNX/OpenVINO deployment paths |
| `DET-E1` | Low-compute edge challenger | D-FINE-N, 640 input | Test whether a newer compact detector can replace the reference on constrained nodes | Small published parameter profile, Apache-2.0 source repository, and official ONNX Runtime/TensorRT tooling |
| `DET-B1` | Balanced candidate | RF-DETR-S, 512 input | Primary quality/latency candidate for general person and vehicle detection | Current fine-tuning-focused detector with Apache-designated code/model tier and a strong published transfer/latency profile |
| `DET-A1` | Accuracy candidate | RF-DETR-L, 704 input | Server or higher-capacity candidate where recall and small-object quality justify cost | Same maintainable family as `DET-B1`, higher published accuracy tier, and Apache-designated model tier |
| `TRK-R0` | Local tracker | ByteTrack | Anonymous stream-local tracking over normalized detections | Simple detector-driven association, no identity embedding requirement, established metrics, and MIT source license |
| `OCR-L0` | Latin balanced OCR | PP-OCRv6-small | English, numeric, and supported Latin-script scene/plate text | Current balanced PP-OCRv6 tier with ONNX Runtime/OpenVINO paths |
| `OCR-L1` | Latin accuracy OCR | PP-OCRv6-medium | Accuracy challenger when `OCR-L0` misses approved gates | Current higher-accuracy PP-OCRv6 tier; server-cost comparison remains explicit |
| `OCR-D0` | Devanagari OCR | `devanagari_PP-OCRv5_mobile_rec` | Hindi and other approved Devanagari text | The current PaddleOCR catalog explicitly identifies Devanagari and number support |
| `OCR-G0` | Gujarati CPU baseline | Tesseract 5 `guj` with `tessdata_fast` | First deterministic Gujarati script baseline | Official Gujarati traineddata exists and the fast tier is intended for lower-cost inference |
| `OCR-G1` | Gujarati accuracy challenger | Tesseract 5 `guj` with `tessdata_best` | Accuracy comparison against `OCR-G0` | Official best tier trades speed for accuracy and remains independently measurable |
| `PLATE-D0` | Plate-region detector | Dedicated detector derived from the promoted H-CAM detector family | Synthetic or explicitly authorized plate-region localization | Avoids assuming a foreign plate checkpoint transfers to Indian layouts or has acceptable provenance |

Exact repositories, commits, checkpoints, weight URLs, licenses, training-data
lineage, hashes, export tools, opsets, dictionaries, and fonts remain
unapproved. A repository license is not evidence that every linked weight or
training dataset has identical terms.

## Why These Roles

### Detection

`DET-R0` is intentionally conservative. It gives CI, laptops, contracts, and
accelerator comparisons a stable reference. It is not expected to win final
accuracy.

`DET-E1` tests a current compact architecture without replacing the reference
before parity evidence exists. `DET-B1` is the preferred balanced research
candidate. `DET-A1` tests the benefit and cost of a larger model from the same
family, reducing training and serving fragmentation if that family succeeds.

The detector taxonomy initially remains bounded to approved Tier A classes such
as person and broad vehicle categories. A pretrained label does not
automatically become an H-CAM capability.

### Tracking

ByteTrack receives only normalized boxes, classes, confidence, frame order, and
stream-local state. Track IDs are ephemeral within one stream and tracker
epoch. No ReID vector, face feature, gait feature, global identity, or
cross-camera join key is permitted.

### OCR And ANPR

PP-OCRv6 covers English and supported Latin scripts, but its published language
coverage must not be stretched to claim Gujarati or Devanagari support.
Devanagari and Gujarati therefore use separate candidates and separate reports.

Plate-region detection, text recognition, normalization, temporal consensus,
and end-to-end exact match remain separate stages and metrics. Raw OCR is never
overwritten by a normalized hypothesis. No registration-owner lookup,
Government matching, watchlist, or enforcement path exists in Phase 3.

## Candidate Funnel

The future evaluation is deliberately staged to avoid spending compute on an
ineligible or clearly unsuitable candidate.

1. **Artifact gate:** exact source, weight, model card, training lineage,
   license, hash, and vulnerability record are approved by the accountable
   owner.
2. **Export gate:** source and exported outputs meet a declared parity tolerance
   on frozen generated fixtures.
3. **Contract gate:** bounds, taxonomy, confidence, provenance, redaction,
   determinism, timeout, and malformed-output tests pass.
4. **Quality gate:** class, size, lighting, occlusion, blur, compression,
   density, and camera-angle slices pass approved minimums.
5. **Resource gate:** initialization, p50/p95/p99 latency, throughput, memory,
   sustained stability, and overload behavior pass on a declared profile.
6. **Downstream gate:** tracking and event quality do not regress beyond an
   approved tolerance.
7. **Runtime gate:** accelerated artifacts preserve approved numeric and
   behavioral parity with the reference.
8. **Promotion gate:** the accountable owner records an ADR selecting a champion,
   fallback, hardware scope, limitations, expiry, and rollback. Separate-person
   review is optional and non-blocking.

Failure at a hard gate stops that candidate. Results are reported per metric
and slice; a weighted aggregate score cannot hide a safety-relevant failure.

## Runtime Mapping

| Profile | Initial candidate mapping | Rule |
| --- | --- | --- |
| Portable CPU | `DET-R0`, `TRK-R0`, and applicable OCR through ONNX Runtime CPU or native Tesseract | First behavioral reference; no silent provider fallback |
| Intel owned hardware | Promoted ONNX candidates through OpenVINO EP | Evaluate only after CPU parity; record exact devices and fallback |
| NVIDIA lab | Promoted candidates through TensorRT/DeepStream | Evaluate only after model behavior is frozen; C10/C50 evidence is separate |
| Shared NVIDIA serving | Triton only after a measured multi-model or shared-GPU need | Serving complexity must be justified by a workload trigger |

## Deferred Or Conditional Candidates

- Ultralytics YOLO26 is not a default Phase 3 candidate. It may enter only
  after an explicit AGPL-compatible project decision or an approved Enterprise
  license and then must pass the same evidence gates.
- RT-DETRv4 is retained as a future accuracy challenger. Its official release
  is recent and its training chain includes a vision-foundation-model teacher;
  maturity and full artifact lineage must be justified before entry.
- PicoDet and PP-YOLOE+ remain Paddle compatibility fallbacks if the selected
  compact or balanced candidates fail a named requirement. Their exact weight
  and training-data terms still require review.
- BoT-SORT and other ReID-capable configurations are excluded from the default
  tracker study because Phase 3 has no identity or cross-camera role.
- VLMs remain outside the core detector/OCR path and retain their separate,
  trigger-based research gate.

## Decision Still Open

The portfolio chooses what should be evaluated, not what should be deployed.
The final champion/fallback decision, exact artifacts, taxonomy, numeric gates,
target hardware, retention, implementation start, and any real-camera use all
remain separate owner decisions.
