# Phase 2: Camera and Video Ingestion

Phase 2 turns the Phase 1 camera registry into a safe, testable stream-control
plane. It manages stream endpoints, performs metadata-only health probes,
resolves streams and discovers normalized media capabilities from one
controlled ONVIF simulator, and issues short-lived authorization for live HLS
playback through MediaMTX.

This phase is an engineering foundation, not production CCTV authorization.
All integration and scale evidence uses generated test video. It does not
connect real cameras, scan a LAN, record video, process Government data, run
biometrics, or add AI analytics.

## Documents

- [Architecture and contracts](architecture-and-contracts.md)
- [Adapters and health worker](adapters-and-health.md)
- [Playback security](playback-security.md)
- [Synthetic 50-stream lab](synthetic-lab.md)
- [Operations and observability](operations-and-observability.md)
- [Safety and data governance](safety-and-governance.md)
- [Build and test](build-and-test.md)
- [Acceptance checklist](acceptance-checklist.md)
- [Readiness report](readiness-report.md)
- [Owner review](owner-review.md)

## Phase Boundary

Phase 2 ends at `ready_for_owner_review`. Phase 3 AI analytics remains blocked
until the owner explicitly accepts this phase. No Phase 2 result authorizes
real CCTV, production police use, Government database access, face recognition,
watchlists, or real-person footage.
