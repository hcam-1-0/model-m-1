# P3.6 Quarantine Failure Analysis R2 Decision Proposal

Status: planning-only owner decision package. No retry, `F:` access, ACL
change, Defender query, hash or trust action, scanner execution, runner
implementation, installation, download, artifact access, model execution,
validation, deployment, or remote Git action is authorized.

## What U3G Proved

U3G consumed its one authorized attempt and failed closed. It proved that the
candidate volume and path met the bounded policy and that the absent root could
be created with a protected security descriptor at creation. The resulting
DACL had exactly three explicit rules, no inherited rule, and no deny rule.
The SYSTEM and Administrators `FullControl` rules matched. The current-process
`Modify` rule did not match the verifier's exact semantic expectation.

The probe was correctly skipped. The empty attempt-created root was removed,
no probe content was retained, and no storage attestation was issued.

The Defender status action returned some bounded status values but no usable
`AMProductVersion`. Candidate selection, SHA-256, and cache-only
WinVerifyTrust were correctly skipped. No Defender executable or scanner ran.

## Failure Analysis

Microsoft documents `FileSystemRights` as a flags enum and states that
`Synchronize` is automatically set when access is allowed. Microsoft's .NET
reference source also ORs `Synchronize` into an allow access mask. The leading
explanation is therefore that the accepted current-process ACE was returned as
`Modify | Synchronize`, while U3G required a raw `Modify` equality.

This is a high-confidence inference, not a machine-proven fact. U3G
intentionally persisted no raw ACE, SID, access mask, SDDL, or security
descriptor. The next design must test the hypothesis through bounded
normalized booleans rather than retroactively changing the consumed result.

The `broad_write_principal_absent=false` result is also not proof that a fourth
or unauthorized principal existed. U3G recorded exactly three rules and
successfully matched SYSTEM and Administrators. Its broad-principal
classification was coupled to failure of the accepted current-process tuple.
U3H separates principal classification from rights normalization.

Microsoft documents that Windows PowerShell Compatibility in PowerShell 7
uses a background Windows PowerShell 5.1 process, implicit remoting, and proxy
modules. Remote output is serialized into property snapshots. This transport
is a plausible contributor to the incomplete Defender property projection,
but raw output was not retained, so it is not treated as a proven cause.

U3H recommends projecting allowlisted scalar values inside native local
Windows PowerShell 5.1 before serialization. It also adds a fail-closed
fallback based on Microsoft's documented latest versioned Defender platform
directory. Directory order never establishes trust by itself: version
agreement, SHA-256, and cache-only WinVerifyTrust remain mandatory.

Primary sources:

