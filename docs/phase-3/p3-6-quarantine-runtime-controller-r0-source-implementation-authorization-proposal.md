# P3.6 U3S Dual Runtime Controller R0 Implementation Authorization

## Purpose

This package requests permission to implement the accepted A+B architecture as
source and generated/static evidence only. It does not request permission to
run PowerShell, inspect the laptop, bind a runtime or manifest, retry U3R, start
U3T, or prepare U3K.

The owner supplied the same R1 acceptance statement twice in one message. The
copies are identical and are recorded as one acceptance. Repetition does not
create additional authority.

## Exact Implementation

The proposed source implementation has four primary artifacts:

1. A canonical versioned JSON contract defining requests, results, typed
   stages, action counts, bounds, redaction, and gate effects.
2. A generated manifest containing at least 192 machine-independent vectors.
3. A PowerShell source controller that will be the authoritative Windows
   machine controller only after later runtime authorization.
4. A Python standard-library reference controller that remains machine-disabled
   and acts as the portable policy engine and cross-language oracle.

Four test modules cover the contract, pure Python policy behavior, PowerShell
source safety, and cross-language contract equivalence.

## Implementation-Time Boundary

The requested authorization permits execution of pure Python reference-policy
functions against generated fixtures. It also permits Python tests, static
verifiers, Ruff, JSON checks, hash checks, coverage, and Git diff checks.

The Python controller may not inspect the filesystem at runtime, read the
environment or registry, use native APIs, access the network, start subprocesses,
or act as a machine controller. Imports including `ctypes`, `cffi`, `os`,
`pathlib`, `platform`, `socket`, `subprocess`, and `urllib` are prohibited.

PowerShell may be written as source but may not be parsed, imported, dot-sourced,
or executed. Its contract sets and prohibited surfaces are verified from Python
as text and structured generated records only.

## Generated Evidence

At least 192 vectors are required:

- 32 request-schema cases;
- 24 authorization and binding cases;
- 48 stage-transition cases;
- 32 redaction and prohibited-field cases;
- 24 resource, timeout, and output-bound cases;
- 32 cross-language projection cases.

All vectors must pass. Python-reference branch coverage must be at least 95%.
The PowerShell and Python action, stage, reason, and schema sets must be equal.
Any difference fails closed.

## Immutable Inputs

The currently accepted generated-validation harness, vector manifest,
transaction runner, pure machine-handler module, and parser-only Windows adapter
must remain byte-exact. This implementation cannot repair or alter those files.

## Delivery Gate

After implementation, exact source hashes, test results, coverage, scope, and
nonobservational limitations must be sealed. At most one local checkpoint commit
may be made and nothing may be pushed. The resulting implementation still needs
separate exact owner acceptance before any U3T preflight package can be prepared.

## Continuing Prohibitions

This proposal does not authorize PowerShell execution, Python machine access,
runtime or manifest observation, storage, `F:` or `B:`, ACLs, scanners, network,
downloads, models, inference, cameras, media, private or Government data,
containers, Kubernetes, deployment, another U3R attempt, U3T, U3K, or remote Git.
