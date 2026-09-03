# P3.6 U4A U3Z R1 Binding-Failure Decision Packet

## Status

- The U3Z R1 authorization was valid and the one allowed attempt is consumed.
- The attempt failed closed with `binding_failed` after 78 milliseconds.
- Runtime process invocations, controller dot-sources, and generated cases were all zero.
- No retry, implementation, U3K, deployment, commit, push, or remote Git action is authorized.

## What The Evidence Proves

The authorization record existed before observation and all 16 authorization
package core hashes matched. Runtime observation then began, but the three
fixed parents did not reach a collectively valid state. The attempt stopped
before runtime size, version, SHA-256, or trust; before all six source bindings;
and before the generated-validation process.

This localizes the failure to the outer attempt controller's fixed-parent
preflight. It does not indicate a failure in the accepted U3Z harness,
materialized vectors, controller R1, or stage-projection contract because none
of those runtime surfaces were reached.

The retained `binding_failed` code cannot distinguish:

1. A missing, reparse, or canonical-mismatch parent.
2. A fixed-parent result aggregation or strict-mode collection failure.
3. Another outer-controller failure before runtime-file classification.

The previous successful binding of the same runtime family on this logical
node is useful historical context, but it is not current evidence and cannot
be reused as authorization or proof.

## Design Gaps

The outer attempt controller was not sealed as a source-controlled core package
artifact. Its exact parent-set aggregation and evidence-writing behavior
therefore cannot be reproduced through immutable source review. The single
`binding_failed` reason also combines too many stages, and no generated static
vectors cover strict-mode empty, scalar, or multiple parent-failure sets.

## Decisions

### D-P3.6-U4A-001: First Remediation Surface

- **A. Additive source-controlled outer attempt controller, recommended.**
  Preserve all accepted and consumed artifacts byte-exact. Later prepare an
  exact package-bound controller for authorization, parent, runtime, source,
  process, result, and evidence stages.
- **B. Modify the U3Z harness.** Mix machine binding into the generated-contract
  harness and invalidate more accepted source evidence.
- **C. Change runtime path or parent rules.** Not justified by the coarse
  evidence and may weaken trust.
- **D. Stop remediation.** Keep U3Z and U3K blocked.

### D-P3.6-U4A-002: Sanitized Binding Taxonomy

- **A. Typed stage and parent-index reasons, recommended.** Retain only an
  allowlisted stage, parent index, and bounded boolean predicates. Never retain
  paths, attributes, raw exceptions, identities, or security material.
- **B. Stage-only reasons.** Simpler, but may not distinguish item failure from
  set aggregation.
- **C. Keep `binding_failed`.** Preserves the current blind spot.
- **D. Retain raw errors and paths.** Breaks the sanitization boundary.

### D-P3.6-U4A-003: Fixed-Parent Set Contract

- **A. Fixed three-record typed vector, recommended.** Materialize exactly
  three ordered boolean records and explicitly reduce them to `all_valid`,
  independent of pipeline null/scalar cardinality behavior.
- **B. Forced-array pipeline filtering.** Smaller change but leaves filtering
  semantics inside the trust boundary.
- **C. Sequential first-failure evaluation.** Simple, but loses the complete
  bounded three-parent classification.
- **D. Remove parent validation.** Reduces path-integrity assurance.

### D-P3.6-U4A-004: Validation And Reentry

- **A. Source acceptance, generated controller validation, then one attempt,
  recommended.** Validate strict-mode collection, taxonomy, redaction, and
  record sealing before consuming another machine attempt.
- **B. Source acceptance then direct runtime retry.** Faster, but can repeat a
  PowerShell-specific collection defect.
- **C. Blind retry.** No additional diagnostic value.
- **D. Advance to U3K.** Violates the successful-runtime-evidence gate.

## Recommended Selection

`A/A/A/A`

Selection authorizes preparation only of a separate source-only implementation
authorization proposal. It does not authorize source changes, tests,
PowerShell, Python machine access, runtime observation, retry, U3K, deployment,
commit, push, or remote Git.
