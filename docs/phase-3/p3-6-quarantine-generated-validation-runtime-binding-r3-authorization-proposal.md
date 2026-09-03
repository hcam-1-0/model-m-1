# P3.6 U3R Generated-Validation Runtime-Binding R3 Authorization Proposal

## Status

- Non-effective planning package only.
- Exact owner authorization is pending.
- No runtime, manifest, module directory, hardware, or machine path was observed.
- No PowerShell parser, import, or execution occurred.
- No retry or generated-validation attempt is authorized yet.

## Preparation Authority

Exact
`D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-IMPLEMENTATION-ACCEPTANCE`
is recorded in acceptance record SHA-256
`32BA42A51029920AE163866A923547CD16054D6C41ECD3C8EC5549B78FB3ED2E`.
That decision authorizes this separate planning package only.

## Accepted Inputs

- R2 harness SHA-256:
  `830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A`
- Generated vector manifest SHA-256:
  `5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C`
- Transaction runner SHA-256:
  `22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A`
- Pure handler SHA-256:
  `41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721`
- Parser-only Windows adapter SHA-256:
  `232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9`

The accepted files remain immutable. U3R does not authorize source changes.

## Proposed Future Attempt

The future decision is
`D-P3.6-U3R-GENERATED-VALIDATION-RUNTIME-BINDING-R3-AUTH`.
It would authorize at most one attempt on `LAB-LAPTOP-01` within 24 hours.
Failure consumes the authorization and no retry is automatic.

The exact runtime candidate is
`C:\Program Files\PowerShell\7\pwsh.exe`. The exact Utility manifest candidate
is `C:\Program Files\PowerShell\7\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1`.

Before any harness invocation, the attempt must:

1. Bind the exact runtime and fixed parent components.
2. Use cache-only, no-UI runtime trust validation with no trust retrieval.
3. Bind the exact Utility manifest and its fixed parent components.
4. Parse only one literal manifest hashtable without evaluating or importing it.
5. Resolve only declared constant-string closure fields under exact `PSHOME`.
6. Reject scripts-to-process, commands, expressions, wildcards, missing files,
   duplicate canonical paths, reparse points, and paths outside `PSHOME`.
7. Bind at most 64 files, depth 4, 64 MiB per file, and 128 MiB total.
8. Cache-only trust-check every declared DLL, EXE, PS1, or PSM1 without trust
   retrieval; data files remain containment/hash/stability bound.
9. Verify all five accepted source hashes.

Only after every preflight succeeds may the exact runtime be invoked once with
`NoLogo`, `NoProfile`, `NonInteractive`, and the R2 harness in `Aggregate`
mode. The runner remains `Contract`-only, the pure handler remains local and
allowlisted, and the Windows adapter may only be parsed.

## Evidence Policy

Success requires a stable runtime, manifest, closure, and source identity;
zero parser errors; 20 passing runner Contract vectors; 64 passing pure-handler
vectors; and zero prohibited action counts.

Failure must be reduced to an allowlisted controller or harness reason code.
Raw stdout, stderr, exceptions, parser tokens, manifest contents, fixtures,
identity, and security material are not retained.

Any result requires separate evidence acceptance. A successful attempt alone
does not authorize U3K.

## Hard Boundary

This proposal does not authorize PowerShell parsing, import, or execution;
runtime, manifest, closure, or hardware observation; retry; machine/storage/
F:/B:/ACL/probe/cleanup/Defender/scanner action; network or trust retrieval;
downloads; artifacts; models; inference; cameras/media/data; containers;
Kubernetes; profile activation; deployment; or remote Git.
