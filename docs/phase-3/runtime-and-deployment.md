# Runtime And Deployment Strategy

## Decision Posture

H-CAM will use a runtime adapter contract and select deployment runtimes from
measured evidence. Model format portability is valuable, but identical exported
files can produce different performance or numeric behavior across execution
providers. Every approved runtime/model/hardware combination needs its own
evaluation record.

The accountable owner may approve the deployment record without a separate
reviewer. This does not remove security, license, parity, benchmark, rollback,
capacity, or explicit deployment-authorization evidence.

The detailed [P3.6 runtime acceleration and scheduling plan](p3-6-plan.md) and
[owner decision packet](p3-6-decision-packet.md) refine this strategy under
`D-P3.6-PLAN-AUTH`. They are planning-only: no runtime, hardware, artifact,
container, implementation, benchmark, or deployment is currently approved.

## Proposed Runtime Roles

| Role | Proposed candidate | Why it is considered | Decision state |
| --- | --- | --- | --- |
| Portable reference | ONNX Runtime CPU Execution Provider | Reproducible laptop/CI path and execution-provider abstraction | Proposed baseline |
| NVIDIA video pipeline | DeepStream 9.0 | Accelerated decode, batching, inference, tracking, and metadata pipeline | Benchmark candidate |
| Shared NVIDIA serving | Triton Inference Server | Versioned model repositories, model backends, scheduling, dynamic batching, health, and metrics | Benchmark candidate |
| Intel edge/runtime | OpenVINO 2026 | CPU/GPU/NPU support and AUTO/HETERO device modes | Benchmark candidate |
| Experiment/registry | MLflow Model Registry | Versioned model records, aliases, tags, and promotion metadata | Governance candidate |

No candidate is a production commitment. Exact versions must be pinned only
after license, platform, security, reproducibility, and benchmark review.

## Model-To-Runtime Plan

The role-based candidates are defined in `model-portfolio.md`:

| Stage | Model role | Initial runtime | Acceleration path |
| --- | --- | --- | --- |
| Reference | `DET-R0` YOLOX-Tiny | ONNX Runtime CPU | OpenVINO EP only after reference parity |
| Edge challenger | `DET-E1` D-FINE-N | ONNX Runtime CPU evaluation | OpenVINO or TensorRT after artifact and parity approval |
| Balanced | `DET-B1` RF-DETR-S | Approved source path, then verified export | TensorRT/DeepStream only after frozen H-CAM quality evidence |
| Accuracy | `DET-A1` RF-DETR-L | Approved source path, then verified export | Server-class TensorRT/DeepStream if measured benefit justifies cost |
| Tracking | `TRK-R0` ByteTrack | H-CAM stream-local association component | Remains stream-local; no dynamic cross-stream batching |
| OCR | `OCR-L0/L1/D0/G0/G1` | ONNX Runtime/OpenVINO where supported; native Tesseract for Gujarati | Each script/model/runtime combination has separate parity and quality evidence |

This mapping selects an experiment order, not a deployable stack. A candidate
whose export cannot meet parity remains on its approved source runtime or is
rejected; H-CAM will not weaken correctness to force a common format.

## Runtime Adapter Contract

Every adapter must implement the same conceptual operations:

```text
inspect_artifact -> load -> warmup -> infer -> health -> metrics -> unload
```

The adapter declares:

- supported artifact formats, opsets, precisions, and input shapes;
- preprocessing and output tensor contract;
- device, memory, concurrency, and batching constraints;
- deterministic or nondeterministic behavior;
- runtime/library/container versions and security updates;
- readiness, liveness, load, inference, and failure metrics;
- bounded timeout, cancellation, and unload behavior.

Runtime-native tensors are normalized inside the adapter boundary.

## Artifact Rules

- ONNX is the preferred interchange format only when export parity passes.
- A native TensorRT, OpenVINO, or other compiled artifact is tied to its source
  model, runtime version, precision, target architecture, calibration data, and
  build recipe.
