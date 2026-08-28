# P3.6 Start Intent Record

Status: `recorded_non_effective_prerequisites_incomplete`.

On 2026-08-29, `mayank-admin` supplied the statement
`continue D-P3.6-START`. The statement is preserved in
[`p3-6-start-intent.json`](../../contracts/phase-3/p3-6-start-intent.json).

The statement is explicit owner intent to continue P3.6, but it is not yet an
effective implementation or runtime-execution authorization. The accepted P3.6
plan requires exact manifests and passed hard gates before a start statement
can authorize executable work.

## Gate Snapshot When Received

| Gate | State | Consequence |
| --- | --- | --- |
| `P36-G0` | Passed | P3.5 baseline and P3.6 planning authority exist |
| `P36-G1` | Blocked | No completed `DET-R0/E1/B1/A1` comparison or approved champion/fallback pair |
| `P36-G2` | Blocked | No exact approved portable, accelerated, and capacity-target machine/runtime/workload manifests |
| `P36-G3` | Passed | The five architecture decisions are accepted |
| `P36-G4` | Blocked | No exact artifact, dependency, driver, runtime, or container research authority |
| `P36-G5` | Blocked | The statement is not bound to an executable package digest and action allowlist |

No later gate can be inferred from an earlier gate. The received statement does
not change G1, G2, or G4 and therefore cannot make G5 pass.

## Why The Statement Is Not Yet Effective

An effective final `D-P3.6-START` record must bind:

- the exact promoted model and fallback plus source and compiled artifacts;
- exact hardware, OS, driver, provider, runtime, precision, decoder, resource,
  and generated-workload profile revisions;
- exact implementation work packages, actions, repository paths, dependencies,
  migrations, APIs, workers, tests, and outputs;
- every permitted artifact source, digest, size, network action, quarantine,
  scan, license, SBOM, provenance, and loading rule;
- Kubernetes/container scope or an explicit empty allowlist;
- parity, quality, capacity, freshness, failure, observability, degradation,
  rollback, and evidence rules;
- a clean source commit, immutable package digest, and continuing prohibitions.

Those values do not currently exist. A broad statement cannot authorize
undisclosed future artifacts, machines, dependencies, paths, downloads, or
runtime actions.

## Current Exact Foundation

P3.2 already approved one exact restricted reference artifact:

- candidate: `DET-R0` / YOLOX-Tiny;
- artifact: `DET-R0-ONNX-UPSTREAM-0.1.1RC0`;
- SHA-256:
  `427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`;
- scope: local generated-only P3.2 reference, not P3.6 promotion or deployment.

`DET-E1`, `DET-B1`, and `DET-A1` remain blocked by unresolved exact artifacts,
weight licensing, lineage, model cards, SBOMs, and H-CAM comparison evidence.
The current laptop has only a historical planning profile; the stronger
GPU-equipped laptop and capacity target are not identified.

## Allowed Effect

Until a final digest-bound start package is accepted, this statement permits no
new executable action. Work may continue only under the earlier
`D-P3.6-PLAN-AUTH` boundary:

- preserve and synchronize the decision record;
- continue read-only public official-source research;
- prepare exact artifact, inventory, workload, and authorization proposals;
- validate and commit local planning records.

## Continuing Non-Authorization

No application, scheduler, runtime, dashboard, Kubernetes, container, model,
dataset, dependency, driver, migration, API, worker, inference, GPU/hardware
test, media/camera/stream, real/private/Government data, deployment, remote Git,
P3.7, or later action is authorized by this start intent.

The statement will be superseded only when `P36-G1`, `P36-G2`, and `P36-G4`
pass and `mayank-admin` accepts an exact immutable `D-P3.6-START` package
digest.
