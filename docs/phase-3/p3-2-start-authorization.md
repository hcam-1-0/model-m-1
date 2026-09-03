# P3.2 Start Authorization

Status: `owner_authorized_generated_only_implementation`.

Authorized by: `mayank-admin` on 2026-08-24.

Owner statement: `d-p3.2 start`.

## Decision

`D-P3.2-START` authorizes P3.2 implementation only for the exact generated-only
CPU baseline recorded in
[`p3-2-start-authorization.json`](../../contracts/phase-3/p3-2-start-authorization.json).
It is not P3.2 completion, model promotion, camera authorization, an accuracy
claim, or deployment approval.

The four entry decisions are now evidence-bound:

- `D-P3.2-001`: controlled research authorization;
- `D-P3.2-002`: exact YOLOX-Tiny ONNX artifact approved for restricted local use;
- `D-P3.2-003`: deterministic `DATA-GEN-R0` inputs approved, with no external
  dataset or real media; and
- `D-P3.2-004`: ONNX Runtime 1.29.0 CPU reference contract approved.

## Exact Baseline

- model: `DET-R0-ONNX-UPSTREAM-0.1.1RC0`;
- model SHA-256:
  `427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`;
- runtime: Python 3.14.6, ONNX 1.22.0, ONNX Runtime 1.29.0, NumPy 2.5.2;
- execution provider: CPU only, with fallback prohibited;
- input: generated BGR, top-left letterbox padding 114, NCHW float32,
  416x416, no normalization;
- output: `[1,3549,85]`, strides 8/16/32 decode, objectness multiplied by
  class probability, class-agnostic NMS at 0.45; and
- classes: person, bicycle, motorcycle, car, bus, truck, and unknown under the
  approved Tier A taxonomy.

## Authorized Implementation

The team may implement the verified runtime adapter, generated-input path,
postprocessing and taxonomy mapping, anonymous normalized observation
persistence and outbox events, synthetic-lab assignment lifecycle, bounded
metrics, audits, failure handling, tests, documentation, and packaging.

## Continuing Boundary

No physical camera, ONVIF media, Sentinel stream, public dataset, or real,
private, Government, police, team-owned, or scraped media is authorized. No
training, fine-tuning, identity, watchlist, ownership lookup, sensitive-trait or
intent inference, operational alert, autonomous action, pilot, production
deployment, artifact redistribution, or remote Git action is authorized.

P3.2 exit requires a separate digest-bound accountable-owner acceptance before
P3.3 can start.
