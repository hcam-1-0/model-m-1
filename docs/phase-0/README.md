# Phase 0 Foundation

Status: complete and accepted on 2026-08-18.

Phase 0 converts the H-CAM idea into a controlled engineering baseline. The goal
is to define what we are building, what is out of scope, what must be proven
before implementation, and what safety boundaries must exist before connecting
real CCTV, government datasets, watchlists, or police workflows.

This phase is planning plus environment validation. It intentionally keeps
product implementation thin until scope, data boundaries, and acceptance gates
are explicit.

## Objectives

- Define the H-CAM product mission, users, workflows, and success criteria.
- Convert the Gujarat Police innovation challenge direction into deployable
  enterprise software requirements.
- Establish a modular architecture baseline for camera ingestion, AI analytics,
  intelligence correlation, operator applications, security, and data storage.
- Document data governance, safety, privacy, audit, and legal authorization
  requirements before using sensitive data.
- Validate the Sentinel Gujarat CCTV reference environment with safe read-only
  tools.
- Produce Phase 1 handoff criteria so implementation starts from a stable
  foundation.

## Deliverables

| Deliverable | Purpose | Status |
| --- | --- | --- |
| [Product Brief](product-brief.md) | Defines mission, users, product surfaces, outcomes, non-goals | Complete |
| [Requirements](requirements.md) | Functional and non-functional requirements for H-CAM | Complete |
| [Architecture Baseline](architecture-baseline.md) | Modular system architecture and first service boundaries | Complete |
| [Data Governance](data-governance.md) | Safety, privacy, data classes, retention, audit, and access policy | Complete |
| [Validation Plan](validation-plan.md) | Test strategy and evidence expected before moving phases | Complete |
| [Roadmap](roadmap.md) | Phase 0 milestones and Phase 1 entry plan | Complete |
| [Acceptance Checklist](acceptance-checklist.md) | Exit gates for Phase 0 | Accepted |
| [Phase 1 Handoff](phase-1-handoff.md) | First implementation scope, stack direction, and done criteria | Complete |
| [Decision Records](decision-records.md) | Phase 0 architecture decisions and proposed Phase 1 decisions | Accepted |
| [Phase 1 Backlog](phase-1-backlog.md) | Implementation backlog for the first backend foundation | Delivered |
| [Backlog Traceability](backlog-traceability.md) | Maps Phase 0 deliverables and remaining review work | Current |
| [Review Questions](review-questions.md) | Questions answered or deferred before Phase 1 | Complete |
| [CCTV Environment](cctv-environment.md) | Sentinel reference environment and probe workflow | Implemented |
| [Team Workflow](team-workflow.md) | Six-person GitHub workflow, PR rules, issue templates, and safety gates | Complete |
| [Readiness Report](readiness-report.md) | Automated Phase 0 evidence, manual gates, and full validation command | Complete |
| [Owner Review](owner-review.md) | Project-owner acceptance record | Accepted |
| [Official Constraints Intake](official-constraints-intake.md) | Source capture packet for challenge rules, datasets, demos, and sensitive data | Accepted baseline |
| [Manual Gate Issues](manual-gate-issues.md) | GitHub issue index for the four resolved Phase 0 manual gates | Closed |

## Current Build Artifacts

- `tools/sentinel_cctv_probe.py`: read-only Sentinel CCTV metadata/state/stream
  probe.
- `tools/phase0_readiness.py`: offline Phase 0 readiness verifier and local
  validation runner.
- `fixtures/sentinel/`: local ignored snapshot output location.
- `tests/`: offline regression tests for probe behavior and Phase 0 docs.
- `.github/workflows/python-ci.yml`: CI gate for Python compile and unit tests.
- `.github/ISSUE_TEMPLATE/`: issue forms for phase tasks, decisions, risks, and
  review questions.
- `.github/PULL_REQUEST_TEMPLATE.md`: PR review baseline for scope, safety, and
  validation evidence.

## Phase 0 Commands

```powershell
python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py
python -m unittest discover -s tests -v
python tools/phase0_readiness.py --run-validation
python tools/sentinel_cctv_probe.py metadata --json
python tools/sentinel_cctv_probe.py snapshot
python tools/sentinel_cctv_probe.py offline-summary
python tools/sentinel_cctv_probe.py registry-export --output fixtures/sentinel/registry-seed.json
```

## Phase 1 Entry Rule

Phase 1 began after the Phase 0 acceptance checklist was approved and is now
complete. The links below remain the authoritative handoff and historical
decision record for the camera registry and stream-state foundation.

Phase 0 maintenance review:

- [Phase 1 Handoff](phase-1-handoff.md)
- [Decision Records](decision-records.md)
- [Phase 1 Backlog](phase-1-backlog.md)
- [Review Questions](review-questions.md)
- [Team Workflow](team-workflow.md)
- [Readiness Report](readiness-report.md)
- [Owner Review](owner-review.md)
- [Official Constraints Intake](official-constraints-intake.md)
- [Manual Gate Issues](manual-gate-issues.md)
- [Backlog Traceability](backlog-traceability.md)
