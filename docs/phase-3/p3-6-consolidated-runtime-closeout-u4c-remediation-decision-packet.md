# P3.6 U4C Runtime-Closeout Failure Decisions

## Current State

The first consolidated runtime-closeout attempt is consumed and failed closed
at `CA-RC-A05-OUTER-CONTROLLER-GENERATED-VALIDATION` with sanitized reason
`process_output_bounds_failed`.

The package, owner statement, exact runtime hash, cache-only trust, three fixed
parents, and all eleven source bindings passed. One target PowerShell process
was started. Its result was not accepted because at least one of the stdout or
stderr bounds failed. The retained evidence does not reveal which predicate
failed, the child exit code, whether dot-sourcing completed, or whether any of
the 416 cases ran. Raw process material was intentionally discarded.

The handler process and U3K never started. `F:` was not accessed. Phase 3 is
not complete, no commit exists, and the consumed authorization cannot be
reused.

## Known Static Compatibility Transition

The complete Phase 3.6 suite currently reports `2011 passed, 1 failed`. The
single failure is the historical pre-authorization assertion in
`tests/test_phase36_consolidated_runtime_closeout_authorization_proposal.py`
that all seven planned output paths remain absent. That assertion was correct
before the accepted attempt; authorization, result, and evidence now exist,
while acceptance and the three U3K outputs remain absent. The test is preserved
unchanged until an exact future U4D compatibility allowlist authorizes its
transition.

## Recommended Remediation

Use an additive, source-controlled, hash-bound PowerShell child harness rather
than another unsealed in-memory driver. The harness should emit exactly one
UTF-8 JSON line through `Console.Out`, suppress all non-data streams, preserve
zero stderr, and expose only typed sanitized process classifications and safe
byte counts. Generated/static validation should cover success, every failure
class, exact byte boundaries, framing, BOM and CLIXML rejection, schema and
exit consistency, identity postflight, and zero retention before another
runtime authorization is prepared.

## Decisions

### D-P3.6-U4C-001: Sanitized Process Failure Taxonomy

- **A. Split typed output and exit classifications (recommended):** Distinguish
  start, timeout, exit, stdout, stderr, framing, JSON, schema, and identity
  failures without retaining process content.
- **B. Keep the combined output reason:** Smaller change, but another attempt
  may fail without identifying the violated predicate.
- **C. Hash raw process streams:** Adds correlation risk without explaining the
  process shape.
- **D. Retain raw diagnostics:** Violates the zero-retention boundary.

### D-P3.6-U4C-002: Generated Validation Child Surface

- **A. Additive hash-bound validation harness (recommended):** Makes the exact
  executed child logic reviewable, reproducible, and statically testable.
- **B. Harden the in-memory encoded command:** Fewer files, but weaker source
  binding and reviewability.
- **C. Extend the handler aggregate harness:** Fewer processes, but couples two
  independently accepted contract layers.
- **D. Skip outer validation:** Breaks the 500-case gate.

### D-P3.6-U4C-003: Child Result Framing Protocol

- **A. One UTF-8 JSON line through Console.Out (recommended):** Maximum 4096
  bytes, no BOM or CLIXML, all non-data streams silent, zero stderr.
- **B. Allow PowerShell object serialization:** Expands runtime-specific parser
  behavior.
- **C. Write a temporary result file:** Adds path, cleanup, and filesystem risk.
- **D. Use exit code only:** Cannot attest case counts and zero-action fields.

### D-P3.6-U4C-004: Pre-Runtime Validation Depth

- **A. Full generated stream and contract matrix (recommended):** At least 320
  generated vectors covering framing, boundaries, classifications, identity,
  and retention.
- **B. Focused 64-vector matrix:** Faster but materially narrower.
- **C. Source-text checks only:** Does not test parent-child behavior.
- **D. Runtime-first validation:** Risks repeating the consumed failure.

### D-P3.6-U4C-005: Authorization And Reentry Topology

- **A. One source-build authorization then one runtime authorization
  (recommended):** Keeps the two-message workflow while binding runtime
  authority to final source and evidence digests and explicitly allowlisting
  the one historical compatibility-test transition.
- **B. Combine build and runtime:** Grants machine authority before final source
  digests are known.
- **C. Reuse the consumed authorization:** Not permitted by the accepted retry
  policy.
- **D. Stop:** Retains current evidence but leaves Phase 3 incomplete.

Recommended selection: `A/A/A/A/A`.

Selecting options authorizes preparation only of a separate non-effective U4D
source implementation authorization proposal. It does not authorize source or
test implementation, PowerShell execution, another runtime attempt, machine or
storage access, `F:`, U3K, models, media/data, deployment, commit, push, or
remote Git.
