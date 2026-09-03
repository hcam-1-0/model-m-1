# P3.6 U4B Outer Attempt Controller R0 Evidence Review

Status: source implementation complete under `D-P3.6-CONSOLIDATED-BUILD-AUTH`.

## Implemented Surface

- Versioned outer-controller contract with one allowlisted operation.
- Eleven ordered, fail-closed stages.
- Exact three-record parent-set contract with indexes `0`, `1`, and `2`.
- Literal Boolean predicate validation and explicit all-valid reduction.
- Authoritative PowerShell source retained as inert source during this build.
- Machine-disabled Python policy reference and cross-language oracle.
- 416 deterministic generated-only vectors across 13 required groups.
- Four focused generated/static test modules.

## Validation

- Focused generated/static checks: 464 passed, 0 failed.
- Python reference branch coverage: 100%.
- Ruff: passed.
- Full Phase 3.6 generated/static checks: 2,005 passed, 0 failed.
- Strict Phase 3 JSON: 297 files parsed without duplicate keys.
- Git diff check: passed.
- PowerShell parsing, import, dot-sourcing, and execution: not performed.

## Compatibility Amendment

`D-P3.6-CONSOLIDATED-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT` changed only two
obsolete pre-authorization path-absence assertions. Their pre-edit hashes and
post-edit hashes are recorded in the implementation evidence. No planning
package, decision, digest assertion, immutable input, unrelated test, or
security boundary was changed.

## Boundaries

This package is source and generated/static evidence only. It authorizes no
PowerShell execution, runtime or hardware observation, machine or storage
action, `F:` or `B:` access, ACL or probe action, scanner activity, network or
download, model or inference activity, camera or media access, private or
Government data, container or Kubernetes action, deployment, commit, push, or
remote Git action.

The next gate is a separate exact-digest owner authorization:
`D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH`.
