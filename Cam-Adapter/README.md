# Cam-Adapter — H-CAM Cloud-Native Ingestion & Recording

**Part of `hcam-core` (model-m-1), not a separate project. Same stack: Python 3.12, FastAPI, Pydantic, SQLAlchemy. Google Colab–native.**

Ingests **N live RTSP/HLS feeds in parallel**, writes **segmented MP4s directly to Google Drive** with **zero CPU re-encode** and **zero RAM accumulation**, runs **YOLOv8 frame-sampling analytics**, and survives network blips with **exponential backoff + jitter**.

---

## Where it lives

```
model-m-1/
├── app/hcam/cam_adapter/          ← importable package (used by backend + Colab)
│   ├── config.py                  ← AdapterConfig / StreamConfig (pydantic)
│   ├── recorder.py                ← FFmpeg segment cmd + TCP enforcement
│   ├── analytics.py               ← FrameSampler (OpenCV + YOLOv8 + autocast + gc)
│   ├── worker.py                  ← CameraWorker (thread) + AdapterOrchestrator
│   ├── telemetry.py               ← TelemetryLoop (Drive usage + CPU/GPU/RAM)
│   └── routes.py                  ← FastAPI: GET /cam-adapter/status, /streams
└── Cam-Adapter/                   ← Colab deliverable
    ├── hcam_colab_ingest.py       ← 7-cell Colab script (# %% [code])
    ├── config.example.json        ← copy → fill RTSP URLs → paste into Cell 4
    └── README.md                  ← this file
```

Integration: `app/hcam/main.py` conditionally includes `cam_adapter.routes`; `app/hcam/settings.py` exposes `HCAM_CAM_ADAPTER_*` env vars.

---

## Quick start (Colab)

1. **Open Colab** → `File → Upload` → `hcam_colab_ingest.py` → open as notebook (or paste cells).
2. **Runtime → Change runtime type → T4 GPU**.
3. Run **Cell 1** (Drive mount + GPU check), **Cell 2** (pip install), **Cell 3** (imports).
4. In **Cell 4**, replace `STREAMS` with your real RTSP/HLS URLs (see `config.example.json`), tweak `segment_time_seconds` / `sample_interval_seconds`.
5. Run **Cell 5** (optional probe), then **Cell 6** (starts orchestrator — keep running).
6. **Interrupt** Cell 6 to stop cleanly; run **Cell 7** to inspect segments/detections.

**Drive output:**

```
/content/drive/MyDrive/cctv-h/camera_recordings/
  cam_01/
    segments/cam_01_2026-08-26_14-30-00.mp4 (5-min chunks)
    detections/cam_01_2026-08-26_14-30-02_123.json
    ffmpeg.log
  cam_02/ ...
  _telemetry.log
```

---

## Adjustable parameters (Cell 4)

| Param | Default | What to tweak |
|-------|---------|---------------|
| `STREAMS` | 1 example | **Paste real URLs here** |
| `segment_time_seconds` | 300 | 60 for 1-min, 600 for 10-min |
| `sample_interval_seconds` | 2.0 | 1.0 = dense, 5.0 = sparse/GPU-light |
| `yolo_model` | yolov8n.pt | `yolov8s/m/l` for accuracy, `yolov8n` for speed |
| `yolo_conf` | 0.35 | lower = more detections, higher = fewer false positives |
| `yolo_classes` | None (all) | ` [0,2,5,7]` = person/car/bus/truck only |
| `backoff_*` | 1/60/0.4 | reconnection tuning |
| `drive_base` | `/content/drive/...` | change for local testing |

**HCAM API auto-load:** uncomment the `httpx` block in Cell 4 to pull `StreamConfig`s from `GET /cameras` automatically.

---

## Architecture — how the 5 requirements are met

**1. RTSP TCP + low-latency demux**
- `os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]="rtsp_transport;tcp"` set **before** `import cv2`.
- FFmpeg cmd: `-rtsp_transport tcp -fflags +genpts -use_wallclock_as_timestamps 1`.
- **Stream copy**: `-c:v copy -c:a aac -b:a 64k` → no re-encode, ~5% CPU even for 4 streams.

