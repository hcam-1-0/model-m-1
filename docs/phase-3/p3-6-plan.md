# P3.6 Runtime Acceleration And Scheduling Plan

Status: planning and primary-source research complete under
`D-P3.6-PLAN-AUTH`; `D-P3.6-001` through `D-P3.6-005` are owner accepted.
Model promotion, exact capability manifests, artifact authority, execution
authority, implementation, and acceptance remain pending. A later
`D-P3.6-START` statement is recorded as non-effective intent because those
prerequisites are incomplete.

Planning authorization:
[P3.6 planning authorization](p3-6-planning-authorization.md).

Research basis:
[P3.6 primary-source research](p3-6-research-record.md).

Accepted architecture decisions:
[P3.6 owner technical decisions](p3-6-owner-decisions.md).

Dynamic hardware policy:
[P3.6 capability profiles](p3-6-capability-profiles.md).

Start intent and prerequisite sequence:
[P3.6 start intent](p3-6-start-intent.md) and
[P3.6 unblock plan](p3-6-unblock-plan.md).

Entry gates:
[`p3-6-entry-gates.json`](../../contracts/phase-3/p3-6-entry-gates.json).

Accepted dependency: P3.5 under `D-P3.5-W10-ACCEPTANCE` for immutable package
digest `4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`.

## Objective

Design a reproducible acceleration and scheduling subsystem that can place an
approved analytics pipeline only on compatible, authorized capacity; improve
measured performance without silently changing model behavior; remain bounded
under overload; and roll back to a verified reference path.

P3.6 is not simply a GPU milestone. Its output is the contract and evidence
needed to answer:

- which exact model/runtime/hardware combinations are acceptable;
- where a workload may run and why;
- how queueing, batching, failures, and contention affect quality and latency;
- how H-CAM prevents unsupported placement and silent fallback;
- how a bad runtime or compiled artifact is suspended and rolled back.

## Planning Boundary

The current effective authorization permits this plan and research only. The
received `D-P3.6-START` statement is not bound to exact actions, artifacts,
machines, paths, workloads, network policy, or a package digest and cannot
bypass blocked G1, G2, or G4. Future sections describe conditional work
packages; they do not authorize their execution.

No current P3.6 result claims acceleration, parity, throughput, C1/C10/C50
capacity, camera performance, GPU support, OpenVINO support on the laptop,
TensorRT/DeepStream support, Triton need, container readiness, or deployment.

## Inherited Foundation

P3.6 reuses rather than rewrites:

- the accepted P3.2 `DET-R0` ONNX Runtime CPU generated-input reference;
- the P3.1 role-based `DET-R0`, `DET-E1`, `DET-B1`, and `DET-A1` portfolio;
- accepted P3.3 anonymous stream-local tracking and epoch isolation;
- accepted P3.4 deterministic event-time rules, resource ceilings, and outbox;
- accepted P3.5 generated-only, zero-retention, default-off ANPR package;
- model-independent runtime adapter operations
  `inspect_artifact -> load -> warmup -> infer -> health -> metrics -> unload`;
- department scope, RBAC, audit, immutable revisions, ETags, assignment state,
  safe reason codes, low-cardinality metrics, and transactional events;
- existing C0/C1/C10/C50 workload terminology and deployment prohibitions.

The authorized sanitized `LAB-LAPTOP-01` inventory records Windows 10 Pro
64-bit build 19045, an Intel Core i5-8365U with four cores/eight logical
processors, 8 GiB RAM, Intel UHD Graphics 620, and no observed discrete NVIDIA
accelerator. Every fixed volume has less than seven percent free space. This
supports portable-profile planning only. A later authorization may permit an
OpenVINO feasibility run, but the current inventory cannot establish provider
support, performance, GPU, C1/C10/C50, production, or procurement claims.

## Hard Entry Gates

| Gate | Requirement | Current state |
| --- | --- | --- |
| `P36-G0` | Accepted P3.5 and explicit P3.6 planning authority | Passed |
| `P36-G1` | Frozen `DET-R0/E1/B1/A1` comparison and promoted champion/fallback | Blocked |
| `P36-G2` | Exact hardware/OS/driver/runtime/precision/workload profiles | Blocked; current-laptop inventory complete, profiles unresolved |
| `P36-G3` | Owner decisions `D-P3.6-001` through `D-P3.6-005` | Passed |
| `P36-G4` | Exact digest-bound artifact/dependency/container research authority | Blocked |
| `P36-G5` | Exact implementation and runtime-execution authority | Blocked; broad start intent received but non-effective |

