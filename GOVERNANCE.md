# Model M-1 Governance

## Purpose

`hcam-1-0/model-m-1` is a private collaborator integration workspace. It is
not the canonical owner repository for `hcam-2-0`, and it has no automatic
synchronization, deployment, or authority relationship with that organization.

## Sources Of Truth

- GitHub code, commits, pull requests, and checks are the source of truth for
  collaborator implementation and validation.
- The [H-CAM Delivery Project](https://github.com/orgs/hcam-1-0/projects/1) is
  the source of truth for collaborator priority, ownership, and work status.
- Repository documents and accepted decision records define architecture,
  scope, safety boundaries, and known limitations.
- Discussions are for exploration. An issue or discussion does not override an
  accepted contract, authorization boundary, or repository policy.

## Change Classes

Routine collaborator changes use an issue, focused branch, pull request,
validation evidence, and documented rollback. Changes involving credentials,
permissions, production infrastructure, live cameras, providers, media,
Government or private data, models, deployments, releases, or cross-organization
transfers require explicit approval for that exact action.

Historical evidence and accepted records must not be silently rewritten to
fit a later branch, repository, or organization. Compatibility transitions
must preserve the original record and document the new context separately.

## Decisions And Acceptance

Architecture decisions state context, options, selection, consequences, and
data/security impact. Phase acceptance requires its documented evidence and
owner decision; merged code alone is not phase acceptance. A collaborator
snapshot does not inherit the original repository's Git ancestry or release
status unless that history is intentionally transferred and verified.

## Repository Roles

Repository and organization roles are managed separately from application
roles. GitHub access does not grant access to cameras, providers, datasets,
models, evidence, infrastructure, or operational systems. CODEOWNERS indicates
review ownership but does not replace GitHub authorization or explicit
high-risk approval.

## Conflict And Recovery

Resolve integration conflicts by preserving both valid capabilities where
possible, documenting any incompatibility, and preferring reversible changes.
Do not force-push shared branches or delete collaborator work without explicit
authorization. Security boundaries fail closed when required evidence,
identity, authorization, or compatibility cannot be established.
