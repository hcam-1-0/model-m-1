# Phase 3.6 R3 Generated Runtime Validation

Status: all 500 generated cases passed; U3K storage has not started.

## Outcome

The additive R3 outer-policy harness accepted all 416 generated policy vectors.
The additive R3 runner/handler harness accepted 20 runner contract vectors and
64 pure-handler vectors. The aggregate run reported zero parser errors, zero
storage invocations, zero Windows-adapter imports or executions, zero machine
actions, zero network actions, and zero raw fixture, process-output, or exception
retention.

## R3 compatibility fixes

- Normalize JSON integers that fit the accepted contract to `Int32` before
  invoking the strict typed controller.
- Apply the machine-disabled reference request-validation boundary before R0
  stage evaluation so malformed generated requests fail at the canonical
  default-deny boundary.
- Import `ConvertFrom-Json` and `ConvertTo-Json` as Utility cmdlets.
- Validate `ForEach-Object` and `Where-Object` against their actual Core
  provenance while retaining Utility provenance for the five Utility cmdlets.
- Bind the additive handler harness to itself and use explicit array cardinality
  for an empty `Compare-Object` result under StrictMode.

The accepted historical R2 harnesses, controller, and vector manifests were not
modified. R3 is an additive compatibility successor.

## Reproduction

Run the outer harness with the exact controller/vector paths and their current
SHA-256 values. Run the handler harness in `Aggregate` mode with its own SHA-256
and the accepted vector-manifest SHA-256. Both commands use the fixed local
PowerShell 7 runtime with `-NoLogo -NoProfile -NonInteractive`.

The canonical sanitized execution record is
`contracts/phase-3/p3-6-consolidated-runtime-closeout-r3-generated-validation-evidence.json`.

## Remaining boundary

This result does not itself authorize or claim storage success. U3K may begin
only after the complete Phase 3.6 generated/static test suite and all exact
source bindings pass. No model, inference, camera, media, private or Government
data, container, Kubernetes, deployment, or remote Git action is included.
