# h-cam-2.0
mayank repo of h cam experiment

## Phase 1 camera registry backend

Phase 1 begins with the normalized camera registry, stream-state contract,
health endpoints, local SQLite database, migration, and import audit trail.

Start here: [docs/phase-1/README.md](docs/phase-1/README.md)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
$env:HCAM_DATABASE_URL = "sqlite:///./var/hcam.db"
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\hcam import-registry tests/fixtures/camera-registry-seed.json
.\.venv\Scripts\python -m uvicorn hcam.main:app --reload
```

The synthetic seed above is for local development only. OpenAPI is available
at `http://127.0.0.1:8000/docs` after startup.

Registry endpoints require explicit local development identity headers. See
[Phase 1 security and management](docs/phase-1/security-and-management.md) for
the role matrix, write API, ETag, audit, and production identity boundaries.

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
