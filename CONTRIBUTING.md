# Contributing To H-CAM Model M-1

`model-m-1` is the integration repository for the `hcam-1-0` collaborator
organization. Contributions should be reviewable, reproducible, and explicit
about safety, data, compatibility, and validation.

## Repository Boundary

`hcam-1-0` and `hcam-2-0` are separate organizations. Do not push, mirror,
merge, or copy work between them unless that exact transfer has been approved.
A reference to H-CAM 2 in historical evidence records provenance; it does not
make H-CAM 2 an automatic remote or deployment target.

## Contribution Workflow

1. Search existing issues and the
   [H-CAM Delivery Project](https://github.com/orgs/hcam-1-0/projects/1).
2. Open the issue form that best matches the work: bug, phase task,
   architecture decision, review question, or risk/compliance item.
3. Define the intended outcome, acceptance criteria, safety boundary, target
   execution profile, validation plan, and rollback before implementation.
4. Create a focused branch from the latest `main`.
5. Keep changes scoped to the linked issue. Do not mix unrelated formatting,
   generated evidence, dependencies, or refactors into the same pull request.
6. Run the smallest relevant checks first, then the broader checks required by
   the affected phase or workflow.
7. Open a pull request and complete every applicable section of the template.
8. Resolve review findings and confirm that documentation, Project status, and
   limitations match the final change.

Suggested branch names:

```text
feature/<issue>-<short-name>
fix/<issue>-<short-name>
docs/<issue>-<short-name>
test/<issue>-<short-name>
experiment/<issue>-<short-name>
```

Use clear, imperative commit messages. Conventional prefixes such as `feat:`,
`fix:`, `docs:`, `test:`, `ci:`, and `chore:` are preferred.

## Local Setup And Validation

Start with [ONBOARDING.md](ONBOARDING.md) and
[TEAMMATE_SETUP.md](TEAMMATE_SETUP.md). Follow the phase documentation for
specialized validation. Never weaken a check merely to make a pull request
green; document an environment limitation and open follow-up work instead.

At minimum, verify that the working tree is intentional and free of patch
formatting errors:

```powershell
git status --short
git diff --check
```

Use generated or synthetic fixtures in automated testing. Live-camera,
provider, hardware, model, dataset, deployment, or Government-data validation
requires an explicit bounded authorization and must not be inferred from a
normal issue or pull request.

## Data And Security Rules

Never commit or paste:

- credentials, passwords, tokens, cookies, private keys, or secret values;
- signed media URLs, private camera addresses, or unrestricted provider URLs;
- CCTV footage, snapshots, recordings, or biometric material;
- Government, police, vehicle-owner, registration, watchlist, case, evidence,
  or personally identifiable data;
- raw security findings that would help someone exploit a system.

Keep synthetic data visibly labeled. Preserve auditability, authorization,
department isolation, least privilege, retention boundaries, and fail-closed
behavior. See [SECURITY.md](SECURITY.md) before reporting a vulnerability.

## Review Standard

Reviewers prioritize correctness, regressions, security, privacy, contract
compatibility, migration safety, accessibility, resource bounds, recovery,
tests, and unsupported claims. Approval of code does not authorize deployment,
live systems, operational actions, or movement to another project phase.
