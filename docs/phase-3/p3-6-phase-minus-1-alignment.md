# P3.6 To Phase -1 Alignment

Status: aligned planning baseline under `D-P3.6-PLAN-AUTH`. This record changes
no accepted P3.6 owner selection and grants no implementation or execution
authority.

Machine-readable record:
[`p3-6-phase-minus-1-alignment.json`](../../contracts/phase-3/p3-6-phase-minus-1-alignment.json).

## Why This Alignment Exists

P3.6 runtime acceleration planning began before the platform-wide Phase -1
contracts were completed. Both bodies of work describe capability inventory,
profile selection, compatibility, scheduling, pipeline composition, evidence,
rollback, and deployment shapes. Leaving both as independent authorities would
create duplicate concepts and incompatible profile names.

The completed Phase -1 contracts are now the shared platform authority. P3.6
is a specialized consumer that contributes detector runtime candidates,
generated benchmark definitions, and candidate-specific evidence. P3.6 does
not replace the shared resolver, scheduler, compatibility registry, pipeline,
evidence, or deployment-profile contracts.

## Immutable Source Baseline

| Source | Revision | Binding |
| --- | --- | --- |
| `hcam-2-0/hcam-protos` | `d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8` | Six experimental shared contracts in `contracts/catalogue.json` |
| `hcam-2-0/hcam-deployment` | `71095fe89d2b711e4982ddc0130fcaedda8703e7` | Four planned deployment overlays |
| Deployment base | `sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf` | Canonical base profile required by every overlay |
| `hcam-2-0/hcam-docs` | `809c44c2f32b2420ab954bed994b098bad1d1238` | Phase -1 delivery evidence |
| P3.6 source baseline | `b39439db514ca4f11bdd3d8591c5f9c170bdebf5` | Planning state before this additive alignment |

These are planning-contract revisions, not executable release approval. Future
P3.6 manifests must bind exact accepted successor revisions if any source
contract changes.

## Ownership Boundary

Phase -1 owns the reusable platform shapes and authority:

- sanitized node capability inventory, provenance, freshness, and unknown
  states;
- deterministic hard-gate filtering, ranking, fallback, and replay identity;
- model/runtime compatibility lifecycle, suspension, fallback, and rollback;
- workload admission, reservation, placement, fencing, leases, queues, retry,
  cancellation, and backend reconciliation;
- typed composable pipeline stages, required/optional behavior, and bypass
  effects;
- immutable adaptive-selection evidence, diagnostics, audit projection, and
  rollback;
- `portable_cpu`, `owned_gpu_lab`, `standalone_server`, and
  `kubernetes_cluster` deployment profile classes.

P3.6 owns only its analytics-runtime specialization:

- detector runtime candidates and staged evaluation order;
- model/runtime/provider/precision parity for each candidate;
- generated runtime benchmark workload definitions;
- separate `CONTRACT`, `INFER`, and `PIPE` evidence;
- C1/C10/C50 measurement and candidate-specific capacity evidence;
- detector batching, queue, freshness, and recovery measurements;
- candidate evidence inputs used by the shared compatibility and rollback
  contracts.

The boundary is deliberate: P3.6 supplies evidence and requirements to shared
contracts, while Phase -1 decides whether an exact workload is admissible and
where an admitted lease may execute.

## Decision Crosswalk

| P3.6 decision | Shared Phase -1 authority | Effective interpretation |
| --- | --- | --- |
| `D-P3.6-001` | Compatibility registry and composable pipeline | Candidate portfolios become exact compatibility entries and pipeline implementations; they do not define a second registry or graph model |
| `D-P3.6-002` | Inventory, resolver, and workload placement | H-CAM admission and leased placement remain authoritative; runtime AUTO selection is advisory inside an admitted device/provider/resource set |
| `D-P3.6-003` | Resolver and adaptive-selection evidence | Objective modes rank eligible profiles; C1/C10/C50 remain generated evidence workloads and do not create profiles |
| `D-P3.6-004` | Compatibility and rollback evidence | P3.6 artifacts and measurements populate immutable compatibility and rollback bundles |
| `D-P3.6-005` | Inventory and resolver | Owned-lab and capacity evidence bind exact shared deployment profiles and cannot be extrapolated |

The accepted values `A`, `A+`, `A+`, `A`, and `A` remain unchanged.

## Profile Vocabulary

The older P3.6 documents used three planning terms. They remain in historical
records for traceability, but their effective meaning is now:

| Historical P3.6 term | Effective meaning | Rule |
| --- | --- | --- |
| `portable_cpu` | Phase -1 `portable_cpu`, profile ID `hcam-portable-cpu` | Exact alias |
| `local_accelerated` | Phase -1 `owned_gpu_lab`, profile ID `hcam-owned-gpu-lab` | Historical alias only; new manifests use `owned_gpu_lab` |
| `capacity_target` | Evidence target that resolves to `standalone_server` or `kubernetes_cluster` | Not a fifth deployment profile |

An exact capacity target must select one shared deployment profile. A single
record cannot ambiguously mean both standalone and Kubernetes execution.

`balanced`, `throughput`, and `latency` are resolver objectives. They are not
deployment profiles, runtime permissions, or evidence waivers.

C1, C10, and C50 are generated-workload evidence tiers. They are not hardware
profiles and make no capacity claim until exact hardware, runtime, workload,
duration, repetition, resource, quality, latency, recovery, and freshness
evidence is accepted.

## Future Manifest Binding

Every future P3.6 proposal must identify:

1. exact `hcam-protos` and `hcam-deployment` revisions;
2. exact base profile digest and deployment profile revision;
3. exact node inventory and compatibility bundle revisions;
4. exact model, source, export, compiled artifact, runtime, precision, and
   configuration digests;
5. exact generated workload and evidence tier;
6. exact resolver objective and admitted resource bounds;
7. exact fallback and rollback records.

The shared lifecycle remains `experimental` or `planned` until separately
promoted. This alignment does not silently promote any contract to production.

## Gate Effect

`P36-G0A` passes because the P3.6 vocabulary and ownership now align with the
completed Phase -1 baseline. All substantive gates retain their prior state:

- `P36-G1`: blocked on acquired evidence, comparison, champion, and fallback;
- `P36-G2`: blocked on exact shared-profile runtime and workload manifests;
- `P36-G3`: passed for the five accepted architecture decisions;
- `P36-G4`: blocked on exact storage/scanner bindings and acquisition authority;
- `P36-G5`: blocked because no digest-bound executable package is authorized.

The R0 model proposal still awaits
`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE`. This alignment does not imply that
acceptance and does not make `D-P3.6-MODEL-RESEARCH-R1-AUTH` issuable.

## Continuing Boundary

This is documentation and contract planning only. It authorizes no downloads,
models, datasets, dependencies, drivers, containers, runtime or inference,
hardware or performance tests, Kubernetes actions, implementation, dashboard,
camera/media/Sentinel/ONVIF access, private or Government data, identity,
cross-camera linkage, watchlists, alerts, deployment, remote Git action, P3.7,
or later work.
