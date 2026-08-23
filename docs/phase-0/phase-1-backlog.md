# Phase 1 Backlog

This is the implementation backlog created from Phase 0. It can be copied into
GitHub Issues, Linear, Notion, or another tracker.

## Epic 1: Backend Project Foundation

### HCAM-001: Create backend application shell

Goal: add the minimal backend package structure, settings module, and app entry
point.

Acceptance:

- app package imports successfully
- local run command is documented
- tests can import the app

### HCAM-002: Add health endpoints

Goal: expose liveness and readiness endpoints for local and future deployment
checks.

Acceptance:

- `GET /health/live` returns live status
- `GET /health/ready` returns dependency readiness
- tests cover both endpoints

## Epic 2: Camera Registry

### HCAM-010: Define camera registry domain model

Goal: model normalized camera records based on `hcam.camera_registry.seed.v1`.

Acceptance:

- model includes camera ID, source, external ID, display name, location, status,
  department, ownership, camera type, GIS-ready location, connectivity, storage,
  maintenance, stream metadata, and provenance
- validation rejects malformed camera IDs and missing source IDs
- tests cover valid and invalid records

### HCAM-011: Import registry seed

Goal: import a local `hcam.camera_registry.seed.v1` JSON file into the backend
data store.

Acceptance:

- importer reads local JSON
- importer upserts cameras idempotently
- importer records source metadata
- tests cover missing file, invalid schema, duplicate import, and successful
  import

### HCAM-012: Expose camera APIs

Goal: expose camera list and camera detail endpoints.

Acceptance:

- `GET /cameras` returns normalized camera records
- `GET /cameras/{camera_id}` returns one camera
- missing camera returns a clear 404
- tests cover list, detail, and missing cases

### HCAM-013: Add Model 1 registry filtering contract

Goal: support the official Model 1 search dimensions without implementing the
GIS user interface yet.

Acceptance:

- camera list can filter by department, camera type, health/status, and source
- coordinate fields use validated latitude/longitude ranges
- missing official values remain explicit unknowns rather than invented data
- tests cover filters, invalid coordinates, and null handling

## Epic 3: Stream State

### HCAM-020: Model stream state

Goal: represent stream path, selected URL, delivery type, codec, container,
reachability, and last check metadata.

Acceptance:

- model separates metadata status from stream reachability
- 5XX stream probe results can be represented without crashing
- tests cover reachable and unreachable stream states

### HCAM-021: Add stream state API fields

Goal: include stream state in camera API responses.

Acceptance:

- camera responses expose stream metadata and last known state
- no raw credentials are returned
- tests cover fields and null handling

## Epic 4: Audit Foundation

### HCAM-030: Define audit event model

Goal: create the minimal audit record structure for future sensitive actions.

Acceptance:

- audit record includes actor, action, target, timestamp, source, and reason
- system actions can be recorded without a user actor
- tests cover serialization and required fields

### HCAM-031: Audit registry import

Goal: record an audit event when camera registry import runs.

Acceptance:

- import success writes audit summary
- import failure writes failure context without sensitive data
- tests cover both paths

## Epic 5: Development Workflow

### HCAM-040: Add backend CI checks

Goal: extend CI with backend test commands when the backend package exists.

Acceptance:

- CI runs all Python tests
- CI fails on import or unit test failure
- README documents local commands

### HCAM-041: Add Phase 1 docs

Goal: document local setup, commands, architecture boundaries, and safety rules.

Acceptance:

- `docs/phase-1/README.md` exists
- setup instructions work from a fresh checkout
- docs repeat no-video and no-sensitive-integration rules
