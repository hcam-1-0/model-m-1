# P3.6 U3N Generated Validation and Runtime Binding R1 Authorization Proposal

Status: sealed non-effective proposal; exact owner authorization pending.

## Preparation authority

`D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE` accepted the exact
U3M source and generated/static evidence package. It authorizes only preparation
of this separate non-effective U3N package. It did not authorize the attempt.

## Exact attempt

U3N proposes one single-use attempt on logical node `LAB-LAPTOP-01`, valid only
within 24 hours of exact digest-bound authorization. A failed or interrupted
attempt consumes the authorization, has no automatic retry, and requires a new
package and owner statement.

The attempt first binds only
`C:\Program Files\PowerShell\7\pwsh.exe`: its fixed parent components must be
local and non-reparse; the file must be regular, bounded to 256 MiB, identify as
PowerShell 7, hash successfully, and pass cache-only, no-UI,
whole-chain-excluding-root trust validation. No alternate runtime discovery,
directory inventory, PATH, registry, WMI, package inventory, hardware
inventory, network retrieval, or trust retrieval is allowed.

Only after the runtime and all accepted source hashes pass may the exact runtime
be invoked once with `-NoLogo`, `-NoProfile`, `-NonInteractive`, and the accepted
harness in `Aggregate` mode. The harness must:

- parse exactly the runner, pure handler, Windows adapter, and harness with zero
  parser errors and without parser-layer execution;
- run exactly 20 runner `Contract` vectors;
- import only the pure-handler module in local scope with its exact four exports
  and run exactly 64 generated vectors;
- keep runner `Storage` and `StorageRequestJson` unreachable;
- treat the Windows adapter as parser-only and never import or execute it;
- retain no raw fixture, child output, exception, identity, or security material;
- report 84 of 84 vectors passed and zero prohibited-action counters.

## Bounds and outputs

The total attempt is bounded to 300 seconds. Parser, contract-vector, handler,
stdout, stderr, result, and evidence limits are fixed by the action spec. Child
execution is noninteractive, hidden, serial, redirected, and killed as a process
tree on timeout. No raw stdout or stderr may be persisted.

Only these future records may be written:

1. `p3-6-quarantine-generated-validation-runtime-binding-r1-authorization.json`
2. `p3-6-quarantine-generated-validation-runtime-binding-r1-result.json`
3. `p3-6-quarantine-generated-validation-runtime-binding-r1-evidence.json`

The authorization record must be committed before runtime observation. Result
and evidence records must be bounded, sanitized, and nonreplacement writes.

## Non-authorization

Preparing this package performs no PowerShell parsing, import, or execution and
does not observe the runtime, hardware, machine, storage, F:, B:, ACL, identity,
probe, cleanup, or scanner state. It performs no network, download, artifact,
model, inference, camera, media, data, container, Kubernetes, deployment, or
remote Git action.

Even successful future U3N execution would only produce evidence. That evidence
must be separately accepted before a new U3K package can be prepared. U3K and
every machine or storage action remain separately gated.
