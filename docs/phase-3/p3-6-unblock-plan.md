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

### P36-U1: Sanitized Current-Laptop Inventory

Decision required: `D-P3.6-INVENTORY-R0-AUTH`.

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

This can supply the exact factual input for the `portable_cpu` manifest. It
does not by itself pass `P36-G2` or authorize OpenVINO execution.

### P36-U2: Exact Model Research Proposal

Current public official-source metadata research can continue under
`D-P3.6-PLAN-AUTH`. The output must identify, without downloading:

- exact source revision and candidate checkpoint/release for `DET-E1`,
  `DET-B1`, and `DET-A1`;
- publisher URL, expected filename, declared size where available, license,
  training-lineage statement, model card, export/runtime path, and expected
  artifact type;
- exact bounded URLs, hosts, size ceilings, quarantine paths, passive
  inspection, malware scan, SBOM, license, and evidence actions for a later
  research authorization;
- unresolved facts that keep a candidate blocked.

No model, source archive, dependency, dataset, or container may be downloaded
until a later `D-P3.6-MODEL-RESEARCH-R0-AUTH` accepts that exact proposal.
No candidate can be promoted from upstream metrics alone.

### P36-U3: Exact Capability Profiles

Prepare three immutable proposals:

1. `P36-PROFILE-PORTABLE-CPU-R0` from authorized sanitized inventory;
2. `P36-PROFILE-LOCAL-ACCELERATED-R0` from a similarly sanitized inventory
   supplied from the owned/authorized stronger laptop;
3. `P36-PROFILE-CAPACITY-TARGET-R0`, or an explicit deferral that narrows P3.6
   to C1 and forbids C10/C50 claims.

Each record must bind the exact runtime/provider/precision/decoder candidates,
resource bounds, generated workload, objective modes, rollback path, evidence
expiry, and owner state. Unknown values keep the profile blocked.

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

## Immediate Owner Decision

The next narrow decision is:

```text
D-P3.6-INVENTORY-R0-AUTH: Authorize sanitized read-only hardware, OS, display
driver, and already-installed runtime inventory on LAB-LAPTOP-01 only. No
network, installs, downloads, containers, Kubernetes, models, inference,
performance/stress/thermal tests, media/data access, deployment, or remote Git.
Exclude hostname, user, serials, MAC/IP addresses, personal paths, and raw
device identifiers.
```

This decision does not authorize collaborator-machine access. A collaborator
may later supply an independently generated sanitized record, or a separate
exact authority can cover an owned and explicitly identified machine.
