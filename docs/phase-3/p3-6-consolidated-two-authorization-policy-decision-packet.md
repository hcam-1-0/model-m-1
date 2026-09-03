# P3.6 Consolidated Two-Authorization Policy

## Objective

This proposal reduces the remaining Phase 3.6 owner workflow to two explicit,
digest-bound authorization messages. Internal validation gates remain ordered
and fail closed, but successful internal transitions no longer require a new
owner message at every step.

`continue` authorizes preparation of this proposal only. It does not select an
option or authorize source implementation, PowerShell, runtime, machine,
storage, U3K, closeout, commit, push, or remote Git action.

## Special Authorization 1: Consolidated Build

Decision ID: `D-P3.6-CONSOLIDATED-BUILD-AUTH`.

The first future statement will both select the six policy decisions and
authorize all remaining non-machine Phase 3.6 work. Under the recommended
policy it covers:

- exactly 20 additive source, generated-test, evidence, and second-package
  preparation paths;
- exactly 13 existing ledger, documentation, and LF synchronization paths;
- up to eight in-scope source revision, validation, and reseal cycles;
- machine-disabled Python generated and static validation;
- final immutable build evidence and preparation of the second authorization
  package.

It does not permit PowerShell parsing or execution, machine observation,
storage, networking, models, cameras, media, deployment, commit, push, or remote
Git.

## Special Authorization 2: Runtime And Closeout

Decision ID: `D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH`.

The second statement can only be prepared after the build succeeds and the
source plus action package has an exact digest. Under the recommended policy it
may authorize:

- package-bound generated PowerShell controller validation;
- exact runtime identity, hash, trust, source, process, and result validation;
- the exact controlled U3K storage actions bound by that future package;
- no more than three total attempts, with retries limited to allowlisted
  transient failures while every source and package hash remains unchanged;
- sanitized evidence, canonical ledger and documentation synchronization;
- conditional Phase 3 completion and one local checkpoint commit if and only if
  every required gate passes.

It cannot authorize source changes after binding, raw material retention,
`B:`, unlisted `F:` paths, cameras, media, private or Government data, model
downloads or inference, networking, installation, updates, containers,
Kubernetes, deployment, push, or remote Git.

## Failure Behavior

Any path, action, scope, hash, trust, deterministic contract, or exhausted
transient failure stops the workflow. The result is a bounded sanitized backlog,
not implicit permission to repair, retry with changed sources, widen scope, or
claim Phase 3 completion.

## Decisions

| Decision | Recommended | Meaning |
|---|---:|---|
| `D-P3.6-CA-001` | `A` | Use two special authorizations. |
| `D-P3.6-CA-002` | `A` | Build all remaining source prerequisites and prepare the runtime package. |
| `D-P3.6-CA-003` | `A` | Allow eight bounded in-scope source revision cycles. |
| `D-P3.6-CA-004` | `A` | Include generated validation, runtime binding, and exact U3K work in authorization two. |
| `D-P3.6-CA-005` | `A` | Close Phase 3 and make one local commit only after every gate passes. |
| `D-P3.6-CA-006` | `A` | Preserve history and stop fail closed on any non-transient failure. |

The recommended aggregate selection is `A/A/A/A/A/A`. Existing U4B remains the
granular fallback until the exact consolidated build authorization is accepted.
