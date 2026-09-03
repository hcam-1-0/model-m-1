# Product Brief

## Product Name

H-CAM 2.0

## Mission

H-CAM is an enterprise video intelligence platform for transforming distributed
CCTV environments into searchable, event-driven, and operationally useful public
safety infrastructure.

The product direction is aligned with the Gujarat Police innovation challenge:
unify diverse CCTV systems, correlate live video signals with authorized data
sources, apply AI to people, vehicles, and events of interest, and generate
real-time alerts for faster law enforcement response.

## Product Principle

Operators should not be forced to watch every camera continuously. H-CAM should
convert camera feeds into structured observations, events, alerts, timelines,
and evidence that can be searched, reviewed, audited, and acted on.

## Primary Users

- Control room operator: monitors alerts, camera health, live feeds, playback,
  and incident queues.
- Investigation officer: searches entities, events, vehicles, timelines, and
  supporting evidence.
- Command officer: views operational status, hotspots, critical incidents, and
  response metrics.
- System administrator: manages users, roles, policies, cameras, integrations,
  and platform health.
- Security/compliance officer: reviews audit trails, access, retention,
  exceptions, and policy violations.
- Developer/integration engineer: connects cameras, APIs, datasets, models, and
  automation workflows.

## Product Surfaces

H-CAM should evolve as a platform with multiple focused surfaces rather than one
overloaded dashboard.

- Command Center: situational overview, critical incidents, risk map, and
  executive status.
- Operations Center: live camera grid, alert queue, playback, camera health, and
  dispatch context.
- Intelligence Center: entity search, timeline reconstruction, event
  correlation, and investigation graph.
- Data Platform: camera registry, datasets, evidence metadata, embeddings,
  retention, and audit-ready exports.
- Admin Center: users, roles, policies, tenancy, integrations, and system
  configuration.
- Cyber Security Center: access monitoring, system events, model/runtime
  security, and incident response.
- Developer Portal: APIs, schemas, webhooks, SDKs, test fixtures, and integration
  documentation.

## Initial Outcome

The first deployable baseline should prove that H-CAM can ingest or reference
camera metadata, model stream state safely, normalize camera records, and
prepare a registry seed for future backend services.

## Non-Goals For Phase 0

- No bulk CCTV download.
- No production surveillance deployment.
- No government database integration without formal authorization and data
  contracts.
- No face recognition, biometric matching, or watchlist matching until legal,
  privacy, and operational controls are documented and approved.
- No hidden endpoint scanning, authentication bypass, scraping, or attempt to
  access non-public systems.
- No final UI implementation beyond planning and interface requirements.

## Success Metrics

- Phase 0 documents are present, linked, and validated by tests.
- Sentinel reference environment is safely probed using metadata-only commands.
- Camera metadata and selected state can be snapshotted locally.
- A normalized `hcam.camera_registry.seed.v1` registry export can be generated
  from local fixtures.
- CI validates the probe and Phase 0 documentation structure.
- Phase 1 has a clear first implementation target.
