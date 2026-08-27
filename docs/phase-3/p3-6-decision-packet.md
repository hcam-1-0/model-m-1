# P3.6 Owner Decision Packet

Status: owner selections pending. Planning and primary-source research are
complete under `D-P3.6-PLAN-AUTH`; implementation remains unauthorized.

Plan: [P3.6 runtime acceleration and scheduling](p3-6-plan.md).

Research: [P3.6 primary-source record](p3-6-research-record.md).

## Decision Rules

- Choose exactly one option for each of `D-P3.6-001` through `D-P3.6-005`.
- Option A is recommended for each decision because the options form one
  conservative, measurable baseline.
- A decision selects architecture policy only. It does not approve a package,
  model, runtime, hardware test, container, implementation, or deployment.
- Exact artifacts, versions, hardware, paths, actions, and evidence require a
  later manifest-bound gate.
- The owner may approve without a separate reviewer under DR-0026, but all
  technical, security, license, privacy, evidence, and rollback gates remain.

## D-P3.6-001: Runtime Portfolio And Activation Triggers

### A. Staged Evidence-Driven Portfolio (Recommended)

Keep ONNX Runtime CPU as the behavior reference. Evaluate ONNX Runtime with
OpenVINO first on exact owned Intel hardware. Evaluate TensorRT and DeepStream
only on exact approved NVIDIA hardware after a model champion is frozen.
Evaluate Triton only after a measured multi-model, multi-consumer, isolation,
or utilization trigger.

Benefits:

- preserves one portable rollback path;
- separates model quality from runtime optimization;
- avoids operating Triton or DeepStream before their complexity is justified;
- supports Intel laptop/edge and later NVIDIA tiers without forcing one stack;
- makes every provider, device, precision, and compiled artifact independently
  reviewable.

Costs and limits:

- more than one adapter and evidence lane may eventually exist;
- a model may fail parity on one accelerator and remain source-runtime only;
- exact runtime versions stay unresolved until hardware is selected.

### B. OpenVINO-Only Standard

Use OpenVINO as the sole accelerator target and defer all NVIDIA-specific
runtimes.

Benefits: smaller runtime portfolio and strong Intel focus.

Risks: may not serve future NVIDIA video-decode/GPU hardware efficiently;
creates pressure to force unsupported exports or assume device portability.

### C. NVIDIA DeepStream/TensorRT Standard

Select NVIDIA as the only accelerated production direction and retain CPU only
for CI/reference.

Benefits: integrated video acceleration and a mature NVIDIA deployment stack.

Risks: no current approved NVIDIA hardware; tighter driver/container coupling;
engine portability limits; higher platform and procurement commitment.

### D. Triton-First Universal Serving

Place all model execution behind Triton from the beginning.

Benefits: central model serving, versioning, scheduling, batching, and metrics.

Risks: premature network/container/control-plane complexity; added latency and
failure modes; does not replace decode, stream ordering, tracking, or H-CAM
policy; unjustified for the current single accepted detector reference.

Recommended selection: `D-P3.6-001: A`.

## D-P3.6-002: Placement, Admission, Batching And Backpressure

### A. Typed Fail-Closed Scheduler With Node-Local Bounded Queues (Recommended)

Use immutable node capability snapshots, hard authorization/compatibility/
capacity constraints, deterministic soft ranking, leased placements,
reconciliation, explicit reservations, per-stream fairness, stateless detector
batching only, freshness deadlines, and a documented degradation ladder.

Benefits:

- no unsupported or unauthorized silent placement;
- domain contract remains independent of Kubernetes or another orchestrator;
- tracking and temporal state retain stream-local ordering;
- queue age and skipped work are visible;
- scheduler decisions are explainable and replayable.

Costs and limits:

- requires an inventory agent, reconciliation state, and capacity model later;
- strict admission may leave work pending rather than maximize nominal use;
- priority and fairness policies still need measured numeric values.

### B. Kubernetes-Native Placement Only

Encode all behavior directly through node labels, affinities, requests, limits,
and device plugins.

Benefits: fewer H-CAM-specific scheduling components if Kubernetes is already
the fixed deployment platform.

Risks: Kubernetes is not yet approved; generic resource placement does not
express all H-CAM data, model, freshness, fallback, and lineage rules; makes
local/laptop and non-Kubernetes deployments harder.

### C. Runtime-Managed Auto Placement

Allow OpenVINO AUTO, Triton, DeepStream, or the provider to select device,
batching, and concurrency.

Benefits: less custom scheduling logic and potentially easier tuning.

Risks: opaque placement and fallback, weak reproducibility, inconsistent policy
enforcement, difficult capacity reservation, and runtime-specific semantics.

### D. Static Per-Node Configuration

Manually assign streams and models to fixed workers with no scheduler.

Benefits: simplest first implementation.

Risks: poor recovery and capacity visibility, configuration drift, manual
errors, no scalable admission, and weak C10/C50 evidence.

Recommended selection: `D-P3.6-002: A`.

## D-P3.6-003: Parity, Benchmark And Claim Policy

### A. Two-Funnel Conjunctive Evidence With Layered C1/C10/C50 (Recommended)

Select the model family first, then compare the exact promoted model across
runtimes. Require normalized-output and downstream parity, quality retention,
no hidden fallback, exact manifests, repeated runs, cold/warm/burst/steady/
failure scenarios, and separate `CONTRACT`, `INFER`, and `PIPE` claims.

Use C1/C10/C50 only with explicit generated workload and exact hardware. Report
p50/p95/p99 latency, throughput, queue/freshness, resource, quality, recovery,
power where available, cost, and operational complexity. Numeric thresholds are
owner-approved after a measured baseline, not invented during planning.

Benefits:

