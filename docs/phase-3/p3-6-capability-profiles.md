# P3.6 Dynamic Capability Profiles

Status: planning baseline accepted through `D-P3.6-001` through
`D-P3.6-005`. Exact machine manifests, implementation, and execution remain
unauthorized and pending.

Machine-readable policy:
[`p3-6-capability-profile-policy.json`](../../contracts/phase-3/p3-6-capability-profile-policy.json).

## Purpose

The same H-CAM application must run on the current CPU-only laptop and on
stronger GPU-equipped laptops or later lab capacity without forking product
behavior. Capability profiles change admitted load and optimization, not
authorization, correctness, evidence, or safety.

This document defines the profile contract that exact hardware manifests must
satisfy before any implementation or runtime authorization is proposed.

## Non-Negotiable Invariants

Every profile uses the same:

- domain, API, observation, tracking, rule, and outbox contracts;
- taxonomy, preprocessing, postprocessing, and approved model behavior;
- department, purpose, data-zone, RBAC, and network authorization;
- artifact lineage, audit, privacy, retention, and prohibited-data controls;
- parity, quality, calibration, freshness, failure, and claim policy;
- explicit degradation, rollback, and safe-pause semantics.

No profile may silently change model family, taxonomy, precision, provider,
data boundary, evidence layer, sampling floor, or retention policy.

## Profile Classes

| Profile | Intended environment | Candidate path | Claim boundary | Current state |
| --- | --- | --- | --- | --- |
| `portable_cpu` | Current laptop and deterministic CI/reference use | ONNX Runtime CPU reference | C1 correctness and small CPU evidence only until measured | Sanitized inventory complete; runtime/workload manifest pending |
| `local_accelerated` | Owned or authorized stronger laptop | Exact validated Intel, NVIDIA, or AMD provider | Exact machine and workload only | Exact manifest pending |
| `capacity_target` | Declared lab/server or later cluster target | Approved accelerated runtime; optional Kubernetes backend | C10/C50 only from signed exact-hardware evidence | Exact manifest pending |

The profile names describe capability, not a person or permanent machine.

## Adaptive Resource Dimensions

After hard gates pass, a validated profile may set different bounded values
for:

- worker count and per-worker concurrency;
- stateless detector batch size and formation delay;
- detector sampling target, never below the approved floor;
- optional enrichment activation and removal order;
- preview resolution, rate, and decode budget where a later UI is authorized;
- input queue count, bytes, age, reservations, and in-flight work;
- CPU/RAM/device/decoder reservations and thermal/power operating policy;
- C1/C10/C50 workload admission and maximum simultaneously active assignments.

The low-capacity sequence is: remove optional enrichment, reduce sampling
within the approved floor, reject stale/excess work, use an exact approved
fallback if it remains valid, then pause. The system does not continue by
silently weakening required behavior.

## Selection And Placement Policy

Future automatic profile selection is permitted only when all of these inputs
exist and are fresh:

1. immutable node capability snapshot;
2. approved model/runtime/hardware compatibility bundle;
3. authorized assignment revision and data boundary;
4. declared objective and load modes;
5. reserved capacity, queue, freshness, and rollback budgets.

H-CAM admission control filters candidates using hard authorization,
compatibility, capacity, security, lineage, and freshness constraints. It then
ranks only eligible candidates. Kubernetes may execute the admitted placement,
and a runtime may select only among admitted devices. Neither becomes an
authorization source.

If inventory is stale, the tuple is unapproved, capacity cannot be reserved,
or a runtime reports an unexpected provider/precision fallback, the workload
remains pending, rolls back to an approved lower profile, or pauses.

## Objective Modes

The future dashboard may expose:

| Mode | Ranking preference | Hard limits that still apply |
| --- | --- | --- |
| `balanced` | Combined bounded latency, throughput, resources, fairness, quality, and recovery | All parity, lineage, security, freshness, and capacity gates |
| `throughput` | Highest sustained fresh throughput | Tail latency, fairness, quality, recovery, and evidence-layer integrity |
| `latency` | Lowest p95/p99 and queue age | Quality, stable capacity, lineage, failure, and security gates |

These modes change ranking and presentation only. They do not change the test
dataset, hide metrics, relabel `INFER` as `PIPE`, or permit an invalid bundle.

## Future Operator Controls

The planned, not implemented, controls are:

- **Hardware**: `Auto`, `Portable CPU`, `Local Accelerated`;
- **Objective**: `Balanced`, `Throughput`, `Latency`;
- **Load**: `Conservative`, `Standard`, `Maximum Validated`.

`Auto` chooses only a profile approved for the current immutable node snapshot.
`Maximum Validated` means the exact tested ceiling for that profile, not all
available resources. The UI must show active profile revision, compatibility
bundle digest, objective, load policy, fallback state, evidence freshness, and
safe reason when the request cannot be admitted.

The dashboard controls are requirements for a later authorized UI package;
this planning record adds no dashboard code.

## Exact Capability Manifest

Each profile revision must eventually bind all of the following:

- profile ID/revision, machine identity, trust zone, owner/authorization, and
  observation/expiry time;
- OS, architecture, kernel, CPU model/features, allocatable cores, RAM, and
  power/thermal policy;
- accelerator vendor/model, stable device identity, memory, firmware, health,
  partition/share mode, and allocatable units;
- driver, compute stack, runtime/provider, precision, configuration, and exact
  compatibility-set digest;
- decoder and codec/profile/resolution/session limits with measured reserve;
- source model, export, compiled artifact, configuration, and build-recipe
  digests;
- concurrency, batch, sampling, queue, freshness, optional-stage, reservation,
  and degradation bounds;
- generated workload tier, input shapes, duration, scenarios, repetitions,
  seeds, background load, and power mode;
- parity, quality, latency, throughput, resource, resilience, recovery, and
  rollback evidence;
- SBOM, provenance, license, vulnerability, signature, approver, status, and
  suspension reason.

Self-reported inventory is not acceptance evidence. Exact manifests require
bounded inspection and measured generated-workload evidence under later
authorization.

## Planned Manifest Records

| Record | Purpose | State |
| --- | --- | --- |
| `P36-PROFILE-PORTABLE-CPU-R0` | Current laptop/CI reference tuple and conservative bounds | Inventory complete; runtime/workload bounds and owner approval pending `P36-G2` |
| `P36-PROFILE-LOCAL-ACCELERATED-R0` | First exact stronger-laptop accelerator tuple | Pending machine selection and `P36-G2` |
| `P36-PROFILE-CAPACITY-TARGET-R0` | First declared C10/C50 lab/server tuple | Pending target authorization and `P36-G2` |

No placeholder value may be interpreted as approval. Unknown driver, runtime,
provider, precision, hardware, or workload fields keep the profile blocked.

## Compatibility Bundle And Rollback

Every approved profile produces an immutable compatibility bundle. A compiled
engine is valid only for its bound machine/runtime tuple. Rollback order is:

1. exact prior validated bundle for the same profile;
2. exact approved source/runtime path on compatible capacity;
3. `portable_cpu` only when its capacity and freshness policy pass;
4. safe pause with an explicit reason.

Automatic roll-forward, mutable `latest` aliases, and cross-machine reuse of
compiled artifacts are prohibited.

## Next Planning Outputs

The next proposal must resolve `P36-G1` and prepare exact R0 manifests for the
available machines. Any external runtime, dependency, driver, container, model,
or compiled artifact then needs a separate digest/source/path-bound research
authorization before acquisition or execution. `D-P3.6-START` remains a later
explicit gate.
