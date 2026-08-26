# H-CAM Core — New Developer Onboarding

Welcome! This document explains everything in **plain English** so a new developer (or AI agent) can get productive fast.

---

## 1. What Is This Project?

H-CAM Core is the backend for the **Gujarat Police CCTV Integration Hackathon 2026**.

**In simple terms:** Gujarat has 26+ government departments, each with their own CCTV cameras. Nobody knows exactly where all the cameras are or if they work. We are building the **central system that tracks every camera** — its location on a map, which department owns it, whether it's online, and more. Target: ~80,000 cameras statewide.

This is **"Model 1"** from the hackathon problem statement: the *Registry & GIS Foundation* that other systems (live video viewing, AI analytics) will build on top of.

---

## 2. The Tech Stack (And Why)

| Thing | Technology | Why we use it |
|-------|-----------|---------------|
| Programming language | Python 3.12+ | Common, good libraries |
| Web framework | FastAPI | Fast, auto-generates API docs |
| Database | PostgreSQL + PostGIS | PostGIS lets us ask "which cameras are near this spot?" very fast |
| Database toolkit | SQLAlchemy 2.0 | Talks to the database using Python code |
| Schema changes | Alembic | Tracks database changes like git tracks code |
| Map format | Mapbox Vector Tiles (MVT) | Standard format map libraries understand |
| Ingest | FFmpeg + frag MP4 | Zero-copy, TCP, segmented |
| AI | Ultralytics YOLOv8 + torch CUDA | 1 frame / N sec, autocast |
| Package manager | uv | Very fast pip replacement |

---

## 3. Project Structure — What Lives Where

```
model-m-1/
├── app/hcam/                    ← ALL application code lives here
│   ├── main.py                  ← Starts the web server, wires everything
│   ├── settings.py              ← Reads config from environment variables
│   ├── database.py              ← Database connection + health checks
│   ├── cli.py                   ← Command-line tools (hcam command)
│   │
│   ├── camera_registry/         ← THE CORE: camera records + maps
│   │   ├── models.py            ← Camera table definition (+ geometry column)
│   │   ├── schemas.py           ← Data shapes for API requests/responses
│   │   ├── routes.py            ← REST endpoints (list/create/update cameras)
│   │   ├── gis_routes.py        ← MAP endpoints (bbox, radius, cluster, tiles)
│   │   ├── service.py           ← Business rules + audit logging
│   │   └── repository.py        ← Database queries
│   │
│   ├── cam_adapter/             ← INGEST: RTSP/HLS → Drive (Model 2 bridge)
│   │   ├── recorder.py          ← FFmpeg frag MP4, TCP, stream-copy
│   │   ├── analytics.py         ← YOLOv8 CUDA sampling
│   │   ├── worker.py            ← Threads + backoff + orchestrator
│   │   ├── telemetry.py         ← Drive/CPU/GPU logs
│   │   ├── config.py            ← AdapterConfig/StreamConfig
│   │   └── routes.py            ← GET /cam-adapter/status
│   │
│   ├── streams/                 ← Video stream metadata (Phase 2)
│   ├── security/                ← Login/roles/permissions
│   ├── audit/                   ← "Who changed what, when" records
│   ├── health/                  ← "Is the server alive?" endpoint
│   └── operations/              ← Backup/restore tools
│
├── migrations/versions/         ← Numbered database changes (0001–0008)
├── Cam-Adapter/                 ← Colab deliverable (standalone script + package)
│   ├── hcam_colab_ingest.py     ← 7 cells (# %% [code]), live.corp8.cloud
│   ├── config.example.json      ← 10 Sentinel cams
│   └── README.md                ← Colab guide
├── tests/                       ← Automated tests
├── tools/                       ← Utility scripts
└── README.md                    ← Full technical docs (+ Cam-Adapter)
```

---

## 4. Key Concepts Explained

