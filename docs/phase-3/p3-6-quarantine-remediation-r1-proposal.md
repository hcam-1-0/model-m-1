# P3.6 Quarantine Remediation R1 Decision Proposal

Status: planning-only decision package. No new attempt, `F:` access, ACL
change, scanner query, scanner execution, installation, download, artifact
access, implementation, deployment, or remote Git action is authorized.

## Why U3E Stopped

The single U3E attempt was consumed and failed closed. `F:` passed the fixed
volume, NTFS, capacity, canonical-path, isolation, and non-reparse checks. The
new exact root inherited write access for a broad well-known principal, so the
ACL gate failed before the 4096-byte probe. The empty root was removed and no
probe content was written or retained.

Defender status metadata was observed, but an exact `MpCmdRun.exe` trust
binding was not produced. ModelScan was unavailable, and the H-CAM passive
inspector remains unimplemented. The scanner chain is therefore incomplete.

## Primary-Source Findings

Microsoft documents a Windows-specific directory creation overload that takes
`DirectorySecurity` and applies it while creating the directory, avoiding a
window where inherited permissions are active. `SetAccessRuleProtection` can
protect the DACL and remove inherited rules.

Microsoft also documents the versioned Defender platform directory and the
`WTD_CACHE_ONLY_URL_RETRIEVAL` WinVerifyTrust flag, which prevents network
retrieval during code-signature verification.

ModelScan 0.8.8 provides JSON reporting and distinct exit codes, but open
upstream issue reports allege false-negative behavior. Those reports are risk
signals rather than independently verified findings. They reinforce the
accepted policy that ModelScan is one mandatory layer beside Defender and the
H-CAM passive inspector, not a standalone proof of safety.

Sources:

- [secure directory creation](https://learn.microsoft.com/en-us/dotnet/api/system.io.directory.createdirectory?view=net-10.0)
- [protected access rules](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.objectsecurity.setaccessruleprotection?view=net-10.0)
- [DirectorySecurity](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.directorysecurity?view=net-9.0)
- [Defender MpCmdRun locations](https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus)
- [cache-only WinVerifyTrust policy](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data)
- [ModelScan](https://github.com/protectai/modelscan)
- [ModelScan 0.8.8 artifacts](https://pypi.org/project/modelscan/0.8.8/)
- [upstream false-negative report](https://github.com/protectai/modelscan/issues/338)

## D-P3.6-U3F-001: Root ACL Provisioning

### A. Protected security-at-create DACL (recommended)

Create the absent root with `DirectorySecurity` already applied, disable
inheritance, and verify the exact canonical DACL before any probe. This avoids
the broad inherited-permission interval that option B would create.

### B. Create then replace ACL

Create under inherited permissions and replace the DACL immediately. This is
simpler but temporarily reproduces the U3E exposure.

### C. Manual owner pre-provisioning

The owner creates and hardens the root outside the attempt. This is less
reproducible and needs separate evidence.

### D. Abandon `F:`

Return to storage selection even though the volume and path passed.

## D-P3.6-U3F-002: Explicit Principals And Rights

### A. Process Modify plus SYSTEM/Admin FullControl (recommended)

Resolve the current process SID in memory, grant it `Modify`, grant LocalSystem
and built-in Administrators `FullControl`, propagate the rules to children,
protect the DACL, and persist only boolean classifications. This is a lab-local
policy; production must bind a service SID, gMSA, or equivalent workload
identity.

### B. Process FullControl

Give all three principals FullControl. This is easier but grants the
interactive account more privilege than required.

### C. Dedicated service SID only

Best production shape, but no exact service identity currently exists on this
laptop.

### D. Owner-supplied identity

Pause until an exact local or domain identity is supplied.

## D-P3.6-U3F-003: Existing Root Handling

### A. Absent root required (recommended)

Any pre-existing file or directory fails before modification. The current
evidence says U3E removed its empty root, but a later attempt must verify
absence again under new authority.

### B. Remediate an existing empty root

Permit ACL replacement after bounded inspection. This changes security on an
object whose origin is not proven.

### C. Owner-confirmed existing root

Accept a separate ownership statement. This is weaker than secure creation
evidence.

### D. Defer

No safe action package can be sealed.

## D-P3.6-U3F-004: Defender Trust Binding

### A. Exact path, SHA-256, cache-only WinVerifyTrust (recommended)

Resolve one documented versioned candidate from `AMProductVersion`, require a
regular non-reparse file, bind its exact path/version/SHA-256, and require
cache-only whole-chain trust verification with no UI and no binary execution.
An unavailable cached chain or revocation result fails closed.

### B. Get-AuthenticodeSignature plus hash

Simpler, but does not encode the same explicit cache-only WinVerifyTrust flags.

### C. Version and hash only

Reproducible but insufficient for publisher trust.

### D. Defer Defender

The storage retry can proceed, but Defender remains unbound.

## D-P3.6-U3F-005: ModelScan Bootstrap Boundary

### A. Separate pinned bootstrap and hostile-fixture package (recommended)

Keep ModelScan out of the retry. A later package must bind the 0.8.8 wheel
SHA-256, full dependency lock, isolated tool environment, JSON and exit-code
contract, and generated hostile fixtures. No model artifact is used for that
bootstrap validation.

### B. Install during the retry

Combines ACL changes, download, dependency resolution, installation, and
scanner binding. This is too broad for the current boundary.

### C. Remove ModelScan

Contradicts accepted U3D policy.

### D. Trust a manual installation

Provides no exact dependency or installation provenance.

## D-P3.6-U3F-006: Retry Scope

### A. Storage remediation plus Defender binding (recommended)

The future one-attempt package may create the secure root, verify its ACL, run
the 4096-byte atomic probe, and bind Defender without executing it. ModelScan,
the passive inspector, artifact acquisition, and runtime work remain separate.

### B. Storage only

Smallest scope, but Defender remains unbound.

### C. Defender only

Leaves storage unbound.

### D. Combine storage, scanner installation, and acquisition

Conflicts with the staged, fail-closed lifecycle.

## Recommended Response

```text
D-P3.6-U3F-001: A
D-P3.6-U3F-002: A
D-P3.6-U3F-003: A
D-P3.6-U3F-004: A
D-P3.6-U3F-005: A
D-P3.6-U3F-006: A
```

Selecting options authorizes only preparation of a new immutable action and
authorization package. It does not authorize another attempt. A later exact
digest-bound acceptance will still be required before any local action.
