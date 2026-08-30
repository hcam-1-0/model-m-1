# P3.6 Prerequisite Unblock Plan

Status: planning-only. The received `D-P3.6-START` statement is recorded but
not effective because G1, G2, and G4 remain blocked.

Machine-readable record:
[`p3-6-unblock-plan.json`](../../contracts/phase-3/p3-6-unblock-plan.json).

## Objective

Produce the exact evidence and manifests needed for one narrow, digest-bound
P3.6 start package without performing downloads, inference, hardware tests,
container/Kubernetes actions, or application implementation prematurely.

## Ordered Unblock Work

### P36-U0A: Phase -1 Shared-Contract Alignment

Status: complete under `D-P3.6-PLAN-AUTH`; `P36-G0A` passed.

The [P3.6 to Phase -1 alignment](p3-6-phase-minus-1-alignment.md) binds the
planning work to exact shared contract and deployment-profile revisions. Phase
-1 owns inventory, resolver, compatibility, placement, pipeline, evidence,
rollback, and deployment-profile semantics. P3.6 owns only runtime-candidate
and benchmark specialization.

Historical `local_accelerated` maps to `owned_gpu_lab`. Historical
`capacity_target` is an evidence target that must resolve to
`standalone_server` or `kubernetes_cluster`; it is not another deployment
profile. This completed planning item changes no acquisition or execution gate.

### P36-U1: Sanitized Current-Laptop Inventory

Status: complete under `D-P3.6-INVENTORY-R0-AUTH`.

The proposed authority is read-only and limited to `LAB-LAPTOP-01`:

- read Windows OS, architecture, CPU, installed memory, and display-controller
  inventory;
- read display-driver and already-installed runtime/provider versions;
- read `nvidia-smi` inventory only if it is already installed;
- write a sanitized local JSON record using the logical node ID
  `LAB-LAPTOP-01`.

The inventory must exclude hostname, Windows user, serial numbers, asset tags,
MAC/IP addresses, network configuration, personal paths, and raw device IDs.
It performs no benchmark, stress, inference, thermal, capacity, model, media,
network, install, update, container, or Kubernetes action.

The sealed output is
[LAB-LAPTOP-01 sanitized inventory R0](p3-6-inventory-lab-laptop-01-r0.md),
SHA-256
`0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F`.
It records an Intel i5-8365U, 8 GiB RAM, Intel UHD 620, no observed discrete
NVIDIA accelerator, and critically low free space on all fixed volumes.

This supplies factual input for the `portable_cpu` manifest. It does not by
itself pass `P36-G2` or authorize OpenVINO execution.

### P36-U2: Exact Model Research Proposal

Status: metadata proposal complete under `D-P3.6-PLAN-AUTH`; acquisition,
execution, and promotion remain blocked.

The exact [model artifact research proposal](p3-6-model-artifact-research-proposal.md)
and [machine-readable package](../../contracts/phase-3/p3-6-model-artifact-research-package.json)
identify, without downloading:

- exact source revision and candidate checkpoint/release for `DET-E1`,
  `DET-B1`, and `DET-A1`;
- publisher URL, expected filename, declared size where available, license,
  training-lineage statement, model card, export/runtime path, and expected
  artifact type;
- exact bounded URLs, hosts, size ceilings, quarantine paths, passive
  inspection, malware scan, SBOM, license, and evidence actions for a later
  research authorization;
- unresolved facts that keep a candidate blocked.

The package contains three exact native checkpoints with a cumulative expected
size of `537,489,237` bytes. Its sealed R0 manifest SHA-256 is
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.
No artifact was downloaded, loaded, scanned, exported, converted, or executed.

`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` may accept only this non-authorizing
planning record. A later acquisition decision is not issuable until an exact
eligible local non-cloud quarantine root and exact scanner invocation are
bound in a regenerated R1 package. No candidate can be promoted from upstream
metrics alone.

### P36-U3: Exact Shared-Profile Manifests

Prepare immutable proposals against the Phase -1 profile model:

1. `P36-PROFILE-PORTABLE-CPU-R0` from authorized sanitized inventory;
2. an `owned_gpu_lab` manifest from a similarly sanitized inventory supplied
   from the owned/authorized stronger laptop; and
3. a capacity evidence target selecting exactly `standalone_server` or
   `kubernetes_cluster`, or an explicit deferral that narrows P3.6 to C1 and
   forbids C10/C50 claims.

Each record must bind the exact runtime/provider/precision/decoder candidates,
resource bounds, generated workload, objective modes, rollback path, evidence
expiry, Phase -1 contract revisions, deployment base digest, and owner state.
Unknown values keep the profile blocked. The historical record names may be
retained for traceability, but cannot create competing profile classes.

### P36-U4: Final Start Package

After G1, G2, G3, and G4 pass, create one immutable package containing:

- exact allowed P3.6 work packages, actions, paths, and outputs;
- exact artifact/runtime/dependency/driver/container manifests or explicit
  empty allowlists;
- exact machine and generated-workload revisions;
- zero-ambiguity network, data, execution, and rollback boundaries;
- clean-source commit, package manifest, and SHA-256 digest.

Only a later owner statement that accepts that exact digest as
`D-P3.6-START` can pass `P36-G5` and begin executable work.

## Next Planning Action

`P36-U2` metadata preparation is complete. The owner may review
`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` against package digest
`2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`;
acceptance would grant no executable authority.

Before `D-P3.6-MODEL-RESEARCH-R1-AUTH` can be prepared, an exact local,
non-cloud, non-network quarantine root must pass a fresh threshold of at least
5 GiB and 15 percent free, and the exact scanner product, version, executable,
command, result handling, and passive checkpoint inspector must be bound.
Volume `B:` remains owner prohibited, and the observed `C:`, `E:`, and `F:`
volumes remain ineligible under the recorded low-free-space policy. No file
may be downloaded, loaded, converted, executed, or promoted meanwhile.

The completed inventory decision does not authorize collaborator-machine
access. A collaborator may later supply an independently generated sanitized
record, or a separate exact authority can cover an owned and explicitly
identified machine.
