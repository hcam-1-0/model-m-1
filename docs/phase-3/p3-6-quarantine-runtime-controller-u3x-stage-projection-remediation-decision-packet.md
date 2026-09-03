# P3.6 U3X Stage-Projection Remediation Decisions

## Current Evidence

The single U3W attempt is consumed and failed closed with
`controller_stage_projection_invalid`. Runtime trust and all five accepted
source bindings succeeded and remained stable. The diagnostic ran once, did
not time out, emitted 485 bytes of bounded output, emitted zero stderr, and
retained no raw controller projection or failure detail.

The retained reason proves that top-level shape, contract identity, terminal
state, and reason-family validation passed before stage validation failed. It
does not reveal the candidate stage values or types.

## Leading Static Hypothesis

The accepted controller's successful `policy_valid` path passes `$null` as
`FailedAction` to a parameter declared `[AllowNull()] [string]`. The controller
then projects that parameter directly. The accepted diagnostic requires exact
`null` for both `failed_action` and `failed_stage` on success.

PowerShell may coerce the string-typed null input to an empty string. This is a
high-confidence inference, not a retained runtime fact. Weakening the contract
to accept both values would create two success representations, so the
recommended direction is an additive controller successor with explicit null
preservation.

## Decisions

### D-P3.6-U3X-001: First Remediation Surface

- **A. Additive controller R1 successor (recommended):** preserve historical
  sources and add explicit null-preserving construction.
- **B. Loosen the diagnostic contract:** accept null or empty string.
- **C. Replace controller and diagnostic together:** widest blast radius.
- **D. Stop remediation:** keep runtime validation and U3K blocked.

### D-P3.6-U3X-002: Canonical Stage Projection Semantics

- **A. Exact null on success (recommended):** `18`, `null`, `null`; failures use
  nonempty allowlisted action and reason strings.
- **B. Omit failure fields on success:** requires a schema-version change.
- **C. Accept null or empty string:** tolerant but noncanonical.
- **D. Use empty strings canonically:** changes the accepted wire contract.

### D-P3.6-U3X-003: Validation Ladder

- **A. Static then bounded PowerShell contract validation (recommended):** add
  generated cross-language vectors, accept source evidence, then separately
  authorize a generated-only PowerShell contract check.
- **B. Generated static evidence only:** does not close the language-semantics
  gap.
- **C. Direct system diagnostic:** uses a costly system attempt too early.
- **D. No validation package:** keeps runtime reentry closed.

### D-P3.6-U3X-004: Runtime Reentry Sequence

- **A. Two-gate validation then one diagnostic (recommended):** source
  acceptance, generated-only contract validation and acceptance, then one new
  digest-bound system diagnostic; U3K remains blocked until success acceptance.
- **B. Blind retry accepted sources:** no new diagnostic value.
- **C. Advance directly to U3K:** breaks the existing gate.
- **D. Do not reenter runtime validation:** preserve the block.

## Current Authority

This packet is planning only. All four owner decisions remain pending. It does
not authorize controller, diagnostic, contract, vector, or test implementation;
PowerShell or Python machine execution; runtime or hardware observation;
machine, storage, scanner, network, model, camera, media, data, container,
Kubernetes, deployment, U3K, another attempt, or remote Git.