### The Camera Record
Every camera in the database has:
- **Identity**: `camera_id`, which department system it came from (`source_id`), its ID in that system (`external_id`)
- **Location**: `latitude`, `longitude`, plus a special `geometry` column that PostGIS uses for fast map queries
- **Status**: is it healthy? connected? under maintenance?
- **Stream info**: how to reach its video (RTSP/HLS URLs)

### The Geometry Column (The GIS Part)
- Every camera with coordinates also gets a `geometry` point (SRID 4326 = standard GPS coordinates)
- A **GIST index** makes "find cameras in this area" queries fast even with 80k cameras
- When you set latitude/longitude, call `camera.sync_geometry_from_coords()` to keep geometry in sync

### The GIS API Endpoints
| Endpoint | Plain-English meaning |
|----------|----------------------|
| `GET /cameras/geo/bbox` | "Show me all cameras inside this rectangle" |
| `GET /cameras/geo/radius` | "Show me all cameras within X meters of this spot" |
| `GET /cameras/geo/cluster` | "Group nearby cameras into dots so the map isn't cluttered" |
| `GET /cameras/geo/tile/{z}/{x}/{y}.pbf` | "Give me one map tile" (how Google Maps-style apps load data) |

### Roles & Access
Three roles: **viewer** (read only), **editor** (can change cameras), **admin** (everything).
In development you fake your identity with headers; in production it's JWT tokens.

### Audit Trail
Every change to a camera is logged: who did it, why (a reason header is required), when. This is mandatory for police systems.

---

## 5. Getting It Running (Copy-Paste Guide)

### Prerequisites
- Windows with PowerShell
- Docker Desktop installed and running
- Git

### Step-by-step

```powershell
# 1. Go to the project folder
cd "C:\Users\modas\OneDrive\Desktop\cctv-h\big push\model-m-1"

# 2. Start the database (first time: downloads ~500MB)
docker run -d --name hcam-postgis -e POSTGRES_DB=hcam -e POSTGRES_USER=hcam -e POSTGRES_PASSWORD=hcam -p 5432:5432 postgis/postgis:15-3.4
# (after first time, just: docker start hcam-postgis)

# 3. Install dependencies (creates .venv automatically)
uv sync --locked --extra dev --extra gis

# 4. Set configuration (these die when you close PowerShell — set them each session)
$env:HCAM_DATABASE_URL = "postgresql://hcam:hcam@localhost:5432/hcam"
$env:HCAM_POSTGIS_ENABLED = "true"
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
$env:HCAM_CREATE_SCHEMA = "true"

# 5. Create/update database tables
uv run --locked --extra dev alembic upgrade head

# 6. Load sample camera data
uv run --locked --extra dev hcam import-registry tests/fixtures/camera-registry-seed.json

# 7. Start the server
uv run --locked --extra dev python -m uvicorn hcam.main:app --reload
```

### Verify it works
Open http://127.0.0.1:8000/docs → **camera-gis** + **cam-adapter** sections appear.

**Cam-Adapter (Colab):** Upload `Cam-Adapter/hcam_colab_ingest.py` to Colab → T4 GPU → Cells 1-6 (auto-loads `live.corp8.cloud` 10 cams) → live `Drive/MyDrive/cctv-h/camera_recordings/cam_*/segments/*.mp4` (frag MP4 playable mid-segment) + `detections/*.json`.

**Cam-Adapter (local dry-run, 2 cams):**
```powershell
uv sync --extra cam-adapter
$env:HCAM_DATABASE_URL="postgresql://hcam:hcam@localhost:5432/hcam"; docker start hcam-postgis
uv run python -c "from pathlib import Path; from hcam.cam_adapter.config import AdapterConfig, StreamConfig; from hcam.cam_adapter.worker import AdapterOrchestrator; import time; s=[StreamConfig(camera_id='dry_a', rtsp_url='https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8')]; c=AdapterConfig(drive_base=Path('./Cam-Adapter/dry_run_recordings'), local_fallback_base=Path('./Cam-Adapter/dry_run_recordings'), segment_time_seconds=30, streams=s); o=AdapterOrchestrator(c); o.start(); time.sleep(35); o.stop()"
# → Cam-Adapter/dry_run_recordings/dry_a/segments/*.mp4  ffprobe: h264
```

