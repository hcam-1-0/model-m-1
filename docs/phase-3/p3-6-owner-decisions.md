# P3.6 Owner Technical Decisions

Status: `D-P3.6-001` through `D-P3.6-005` accepted by `mayank-admin` on
2026-08-29. A `D-P3.6-START` statement was subsequently received but is
non-effective pending exact manifest-bound authorization.

Machine-readable record:
[`p3-6-owner-decisions.json`](../../contracts/phase-3/p3-6-owner-decisions.json).

Capability-profile policy:
[`p3-6-capability-profile-policy.json`](../../contracts/phase-3/p3-6-capability-profile-policy.json).

Start-intent record: [P3.6 start intent](p3-6-start-intent.md).

## Decision Summary

| Decision | Accepted baseline | Effect |
| --- | --- | --- |
| `D-P3.6-001` | A. Staged evidence-driven portfolio | Keep CPU/reference portability; add accelerators only through exact parity and evidence gates |
| `D-P3.6-002` | A+. Fail-closed scheduler, Kubernetes backend, constrained runtime advisory placement | H-CAM owns admission and policy; Kubernetes and runtimes execute only admitted choices |
| `D-P3.6-003` | A+. Two-funnel conjunctive evidence with switchable objective views | Balanced, Throughput, and Latency may rank valid results but cannot weaken hard gates |
| `D-P3.6-004` | A. Immutable compatibility bundle with CPU/source rollback | Every optimized path is bound to an exact reproducible tuple and explicit fallback |
| `D-P3.6-005` | A. Owned-lab then authorized capacity target | Current laptop proves portable behavior; stronger machines prove only their exact measured capacity |

`A+` means the owner accepted Option A and added a constrained extension. It
does not combine the unsafe parts of Options B or C with A. The typed H-CAM
scheduler remains authoritative, Kubernetes remains an optional execution
backend, and runtime-managed placement remains advisory within an already
admitted device/provider/resource set.

## D-P3.6-001: Staged Runtime Portfolio

Selected option: **A. Staged evidence-driven portfolio**.

- ONNX Runtime CPU remains the behavior reference and portable rollback path.
- OpenVINO is evaluated first only on an exact approved Intel profile.
- TensorRT and optional DeepStream are evaluated only on exact approved NVIDIA
  hardware after the promoted model and fallback are frozen.
- Triton is evaluated only after a measured multi-model, multi-consumer,
  isolation, or utilization trigger.
- Each provider, precision, compiled artifact, device, and configuration needs
  independent parity, security, capacity, and rollback evidence.
- Failure to accelerate does not justify changing taxonomy, quality gates,
  event semantics, or evidence requirements.

## D-P3.6-002: Fail-Closed Scheduling With Bounded Backends

Selected option: **A+**.

The accepted foundation is a typed fail-closed scheduler with immutable node
capability snapshots, hard admission constraints, deterministic soft ranking,
leased placements, bounded node-local queues, reservations, fairness,
reconciliation, and explicit degradation.

The owner additions are constrained as follows:

- Kubernetes may become an execution backend for admitted workloads, node
  inventory, process/container placement, health, and restart operations.
- Kubernetes labels, affinities, device plugins, requests, or limits cannot
  grant H-CAM authorization or override department, data-zone, artifact,
  compatibility, freshness, or rollback policy.
- OpenVINO AUTO, ONNX Runtime providers, Triton, DeepStream, or another runtime
  may advise placement only inside the exact provider/device/resource set that
  H-CAM already admitted.
- Silent provider, device, precision, model, or CPU fallback is prohibited.
- Laptop execution remains possible without Kubernetes through the same domain
  contracts and node-local scheduler semantics.

## D-P3.6-003: Evidence And Switchable Objectives

Selected option: **A+**.

The two required funnels remain separate:

1. select the model champion and fallback using quality, lineage, stability,
   resource, and downstream evidence;
2. compare exact runtime/provider/hardware bundles only for the promoted model.

