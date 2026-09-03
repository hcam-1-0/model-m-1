# P3.6 Quarantine Transaction Runner R0 Implementation Authorization Proposal

Decision: `D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH`

Status: sealed non-effective owner-authorization proposal pending exact owner
review. This document and its package do not authorize runner implementation,
runner execution, storage or hardware queries, `F:` access, ACL work, Defender,
scanners, downloads, models, deployment, or remote Git.

## Why This Gate Exists

U3G used an ephemeral one-shot transaction and failed closed at DACL semantic
verification. U3H selected a reviewable content-hashed runner proposal before
separate implementation and execution authority. It also separated storage
from Defender so that one failure cannot consume authority for both paths.

The accepted U3H record has SHA-256
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`
and binds package digest
`19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
It authorizes preparation of this proposal, not implementation.

## Proposed Runner Design

The proposal contains no executable handler. Its plain-text source design binds
the intended transaction sequence, default-deny dispatch, failure behavior,
cleanup boundaries, sanitization, and non-authority. The associated JSON
contract defines the future interface and evidence requirements.

The future implementation must use a static mapping for exactly ten reserved
storage actions, `U3K-A01` through `U3K-A10`. Unknown, missing, duplicate,
reordered, disabled, or mutated actions must fail before machine access.
Dynamic evaluation, script blocks from data, reflection-based lookup, command
strings, shell fallbacks, plugins, and environment-defined handlers are
prohibited.

## Runtime Binding

The proposed implementation family is PowerShell 7 on Windows, with canonical
candidate path `C:\Program Files\PowerShell\7\pwsh.exe` and fixed noninteractive
flags. This planning package does not query that path or claim that a particular
version is present or trusted.

Before any execution proposal, a later package must bind the exact regular,
non-reparse runtime path, size, file and product versions, SHA-256, cache-only
trust result, exact implemented runner path, and exact runner SHA-256. Alternate
runtime or path fallback and network retrieval are prohibited.

## Generated Contract Vectors

Twenty non-executable vectors cover:

- package, core-file, owner-statement, window, attempt, runner, and runtime
  binding failures;
- unknown, missing, duplicate, reordered, and disabled action denial;
- path, volume, probe-size, timeout, and output-path mutation denial;
- existing-root fail-closed behavior;
- exact `Modify | Synchronize` normalization and excessive-rights rejection;
- independent principal, rule-count, rights, inheritance, propagation, deny,
  and unauthorized-principal classification;
- generated probe success, failure, cleanup, and zero retention;
- denial of every Defender action from the storage-only profile; and
- output sanitization and write-allowlist enforcement.

The vectors contain no media, private data, machine facts, raw ACL, SID,
security descriptor, or probe payload. They do not provide an execution
harness. If implementation is later authorized, its contract tests remain
machine-independent and network-free.

## What Exact Acceptance Would Authorize

Exact acceptance of the final package digest would authorize only:

- one reviewable PowerShell runner source file;
- one generated-only, machine-independent contract harness for the twenty
  sealed vectors;
- one non-observational implementation-evidence record; and
- one sealed implementation package for later owner review.

It would not authorize running any handler or observing a local runtime. The
implemented source and test evidence must be sealed and accepted before a
storage execution package can be issued.

## Exact Owner Statement Template

The final manifest digest replaces
`<RUNNER_PROPOSAL_PACKAGE_DIGEST_SHA256>`:

```text
D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH: I, mayank-admin, authorize implementation only of the non-executable P3.6 quarantine transaction-runner R0 proposal against package digest <RUNNER_PROPOSAL_PACKAGE_DIGEST_SHA256>. Implementation is limited to one reviewable PowerShell source file, a machine-independent generated-only contract harness for all twenty sealed vectors, and non-observational implementation evidence and package records. The implementation must retain static default-deny dispatch, exact sealed inputs, bounded sanitized outputs, zero-retention generated fixtures, and fail-before-machine-access behavior. This does not authorize running the runner against F: or any machine resource, querying hardware/storage/runtime/ACL/Defender/scanners, a storage attempt, runtime binding observation, downloads, models, inference, cameras/media/data, containers/Kubernetes, deployment, or remote Git. Execution requires a later exact implemented-source and runtime-bound package plus separate digest-bound owner authorization.
```

`Continue`, the U3H acceptance, or acceptance of a storage proposal cannot be
interpreted as runner implementation or execution authority.
