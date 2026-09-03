# P3.6 Portable CPU R1 Admission Gap R0

Status: planning-only gap analysis complete; four owner policy selections are
pending. No inventory, runtime, artifact, hardware, container, deployment, or
implementation authority is granted.

## Purpose

The authorized R1 inventory fixed one specific problem: H-CAM now has a
sanitized current-laptop record conforming to the exact shared Phase -1 node
inventory schema. It did not make `portable_cpu` runnable or resolver-eligible.

This record compares:

- the sanitized R1 inventory and bounded collection evidence;
- the accepted, non-executable portable CPU R0 planning package;
- the exact Phase -1 inventory, compatibility, resolver, placement, selection,
  and deployment-profile contracts; and
- the current `P36-G2` gate.

The machine-readable records are:

- [R1 admission gap](../../contracts/phase-3/p3-6-portable-r1-admission-gap.json);
- [owner decision packet](../../contracts/phase-3/p3-6-portable-r1-decision-packet.json); and
- the package manifest added after final hash verification.

## What R1 Establishes

R1 supplies the shared inventory shape, opaque identity, CPU-laptop class,
Windows/AMD64 platform family, physical and logical CPU counts, observed memory,
local read-only provenance, redaction policy, explicit unknowns, and a bounded
observation/validity interval.

R1 does **not** establish:

- model/runtime/provider/precision compatibility;
- artifact presence, provenance, signature, SBOM, vulnerability state, or
  promotion status;
- allocatable or reserved CPU and memory;
- accelerator, container, Kubernetes, or scheduler support;
- pipeline, workload, capacity, policy, or authorization digests;
- latency, throughput, quality, freshness, recovery, or resource thresholds;
- an eligible resolver candidate; or
- profile activation or deployment authority.

Its maximum validity ends at `2026-08-31T17:57:26.397Z`. After that time it is
preserved as historical evidence but must fail a new admission evaluation with
`input_stale`.

## Seven Resolver Inputs

The shared resolver requires exactly seven input kinds.

| Input | Current state |
| --- | --- |
| Capability inventory | R1 is observed and bounded; admission use requires it to be unexpired |
| Authorization context | Missing for profile validation, admission, and execution |
| Policy snapshot | Planning policy exists; no immutable admission-time snapshot exists |
| Compatibility snapshot | Missing |
| Workload requirements | Generated C1 shape proposed; exact digest and numeric values missing |
| Pipeline graph | Exact stage and contract digests missing |
| Capacity snapshot | Allocatable/reserved capacity and freshness evidence missing |

Therefore the only correct resolver result remains `pending` or `rejected`; it
cannot be `selected` or `fallback`.

## Gap Summary

The machine-readable record contains 22 exact gaps across:

- inventory freshness and refresh timing;
- authorization and immutable policy input;
- model choice, compatibility, artifacts, pipeline, license, security,
  fallback, and rollback;
- runtime/provider/precision and exact runtime configuration;
- allocatable/reserved CPU and memory;
- deterministic workload digest, seeds, iterations, repetitions, duration, and
  numeric gates;
- pipeline graph, capacity snapshot, candidate set, and replay evidence;
- deployment-profile prerequisites; and
- `owned_gpu_lab` plus future standalone-server/Kubernetes disposition.

R1 closes none of these by inference. An observed field is not an admission
claim unless the relevant contract and evidence explicitly say so.

## Owner Decisions

### D-P3.6-U3B-001: Inventory Refresh Timing

**A. Just-in-time digest-bound refresh (recommended).** Preserve R1 after
expiry and request another one-attempt refresh only when compatibility,
workload, policy, and candidate records are sealed. This minimizes machine
access and gives the future review a genuinely fresh input.

**B. Refresh at each planning milestone.** Produces more snapshots but repeats
owner actions and allows each result to expire before the other inputs are
ready.

**C. Reusable periodic collector.** Better operationally, but this is product
implementation and materially expands security and privacy scope. It is not
authorized now.

**D. Waive or extend expiry.** Conflicts with the accepted 24-hour fail-closed
policy.

### D-P3.6-U3B-002: Resolver Admission Policy

**A. Strict seven-input fail-closed admission (recommended).** The profile can
enter the candidate set only when every resolver input is fresh, valid, and
content-addressed, and generated validation has passed. Unknown or stale input
rejects it.

**B. Inventory-only provisional eligibility.** Useful for a demonstration, but
it weakens the shared contract and risks turning a planning record into an
execution path.

**C. Manual operator activation.** Rejected by the accepted rule that UI and
operator controls cannot waive hard safety gates.

**D. Defer portable CPU.** Valid but removes the laptop/CI reference path and
slows compatibility work for collaborators and future servers.

### D-P3.6-U3B-003: Compatibility Bundle

**A. Complete immutable compatibility bundle (recommended).** Bind model,
runtime, provider, precision, artifacts, provenance, SBOM, signature,
vulnerability report, pipeline digests, license, security expiry, target,
fallback, rollback, and policy references.

**B. Model and runtime only.** Smaller, but structurally insufficient for shared
compatibility admission and safe rollback.

**C. Mutable local environment.** Easy on one laptop but not reproducible across
friends' GPUs or Government/server environments.

**D. No compatibility bundle.** Contradicts the accepted immutable-bundle and
no-silent-fallback decisions.

### D-P3.6-U3B-004: Generated C1 Validation Shape

**A. Deterministic `CONTRACT` plus C1 `INFER` matrix (recommended).** Seal fixed
seeds, cold start, warm steady state, bounded burst, dependency loss, safe
shutdown, warmup/measured iterations, repetitions, resource ceilings,
recovery checks, and balanced/throughput/latency reports. Balanced remains the
default. This is still a design only; exact numeric values and execution need a
later package and authorization.

**B. Minimal deterministic smoke.** Fast, but proves no queue, resource,
recovery, sustained behavior, or objective-mode evidence.

**C. Throughput stress first.** Resource aggressive, unsuitable as the current
laptop baseline, and not authorized.

**D. Defer generated validation.** Leaves `P36-G2` blocked indefinitely.

Recommended selection: `A/A/A/A`.

## Gate Effect

Preparing or accepting these policy choices cannot by itself:

- refresh inventory;
- make `portable_cpu` resolver-eligible;
- authorize artifact or dependency acquisition;
- authorize runtime/model execution or hardware testing;
- activate placement, scheduling, containers, or Kubernetes;
- access cameras, media, private data, or Government data;
- implement product or dashboard behavior;
- authorize deployment; or
- authorize remote Git.

`P36-G2` remains blocked. `P36-G1`, `P36-G4`, and `P36-G5` are unchanged.