`CONTRACT`, `INFER`, and `PIPE` evidence remain distinct, and C1/C10/C50 claims
remain bound to exact generated workloads and hardware. The accepted future
views are:

- **Balanced**: rank eligible profiles using bounded latency, throughput,
  resources, quality, fairness, and recovery;
- **Throughput**: prioritize sustained fresh throughput after every parity,
  tail-latency, fairness, lineage, and security gate passes;
- **Latency**: prioritize p95/p99 latency and freshness after every quality,
  capacity, lineage, and security gate passes.

The future dashboard may expose these as controls. They are policy views, not
permission to relabel evidence, hide failed metrics, or bypass hard gates.

## D-P3.6-004: Immutable Bundle And Rollback

Selected option: **A. Immutable compatibility bundle with CPU/source
rollback**.

- every profile binds model source/export/compiled derivative, runtime,
  provider, precision, configuration, hardware, firmware, driver, OS, decoder,
  container when used, SBOM, provenance, license, vulnerability state,
  benchmark evidence, and rollback tuple;
- optimized bundles are profile-specific and are not assumed portable;
- fallback is explicit, audited, capacity-checked, and evidence-backed;
- CPU/source rollback is retained, but the assignment pauses if that fallback
  cannot meet its approved safety or freshness bounds;
- mutable aliases, hidden roll-forward, and worker-side arbitrary artifact or
  plugin locations remain prohibited.

## D-P3.6-005: Two-Gate Hardware Evidence

Selected option: **A. Two-gate owned-lab then authorized capacity-target
strategy**.

- the current laptop is the portable CPU/reference profile and may later be an
  exact Intel/OpenVINO feasibility target;
- a stronger GPU-equipped laptop is a separate `local_accelerated` profile,
  never an assumed extension of the current machine;
- C10/C50 and server/cluster claims require a separately declared and approved
  `capacity_target` profile;
- results are valid only for the exact machine, power mode, software tuple,
  generated workload, duration, and repetitions in the signed evidence;
- no laptop or lab result is extrapolated into statewide or production claims.

## Dynamic Capability Policy

H-CAM keeps one application and one set of domain, API, event, security,
lineage, audit, privacy, retention, and failure contracts across hardware.
Profiles adapt resource use rather than product correctness.

Permitted adaptive dimensions are worker concurrency, stateless detector batch
size, detector sampling within an approved floor, optional enrichment,
preview rate/quality, and bounded queue/reservation values. A lower-capacity
machine removes optional work or reduces admitted load before it changes a
contract or processes stale work.

Three planning profiles are recorded:

- `portable_cpu`: conservative current-laptop/CI reference;
- `local_accelerated`: exact validated stronger laptop with an approved Intel,
  NVIDIA, or AMD provider;
- `capacity_target`: separately authorized lab/server profile for C10/C50 and
  optional Kubernetes evidence.

Automatic selection can choose only a fresh, validated profile with an approved
compatibility bundle. If none qualifies, H-CAM uses an approved lower profile
or pauses. It never invents a configuration from unverified hardware.

## Remaining Gates

- `P36-G1`: freeze model-family comparison, champion, and fallback;
- `P36-G2`: approve exact machine, OS, driver, runtime, provider, precision,
  decoder, resource, and generated workload manifests;
- `P36-G4`: authorize exact digest-bound artifact, dependency, driver, or
  container research;
- `P36-G5`: authorize exact implementation and runtime execution through a
  later `D-P3.6-START` record.

## Continuing Non-Authorization

These selections approve architecture planning only. They do not authorize
downloads, dependencies, models, datasets, drivers, containers, runtime or
inference execution, GPU/hardware tests, Kubernetes actions, dashboard or
application implementation, cameras, media, Sentinel/ONVIF/stream access,
real/private/Government data, training, identity, cross-camera linkage,
watchlists, operational alerting, deployment, remote Git, P3.7, or later work.
