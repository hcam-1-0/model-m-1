# Manual Gate Issues

These GitHub issues track the Phase 0 gates and their current state. The project
owner approved all remaining gates on 2026-08-18.

## Gate Issue Index

| Gate | Issue | Status | Required Evidence |
| --- | --- | --- | --- |
| Review Phase 0 docs with project owner | [#10](https://github.com/mayankthakor227/h-cam-2.0/issues/10) | Owner-approved for closure on 2026-08-18 | Owner review outcome recorded in `owner-review.md` or linked PR/issue comment |
| Confirm official challenge constraints and dataset rules | [#11](https://github.com/mayankthakor227/h-cam-2.0/issues/11) | Closed on 2026-08-17 through [PR #15](https://github.com/mayankthakor227/h-cam-2.0/pull/15) | Official rules, dataset policy, sensitive-data policy, demo rules, and source evidence recorded in `official-constraints-intake.md` |
| Approve, revise, or reject proposed Phase 1 decisions | [#12](https://github.com/mayankthakor227/h-cam-2.0/issues/12) | DR-0004 and DR-0005 owner-approved for closure on 2026-08-18 | DR-0004 and DR-0005 resolved in `decision-records.md`, with follow-up docs updated |
| Authorize Phase 1 camera registry implementation start | [#13](https://github.com/mayankthakor227/h-cam-2.0/issues/13) | Owner-authorized for closure on 2026-08-18 | Previous gate issues closed and explicit owner/user instruction to move to Phase 1 |

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

The project owner accepted Phase 0, approved DR-0004 and DR-0005, and explicitly
authorized Phase 1. Issues #10, #12, and #13 can close with the merged acceptance
evidence. Sensitive integrations remain separately blocked until authorized.
