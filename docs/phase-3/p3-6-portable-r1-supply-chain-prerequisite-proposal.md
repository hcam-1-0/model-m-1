# P3.6 Portable R1 Supply-Chain Prerequisite Proposal R0

Status: sealed planning proposal pending five independent owner selections. It
is not an authorization to inspect storage or installed software, create a
directory, install or run a scanner, download an artifact, load a checkpoint,
execute a model, calibrate, validate, implement, or deploy.

Planning authority: `D-P3.6-PLAN-AUTH`.

The proposal follows the accepted U3C `A/A/A/A` policy and prepares only the
prerequisites for a future immutable R1 artifact and supply-chain review. It
does not prepare or authorize the R1 acquisition itself.

## Why This Package Is Required

The exact three-candidate metadata package is accepted, but the physical
quarantine root and exact scanner commands remain unresolved. Historical
sanitized evidence marked `C:`, `E:`, and `F:` ineligible under the current
free-space policy, and `B:` is owner prohibited because it is RaiDrive/Google
Drive. That historical observation is not authority to query or use any drive
now.

The accepted compatibility lifecycle requires:

1. `R0`: planning and owner policy;
2. `R1`: immutable artifact and supply-chain review without model loading;
3. `R2`: separately authorized generated-only non-promotional calibration;
4. `R3`: separately authorized held-out validation; and
5. `R4`: eligible or rejected only after every resolver input and hard gate
   passes.

This document narrows the transition from `R0` toward a possible `R1` without
crossing it.

## Primary-Source Findings

Microsoft documents that `MpCmdRun.exe` supports custom file scanning,
`-DisableRemediation`, and `-ReturnHR`. Its ordinary zero return can also mean
malware was successfully remediated, so a future H-CAM binding cannot treat
exit zero alone as clean. The selected design disables remediation and requires
an exact version, exact command, HRESULT, and bounded-output interpretation.

Protect AI documents ModelScan as a static model-serialization scanner that
does not framework-load the model. Its CLI defines exit codes `0` through `4`;
the proposed policy accepts only `0` plus a valid complete JSON report with no
findings, skips, or unsupported target.

PyTorch explicitly warns that `torch.load` uses an unpickler and that data from
an untrusted source must not be loaded. `weights_only=True` narrows unpickling,
but this proposal does not use it as a substitute for passive R1 review.

CycloneDX ML-BOM provides a standard model-component inventory for identity,
provenance, licenses, frameworks, and lifecycle context. R1 therefore requires
a CycloneDX 1.6 ML-BOM in addition to scanner reports and hashes.

Sources:

