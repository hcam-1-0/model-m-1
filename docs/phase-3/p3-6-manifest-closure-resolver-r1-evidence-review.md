# P3.6 U4F Manifest Closure Resolver R1

## Outcome

The U4F source remediation is implemented and locally validated. It replaces the
R2 all-paths-equal closure assumption with a typed resolver while preserving the
consumed R2 authorization, result, evidence, and action specification unchanged.

The implementation binds the delegated recommended selection for
`D-P3.6-U4E-001` through `D-P3.6-U4E-005` as `A/A/A/A/A`. The delegation record
explicitly distinguishes owner delegation from agent selection.

## Resolver Policy

- Path-valued load-bearing entries resolve from the manifest directory and must
  remain below the module root and exact PSHome.
- Bare binary names in `NestedModules` and `RequiredAssemblies` use exactly two
  ordered candidates: manifest directory, then the exact PSHome root.
- Two present candidates are ambiguous and fail closed.
- Every selected load-bearing target must be regular, non-reparse, trusted, and
  individually and collectively size bounded.
- `FileList` remains informational. Missing non-code inventory is counted and
  allowed without path retention; missing code-like inventory fails closed.
- Absolute, UNC/device, URI, wildcard, variable, expression, traversal,
  out-of-root, duplicate, malformed, reparse, untrusted, and overbound inputs
  fail closed.

This distinction follows Microsoft's documented manifest model: `RootModule`
paths are relative to the manifest, `NestedModules` entries can be module names
or paths, `RequiredAssemblies` accepts a filename or path, and `FileList` is an
informational inventory.

## Evidence

- 512 deterministic generated cases across 16 boundary groups.
- Focused validation: 530 passed, 0 failed.
- Complete Phase 3.6 validation: 2,573 passed, 0 failed across 77 test files.
- Ruff passed.
- Git diff check passed; only the pre-existing Windows line-ending warnings
  were emitted.
- The PowerShell policy module loaded under the exact local PowerShell 7 runtime
  and emitted the expected version 1.1.0 projection.

The bounded local diagnostic established why R2 failed: the Utility manifest's
single `NestedModules` value is a bare DLL name; the manifest-directory candidate
is absent, while the exact PSHome candidate exists and has valid local
Authenticode status. No raw paths, manifest text, parser tokens, exception
material, or security material were retained in evidence.

## Remaining Boundary

This evidence completes the U4F source remediation. It is not full R3 closeout
evidence and does not claim cache-only WinVerifyTrust closure, U3K storage
success, Phase 3 completion, deployment, or remote Git publication. R3 must bind
the exact final U4F package, execute the complete ordered validation once, and
only then proceed to the existing U3K and Phase 3 closeout gates.
