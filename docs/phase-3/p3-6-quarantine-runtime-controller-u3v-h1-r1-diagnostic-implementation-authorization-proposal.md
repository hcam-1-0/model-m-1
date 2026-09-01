# P3.6 U3V H1 R1 Diagnostic Source Authorization Proposal

## Authority

`D-P3.6-U3U-FAILURE-ANALYSIS-DECISIONS` accepted U3U planning package
SHA-256
`C58B9291E06396374DE92308F2CC52CDB51824BFFDFD1958E4D655C75A894CCD`
with `A/A/A/A`. That decision authorizes preparation of this proposal only.
It does not authorize any source or test implementation.

## Why This Proposal Exists

The consumed U3T R1 attempt proved that the exact PowerShell runtime, its fixed
parents, cache-only trust binding, and all five accepted source bindings were
stable. The accepted H1 process then returned `result_contract_invalid`.

The historical H1 harness intentionally retained no controller projection or
individual failed predicate. Its static tests validated source text and fixed
JSON outputs but did not validate the actual PowerShell return shape. The next
source package must close that evidence gap without changing the accepted
controller or retaining raw diagnostic material.

## Proposed Additive Source Surface

The future authorization is limited to eight implementation paths:

1. A versioned diagnostic contract.
2. An additive PowerShell H1 R1 diagnostic harness.
3. A machine-disabled Python reference classifier.
4. At least 128 generated-only vectors.
5. One generated/static differential test module.
6. Nonobservational implementation evidence.
7. A digest-bound implementation package.
8. A human evidence review.

One existing U3U planning test may receive only a transition-aware assertion
update. Canonical ledgers, documentation, and line-ending records may be
synchronized. One local checkpoint commit may be made after clean validation;
push is not authorized.

## Diagnostic Taxonomy

The source must emit only one fixed bounded JSON projection using one of these
reason codes:

- `source_binding_failed`
- `controller_top_level_shape_invalid`
- `controller_contract_identity_invalid`
- `controller_terminal_state_invalid`
- `controller_reason_family_invalid`
- `controller_stage_projection_invalid`
- `controller_action_counts_invalid`
- `controller_retention_projection_invalid`
- `controller_gate_effect_invalid`
- `controller_projection_valid`
- `diagnostic_internal_contract_invalid`

No candidate value, type name, key set, raw projection, stdout, stderr,
exception, environment, identity, native status, or security material may be
retained.

## Generated Evidence Requirements

- At least 128 generated-only vectors.
- Every reason code, output bound, redaction rule, and fail-closed transition
  covered.
- At least 95 percent branch coverage for the new Python reference classifier.
- Canonical PowerShell contract projection compared statically to the Python
  reference.
- No external fixture, model, media, private data, or Government data.
- No PowerShell parsing, import, dot-sourcing, or execution.
- No Python machine, filesystem-runtime, registry, environment, network,
  native API, subprocess, or fallback access.

## Immutable Historical Inputs

The accepted H1 harness, PowerShell controller, controller contract and
vectors, Python policy oracle, consumed U3T R1 records, failure analysis, U3U
decision packet, planning package, and owner acceptance must remain byte-exact.

## Gate Effect

This proposal authorizes nothing by itself. Exact owner authorization against
the final package digest may authorize source-only implementation. A completed
source package would still require separate exact owner acceptance before any
runtime diagnostic package could be prepared. Another attempt, U3K, deployment,
and remote Git remain blocked.
