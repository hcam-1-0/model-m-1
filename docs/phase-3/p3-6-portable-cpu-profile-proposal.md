# P3.6 Portable CPU Profile Proposal R0

Status: sealed non-executable planning proposal under `D-P3.6-PLAN-AUTH`.
Owner review is pending. The profile is not resolver-eligible and cannot run.

Machine-readable records:

- [portable CPU proposal](../../contracts/phase-3/p3-6-portable-cpu-profile-proposal.json);
- [portable CPU research sources](../../contracts/phase-3/p3-6-portable-cpu-research-sources.json); and
- [Phase -1 alignment](p3-6-phase-minus-1-alignment.md).

## Purpose

This proposal converts the already authorized `LAB-LAPTOP-01` inventory into a
reviewable candidate for the shared Phase -1 `portable_cpu` profile. It does
not probe the laptop again, install anything, load a model, run inference, or
claim performance. Unknown values remain explicit blockers.

The proposal provides a conservative local baseline that can later be compared
with an `owned_gpu_lab`, `standalone_server`, or `kubernetes_cluster` profile
without changing H-CAM domain, security, pipeline, evidence, or failure
contracts.

## Immutable Bindings

| Input | Exact binding |
| --- | --- |
| Shared contracts | `hcam-protos@d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8` |
| Deployment profiles | `hcam-deployment@71095fe89d2b711e4982ddc0130fcaedda8703e7` |
| Deployment base | `sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf` |
| Overlay | `profiles/v1alpha1/overlays/portable-cpu.json` |
| Inventory | `P36-INVENTORY-LAB-LAPTOP-01-R0`, SHA-256 `0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F` |
| Logical profile | `portable_cpu` / `hcam-portable-cpu` |

The Phase -1 contracts remain experimental/planned. This proposal does not
promote them or create an executable deployment profile.

## Existing Machine Evidence

The sealed inventory records:

- Windows 10 Pro 64-bit build 19045;
- Intel Core i5-8365U, four physical cores and eight logical processors;
- 8 GiB RAM;
- Intel UHD Graphics 620, excluded from this CPU-only profile;
- no observed discrete NVIDIA accelerator;
- less than seven percent free space on every observed fixed volume;
- no AI runtime packages in the default Python distribution at inventory time.

The inventory does not establish trust-zone policy, runtime availability,
artifact availability, decoder capacity, inference performance, thermal
behavior, or C1/C10/C50 capacity. Its freshness expiry is also unresolved, so
it cannot currently satisfy resolver admission.

## Candidate Behavior Reference

The proposal carries forward the accepted P3.2 generated-only CPU behavior
tuple as a candidate, not as a P3.6 activation:

| Field | Candidate value |
| --- | --- |
| Model | `DET-R0` YOLOX-Tiny |
| Model digest | `427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7` |
| Input | float32 `[1, 3, 416, 416]` |
| Python | `3.14.6` |
| ONNX Runtime | `1.29.0` |
| Provider | exactly `CPUExecutionProvider` |
| Precision | float32 |
| Execution | sequential, one intra-op thread, one inter-op thread |
| Graph optimization | basic |

The existing lock identifies the CPython 3.14 Windows x64 ONNX Runtime wheel
as 14,350,643 bytes with SHA-256
`4a3129ae56e70d2618ff773920166916310370a7e3cacb60b9e0e8910092725f`.
That is metadata only. The proposal does not claim the wheel is present,
scanned, loadable, or approved as a P3.6 bundle.

The historical P3.2 generated structural smoke completed in 206 ms. That value
is deliberately excluded from every P3.6 latency, throughput, freshness,
capacity, quality, pilot, and deployment decision.

## Why Configuration Must Be Explicit

[ONNX Runtime thread-management documentation](https://onnxruntime.ai/docs/performance/tune-performance/threading.html)
describes separate intra-op and inter-op controls, sequential versus parallel
graph execution, and thread spinning. Spinning can trade CPU and power use for
latency, so an exact profile must state it rather than accept an invisible
default.

[ONNX Runtime execution-provider documentation](https://onnxruntime.ai/docs/execution-providers/)
defines ordered provider priority and provider-option inspection. The portable
reference therefore requires exactly `CPUExecutionProvider`; an unexpected
provider list or precision is a rejection, not an automatic fallback.

[ONNX Runtime graph-optimization documentation](https://onnxruntime.ai/docs/performance/model-optimizations/graph-optimizations.html)
states that offline optimization binds provider, optimization, and target
assumptions. This proposal forbids an offline optimized graph until it is
reviewed as a separate derived artifact.

The official [ONNX Runtime installation guidance](https://onnxruntime.ai/docs/install/)
also has platform prerequisites. A lock entry is not proof that the runtime is
installed or usable on this node.

## Conservative Candidate Envelope

The proposed starting envelope is intentionally narrow:

- one active assignment;
- one worker process and one worker operation at a time;
- detector batch size one;
- one in-flight inference request;
- a two-item bounded queue;
- no oversubscription;
- optional enrichment off;
- all required pipeline stages preserved;
- reject and safe-pause on provider or precision mismatch.

These are planning values, not measured or accepted capacity. Queue age, CPU
and memory reservations, sampling floor, spinning, memory arenas, and thermal
policy remain unresolved. The unresolved values keep the profile ineligible.

## Proposed Generated Workload

The first eventual validation is restricted to C1 `INFER` evidence using a
deterministic in-memory float32 tensor shaped `[1, 3, 416, 416]`. It excludes
decode, media, files, cameras, streams, external data, and persistence.

The eventual scenarios are cold start, warm steady operation, bounded burst,
dependency loss, and safe shutdown. Duration, warmup count, measured count,
repetitions, seed manifest, and numeric acceptance thresholds remain
unresolved. No scenario may execute without a separate exact authorization.

`balanced` is the proposed default objective. `throughput` and `latency` remain
disabled until exact evidence can rank eligible profiles without bypassing
quality, capacity, freshness, fairness, lineage, or recovery gates.

## Required Evidence Before Activation

Activation requires all of the following through later decisions:

1. `P36-G1` model champion and fallback approval;
2. fresh inventory expiry and trust-zone policy;
3. sealed runtime dependency closure and model-artifact state;
4. explicit thread spinning, memory arena, CPU, RAM, queue-age, and sampling
   values;
5. immutable C1 workload duration, iterations, repetitions, and seeds;
6. numeric quality, latency, throughput, freshness, resource, and recovery
   gates;
7. authorized generated-only evidence for the exact tuple;
8. immutable compatibility and rollback bundle;
9. an exact digest-bound implementation/runtime authorization.

Until then, the resolver must report the profile as ineligible and return a
bounded safe reason. It must not substitute defaults.

## Owner Decision

The later decision
`D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE` may accept only this planning
proposal. Acceptance would not make the profile resolver-eligible and would
not authorize artifact acquisition, installation, runtime execution, model
loading, inference, hardware testing, implementation, or deployment.

## Continuing Boundary

This proposal authorizes no dependency/model/dataset/driver/container/artifact
download, runtime or inference, hardware/performance/stress/thermal test,
container/Kubernetes action, product implementation, camera/media/Sentinel/
ONVIF/stream access, private or Government data, identity, watchlist, alert,
deployment, remote Git action, P3.7, or later work.
