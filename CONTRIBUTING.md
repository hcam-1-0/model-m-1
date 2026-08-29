# Contributing to H-CAM

H-CAM is a security-sensitive camera registry, GIS, and stream-management system. Contributions must be reviewable, testable, and free of operational or personally sensitive data.

## Start With A GitHub Item

Use the structured issue forms for phase tasks, architecture decisions, risks, and review questions. Keep one observable outcome per issue and link it to the organization Project when available.

For code changes:

1. Create a branch from the approved base branch.
2. Keep camera-provider, recording, analytics, and control changes explicitly separated in scope.
3. Add or update tests before opening a pull request.
4. Use the pull request template and link the relevant issue or Project item.
5. Do not merge until required checks and reviews pass.

Direct pushes to `main` are not part of the normal workflow. The `Camera-adapter` and `live-test` branches remain isolated until a reviewed pull request authorizes integration.

## Local Validation

```powershell
uv sync --locked --extra dev --extra postgres --extra cam-adapter
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"
uv run --locked --extra dev --extra postgres --extra cam-adapter ruff check app tests tools migrations
uv run --locked --extra dev --extra postgres --extra cam-adapter pytest
git diff --check
```

Use the PostgreSQL and synthetic-lab evidence commands in `docs/phase-2/build-and-test.md` only against disposable test systems.

## Data And Media Rules

- Never commit CCTV video, screenshots containing identifiable people or plates, credentials, cookies, private camera locators, government records, or production exports.
- Use synthetic fixtures and redacted metadata.
- Keep recordings, analytics, model execution, and camera control disabled unless the issue and pull request explicitly authorize them.
- Use exact host allow-lists. Do not crawl domains or probe unapproved endpoints.
- Report security-sensitive findings privately under the repository Security tab.

## Review Expectations

Reviewers check API compatibility, authorization, department scope, egress controls, data retention, failure behavior, migrations, operational rollback, and test evidence. HTTP success alone is not evidence that browser video decoded; media work should also report player state or a clearly documented verification gap.