No later gate can be inferred from approval of an earlier gate.

## Accepted Architecture Baseline

The owner selected the staged runtime portfolio, typed fail-closed scheduler,
two-funnel evidence policy, immutable compatibility bundle, and two-gate
hardware strategy. Three bounded extensions are part of that baseline:

- Kubernetes may execute admitted placements, but H-CAM remains the authority
  for assignment authorization, compatibility, capacity, freshness, lineage,
  degradation, and rollback.
- Runtime-managed placement may advise only among devices/providers/resources
  already admitted by H-CAM. It cannot silently select an unapproved provider,
  precision, model, or fallback.
- Balanced, Throughput, and Latency modes may rank eligible profiles and shape
  future dashboard presentation. They cannot bypass parity, security, quality,
  fairness, lineage, freshness, or claim-integrity gates.

The same application and contracts must work across a conservative CPU-only
profile and stronger validated accelerated profiles. Dynamic behavior changes
resource policy and admitted load, not product correctness or safety.

## Target Architecture

```text
Approved assignment revision
          |
          v
Capability profile + placement admission
  - department/data authorization
  - model/runtime compatibility
  - validated profile revision
  - node health and maintenance
  - reserved CPU/RAM/device/decoder
  - queue-age and latency budget
          |
          v
Leased workload placement --------------------+
          |                                   |
          v                                   v
Node-local bounded queue              Reconciler / audit
  - freshness deadline                  - desired vs actual
  - priority class                      - lease expiry
  - batch eligibility                   - drift / suspension
  - overload action                     - safe reason code
          |
          v
Pinned runtime adapter
  - ONNX Runtime CPU reference
  - OpenVINO candidate on exact Intel profile
  - TensorRT/DeepStream candidate on exact NVIDIA profile
  - Triton only after measured trigger
          |
          v
Normalized observations -> ordered stream-local tracking/rules -> outbox
          |
          +--> low-cardinality health, latency, resource and degradation metrics
```

The control plane decides whether an assignment and capability profile are
eligible and records why. The node-local data plane enforces queue and resource
bounds. Kubernetes or another orchestrator may place processes or containers
later, but it cannot override H-CAM authorization, compatibility, freshness,
lineage, or rollback constraints. Runtime AUTO placement is advisory only
inside the exact admitted device/provider set.

## Runtime Portfolio

| Runtime role | Candidate | Earliest valid purpose | Activation trigger | Required fallback |
| --- | --- | --- | --- | --- |
| Behavior reference | ONNX Runtime CPU | Correctness, parity, deterministic generated baseline | Existing accepted `DET-R0`; promoted models require separate artifacts | Source/CPU reference itself |
| Intel accelerator | ONNX Runtime OpenVINO EP first; native OpenVINO only if justified | Exact owned Intel CPU/GPU/NPU feasibility | Approved device profile and measured benefit with parity | ONNX Runtime CPU |
| NVIDIA model engine | TensorRT | Exact approved NVIDIA detector acceleration | Promoted model, compatible hardware, reproducible engine build | Approved source/ONNX runtime |
| NVIDIA video pipeline | DeepStream | Integrated decode/batch/infer/metadata performance | Decode-to-event workload and measured integration benefit | Non-DeepStream pipeline |
| Shared serving | Triton | Multi-model or multi-consumer serving | Explicit workload trigger and measured operational benefit | In-process approved adapter |

No runtime may silently fall back to another provider or precision in accepted
evidence. A fallback is an explicit deployment transition with audit and health
state, not an unrecorded provider behavior.

## Dynamic Capability Profiles

P3.6 uses capability-based profiles rather than separate product builds.

| Profile | Intended use | Resource posture | Evidence boundary |
| --- | --- | --- | --- |
| `portable_cpu` | Current laptop and CPU/CI reference | Conservative concurrency, batch, sampling, preview, queue, and optional-enrichment policy | C1 correctness and exact small-machine evidence only until measured |
| `local_accelerated` | Stronger owned/authorized laptop | Higher settings only inside an exact validated provider/device bundle | Exact machine and workload only |
| `capacity_target` | Declared lab/server or cluster target | Approved C10/C50 reservations and optional Kubernetes backend | Signed exact-hardware/workload evidence; no extrapolation |

