# P3.6 Dynamic Capability Profiles

Status: planning baseline accepted through `D-P3.6-001` through
`D-P3.6-005`. Exact machine manifests, implementation, and execution remain
unauthorized and pending. A sealed non-executable `portable_cpu` R0 proposal
is owner accepted as planning only. R1 exists and the U3B `A/A/A/A` admission
policies are accepted. The exact compatibility and generated C1 proposal is
sealed and its U3C `A/A/A/A` planning policies are owner accepted; the profile is not
resolver-eligible. The U3D portable R1 supply-chain prerequisite policies are
owner accepted as `A/A/A/A/A`, but all exact storage, scanner, artifact,
inspection, and runtime bindings and evidence remain pending.
The exact `F:\HCAM-Quarantine` U3E attempt was consumed and failed closed at
the broad-write ACL gate. U3F remediation choices were accepted as
`A/A/A/A/A/A`; the exact U3G package was authorized and its one attempt is now
consumed. U3G failed closed because the current-process `Modify` rule did not
match the required exact post-create DACL semantics, and Defender yielded no
usable product version. The empty root was removed and no probe content was
retained. No retry or profile action is authorized. U3G package digest:
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
U3H failure analysis is sealed under digest
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
Its `A/A/A/A/A/A` design is owner accepted under acceptance SHA-256
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`
and remains resolver-ineligible; it authorizes proposal preparation only and no
retry, runner implementation, or profile action.
The resulting U3I runner package is sealed under digest
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`,
and the U3J storage R2 planning package is sealed under digest
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.
Both exact requested statements are accepted. The resulting contract-only
runner implementation is sealed under digest
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`
and owner accepted. Its historical runtime binding was also accepted, but it
predates the U3L machine-handler implementation and cannot authorize the current
sources. The U3L handlers are now accepted as source and generated/static
evidence only under
`D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE`. The profile remains
resolver-ineligible and non-executable until a fresh runtime binding, newly
sealed executable U3K package, and separate storage authority exist. The
historical non-effective runtime-binding authorization package is sealed under digest
`37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`.

Machine-readable policy:
[`p3-6-capability-profile-policy.json`](../../contracts/phase-3/p3-6-capability-profile-policy.json).

Effective shared-contract mapping:
[P3.6 to Phase -1 alignment](p3-6-phase-minus-1-alignment.md).

Portable CPU proposal:
[P3.6 portable CPU profile proposal R0](p3-6-portable-cpu-profile-proposal.md),
package digest
`56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.

