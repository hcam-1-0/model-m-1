# H-CAM Core — Camera Registry & GIS Backend

[![Python CI](https://github.com/hcam-1-0/model-m-1/actions/workflows/python-ci.yml/badge.svg?branch=Camera-adapter)](https://github.com/hcam-1-0/model-m-1/actions/workflows/python-ci.yml)
[![Security](https://github.com/hcam-1-0/model-m-1/actions/workflows/security.yml/badge.svg?branch=Camera-adapter)](https://github.com/hcam-1-0/model-m-1/actions/workflows/security.yml)

**H-CAM** (Heterogeneous Camera Analytics & Management) is the backend foundation for the Gujarat Police CCTV Integration Hackathon 2026. It implements **Model 1: Centralised CCTV Registry & GIS Mapping** as the mandatory foundation, with extensible APIs for Models 2–4.

Repository work is managed through structured GitHub Issues, reviewed pull requests, pinned Actions, Dependabot, generated release notes, and the organization delivery Project. See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        H-CAM Core (FastAPI)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐  │
│  │ Camera Registry│  │ Stream Mgmt   │  │ GIS / Spatial API   │  │
│  │ (Phase 1)      │  │ (Phase 2)     │  │ (Phase 1+GIS)       │  │
│  │                │  │               │  │                     │  │
│  │ • CRUD + Audit │  │ • Health probe│  │ • BBox / Radius     │  │
│  │ • Import/Export│  │ • ONVIF caps  │  │ • Clustering        │  │
│  │ • Versioning   │  │ • Synthetic   │  │ • Vector Tiles (MVT)│  │
│  │ • ETag/Precond │  │   50-cam lab  │  │ • PostGIS + GIST    │  │
│  └───────┬────────┘  └───────┬───────┘  └─────────┬───────────┘  │
│  ┌───────────────┐           │                    │              │
│  │ Cam-Adapter   │◄──────────┘                    │              │
│  │ (Model 2)     │  RTSP/HLS → Drive frag MP4     │              │
│  │ • Thread/worker│  YOLOv8 CUDA sampling → JSON  │              │
│  │ • Backoff     │  Telemetry (CPU/GPU/Drive)     │              │
│  └───────────────┘                                │              │
│          └───────────────────┼────────────────────┘              │
│                              ▼                                   │
│              ┌─────────────────────────────────┐                │
│              │   PostgreSQL + PostGIS          │                │
│              │   (SQLite for local dev only)   │                │
│              └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

| Area | Capability |
|------|------------|
| **Camera Registry** | Normalized metadata, department/ownership/type, health status, audit trail, optimistic locking |
| **GIS / Spatial** | PostGIS geometry column, GIST index, bbox/radius/cluster queries, MVT vector tiles for web maps |
| **Cam-Adapter (NEW)** | Multi-threaded RTSP/HLS → Drive (5-min frag MP4, TCP, stream-copy), YOLOv8 CUDA sampling → JSON, backoff+jitter, telemetry |
| **Stream Management** | Multi-protocol endpoints (RTSP/HLS/ONVIF), metadata-only health probes, capability discovery |
| **Security** | JWT auth, role-based access (viewer/editor/admin), department-scoped data isolation |
| **Operations** | Prometheus metrics, structured logging, DB backup/restore/recovery drills |
| **Scalability** | Connection pooling, async-ready, read-replica compatible, 80k+ camera target |

---

## Quick Start (Development)

### Prerequisites
- Python 3.12+
- `uv` package manager (`pip install uv`)
- PostgreSQL 15+ with **PostGIS 3.4+** (required for GIS features)
- `ffprobe` (for stream health probes)

### 1. Install Dependencies
```powershell
git clone https://github.com/hcam-1-0/model-m-1.git
cd model-m-1
git switch Camera-adapter
uv sync --locked --extra dev --extra postgres --extra gis --extra cam-adapter
```

### 2. Configure Environment
```powershell
# PostgreSQL with PostGIS (required for GIS)
$env:HCAM_DATABASE_URL = "postgresql://user:pass@localhost:5432/hcam"
$env:HCAM_POSTGIS_ENABLED = "true"
$env:HCAM_DB_POOL_SIZE = "10"
$env:HCAM_DB_MAX_OVERFLOW = "20"

# Development auth (disabled in production)
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
$env:HCAM_CREATE_SCHEMA = "true"  # auto-create tables on startup

# Stream probe
$env:HCAM_FFPROBE_EXECUTABLE = "ffprobe"
```

### 3. Run Migrations
```powershell
uv run --locked --extra dev alembic upgrade head
```
This applies all migrations including **0008_postgis_gis** which:
- Enables PostGIS extension
- Adds `geometry` column (POINT, SRID 4326) to `cameras`
- Creates GIST spatial index
- Backfills geometry from existing lat/long

### 4. Import Sample Data
```powershell
uv run --locked --extra dev hcam import-registry tests/fixtures/camera-registry-seed.json
```

### 5. Start Server
```powershell
uv run --locked --extra dev python -m uvicorn hcam.main:app --reload
```
OpenAPI docs: `http://127.0.0.1:8000/docs`

---

## GIS API Endpoints

All endpoints require `CAMERA_VIEWER` role (or higher).

### Bounding Box Query
```http
GET /cameras/geo/bbox?min_lon=72.5&min_lat=22.0&max_lon=73.5&max_lat=23.5&limit=500
```
Returns cameras within a rectangular bounds as GeoJSON FeatureCollection.

### Radius Query
```http
GET /cameras/geo/radius?lon=72.571&lat=23.022&radius_m=5000&limit=200
```
Returns cameras within `radius_m` meters of a point (uses geography for accurate distance).

### Clustered Points (for map rendering)
```http
GET /cameras/geo/cluster?min_lon=72.5&min_lat=22.0&max_lon=73.5&max_lat=23.5&zoom=12&grid_size=64
```
Returns grid-clustered points with counts and aggregated properties. Optimized for MapLibre/Leaflet clustering.

### Vector Tile (MVT) — For MapLibre GL / Leaflet VectorGrid
```http
GET /cameras/geo/tile/{z}/{x}/{y}.pbf
```
Returns Mapbox Vector Tile (protobuf) for efficient rendering at scale. Configure tile layer:
```js
// MapLibre GL JS
map.addSource('cameras', {
  type: 'vector',
  tiles: ['http://localhost:8000/cameras/geo/tile/{z}/{x}/{y}.pbf'],
  minzoom: 0, maxzoom: 18
});
map.addLayer({
  id: 'camera-points',
  type: 'circle',
  source: 'cameras',
  'source-layer': 'cameras',
  paint: { 'circle-radius': 4, 'circle-color': '#3b82f6' }
});
```

---

## Cam-Adapter — Cloud Ingest (RTSP/HLS → Drive + YOLOv8)

Wired under `app/hcam/cam_adapter/` and Colab script `Cam-Adapter/hcam_colab_ingest.py`. Same stack (FastAPI, Pydantic, SQLAlchemy), shared `Settings` (`HCAM_CAM_ADAPTER_*`).

The branch supports two deliberately separate operating modes. Recording/analytics workers remain explicit and review-gated. The project-local Windows configuration uses the live-only WHEP/WebRTC viewer with recording disabled, zero stream workers, and no MP4 output. Its basic operations page is `/adapter-backend-dashboard`; the directly connected monitoring extension is `/camera-monitoring-dashboard`. An API or session success is not treated as proof of decoded browser pixels.

**Sentinel host:** `live.corp8.cloud` — `GET https://live.corp8.cloud/api/ingest` returns 30 live cams (mix h264/hevc). Adapter auto-loads via `USE_SENTINEL_CATALOG=True` in Cell 4.

| Requirement | How it’s met |
|-------------|--------------|
| RTSP TCP + low-latency | `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp` before `import cv2`; FFmpeg `-rtsp_transport tcp -fflags +genpts -use_wallclock_as_timestamps 1` |
| Segmented, zero-copy | `-c:v copy -c:a aac -movflags +frag_keyframe+empty_moov -f segment -segment_time 300 -strftime 1` → `cam_06_%Y-%m-%d_%H-%M-%S.mp4` (frag = playable mid-segment) |
| YOLOv8 sampling | `FrameSampler` 1 frame / `sample_interval` sec, `torch.cuda.amp.autocast()`, `del frame; gc.collect(); torch.cuda.empty_cache()` → `detections/*.json` |
| Threading + backoff | `CameraWorker(threading.Thread)` per cam + `exponential_backoff(base*2**attempt, jitter)` reset after 90s healthy |
| Telemetry | `TelemetryLoop` every 30s: `rglob *.mp4` sum + `psutil` CPU/RAM/disk + `torch.cuda.memory_*` → console + `base/_telemetry.log` |

**Colab one-click:** Upload `hcam_colab_ingest.py` → T4 GPU → Cells 1-6 (edit `SENTINEL_MAX_CAMERAS` in Cell 4) → live segments to `Drive/MyDrive/cctv-h/camera_recordings/cam_*/segments/`. See `Cam-Adapter/README.md` for full guide.

**Local/server:** `pip install -e ".[cam-adapter]"` → `GET /cam-adapter/status` (needs `CAMERA_VIEWER`). Env: `HCAM_CAM_ADAPTER_DRIVE_BASE`, `HCAM_CAM_ADAPTER_SEGMENT_TIME=300`, `HCAM_CAM_ADAPTER_YOLO_CONF=0.35`, etc.

**Dry-run:** `Cam-Adapter/dry_run_recordings/` (gitignored) — verified 2-cam 35s → 23MB frag MP4 `ffprobe: h264,1920` ✓.

---

## Project Structure

```
model-m-1/
├── app/hcam/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory (includes cam_adapter)
│   ├── cli.py                  # CLI entry point (hcam command)
│   ├── settings.py             # Configuration (env-driven, incl. HCAM_CAM_ADAPTER_*)
│   ├── database.py             # SQLAlchemy engine/session
│   ├── metrics.py              # Prometheus metrics
│   ├── observability.py        # Request ID, logging middleware
│   ├── camera_registry/
│   │   ├── models.py           # Camera ORM + geometry column
│   │   ├── schemas.py          # Pydantic models (incl. GeoJSON)
│   │   ├── routes.py           # REST API + GIS routes include
│   │   ├── gis_routes.py       # Spatial queries + MVT tiles
│   │   ├── repository.py       # DB queries
│   │   ├── service.py          # Business logic + audit
│   │   └── importer.py         # Seed file import
│   ├── cam_adapter/            # Cloud ingest (Model 2 bridge)
│   │   ├── config.py           # AdapterConfig/StreamConfig
│   │   ├── recorder.py         # FFmpeg frag MP4, TCP, stream-copy
│   │   ├── analytics.py        # FrameSampler YOLOv8 CUDA + autocast + gc
│   │   ├── worker.py           # CameraWorker threads + backoff + orchestrator
│   │   ├── telemetry.py        # TelemetryLoop Drive/CPU/GPU
│   │   └── routes.py           # GET /cam-adapter/status, /streams
│   ├── streams/
│   │   ├── routes.py           # Stream endpoints API
│   │   ├── worker.py           # Health probe worker
│   │   ├── capability_worker.py# ONVIF capability refresh
│   │   ├── lab.py              # Synthetic 50-camera lab
│   │   └── network.py          # Network policy / egress rules
│   ├── health/
│   ├── security/
│   ├── audit/
│   └── operations/
│   ├── Cam-Adapter/            # Colab deliverable (standalone + package-aware)
│   │   ├── hcam_colab_ingest.py# 7-cell Colab script (# %% [code])
│   │   ├── config.example.json # 10 Sentinel cams (live.corp8.cloud)
│   │   └── README.md           # Colab guide
```
├── migrations/
│   ├── versions/               # Alembic migrations (0001–0008)
│   └── env.py
├── tests/
├── tools/
│   ├── phase2_lab.py
│   ├── sentinel_cctv_probe.py
│   └── phase0_readiness.py
├── docs/
│   ├── phase-0/ through phase-3/
│   └── phase-2/capability-management.md
├── contracts/
├── deploy/
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## Configuration Reference

### Core
| Env Var | Default | Description |
|---------|---------|-------------|
| `HCAM_DATABASE_URL` | `sqlite:///./var/hcam.db` | PostgreSQL for production/GIS |
| `HCAM_POSTGIS_ENABLED` | `false` | Enable PostGIS features (requires PG) |
| `HCAM_ENVIRONMENT` | `development` | `development`, `test`, `production` |
| `HCAM_DEV_AUTH_ENABLED` | `false` | Allow dev auth headers |
| `HCAM_CREATE_SCHEMA` | `false` | Auto-create tables (dev only) |

### Database Pool (PostgreSQL)
| Env Var | Default | Description |
|---------|---------|-------------|
| `HCAM_DB_POOL_SIZE` | `5` | Persistent connections |
| `HCAM_DB_MAX_OVERFLOW` | `10` | Extra connections under load |
| `HCAM_DB_POOL_TIMEOUT` | `30.0` | Seconds to wait for connection |
| `HCAM_DB_POOL_RECYCLE` | `1800` | Recycle connections (seconds) |

### GIS / Vector Tiles
| Env Var | Default | Description |
|---------|---------|-------------|
| `HCAM_GIS_TILE_EXTENT` | `4096` | MVT tile extent (256–8192) |
| `HCAM_GIS_TILE_BUFFER` | `256` | Buffer around tile (0–1024) |
| `HCAM_GIS_MAX_FEATURES_PER_TILE` | `10000` | Feature limit per tile |
| `HCAM_GIS_CLUSTER_MIN_ZOOM` | `0` | Min zoom for clustering |
| `HCAM_GIS_CLUSTER_MAX_ZOOM` | `20` | Max zoom for clustering |

### Cam-Adapter
| Env Var | Default | Description |
|---------|---------|-------------|
| `HCAM_CAM_ADAPTER_DRIVE_BASE` | `/content/drive/.../camera_recordings` | Drive root for segments/detections |
| `HCAM_CAM_ADAPTER_SEGMENT_TIME` | `300` | Segment length sec (30-3600) |
| `HCAM_CAM_ADAPTER_SAMPLE_INTERVAL` | `2.0` | YOLO sample sec (0.5-60) |
| `HCAM_CAM_ADAPTER_YOLO_MODEL` | `yolov8n.pt` | `n/s/m/l` |
| `HCAM_CAM_ADAPTER_YOLO_CONF` | `0.35` | Confidence 0.1-0.95 |
| `HCAM_CAM_ADAPTER_TELEMETRY_INTERVAL` | `30` | Telemetry sec (5-300) |

### Stream / ONVIF
| Env Var | Default | Description |
|---------|---------|-------------|
| `HCAM_FFPROBE_EXECUTABLE` | `ffprobe` | Path to ffprobe |
| `HCAM_STREAM_PROBE_TIMEOUT_SECONDS` | `8.0` | Probe timeout |
| `HCAM_ONVIF_DISCOVERY_ENABLED` | `false` | Enable WS-Discovery |
| `HCAM_ONVIF_EGRESS_RULES_FILE` | — | JSON egress rules file |

---

## Running Tests

The design baseline, acceptance evidence, and delivery roadmap are indexed in
[`docs/phase-0/README.md`](docs/phase-0/README.md). The main CI run keeps the
established core at 90% branch coverage. The live-only Camera Adapter and GIS
HTTP extension also run in a dedicated smoke job so their optional runtime
dependencies cannot weaken the core gate.

```powershell
# Unit tests
uv run --locked --extra dev pytest tests/ -v

# With coverage
uv run --locked --extra dev pytest tests/ --cov=hcam --cov-report=term-missing

# Lint
uv run --locked --extra dev ruff check .

# Type check (if configured)
uv run --locked --extra dev mypy app/hcam
```

---

## Production Deployment

### Docker
```dockerfile
# See deploy/Dockerfile for multi-stage build
docker build -t hcam-core .
docker run -p 8000:8000 \
  -e HCAM_DATABASE_URL=postgresql://... \
  -e HCAM_POSTGIS_ENABLED=true \
  -e HCAM_ENVIRONMENT=production \
  hcam-core
```

### Required Production Settings
- `HCAM_DATABASE_URL` pointing to PostgreSQL + PostGIS
- `HCAM_POSTGIS_ENABLED=true`
- `HCAM_ENVIRONMENT=production`
- `HCAM_DEV_AUTH_ENABLED=false`
- Valid JWT auth via `HCAM_AUTH_*` settings
- TLS termination at load balancer

### Scaling to 80,000 Cameras
- **DB**: PostgreSQL 15+ with `pgvector` / partitioning by department
- **Pool**: `HCAM_DB_POOL_SIZE=20`, `HCAM_DB_MAX_OVERFLOW=40`
- **Read Replicas**: Route GIS queries to read replicas
- **Caching**: Redis for tile caching (add `TileCacheMiddleware`)
- **MVT**: Pre-generate tiles nightly for zoom 0–12; serve 13+ on-demand
- **Workers**: Run `stream-worker` and `capability-worker` as separate services

---

## Hackathon Context (Gujarat CCTV Integration)

This backend implements **Model 1** (Registry & GIS Foundation) per the problem statement:
- Centralised camera metadata registry across 26+ departments
- GIS mapping with PostGIS for ~80,000 cameras statewide
- Interoperable APIs for Models 2/3/4 to build upon
- ONVIF capability discovery for heterogeneous vendor integration
- Synthetic lab (50 streams) for testing without live feeds

### Next Phases (Roadmap)
- **Phase 2+**: Stream gateway, HLS/WebRTC relay, ANPR metadata pipeline
- **Phase 3**: AI analytics (vehicle/person detection, cross-camera tracking)
- **Integration**: eGujCop, VAHAN, SARTHI, AFIS/NAFIS watchlist correlation

---

## For New Developers / AI Agents

### Key Entry Points
- **App factory**: `app/hcam/main.py:create_app()`
- **Settings**: `app/hcam/settings.py:Settings.from_environment()`
- **Database**: `app/hcam/database.py:Database` + `build_engine()`
- **Camera API**: `app/hcam/camera_registry/routes.py`
- **GIS API**: `app/hcam/camera_registry/gis_routes.py`
- **CLI**: `app/hcam/cli.py:main()`

### Adding a New Feature
1. Create migration in `migrations/versions/` (follow naming: `000X_feature.py`)
2. Add ORM model in appropriate module (`models.py`)
3. Add Pydantic schemas in `schemas.py`
4. Add repository queries in `repository.py`
5. Add business logic in `service.py`
6. Add routes in `routes.py` (or new `*_routes.py`)
7. Update `REQUIRED_*_COLUMNS` in `database.py` if new tables
8. Write tests in `tests/`
9. Run `alembic revision --autogenerate -m "description"` then edit

### GIS-Specific Notes
- Geometry column uses **SRID 4326** (WGS84 lat/long)
- Always use `func.ST_*` functions for spatial queries (see `gis_routes.py`)
- GIST index on `cameras.geometry` enables fast bbox/radius
- MVT tiles use `ST_AsMVTGeom` with configurable extent/buffer
- For clustering: `ST_SnapToGrid` + aggregation

---

## License
Government of Gujarat / Gujarat Police Innovation Hackathon 2026 — Internal use only.