All profiles preserve the same domain, API, event, taxonomy, authorization,
security, lineage, audit, privacy, retention, quality, failure, and rollback
contracts. Only these dimensions may adapt after exact validation:

- worker concurrency and stateless detector batch size;
- sampling within an approved minimum floor;
- optional enrichment and preview rate/quality;
- bounded queue, reservation, in-flight, and workload-admission values;
- CPU, memory, accelerator, decoder, thermal, and power budgets.

Automatic selection considers only fresh immutable node inventory and exact
approved compatibility bundles. If the requested profile is unavailable,
H-CAM may use a separately approved lower profile when its capacity/freshness
policy passes; otherwise it pauses with a safe reason. Unknown hardware or
unvalidated runtime state never creates a profile automatically.

### Future Control Surface

A later authorized dashboard package should expose:

- hardware: `Auto`, `Portable CPU`, `Local Accelerated`;
- objective: `Balanced`, `Throughput`, `Latency`;
- load: `Conservative`, `Standard`, `Maximum Validated`.

The controls select approved policy revisions only. The UI must show the active
profile revision, compatibility-bundle digest, objective/load mode, evidence
freshness, fallback/degradation state, and safe rejection reason. This is a
future requirement, not current dashboard implementation authority.

### Exact Manifest Requirement

Before `P36-G2` can pass, every proposed profile revision must bind the machine,
trust zone, OS/kernel/architecture, CPU/RAM, accelerator/firmware, driver and
compute stack, runtime/provider/precision, decoder limits, artifact/configuration
digests, concurrency/batch/sampling/queue/freshness bounds, generated workload,
parity/quality/performance/recovery evidence, SBOM/provenance/license/security,
observation expiry, approver, and rollback tuple. Placeholder or self-reported
capability alone is insufficient.

## Model Selection Before Acceleration

P3.6 uses two non-interchangeable funnels.

### Funnel A: Model Family

Compare `DET-R0`, `DET-E1`, `DET-B1`, and `DET-A1` on frozen generated or later
explicitly authorized evaluation inputs. Each candidate keeps its intended
resolution and source runtime. Select a champion and fallback using quality,
calibration, per-class/slice behavior, resource use, license, artifact lineage,
stability, and downstream tracking/rule effects.

The current exact `DET-R0` artifact is a reference, not an automatic champion.
The other candidates remain blocked until exact artifacts and data gates exist.

### Funnel B: Runtime

Only the promoted model enters acceleration comparison. Use identical frozen
inputs, preprocessing, postprocessing, taxonomy, and output matching. A
compiled derivative must bind back to the source artifact and build recipe.

Runtime improvement cannot compensate for a failed quality or lineage gate.

## Node Capability Model

Every node inventory observation should be immutable and time-bounded. The
proposed record includes:

- node ID, trust zone, department/purpose eligibility, site, and failure domain;
- operating system, architecture, kernel, container runtime, and node-agent
  versions;
- CPU model/features, allocatable cores, RAM, huge pages where relevant, and
  thermal/power policy;
- accelerator vendor/model, stable device identity, memory, supported
  precisions, partition/share mode, health, and allocatable units;
- firmware, driver, CUDA/OpenCL/Level Zero/NPU stack, runtime/provider, and
  compatibility-set digest;
- decoder types, codec/profile/resolution/session limits, and measured reserve;
- model/runtime/precision allowlist and immutable artifact cache inventory;
- current reservations, queue pressure, maintenance/drain state, heartbeat,
  clock health, and inventory expiry;
- SBOM/provenance/vulnerability status and active deployment revision.

Self-reported capability is not sufficient for production trust. A later
attestation design must bind the node agent, inventory, and deployment policy.

## Placement And Admission

### Hard Constraints

An assignment is rejected or remains pending unless all required values match:

- department, purpose, data class, residency, and network zone;
- approved model, runtime, precision, configuration, and artifact digests;
- compatible OS, architecture, driver, device, decoder, and runtime set;
- minimum reserved CPU, RAM, accelerator memory, decoder capacity, and local
  storage without overcommit;