- [Microsoft Defender MpCmdRun reference](https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus)
- [Protect AI ModelScan](https://github.com/protectai/modelscan)
- [PyTorch torch.load security warning](https://docs.pytorch.org/docs/2.13/generated/torch.load.html)
- [OWASP CycloneDX ML-BOM guide](https://cyclonedx.org/guides/OWASP-CycloneDX-Authoritative-Guide-to-AI-ML-BOM-en.pdf)

## Recommended Storage Policy

Option `A` binds no drive or path now. A later, separately authorized,
single-attempt attestation must prove an owner-supplied root is:

- on an exact local fixed physical NTFS or ReFS volume;
- outside Git worktrees, cloud-sync roots, network shares, mapped network
  drives, RaiDrive, and broadly shared locations;
- free of symlink, junction, mount-point, or other reparse components;
- capable of exclusive creation, fsync, readback, and atomic rename;
- at least 5 GiB free and at least 15 percent free after reserved headroom; and
- no more than 60 minutes old when an exact R1 authorization is issued.

Both space thresholds must pass. `B:` remains prohibited. `F:` receives no
special permission; it can be considered only if a later exact check passes
the same rules and the owner selects a policy that allows it.

No storage query, directory creation, write probe, or cleanup is authorized by
this proposal.

## Recommended Scanner Chain

Option `A` requires three independent, versioned layers:

1. Microsoft Defender custom scan with remediation disabled;
2. pinned Protect AI ModelScan static serialization scan; and
3. an H-CAM passive structure inspector that uses bounded header/archive/pickle
   opcode inspection without extraction, unpickling, framework import, model
   construction, GPU access, or network access.

The exact Defender platform, security-intelligence version, executable, and
command remain unresolved. ModelScan `0.8.8` is only a candidate from the
official release record; its exact package/wheel digest, executable, isolated
runtime, and command remain unresolved. The H-CAM inspector is not implemented
or authorized.

All three bindings require later review. This proposal neither queries whether
they are installed nor installs or executes them.

## Recommended Verdict Policy

Option `A` passes only when exact source/size/identity checks, SHA-256, all three
scanner layers, license/lineage/provenance, and CycloneDX ML-BOM evidence are
complete and clean.

Any detection at any severity, unsupported or skipped target, timeout, crash,
malformed or truncated report, version drift, ambiguous Defender result,
source/size/hash mismatch, unsafe archive or pickle structure, or missing
supply-chain field rejects the artifact. There is no manual override of a hard
failure. A rejected object remains sealed in quarantine until a separate exact
cleanup decision authorizes deletion.

Scanner success is not proof that an artifact is safe, compatible, accurate,
or promotable. It is one required R1 supply-chain input.

## Recommended Acquisition Lifecycle

Option `A` requires one artifact at a time:

1. revalidate fresh storage and scanner bindings;
2. create an exclusive `.partial` object;
3. stream only from the exact allowlisted HTTPS source with proxies,
   credentials, and unapproved redirects disabled;
4. enforce expected size while streaming;
5. fsync, close, hash, and verify publisher identity metadata;
6. run every passive scanner layer;
7. emit bounded reports, provenance, license, SBOM, and ML-BOM evidence; and
8. atomically seal an accepted or rejected R1 state.

There is no parallel acquisition, direct write to final names, automatic
retry, automatic deletion, or acquisition of source code, dependencies,
datasets, containers, alternate weights, or companion artifacts.

## R1 And R2 Separation

Option `A` keeps R1 passive. R1 may acquire, hash, scan, and document exact
objects only after a separate digest-bound authorization. R1 must never call
`torch.load`, unpickle, import a model framework, construct a model, export,
convert, infer, calibrate, validate, benchmark, admit, activate, or promote.

A future R2 would require accepted R1 digests, a separate generated-only
network-denied runtime authorization, exact runtime/provider/precision and
pipeline contracts, accepted U3C workload dimensions, resource gates, and zero
raw tensor/output retention. R2 would remain non-promotional. R3 held-out
validation would still require another package and authority.

## Owner Decisions

### D-P3.6-U3D-001: Storage root and attestation

- `A` recommended: owner-supplied exact local root plus separate fresh
  single-attempt attestation.
- `B`: prefer `F:` after it passes the same fresh checks.
- `C`: permit exact owner-owned encrypted removable storage with additional
  custody evidence.
- `D`: defer.

### D-P3.6-U3D-002: Scanner chain

- `A` recommended: Defender plus ModelScan plus passive structure inspector.
- `B`: Defender plus passive inspector.
- `C`: ModelScan plus passive inspector.
- `D`: defer.

### D-P3.6-U3D-003: Verdict policy

- `A` recommended: every layer clean, supported, complete, and fail closed.
- `B`: block only critical/high findings.
- `C`: permit manual owner override.
- `D`: informational scanning only.

### D-P3.6-U3D-004: Acquisition lifecycle

- `A` recommended: sequential partial, hash, scan, ML-BOM, atomic seal.
- `B`: parallel bounded acquisition.
- `C`: direct final-name acquisition.
- `D`: defer.

### D-P3.6-U3D-005: R1/R2 separation

- `A` recommended: immutable passive R1 before separately authorized R2.
- `B`: allow weights-only loading in R1.
- `C`: combine R1 acquisition and R2 calibration.
- `D`: defer.

Recommended selection: `A/A/A/A/A`.

## Current Gate Effect

The proposal changes no hard gate:

- `P36-G1`: blocked;
- `P36-G2`: blocked;
- `P36-G4`: blocked; and
- `P36-G5`: blocked.

Owner acceptance of U3D would select planning policy only. It would not bind a
physical root, attest storage, bind or run scanners, authorize artifact
acquisition, create R1 evidence, authorize R2, make a profile resolver-eligible,
or permit implementation or deployment.
