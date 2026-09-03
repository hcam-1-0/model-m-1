# P3.6 U3S Runtime Controller Remediation Decisions

## Current State

The single U3R attempt was consumed with the sanitized reason
`runtime_binding_failed`. It stopped before Utility-manifest observation,
Aggregate harness execution, runner contracts, pure handlers, or the Windows
adapter. The current authorization cannot be reused and U3K remains blocked.

The failed attempt retained no raw exception, native trust code, path metadata,
manifest content, parser token, stdout, or stderr. The exact runtime substage is
therefore intentionally unknown.

An earlier monolithic inline controller submission was rejected by Windows
before shell creation because it exceeded the command-length limit. That event
did not observe the runtime and did not consume the attempt. The subsequent
bounded runtime controller did consume the attempt and failed in 59 ms. These
events demonstrate that an inline, unsealed controller is not a durable
production execution surface.

## Recommended Direction

Build no new runtime package yet. First establish a persisted, package-bound,
source-only controller with generated static tests and granular sanitized stage
codes. Accept that source separately. Then authorize one preflight-only runtime
diagnostic. Only a successful, separately accepted preflight may lead to a new
full generated-validation package.

## D-P3.6-U3S-001: Controller Architecture

### A. Persisted package-bound PowerShell controller (recommended)

Uses the already selected PowerShell 7 runtime. Before the exact Utility module
is bound, the controller may use only PowerShell language constructs and .NET
APIs. Its exact source hash becomes part of every future runtime package.

### B. Persisted Python stdlib controller

Provides good isolation through `ctypes` and `subprocess`, but adds a second
runtime whose executable, dependencies, and trust policy must also be bound.

### C. Another ephemeral diagnostic controller

Fast, but repeats the missing source identity, static validation, and transport
reliability problems exposed by U3R.

### D. Stop runtime-controller work

Ends this P3.6 path and leaves U3R and U3K blocked.

## D-P3.6-U3S-002: Sanitized Diagnostic Granularity

### A. Typed stage taxonomy (recommended)

Records only allowlisted stages such as path classification, metadata, hash,
trust initialization, trust verification, provider-state close, and identity
stability. No raw native code, exception, path expansion, or security state is
retained.

### B. Typed stages plus normalized native families

Adds a small allowlist of native failure families. It offers more diagnostic
value but increases the security and compatibility contract.

### C. Single coarse failure code

Preserves the current `runtime_binding_failed` behavior, which cannot guide a
specific remediation.

### D. No future runtime diagnostics

Stops the path without gathering any additional runtime evidence.

## D-P3.6-U3S-003: Controller Validation Evidence

### A. Generated static and simulated boundary suite (recommended)

Requires generated cases for exact paths, reparse rejection, file bounds,
hashes, native structure layout, trust verify/close state, manifest policy,
process boundaries, redaction, timeout, and fail-closed transitions. The tests
remain generated-only and do not execute PowerShell or machine APIs.

### B. Static source inspection only

Checks source tokens and hashes but does not simulate state transitions or
native interop outcomes.

### C. Runtime smoke test as implementation evidence

Uses machine execution before source acceptance and conflicts with the current
source-first gate.

### D. No controller implementation

Leaves the runtime path closed.

## D-P3.6-U3S-004: Runtime Reentry Sequence

### A. Three separate gates (recommended)

1. Source-only controller implementation and generated/static acceptance.
2. One digest-bound preflight-only runtime diagnostic and evidence acceptance.
3. A later, separate full generated-validation retry package.

### B. Source acceptance then direct full retry

Combines the first controller runtime execution with manifest binding and all
84 generated vectors. Another controller defect could consume the full retry.

### C. Immediate preflight without persisted source

Repeats the current source identity and reproducibility gap.

### D. Do not reenter runtime validation

Keeps U3R and U3K blocked.

## Recommended Selection

`A / A / A / A`

Selecting these options authorizes preparation only of a separate source-only
implementation authorization proposal. It does not authorize implementation,
PowerShell parsing/import/execution, runtime or machine observation, another
attempt, storage, network, scanners, models, media, containers, Kubernetes,
deployment, U3K, or remote Git.
