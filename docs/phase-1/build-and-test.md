# Phase 1 Build And Test Standard

Phase 1 is validated as source code, a database migration chain, and an
installable Python distribution. Passing API tests alone is not sufficient.

## Supported Interpreters

CI tests the declared backend on Python 3.12, Python 3.13, and Python 3.14. Local
development may use any of these versions. A new interpreter version must be
added to CI before the project claims support for it.

## Clean Development Install

```powershell
uv sync --locked --extra dev
```

The repository requires uv `0.12.3`. `uv.lock` is the reviewed universal
dependency graph for Python 3.12-3.14; local, CI, package, and container checks
must not silently regenerate it.

Verify the environment before testing:

```powershell
uv lock --check
uv pip check
uv run --locked --extra dev pip-audit --skip-editable
```

The source distribution includes the Python test suite and JSON fixtures used
by its readiness tools, in addition to deployment, contract, documentation,
and GitHub governance assets. This allows an extracted sdist to reproduce the
offline governance checks instead of depending on files only present in a Git
checkout.

## Static And Automated Tests

```powershell
uv run --locked --extra dev ruff check app tests tools migrations
uv run --locked --extra dev python -m compileall -q app tools migrations
uv run --locked --extra dev python tools\release_contracts.py check
uv run --locked --extra dev pytest --cov=hcam --cov-report=term-missing --cov-fail-under=90
uv run --locked --extra dev python tools\phase0_readiness.py --run-validation --strict
uv run --locked --extra dev python tools\phase1_readiness.py --run-validation
uv run --locked --extra dev python tools\phase1_performance.py --cameras 1000 --iterations 100 --json
uv run --locked --extra dev python tools\phase1_load.py --cameras 1000 --requests 400 --concurrency 16 --json
```

Coverage is a regression floor, not proof that behavior is correct. The suite
also includes API authorization, audit, malformed input, direct database
constraint, optimistic concurrency, migration-head readiness, CLI, and
migration round-trip tests.

The reviewed Phase 0-2 release baseline is stored in
`contracts/phase-2/openapi.json` and `contracts/phase-2/database.json`. The
contract check renders the real FastAPI schema and upgrades a disposable
SQLite database through Alembic before comparing exact normalized metadata.
Intentional changes require API, RBAC, migration, index, foreign-key, and
constraint review before running:

```powershell
uv run --locked --extra dev python tools\release_contracts.py write --acknowledge-reviewed-change
```

## Migration Lifecycle

Use a disposable database for the destructive round trip:

```powershell
$env:HCAM_DATABASE_URL = "sqlite:///./var/phase1-migration-test.db"
uv run --locked --extra dev alembic upgrade head
uv run --locked --extra dev alembic check
uv run --locked --extra dev alembic downgrade base
uv run --locked --extra dev alembic upgrade head
uv run --locked --extra dev alembic check
```

The readiness endpoint rejects databases that are missing required camera
columns or whose Alembic revision does not match the application schema head.
Automatic `create_all` schema creation is forbidden in production.

## Distribution Build

Build both standard Python artifacts:

```powershell
uv run --locked --extra dev python -m build --no-isolation
```

The source distribution includes the Alembic configuration, migration chain,
reviewed contracts, documentation, synthetic seed fixture, and the Markdown/YAML
GitHub governance assets exercised by repository tests. CI installs the wheel
into a new virtual environment and verifies package metadata, application
creation, and the `hcam` command before accepting the build.

When a dependency constraint intentionally changes, run `uv lock`, review the
complete `uv.lock` diff, run `uv lock --check`, and include the lock change in
the same review as `pyproject.toml`. Do not hand-edit the lock file.

Build output under `dist/`, coverage data, local databases, and generated
Sentinel fixtures are ignored by Git.

## CI Acceptance

Every pull request and `main` push must pass:

- Python 3.12, Python 3.13, and Python 3.14 compile and test jobs;
- Ruff error and bug checks;
- at least 90% branch-aware `hcam` package coverage;
- dependency consistency and vulnerability audit;
- immutable `setup-uv` action pinning and `uv.lock` enforcement;
- migration upgrade and drift checks;
- reviewed OpenAPI and database contract drift checks;
- Phase 0 and Phase 1 readiness checks;
- isolated wheel installation and command smoke tests.
- bounded sequential and concurrent synthetic load checks;
- measured SQLite recovery drill;
- digest-pinned, non-root image and hardened Compose runtime validation.

Third-party GitHub Actions are pinned to reviewed commit SHAs while retaining
their release-version comments. Dependency consistency and vulnerability
audits run separately from this workflow supply-chain control.

No CI job connects to production CCTV, downloads video, or accesses Government
or police data.

## PostgreSQL Integration

The optional PostgreSQL test dependency is installed with:

```powershell
uv sync --locked --extra dev --extra postgres
```

GitHub Actions owns the authoritative Phase 1 PostgreSQL integration run. It
uses an isolated PostgreSQL 18 service container, applies and checks migrations,
runs the synthetic registry integration contract, and verifies downgrade and
re-upgrade. Local execution requires an explicitly disposable database URL:

```powershell
$env:HCAM_DATABASE_URL = "postgresql+psycopg://.../disposable_hcam_test"
$env:HCAM_POSTGRES_TEST_URL = $env:HCAM_DATABASE_URL
uv run --locked --extra dev --extra postgres alembic upgrade head
uv run --locked --extra dev --extra postgres pytest -q -m postgres tests/test_postgres_integration.py
```

Never point these destructive migration-round-trip commands at a shared or
production database.

## Operational Validation

SQLite backup/restore and synthetic performance commands are documented in
[operations-and-observability.md](operations-and-observability.md). The
performance threshold is a regression guard for CI, not a production SLO or
capacity statement.

Run a disposable recovery drill after migrating and seeding a local SQLite
database:

```powershell
.\.venv\Scripts\hcam recovery-drill .\backups\phase1-drill
```

Validate the container model and image when Docker is available:

```powershell
docker build --check .
docker build --build-arg "VCS_REF=$(git rev-parse HEAD)" -t hcam-core:phase1 .
```

The authoritative CI container job additionally renders the Compose model,
starts PostgreSQL 18, runs migrations separately, starts the API as UID/GID
10001 with a read-only root filesystem and dropped capabilities, and probes
liveness, readiness, registry authorization, and protected metrics.
