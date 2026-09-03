# P3.6 U3S Dual Runtime Controller Architecture

## Recorded Selection

The owner selected:

- `D-P3.6-U3S-001: A+B`
- `D-P3.6-U3S-002: A`
- `D-P3.6-U3S-003: A`
- `D-P3.6-U3S-004: A`

The original R0 packet presented A and B as alternatives. This R1 proposal
normalizes the explicit combined selection into two non-overlapping roles. It
does not treat both implementations as simultaneous machine executors.

## PowerShell Controller

The PowerShell implementation is the authoritative Windows machine controller.
It owns exact local path classification, bounded metadata and hashing,
cache-only trust verification, provider-state closure, manifest parsing after
authorization, process boundaries, and sanitized evidence projection.

Before the exact Utility module is bound, it may use only PowerShell language
constructs and approved .NET APIs. It must be persisted as repository source,
statically tested, independently hashed, and bound into every future execution
package.

## Python Reference Controller

The Python implementation is a portable policy engine and cross-language
oracle. Its default scope is generated-only and machine-disabled. It validates
request envelopes, evaluates state transitions, verifies sanitized result and
evidence contracts, runs canonical generated vectors, and compares the
PowerShell projection with the expected canonical projection.

Python is not an automatic runtime fallback. Allowing it to call machine APIs
or start processes later would require separate Python-runtime binding,
dependency review, security review, lab evidence, and owner authorization.

## Shared Contract

Both implementations consume one versioned contract containing:

- request and authorization envelopes;
- typed sanitized stage codes;
- action ordering and terminal-state rules;
- output, timeout, and resource bounds;
- redaction and prohibited-field rules;
- result and evidence schemas;
- generated conformance vectors.

Unknown fields, unknown reason codes, schema disagreement, and projection
differences fail closed. The controllers cannot silently reinterpret or extend
the canonical contract.

## Machine Authority

Only the PowerShell controller has default machine-action authority. Python is
machine-disabled, simultaneous execution is forbidden, automatic failover is
forbidden, and automatic retry is forbidden. A PowerShell/Python policy
disagreement produces a terminal `cross_language_projection_diverged` result
with no machine action.

## Evidence Strategy

The source-only implementation must include generated simulations for exact
path handling, reparse rejection, file bounds, hashes, native structure layout,
trust initialization, trust verification, provider-state closure, manifest
policy, process startup, timeout, bounded output, redaction, and fail-closed
state transitions.

The same vectors must produce equivalent PowerShell and Python projections.
Source acceptance cannot execute PowerShell, Python controller code, native
machine APIs, subprocesses, manifests, or runtime validation.

## Runtime Reentry

1. Accept the dual-controller source and generated/static evidence.
2. Separately authorize a PowerShell-only preflight runtime diagnostic.
3. Accept successful preflight evidence.
4. Separately authorize manifest binding and the complete 84-vector validation.

U3K remains blocked throughout these gates. The current selection authorizes
only preparation of a new source-only implementation authorization proposal
after the revised R1 planning package is accepted.
