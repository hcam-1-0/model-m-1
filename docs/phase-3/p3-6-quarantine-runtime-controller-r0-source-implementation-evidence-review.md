# P3.6 U3S Dual Runtime Controller R0 Source Evidence

## Accepted Scope

The owner authorized source-only implementation against authorization package
SHA-256
`3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC`.
The implementation contains one canonical contract, one generated vector
manifest, an authoritative but non-executed PowerShell controller, a
machine-disabled Python policy reference, and four focused test modules.

A separate compatibility amendment authorized one transition-only edit to the
historical implementation-proposal test. Its immutable authorization package,
digest, duplicate-statement, documentation, and line-ending checks remain.
Only the obsolete requirement that authorized implementation paths be absent
was replaced with exact path-presence and closed-gate assertions.

## Implemented Architecture

PowerShell remains the only intended Windows machine controller. Its R0 source
is default denied, declares the future bounded operations, and embeds a static
canonical projection. It was not parsed, imported, dot-sourced, or executed.

Python is the standard-library-only policy reference and cross-language oracle.
It imports only `hashlib`, `json`, and `typing`. It has no filesystem, registry,
environment, network, native API, process, machine-controller, or fallback
surface.

Both controllers project the same version, request and result fields, two
modes, 18 ordered actions, 18 failure reasons, resource fields, redaction
fields, and source-binding fields. Any unknown field, action, reason, state, or
projection difference terminates closed.

## Generated Evidence

The manifest contains exactly 192 explicit deterministic vectors:

- 32 request-schema vectors;
- 24 authorization and binding vectors;
- 48 stage-transition vectors;
- 32 redaction and prohibited-field vectors;
- 24 resource, timeout, and output-bound vectors;
- 32 cross-language projection vectors.

Focused generated and static validation passed 244 tests. Python-reference
branch coverage is 100 percent: 152 statements and 94 branches with no misses
or partial branches. The full Phase 3.6 suite passes 705 tests after the exact
compatibility transition. Ruff, strict JSON, line-ending, scope, hash, and Git
diff checks pass.

## Exact Primary Hashes

- Canonical contract: `3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E`
- Vector manifest: `31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B`
- PowerShell controller: `78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB`
- Python reference: `C1470C65C6D5DA3EF93161F519BBC01507BBB805C6D433F58C65FDCAFE3FFC4F`

The accepted generated-validation harness, prior vector manifest, transaction
runner, pure handler, and Windows adapter remain byte-exact.

## Boundaries

This is nonobservational source and generated/static evidence. No PowerShell
parser or runtime was used. No runtime, manifest, hardware, machine, storage,
`F:`, `B:`, ACL, probe, cleanup, scanner, network, dependency, artifact, model,
inference, camera, media, private or Government data, container, Kubernetes,
profile activation, deployment, U3R retry, U3T attempt, U3K, or remote Git
action occurred.

`Preflight` remains machine-disabled. The implementation package grants no
runtime authority and requires separate exact owner acceptance. Acceptance can
permit preparation only of a separate non-effective U3T planning and
authorization proposal; it cannot authorize a U3T attempt or any machine
action.
