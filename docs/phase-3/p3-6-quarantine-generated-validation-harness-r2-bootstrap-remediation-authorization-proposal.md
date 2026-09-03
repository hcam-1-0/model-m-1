# P3.6 U3Q Harness R2 Bootstrap Remediation Proposal

Status: sealed non-effective source-only proposal; exact owner authorization
pending.

## Why U3P Failed Closed

The single U3P attempt passed runtime trust, exact-path policy, source binding,
and post-execution identity checks. The harness process then exited with code
`1`, produced zero stdout bytes, and produced 302 bounded stderr bytes. Raw
stderr was intentionally neither inspected nor retained. The result therefore
failed closed as `result_contract_invalid`; the U3P authorization is consumed
and cannot be reused.

Static source inspection identifies a high-confidence bootstrap gap. The
harness sets `PSModuleAutoLoadingPreference=None`, but it later uses fourteen
references to seven commands from `Microsoft.PowerShell.Utility`. The first is
`ConvertFrom-Json`. Its failure trap also calls `ConvertTo-Json` from the same
module, so an unavailable Utility module can prevent both normal execution and
sanitized failure serialization. This mechanism is strongly supported by the
source and Microsoft documentation, but it is not claimed as runtime-confirmed.

## Selected R2 Design

The proposal does not re-enable broad module autoloading. Source-only R2 work
would:

1. Construct the shipped Utility manifest path strictly under
   `$PSHOME\Modules` without reading or searching `PSModulePath`.
2. Classify that exact manifest as a bounded regular non-reparse file.
3. Import exactly seven Utility cmdlets with `Scope Local` and `NoClobber`.
4. Verify exact command names and `Microsoft.PowerShell.Utility` provenance.
5. Set `PSModuleAutoLoadingPreference=None` only after bootstrap succeeds.
6. Use a fixed, module-independent .NET console JSON writer if bootstrap fails.
7. Preserve all 84 generated vectors, Contract-only runner behavior, the
   parser-only Windows adapter boundary, zero retention, and default denial.

The seven allowed Utility cmdlets are `Compare-Object`, `ConvertFrom-Json`,
`ConvertTo-Json`, `ForEach-Object`, `Measure-Object`, `Sort-Object`, and
`Where-Object`.

## Gates

The package requests source and generated/static implementation authority only.
It does not authorize PowerShell parsing, import, or execution; runtime or
hardware observation; a retry; U3R or U3K; machine/storage actions; network;
downloads; models; media/data; containers/Kubernetes; profile activation;
deployment; or remote Git.

After implementation, exact source evidence and a new implementation package
must receive separate owner acceptance. Only then may a separate non-effective
U3R package be prepared to bind the exact runtime Utility manifest and nested
implementation closure. A future runtime attempt would still require its own
digest-bound owner authorization.

## Owner Decision

Pending decision:
`D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-AUTH`.

Use only the exact authorization statement sealed in the package manifest.
Planning, `continue`, and the consumed U3P authorization do not grant this
implementation authority.
