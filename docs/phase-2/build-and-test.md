# Build and Test

## Offline Checks

```powershell
python -m compileall -q app tools migrations
python -m ruff check app tests tools migrations
python -m pytest --cov=hcam --cov-report=term-missing --cov-fail-under=90
$env:HCAM_DATABASE_URL = "sqlite:///./var/phase2-check.db"
python -m alembic upgrade head
python -m alembic check
python tools/phase2_readiness.py --run-validation
```

Tests cover API authorization and ETags, locator sanitization, migration
backfill and round trip, FFprobe parsing/classification, real local generated
media inspection, execution-time output flood termination, fail-closed network
policy, ONVIF proxy/redirect denial, simulator resolution, bounded capability
and profile discovery, authorization and audit controls, leases,
hysteresis/backoff, outbox creation and delivery rollback, history retention,
camera projection, ES256/JWKS/path scope, lab seeding, and Compose safety
properties. The 2026-08-19 local run passed 268 tests with one expected
PostgreSQL-URL skip and 90.67% branch coverage; the container lab separately
exercised PostgreSQL 18.

## Container Checks

```powershell
python tools/phase2_lab.py prepare --force
python tools/phase2_lab.py config
python tools/phase2_lab.py start
python tools/phase2_lab.py verify --timeout 360
python tools/phase2_failure_drill.py
python tools/phase2_lab.py stop
```

The container gate requires all 50 streams healthy, path-isolated playback,
full-fleet recovery after an isolated ONVIF outage, and a zero unpublished
outbox backlog after the dispatcher drains.

GitHub CI runs Python 3.12-3.14, SQLite and PostgreSQL migration checks,
dependency audit, package installation, non-root image validation, Phase 1
regressions, and the full 50-stream synthetic lab.