- [FileSystemRights and automatic Synchronize](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.filesystemrights?view=net-10.0)
- [Microsoft .NET reference source](https://github.com/microsoft/referencesource/blob/main/mscorlib/system/security/accesscontrol/filesecurity.cs)
- [Windows PowerShell Compatibility](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_windows_powershell_compatibility?view=powershell-7.6)
- [PowerShell remote output and deserialization](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_remote_output?view=powershell-7.6)
- [Get-MpComputerStatus](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus?view=windowsserver2025-ps)
- [Defender platform updates and versioned location](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-updates)
- [MpCmdRun locations](https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus)

## D-P3.6-U3H-001: Allow-Rights Normalization

### A. Exact `Modify | Synchronize` (recommended)

Require every `Modify` bit plus the automatically added `Synchronize` bit and
no other right. Explicitly reject `ChangePermissions`, `TakeOwnership`,
`FullControl`, generic-all, and unknown bits. This preserves least privilege
while matching documented .NET allow-mask behavior.

### B. Raw `Modify` equality

Retain the U3G comparison. It is expected to fail whenever .NET adds
`Synchronize`.

### C. Required-rights subset

Pass when `Modify` is present even if other rights exist. This could accept
excessive privileges and is not recommended.

### D. Current-process `FullControl`

Avoid the normalization issue by granting more privilege. This weakens the
accepted least-privilege policy.

## D-P3.6-U3H-002: DACL Tuple Verification

### A. Independent normalized tuple checks (recommended)

Require exactly three explicit allow tuples. Compare in-memory SID,
normalized rights, inheritance, propagation, and access type separately.
Calculate unauthorized-principal absence independently from rights matching.
Persist only bounded booleans, never identity or raw ACL data.

### B. Raw SDDL equality

Compare complete descriptor text. This can fail on harmless canonical ordering
and expands sensitive descriptor handling.

### C. Effective access only

Prove that the process can write without proving the absence of broad,
inherited, deny, or excessive rules.

### D. Manual ACL review

Move classification to an operator. This is less reproducible and conflicts
with the sanitized evidence model.

## D-P3.6-U3H-003: Defender Status Transport

### A. Native Windows PowerShell scalar projection (recommended)

For a future separately authorized attempt, bind the exact local Windows
PowerShell 5.1 executable, use `-NoProfile` and `-NonInteractive`, run
`Get-MpComputerStatus` there, verify required property presence and scalar
types there, and return only allowlisted JSON scalars under strict output and
timeout limits. This does not run Defender or perform a scan.

### B. PowerShell 7 compatibility session

Keep the implicit-remoting path associated with U3G's incomplete projection.

### C. CIM-only query

Use a later-researched CIM class. No exact supported class/property contract
is sealed yet.

### D. Defer status metadata

Skip Defender status and leave the binding unresolved.

## D-P3.6-U3H-004: Defender Candidate Fallback

### A. Product version, then bounded latest-directory fallback (recommended)

Use valid native `AMProductVersion` first. If absent, inspect at most 64 direct
regular non-reparse platform directories, parse version basenames, select one
highest version, and require one exact `MpCmdRun.exe` child. The directory and
`FileVersionInfo` versions must agree. Bind SHA-256 and require cache-only
WinVerifyTrust. Any ambiguity or failure stops the path.

### B. `AMProductVersion` only

Fail whenever the property is absent. This is simple but can repeat U3G.

### C. Latest directory without trust

Use directory recency and a hash without publisher trust. This is not
acceptable for the scanner chain.

### D. Prefer Program Files fallback

Bind the operating-system fallback before the current updated platform. This
can select an older inactive binary.

## D-P3.6-U3H-005: Attempt Decomposition

### A. Storage first, Defender separately (recommended)

Prepare a storage-only package and require exact owner authorization. Only
after its evidence is accepted, prepare a Defender-only package requiring a
second exact authorization. Independent failure domains produce clearer
evidence and avoid consuming unrelated authority.

### B. Combined storage and Defender

Repeat U3G's combined shape. It uses fewer decision cycles but couples two
independent failure paths.

### C. Defender first

Avoid `F:` initially but leave the quarantine root unresolved.

### D. Stop local binding

Preserve current evidence and leave the gates blocked.

## D-P3.6-U3H-006: Transaction Runner Reviewability

### A. Content-hashed reviewable runner proposal (recommended)

Require a future package to include a human-reviewable, content-hashed runner
source proposal, exact interpreter/runtime binding, generated-only contract
tests, default-deny action dispatch, bounded outputs, deterministic cleanup,
and explicit failure states. Selecting this option authorizes only preparation
of that proposal. It does not authorize implementation or execution.

### B. Ephemeral in-memory loader

Continue building mechanics only at execution time. This is difficult to
review, reproduce, test, and bind before authorization.

### C. Manual commands

Use an operator checklist. This weakens deterministic cleanup, timeout,
sanitization, and action evidence.

### D. Abstract action specification only

Retain prose and JSON intent without a proposed reviewable runner source. The
gap between reviewed intent and actual execution remains.

## Recommended Response

```text
D-P3.6-U3H-001: A
D-P3.6-U3H-002: A
D-P3.6-U3H-003: A
D-P3.6-U3H-004: A
D-P3.6-U3H-005: A
D-P3.6-U3H-006: A
```

Selecting options authorizes only recording the chosen design and preparing
new non-effective proposals. It does not authorize runner implementation,
another attempt, `F:` or ACL action, Defender access, hashing, WinVerifyTrust,
scanner use, acquisition, models, runtime, validation, or deployment. Each
future machine attempt still requires a new immutable package digest and a new
exact owner authorization.