**2. Segmented + zero-copy**
- `-f segment -segment_time 300 -segment_format mp4 -reset_timestamps 1 -strftime 1` → `cam_01_%Y-%m-%d_%H-%M-%S.mp4`.
- No frame buffers in Python for recording path; FFmpeg writes straight to Drive via kernel page cache.
- Analytics path uses single-frame zero-copy read + explicit `del frame; gc.collect(); torch.cuda.empty_cache()`.

**3. YOLOv8 sampling**
- Separate `cv2.VideoCapture` per camera with `CAP_PROP_BUFFERSIZE=1` (latest frame only).
- `1 frame every N seconds` gate via `time.monotonic()`.
- `torch.cuda.amp.autocast()` for FP16 on CUDA; `YOLO.predict(..., device="0")`.
- Atomic JSON write: `.tmp` → `replace()` to avoid partial Drive files.

**4. Multi-threading + backoff**
- `CameraWorker(threading.Thread)` per stream, isolated. `AdapterOrchestrator` owns N workers + telemetry.
- Exponential backoff with jitter: `min(cap, base*2**attempt) * uniform(1-jitter, 1)`, reset after 90s healthy.
- `start_new_session=True` so SIGTERM kills only FFmpeg, not Colab.

**5. Telemetry**
- `TelemetryLoop` daemon, every 30s: `rglob("*.mp4")` sum + `psutil` CPU/RAM/disk + `torch.cuda.memory_*`.
- Logs to stdout **and** `base/_telemetry.log` on Drive.

---

## Local / server usage (same stack, no Colab)

```bash
pip install -e ".[cam-adapter]"        # opencv, psutil
pip install -e ".[colab]"              # + ultralytics, torch (heavy)
python -c "from hcam.cam_adapter.config import AdapterConfig, StreamConfig; ..."

# Or via FastAPI (already wired):
curl -H "X-HCAM-Actor: local-admin" -H "X-HCAM-Roles: platform.admin" -H "X-HCAM-Departments: *" http://localhost:8000/cam-adapter/status
```

### Safe local catalog + lifecycle

Copy [`local-adapter-config.example.json`](local-adapter-config.example.json) to an ignored local runtime folder, then set `HCAM_CAM_ADAPTER_CONFIG_FILE` to its absolute path before starting H-CAM. The file must list every permitted source host in `allowed_source_hosts`; the adapter will not start without that allow-list.

The optional `catalog` section fetches only its configured HTTPS URL. It does not crawl domains, follow redirects, or probe feeds on reload. Its `enabled` flag controls the **separate recorder** and stays `false` for a live-only setup. `POST /cam-adapter/validate` probes only sources already approved by that local file.

### Live-only browser viewer (no recordings)

For live footage, set `catalog.source_kind` to `"whep"` and `catalog.viewer_enabled` to `true`; leave `catalog.enabled` as `false` and keep `streams` empty. H-CAM will use the configured dynamic catalogue to offer at most `max_cameras` approved WHEP/WebRTC cameras. It handles browser signalling and short-lived upstream-session cleanup, while the media travels directly to the browser. It does **not** invoke FFmpeg, create MP4 segments, save clips, or write camera frames to disk.

After starting the local H-CAM server, create a one-time browser launch link with a platform-admin development identity:

```powershell
$headers = @{
  "X-HCAM-Actor" = "local-admin"
  "X-HCAM-Roles" = "platform.admin"
  "X-HCAM-Departments" = "*"
}
$session = Invoke-RestMethod -Method Post -Headers $headers -Uri "http://127.0.0.1:8000/cam-adapter/live/session"
Start-Process ("http://127.0.0.1:8000" + $session.launch_path)
```

