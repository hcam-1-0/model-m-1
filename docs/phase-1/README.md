# Phase 1: Camera Registry Foundation

Phase 1 starts the H-CAM product backend with one bounded domain: the normalized
camera registry. It consumes local `hcam.camera_registry.seed.v1` files and
exposes camera metadata through a stable HTTP API.

This foundation implements HCAM-001, HCAM-002, HCAM-010 through HCAM-013,
HCAM-020, HCAM-021, HCAM-030, HCAM-031, HCAM-040, and HCAM-041 from the Phase 1
backlog. It does not claim the complete CCTV integration or analytics platform.

## Included

- FastAPI application with generated OpenAPI
- SQLAlchemy camera and audit models
- Alembic migration lifecycle
- SQLite local development database
- PostgreSQL-compatible ORM boundary for later deployment
- validated local registry seed adapter
- idempotent camera upsert with import audit events
- `GET /cameras` and `GET /cameras/{camera_id}`
- audited `POST /cameras` and `PATCH /cameras/{camera_id}` management APIs
- administrator-only `POST /camera-imports` bulk API onboarding
- source, department, type, health, and operational-status filters
- fail-closed role and department authorization boundary
- ETag-based optimistic concurrency for camera updates
- liveness and database/schema readiness checks
- synthetic fixtures and automated tests
- Python package build, isolated installation, coverage, lint, and dependency
  audit gates
- validated request IDs, metadata-only JSON access events, and mutation-audit
  correlation
- SQLite online backup, integrity manifest, verification, and restore-to-new-file
  recovery checks
- isolated PostgreSQL 18 migration/API integration and a bounded synthetic
  performance regression smoke in CI
- file-mounted database and metrics secret support with fail-fast validation
- protected Prometheus request metrics using bounded route-template labels
- measured, non-overwriting SQLite backup/restore/readiness drills
- bounded concurrent load and database-outage behavior checks
- digest-pinned, non-root OCI image and disposable PostgreSQL Compose validation
- version-controlled Grafana service dashboard and explicit regression
  objectives

## Safety Boundary

- No CCTV footage, frames, or clips are stored.
- No production CCTV connection is opened by the backend.
- No Government database, biometric, watchlist, or sensitive-record integration
  is present.
- Test data is synthetic and is not Government or police data.
- User information, passwords, URL credentials, query tokens, and fragments are
  removed from stream references before storage.
- Unknown official fields stay explicit `null` values.
- The Sentinel probe remains a separate reference adapter and is not the H-CAM
  product backend.

## Local Setup

Use Python 3.12 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Create and migrate the local database:

```powershell
$env:HCAM_DATABASE_URL = "sqlite:///./var/hcam.db"
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
.\.venv\Scripts\alembic upgrade head
```

Import the committed synthetic seed:

```powershell
.\.venv\Scripts\hcam import-registry tests/fixtures/camera-registry-seed.json
```

For an already-created local Sentinel metadata snapshot, generate and import a
registry seed without storing video:

```powershell
.\.venv\Scripts\python tools/sentinel_cctv_probe.py registry-export --output fixtures/sentinel/registry-seed.json
.\.venv\Scripts\hcam import-registry fixtures/sentinel/registry-seed.json
```

Generated Sentinel JSON remains ignored by Git.

Start the API:

```powershell
.\.venv\Scripts\python -m uvicorn hcam.main:app --reload
```

Useful URLs:

- `http://127.0.0.1:8000/health/live`
- `http://127.0.0.1:8000/health/ready`
- `http://127.0.0.1:8000/cameras`
- `http://127.0.0.1:8000/docs`

The local development authenticator requires explicit headers. Example:

```powershell
$headers = @{
  "X-HCAM-Actor" = "local-operator"
  "X-HCAM-Roles" = "camera.viewer"
  "X-HCAM-Departments" = "*"
}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cameras" -Headers $headers
```

These headers are not production credentials. The application rejects local
development authentication in production mode. See
[security-and-management.md](security-and-management.md).

Build and quality commands are defined in
[build-and-test.md](build-and-test.md).
Backup, recovery, request correlation, PostgreSQL validation, and performance
smoke behavior are defined in
[operations-and-observability.md](operations-and-observability.md).
Service indicators and objective boundaries are defined in
[service-objectives.md](service-objectives.md). Container validation is defined
in [deployment validation](../../deploy/README.md).

## Camera API

`GET /cameras` supports:

- `source`
- `department`
- `camera_type`
- `health_status`
- `status` for operational state
- `limit` from 1 to 500
- `offset` from 0

Responses separate:

- registry metadata availability
- operational camera state
- connectivity and health state
- stream reachability and last check time

No reachability value is inferred from metadata status. It stays `null` unless a
source explicitly provides a stream test result.

## Registry Import Contract

The importer accepts only schema `hcam.camera_registry.seed.v1`. It validates:

- namespaced camera IDs such as `sentinel:1`
- lowercase source IDs
- unique camera IDs and source/external-ID pairs
- latitude from -90 to 90
- longitude from -180 to 180
- paired coordinates

Repeated import is idempotent. Each successful or failed attempt produces an
audit event; failure context contains only a filename and error type.

Manual/API onboarding and controlled bulk API import are documented in
[security-and-management.md](security-and-management.md). Camera updates require
the current response ETag in `If-Match` and a reason in `X-HCAM-Reason`.

## Validation

```powershell
.\.venv\Scripts\python -m compileall -q app tools
.\.venv\Scripts\pytest
$env:HCAM_DATABASE_URL = "sqlite:///./var/migration-test.db"
.\.venv\Scripts\alembic upgrade head
```

The existing Phase 0 readiness tool remains available:

```powershell
.\.venv\Scripts\python tools/phase0_readiness.py --run-validation --strict
.\.venv\Scripts\python tools/phase1_readiness.py --run-validation
```

## Phase 1 Gate

Engineering evidence is tracked in [acceptance-checklist.md](acceptance-checklist.md)
and [readiness-report.md](readiness-report.md). The evidence and exact decision
statement are consolidated in [owner-review.md](owner-review.md). The project
owner accepted Phase 1 on 2026-08-18 and authorized Phase 2 planning. AI inference, production video
ingestion, biometrics, real watchlists, and Government integrations remain out
of scope.
