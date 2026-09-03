# P3.6 U3P Generated Validation And Runtime Binding R2 Authorization Proposal

## Preparation Authority

The exact U3O R1 source-remediation implementation package SHA-256
`2D9A234A3C1C29276D6D27160849E34DB7440631AC2CD97BEAA650FB48F52E8E`
was accepted under acceptance-record SHA-256
`8A6EBD49F71667ECF9961BB02CA891A610497DEBCE23DDDFB9A65FA08F2917EC`.
That acceptance authorizes preparation of this non-effective proposal only.

## Proposed Attempt

The proposal requests one attempt on `LAB-LAPTOP-01` within 24 hours of exact
digest-bound owner authorization. It binds only:

- `C:\Program Files\PowerShell\7\pwsh.exe` and its fixed parent components;
- remediated harness SHA-256
  `F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3`;
- vector manifest SHA-256
  `5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C`;
- runner SHA-256
  `22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A`;
- pure-handler SHA-256
  `41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721`;
- parser-only Windows-adapter SHA-256
  `232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9`.

The exact runtime would be invoked once with `NoLogo`, `NoProfile`, and
`NonInteractive`. The harness would run in `Aggregate` mode against 20 runner
contract vectors and 64 pure-handler vectors. The runner's `Storage` mode is
unreachable, and the Windows adapter remains parser-only.

## Failure And Evidence Policy

Any success or failure consumes the single authorization. Failure output may
contain only one of six layer-level codes: `binding_failed`, `manifest_failed`,
`parser_failed`, `contract_failed`, `handler_failed`, or
`result_serialization_failed`. Raw output, exceptions, fixtures, identities,
and security material are not retained.

Only three bounded sanitized records may be written: authorization, result,
and evidence. Successful evidence still requires separate owner acceptance.
The attempt alone cannot make U3K requestable.

## Prohibited Scope

The proposal excludes `Storage` mode, Windows-adapter import or execution,
machine/storage/`F:`/`B:`/ACL/identity/probe/cleanup/scanner action, alternate
runtime or hardware discovery, network trust retrieval, downloads, artifacts,
models, inference, cameras/media/data, containers/Kubernetes, profile
activation, deployment, and remote Git.

## Current Gate

This proposal is non-effective. No runtime observation or PowerShell action is
authorized until the final package digest is sealed and the owner records exact
`D-P3.6-U3P-GENERATED-VALIDATION-RUNTIME-BINDING-R2-AUTH` against that digest.
