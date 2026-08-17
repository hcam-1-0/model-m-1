# Phase 1 Handoff

This handoff converts Phase 0 planning into the first implementation package.
It does not start Phase 1 by itself; it defines what must be true when Phase 1
starts.

## Phase 1 Objective

Build the H-CAM core platform foundation around the camera registry and stream
state model proven by the Sentinel probe.

The Camera Registry is the first core backend domain.

This implements the backend foundation of the challenge's mandatory Model 1.
It does not claim that Model 1 is complete until GIS, onboarding, health,
search, audit, export, and gap-analysis capabilities are delivered.

The first implementation should accept the generated
`hcam.camera_registry.seed.v1` JSON and expose normalized camera records through
a tested backend boundary.

## Phase 1 Starting Scope

Included:

- project structure for backend code, tests, and configuration
- camera registry domain model
- GIS-ready location, department, ownership, camera type, connectivity,
  storage, health, and maintenance fields
- importer for `hcam.camera_registry.seed.v1`
- local development database
- API endpoints for cameras and stream state
- source adapter abstraction
- audit log foundation
- basic health and readiness endpoints
- CI checks for backend tests

Excluded:

- production CCTV ingestion
- bulk video recording
- AI inference runtime
- biometric recognition
- government database integration
- watchlist matching
- production authentication provider integration
- operator UI implementation
- GIS map UI and gap-analysis reports

## Recommended Backend Stack

Use a conservative Python backend for Phase 1:

- Python 3.12+
- FastAPI for HTTP APIs
- Pydantic for request/response and domain validation
- SQLAlchemy for database access
- Alembic for migrations
- SQLite for first local development
- PostgreSQL as the production target
- pytest for backend tests
- Docker only after the basic local runtime is proven

Reasoning:

- The current repo already uses Python for Sentinel tooling.
- Camera registry import and stream state are data-heavy, not UI-heavy.
- FastAPI/Pydantic fit strongly typed API contracts and generated OpenAPI docs.
- SQLite keeps first laptop setup simple for the six-person team.
- PostgreSQL gives a clear path to production without changing the domain model.

## First Package Layout

```text
h-cam-2.0/
  app/
    hcam/
      __init__.py
      main.py
      settings.py
      camera_registry/
        models.py
        schemas.py
        repository.py
        importer.py
        routes.py
      audit/
        models.py
        repository.py
      health/
        routes.py
  tests/
    test_camera_registry_import.py
    test_camera_registry_api.py
    test_health.py
  docs/
    phase-1/
      README.md
```

## First Implementation Sequence

1. Add backend dependency and project metadata.
2. Add application shell with `/health/live` and `/health/ready`.
3. Define camera registry schema from `hcam.camera_registry.seed.v1`.
4. Add local database setup and migration path.
5. Add registry importer that reads a local generated seed file.
6. Add `GET /cameras` and `GET /cameras/{camera_id}`.
7. Add stream state fields and source provenance.
8. Add department, GIS, ownership, connectivity, storage, and maintenance
   fields without requiring real Government data.
9. Add audit table/interface for future sensitive actions.
10. Add tests and CI commands.

## Phase 1 Done Criteria

- Local backend starts from a clean checkout.
- Camera registry seed imports without manual editing.
- Camera list and camera detail APIs return normalized records.
- Tests cover import, validation, API behavior, and failure cases.
- CI is green.
- No CCTV video is stored.
- No sensitive integrations are added.
- Phase 1 docs explain setup and boundaries.

## Open Decisions Before Coding

- Confirm Python backend stack.
- Confirm single-repo Phase 1 structure before considering multiple repos.
- Confirm whether SQLite is acceptable for first laptop development.
- Confirm naming for internal camera IDs and source IDs.
- Confirm whether GitHub Issues or another tracker will own the implementation
  backlog.
