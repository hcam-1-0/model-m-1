# P3.6 U3Z Controller R1 Generated Contract-Validation Harness Evidence Review

## Review Status

- The authorized U3Z H1 source-only implementation is complete.
- Exactly 288 generated-only cases were materialized with one-to-one provenance.
- The implementation-only generated/reference/source-text validation passed
  297 checks; combined transition and implementation validation passed 303.
- Exact owner implementation acceptance is pending.
- The separately authorized compatibility-test transition is complete.
- Clean full Phase 3.6 post-seal validation passed all 1,503 checks.
- PowerShell was not parsed, imported, dot-sourced, or executed.
- Runtime binding, generated validation, U3K, deployment, commit, push, and
  remote Git remain blocked.

## Authority

- Decision:
  `D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-HARNESS-IMPLEMENTATION-AUTH`
- Authorization package SHA-256:
  `B9696A95EF14D186C7D2CC8D949EE711C2621E907DAD28AF4FC192B2A1A1F09A`
- Canonical owner statement: 1,465 UTF-8 bytes
- Canonical owner statement SHA-256:
  `5136263DC036CD37AAEB7EEBA05076C5567761246F59566EB12B4DBA9AE1DA5C`
- Compatibility decision:
  `D-P3.6-U3Z-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT`
- Compatibility owner statement: 1,704 UTF-8 bytes
- Compatibility owner statement SHA-256:
  `E7F7B483EBF3DABD46CA213CB6773582CE23542BB3EA8BB8FBB535F212327692`
- Transitioned proposal-test SHA-256:
  `42FF55E604C3CE0490F30619D8A043FF48408CB63F97CB256565F555ED2C99E1`
- Accepted U3Y implementation package SHA-256:
  `ED306CDFAA604675DAC42AF3137C566EC82EC2BEBCA9B68BE60DE4B8D6D1DC78`

The authorization package and exact owner statement were verified before the
U3Z implementation paths were created.

## Immutable U3Y Boundary

The accepted U3Y implementation package contains sixteen core files. The
package and every listed core file were rehashed and remain byte-exact. U3Z did
not modify the accepted controller, controller contract, Python reference,
source vector manifest, U3Y evidence, U3Y tests, or U3Y review.

The primary accepted bindings remain:

- Controller SHA-256:
  `787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31`
- Controller contract SHA-256:
  `637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4`
- Source vector manifest SHA-256:
  `D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4`
- Machine-disabled Python reference SHA-256:
  `B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0`

## Source Result

- Additive PowerShell harness:
  `tools/phase36_quarantine_runtime_controller_r1_generated_validation.ps1`
- Harness SHA-256:
  `D9EE5CC7599AACCE3363CE5C29EE479D777F94CF886AE779390B7027C40FA382`
- Materialized vector manifest:
  `contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json`
- Materialized vector SHA-256:
  `7BCDFCA583644BD4ED5F4B747C3969B4C9FF4029B48734F8BD4D90BA5D600A21`
- Generated/static test:
  `tests/test_phase36_quarantine_runtime_controller_u3z_generated_contract_validation_static.py`
- Generated/static test SHA-256:
  `C633E51B7246975992CE3EAD107ADED94C9132A95F821ED8BAA40B8BEAD169A7`

The harness binds the accepted controller, contract, source vector manifest,
and Python reference by exact SHA-256. It also requires caller-supplied exact
harness and materialized-manifest digests. It reads only the repository-bound
materialized fixture and exposes only the exact controller function
`Invoke-HcamRuntimeControllerR1`.

The harness accepts no request, result, or expected projection from a caller.
Every case is a generated `Policy` request with machine authority, Python
fallback, and automatic retry disabled. It emits only a bounded aggregate
success result or an allowlisted sanitized layer failure.

## Vector Materialization

The accepted manifest has nine groups of 32 vectors:

1. `policy_valid_exact_null_success`
2. `empty_string_rejected`
3. `missing_field_rejected`
4. `wrong_type_rejected`
5. `completed_action_bounds`
6. `all_eighteen_failure_actions`
7. `all_eighteen_failure_reasons`
8. `cross_language_canonical_projection`
9. `zero_retention_and_closed_gates`

The 288 materialized cases retain the source vector ID, source index, source
kind, group, description, canonical source-vector digest, compilation rule,
source expectation, request digest, and expected-projection digest.

The 96 request vectors are directly materialized. The 160 result-validation
vectors are checked by the accepted Python reference and mapped to either
policy success or the typed `validate_result_contract` failure stage. The 32
contract-projection vectors are checked by the reference and mapped to either
policy success or the typed `compare_cross_language_projection` failure stage.
This preserves one-to-one provenance while keeping the future harness surface
to generated `Policy` requests and one controller entry point.

## Static Validation

- Materialized cases reconstructed from source: 288
- One-to-one source IDs and indices: 288 unique and exact
- Literal-null success cases: 32
- Failure-action and failure-reason coverage: all 18 mappings
- Focused U3Z implementation generated/static checks: 297 passed, 0 failed
- Combined U3Z transition and implementation checks: 303 passed, 0 failed
- Full Phase 3.6 static suite: 1,503 passed, 0 failed
- Strict JSON and duplicate-key checks: 271 files passed
- Ruff: passed
- Git diff check: passed
- PowerShell parser, import, dot-source, or execution count: 0
- Python machine or fallback action count: 0
- Runtime or hardware observation count: 0
- Network, download, model, inference, camera, media, or data action count: 0
- Container, Kubernetes, profile activation, or deployment action count: 0
- Commit, push, or remote Git action count: 0

This is nonobservational evidence. It does not establish PowerShell syntax or
runtime behavior, and it does not claim that the 288 cases passed through the
PowerShell controller.

## Compatibility Transition

The historical pre-authorization proposal test at
`tests/test_phase36_quarantine_runtime_controller_u3z_generated_contract_validation_proposal.py`
correctly asserted that all six future implementation paths were absent and
that U3Z authorization was pending when the planning package was sealed. Those
assertions are now stale because the owner explicitly authorized the six paths.

The full 56-file Phase 3.6 static suite confirms the scope precisely: 1,502
checks pass and only that single path-absence assertion fails.

The exact compatibility-test allowlist amendment was separately authorized.
Only that proposal test was changed. The obsolete path-absence assertion was
replaced with transition-aware checks that all six authorized paths exist,
source implementation is complete, compatibility is recorded, owner acceptance
is pending, and all runtime, machine, U3K, deployment, commit, push, and remote
Git gates remain closed. All other historical planning and gate assertions
remain intact.

After this transition, the combined focused suite passed 303 checks and the
full 56-file Phase 3.6 suite passed all 1,503 checks.

## Limitations And Next Gate

- The harness has not been parsed or run by PowerShell.
- No runtime path, metadata, hash, trust, identity, module, manifest, machine,
  hardware, storage, ACL, probe, cleanup, or scanner action occurred.
- No generated-validation attempt or runtime-binding package is authorized.
- No model, inference, camera, media, private data, or Government data was used.
- No container, Kubernetes, profile activation, deployment, U3K, commit, push,
  or remote Git action is authorized.

The implementation package is resealed for exact owner source-implementation
acceptance. Only that later acceptance may permit preparation of a separate,
non-effective runtime-binding and generated-validation authorization proposal.
It will not itself authorize a PowerShell attempt.
