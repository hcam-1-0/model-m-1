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

Status: metadata planning package owner accepted under
`D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE`; acquisition, execution, and promotion
remain blocked.

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

The owner acceptance covers only this non-authorizing planning record. A later
acquisition decision is not issuable until an exact
eligible local non-cloud quarantine root and exact scanner invocation are
bound in a regenerated R1 package. No candidate can be promoted from upstream
metrics alone.

### P36-U3: Exact Shared-Profile Manifests

Status: portable CPU R0 non-executable planning proposal and inventory-policy
`A/A/A/A` choices owner accepted. The separate one-time shared-schema R1
collection succeeded and is consumed; all activation and validation gates
remain blocked.

The [portable CPU profile proposal R0](p3-6-portable-cpu-profile-proposal.md)
binds the authorized inventory, accepted P3.2 CPU behavior reference, exact
Phase -1 revisions, conservative single-assignment envelope, and generated C1
`INFER` workload shape. Its package digest is
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.
It deliberately leaves resource bounds, workload duration/repetition, evidence
thresholds, trust-zone expiry, dependency closure, and artifact state
unresolved. It is not a validated manifest and does not pass `P36-G2`.

The exact [inventory and admission gap](p3-6-inventory-admission-gap.md) also
shows that the historical R0 inventory is not structurally conforming to the
shared Phase -1 inventory schema. Its sealed package digest is
`CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.
The selected policy preserves R0, required a new exact shared-schema R1, uses a
maximum 24-hour freshness window plus early change invalidation, binds observed
local provenance to a separate generated-only trust-policy digest, and blocks
new admission on expiry while independent leases remain authoritative. The
separate exact `D-P3.6-INVENTORY-R1-AUTH` was accepted against package digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`.
Its one attempt produced the sanitized
[R1 record](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json) and
[bounded evidence](../../contracts/phase-3/p3-6-inventory-r1-collection-evidence.json).
That attempt is consumed and grants no profile admission or further collection.

The follow-on [portable CPU R1 admission gap](p3-6-portable-r1-admission-gap.md)
is sealed under package digest
`471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`.
It identifies 22 remaining gaps and presents decisions
`D-P3.6-U3B-001` through `D-P3.6-U3B-004`. `mayank-admin` accepted the
recommended `A/A/A/A` planning policies. The acceptance is non-effective and
leaves all profile, execution, and implementation gates closed.

The exact follow-on
[portable compatibility and generated C1 validation proposal](p3-6-portable-compatibility-validation-proposal.md)
is sealed under package digest
`9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A`.
It presents `D-P3.6-U3C-001` through `004`, with `A/A/A/A` recommended and all
four choices now owner accepted as non-effective planning policy. It changes no
hard gate.

The next exact
[portable R1 supply-chain prerequisite proposal](p3-6-portable-r1-supply-chain-prerequisite-proposal.md)
is sealed under package digest
`496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
It presents `D-P3.6-U3D-001` through `005`; the owner accepted `A/A/A/A/A` as
non-effective planning policy. No exact local quarantine root or scanner chain
is bound, and the acceptance changes no hard gate or authority.

The owner then supplied `F:` as the candidate volume. The proposed isolated
root `F:\HCAM-Quarantine` and one-attempt storage/scanner metadata action set are
sealed in the
[U3E authorization proposal](p3-6-quarantine-scanner-binding-r0-authorization-proposal.md)
under digest
`9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`.
The owner accepted it and the single attempt was consumed. Volume and path
checks passed, the broad-write ACL gate failed, the atomic probe was skipped,
and the empty root was removed. No retry is authorized.

The
[U3F quarantine remediation decision proposal](p3-6-quarantine-remediation-r1-proposal.md)
is sealed under digest
`9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`.
The owner selected `A/A/A/A/A/A`. The resulting
[U3G authorization proposal](p3-6-quarantine-remediation-r1-authorization-proposal.md)
is sealed under digest
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`
and was exactly owner authorized. The single attempt is consumed: exact DACL
verification failed, the probe was skipped, the empty root was removed, and
Defender yielded no usable product version. No retry is authorized.

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

The portable planning proposal, inventory `A/A/A/A` policies, model metadata
proposal, and completed one-time R1 outcome are linked from the
[P3.6 planning acceptance record](p3-6-planning-acceptances.md). The U3B
`A/A/A/A` policies are now explicitly accepted against package digest
`471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`.
Those U3C choices are now accepted as `A/A/A/A` planning policy against exact
package digest
`9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A`.
The non-executable R1 supply-chain prerequisites are now sealed as the U3D
package under digest
`496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
The owner accepted `D-P3.6-U3D-001` through `005` as `A/A/A/A/A`, accepted and
consumed U3E, selected U3F `A/A/A/A/A/A`, and exactly authorized U3G against
package digest
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
U3G is consumed and failed closed. The next planning action is bounded failure
analysis for the exact DACL semantic mismatch and unavailable Defender product
version. That analysis is complete and the non-effective U3H owner decision
package is sealed under digest
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
The owner selected `D-P3.6-U3H-001` through `006` as `A/A/A/A/A/A` under
acceptance SHA-256
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`.
That preparation is complete. The non-effective U3I runner
implementation-authorization package is sealed under digest
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`,
and the separate U3J storage R2 planning package is sealed under digest
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.
Both requested statements are accepted. U3I authorized contract-only source and
generated harness implementation; U3J accepted the storage design only. The
implementation is complete within that scope and sealed under digest
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`.
The next action is exact owner review as
`D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE`.

The runner was parser checked but not executed. All machine handlers remain
unimplemented and fail closed. Even implementation acceptance cannot authorize
a runner execution or machine query; it permits preparation only of a separate
non-effective runtime-binding proposal. The final U3K storage execution package
cannot be prepared until separately authorized runtime evidence is sealed and
accepted. A Defender-only proposal remains sequenced after successful storage
evidence is accepted. No prior decision authorizes a retry, `F:` or ACL access,
scanner action, artifact access, runtime/model execution, profile activation,
validation, or deployment.

Before `D-P3.6-MODEL-RESEARCH-R1-AUTH` can be prepared, an exact local,
non-cloud, non-network quarantine root must pass a fresh threshold of at least
5 GiB and 15 percent free, and the exact scanner product, version, executable,
command, result handling, and passive checkpoint inspector must be bound.
Volume `B:` remains owner prohibited, and the historical `C:`, `E:`, and `F:`
observations are not current authority under the recorded low-free-space
policy. The U3G observation is consumed and cannot be refreshed or reused as
authority. No file may be downloaded, loaded, converted, executed, or promoted
meanwhile.

The completed inventory decision does not authorize collaborator-machine
access. A collaborator may later supply an independently generated sanitized
record, or a separate exact authority can cover an owned and explicitly
identified machine.
