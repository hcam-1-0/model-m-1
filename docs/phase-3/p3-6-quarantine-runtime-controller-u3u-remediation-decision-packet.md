# P3.6 U3U H1 Remediation Decisions

## Current State

The single U3T R1 attempt was consumed with the allowlisted reason
`result_contract_invalid`. Runtime classification, bounded metadata, SHA-256,
cache-only trust verification and close, all three fixed parent checks, and all
five accepted source bindings passed before and after the process. The H1
process ran once, did not time out, produced zero stderr, and exited with its
documented result-contract failure code.

The failure record intentionally retains neither the candidate controller
projection nor the individual failed predicate. The H1 output reports 16
completed actions because that is the fixed sanitized failure projection; it
does not prove that the underlying controller completed exactly 16 actions.

The existing H1 tests validate source text, embedded JSON, bounds, hashes, and
forbidden surfaces. They do not execute PowerShell or validate the runtime
controller return shape. That static-only gap is confirmed. The exact runtime
field, type, value, or controller reason mismatch remains unobserved.

## Recommended Direction

Do not retry the same H1 and do not change the accepted controller yet. Create
an additive, package-bound H1 R1 diagnostic harness that maps each result-field
group to a small allowlisted reason taxonomy while retaining no values, raw
output, type names, exceptions, or environment material. Validate it with
generated static differential vectors, accept the source separately, and only
then request one new digest-bound generated-only runtime diagnostic.

## D-P3.6-U3U-001: First Remediation Surface

### A. Additive H1 R1 diagnostic harness (recommended)

Preserves the accepted controller and the historical H1 harness byte-exact.
The new harness isolates the failed result group without guessing at a
controller defect.

### B. Modify the controller first

Changes accepted controller behavior before the failed H1 predicate is known.
This invalidates more evidence and risks solving the wrong problem.

### C. Modify both controller and H1

Creates the largest change surface and prevents clean attribution of a later
success.

### D. Stop U3T remediation

Leaves U3T and U3K blocked with no new source or runtime work.

## D-P3.6-U3U-002: Sanitized Diagnostic Contract

### A. Typed field-group reason taxonomy (recommended)

Allows one bounded reason for top-level shape, identity, terminal/success,
reason, stage, count, retention, or gate mismatch, plus an allowlisted
controller reason family. No candidate value, type name, raw projection,
stdout, stderr, exception, or environment data is retained.

### B. Bounded mismatch bitset

Uses fixed booleans for each field group. It is compact but less readable and
harder to evolve safely across contract versions.

### C. Keep one coarse invalid code

Repeats the current diagnostic blind spot and gives another attempt little
value.

### D. Retain raw controller output

Provides maximum debugging detail but breaks the existing zero-raw-retention
boundary and is not recommended.

## D-P3.6-U3U-003: Source Validation Evidence

### A. Generated static differential suite (recommended)

Requires generated cases for every allowlisted result group, controller reason
family, redaction rule, output bound, and fail-closed transition. The suite may
compare canonical generated mappings with the already accepted machine-disabled
Python policy oracle, but it may not access machine state or execute PowerShell.

### B. Static token and hash checks only

Repeats the evidence model that did not catch the U3T R1 runtime mismatch.

### C. PowerShell execution as implementation evidence

Combines source acceptance and runtime authorization, weakening the current
source-first gate.

### D. No validation package

Leaves the remediation unreviewable and runtime reentry closed.

## D-P3.6-U3U-004: Runtime Reentry Sequence

### A. Source acceptance then one diagnostic retry (recommended)

1. Implement and statically validate the additive H1 R1 source.
2. Record exact owner source acceptance.
3. Prepare and separately authorize one digest-bound generated-only runtime
   diagnostic.
4. Require successful evidence and owner acceptance before any U3K package.

### B. Blind retry of accepted H1

Repeats the same input with no added diagnostic value.

### C. Advance directly to U3K

Breaks the existing U3T success gate and is not recommended.

### D. Do not reenter runtime validation

Keeps U3T and U3K blocked.

## Recommended Selection

`A / A / A / A`

Selecting these options authorizes preparation only of a separate source-only
H1 R1 implementation authorization proposal. It does not authorize source or
test implementation, PowerShell parsing/import/execution, runtime or machine
observation, another attempt, storage, network, scanners, models, media,
containers, Kubernetes, deployment, U3K, or remote Git.
