# P3.6 U3Y Controller R1 Stage-Projection Source Evidence

## Authorized Scope

The owner authorized source-only implementation against U3Y authorization
package SHA-256
`35086DDC152DDF659097F6841AA364B965E0851833C339DCF2736BEF1AA0940A`.
Implementation is confined to the eleven additive paths bound by that package.
The evidence record SHA-256 is
`74DA543B13694D380211632133F77D0AE84C1A5C1612BB734700313FFFFABFDD`.

## Implemented Remediation

The additive R1 PowerShell source separates successful and failed terminal
projection construction. `New-HcamPolicyValidProjection` writes
`completed_actions = 18`, `failed_action = $null`, and
`failed_stage = $null` directly into the stage projection. No failed-action or
failed-stage value crosses a string-typed nullable parameter.

`New-HcamActionFailureProjection` remains fail closed. It accepts a nonempty
action string, validates it against the 18-action map, derives the exact mapped
reason, and writes the zero-based completed-action index. An unknown action is
mapped to `validate_result_contract` and `result_contract_invalid`.

The machine-disabled Python reference independently enforces the same wire
semantics. It rejects empty strings, omitted fields, wrong types, out-of-range
completed-action counts, mismatched actions and reasons, nonzero retention,
open gates, and inconsistent success/reason pairs.

## Generated Evidence

The manifest contains exactly 288 deterministic generated-only vectors: 32 in
each of nine required groups. It covers literal-null success, empty-string
rejection, missing fields, wrong types, completed-action bounds, all 18 actions,
all 18 reasons, cross-language canonical projection, and zero-retention closed
gates.

All 429 focused generated/static tests pass. The machine-disabled Python
reference has 100 percent coverage: 202 statements and 122 branches with zero
missing or partial branches. Ruff, strict parsing of 264 Phase 3 JSON files,
and `git diff --check` pass. Static PowerShell evidence consists only of inert
source-text checks and the explicitly delimited JSON contract projection.

## Exact Primary Hashes

- Contract: `637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4`
- PowerShell source: `787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31`
- Python reference: `B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0`
- Vector manifest: `D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4`

The accepted historical controller, diagnostic, diagnostic contract, and U3W
evidence remain byte-exact.

## Compatibility Gate

The owner authorized the exact compatibility transition against provisional
implementation-package SHA-256
`643540124398CF4F531597C2EB688BBB5D92F113776A1DFEDBFBF419636BBE5B`.
The transition decision is
`D-P3.6-U3Y-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT`.
The 1,542-byte owner statement has SHA-256
`791BD3E84396936CA50C8CCA23392A54C519763827E9CF6C3F5793FB78DCFE7D`.

The single allowlisted historical U3Y test now recognizes all eleven authorized
paths as present and verifies that source implementation is complete, owner
source acceptance is pending and requestable, and every PowerShell, Python
machine, runtime, retry, U3K, deployment, and remote-Git gate remains closed.
All immutable U3X acceptance, U3Y authorization-package, exact-null,
immutable-input, and historical artifact assertions remain in force.
The sealed legacy pending flags required by the immutable R1 evidence tests are
retained, while distinct post-transition fields record the effective completed
and requestable state.

The prior full-suite result of 1,199 passed and one transition-only failure is
retained in the evidence record. After the authorized transition, all 1,200
tests across 54 Phase 3.6 files pass. Source acceptance is now requestable. The
next required decision is
`D-P3.6-U3Y-CONTROLLER-R1-STAGE-PROJECTION-IMPLEMENTATION-ACCEPTANCE`.

## Boundaries

No PowerShell parser, import, dot-source, or execution occurred. No Python
machine access or fallback, runtime or hardware observation, storage, `F:`,
`B:`, ACL, probe, cleanup, scanner, network, download, artifact, model,
inference, camera, media, data, container, Kubernetes, profile activation,
deployment, another attempt, U3K, commit, push, or remote Git action occurred.