- Each artifact has a SHA-256 digest, signature, software/model bill of
  materials, license record, source model, and reproducible build evidence.
- Mutable registry aliases can select a candidate for deployment, but workers
  resolve and record the immutable version before starting.
- Model files are never fetched from arbitrary URLs by a worker.

## Batching And State

Detection can be stateless and may use bounded batching when the measured
latency budget allows it. Tracking and temporal rules are stateful and retain
stream-local ordering; they must not be dynamically batched in a way that
mixes state or reorders frames.

Batch settings are workload-specific. Throughput gains cannot justify
unbounded queue delay, stale events, or hidden frame drops.

## Hardware Profiles

Every benchmark and deployment declares a hardware profile:

- CPU model, core/thread allocation, instruction capabilities, and RAM;
- accelerator vendor/model, memory, driver, runtime, and power mode;
- operating system, kernel, container runtime, and architecture;
- decoder path and number/resolution/codec/frame rate of sources;
- network and storage conditions;
- model, precision, batch, sampling, and tracker settings.

Results without this manifest are not comparable evidence.

## Capacity Tiers

| Tier | Purpose | Minimum workload |
| --- | --- | --- |
| C0 | CI contract and deterministic smoke | prerecorded generated frames, no GPU required |
| C1 | Developer functional path | 1 synthetic stream |
| C10 | Concurrency and backpressure | 10 synthetic streams |
| C50 | Challenge-aligned lab evidence | approximately 50 synchronized synthetic-live streams |
| C-Statewide | Architecture model only | shard, bandwidth, event-rate, GPU, storage, and failure-domain calculations for approximately 80,000 cameras |

C50 does not prove C-Statewide. Statewide claims require workload assumptions,
capacity equations, failure-domain design, staged field evidence, and margin.

## Workload Placement

Placement considers:

- authorization and data residency;
- source reachability and bandwidth;
- required event latency and sampling floor;
- decoder and accelerator capacity;
- model/runtime compatibility;
- failure-domain and maintenance state;
- cost and power budget;
- privacy preference for local processing.

The scheduler must reject or queue an assignment when no node satisfies all
hard constraints. It must not silently place sensitive workloads on a less
restricted node.

## Backpressure Policy

Each assignment declares maximum queue age, sampling target and floor, optional
nodes, and overload action. Metrics expose received frames, sampled frames,
processed frames, skipped stale frames, queue age, model latency, event latency,
and degradation state.

Proposed overload sequence:

1. skip optional enrichment such as OCR when policy allows;
2. reduce detector sampling no lower than the approved floor;
3. discard stale frames before current frames;
4. pause the assignment and report `capacity_exhausted`;
5. require explicit recovery or automatic recovery under a documented policy.

## Deployment Security Baseline

- Run decoder and model workers as non-root with read-only root filesystems.
- Mount only approved immutable artifacts and minimal temporary storage.
- Deny outbound network access unless an exact dependency requires it.
- Use internal authenticated media access; never expose camera credentials.
- Apply CPU, GPU, memory, process, file, response-size, and execution-time
  limits.
- Separate control-plane identity from media and artifact access identity.
- Pin images by digest and scan dependencies and model-serving surfaces.
- Treat GPU drivers and media decoders as security-sensitive platform
  dependencies with patch and rollback procedures.

## Selection Experiments

Model-family selection and runtime selection are two different experiments.
First compare `DET-R0`, `DET-E1`, `DET-B1`, and `DET-A1` through the staged
portfolio funnel on frozen H-CAM inputs. Then compare the promoted model against
accelerated runtimes using the same model artifact or a documented compiled
derivative. Selection uses slice quality, calibration, decode-to-event latency,
throughput, memory, power where available, recovery behavior, observability,
platform fit, license, operational complexity, and total cost.

No hidden weighted score may override a hard quality, security, privacy,
license, stability, or slice gate. The model champion/fallback and runtime
choice receive separate ADRs; architecture diagrams and upstream benchmark
tables are not H-CAM selection evidence.
