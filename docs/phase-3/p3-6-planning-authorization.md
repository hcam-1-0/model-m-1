# P3.6 Planning Authorization

Decision: `D-P3.6-PLAN-AUTH`

Status: planning and primary-source research authorized by `mayank-admin` on
2026-08-27.

Machine-readable record:
[`p3-6-planning-authorization.json`](../../contracts/phase-3/p3-6-planning-authorization.json).

## Owner Statement

The owner submitted:

> D-P3.6-PLAN-AUTH: Authorize planning and primary-source research only for
> P3.6 Runtime Acceleration and Scheduling. No downloads, runtime execution,
> GPU/hardware testing, containers, deployment, camera/media/data access,
> implementation, or remote Git actions.

This statement is exact planning authority. It is not an artifact-research,
runtime-execution, implementation-start, benchmark, deployment, or acceptance
decision.

## Authorized Work

- inspect accepted local Phase 3 documentation, contracts, and evidence;
- read current public primary-source documentation over HTTPS without saving
  packages, model artifacts, datasets, drivers, or containers;
- compare documented runtime, device, batching, scheduling, portability,
  benchmark, observability, and supply-chain properties;
- design runtime roles, activation triggers, node capability records,
  scheduling, admission, bounded queues, batching, backpressure, parity,
  benchmarking, packaging, degradation, rollback, and acceptance gates;
- prepare machine-readable planning records, documentation, owner choices, and
  a separate future implementation-start gate;
- validate the planning documents and create a local planning branch/commit.

## Not Authorized

No model, weight, dataset, source archive, package, driver, firmware, or
container may be downloaded. No inference, decoder, scheduler, accelerator,
GPU, CPU, NPU, media, benchmark, hardware inventory refresh, container, or
deployment command may run. No application code, runtime adapter, API,
migration, worker, scheduler, infrastructure, dependency, lockfile, or host
configuration may change.

No camera, ONVIF endpoint, Sentinel stream, media, generated benchmark data,
public dataset, private data, Government data, or police data may be accessed.
No training, fine-tuning, export, quantization, engine compilation, performance
claim, capacity claim, pilot, production use, remote Git action, P3.7, or later
work is authorized.

## Accepted Dependency

P3.5 is accepted under `D-P3.5-W10-ACCEPTANCE` for immutable package digest
`4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`
at commit `1611922b4f410aa0cdbce369e4f3c8838f53e19f`.

P3.6 planning may reference that generated-only, zero-retention, default-off
package. It may not activate it, reinterpret its synthetic evidence as a
performance baseline, or weaken any existing restriction.

The planning baseline is repository head
`c0cb82b32f3ec399b64668da4600540c88b8c25e` on the new local branch
`codex/phase3-runtime-acceleration-planning`.

## Required Next Gates

1. owner selection for `D-P3.6-001` through `D-P3.6-005`;
2. completion and approval of the detector model-family comparison;
3. exact hardware, operating-system, driver, runtime, precision, artifact, and
   workload profiles;
4. a separately bounded artifact/dependency/container research authority if
   external materials are required;
5. an exact `D-P3.6-START` statement bound to reviewed manifests and paths.

Until every applicable gate is complete, P3.6 remains planning-only.
