# Repository Governance

## Branches And Reviews

- `main` is the reviewed integration branch.
- `Camera-adapter` is the camera-adapter integration branch.
- `live-test` and other lab branches remain isolated and must not silently change production behavior.
- Meaningful changes use issues, pull requests, required checks, and explicit reviewer decisions. Direct pushes to `main` are avoided.

## Decision Records

Use the architecture-decision issue form for changes to authentication, camera egress, API contracts, storage, recording, analytics, control, retention, deployment, or cross-repository ownership. Use the risk form when a security, privacy, compliance, or availability control must be tracked independently.

## GitHub Project Model

The organization delivery Project should use these fields:

| Field | Suggested values |
|---|---|
| Status | Backlog, Ready, In progress, In review, Blocked, Done |
| Priority | Critical, High, Medium, Low |
| Area | Core API, GIS, Camera Adapter, Monitoring UI, Security, Operations, Organization |
| Phase | Phase 0, Phase 1, Phase 2, Camera Adapter, Future |
| Effort | XS, S, M, L, XL |
| Target | Iteration or milestone date |

Recommended views are Roadmap, Current iteration, Camera Adapter, Security and risk, and Done. Automation should add new repository issues and pull requests to the Project; moving an item to Done requires linked evidence rather than only a status change.

## Releases

Releases are cut from reviewed commits, use generated release notes, and identify migrations, compatibility changes, security considerations, rollback steps, and any manual deployment gates. A GitHub Release is documentation of an approved artifact; it is not deployment authorization.
