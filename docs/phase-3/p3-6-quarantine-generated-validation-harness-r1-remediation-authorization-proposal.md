# P3.6 U3O Validation Harness R1 Remediation Authorization Proposal

Status: sealed non-effective proposal; source-only implementation authorization
pending.

## Failure evidence

The single U3N attempt was consumed and failed closed. Exact runtime path,
PowerShell 7 major version, runtime SHA-256, cache-only trust validation, and
all five pre-execution source hashes passed. The exact outer runtime was invoked
once, but it returned no accepted `Aggregate` result. Raw output and exceptions
were intentionally not retained, no retry occurred, and U3K remains blocked.

The sealed records are:

- authorization SHA-256
  `1218C1C35C58AB253D811044046F2EDD364790A6469150248BFFBAB37AAE395B`;
- result SHA-256
  `AD3A8B62105C4DF85E613024C034CECB8DB66C583E7DB49BDA1D4EB09772A8F7`;
- evidence SHA-256
  `0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42`.

## Source analysis

The accepted harness disables automatic module imports with
`$PSModuleAutoLoadingPreference = 'None'` before its first binding check. That
check calls `Get-FileHash`, which Microsoft documents as part of
`Microsoft.PowerShell.Utility`. Microsoft also documents that the `None`
preference disables automatic module imports. The harness does not explicitly
import the utility module.

This is a high-confidence source/runtime dependency conflict, not a claim of
runtime confirmation. The zero-retention failure record cannot exclude another
later PowerShell semantic failure.

Primary sources:

- [PowerShell preference variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables?view=powershell-7.5)
- [Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-7.5)
- [.NET SHA256.HashData](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.sha256.hashdata?view=net-9.0)

## Proposed source-only remediation

The R1 implementation would change only the accepted validation harness and
allowlisted generated/static evidence surfaces:

1. Keep module autoloading disabled.
2. Replace `Get-FileHash` with bounded read-only .NET SHA-256 streaming.
3. Preserve the single explicit pure-handler module import.
4. Add only six allowlisted layer-level failure classifications: binding,
   manifest, parser, contract, handler, and result serialization.
5. Retain no raw exception, output, fixture, identity, or security material.
6. Preserve four modes, four parser files, 20 contract vectors, 64 pure-handler
   vectors, contract-only runner execution, parser-only Windows adapter, and
   all default-deny boundaries.

The accepted vector manifest, runner, handler, and adapter remain byte-exact.
Implementation evidence remains Python-generated/static and non-observational.

## Non-authorization

This package preparation changes no harness source and performs no PowerShell
parsing, import, or execution. It authorizes no runtime observation or retry,
U3P package, machine or storage action, `F:`/`B:`/ACL/probe/cleanup/scanner
work, network action, download, artifact, model, inference, camera/media/data,
container/Kubernetes, profile activation, deployment, or remote Git action.

If exact U3O implementation authorization is later issued, the resulting R1
source and generated/static evidence must still receive separate owner
acceptance. Only then may a new non-effective U3P runtime-retry package be
prepared.