- source reachability and permitted data path when such access is authorized;
- queue-age, event-latency, sampling-floor, and failure-domain policy;
- healthy, fresh node inventory with no maintenance, drain, or suspension;
- security, license, SBOM, provenance, and vulnerability gates.

### Soft Ranking

Among eligible nodes, ranking may consider locality, expected latency, current
headroom, power, cost, cache warmth, and failure-domain balance. A soft score
cannot override a hard constraint.

### Lease And Reconciliation

- placements use a bounded lease and monotonic assignment revision;
- the node accepts only the latest authorized revision and exact artifact set;
- expired heartbeat or lease stops new work and enters a declared degradation
  state;
- reconciliation compares desired, admitted, loaded, and healthy state;
- duplicate start, stale revision, wrong artifact, or incompatible node fails
  closed with a safe reason code;
- recovery is idempotent and records whether state or work was lost.

## Queues, Batching And Backpressure

Each assignment declares:

- input freshness deadline and maximum queue length/bytes;
- detector sampling target and approved minimum;
- permitted stateless batch sizes and maximum batch-formation delay;
- maximum in-flight requests and per-stream fairness limit;
- optional enrichment stages and their removal order;
- overload, dependency-failure, and recovery actions;
- whether reordering is forbidden and how event time is preserved.

Detector batching may combine inputs only after preserving stream ID, source
event time, frame sequence, assignment revision, and lineage. The batcher
discards stale work before current work and records every skip. It must not
batch tracking state, temporal rules, ANPR consensus, or any stage whose state
would cross stream or tracker epoch.

Proposed overload order:

1. stop accepting work above the bounded queue;
2. remove approved optional enrichment;
3. reduce detector sampling no lower than the approved floor;
4. discard stale queued inputs with explicit counters and reason codes;
5. route to an explicitly approved fallback only if capacity and parity gates
   pass for that exact placement;
6. pause the assignment as `capacity_exhausted` rather than process stale data.

The scheduler must prevent one stream, department, model, or retry loop from
consuming all capacity. Fairness policy and priority classes require owner
approval before implementation.

## Parity Contract

Parity compares normalized observations, not runtime-native tensors alone.
For every input it records:

- class IDs, matched/unmatched detections, box geometry, confidence, and order;
- pre/postprocessing and numeric dtype;
- provider partition/fallback information where available;
- deterministic run and repeated-build variance;
- downstream tracker/rule deltas on matched generated sequences;
- slice, abstention, failure, timeout, and malformed-output changes.

Required gates are conjunctive:

- no schema, lineage, bounds, prohibited-data, or taxonomy difference;
- no unsupported class loss or new class outside the frozen taxonomy;
- owner-approved count, IoU, confidence, aggregate quality, calibration, and
  downstream tolerances;
- no hidden provider fallback or precision change;
- reproducible evidence across the approved repetition count;
- safe failure on unsupported operators, device loss, OOM, timeout, or corrupt
  compiled artifact.

Numeric tolerances remain unapproved. P3.6 planning does not invent them.

## Benchmark Matrix

### Evidence Layers

| Layer | Included path | Valid claim |
| --- | --- | --- |
| `CONTRACT` | Generated metadata and deterministic adapter doubles | API/state correctness only |
| `INFER` | Generated in-memory input through preprocess, model, postprocess, normalization | Exact model/runtime inference behavior |
| `PIPE` | Explicitly authorized generated source through decode, analytics, tracking/rules, outbox | Decode-to-event behavior for that workload |

No layer may be relabeled as another.

### Capacity Tiers

| Tier | Required scenarios | Minimum purpose |
| --- | --- | --- |
| C1 | steady, burst, cold load, warm load, dependency loss | single-assignment latency and correctness |
| C10 | mixed streams, fairness, bounded queue, one worker loss | concurrency and backpressure |
| C50 | mixed workload, restart, drain, capacity loss, long soak | challenge-aligned lab evidence only |

C50 requires a separately approved target capable of the workload. It does not
prove statewide capacity or production readiness.

### Metrics

- p50/p95/p99 preprocess, queue, batch wait, infer, postprocess, track, rule,
  publish, and total latency where included;
