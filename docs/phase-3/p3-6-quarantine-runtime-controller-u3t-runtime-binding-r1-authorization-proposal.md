# P3.6 U3T Runtime-Controller Preflight R1 Authorization Proposal

## Status

- Non-effective planning package only.
- Exact owner authorization is pending.
- No runtime, parent component, manifest, module, hardware, or machine path was
  observed.
- No PowerShell parser, import, dot-source, or execution occurred.
- No U3T R1 attempt, retry, or U3K work is authorized.

## Preparation Authority

Exact
`D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-ACCEPTANCE` is recorded in
acceptance record SHA-256
`7868C38EAF59595A72AC61D209EA398D3477237D750F234B8F9E5712F0AA9AB3`.
It accepts H1 source/generated-static evidence and authorizes preparation only
of this separate R1 proposal.

## Accepted Inputs

- H1 implementation package SHA-256:
  `AF16FFBD8214B7509FA634FBF5897B9CD4E0AE54E50B05F95678187E6CF00788`
- H1 harness SHA-256:
  `69CBF4637A22BB7859ED07D19804C8576D76FB1270FF58D0D182EED2592FCE7B`
- H1 vector manifest SHA-256:
  `394A4564D54B531EBBC7C16BEA6F66D0D41DEDA757E5E979C796B350462DAB4F`
- Authoritative PowerShell controller SHA-256:
  `78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB`
- Controller contract SHA-256:
  `3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E`
- Controller vector manifest SHA-256:
  `31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B`

These files remain immutable. This proposal authorizes no source changes.

## Proposed Future Attempt

The future decision is `D-P3.6-U3T-RUNTIME-BINDING-R1-AUTH`. It would permit
at most one attempt on logical node `LAB-LAPTOP-01` during a 24-hour window.
Failure consumes the authorization; there is no automatic retry.

The only runtime candidate is
`C:\Program Files\PowerShell\7\pwsh.exe`. A future authorized attempt must
classify that exact regular non-reparse file and only its three fixed parent
components. It may bind bounded size, version, SHA-256, and cache-only no-UI
whole-chain-excluding-root trust without retrieval. No alternate discovery,
directory inventory, `PATH`, `PSModulePath`, registry, WMI, package, module, or
hardware query is permitted.

Only after the authorization, runtime, parent, and accepted source bindings all
pass may the exact runtime invoke the accepted H1 harness once with `NoLogo`,
`NoProfile`, and `NonInteractive`. The process is limited to 30 seconds,
16 KiB stdout, zero stderr, and a 64 KiB result. Module autoloading remains
disabled. The H1 harness carries one fixed generated `Policy` request and no
external input.

## Evidence Policy

Success requires `policy_valid`, 18 projected policy actions, zero machine
actions, zero Python fallback, zero retry, zero raw retention, and stable
runtime, parent, harness, controller, contract, and vector identities.

Failure must reduce to one of the 13 allowlisted reason codes. Raw stdout,
stderr, exceptions, invocation details, environment, checkout root, identity,
and security material are not retained. Only three exact bounded sanitized
authorization, result, and evidence records may be written.

Any result requires separate evidence acceptance. A successful attempt alone
does not authorize U3K or another attempt.

## Hard Boundary

This proposal does not authorize PowerShell parsing, import, dot-sourcing, or
execution; runtime, parent, manifest, module, hardware, or machine observation;
Python machine access; retry; machine/storage/F:/B:/ACL/identity/probe/cleanup/
Defender/scanner action; network or trust retrieval; downloads; artifacts;
models; inference; cameras/media/data; containers; Kubernetes; profile
activation; deployment; U3R retry; U3K; or remote Git.
