# Team Workflow

This document defines how the six-person H-CAM team should work in the
`mayankthakor227/h-cam-2.0` repository during Phase 0 and the Phase 1 entry
period. It is a governance baseline, not product implementation.

## Operating Rule

GitHub is the source of truth for code, review evidence, CI, and repository
state. Planning decisions can be discussed in chat, Slack, Notion, Linear, or
meetings, but repository work must be represented by an issue, branch, pull
request, or documented decision before it becomes implementation.

The current Phase 0 rule remains active:

```text
Do not start Phase 1 product implementation until the Phase 0 acceptance
checklist is reviewed and the project owner approves the first implementation
scope.
```

## Team Roles

| Role | Primary Ownership | Typical Repository Work |
| --- | --- | --- |
| Lead / System Architect | Scope, architecture, final tradeoffs, phase movement | ADRs, phase docs, PR review, integration boundaries |
| Backend Engineer | APIs, database, auth, event contracts | camera registry, service skeletons, tests, API docs |
| AI / Computer Vision Engineer | detection, tracking, ANPR, model behavior | model interfaces, offline fixtures, evaluation notes |
| Frontend Engineer | command center, dashboards, operator flows | UI specs, app shell, visual validation, UX issues |
| Infrastructure / DevOps Engineer | CI, deployment, local environment, observability | workflows, Docker later, runtime docs, health checks |
| Data / GIS Engineer | metadata, GIS, evidence model, validation datasets | camera metadata, map fields, registry seed review |

Ownership does not mean isolation. Every meaningful PR should be reviewed by at
least one person outside the owning area when the change affects shared
contracts, data handling, security, or phase scope.

## Work Intake

Use GitHub issues to make work visible.

- Use `Phase Task` for planned implementation, documentation, validation, or
  research work.
- Use `Architecture Decision` when a technical choice affects module
  boundaries, data contracts, deployment, storage, AI behavior, or security.
- Use `Risk Or Compliance Item` for security, privacy, audit, retention,
  legal authorization, operational reliability, or model safety concerns.
- Use `Review Question` when a project owner or technical lead answer is
  needed before work can safely continue.

Issue descriptions should state the outcome, acceptance criteria, data handled,
validation plan, and owner. Avoid vague work items such as "improve backend" or
"make AI better" unless they are broken into testable tasks.

## Branch Policy

No direct pushes to `main`.

Use small, named branches:

```text
codex/phase-0-topic
feature/hcam-001-camera-registry
docs/phase-0-review-update
test/sentinel-offline-fixture
fix/ci-path-handling
```

For personal laptops, each developer should keep a local clone connected to the
same GitHub remote and should check status before starting work:

```powershell
git status --short --branch
git fetch origin
git switch main
git pull --ff-only
```

If local files appear that are unrelated to the current task, inspect them
before writing. Do not overwrite another teammate's work.

## Pull Request Policy

Every PR should explain scope, safety and data handling, validation, and
documentation impact. The PR template is mandatory for work that changes
repository behavior or project direction.

Required checks before review:

```powershell
python -m py_compile tools/sentinel_cctv_probe.py
python -m unittest discover -s tests -v
git diff --check
```

Additional checks should be added when the change touches a specific subsystem.
Examples:

- API schema tests for backend contracts.
- Fixture validation for registry or metadata changes.
- Screenshot or interaction evidence for UI changes.
- Deployment smoke tests for infrastructure changes.
- Model evaluation notes for AI behavior changes.

## Safety And Data Rules

The repository must not contain:

- CCTV video.
- Credentials, tokens, cookies, secrets, or private keys.
- Government database exports.
- Police records, case files, citizen records, watchlists, or owner details.
- Personally sensitive data unless explicitly authorized and governed.

Allowed during Phase 0:

- Public documentation.
- Synthetic examples clearly marked as synthetic.
- Metadata-only Sentinel environment observations.
- Ignored local fixtures under `fixtures/sentinel/`.
- Tests that mock network and stream behavior.

Generated Sentinel snapshots and registry seed outputs are local development
artifacts unless reviewed and explicitly promoted. They remain ignored by Git so
they do not become accidental evidence, data dumps, or stale source of truth.

## Tool Boundaries

Slack, Notion, Linear, and similar tools can help coordinate the team, but they
do not replace repository evidence.

- Slack: quick questions, daily coordination, blockers, announcements.
- Notion: long-form planning, project notes, architecture narratives,
  presentation preparation, meeting notes.
- Linear: optional structured issue planning if the team later connects it.
- GitHub: final code, docs, branches, PRs, CI, issues, and review trail.

The practical rule is:

```text
Discuss anywhere, decide in a durable document, implement through GitHub.
```

## Phase Movement

Phase movement requires explicit approval. The team should not treat a merged PR
as permission to move from Phase 0 to Phase 1 unless the acceptance checklist is
reviewed and the project owner confirms the next phase.

Before Phase 1 starts, review:

- `docs/phase-0/acceptance-checklist.md`
- `docs/phase-0/phase-1-handoff.md`
- `docs/phase-0/phase-1-backlog.md`
- `docs/phase-0/decision-records.md`
- `docs/phase-0/review-questions.md`

## Conflict Handling

If two people edit the same area, stop and reconcile through a PR or issue
comment instead of force-pushing over the work. If generated local artifacts
change while testing, keep them untracked unless the team deliberately converts
them into stable checked-in test fixtures.

When a decision is unclear, open a `Review Question` issue instead of embedding
the assumption into implementation.