- prevents a faster but behaviorally weaker runtime from winning;
- prevents tensor-only measurements from becoming camera/stream claims;
- makes results reproducible and limits C50 overclaiming;
- preserves slice and failure evidence instead of a single average score.

Costs and limits:

- requires more fixtures, manifests, repetitions, and analysis;
- C10/C50 remain blocked until suitable hardware and workloads exist;
- no immediate percentage improvement can be promised.

### B. Throughput-First Selection

Choose the runtime with the highest inferences per second after a basic smoke
parity check.

Benefits: fast and simple comparison.

Risks: can hide tail latency, queue staleness, quality drift, contention,
recovery, power, and operational cost; unsuitable for H-CAM acceptance.

### C. Latency-Only Edge Selection

Optimize single-stream p95/p99 latency and defer concurrency evidence.

Benefits: focused edge responsiveness.

Risks: does not prove multi-stream capacity, fairness, overload, or integrated
decode-to-event performance.

### D. Upstream/Vendor Benchmark Selection

Choose from published model and runtime tables without H-CAM execution.

Benefits: no local benchmark effort.

Risks: upstream hardware, data, preprocessing, versions, and scenarios differ;
cannot establish H-CAM quality, latency, compatibility, or cost.

Recommended selection: `D-P3.6-003: A`.

## D-P3.6-004: Packaging, Security, Degradation And Rollback

### A. Immutable Compatibility Bundle With CPU/Source Rollback (Recommended)

Bind source model, export, compiled derivative, runtime/provider, precision,
configuration, hardware, firmware, driver, OS, decoder, container manifest,
SBOM, provenance, license, vulnerability status, benchmark evidence, and
rollback tuple. Default execution off. Deny arbitrary model/plugin URLs and
outbound network. Require non-root/read-only/resource-bounded packaging where a
container is later selected.

Use explicit degradation: remove optional work, reduce sampling within the
approved floor, reject stale work, use only an approved compatible fallback,
roll back to the verified tuple, or pause. Every transition is audited and
tested under load.

Benefits:

- reproducible and reviewable deployment unit;
- protects against engine portability and driver/runtime mismatch;
- supports rapid suspension and precise rollback;
- makes degradation visible rather than silently reducing correctness.

Costs and limits:

- more build, SBOM, signature, scan, registry, and retention evidence;
- CPU fallback may not meet every future capacity target and may require pause;
- exact signing and registry technologies remain deferred.

### B. Runtime And Model Digests Only

Pin model and runtime package hashes but leave driver, hardware, configuration,
and container outside the promotion record.

Benefits: smaller evidence package.

Risks: insufficient for compiled-engine portability, native dependencies,
device behavior, reproducibility, and vulnerability response.

### C. Mutable Environment Aliases With Automatic Roll Forward

Use tags/aliases for latest approved runtime and automatically update workers.

Benefits: simpler patch rollout.

Risks: running state becomes difficult to reproduce; update can change behavior
or compatibility without complete parity and rollback evidence.

### D. No Compiled Artifact Retention

Build runtime-specific artifacts on every worker startup from the source model.

Benefits: avoids storing engine binaries.

Risks: slow and variable startup, nondeterministic tactic selection, build tools
on workers, larger attack surface, and poor rollback reproducibility.

Recommended selection: `D-P3.6-004: A`.

## D-P3.6-005: Hardware Evidence Strategy

### A. Two-Gate Owned-Lab Then Capacity-Target Strategy (Recommended)

After separate execution authority, use `LAB-LAPTOP-01` only for CPU reference
and exact Intel/OpenVINO feasibility. Separately approve a declared owned or
authorized capacity target for C10/C50 and any NVIDIA evaluation. Do not
extrapolate laptop results to edge appliances, servers, or statewide capacity.

Benefits:

- can obtain low-cost local parity/harness evidence first;
- separates feasibility from procurement and scale claims;
- allows Intel and NVIDIA paths to be compared only where hardware exists;
- avoids selecting a vendor before workload evidence.

Costs and limits:

- needs a later hardware target or approved lab for C10/C50;
- results from two profiles are not directly comparable without workload and
  configuration normalization;
- no GPU acceleration is guaranteed on the current laptop.

### B. Existing Laptop Only

Limit P3.6 to `LAB-LAPTOP-01` and its currently recorded hardware.

Benefits: no new hardware dependency.

Risks: cannot support NVIDIA, production, or credible C10/C50 claims; Intel GPU
support and benefit are unverified; thermal limits distort long runs.

### C. NVIDIA Capacity Target First

Defer laptop acceleration and require an exact NVIDIA server/edge profile for
all runtime evidence.

Benefits: directly targets TensorRT/DeepStream and larger concurrency.

Risks: hardware/procurement dependency and vendor commitment before local
parity tooling; no current approved target.

### D. Research-Only Deferral

Complete policy documents but defer all hardware selection and execution.

Benefits: zero current hardware/runtime risk.

Risks: P3.6 cannot progress beyond planning or produce measured acceleration.

Recommended selection: `D-P3.6-005: A`.

## Owner Decision Record

Submit choices in this exact form:

```text
D-P3.6-001: A|B|C|D
D-P3.6-002: A|B|C|D
D-P3.6-003: A|B|C|D
D-P3.6-004: A|B|C|D
D-P3.6-005: A|B|C|D
```

Owner choices will authorize the technical planning baseline only. After they
are recorded, the next action is to prepare exact artifact, hardware, runtime,
workload, path, and execution proposals. Do not submit `D-P3.6-START` until
those exact manifests and remaining blockers have been reviewed.

## Continuing Non-Authorization

No choice in this packet authorizes downloads, dependencies, model artifacts,
datasets, drivers, containers, runtime execution, GPU/hardware tests, media,
cameras, data, implementation, deployment, remote Git, P3.7, or later work.
