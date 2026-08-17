# Requirements

This file is the starting requirements baseline for H-CAM 2.0. It separates
Phase 0 foundation work from later production modules.

## Requirement Levels

- P0: required before Phase 1 implementation can start safely.
- P1: required for the first usable platform foundation.
- P2: required for broader enterprise deployment.

## Phase 0 Requirements

| ID | Level | Requirement | Evidence |
| --- | --- | --- | --- |
| P0-REQ-001 | P0 | Document product mission, users, scope, and non-goals | `docs/phase-0/product-brief.md` |
| P0-REQ-002 | P0 | Document modular architecture baseline | `docs/phase-0/architecture-baseline.md` |
| P0-REQ-003 | P0 | Document data governance and safety rules | `docs/phase-0/data-governance.md` |
| P0-REQ-004 | P0 | Validate Sentinel reference CCTV metadata safely | `tools/sentinel_cctv_probe.py metadata` |
| P0-REQ-005 | P0 | Save local metadata/state fixtures without video | `tools/sentinel_cctv_probe.py snapshot` |
| P0-REQ-006 | P0 | Produce normalized camera registry seed from fixtures | `tools/sentinel_cctv_probe.py registry-export` |
| P0-REQ-007 | P0 | Maintain offline tests and CI | `tests/`, `.github/workflows/python-ci.yml` |
| P0-REQ-008 | P0 | Define Phase 1 entry criteria | `docs/phase-0/acceptance-checklist.md` |
| P0-REQ-009 | P0 | Capture official portal constraints and distinguish requirements from access authorization | `docs/phase-0/official-constraints-intake.md` |

## Official Challenge Requirements

- Treat Model 1, Centralised CCTV Registry and GIS Foundation, as mandatory.
- Combine Model 1 with viewing, federation, central VMS/AI, or an approved
  hybrid/custom architecture for the complete challenge solution.
- Use open-source technologies and an open, modular, secure, scalable,
  standards-based, vendor-neutral design.
- Plan heterogeneous integration across analog/IP cameras, multiple VMS
  platforms, RTSP, ONVIF, vendor SDKs, and documented APIs.
- Support the organizer's approximately 50-camera synchronized simulated-live
  sandbox and plan for approximately 80,000 cameras statewide.
- Demonstrate real working software; concept-only mock-ups and animations do not
  satisfy the official demo requirement.
- Keep Government database integrations interface-ready but disconnected until
  credentials, data, and handling authorization are officially supplied.

## Platform Functional Requirements

### Camera And Video Foundation

- Register cameras with stable internal IDs and external source IDs.
- Store camera metadata, location labels, stream paths, stream delivery type,
  codec, container, status, and source provenance.
- Store GIS-ready coordinates, department, ownership, camera type,
  connectivity, storage, health, and maintenance metadata required by Model 1.
- Support bulk, manual, and API-based onboarding with metadata validation and
  audit trails.
- Support RTSP, HTTP progressive streams, HLS, and future official API adapters.
- Track stream health separately from camera metadata.
- Keep adapters isolated so Sentinel reference data can be replaced by official
  integrations later.

### AI Analytics

- Convert video frames into structured observations instead of pushing raw
  continuous video into general-purpose language models.
- Support object/person/vehicle detection as separate model capabilities.
- Support ANPR as a distinct capability with confidence scoring and review.
- Support event detection such as intrusion, loitering, crowd density,
  abandoned object, accident, fire/smoke, wrong-way movement, and restricted
  area entry when datasets and authorization allow it.
- Keep model outputs versioned with model name, version, confidence, timestamp,
  camera ID, and processing node.

### Intelligence And Correlation

- Convert individual detections into events.
- Correlate events across cameras using time, location, attributes, and
  authorized identity or vehicle data.
- Support watchlists only with explicit authorization, audit, retention, and
  approval controls.
- Provide investigation timelines and entity histories.

### Operator Applications

- Provide camera grid, map/GIS view, alert queue, timeline, playback, search,
  case/evidence view, and system health surfaces.
- Keep command, operations, intelligence, admin, data, and cybersecurity
  surfaces separate where workflows differ.
- Support role-based access so users see only permitted cameras, cases, data,
  and actions.

### Administration And Security

- Support authentication, role-based access control, audit logs, policy
  configuration, camera onboarding, integration configuration, and emergency
  access workflows.
- Maintain immutable audit records for sensitive reads, exports, user changes,
  policy changes, watchlist changes, and evidence access.
- Encrypt secrets and sensitive data in transit and at rest.

### Data Platform

- Store camera registry data, event metadata, model outputs, evidence metadata,
  audit logs, and retention records in purpose-fit stores.
- Separate raw media storage from derived metadata.
- Support local development fixtures that never contain CCTV footage.
- Support future vector/embedding search only when retention and privacy
  controls are defined.

## Non-Functional Requirements

- Safety: no authentication bypass, hidden endpoint scanning, or unauthorized
  data access.
- Auditability: every sensitive action must be traceable to a user, service, and
  reason.
- Modularity: adapters, camera registry, AI inference, event processing, APIs,
  and applications must remain separable.
- Reliability: stream failures must be reported as state data rather than
  crashing operators or batch jobs.
- Scalability: architecture should support edge processing, distributed
  inference, event-driven pipelines, and a documented path to approximately
  80,000 cameras.
- Testability: offline tests must cover deterministic behavior without requiring
  live CCTV access.
- Portability: Phase 0 tools should run on a developer laptop with Python
  stdlib and optional `ffprobe`.
