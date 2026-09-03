# P3.6 Quarantine Remediation R1 Authorization Proposal

Decision: `D-P3.6-U3G-BINDING-R1-AUTH`

Status: sealed non-effective owner-authorization package pending exact owner
review. This document is not authority to access `F:`, create or modify a
directory or ACL, query or hash Defender, invoke WinVerifyTrust, install or run
a scanner, download anything, access an artifact, execute a model, implement
product code, deploy, or use remote Git.

## Accepted Policy

`mayank-admin` selected `A/A/A/A/A/A` for `D-P3.6-U3F-001` through `006`
against decision-package digest
`9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`.

Those selections authorize preparation of this exact package only. They bind:

- protected security applied while creating the absent directory;
- current-process `Modify`, LocalSystem `FullControl`, and built-in
  Administrators `FullControl`, with child inheritance and no other ACE;
- fail-before-modification behavior if the candidate root already exists;
- exact Defender path/version/size/SHA-256 plus cache-only WinVerifyTrust;
- a separate future ModelScan bootstrap and hostile-fixture package; and
- one future retry limited to storage remediation and Defender binding.

They do not authorize the retry. Exact acceptance of this new package digest is
still required.

## Consumed U3E Evidence

U3E package digest
`9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`
was accepted and its only attempt was consumed. The fixed NTFS volume, capacity,
canonical path, isolation, and non-reparse checks passed. The new root inherited
a broad-write ACE, so the probe was skipped and the attempt-created empty root
was removed. Defender status metadata was observed, but no binary candidate was
evaluated. ModelScan was unavailable and the passive inspector was not
implemented.

U3G does not retry the inherited-ACL design. It requires security at creation
and prohibits a plain create-then-rewrite fallback.

## Exact Target And Bounds

| Boundary | Exact value |
| --- | --- |
| Logical node | `LAB-LAPTOP-01` |
| Candidate volume | `F:` only |
| Candidate root | `F:\HCAM-Quarantine` only |
| Excluded project path | `F:\h cam` |
| Prohibited volume | `B:` |
| Initial root state | Absent; any existing object fails without modification |
| Volume | Ready, fixed, NTFS/ReFS |
| Free-space floor | At least 5 GiB and at least 15% |
| Attempts | One |
| Acceptance window | 24 hours |
| Per-action timeout | 30 seconds |
| Total timeout | 180 seconds |
| Probe | One deterministic generated 4096-byte probe with zero content retention |
| Defender candidate | One direct version-matched `MpCmdRun.exe`, at most 128 MiB |
| Defender directory bound | At most 64 direct platform directories, no recursion |
| Network | Disabled |
| Retry | None |

## Exact DACL

The future attempt may resolve `WindowsIdentity.GetCurrent().User` only in
process memory. It may not translate or persist the account name or SID.

The in-memory `DirectorySecurity` descriptor must call
`SetAccessRuleProtection(true, false)` and contain only these explicit allow
rules:

| Principal | Rights | Inheritance |
| --- | --- | --- |
| Current process SID | `Modify` | Container and object inherit |
| LocalSystem (`S-1-5-18`) | `FullControl` | Container and object inherit |
| Built-in Administrators (`S-1-5-32-544`) | `FullControl` | Container and object inherit |

The exact root may be created only through
`FileSystemAclExtensions.CreateDirectory(DirectorySecurity, String)`. The
attempt must fail if that security-at-create API is unavailable. It may not
create the directory normally and replace the ACL afterward.

Before the probe, the attempt must verify that the DACL is protected, has no
inherited or deny ACE, has exactly the three accepted semantic rules and flags,
and contains no broad-write principal. Only boolean policy results may be
persisted; raw ACLs, SIDs, account names, and security descriptors are
prohibited.

Microsoft documents that its security-aware directory creation API applies the
security descriptor when the directory is created, avoiding pre-security
access. Microsoft also documents that protected access rules cannot be changed
through parent inheritance and that `preserveInheritance=false` removes
inherited rules.

Sources:

- [security-aware directory creation](https://learn.microsoft.com/en-us/dotnet/api/system.io.filesystemaclextensions.createdirectory?view=net-10.0)
- [Directory.CreateDirectory security overload](https://learn.microsoft.com/en-us/dotnet/api/system.io.directory.createdirectory?view=net-10.0)
- [protected access rules](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.objectsecurity.setaccessruleprotection?view=net-10.0)

## Atomic Storage Probe

Only after every storage and DACL prerequisite passes, the attempt may:

1. Fail if either exact probe path already exists.
2. Exclusively create `.hcam-storage-attestation.partial`.
3. Write exactly 4096 deterministic generated non-secret, non-media bytes.
4. Flush to disk, close, read back, and compare SHA-256.
5. Atomically rename to `.hcam-storage-attestation.verified`.
6. Read back and compare again.
7. Delete the verified probe.

No other file may be read or written. Probe content retention is zero. If the
storage path succeeds, the exact empty hardened root may remain. If storage
fails, the root may be removed only when this attempt created it and it is
empty. Cleanup failure leaves the root ineligible and requires manual review
under separate authority.

## Defender Binding

The attempt may invoke `Get-MpComputerStatus` once and retain only product,
engine, signature, signature-update time, antivirus-enabled, and real-time
protection-enabled fields. Threat history, exclusions, preferences, quarantine,
events, scans, remediation, and updates are prohibited.

Microsoft documents the preferred current `MpCmdRun.exe` location under the
versioned `%ProgramData%\Microsoft\Windows Defender\Platform` directory. U3G
may inspect at most 64 direct, non-reparse version directories and must resolve
exactly one basename equal to the observed `AMProductVersion` or that version
plus a decimal suffix. No recursion or `Program Files` fallback is allowed.

The exact candidate must be a regular non-reparse file, at most 128 MiB, whose
normalized product version matches the current `AMProductVersion`. The attempt
may bind its exact system path, size, file version, product version, and
SHA-256. It may not invoke the executable.

For that file only, an exact process-memory interop declaration may call
WinVerifyTrust using:

- `WINTRUST_ACTION_GENERIC_VERIFY_V2`;
- `WTD_UI_NONE`;
- `WTD_REVOKE_WHOLECHAIN`;
- `WTD_CHOICE_FILE`;
- `WTD_STATEACTION_VERIFY`, followed by `WTD_STATEACTION_CLOSE`; and
- `WTD_CACHE_ONLY_URL_RETRIEVAL`.

Only `ERROR_SUCCESS` is accepted. Missing cached chain or revocation data fails
closed. No source or helper assembly may be retained, no UI may appear, and raw
certificate, chain, subject, issuer, serial, thumbprint, and error text are not
persisted.

Sources:

- [documented Defender command-line locations](https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus)
- [WINTRUST_DATA cache-only and whole-chain policy](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data)

## Ordered Actions

The future attempt is limited to `U3G-A01` through `U3G-A13`:

1. Bind UTC start time.
2. Verify exact owner authorization, package/core hashes, U3F acceptance, use
   window, and unconsumed state.
3. Write the sanitized authorization record before machine access.
4. Re-attest bounded `F:` volume metadata.
5. Verify canonical path, isolation, non-reparse state, and exact absence.
6. Construct the exact DACL in memory.
7. Create the exact root with security already applied.
8. Verify only sanitized DACL policy booleans.
9. Run and clean the exact atomic probe.
10. Read bounded Defender status metadata.
11. Resolve, version-check, size-check, and hash one exact candidate.
12. Apply cache-only WinVerifyTrust and close its state.
13. Write sanitized result and evidence records.

Storage and Defender are reported independently. Passing either does not turn
the scanner chain ready: ModelScan and the H-CAM passive inspector are still
missing. The attempt cannot authorize acquisition, model loading, validation,
profile activation, or deployment.

## Exact Outputs

If authorized, exactly three records may be written:

- `contracts/phase-3/p3-6-quarantine-remediation-r1-authorization.json` before
  machine access;
- `contracts/phase-3/p3-6-quarantine-remediation-r1-result.json`; and
- `contracts/phase-3/p3-6-quarantine-remediation-r1-evidence.json`.

The authorization record contains no observed machine facts. Result and
evidence records are allowlisted and sanitized. No raw exception, command
output, user identity, SID, ACL, certificate chain, device identifier, network
address, secret, or personal path may be retained.

## Continuing Prohibitions

Even exact acceptance does not authorize:

- access to `B:`, `F:\h cam`, another volume, or another `F:` path;
- changing or taking ownership of an existing candidate root;
- Defender, ModelScan, or any other scanner execution;
- scans, remediation, updates, configuration changes, or security-intelligence
  changes;
- ModelScan query, installation, import, execution, or fixture bootstrap;
- downloads, dependencies, model or dataset acquisition, or artifact access;
- checkpoint loading, unpickling, conversion, inference, calibration,
  validation, benchmarking, or hardware testing;
- cameras, streams, media, private data, or Government data;
- Docker, Kubernetes, deployment, profile activation, product implementation,
  or remote Git.

Failure consumes the authorization. There is no automatic retry.

## Exact Owner Authorization Template

The final package digest will replace `<PACKAGE_DIGEST_SHA256>`:

```text
D-P3.6-U3G-BINDING-R1-AUTH: I, mayank-admin, authorize one local remediation and binding attempt against package digest <PACKAGE_DIGEST_SHA256> within 24 hours for exact candidate root F:\HCAM-Quarantine. The attempt may verify the exact package and write its authorization record; query only F: readiness, fixed-drive type, NTFS/ReFS filesystem, total and free capacity, and exact canonical/reparse/absence properties; resolve the current process SID only in memory; create only the absent F:\HCAM-Quarantine root with the exact protected DACL granting current-process Modify and LocalSystem/Administrators FullControl; verify only sanitized DACL booleans; perform and clean one 4096-byte atomic probe; query bounded Defender status; inspect at most 64 direct versioned platform directories; hash and inspect one version-matched regular non-reparse MpCmdRun.exe of at most 128 MiB; perform cache-only, no-UI, whole-chain WinVerifyTrust without executing the binary; and write only the exact sanitized result and evidence records. Failure consumes the authorization and requires a new digest-bound authorization. This does not authorize any existing-root ACL change, any other path or volume, B:, F:\h cam, Defender or other scanner execution, scan, remediation, update or configuration change, ModelScan query/install/import/execution, downloads, artifact acquisition, checkpoint loading, inference, validation, hardware testing, media/data, containers/Kubernetes, product implementation, deployment, or remote Git.
```

No shortened statement, `continue`, prior U3E authority, or U3F selection may
be interpreted as U3G authorization.