- throughput, effective frames per second, freshness, queue age, batch-size
  distribution, accepted/rejected/skipped/dropped work, and fairness;
- CPU, RAM, accelerator utilization/memory, decoder sessions, network, disk,
  temperature, throttling, and power where the exact target exposes them;
- load, compile, warmup, steady-state, unload, restart, failover, and rollback
  time;
- quality/parity, calibration, tracking/rule deltas, abstention, and safe
  failure counts;
- image/container/artifact size, startup cost, operator complexity, support
  lifecycle, license, and estimated cost under declared assumptions.

### Manifest

Every result binds run ID, UTC time, operator, clean source commit, exact input
manifest and hashes, model/source/compiled artifact, runtime/provider,
precision, configuration, hardware, firmware, driver, OS, container, decoder,
stream shape, duration, warmup, repetitions, random seeds, background load,
power mode, raw results, failures, and comparison baseline.

H-CAM may borrow benchmark discipline from MLPerf but must not use the MLPerf
name for results that do not follow its formal rules.

## Security And Supply Chain

- exact HTTPS source identity and digest before any future acquisition;
- quarantine, no redirects/proxies, bounded files, passive inspection,
  malware scan, license review, and explicit extraction/loading gate;
- source-model-to-export-to-engine provenance and reproducible build recipe;
- SBOM for model, runtime, native libraries, decoder, plugins, container base,
  and driver-facing packages;
- immutable container manifest digest, non-root user, read-only root filesystem,
  dropped capabilities, seccomp, resource limits, and no network by default;
- no worker-side arbitrary model URL, plugin path, code execution, shell, or
  mutable runtime registry alias;
- exact driver/runtime compatibility and security-advisory review;
- hostile model, malformed tensor, oversized output, plugin, decoder, OOM,
  timeout, cancellation, and device-reset tests in a later isolated lab;
- signed evidence manifests and auditable promotion/suspension/rollback.

No container is required by the domain design. A future container path is an
independently reviewed deployment package, not a prerequisite for planning.

## Observability

Low-cardinality metrics should expose:

- eligible, admitted, pending, rejected, running, degraded, and suspended
  assignments;
- fresh/stale node inventories and lease recovery;
- queue depth/age, batch wait/size, sampling state, skip/drop/reject counts;
- runtime load/infer/unload outcomes and safe failure reasons;
- latency, throughput, utilization, memory, throttling, and health buckets;
- parity failures, artifact mismatch, provider fallback, and rollback;
- scheduler reconciliation duration and placement churn.

Camera IDs, stream IDs, node IDs, users, model URLs, artifact paths, hardware
serials, plate text, and other high-cardinality or sensitive values are not
metric labels. Detailed identifiers belong only in scoped audit records.

Proposed alerts cover no eligible capacity, stale inventory, queue-age budget,
repeated OOM/device reset, parity regression, runtime crash loop, artifact
mismatch, driver/runtime incompatibility, assignment churn, and rollback
failure.

## Degradation And Rollback

The minimum degradation ladder is:

1. remove approved optional enrichment;
2. reduce sampling within the approved floor;
3. reject stale or excess work;
4. move only to an explicitly approved compatible placement;
5. roll back to the exact verified runtime/artifact/configuration tuple;
6. use the verified CPU/source fallback when its capacity and latency policy
   permit;
7. otherwise pause and expose `capacity_exhausted` or the exact safe reason.

Rollback must not silently change the model family, taxonomy, precision,
sampling floor, data zone, department, or retention policy. It is tested under
load and records activation time, lost/skipped work, state reset, tracker epoch,
and recovery evidence.

## Future Work Packages

These packages are ordered proposals, not current implementation authority.