The launch link is single-use and expires after `viewer_session_ttl_seconds` (15 minutes in the local configuration). The browser receives a short-lived, HTTP-only loopback cookie and sees only camera labels and local H-CAM endpoints; upstream stream URLs are not exposed to the page.

### Basic adapter-backend-dashboard

The basic no-animation operations dashboard is available at `/adapter-backend-dashboard`. It reports the adapter configuration, recorder state, worker count, live-viewer state, and the approved camera list. The dashboard does not start workers or recordings. If the live catalogue is unavailable, it continues to show the adapter snapshot and marks just the camera-list section unavailable.

### Camera monitoring dashboard extension

The DSS-style monitoring workspace is a second page at `/camera-monitoring-dashboard`; it extends rather than replaces the basic dashboard. Both pages link directly to each other and share the same short-lived, root-scoped browser session, `/cam-adapter/dashboard/data` camera/status response, and `/cam-adapter/live/whep/{camera_id}` live-video path. Opening the extension does not create another adapter, recording process, or separate camera configuration.

The extension provides a searchable camera resource list, one large selected-camera live view, adapter health, and selected-camera state. Its analytics-events rail deliberately stays empty until a real analytics event API is connected; it does not display fabricated ANPR detections.

Create a short-lived local dashboard launch link with the same headers:

```powershell
$dashboardSession = Invoke-RestMethod -Method Post -Headers $headers -Uri "http://127.0.0.1:8000/cam-adapter/dashboard/session"
Start-Process ("http://127.0.0.1:8000" + $dashboardSession.launch_path)
```

To launch directly into the monitoring extension, use the same headers:

```powershell
$monitoringSession = Invoke-RestMethod -Method Post -Headers $headers -Uri "http://127.0.0.1:8000/cam-adapter/monitoring-dashboard/session"
Start-Process ("http://127.0.0.1:8000" + $monitoringSession.launch_path)
```

The included Windows local setup uses `runtime/camera-adapter.json`; it is git-ignored and starts with no active streams. All segments and adapter logs remain under the local project directory.

**Env vars** (also in `Settings`):

```
HCAM_CAM_ADAPTER_DRIVE_BASE=/content/drive/MyDrive/cctv-h/camera_recordings
HCAM_CAM_ADAPTER_SEGMENT_TIME=300
HCAM_CAM_ADAPTER_SAMPLE_INTERVAL=2.0
HCAM_CAM_ADAPTER_YOLO_MODEL=yolov8n.pt
HCAM_CAM_ADAPTER_YOLO_CONF=0.35
HCAM_CAM_ADAPTER_TELEMETRY_INTERVAL=30
HCAM_CAM_ADAPTER_CONFIG_FILE=/absolute/path/to/camera-adapter.json
```

---

## Production notes

- **Memory:** keep Colab RAM < 80% — reduce `sample_interval` or `yolo_model` size if OOM; telemetry warns each 30s.
- **Drive IOPS:** `.json` per sample → for 4 cams × 0.5 fps = 2 writes/s, safe. For 10+ cams, set `yolo_classes=[2]` to reduce writes.
- **FFmpeg:** Colab has `ffmpeg 6.x`; for local Debian: `apt-get install ffmpeg`.
- **Credentials in URLs:** use env secrets, redacted in logs as `host/path`.
- **Phase-3 hook:** detections JSON schema is ready for `eGujCop/VAHAN` correlation — add `vehicle.plate` field when ANPR lands.

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `cv2.VideoCapture` hangs | check `OPENCV_FFMPEG_CAPTURE_OPTIONS` set **before** import; use `tcp`; test with `ffprobe` Cell 5 |
| Green/gray artifacts | TCP already forced; if persists, add `extra_ffmpeg_input_args=["-err_detect","ignore_err"]` |
| `torch.cuda.is_available()==False` | Runtime → Change runtime type → GPU; `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| Drive `No space` | `sample_interval` 5s, `yolo_classes` filter, or shard across Drives |
| Segments 0 bytes | check `ffmpeg.log` per camera; often auth 401 — URL-encode `user:pass` |

