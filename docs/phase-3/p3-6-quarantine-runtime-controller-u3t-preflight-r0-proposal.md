# P3.6 U3T Preflight R0 Proposal

## Purpose

U3S source implementation is accepted. U3T is the next diagnostic boundary,
but no runtime action is authorized. The accepted controller file defines
functions and does not provide a safe top-level preflight entrypoint. U3T
therefore starts with an additive, exact-hash-bound harness source gate.

## Gate H1: Source Harness

H1 proposes one minimal PowerShell harness, at least 48 generated vectors, and
one Python source-text/static test module. The harness will be designed to load
the exact accepted controller and submit one generated `Policy` request. It
will not enable controller `Preflight` machine authority.

H1 implementation, if separately authorized, remains source-only. PowerShell
cannot be parsed, imported, dot-sourced, or executed. Python can evaluate only
generated fixtures and source text; it cannot inspect a machine or serve as a
runtime fallback.

## Gate R1: Future Runtime-Bound Preflight

R1 remains a later separate authorization. Only after H1 source acceptance may
a new package bind an exact PowerShell runtime path, size, version, SHA-256,
cache-only trust result, fixed parent components, accepted controller hash, and
accepted harness hash. Historical runtime evidence is not reusable.

The eventual R1 attempt is limited to one process, one attempt, a 30-second
deadline, bounded sanitized output, and no retry. It may produce one generated
`Policy` projection or one allowlisted failure code. It cannot access a Utility
manifest, modules, closure, hardware, storage, network, cameras, media, models,
or external data.

## Boundaries

This proposal grants no H1 implementation and no R1 attempt. It does not
authorize PowerShell parsing or execution, Python machine access, runtime or
manifest observation, hardware or machine access, storage, `F:`, `B:`, ACLs,
probes, cleanup, scanners, network, downloads, artifacts, models, inference,
cameras, media, private or Government data, containers, Kubernetes, profile
activation, deployment, U3R retry, U3K, or remote Git.

The next requestable decision is
`D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH` against the separately
sealed planning package digest.
