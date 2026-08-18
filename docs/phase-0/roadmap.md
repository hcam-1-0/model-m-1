# Roadmap

## Phase 0: Product And Environment Foundation

Status: complete and accepted on 2026-08-18.

Milestones:

- 0.1 Sentinel reference probe: complete.
- 0.2 Offline fixtures and summary: complete.
- 0.3 Registry seed export: complete.
- 0.4 Phase 0 product, requirements, architecture, governance, validation, and
  acceptance docs: complete as a baseline.
- 0.5 Phase 1 implementation plan and backlog: complete in
  `phase-1-handoff.md` and `phase-1-backlog.md`.

## Phase 1: Core Platform Foundation

Status: complete and accepted on 2026-08-18.

Primary goal: build the first H-CAM backend foundation around the camera
registry.

Recommended first build order:

1. Repository structure for backend, docs, tests, and local scripts.
2. Camera registry data model based on `hcam.camera_registry.seed.v1`.
3. Import path from Sentinel registry seed into local database.
4. Camera source adapter interface.
5. Stream health state model.
6. Minimal API for listing cameras and stream state.
7. Auth/RBAC placeholder with clear production requirements.
8. Audit log foundation.

Delivered evidence:

- normalized camera registry and stream-state model
- local and API seed onboarding
- read, create, and partial-update APIs
- fail-closed authentication boundary with local-only test identity
- role and department authorization
- optimistic concurrency and audited writes
- SQLite migrations with a PostgreSQL-compatible ORM boundary
- automated Phase 1 readiness verification

The owner accepted the Phase 1 gate on 2026-08-18. Phase 2 planning is
authorized under the documented safety boundaries.

## Phase 2: Video Ingestion And Stream Management

- RTSP/ONVIF and HTTP/HLS adapters.
- Stream health worker.
- Camera grouping, location metadata, and operator-ready status.
- Recording policy design, not uncontrolled recording.

## Phase 3: AI Analytics

- Model pipeline interface.
- Detection and tracking event schemas.
- Initial vehicle/person/object detection proof with test media.
- Confidence, model versioning, and human review metadata.

## Phase 4: Intelligence And Alerts

- Event correlation.
- Watchlist integration only after authorization and governance.
- Alert rules, escalation, investigation timeline, and evidence records.

## Phase 5: Operator Applications

- Command dashboard.
- Operations camera grid.
- Intelligence search and timeline.
- Admin, data, and cybersecurity surfaces.

## Phase 6: Production Readiness

- Deployment topology.
- Observability.
- Security hardening.
- Retention and legal hold.
- Disaster recovery.
- Performance testing.

## Phase 7: Demonstration And Submission

- Controlled demo environment.
- Synthetic or authorized datasets only.
- Architecture package.
- Validation evidence.
- Presentation and recorded walkthrough.
