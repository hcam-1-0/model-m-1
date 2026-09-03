# P3.6 U3I Runtime Binding R0 Authorization Proposal

Status: proposal prepared; exact owner authorization pending; no runtime
observation or execution performed.

## Purpose

The accepted contract-only transaction runner cannot be included in a final
storage execution package until its exact PowerShell runtime is bound. This
proposal defines one future, separately authorized, sanitized read-only attempt
to bind the runtime file without running it.

The target is deliberately fixed:

- logical node: `LAB-LAPTOP-01`;
- runtime family: PowerShell 7 on Windows;
- exact executable: `C:\Program Files\PowerShell\7\pwsh.exe`;
- exact runner source:
  `tools/phase36_quarantine_transaction_runner.ps1`;
- accepted runner source SHA-256:
  `C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.

Microsoft documents `$Env:ProgramFiles\PowerShell\7` as the default current
PowerShell 7 MSI installation directory and `pwsh.exe` as the PowerShell 7
executable. That supports the fixed candidate but does not prove it exists or
is trusted on this laptop. The future attempt must establish those facts under
separate authority.

## Current Authority

`D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE` accepted only the sealed
contract implementation and generated/static evidence package:

`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`

That acceptance authorizes this proposal. It does not authorize the proposed
observation. The runtime path, installed version, size, SHA-256, and trust state
remain unknown.

## Proposed One-Attempt Transaction

A later exact authorization would permit these serial actions only:

1. Read one UTC start time.
2. Verify the authorization statement, sealed package digest, every core-file
   digest, accepted implementation record, source digest, single-attempt state,
   and 24-hour window.
3. Write the bounded authorization record before runtime-file observation.
4. Canonicalize only the fixed executable path, inspect only its fixed parent
   components, reject reparse points, and require a regular local online file.
5. Read bounded file size, file version, product version, and product-name
   classification; require PowerShell major version 7; hash the exact file with
   SHA-256; detect change during observation.
6. Run cache-only, no-UI, whole-chain-excluding-root `WinVerifyTrust`; export no
   certificate or chain data; close provider state on every outcome.
7. Hash only the accepted repository-relative runner source and require the
   accepted source digest; do not execute it.
8. Write only normalized, bounded authorization, result, and evidence records.

The future transaction allows no PATH, environment, registry, WMI, package-
manager, or directory inventory. It has no alternate-path fallback and no
network retrieval. If the fixed runtime is missing, changed, too large,
untrusted, or unverifiable from cached trust material, the attempt records a
sanitized failure and stops.

## Bounds

- one attempt;
- authorization expires 24 hours after exact owner authorization;
- successful binding evidence is valid for 24 hours;
- 30-second per-action timeout and 120-second total timeout;
- maximum runtime file size: 256 MiB;
- no parallel action and no automatic retry;
- failure consumes the authorization;
- no raw exception, command output, certificate identity, user identity,
  environment, PATH, registry, directory listing, or personal repository path
  is retained.

## Explicit Non-Authorization

This proposal does not authorize:

- execution of `pwsh.exe` or the transaction runner;
- implementation or invocation of machine handlers;
- any `F:`, `B:`, storage, ACL, directory, probe, or cleanup action;
- Defender, ModelScan, or another scanner action;
- network trust retrieval;
- install, update, download, artifact, dependency, model, dataset, driver, or
  container acquisition;
- model loading, inference, validation, benchmark, hardware test, camera,
  media, private data, or Government data;
- profile activation, scheduling, Docker, Kubernetes, deployment, or remote
  Git.

Even a successful future runtime-binding attempt would not authorize runner
execution or storage work. Its exact evidence would need to be sealed and
separately accepted. Only then could a new final U3K storage package be
prepared for another explicit owner authorization.

## Decision

Pending decision:

`D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH`

The exact authorization statement is stored in the sealed machine-readable
package. The statement must include the final package digest. A bare
`continue`, the implementation acceptance, or the U3J storage-design
acceptance is not authority to perform the attempt.

## Primary Sources

- [Install PowerShell 7 on Windows](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows)
- [Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash)
- [FileVersionInfo.ProductVersion](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.fileversioninfo.productversion)
- [WINTRUST_DATA](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data)
- [Path.GetFullPath](https://learn.microsoft.com/en-us/dotnet/api/system.io.path.getfullpath)
- [FileAttributes](https://learn.microsoft.com/en-us/dotnet/api/system.io.fileattributes)
