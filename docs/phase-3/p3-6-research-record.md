# P3.6 Primary-Source Research Record

Status: complete for planning on 2026-08-27 under `D-P3.6-PLAN-AUTH`.

Machine-readable source ledger:
[`p3-6-research-sources.json`](../../contracts/phase-3/p3-6-research-sources.json).

This was read-only documentation research. It downloaded no artifact, package,
driver, model, dataset, or container and executed no runtime, hardware test,
media path, or deployment action.

## Research Questions

1. Which runtime should remain the portable behavior reference?
2. When is Intel acceleration justified, and how must device choice be bound?
3. When are TensorRT and DeepStream justified instead of a portable adapter?
4. What measured condition could justify Triton?
5. Which scheduling and batching controls are required to preserve latency,
   stream-local state, authorization, and failure isolation?
6. What benchmark and supply-chain evidence is required before a runtime claim?

## Findings

### Portable Reference

[ONNX Runtime's OpenVINO Execution Provider](https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html)
confirms that OpenVINO can be registered behind the existing execution-provider
surface with explicit options. That supports retaining ONNX Runtime CPU as the
behavior reference and treating every accelerator/provider configuration as a
separate evaluated combination.

An ONNX file alone does not identify provider fallback, graph partitioning,
device, precision, thread settings, optimization level, or compiled cache.
Those settings must be in the manifest and parity evidence.

### Intel OpenVINO

[OpenVINO 2026 system requirements](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino/system-requirements.html)
document CPU, Intel GPU, and Intel NPU paths, but device support depends on exact
hardware, operating system, kernel, and drivers. GPU/NPU enablement may require
host changes outside the runtime package. The existing `LAB-LAPTOP-01` profile
is therefore only a possible future feasibility target; its Intel UHD Graphics
620 must not be declared compatible or performant without an authorized,
current exact-device check.

[OpenVINO AUTO](https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/auto-device-selection.html)
selects among compatible devices and defaults to a latency performance hint
unless configured otherwise. AUTO is useful for exploratory feasibility, but
an acceptance benchmark must record the actual selected device and explicit
performance hint. Opaque device selection cannot support a reproducible runtime
claim.

[OpenVINO supported devices](https://docs.openvino.ai/2026/documentation/compatibility-and-support/supported-devices.html)
also describes HETERO and automatic batching. These are separate execution
strategies, not harmless toggles. Each needs its own quality, latency, resource,
and fallback evidence.

### NVIDIA TensorRT And DeepStream

The current [TensorRT support matrix](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/support-matrix.html)
states that serialized engines are not generally portable across operating
systems and, without compatibility modes, GPU architectures. The deployment
unit must bind source model, ONNX/opset or source graph, engine digest, builder
version and flags, precision, timing cache, target GPU architecture, CUDA,
driver, operating system, and container.

[TensorRT precision control](https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/precision-control.html)
also explains why separate builds may not be bit-identical. H-CAM should require
semantic parity and bounded numeric tolerance rather than bitwise identity, and
should preserve build provenance and repeated-build variance evidence.

[DeepStream 9.0 release notes](https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_Release_notes.html)
define a specific supported-platform matrix and known limitations. They also
deprecate the existing Python bindings in favor of pyservicemaker. A future
DeepStream path therefore needs a deliberate integration-language decision and
cannot be introduced as a transparent Python dependency.

[Gst-nvstreammux](https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_plugin_gst-nvstreammux.html)
batches frames from multiple sources and flushes on full batch or timeout. Its
batch size, timeout, scaling, source lifecycle, timestamp behavior, and
per-source metadata directly affect latency and ordering. DeepStream is most
valuable when accelerated decode-to-metadata integration is itself measured;
it is unnecessary for a tensor-only runtime comparison.

### Triton Trigger

[Triton 26.07 release notes](https://docs.nvidia.com/deeplearning/triton-inference-server/release-notes/rel-26-07.html)
show that a release is a coupled container stack containing CUDA, TensorRT,
ONNX Runtime, OpenVINO, and other libraries. Selecting Triton is therefore a
platform and operations decision, not merely choosing an inference API.

[Triton batching](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/batcher.html)
supports bounded queue size, delay, priority, timeout, and ordering controls.
Dynamic batching is intended for stateless models. H-CAM may batch detector
requests only when stream identity and event time remain attached and queue age
stays inside the approved budget. Tracking and temporal rules remain local,
ordered state and must not enter a generic stateless batch.

Triton remains blocked until one of these is measured on approved hardware:

- at least two independently versioned model families need shared serving;
- multiple consumers need a stable network inference boundary;
- one process cannot meet isolation, lifecycle, or utilization requirements;
- model version routing and server-level scheduling provide a measured benefit
  greater than their latency, security, and operational cost.

### Device Scheduling And Isolation

[Kubernetes device plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
advertise integer extended resources that cannot be overcommitted. A scheduler
must treat accelerator capacity as an explicit hard constraint rather than an
ordinary CPU-style soft request.

[NVIDIA MIG management](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/gpu-operator-mig.html)
requires an explicit strategy and can disrupt GPU workloads or reboot nodes
when geometry changes. MIG geometry must be an administrator-managed node
profile outside assignment scheduling.

[NVIDIA GPU time slicing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
does not provide MIG-style memory or fault isolation and does not guarantee
proportional compute. It is unsuitable as a default for latency-sensitive or
security-isolated workloads. A future time-slicing option requires independent
contention, OOM, observability, fairness, and failure-isolation evidence.

The H-CAM scheduler should remain orchestrator-neutral at the domain boundary.
It can publish explicit requirements and accept node capability snapshots;
Kubernetes, a local lab runner, or another orchestrator may implement placement
later without changing assignment semantics.

### Benchmark Method

[MLPerf Inference rules](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc)
bind the system under test, quality requirement, preprocessing and
postprocessing, latency, throughput, and workload scenario. H-CAM is not
claiming MLPerf conformance, but adopts the useful discipline that single
stream, multistream, server, and offline measurements answer different
questions and that performance is invalid without quality evidence.

P3.6 must report two distinct benchmark layers:

- `INFER`: fixed generated tensor/frame inputs through preprocess, inference,
  postprocess, and normalized observation;
- `PIPE`: an explicitly authorized generated decode-to-event pipeline with
  source timing, queueing, tracking, rules, and publication included.

An `INFER` result cannot be reported as camera, decoder, stream, or event
latency. C1/C10/C50 names must include the layer and workload manifest.

### Supply Chain And Reproducibility

The [OCI image manifest specification](https://specs.opencontainers.org/image-spec/manifest/)
supports immutable content-digest binding. Runtime evidence should name image
manifest digests rather than mutable tags.

[SLSA 1.2 provenance](https://slsa.dev/spec/v1.2/provenance) defines verifiable
records of where, when, and how an artifact was produced. A TensorRT engine,
OpenVINO compiled blob, native extension, or container needs source/build
provenance in addition to its checksum.

[CycloneDX SBOM guidance](https://cyclonedx.org/guides/sbom/lifecycle_phases/)
supports software and machine-learning component inventory. The P3.6 evidence
set should cover the source model, compiled derivative, runtime, native
libraries, decoder, container base, and driver-facing packages as one reviewed
deployment unit.

## Planning Conclusions

- Keep ONNX Runtime CPU as the portable behavior reference.
- Evaluate OpenVINO first on an exact owned Intel profile after authorization;
  pin the actual device and explicit performance hint in evidence.
- Evaluate TensorRT/DeepStream only on exact approved NVIDIA hardware after one
  model is promoted and the integrated video-pipeline benefit is testable.
- Introduce Triton only after its explicit multi-model/shared-serving trigger.
- Keep detector batching stateless, bounded, and latency-budgeted; retain
  tracking and temporal rules as ordered stream-local state.
- Separate model-family quality selection from runtime acceleration.
- Treat engine, runtime, driver, OS, hardware, precision, configuration, and
  container as one versioned compatibility unit.
- Require explicit admission, no silent fallback, safe overload behavior,
  immutable evidence, and a tested CPU/source rollback.

These are recommendations for owner decision, not approved runtime choices.

## Unresolved Before Any Execution

- promoted detector champion and fallback after `DET-R0/E1/B1/A1` comparison;
- exact generated workload, model artifacts, preprocessing, postprocessing, and
  numeric parity tolerances;
- exact Intel and/or NVIDIA hardware, OS, firmware, driver, power mode, decoder,
  runtime, provider, precision, and container versions;
- whether a C10/C50-capable owned or authorized lab target exists;
- approved queue-age, latency, throughput, resource, quality, power, cost, and
  recovery gates;
- artifact/dependency/container research authority;
- implementation and runtime-execution authority;
- deployment orchestrator and production target, which remain deferred.

All versions, support matrices, security advisories, licenses, and known issues
must be rechecked immediately before a later artifact or execution gate.