Inventory admission analysis:
[P3.6 inventory and admission gap R0](p3-6-inventory-admission-gap.md), package
digest `CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.

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

## Effective Phase -1 Profile Model

The platform-wide Phase -1 contracts now own deployment profile classes. P3.6
uses those contracts rather than defining a second profile system:

| P3.6 planning term | Effective Phase -1 class | Interpretation |
| --- | --- | --- |
| `portable_cpu` | `portable_cpu` / `hcam-portable-cpu` | Exact alias |
| `local_accelerated` | `owned_gpu_lab` / `hcam-owned-gpu-lab` | Historical alias for an exact owned or authorized accelerated lab machine |
| `capacity_target` | `standalone_server` or `kubernetes_cluster` | Evidence target only; it must resolve to one exact profile and is not a fifth profile class |

The canonical Phase -1 profile classes are `portable_cpu`, `owned_gpu_lab`,
`standalone_server`, and `kubernetes_cluster`, all derived from deployment base
digest
`sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf`.

## Historical P3.6 Profile Vocabulary

The following accepted table is retained for decision traceability. Its terms
must be interpreted through the Phase -1 mapping above in every new manifest.

| Profile | Intended environment | Candidate path | Claim boundary | Current state |
| --- | --- | --- | --- | --- |
| `portable_cpu` | Current laptop and deterministic CI/reference use | ONNX Runtime CPU reference | C1 correctness and small CPU evidence only until measured | Non-executable R0, U3B, U3C `A/A/A/A`, U3D `A/A/A/A/A`, U3F `A/A/A/A/A/A`, and U3H accepted; U3E/U3G are consumed; U3I implementation evidence and U3J design are accepted; runtime-binding authorization/evidence remain pending and non-executable; six resolver inputs, exact bindings, artifacts, and executable validation remain unresolved |
| `local_accelerated` | Owned or authorized stronger laptop | Exact validated Intel, NVIDIA, or AMD provider | Exact machine and workload only | Exact manifest pending |
| `capacity_target` | Declared lab/server or later cluster target | Approved accelerated runtime; optional Kubernetes backend | C10/C50 only from signed exact-hardware evidence | Exact manifest pending |

The historical terms describe capability, not a person or permanent machine.
They do not supersede the shared Phase -1 profile classes.

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

- **Hardware**: `Auto`, `Portable CPU`, `Owned GPU Lab`, `Standalone Server`,
  `Kubernetes Cluster`;
- **Objective**: `Balanced`, `Throughput`, `Latency`;
- **Load**: `Conservative`, `Standard`, `Maximum Validated`.

`Auto` chooses only a shared Phase -1 profile approved for the current immutable
node snapshot. The historical `Local Accelerated` label may be shown as an
alias for `Owned GPU Lab`, but it must not become a separate resolver value.
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

The historical `LAB-LAPTOP-01` R0 record predates the shared Phase -1 inventory
shape and cannot satisfy this input directly. It remains immutable planning
evidence. The separately authorized R1 uses the exact shared schema,
owner-selected freshness and trust policy, and fail-closed expiry semantics.
It supplies only the capability-inventory input and cannot establish admission.

## Planned Manifest Records

| Record | Purpose | State |
| --- | --- | --- |
| `P36-PROFILE-PORTABLE-CPU-R0` | Current laptop/CI reference tuple and conservative bounds | Planning proposal and U3B admission policies accepted; exact compatibility, six resolver inputs, resources, workload values, and generated validation remain pending `P36-G2` |
| `P36-PROFILE-LOCAL-ACCELERATED-R0` | Historical name for the first exact `owned_gpu_lab` tuple | Pending machine selection and `P36-G2`; future manifest uses the shared class |
| `P36-PROFILE-CAPACITY-TARGET-R0` | Historical name for a C10/C50 evidence target resolving to `standalone_server` or `kubernetes_cluster` | Pending target/profile authorization and `P36-G2`; not a deployment profile |

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

All six U3H policies and the U3I/U3J proposal decisions are accepted. The
contract-only runner and generated harness are implemented under U3I, while
U3J remains planning-only. The contract-only U3I implementation evidence is
accepted. One exact runtime-binding attempt was authorized, succeeded, and
consumed its authority. Exact `D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` is
recorded for evidence SHA-256
`4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`,
and the final U3K preparation package is sealed under SHA-256
`4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`.
Runner execution, storage or Defender access, and profile admission remain
  blocked. That package is historical and non-executable because it binds the
  placeholder runner. The handler implementation proposal was sealed under
  package SHA-256
  `EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311`,
  then exactly authorized and consumed. The implemented runner, pure handler,
  isolated Windows adapter, 64-vector verifier, and compatibility evidence are
  sealed under SHA-256
`79F29A6828DDBBE5E0967C4498C753DD19D547714CF8934AEFD93A9D6299B3D7`.
  Exact `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE` is recorded
  under SHA-256
  `06085F3E296B450204FC0E8171314581F40853A11B0AA74161238C390A05B631`.
  This does not activate a profile or authorize PowerShell, runtime, or machine
  access. Only separate validation/runtime-binding planning may proceed. A
  Defender-only proposal remains sequenced after accepted storage evidence.
  The resulting U3M planning package is sealed under SHA-256
  `F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`;
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH` was consumed, and the
  resulting implementation is accepted under
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE`. Neither
  decision activates a capability profile or authorizes PowerShell/runtime
  work.

The owner may review the portable planning record through
`D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE`; acceptance would not activate it.
Planning must still resolve `P36-G1`, the portable proposal's explicit unknown
values, and exact manifests for `owned_gpu_lab` when authorized inventory
exists. Any capacity evidence proposal must select either `standalone_server`
or `kubernetes_cluster`. Any external runtime, dependency, driver, container,
model, or compiled artifact then needs a separate digest/source/path-bound
research authorization before acquisition or execution. `D-P3.6-START`
remains a later explicit gate.

## U3M Generated Validation Status

The source-only U3M implementation authorized by
`D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH` is complete against
authorization digest
`F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`.
Its package digest is
`D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A`.
This supplies generated/static validation infrastructure only; it supplies no
compatibility measurement, workload evidence, runtime binding, profile
eligibility, placement decision, or activation authority. Exact U3M
`D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE` is recorded under
acceptance-record SHA-256
`25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9`.
The separate non-effective U3N package is sealed under SHA-256
`E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E`;
exact `D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH` remains
required before any PowerShell or runtime attempt.

## U3N Failure And U3O Effect On Profiles

The single U3N attempt was consumed and failed closed. Evidence SHA-256 is
`0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42`.
No capability profile became eligible and no placement or activation decision
was produced. The non-effective remediation package SHA-256 is
`17B2142E7F3502724C6653371556DA17F7231D6C56AB0421EC39725556EAA338`;
exact
`D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-AUTH` was
subsequently recorded and consumed for source/static work only. It cannot
activate a profile, execute a model, select hardware, schedule a workload, or
deploy.

## U3O R1 Implementation Effect

The source-only R1 remediation is sealed under harness SHA-256
`F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3`,
evidence SHA-256
`07FF33F19A3C846E69AA8E9C1FD34F9EEBA621BEF1A2424C9173015FB4A0E695`,
and implementation-package SHA-256
`2D9A234A3C1C29276D6D27160849E34DB7440631AC2CD97BEAA650FB48F52E8E`.
Exact
`D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-ACCEPTANCE`
is recorded under acceptance-record SHA-256
`8A6EBD49F71667ECF9961BB02CA891A610497DEBCE23DDDFB9A65FA08F2917EC`.
That acceptance authorized only the non-effective U3P package recorded below.
No profile is eligible or active, and no model placement, scheduling,
acceleration, runtime, or deployment evidence is created.

## U3P R2 Result And U3Q Effect

The U3P package SHA-256 is
`2AFD1D377A68DC35286FE73E58A2B4733BB91BD225BDDBA443472FF76F5603A3`.
Its single authorized attempt was consumed and failed closed as
`result_contract_invalid`; evidence SHA-256 is
`634674D4C50BB63AAF1A73FFEABB804AC51439002787542E76EB66627A9AD3DE`.
The consumed decision was
`D-P3.6-U3P-GENERATED-VALIDATION-RUNTIME-BINDING-R2-AUTH`.
The subsequent non-effective U3Q source-remediation package SHA-256 is
`5EC2889439E81B9F955FE7C3864A0931466458EAFA77C5797E44B24DC9AB0B47`.
Exact
`D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-AUTH`
and `D-P3.6-U3Q-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT` were recorded. The R2
source implementation package SHA-256 is
`2D59FA211DE5DFE331128F189400A28D0D30FAF1BD5C01F077EB6FECF4C236FF`.
Exact
`D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-ACCEPTANCE`
is recorded in acceptance record SHA-256
`32BA42A51029920AE163866A923547CD16054D6C41ECD3C8EC5549B78FB3ED2E`.
Only U3R planning is newly authorized. No profile becomes eligible, active, or
preferred. Every runtime/profile action remains separately gated.

The non-effective U3R R3 authorization package SHA-256 is
`A912EF51629A3E73FFF2ECE7AAB8A7D3017A659F9FB75F5402A90027D4B53D98`.
Exact `D-P3.6-U3R-GENERATED-VALIDATION-RUNTIME-BINDING-R3-AUTH` is pending.
No capability profile becomes resolver-eligible from this package.

U3R was later consumed and failed closed before manifest observation. The U3S
dual-controller source package does not activate a capability profile. Its
authorization package SHA-256 is
`3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC`, and
exact `D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH` was subsequently
recorded. Neither implementation nor acceptance makes a profile
resolver-eligible; separate U3T preflight and later runtime evidence are
required.

The source implementation is now sealed at SHA-256
`484A6FB71216F43A1EAF668DC59091D4FD42EF8543585BFBB588CFCDE089BE30`.
This does not change profile eligibility: the PowerShell source has not run,
Python remains machine-disabled, no runtime or manifest was observed, and all
capability profiles remain non-resolver-eligible. Exact
`D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-ACCEPTANCE` is recorded. The
non-effective U3T H1 package SHA-256 is
`26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2`, with
`D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH` pending. It activates no
profile and grants no runtime or machine authority.

Exact `D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH` is now recorded,
and its source-only result is sealed at SHA-256
`AF16FFBD8214B7509FA634FBF5897B9CD4E0AE54E50B05F95678187E6CF00788`.
This generated/static evidence does not make any capability profile
resolver-eligible. No PowerShell runtime, machine capability, accelerator, or
deployment evidence exists from H1. Exact
`D-P3.6-U3T-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT` is recorded and all 719
Phase 3.6 static tests pass. Exact H1 owner acceptance remains required.
