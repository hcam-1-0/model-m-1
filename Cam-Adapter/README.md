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
curl -H "X-HCAM-User: dev" -H "X-HCAM-Roles: camera_viewer" http://localhost:8000/cam-adapter/status
```

**Env vars** (also in `Settings`):

```
HCAM_CAM_ADAPTER_DRIVE_BASE=/content/drive/MyDrive/cctv-h/camera_recordings
HCAM_CAM_ADAPTER_SEGMENT_TIME=300
HCAM_CAM_ADAPTER_SAMPLE_INTERVAL=2.0
HCAM_CAM_ADAPTER_YOLO_MODEL=yolov8n.pt
HCAM_CAM_ADAPTER_YOLO_CONF=0.35
HCAM_CAM_ADAPTER_TELEMETRY_INTERVAL=30
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