---

## 6. Common Tasks

### "I changed a model, now what?"
```powershell
# Generate a new migration file
uv run --locked --extra dev alembic revision --autogenerate -m "what I changed"
# Review the file in migrations/versions/, then apply:
uv run --locked --extra dev alembic upgrade head
```
Also update `CURRENT_SCHEMA_REVISION` in `database.py` to the new revision ID.

### "I want to add a new API endpoint"
1. Add the function in `routes.py` (regular) or `gis_routes.py` (spatial)
2. Add request/response shapes in `schemas.py` if needed
3. Restart the server (`--reload` does this automatically)

### "How do I run the tests?"
```powershell
uv run --locked --extra dev pytest tests/ -v
```

### "Something's broken — where do I look?"
- **Import error** → check the traceback file path; likely a bad import
- **Migration fails** → is Docker running? Is `HCAM_DATABASE_URL` set?
- **Connection refused on :8000** → server didn't start; read the error above it
- **"sqlite3.OperationalError: near EXTENSION"** → you forgot to set `HCAM_DATABASE_URL`, it defaulted to SQLite

---

## 7. Environment Variables Cheat Sheet

| Variable | Example value | What it does |
|----------|--------------|--------------|
| `HCAM_DATABASE_URL` | `postgresql://hcam:hcam@localhost:5432/hcam` | Where the database lives |
| `HCAM_POSTGIS_ENABLED` | `true` | Turn on spatial features (needs PostgreSQL!) |
| `HCAM_ENVIRONMENT` | `development` | dev / test / production |
| `HCAM_DEV_AUTH_ENABLED` | `true` | Allow header-based fake login (dev only) |
| `HCAM_CREATE_SCHEMA` | `true` | Auto-create tables on startup (dev only) |
| `HCAM_DB_POOL_SIZE` | `10` | How many DB connections to keep open |

Full list: see `app/hcam/settings.py`.

---

## 8. How We'll Scale to 80,000 Cameras

Already built in:
- GIST spatial index → fast map queries at any scale
- Server-side clustering → maps stay responsive when zoomed out
- Vector tiles → browsers render thousands of points smoothly
- Connection pooling → handles many simultaneous users

Future plan (when needed):
- Split database by district (partitioning)
- Read-only database copies for map queries (read replicas)
- Cache pre-generated map tiles (Redis)
- Run stream-health workers as separate processes

---

## 9. Hackathon Big Picture

```
Model 1 (US — DONE ✅)     Model 2              Model 3               Model 4
Registry + GIS      →     Unified viewing  →   VMS federation   →    Central VMS + AI
Camera inventory          Live video feeds     Vendor adapters       ANPR, tracking
Map visualization         ANPR metadata        Event bus             Watchlist alerts
```

Police databases we'll eventually connect to: eGujCop (cases), VAHAN (vehicles), SARTHI, AFIS/NAFIS (fingerprints).

Evaluation demo requirement: onboard ~50 government cameras, trace a vehicle across cameras, show its route **on our GIS map**, generate watchlist alerts in real time.

---

## 10. Rules of Thumb

1. **Never commit secrets** — passwords/tokens go in environment variables or `_FILE` secret files
2. **Every write needs a reason** — the API requires an `X-HCAM-Reason` header; that's intentional (audit trail)
3. **Test against PostgreSQL**, not SQLite — spatial features only work on PostGIS
4. **Keep migrations numbered and ordered** — never edit an already-applied migration
5. **Ask before touching** `security/`, `settings.py` validation, or production flags — these have safety checks that are load-bearing
