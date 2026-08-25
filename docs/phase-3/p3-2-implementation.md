# P3.2 Generated-Only Detection Implementation

Status: implemented and under validation; owner exit acceptance is pending.

Decision authority: `D-P3.2-START`, expiring 2026-09-24.

## Scope

This is the portable detection slice authorized by `D-P3.2-START`. It runs one
exact YOLOX-Tiny ONNX artifact through ONNX Runtime CPU on deterministic
416 x 416 generated BGR frames. It has no camera decoder, stream adapter, image
upload, media URL, file-path input, recording, public dataset, training, or
deployment path.

The runtime is default-off and production configuration rejects it. The model
remains outside Git and is loaded only from a configured local artifact root
after filename, size, SHA-256, symlink, traversal, and root-boundary checks.

## Exact Activation Contract

An assignment can activate only when all of these values match:

| Field | Required value |
| --- | --- |
| Execution scope | `generated_only` |
| Capability | `object_detection` |
| Pipeline ID | `hcam.det-r0.generated` |
| Pipeline version | `sha256:8254f905921bc04bc42074a2353efcac81a0004bd2ffd2173f473b65dd9b47f7` |
| Model ID | `DET-R0-ONNX-UPSTREAM-0.1.1RC0` |
| Model version | `sha256:427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` |
| Taxonomy | `hcam.objects.tier_a.v1` |
| Policy version | `sha256:ba36957e4bf3207952e7f01ab584c960710dee2097c2e65cc7881f648ec93140` |
| Approval record | `D-P3.2-START` |
| Sampling | At most 1 FPS |
| Maximum queue age | At most 1,000 ms |
| Geometry | Empty |
| Retention | `derived.analytics.standard` |

Activation and execution also fail closed after the authorization expiry date
unless a new owner record updates the implementation binding.

The pipeline, policy, and generated-data versions are canonical SHA-256
bindings to the approved runtime, start-authorization, and dataset records.
Tests fail if those records drift from the implementation constants.

## Runtime Boundary

The optional `analytics` dependency group pins `numpy==2.5.2`, `onnx==1.22.0`,
and `onnxruntime==1.29.0`. The enabled adapter requires the approved Python
`3.14.6` reference profile, exact 20,219,662-byte artifact, and only
`CPUExecutionProvider`. Fallback is disabled. Startup validates ONNX structure,
input/output contracts, external-data absence, and the deterministic reference
output digest.

Inference is batch size one with sequential execution, one inter-op thread, one
intra-op thread, basic graph optimization, a 1,000 ms limit, cancellable ONNX
RunOptions, at most 300 post-NMS candidates, and no network access. The adapter
checks process resident memory against the approved 1 GiB ceiling before and
after inference, consumes an in-memory lease once, and maps exceptions to
bounded failure codes. A future deployment would still require an external
process/container memory limit; this local in-process check is not deployment
isolation.

## Processing

The server creates `DATA-GEN-R0` pixels programmatically from a bounded seed.
Requests never accept pixel bytes. The frame is BGR8, 416 x 416, and SHA-256
identified. Preprocessing produces float32 NCHW input without value
normalization. No alternate media size is accepted in this slice.

Postprocessing uses YOLOX strides 8, 16, and 32; grid decoding; exponential
width and height; objectness times highest class probability; class-agnostic
NMS at IoU 0.45; the assignment threshold; normalized boxes; and this exact
Tier A mapping:

- `object.person`
- `vehicle.bicycle`
- `vehicle.car`
- `vehicle.motorcycle`
- `vehicle.bus`
- `vehicle.truck`
- `object.unknown`

The approved taxonomy record is
[`p3-2-taxonomy.json`](../../contracts/phase-3/p3-2-taxonomy.json). It preserves
the prohibitions on biometrics, re-identification, cross-camera linkage,
sensitive traits, and autonomous enforcement.

## API And Lifecycle

The existing assignment APIs remain compatible. New control operations require
`camera.editor` or `platform.admin`, department scope, `If-Match`, and
`X-HCAM-Reason`:

- `POST /analytics-assignments/{id}/activate`
- `POST /analytics-assignments/{id}/pause`

Generated execution accepts only `seed`, `sequence`, and UTC `observed_at`:

- `POST /analytics-assignments/{id}/generated-runs`
- `GET /analytics-generated-runs/{run_id}`
- `GET /analytics-generated-runs/{run_id}/observations`

Lifecycle states are `blocked`, `paused`, `running`, `degraded`, and `failed`.
Transient runtime failures degrade the assignment. Configuration, artifact,
unsupported-capability, or invalid-input failures fail it closed. A later
successful generated run recovers a degraded assignment to `running`.
Configuration updates require a paused or blocked assignment.

Run, observation, and event IDs are deterministic. Repeating the same
assignment version, sequence, timestamp, and input reuses the existing run
without invoking inference or duplicating metadata.

## Persistence And Retention

Migration `0009_generated_analytics` adds:

- `analytics_generated_runs`: assignment/version, generated source lineage,
  input digest, bounded outcome, duration, and retention class;
- `analytics_observations`: anonymous Tier A class, confidence, normalized box,
  source metadata, immutable lineage, and outbox event ID.

Neither table has a frame, image, media, path, URL, locator, pixel, byte, or
blob column. Candidates produce validated
`hcam.analytics.observation.created.v1` events in the transactional outbox.
Runs, observations, and their observation events are deleted after 168 hours
for standard metadata or 24 hours for restricted metadata.

## Observability

Metrics use bounded status, state, operation, or failure-category labels:

- assignment lifecycle counts;
- generated run outcomes and average duration;
- bounded failure categories;
- retained anonymous observation count;
- active generated-frame leases;
- unpublished analytics outbox events.

Camera, stream, assignment, run, model, path, actor, and reason values are not
metric labels. Audits contain no frame content or artifact paths.

## Configuration

The runtime is disabled unless explicitly configured:

```text
HCAM_ANALYTICS_GENERATED_RUNTIME_ENABLED=true
HCAM_ANALYTICS_ARTIFACT_ROOT=<approved-local-artifact-root>
HCAM_ANALYTICS_MODEL_RELATIVE_PATH=DET-R0-ONNX-UPSTREAM-0.1.1RC0/yolox_tiny.onnx
```

It is forbidden when `HCAM_ENVIRONMENT=production`. The model is not copied
into a wheel, source distribution, container, fixture, snapshot, or Git path.

## Validation

The local external-artifact harness is:

```powershell
uv run python tools/phase32_generated_e2e.py `
  --artifact-root "<approved-local-artifact-root>"
```

It creates a temporary migrated database, validates readiness, seeds one
synthetic registry entry, activates the exact assignment, executes and replays
one generated input, inspects aggregate persistence, disposes the application,
and deletes the database. The evidence is
[`p3-2-local-e2e-evidence.json`](../../contracts/phase-3/p3-2-local-e2e-evidence.json).

The approved block fixture produced zero candidates at confidence 0.25. This is
an expected successful result and proves no accuracy, fairness,
representativeness, latency, pilot, production, or deployment claim.

## Remaining Exit Gate

Technical validation and the evidence-package digest are reported by
`tools/phase32_implementation_readiness.py`. P3.2 remains unaccepted until
`mayank-admin` accepts that exact digest. Acceptance would authorize only this
generated-only implementation state; it would not authorize P3.3, cameras,
media, public datasets, training, operational analytics, or deployment.
