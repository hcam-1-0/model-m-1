# Phase 2: Camera and Video Ingestion

Phase 2 turns the Phase 1 camera registry into a safe, testable stream-control
plane. It manages stream endpoints, performs metadata-only health probes,
resolves streams, maintains authenticated read-only ONVIF capability history,
supports controlled ONVIF inspection and synthetic PTZ validation, and issues
short-lived authorization for live HLS playback through MediaMTX.

This phase is an engineering foundation, not production CCTV authorization.
All integration and scale evidence uses generated test video. It does not
connect unauthorized cameras, scan arbitrary networks, record video, process
Government data, run biometrics, or add AI analytics.

## Documents

- [Build and review backlog](backlog.md)
- [Architecture and contracts](architecture-and-contracts.md)
- [Adapters and health worker](adapters-and-health.md)
- [ONVIF capability management](capability-management.md)
- [Controlled ONVIF operations](onvif-operations.md)
- [Controlled private-camera validation](private-camera-validation.md)
- [Publication evidence runner](publication-evidence.md)
- [Playback security](playback-security.md)
- [Synthetic 50-stream lab](synthetic-lab.md)
- [Operations and observability](operations-and-observability.md)
- [Safety and data governance](safety-and-governance.md)
- [Build and test](build-and-test.md)
- [Acceptance checklist](acceptance-checklist.md)
- [Controlled ONVIF extension publication checklist](extension-publication-checklist.md)
- [Readiness report](readiness-report.md)
- [Owner review](owner-review.md)

## Phase Boundary

Phase 2 core was accepted by the owner on 2026-08-21. The later authenticated
capability-management and controlled ONVIF operations extension was separately
accepted and merged through pull request #31 on 2026-08-23. Phase 3 AI
analytics planning is authorized, but implementation remains subject to its
own dataset, model, safety, architecture, and validation gates. No Phase 2
result authorizes physical-camera control, recording, real CCTV, production
police use, Government database access, analytics, face recognition,
watchlists, deployment, or real-person footage.
