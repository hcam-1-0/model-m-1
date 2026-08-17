# Phase 0 Foundation

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
| [Product Brief](product-brief.md) | Defines mission, users, product surfaces, outcomes, non-goals | Started |
| [Requirements](requirements.md) | Functional and non-functional requirements for H-CAM | Started |
| [Architecture Baseline](architecture-baseline.md) | Modular system architecture and first service boundaries | Started |
| [Data Governance](data-governance.md) | Safety, privacy, data classes, retention, audit, and access policy | Started |
| [Validation Plan](validation-plan.md) | Test strategy and evidence expected before moving phases | Started |
| [Roadmap](roadmap.md) | Phase 0 milestones and Phase 1 entry plan | Started |
| [Acceptance Checklist](acceptance-checklist.md) | Exit gates for Phase 0 | Started |
| [Phase 1 Handoff](phase-1-handoff.md) | First implementation scope, stack direction, and done criteria | Started |
| [Decision Records](decision-records.md) | Phase 0 architecture decisions and proposed Phase 1 decisions | Started |
| [Phase 1 Backlog](phase-1-backlog.md) | Implementation backlog for the first backend foundation | Started |
| [Review Questions](review-questions.md) | Questions to answer before coding Phase 1 | Started |
| [CCTV Environment](cctv-environment.md) | Sentinel reference environment and probe workflow | Implemented |
| [Team Workflow](team-workflow.md) | Six-person GitHub workflow, PR rules, issue templates, and safety gates | Started |
| [Readiness Report](readiness-report.md) | Automated Phase 0 evidence, manual gates, and full validation command | Started |

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

Phase 1 should not start until the Phase 0 acceptance checklist is reviewed.
The first implementation phase should build the platform foundation around the
camera registry and stream state model proven by the Sentinel probe.

Before coding Phase 1, review:

- [Phase 1 Handoff](phase-1-handoff.md)
- [Decision Records](decision-records.md)
- [Phase 1 Backlog](phase-1-backlog.md)
- [Review Questions](review-questions.md)
- [Team Workflow](team-workflow.md)
- [Readiness Report](readiness-report.md)
