# Phase 1 Backlog Traceability

Status: original Phase 1 backlog delivered and accepted on 2026-08-18.

| Backlog item | State | Primary implementation evidence | Review focus |
| --- | --- | --- | --- |
| HCAM-001 Application shell | Complete | `hcam.main`, package metadata | Clean installation and import |
| HCAM-002 Health endpoints | Complete | `hcam.health`, readiness tests | Migration and database failure behavior |
| HCAM-010 Camera model | Complete | camera models/schemas, migration `0001` | Constraints and unknown values |
| HCAM-011 Registry import | Complete | registry importer and fixtures | Idempotency, limits, provenance, audit |
| HCAM-012 Camera APIs | Complete | camera routes/repository | Scope, pagination, 404 behavior |
| HCAM-013 Model 1 filters | Complete | camera filter contracts/tests | Department/GIS/null handling |
| HCAM-020 Stream state model | Complete | camera projection and Phase 2 endpoint model | Metadata versus reachability separation |
| HCAM-021 Stream API fields | Complete | camera/stream responses | Credential and token redaction |
| HCAM-030 Audit model | Complete | `hcam.audit` | Actor, reason, request correlation |
| HCAM-031 Import audit | Complete | importer audit paths | Success and sanitized failure evidence |
| HCAM-040 Backend CI | Complete | Python CI and build checks | Current interpreter/dependency matrix |
| HCAM-041 Phase 1 docs | Complete | `docs/phase-1` | Fresh-checkout accuracy |

## Maintenance Backlog

- P1-R1: run the Phase 1 readiness verifier on every cross-phase release;
- P1-R2: verify the full Alembic chain on SQLite and PostgreSQL;
- P1-R3: enforced by deterministic reviewed OpenAPI and migrated-database
  snapshots, `tools/release_contracts.py check`, CI, and readiness tests;
- P1-R4: review fail-closed authentication, RBAC, department scoping, ETags,
  audit, request limits, and stream-reference sanitization;
- P1-R5: rehearse backup, restore, outage, container, metrics, and concurrent
  load evidence after infrastructure changes;
- P1-R6: create defect issues only when current evidence fails.

Production identity, GIS/operator UI, evidence retention, very-large queued
imports, and Government integrations remain later-phase work rather than
reopening the accepted Phase 1 boundary.
