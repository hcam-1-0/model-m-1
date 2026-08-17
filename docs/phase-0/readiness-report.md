# Readiness Report

This report explains the current Phase 0 completion state and how to prove it
from the repository.

## Current Status

Phase 0 is ready for owner review from an automated engineering perspective.
It is not approved for Phase 1 product implementation until the remaining
manual gates are answered.

Automated readiness means:

- Phase 0 product, requirements, architecture, governance, validation, roadmap,
  Sentinel environment, handoff, backlog, team workflow, owner review, and
  official constraints intake documents exist.
- The remaining manual gates are tracked as GitHub issues #10, #11, #12, and
  #13.
- The Sentinel CCTV probe is implemented as a read-only, metadata-oriented
  environment tool.
- Offline tests cover the Sentinel probe behavior, Phase 0 document structure,
  GitHub governance templates, and readiness verifier.
- GitHub Actions runs the offline validation suite.
- Generated Sentinel JSON fixtures are ignored under `fixtures/sentinel/`.
- No CCTV video, credentials, government datasets, police records, watchlists,
  owner details, or personally sensitive data should be committed.

## Automated Verification

Run the full local Phase 0 readiness check:

```powershell
python tools/phase0_readiness.py --run-validation
```

This performs static repository checks and then runs:

```powershell
python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py
python -m unittest discover -s tests -v
git diff --check
```

For machine-readable output:

```powershell
python tools/phase0_readiness.py --run-validation --json
```

The expected status before owner approval is:

```text
ready_for_owner_review
```

That status means automated gates pass, but manual gates remain.

## Manual Gates Still Required

These items cannot be truthfully completed by code alone:

- Review Phase 0 docs with the project owner.
- Confirm official challenge constraints and dataset rules before sensitive
  integration.
- Approve, revise, or reject the proposed Phase 1 decisions.
- Start camera registry backend implementation only after Phase 1 is approved.

These gates protect the project from accidentally moving into real police data,
watchlists, government database integrations, or CCTV storage without explicit
authorization and policy.

## Evidence Map

| Evidence | File Or Command |
| --- | --- |
| Product scope | `docs/phase-0/product-brief.md` |
| Requirements | `docs/phase-0/requirements.md` |
| Architecture baseline | `docs/phase-0/architecture-baseline.md` |
| Data governance | `docs/phase-0/data-governance.md` |
| Sentinel environment | `docs/phase-0/cctv-environment.md` |
| Validation plan | `docs/phase-0/validation-plan.md` |
| Phase 1 handoff | `docs/phase-0/phase-1-handoff.md` |
| Phase 1 backlog | `docs/phase-0/phase-1-backlog.md` |
| Team workflow | `docs/phase-0/team-workflow.md` |
| Owner review | `docs/phase-0/owner-review.md` |
| Official constraints intake | `docs/phase-0/official-constraints-intake.md` |
| Manual gate issue index | `docs/phase-0/manual-gate-issues.md` |
| Acceptance checklist | `docs/phase-0/acceptance-checklist.md` |
| Readiness verifier | `python tools/phase0_readiness.py --run-validation` |
| Offline regression suite | `python -m unittest discover -s tests -v` |
| CI evidence | GitHub Actions `Sentinel probe offline checks` |

## Phase Movement Rule

Do not treat this report or a passing readiness command as approval to begin
Phase 1. A passing command proves repository readiness. Phase movement still
requires project-owner review and official dataset/authorization confirmation.
