# P3.6 U3T H1 Preflight Harness R0 Evidence Review

## Result

The exact H1 source-only authorization was recorded against planning package
SHA-256
`26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2`.
The additive harness source, 48 generated source-text vectors, and one Python
static test module are implemented and sealed as non-executable evidence.

The three primary artifact hashes are:

- Harness source: `69CBF4637A22BB7859ED07D19804C8576D76FB1270FF58D0D182EED2592FCE7B`
- Generated-vector manifest: `394A4564D54B531EBBC7C16BEA6F66D0D41DEDA757E5E979C796B350462DAB4F`
- Python static test: `D6F5A7BAA5CC37C7ABF89912AC787A1B0CD79D47BD802DBB73546CE3A5A419E2`
- Authorized compatibility test: `E075708B67B53DFD1DE9D14BD31B544A6335A20573AA123EF88293F0A06FE3D7`

## Harness Design

The source accepts no parameters or external request. It contains one fixed
generated `Policy` request and binds the accepted controller by exact sibling
path, a 64 KiB file-size ceiling, and SHA-256. It contains exactly one future
dot-source expression and one future `Invoke-HcamRuntimeController` expression.
Those expressions have not been parsed, imported, dot-sourced, or executed.

The generated request keeps machine authority and automatic retry false. It
declares one future process at most, one attempt, a 30-second total bound,
16 KiB stdout, zero stderr, 64 KiB result, zero closure files, and zero cleanup
actions. Its fixed outputs retain no raw material and expose only
`source_binding_failed`, `result_contract_invalid`, or `policy_valid`.

## Generated Evidence

The 48 vectors cover:

- 12 request and source-binding assertions.
- 8 controller-load and function-binding assertions.
- 12 sanitized-result assertions.
- 8 timeout and output-bound assertions.
- 8 forbidden-surface and closed-gate assertions.

Python read the PowerShell file only as inert UTF-8 text. It did not use a
PowerShell parser, runtime, module loader, subprocess, native machine API, or
fallback controller. The accepted U3S contract, vectors, controller sources,
evidence, package, and five prior inputs remain byte-exact.

The exact
`D-P3.6-U3T-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT` statement is recorded with
UTF-8 SHA-256
`FC441D894C23EFBAF3CE449B888535C06E4905BF66152D2B39B01970BF15E043`.
It authorized only the historical U3T planning test to transition from a
pre-authorization path-absence assertion to checks for the six exact H1 paths,
48 generated vectors, the recorded amendment, pending H1 owner acceptance, and
closed runtime and machine gates.

The focused H1 suite passes all 8 tests. The explicit Phase 3.6 suite passes all
719 tests after the authorized compatibility transition. Ruff, strict JSON,
line-ending, immutable-hash, and Git diff checks also pass. No PowerShell source
was parsed, imported, dot-sourced, or executed during this validation.

## Limitations

This is source and generated/static evidence only. It does not establish that
the PowerShell source parses or runs. It is not runtime, trust, manifest,
hardware, machine, storage, model, camera, media, deployment, or conformance
evidence.

No PowerShell parsing, import, dot-sourcing, or execution; Python machine
access; runtime or manifest observation; storage; `F:`; `B:`; ACL; probe;
cleanup; scanner; network; download; artifact; model; inference; camera;
media; private or Government data; container; Kubernetes; profile activation;
deployment; U3R retry; U3T R1 attempt; U3K; or remote Git action was performed.

## Next Gate

The next decision is
`D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-ACCEPTANCE` against the final
resealed package digest. It can accept only source and generated/static
evidence and permit preparation only of a separate non-effective U3T R1
runtime-binding and one-attempt authorization proposal. It cannot authorize
PowerShell execution, runtime or machine observation, an R1 attempt, U3R retry,
U3K, deployment, or remote Git.
