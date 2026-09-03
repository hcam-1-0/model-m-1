# P3.6 U3M Generated Validation And Runtime Binding R1 Plan

Status: planning package prepared; source-only harness implementation
authorization pending; no PowerShell or runtime action performed.

## Purpose

The accepted U3L implementation gives H-CAM three exact PowerShell sources: the
transaction runner, pure machine-handler state machine, and isolated Windows
adapter. Generated Python and static evidence passed, but PowerShell has never
parsed, imported, or executed these current sources. The prior runtime binding
is also expired and binds an older placeholder runner.

This plan closes those gaps without combining planning, implementation,
execution, runtime observation, and storage into one authority. It introduces
two independently accepted stages before a new U3K storage package can even be
considered.

## Accepted Inputs

| Source | Accepted SHA-256 | Future validation role |
|---|---|---|
| `tools/phase36_quarantine_transaction_runner.ps1` | `22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A` | Parse and run only `Contract` mode |
| `tools/phase36_quarantine_machine_handlers.psm1` | `41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721` | Parse, import locally, and run pure generated transitions |
| `tools/phase36_quarantine_windows_storage_adapter.psm1` | `232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9` | Parse only; never import or execute |

These hashes are accepted by
`D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE` and package SHA-256
`79F29A6828DDBBE5E0967C4498C753DD19D547714CF8934AEFD93A9D6299B3D7`.
This plan does not mutate or supersede that package.

## Why Two Gates Are Required

The validation harness does not exist yet. An execution package cannot safely
authorize an unsealed future script. The sequence is therefore:

1. `U3M-G1`: separately authorize source-only harness and generated-vector
   implementation. Python static checks may run, but PowerShell may not parse,
   import, or execute.
2. `U3M-G2`: separately accept the exact harness, fixtures, tests, and
   non-observational evidence package.
3. `U3N-G1`: prepare and separately authorize one attempt that first binds the
   exact PowerShell runtime, then performs bounded parser and generated runtime
   validation against exact accepted hashes.
4. `U3N-G2`: separately accept the sanitized runtime-binding and validation
   evidence.
5. Only then prepare a new U3K package. Storage execution still requires a
   separate digest-bound `D-P3.6-U3K-STORAGE-R2-AUTH`.

A bare `continue`, this planning package, or U3L acceptance cannot skip a gate.

## Future Validation Layers

### L1: Parser

The future authorized harness will call Microsoft's
[`Parser.ParseFile`](https://learn.microsoft.com/en-us/dotnet/api/system.management.automation.language.parser.parsefile?view=powershellsdk-7.4.0)
for the exact runner, pure handler, Windows adapter, and accepted harness. It
must record only role, hash, parse status, and error count. Parsing must not be
reported as execution evidence.

### L2: Runner Contract Mode

The exact runtime will invoke the runner with `-Mode Contract` for all twenty
sealed generated contract vectors. Every child process must use `-NoLogo`,
`-NoProfile`, and `-NonInteractive`, whose behavior is documented in
Microsoft's [`about_Pwsh`](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_pwsh?view=powershell-7.5).

`Storage` mode, `StorageRequestJson`, adapter import, `F:`, and machine access
are prohibited. The harness must reject any command line containing those
inputs.

### L3: Pure Handler Module

Only the exact pure-handler module may be imported. The future harness must use
an exact file path, `-Scope Local`, `-NoClobber`, and an exact four-function
allowlist. Microsoft documents these controls in
[`Import-Module`](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/import-module?view=powershell-7.5).

The 64 generated transition vectors operate on symbolic, in-memory state and
fake outcomes. They may not import or call the Windows adapter and may not use
filesystem, identity, ACL, process, registry, WMI, service, scanner, network,
environment-inventory, or download APIs.

### L4: Aggregate Evidence

Only counts, hashes, stable reason codes, timing buckets, and zero-access
booleans may be retained. Raw vectors, process output, stderr, exceptions,
identities, paths outside the declared constants, security descriptors, and
machine details are prohibited.

## Fresh Runtime Binding

The historical runtime-binding acceptance has SHA-256
`F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E`.
It expired and binds runner SHA-256
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`,
so it cannot apply to the current runner.

The later U3N package must bind only
`C:\Program Files\PowerShell\7\pwsh.exe` on logical node `LAB-LAPTOP-01`.
Before any validation execution, one separately authorized attempt must verify
the exact path and fixed parents, non-reparse regular-file status, bounded size,
version classification, full SHA-256, and cache-only no-UI whole-chain trust.
It may not discover an alternate runtime, query PATH, registry, WMI, package
managers, or directories, or retrieve trust material over the network.

## Process Bounds

The later process design requires `UseShellExecute=false`, redirected bounded
stdout/stderr, no window, no profile, no interaction, per-layer deadlines, one
serial attempt, and no retry. Microsoft documents that redirected standard
output requires `UseShellExecute=false` in
[`RedirectStandardOutput`](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.redirectstandardoutput?view=net-10.0),
and explains direct executable creation in
[`UseShellExecute`](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.useshellexecute?view=netframework-4.8.1).

The U3N attempt is not authorized by this plan. Its final executable path,
runtime hash, harness hash, source hashes, vectors, timeouts, outputs, and owner
statement must be sealed in a new package first.

## Current Decision

The next requestable decision is:

`D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH`

Its exact statement is stored in the sealed machine-readable package. If
accepted, it permits only source-only implementation, generated JSON fixtures,
Python reference/static tests, evidence, package sealing, and documentation
synchronization. It does not permit PowerShell parsing, import, execution, or
runtime observation.

## Explicit Non-Authorization

This planning package does not authorize:

- creating or changing the harness, fixtures, tests, or accepted source files;
- parsing, importing, or executing PowerShell;
- invoking runner `Contract` or `Storage` mode;
- importing or calling the pure handler or Windows adapter;
- observing runtime, hardware, identity, storage, `F:`, ACL, probes, cleanup,
  Defender, ModelScan, or another scanner;
- network access by the future harness, downloads, artifacts, dependencies,
  models, datasets, inference, cameras, media, private data, or Government data;
- containers, Docker, Kubernetes, profile activation, deployment, or remote
  Git.

`P36-G1`, `P36-G2`, `P36-G4`, and `P36-G5` remain blocked.
