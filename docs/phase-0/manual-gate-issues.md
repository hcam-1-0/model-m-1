# Manual Gate Issues

These GitHub issues track the remaining Phase 0 gates that cannot be completed
by automation alone. They are the live work items that must close before H-CAM
moves into Phase 1 implementation.

## Gate Issue Index

| Gate | Issue | Status | Required Evidence |
| --- | --- | --- | --- |
| Review Phase 0 docs with project owner | [#10](https://github.com/mayankthakor227/h-cam-2.0/issues/10) | Open | Owner review outcome recorded in `owner-review.md` or linked PR/issue comment |
| Confirm official challenge constraints and dataset rules | [#11](https://github.com/mayankthakor227/h-cam-2.0/issues/11) | Satisfied by official public portal intake on 2026-08-18 | Official rules, dataset policy, sensitive-data policy, demo rules, and source evidence recorded in `official-constraints-intake.md` |
| Approve, revise, or reject proposed Phase 1 decisions | [#12](https://github.com/mayankthakor227/h-cam-2.0/issues/12) | Open | DR-0004 and DR-0005 resolved in `decision-records.md`, with follow-up docs updated |
| Authorize Phase 1 camera registry implementation start | [#13](https://github.com/mayankthakor227/h-cam-2.0/issues/13) | Open | Previous gate issues closed and explicit owner/user instruction to move to Phase 1 |

## Labels

The gate issues use these repository labels:

- `phase-0`: Phase 0 foundation, validation, and review work.
- `phase-gate`: Required gate before moving between project phases.
- `manual-gate`: Requires human owner or official approval.
- `needs-owner-review`: Needs project-owner review before closure.
- `official-rules`: Depends on official challenge rules or source material.

## Closure Policy

Do not close a manual gate issue because tests pass. Automated checks prove
repository readiness only. A gate closes only when the issue acceptance criteria
are satisfied and the corresponding Phase 0 document is updated.

## Phase 1 Guardrail

Issue #13 is the final Phase 1 entry gate. Phase 1 should not start until the
remaining owner gates #10 and #12 are closed, official intake issue #11 is
closed with its evidence, and the project owner explicitly approves Phase 1
camera registry backend implementation.
