# P3.6 U3L Machine Handlers R0 Implementation Authorization Proposal

Decision: `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH`

Status: sealed non-effective owner-authorization proposal pending exact owner
review. This proposal does not authorize implementation, source changes,
PowerShell execution, runner or module execution, Windows-adapter import,
machine access, `F:` access, ACL operations, a storage probe, cleanup, scanners,
downloads, models, deployment, or remote Git.

## Why This Gate Exists

The accepted transaction runner is deliberately contract-only. Its exact
source SHA-256 is
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`,
and all ten `U3K-A01` through `U3K-A10` machine-action cases throw
`P36_MACHINE_HANDLER_NOT_IMPLEMENTED`.

The final U3K preparation package is sealed under SHA-256
`4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`,
but it is intentionally non-effective. `D-P3.6-U3K-STORAGE-R2-AUTH` is not
requestable until exact machine-handler source, generated tests, evidence, and
a current runtime binding are sealed and accepted in a newly generated
executable package.

## Primary-Source Finding

The accepted U3J design named the managed
`FileSystemAclExtensions.CreateDirectory(DirectorySecurity, String)` API for
security at creation. Microsoft documents that this API returns an existing
directory when the target already exists. An absence check followed by this
managed call therefore cannot prove that the current attempt created the root
if another process creates it between those operations.

The proposed implementation corrects that narrow API choice while preserving
the accepted security policy. Microsoft documents that `CreateDirectoryW` can
apply a supplied security descriptor at creation and returns
`ERROR_ALREADY_EXISTS` when the target exists. The implementation must use
that exclusive result, with a non-null `SECURITY_ATTRIBUTES` descriptor, before
it may mark `root_created_by_attempt=true`. A managed existing-directory return,
plain directory creation followed by ACL rewriting, or any fallback is
prohibited.

Primary references:

- [CreateDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createdirectoryw)
- [SECURITY_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/wtypesbase/ns-wtypesbase-security_attributes)
- [Managed CreateDirectory with ACL](https://learn.microsoft.com/en-us/dotnet/api/system.io.filesystemaclextensions.createdirectory?view=net-10.0)
- [SetAccessRuleProtection](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.objectsecurity.setaccessruleprotection?view=net-10.0)
- [FileSystemRights](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.filesystemrights?view=net-10.0)
- [DriveInfo.IsReady](https://learn.microsoft.com/en-us/dotnet/api/system.io.driveinfo.isready?view=net-10.0)
- [Reparse-point operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-operations)
- [FileStream.Flush(Boolean)](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-10.0)
- [MoveFileExW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)

The machine-readable research record contains the complete source-to-constraint
mapping. Documentation review is not runtime validation and makes no claim
about the current state of `LAB-LAPTOP-01` or `F:`.

## Proposed Source Architecture

The proposed implementation has three PowerShell source boundaries and one
Python generated verifier:

1. `tools/phase36_quarantine_transaction_runner.ps1`

   Retains the accepted `Contract` behavior and adds a default-off storage
   orchestration path. It verifies the exact future package, owner statement,
   source hashes, runtime binding, target, action order, limits, and unused
   attempt before importing the Windows adapter or allowing machine access.

2. `tools/phase36_quarantine_machine_handlers.psm1`

   Holds the pure typed state machine for the ten actions. It may classify
   adapter results, enforce order, maintain attempt-owned cleanup state, and
   emit allowlisted reason codes. It may not call machine, filesystem, network,
   registry, process, service, scanner, or environment APIs.

3. `tools/phase36_quarantine_windows_storage_adapter.psm1`

   Is the only direct machine-API boundary. It may expose only the operations
   fixed by the implementation contract. It may not be imported until a later
   exact execution preflight succeeds, and it may not be imported or executed
   during this implementation stage.

4. `tests/test_phase36_quarantine_machine_handlers_generated.py`

   Evaluates 64 deterministic generated vectors against a machine-independent
   reference state machine and performs static source checks. It reads source
   and JSON only. It does not run PowerShell, import either module, access a
   machine path, create temporary probe data, or use the network.

Dynamic action discovery, plugins, environment-defined handlers, reflection
dispatch, command strings, `Invoke-Expression`, shell fallbacks, wildcard or
recursive deletion, and existing-root ACL rewriting are prohibited.

## Exact Ten-Action Boundary

The proposal implements only the accepted action order:

1. `U3K-A01`: bind one UTC start time.
2. `U3K-A02`: verify the exact owner statement, executable package, every core
   hash, source and runtime bindings, unused attempt, target, order, limits,
   output paths, and authorization window before machine access.
3. `U3K-A03`: durably write only the sanitized authorization record before
   `F:` access.
4. `U3K-A04`: read only `IsReady`, `DriveType`, `DriveFormat`, `TotalSize`, and
   `AvailableFreeSpace` for exact `F:`.
5. `U3K-A05`: verify exact canonical path, non-reparse parent, isolation from
   `F:\h cam`, and true candidate absence without directory enumeration.
6. `U3K-A06`: resolve the current process SID in memory and construct the exact
   protected three-rule security descriptor without persisting identity or ACL
   material.
7. `U3K-A07`: use exclusive `CreateDirectoryW` security-at-create semantics;
   `ERROR_ALREADY_EXISTS` fails closed and never triggers cleanup.
8. `U3K-A08`: independently verify protection, rule count, principals, rights,
   inheritance, propagation, access type, no deny or inherited rule, and no
   unauthorized principal.
9. `U3K-A09`: exclusively create 4096 deterministic generated bytes, flush to
   disk, hash-read, perform a same-directory nonreplacement write-through
   rename, hash-read again, and delete all attempt-created probe content.
10. `U3K-A10`: write bounded canonical sanitized result and evidence records
    only to the two exact repository paths.

No action may run in parallel. Any mismatch, unknown action, invalid transition,
deadline failure, raw-output request, cleanup ambiguity, or unallowlisted API
must fail closed without retry or authority expansion.

## Generated Test Boundary

The 64-vector plan contains 56 action-specific vectors and eight cross-cutting
vectors. It covers exact successes, package and source mismatches, expired or
consumed authority, path and reparse rejection, DACL tuple independence,
exclusive-creation races, probe flush and hash failures, bounded cleanup,
sanitization, timeout state, default-deny ordering, Windows-adapter isolation,
and continuing non-authorization.

Exact acceptance would authorize the Python generated reference verifier and
static source checks only. It would not authorize a PowerShell parser, the
runner, either PowerShell module, or the Windows adapter to execute or import.
The implementation evidence must explicitly record those operations as not
performed.

## What Exact Acceptance Would Authorize

Exact acceptance of the package digest would authorize only:

- modification of the existing runner and creation of the two exact
  PowerShell modules;
- creation and execution of the exact generated-only Python verifier;
- synchronization of Phase 3.6 package-integrity tests and canonical ledgers;
- non-observational implementation evidence and a sealed exact-source package;
  and
- the exclusive `CreateDirectoryW` correction specified by this proposal.

It would not authorize PowerShell or source execution, machine observation,
runtime binding, `F:` access, directory creation, ACL work, probe or cleanup,
Defender or scanner work, artifacts or models, inference, media or data,
containers or Kubernetes, deployment, or remote Git.

## Required Later Gates

After implementation, all exact source and evidence hashes require separate
owner acceptance. Any generated PowerShell test requires a separate current
runtime-bound authorization if it is later considered necessary. A future
storage attempt then requires a newly generated executable U3K package that
binds the corrected action specification, exact accepted sources and tests,
and a fresh accepted runtime binding. Only that package can receive a separate
`D-P3.6-U3K-STORAGE-R2-AUTH`.

## Exact Owner Statement Template

Replace `<MACHINE_HANDLER_PROPOSAL_PACKAGE_DIGEST_SHA256>` with the exact sealed
package digest:

```text
D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH: I, mayank-admin, authorize implementation only of the P3.6 U3K machine-handlers R0 proposal against package digest <MACHINE_HANDLER_PROPOSAL_PACKAGE_DIGEST_SHA256>. Implementation is limited to the exact source, generated-Python-test, evidence, package, ledger, documentation, and compatibility-test paths allowlisted by that package. It must retain static ten-action default-deny dispatch, isolate all direct machine APIs in the exact Windows adapter, use exclusive CreateDirectoryW security-at-create semantics, pass all 64 generated-only vectors and the full Phase 3.6 suite, and seal exact source and evidence hashes for separate acceptance. This authorizes generated Python reference and static tests only. It does not authorize PowerShell, runner, module, or Windows-adapter execution or import; runtime, hardware, storage, F:, ACL, probe, cleanup, Defender/scanners, downloads, artifacts, models, inference, cameras/media/data, containers/Kubernetes, deployment, or remote Git. Any execution requires a later current runtime-bound executable U3K package and separate digest-bound D-P3.6-U3K-STORAGE-R2-AUTH.
```

`Continue`, any prior acceptance, or the existence of this package cannot be
interpreted as machine-handler implementation or execution authority.
