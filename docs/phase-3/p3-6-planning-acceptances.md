# P3.6 Planning Acceptances R0

Status: three planning-only owner acceptances recorded on 2026-08-30. A later,
separate `D-P3.6-INVENTORY-R1-AUTH` accepted one bounded collection attempt;
that attempt succeeded and is consumed. No continuing inventory collection,
artifact acquisition, implementation, runtime, or deployment authority exists.

Machine-readable records:

- [portable CPU proposal acceptance](../../contracts/phase-3/p3-6-portable-cpu-profile-acceptance.json);
- [inventory and admission owner decisions](../../contracts/phase-3/p3-6-inventory-admission-owner-decisions.json); and
- [model metadata proposal acceptance](../../contracts/phase-3/p3-6-model-artifact-research-acceptance.json).

Later R1 outcome records:

- [consumed owner authorization](../../contracts/phase-3/p3-6-inventory-r1-authorization.json);
- [sanitized shared-schema R1](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json); and
- [bounded collection evidence](../../contracts/phase-3/p3-6-inventory-r1-collection-evidence.json).

## Portable CPU Planning Proposal

`D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE` accepts package digest
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`
as the conservative non-executable `portable_cpu` planning baseline.

The accepted planning values include the CPU behavior reference, single
assignment/worker operation, batch one, one in-flight inference request, a
bounded two-item queue, and a future generated C1 `INFER` workload. All
unresolved runtime, resource, dependency, artifact, workload, quality,
freshness, and validation fields remain blockers. The profile is not
resolver-eligible or active.

## Inventory And Admission Policy

The owner selected `A/A/A/A` against package digest
`CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`:

| Decision | Accepted selection |
| --- | --- |
| `D-P3.6-U3A-001` | Preserve historical R0 and later collect a new exact shared-schema R1 |
| `D-P3.6-U3A-002` | Maximum 24-hour inventory validity with immediate authorized-change invalidation |
| `D-P3.6-U3A-003` | Local read-only observed provenance plus a separate digest-bound owned-local generated-only trust policy |
| `D-P3.6-U3A-004` | Block new admission on expiry while independent reservation, lease, fencing, health, and policy rules remain authoritative |

Historical R0 remains immutable, nonconforming to the shared inventory shape,
stale under the accepted policy, and ineligible for admission. These policy
selections did not authorize a query or projection. A separate exact
`D-P3.6-INVENTORY-R1-AUTH` package was prepared under digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`.
The owner later accepted that digest; its one local read-only attempt produced a
sanitized shared-schema-valid R1 and is consumed. The R1 does not activate or
admit a profile.

## Model Metadata Proposal

`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` accepts package digest
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`
as metadata-only planning for `DET-E1`, `DET-B1`, and `DET-A1`.

No artifact is authorized for download, loading, scanning, conversion, export,
or execution. A future `D-P3.6-MODEL-RESEARCH-R1-AUTH` is not issuable until an
eligible exact local quarantine root and exact scanner/passive-inspection
bindings are sealed in a regenerated package.

## Gate State

| Gate | State after these acceptances |
| --- | --- |
| `P36-G0` | Passed |
| `P36-G0A` | Passed |
| `P36-G1` | Blocked: no acquired comparison artifacts, H-CAM evidence, or approved champion/fallback |
| `P36-G2` | Blocked: R1 exists, but exact runtime/resource/workload manifest, compatibility values, other profiles, and generated validation evidence remain missing |
| `P36-G3` | Passed |
| `P36-G4` | Blocked: no acquisition authority or exact storage/scanner binding |
| `P36-G5` | Blocked: no digest-bound implementation/runtime authorization |

## Continuing Boundary

The completed R1 decision authorizes no further inventory projection or
recollection. These decisions authorize no package/model/
dataset/driver/container download, model loading, inference, benchmark,
hardware test, scheduler, container, Kubernetes, application implementation,
camera/media/stream/data access, profile activation, model promotion,
deployment, remote Git action, P3.7, or later work.
