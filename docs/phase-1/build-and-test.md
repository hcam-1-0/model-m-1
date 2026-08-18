# Phase 1 Build And Test Standard

Phase 1 is validated as source code, a database migration chain, and an
installable Python distribution. Passing API tests alone is not sufficient.

## Supported Interpreters

CI tests the declared backend on Python 3.12, Python 3.13, and Python 3.14. Local
development may use any of these versions. A new interpreter version must be
added to CI before the project claims support for it.

## Clean Development Install

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Verify the environment before testing:

```powershell
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\pip-audit --skip-editable
```

## Static And Automated Tests

```powershell
.\.venv\Scripts\ruff check app tests tools migrations
.\.venv\Scripts\python -m compileall -q app tools migrations
.\.venv\Scripts\pytest --cov=hcam --cov-report=term-missing --cov-fail-under=90
.\.venv\Scripts\python tools\phase0_readiness.py --run-validation --strict
.\.venv\Scripts\python tools\phase1_readiness.py --run-validation
.\.venv\Scripts\python tools\phase1_performance.py --cameras 1000 --iterations 100 --json
```

Coverage is a regression floor, not proof that behavior is correct. The suite
also includes API authorization, audit, malformed input, direct database
constraint, optimistic concurrency, migration-head readiness, CLI, and
migration round-trip tests.

## Migration Lifecycle

Use a disposable database for the destructive round trip:

```powershell
$env:HCAM_DATABASE_URL = "sqlite:///./var/phase1-migration-test.db"
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\alembic check
.\.venv\Scripts\alembic downgrade base
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\alembic check
```

The readiness endpoint rejects databases that are missing required camera
columns or whose Alembic revision does not match the application schema head.
Automatic `create_all` schema creation is forbidden in production.

## Distribution Build

Build both standard Python artifacts:

```powershell
.\.venv\Scripts\python -m build
```

The source distribution includes the Alembic configuration, migration chain,
documentation, and synthetic seed fixture. CI installs the wheel into a new
virtual environment and verifies package metadata, application creation, and
the `hcam` command before accepting the build.

Build output under `dist/`, coverage data, local databases, and generated
Sentinel fixtures are ignored by Git.

## CI Acceptance

Every pull request and `main` push must pass:

- Python 3.12, Python 3.13, and Python 3.14 compile and test jobs;
- Ruff error and bug checks;
- at least 90% branch-aware `hcam` package coverage;
- dependency consistency and vulnerability audit;
- migration upgrade and drift checks;
- Phase 0 and Phase 1 readiness checks;
- isolated wheel installation and command smoke tests.

Third-party GitHub Actions are pinned to reviewed commit SHAs while retaining
their release-version comments. Dependency consistency and vulnerability
audits run separately from this workflow supply-chain control.

No CI job connects to production CCTV, downloads video, or accesses Government
or police data.

## PostgreSQL Integration

The optional PostgreSQL test dependency is installed with:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev,postgres]"
```

GitHub Actions owns the authoritative Phase 1 PostgreSQL integration run. It
uses an isolated PostgreSQL 18 service container, applies and checks migrations,
runs the synthetic registry integration contract, and verifies downgrade and
re-upgrade. Local execution requires an explicitly disposable database URL:

```powershell
$env:HCAM_DATABASE_URL = "postgresql+psycopg://.../disposable_hcam_test"
$env:HCAM_POSTGRES_TEST_URL = $env:HCAM_DATABASE_URL
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\pytest -q -m postgres tests/test_postgres_integration.py
```

Never point these destructive migration-round-trip commands at a shared or
production database.

## Operational Validation

SQLite backup/restore and synthetic performance commands are documented in
[operations-and-observability.md](operations-and-observability.md). The
performance threshold is a regression guard for CI, not a production SLO or
capacity statement.