| Package | Purpose | Required input | Exit evidence |
| --- | --- | --- | --- |
| `P36-W0` | Planning, primary research, and owner architecture choices | `D-P3.6-PLAN-AUTH` | Complete; decisions and dynamic profile policy recorded |
| `P36-W1` | Model-family promotion | Exact approved `DET-R0/E1/B1/A1` artifacts and data | Champion/fallback ADR and quality evidence |
| `P36-W2` | Runtime/node/profile/scheduler contracts | Approved decisions and exact proposed manifests | Schemas, negative tests, no runtime activation |
| `P36-W3` | Intel feasibility | Exact owned Intel profile and OpenVINO authority | CPU/OpenVINO parity, compatibility, performance, rollback |
| `P36-W4` | NVIDIA feasibility | Exact owned/authorized NVIDIA profile | TensorRT and optional DeepStream parity/performance/security |
| `P36-W5` | Triton trigger evaluation | Measured shared-serving need | Accept/reject ADR, operational-cost evidence |
| `P36-W6` | Placement, admission, and optional Kubernetes execution adapter | Approved node profiles and capacity policy | Deterministic placement, leases, isolation, backend parity, fail-closed tests |
| `P36-W7` | Bounded queues and batching | Approved latency/sampling/fairness gates | C1/C10 backpressure and state-ordering evidence |
| `P36-W8` | C1/C10/C50 benchmark and objective views | Approved generated workloads and hardware | Signed manifests and reproducible Balanced/Throughput/Latency reports |
| `P36-W9` | Supply chain and resilience | Exact deployment tuple | SBOM, provenance, scans, fault/rollback evidence |
| `P36-W10` | Selection and acceptance | All hard gates passed | Runtime ADR, pinned package, limitations, owner acceptance |

Each executable package needs an exact authorization naming its actions,
artifacts, paths, network policy, hardware, data source, and outputs.

## Testing Strategy For Later Authorization

- contract bounds, canonicalization, compatibility, redaction, and hostile
  values;
- deterministic placement for identical inventory and assignment snapshots;
- department, data-zone, runtime, device, precision, artifact, and capacity
  rejection cases;
- stale inventory, expired lease, duplicate assignment, stale revision,
  maintenance, drain, node loss, and split-brain reconciliation;
- queue byte/count/age bounds, fairness, cancellation, overload, retry, and
  no-unbounded-memory tests;
- reference/accelerator parity, repeated build, fallback detection, malformed
  outputs, OOM, timeout, and device reset;
- C1/C10/C50 generated workloads with cold/warm/burst/steady/soak/failure
  scenarios on exact hardware;
- immutable package, SBOM, provenance, vulnerability, signature, and rollback
  verification;
- at least 90% branch coverage for new deterministic application logic plus
  PostgreSQL concurrency and migration evidence if persistence is introduced.

CI remains CPU-only, generated-only, deterministic, offline, and default-off.
GPU/container/hardware tests remain separate opt-in lab jobs.

## Risks And Controls

| Risk | Control |
| --- | --- |
| Runtime optimization changes detections | normalized parity and downstream gates |
| Engine works only on builder machine | exact compatibility tuple and reproducible build |
| AUTO or provider silently falls back | provider/device telemetry and acceptance rejection |
| Batching improves throughput but breaks freshness | explicit queue delay, age budget, stale-first discard |
| One workload monopolizes accelerator | reservations, fairness, bounded in-flight work |
| GPU sharing weakens isolation | default exclusive/MIG evidence; time slicing separately gated |
| Driver/container stack becomes vulnerable | pinned versions, SBOM, advisory review, suspension |
| C50 result is treated as statewide proof | explicit claim taxonomy and capacity-model separation |
| Scheduler moves restricted work | authorization/residency as hard constraints |
| Rollback hides quality or state loss | explicit tuple, audit, epoch reset, loss statement |

## Exit Criteria

P3.6 can be accepted only when:

1. the model champion and fallback have approved quality evidence;
2. runtime, hardware, driver, precision, artifact, configuration, workload, and
   package tuples are immutable and reviewed;
3. reference/accelerator parity and downstream behavior pass approved gates;
4. placement, admission, leases, queues, batching, backpressure, and fairness
   fail closed under deterministic and concurrent tests;
5. C1/C10/C50 claims are supported by signed exact-hardware manifests or are
   explicitly narrowed;
6. security, licenses, SBOM, provenance, vulnerabilities, observability,
   degradation, recovery, and rollback evidence pass;
7. the runtime ADR records cost, complexity, known limits, rejected candidates,
   support lifecycle, and fallback;
8. an exact package digest and source commit are accepted by `mayank-admin`.

P3.6 acceptance would still not authorize cameras, real media, Government or
private data, operational alerts, deployment, P3.7, or later work unless an
independent decision explicitly grants that scope.
