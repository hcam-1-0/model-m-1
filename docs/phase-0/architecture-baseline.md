# Architecture Baseline

H-CAM should be built as a modular public-safety platform. Phase 0 does not
implement the full platform, but it defines the boundaries that Phase 1 should
respect.

## Official Model Alignment

The official challenge requires Model 1, Centralised CCTV Registry and GIS
Foundation, in every submission. H-CAM therefore uses a registry-first hybrid
architecture:

```text
Mandatory Model 1 Registry And GIS Foundation
  + Model 2 Unified Viewing And Selective Analytics
  + Model 3 VMS Federation And Middleware
  + Model 4 capabilities where central VMS/AI is justified
  = H-CAM Hybrid Platform
```

Phase 1 starts with the mandatory Model 1 backend contract. Later phases add
feed integration, federation, AI, and operator surfaces without replacing the
registry foundation.

## Architecture Principle

Raw video is not the primary product object. The platform should convert video
into camera state, stream health, observations, events, alerts, evidence, and
audit records.

## Logical Layers

```text
Camera Sources
  -> Adapter Layer
  -> Camera Registry
  -> Stream State And Health
  -> Video Processing Pipeline
  -> AI Inference
  -> Event And Intelligence Layer
  -> Storage And Audit
  -> APIs And Realtime Channels
  -> Operator, Admin, Intelligence, Data, And Security Apps
```

## Phase 0 Implemented Boundary

The implemented Phase 0 boundary is the Sentinel reference adapter:

- fetch camera metadata from public observed endpoints
- fetch selected camera state
- probe selected streams with metadata-only `ffprobe`
- save local JSON fixtures
- summarize fixtures offline
- export a normalized H-CAM camera registry seed

This is not the production ingestion engine. It is a safe environment adapter
and data-shape proof for the first backend work.

## First Core Domain Model

The first persistent H-CAM domain model should be the camera registry.

Minimum fields:

- `camera_id`: stable H-CAM internal ID
- `source`: adapter/source system name
- `external_id`: ID used by the source system
- `display_name`
- `number`
- `location.label`
- `location.latitude`
- `location.longitude`
- `location.timezone`
- `department`
- `ownership`
- `camera.type`
- `connectivity`
- `storage`
- `maintenance`
- `status.metadata`
- `status.state`
- `stream.delivery`
- `stream.codec`
- `stream.container`
- `stream.stream_path`
- `stream.hls_path`
- `stream.selected_url`
- `source provenance and timing metadata`

The current `registry-export` command produces this as
`hcam.camera_registry.seed.v1`.

## Proposed Phase 1 Services

| Service | Responsibility |
| --- | --- |
| Camera Registry API | Store normalized cameras, sources, stream endpoints, and status |
| Adapter Runtime | Run source-specific adapters such as Sentinel, RTSP, ONVIF, or official APIs |
| Stream Health Worker | Probe streams, update reachability, and record codec/container facts |
| Event Bus | Publish camera, stream, detection, alert, and audit events |
| Auth And RBAC | Users, roles, permissions, and tenant boundaries |
| Audit Log | Immutable record of sensitive actions and system events |
| Operator API | Read cameras, status, alerts, timeline, and search results |

## Data Flow For Sentinel Reference Adapter

```text
/api/cameras
  -> metadata summary
  -> snapshot cameras.json
  -> registry-export
  -> hcam.camera_registry.seed.v1

/api/cameras/{id}/state
  -> selected camera state
  -> snapshot camera-{id}-state.json
  -> offline-summary and registry-export

/stream/{id}
  -> metadata-only ffprobe
  -> stream compatibility result
```

## Module Boundaries

- Adapter code must not own H-CAM business policy.
- Camera registry owns normalized camera identity and source mapping.
- Stream workers own reachability and media metadata.
- AI inference owns model execution and model result versioning.
- Intelligence owns event correlation and alert rules.
- Operator apps consume APIs and realtime events; they do not connect directly
  to source CCTV systems.
- Audit is cross-cutting and must capture sensitive read/write/export actions.

## Deployment Direction

Phase 1 can start as a single repository and simple runtime, but boundaries
should be service-ready. Later phases may split services or packages as load,
team ownership, and deployment needs become clear.

The statewide design target is approximately 80,000 cameras. That target is a
capacity-planning requirement, not a claim that Phase 1 will ingest that volume.
