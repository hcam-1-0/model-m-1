# h-cam-2.0
mayank repo of h cam experiment

## Phase 3 AI analytics planning

Phase 3 planning defines anonymous detection, per-camera tracking, line/zone
events, synthetic ANPR, runtime selection, data/model governance, security, and
validation. It adds planning documents only: no AI runtime, model, dataset, or
real CCTV analytics has been implemented or authorized.

Start here: [docs/phase-3/README.md](docs/phase-3/README.md)

## Phase 2 camera and video ingestion

Phase 2 adds stream endpoint management, metadata-only health workers, a
controlled ONVIF simulator, authenticated background capability inventory,
short-lived HLS authorization, and a disposable 50-stream synthetic lab. It
does not discover camera networks, control cameras, capture images, or record
video.

Start here: [docs/phase-2/README.md](docs/phase-2/README.md)

Reviewed OpenAPI and migrated-database baselines are documented in
[contracts/phase-2/README.md](contracts/phase-2/README.md).

```powershell
python tools/phase2_lab.py prepare
python tools/phase2_lab.py config
python tools/phase2_lab.py start
python tools/phase2_lab.py verify --timeout 360
python tools/phase2_lab.py stop
```

Capability refresh is opt-in for each ONVIF stream. The worker and detailed
contract are documented in
[ONVIF capability management](docs/phase-2/capability-management.md):

```powershell
hcam capability-worker --once
hcam capability-worker --poll-seconds 5
```

## Phase 1 camera registry backend

Phase 1 begins with the normalized camera registry, stream-state contract,
health endpoints, local SQLite database, migration, and import audit trail.

Start here: [docs/phase-1/README.md](docs/phase-1/README.md)

```powershell
uv sync --locked --extra dev
$env:HCAM_DATABASE_URL = "sqlite:///./var/hcam.db"
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
uv run --locked --extra dev alembic upgrade head
uv run --locked --extra dev hcam import-registry tests/fixtures/camera-registry-seed.json
uv run --locked --extra dev python -m uvicorn hcam.main:app --reload
```

The synthetic seed above is for local development only. OpenAPI is available
at `http://127.0.0.1:8000/docs` after startup.

Registry endpoints require explicit local development identity headers. See
[Phase 1 security and management](docs/phase-1/security-and-management.md) for
the role matrix, write API, ETag, audit, and production identity boundaries.
See [Phase 1 build and test](docs/phase-1/build-and-test.md) for the interpreter
matrix, coverage, lint, migration, dependency-audit, and artifact checks.
See [Phase 1 operations and observability](docs/phase-1/operations-and-observability.md)
for request IDs, metadata-only access events, SQLite backup/recovery,
PostgreSQL integration, protected Prometheus metrics, synthetic performance,
and concurrent load smokes. See
[Phase 1 service objectives](docs/phase-1/service-objectives.md) for metric
labels, regression objectives, and the Grafana dashboard, and
[deployment validation](deploy/README.md) for the non-root container stack.

Local SQLite recovery commands never overwrite existing files:

```powershell
.\.venv\Scripts\hcam backup-database .\backups\hcam-phase1.db
.\.venv\Scripts\hcam verify-backup .\backups\hcam-phase1.db
.\.venv\Scripts\hcam restore-backup .\backups\hcam-phase1.db .\var\hcam-restored.db
.\.venv\Scripts\hcam recovery-drill .\backups\drill-001
```

## Phase 0 foundation

Phase 0 defines the H-CAM product baseline, requirements, architecture,
governance, validation gates, and Phase 1 entry plan.

Start here: [docs/phase-0/README.md](docs/phase-0/README.md)

## Sentinel CCTV environment probe

This repository includes a safe, read-only probe for the Sentinel Gujarat CCTV
reference environment. It is for development planning and stream compatibility
checks only; it does not bulk-download CCTV footage.

```powershell
python tools/sentinel_cctv_probe.py metadata
python tools/sentinel_cctv_probe.py state --camera-id 1
python tools/sentinel_cctv_probe.py stream-test --camera-id 1
python tools/sentinel_cctv_probe.py snapshot
python tools/sentinel_cctv_probe.py offline-summary
python tools/sentinel_cctv_probe.py registry-export --output fixtures/sentinel/registry-seed.json
python tools/sentinel_cctv_probe.py all
```

Default target: `https://live.sentinelgujarat.in`

Offline regression checks:

```powershell
python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py
python -m unittest discover -s tests -v
python tools/phase0_readiness.py --run-validation
```

See [docs/phase-0/cctv-environment.md](docs/phase-0/cctv-environment.md) for
the observed API shape, safety rules, and test workflow.

See [docs/phase-0/readiness-report.md](docs/phase-0/readiness-report.md) for
the completed Phase 0 evidence map.
