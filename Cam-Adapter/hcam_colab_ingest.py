# %% [markdown]
# # H-CAM Cam-Adapter — Colab Production Ingest (RTSP/HLS → Drive + YOLOv8)
# **Google Colab | Multi-stream | Segmented MP4 | Zero-copy | YOLOv8 sampling | Auto-reconnect**
#
# Target: `/content/drive/MyDrive/cctv-h/camera_recordings/<camera_id>/segments/*.mp4` + `detections/*.json`
# Stack: Python 3.12, FFmpeg (stream copy), OpenCV TCP, PyTorch CUDA, Ultralytics YOLOv8, psutil
# 
# **How to use:** Run cells top-to-bottom. Edit `STREAMS` in Cell 4 before starting.
# Requires: Colab GPU (T4/L4) for YOLO, Drive mount for persistence.

# %% [code] — Cell 1: Environment & Drive mount
import os, sys, time, json, subprocess, pathlib
print("Python:", sys.version)
# Drive mount — idempotent
try:
    from google.colab import drive
    if not pathlib.Path("/content/drive/MyDrive").exists():
        print("Mounting Drive...")
        drive.mount('/content/drive')
    else:
        print("Drive already mounted")
    print("Drive OK:", pathlib.Path("/content/drive/MyDrive").exists())
except ImportError:
    print("[WARN] Not in Colab — Drive mount skipped (local fallback will be used)")

# GPU check
try:
    import torch
    print("Torch:", torch.__version__, "CUDA:", torch.cuda.is_available(), "Device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
except Exception as e:
    print("Torch not yet installed:", e)

# FFmpeg check
try:
    print(subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5).stdout.splitlines()[0])
except Exception as e:
    print("FFmpeg missing:", e)

# TCP enforcement at process start (must be before cv2 import)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = "rtsp_transport;tcp"
print("ENV OPENCV_FFMPEG_CAPTURE_OPTIONS=", os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"])

# %% [code] — Cell 2: Install dependencies (Colab)
# Run once per runtime. Safe to re-run — pip will skip satisfied.
# Comment out after first successful run to save time.
import subprocess, sys
pkgs = [
    "ultralytics>=8.2",
    "opencv-python>=4.8",
    "psutil>=5.9",
    "shapely",  # kept for parity with hcam-core gis; not required for ingest
]
print("Installing:", pkgs)
# Use --no-cache-dir to reduce disk, --quiet for clean logs
ret = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir"] + pkgs, text=True)
print("pip exit:", ret.returncode)
# Verify
try:
    import cv2, psutil
    from ultralytics import YOLO
    import torch
    print("cv2", cv2.__version__, "psutil", psutil.__version__, "ultralytics OK", "torch CUDA", torch.cuda.is_available())
except Exception as e:
    print("Post-install verify failed:", e)
    raise

# %% [code] — Cell 3: Imports & global helpers (standalone fallback + package-aware)
import gc, random, threading, math, shlex, signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import cv2
import psutil
import torch
from ultralytics import YOLO

# Try to import from hcam-core package if available (pip install -e .), else fallback to inline logic
try:
    from hcam.cam_adapter.config import AdapterConfig, StreamConfig  # type: ignore
    from hcam.cam_adapter.recorder import build_ffmpeg_segment_cmd, ensure_camera_dirs, popen_recorder, terminate_recorder  # type: ignore
    from hcam.cam_adapter.analytics import FrameSampler  # type: ignore
    from hcam.cam_adapter.telemetry import TelemetryLoop  # type: ignore
    from hcam.cam_adapter.worker import CameraWorker, AdapterOrchestrator  # type: ignore
    HCAM_PACKAGE = True
    print("hcam.cam_adapter package found — will use it")
except Exception as e:
    HCAM_PACKAGE = False
    print("hcam package not found, using inline fallback:", e)
    # ---------- INLINE FALLBACK (full implementation in this file) ----------
    # This keeps the Colab script self-contained even without pip install -e .
    # Config
    from pydantic import BaseModel, Field
    from typing import Literal
    class StreamConfig(BaseModel):
        camera_id: str
        rtsp_url: str
        enabled: bool = True
        transport: Literal["tcp","udp"] = "tcp"
        location_label: str | None = None
        department: str | None = None
    class AdapterConfig(BaseModel):
        drive_base: Path = Path("/content/drive/MyDrive/cctv-h/camera_recordings")
        local_fallback_base: Path = Path("./camera_recordings")
        segment_time_seconds: int = 300
        sample_interval_seconds: float = 2.0
        yolo_model: str = "yolov8n.pt"
        yolo_conf: float = 0.35
        yolo_classes: list[int] | None = None
        yolo_device: str = "0"
        max_reconnect_attempts: int = 0
        backoff_base_seconds: float = 1.0
        backoff_max_seconds: float = 60.0
        backoff_jitter: float = 0.4
        telemetry_interval_seconds: float = 30.0
        ffmpeg_bin: str = "ffmpeg"
        rtsp_transport: str = "tcp"
        extra_ffmpeg_input_args: list[str] = Field(default_factory=list)
        extra_ffmpeg_output_args: list[str] = Field(default_factory=list)
        streams: list[StreamConfig] = Field(default_factory=list)
        def effective_base(self) -> Path:
            return self.drive_base if self.drive_base.parent.exists() or self.drive_base.exists() else self.local_fallback_base
        def drive_camera_dir(self, cid: str) -> Path:
            return self.drive_base / cid
    # Recorder helpers
    def build_ffmpeg_segment_cmd(*, ffmpeg_bin, rtsp_url, output_pattern, segment_time=300, rtsp_transport="tcp", extra_input_args=(), extra_output_args=(), is_hls=None):
        if is_hls is None:
            is_hls = rtsp_url.lower().endswith(".m3u8") or "m3u8" in rtsp_url.lower()
        cmd=[ffmpeg_bin,"-hide_banner","-loglevel","warning"]
        if not is_hls and rtsp_transport=="tcp": cmd+=["-rtsp_transport","tcp"]
        cmd+=["-fflags","+genpts","-use_wallclock_as_timestamps","1"]+list(extra_input_args)+["-i",rtsp_url]
        cmd+=["-c:v","copy","-c:a","aac","-b:a","64k","-movflags","+frag_keyframe+empty_moov+default_base_moof","-f","segment","-segment_time",str(segment_time),"-segment_format","mp4","-segment_format_options","movflags=+frag_keyframe+empty_moov+default_base_moof","-reset_timestamps","1","-strftime","1"]+list(extra_output_args)+[output_pattern]
        return cmd
    def ensure_camera_dirs(base: Path, camera_id: str):
        cam=base/camera_id; seg=cam/"segments"; det=cam/"detections"; seg.mkdir(parents=True, exist_ok=True); det.mkdir(parents=True, exist_ok=True); return cam,seg,det
    def popen_recorder(cmd, log_path: Path):
        import subprocess
        log_path.parent.mkdir(parents=True, exist_ok=True)
        lf=open(log_path,"ab",buffering=0)
        proc=subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=lf, stdin=subprocess.DEVNULL, start_new_session=True)
        proc._log_file=lf  # type: ignore
        return proc
    def terminate_recorder(proc, timeout=8.0):
        import subprocess
        try:
            if getattr(proc,"stdin",None) is not None:
                try: proc.stdin.write(b"q"); proc.stdin.flush()
                except: pass
            proc.terminate()
            try: proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
        finally:
            lf=getattr(proc,"_log_file",None)
            if lf:
                try: lf.close()
                except: pass
    # Analytics sampler
    COCO_LABELS={0:"person",1:"bicycle",2:"car",3:"motorcycle",5:"bus",7:"truck"}
    class FrameSampler:
        def __init__(self, rtsp_url, camera_id, detections_dir, sample_interval=2.0, yolo_model="yolov8n.pt", yolo_conf=0.35, yolo_classes=None, yolo_device=None, rtsp_transport="tcp"):
            self.rtsp_url=rtsp_url; self.camera_id=camera_id; self.detections_dir=detections_dir
            self.sample_interval=sample_interval; self.yolo_model_id=yolo_model; self.yolo_conf=yolo_conf
            self.yolo_classes=yolo_classes; self.rtsp_transport=rtsp_transport; self._cap=None; self._yolo=None
            self._device=yolo_device or ("0" if torch.cuda.is_available() else "cpu"); self._last_sample_wall=0.0
        def _ensure_yolo(self):
            if self._yolo is not None: return self._yolo
            self._yolo=YOLO(self.yolo_model_id); return self._yolo
        def _ensure_capture(self):
            if self._cap is not None and self._cap.isOpened(): return self._cap
            if self._cap is not None:
                try: self._cap.release()
                except: pass
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]=f"rtsp_transport;{self.rtsp_transport}"
            cap=cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            try: cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
            except: pass
            self._cap=cap; return cap
        def _read_frame(self):
            cap=self._ensure_capture()
            if not cap.isOpened(): return None
            ok,frame=cap.read()
            if not ok or frame is None:
                try: cap.release()
                except: pass
                self._cap=None; return None
            return frame
        def sample_once(self):
            import time
            now=time.monotonic()
            if now-self._last_sample_wall < self.sample_interval: return None
            self._last_sample_wall=now
            frame=self._read_frame()
            if frame is None: return None
            try:
                yolo=self._ensure_yolo()
                use_cuda=torch.cuda.is_available() and self._device!="cpu"
                if use_cuda:
                    with torch.cuda.amp.autocast():
                        results=yolo.predict(source=frame, conf=self.yolo_conf, classes=self.yolo_classes, verbose=False, device=self._device)
                else:
                    results=yolo.predict(source=frame, conf=self.yolo_conf, classes=self.yolo_classes, verbose=False, device=self._device)
                r=results[0]; dets=[]
                if r.boxes is not None and len(r.boxes)>0:
                    xyxy=r.boxes.xyxy.cpu().numpy(); conf=r.boxes.conf.cpu().numpy(); cls=r.boxes.cls.cpu().numpy().astype(int)
                    for (x1,y1,x2,y2),c,k in zip(xyxy,conf,cls):
                        dets.append({"bbox":[float(x1),float(y1),float(x2),float(y2)],"conf":float(c),"class_id":int(k),"label":COCO_LABELS.get(int(k),str(int(k)))})
                payload={"camera_id":self.camera_id,"ts":datetime.now(timezone.utc).isoformat(),"model":self.yolo_model_id,"conf_thresh":self.yolo_conf,"detections":dets,"count":len(dets)}
                return payload
            finally:
                try: del frame
                except: pass
                gc.collect()
                if torch.cuda.is_available():
                    try: torch.cuda.empty_cache()
                    except: pass
        def write_detection(self,payload):
            ts=datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]
            out=self.detections_dir/f"{self.camera_id}_{ts}.json"
            out.parent.mkdir(parents=True,exist_ok=True)
            tmp=out.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,indent=2),encoding="utf-8"); tmp.replace(out); return out
        def close(self):
            if self._cap is not None:
                try: self._cap.release()
                except: pass
                self._cap=None
    def _human_bytes(n):
        for u in ("B","KB","MB","GB"):
            if abs(n)<1024: return f"{n:.1f}{u}"
            n/=1024
        return f"{n:.1f}TB"
    def collect_drive_usage(base: Path):
        total=count=0
        if not base.exists(): return 0,0
        for p in base.rglob("*.mp4"):
            try: total+=p.stat().st_size; count+=1
            except: continue
        return total,count
    def collect_system_stats():
        s={}
        try:
            s["cpu_percent"]=psutil.cpu_percent(interval=None)
            vm=psutil.virtual_memory(); s["ram_percent"]=vm.percent; s["ram_used"]=_human_bytes(vm.used); s["ram_total"]=_human_bytes(vm.total)
            s["disk_percent"]=psutil.disk_usage(str(Path.cwd())).percent
        except Exception as e: s["psutil_error"]=str(e)
        if torch.cuda.is_available():
            try:
                s["cuda_available"]=True; s["cuda_device_count"]=torch.cuda.device_count()
                for i in range(torch.cuda.device_count()):
                    s[f"gpu_{i}_mem_allocated"]=_human_bytes(torch.cuda.memory_allocated(i))
            except Exception as e: s["cuda_error"]=str(e)
        else: s["cuda_available"]=False
        return s
    class TelemetryLoop:
        def __init__(self, base, interval=30.0, logger=None, log_file=None):
            self.base=base; self.interval=interval; self.logger=logger or (lambda m: print(m,flush=True)); self.log_file=log_file; self._stop=threading.Event(); self._thread=None
        def start(self):
            if self._thread and self._thread.is_alive(): return
            self._stop.clear(); self._thread=threading.Thread(target=self._loop,name="hcam-telemetry",daemon=True); self._thread.start()
        def stop(self):
            self._stop.set()
            if self._thread: self._thread.join(timeout=5)
        def _log(self,msg):
            try: self.logger(msg)
            except: pass
            if self.log_file:
                try:
                    self.log_file.parent.mkdir(parents=True,exist_ok=True)
                    open(self.log_file,"a",encoding="utf-8").write(msg+"\n")
                except: pass
        def _loop(self):
            try: psutil.cpu_percent(interval=None)
            except: pass
            while not self._stop.is_set():
                try:
                    tb,c=collect_drive_usage(self.base); ss=collect_system_stats()
                    ts=time.strftime("%Y-%m-%d %H:%M:%S")
                    line=f"[{ts}] TELEMETRY base={self.base} segments={c} drive_used={_human_bytes(tb)} cpu={ss.get('cpu_percent','?')}% ram={ss.get('ram_percent','?')}% cuda={ss.get('cuda_available',False)}"
                    self._log(line)
                except Exception as e: self._log(f"[telemetry] {e}")
                self._stop.wait(self.interval)
    def exponential_backoff(attempt, base, cap, jitter):
        exp=min(cap, base*(2**attempt))
        if jitter<=0: return exp
        low=exp*(1-jitter); return random.uniform(low, exp)
    class CameraWorker(threading.Thread):
        def __init__(self, stream, cfg, base, logger=None):
            super().__init__(name=f"hcam-worker-{stream.camera_id}",daemon=True)
            self.stream=stream; self.cfg=cfg; self.base=base; self.logger=logger or (lambda m: print(m,flush=True)); self._stop=threading.Event(); self._proc=None; self._sampler=None
        def _log(self,msg):
            try: self.logger(f"[{self.stream.camera_id}] {msg}")
            except: pass
        def stop(self):
            self._stop.set()
            if self._proc:
                try: terminate_recorder(self._proc)
                except: pass
            if self._sampler:
                try: self._sampler.close()
                except: pass
        def run(self):
            attempt=0
            _,seg_dir,det_dir=ensure_camera_dirs(self.base,self.stream.camera_id)
            log_path=self.base/self.stream.camera_id/"ffmpeg.log"
            try: self._sampler=FrameSampler(self.stream.rtsp_url,self.stream.camera_id,det_dir,self.cfg.sample_interval_seconds,self.cfg.yolo_model,self.cfg.yolo_conf,self.cfg.yolo_classes,self.cfg.yolo_device,self.cfg.rtsp_transport)
            except Exception as e: self._log(f"sampler init failed: {e}"); self._sampler=None
            pattern=str(seg_dir/f"{self.stream.camera_id}_%Y-%m-%d_%H-%M-%S.mp4")
            cmd=build_ffmpeg_segment_cmd(ffmpeg_bin=self.cfg.ffmpeg_bin, rtsp_url=self.stream.rtsp_url, output_pattern=pattern, segment_time=self.cfg.segment_time_seconds, rtsp_transport=self.cfg.rtsp_transport, extra_input_args=self.cfg.extra_ffmpeg_input_args, extra_output_args=self.cfg.extra_ffmpeg_output_args)
            self._log(f"FFmpeg: {' '.join(cmd)}")
            while not self._stop.is_set():
                if self.cfg.max_reconnect_attempts and attempt>=self.cfg.max_reconnect_attempts: self._log("max attempts reached"); break
                if attempt>0:
                    bo=exponential_backoff(attempt-1,self.cfg.backoff_base_seconds,self.cfg.backoff_max_seconds,self.cfg.backoff_jitter)
                    self._log(f"backoff {bo:.1f}s (attempt {attempt})")
                    if self._stop.wait(bo): break
                self._log(f"starting recorder attempt {attempt}")
                try: self._proc=popen_recorder(cmd,log_path)
                except Exception as e: self._log(f"popen failed {e}"); attempt+=1; continue
                healthy_since=time.monotonic()
                while not self._stop.is_set():
                    ret=self._proc.poll()
                    if ret is not None:
                        self._log(f"FFmpeg exited {ret} -> reconnect")
                        try:
                            lf=getattr(self._proc,"_log_file",None)
                            if lf: lf.close()
                        except: pass
                        self._proc=None
                        if self._sampler:
                            try: self._sampler.close()
                            except: pass
                        break
                    if self._sampler:
                        try:
                            p=self._sampler.sample_once()
                            if p is not None:
                                out=self._sampler.write_detection(p)
                                if p["count"]>0: self._log(f"YOLO {p['count']} -> {out.name}")
                        except Exception as e: self._log(f"analytics {e}")
                        gc.collect()
                    if time.monotonic()-healthy_since>90 and attempt!=0:
                        self._log("healthy 90s reset backoff"); attempt=0; healthy_since=time.monotonic()
                    if self._stop.wait(0.5): break
                if self._stop.is_set():
                    if self._proc:
                        try: terminate_recorder(self._proc)
                        except: pass
                        self._proc=None
                    break
                attempt+=1
            self._log("worker stopped")
            if self._sampler:
                try: self._sampler.close()
                except: pass
    class AdapterOrchestrator:
        def __init__(self,cfg,base=None,logger=None):
            self.cfg=cfg; self.base=base or cfg.effective_base(); self.logger=logger or (lambda m: print(m,flush=True)); self.workers=[]; self.telemetry=TelemetryLoop(self.base,cfg.telemetry_interval_seconds,self.logger, self.base/"_telemetry.log")
        def start(self):
            self.base.mkdir(parents=True,exist_ok=True); self.telemetry.start()
            for s in self.cfg.streams:
                if not s.enabled: continue
                w=CameraWorker(s,self.cfg,self.base,self.logger); w.start(); self.workers.append(w)
            self.logger(f"[orch] {len(self.workers)} workers @ {self.base}")
        def stop(self):
            self.logger("[orch] stopping..."); self.telemetry.stop()
            for w in self.workers: w.stop()
            for w in self.workers: w.join(timeout=10)
            self.logger("[orch] stopped")
        def wait(self):
            try:
                while any(w.is_alive() for w in self.workers): time.sleep(1)
            except KeyboardInterrupt: self.stop()
    print("Inline fallback classes loaded")

print("Imports OK. HCAM_PACKAGE=", HCAM_PACKAGE)

# %% [code] — Cell 4: Adjustable parameters — EDIT THIS
# -------------------------------------------------------------------
# Fill your live streams here. Works for RTSP and HLS (.m3u8).
# For Gujarat Sentinel feeds host is live.corp8.cloud (30 cams).
# Tip: Keep 2-3 streams per Colab T4; 4-6 max on L4/High-RAM.
# -------------------------------------------------------------------
# Option A: Manual list (uncomment what you need)
STREAMS = [
    # Live Sentinel examples — verified 2026-08-26 (live:true, mix h264/hevc)
    StreamConfig(camera_id="cam_06", rtsp_url="rtsp://live.corp8.cloud:8554/stream/6", location_label="06 Timbavadi gate-Junagadh", department="Gujarat Police"),
    StreamConfig(camera_id="cam_13", rtsp_url="rtsp://live.corp8.cloud:8554/stream/13", location_label="13 CN Vidhyalaya", department="Gujarat Police"),
    StreamConfig(camera_id="cam_23", rtsp_url="rtsp://live.corp8.cloud:8554/stream/23", location_label="30 kheram", department="Gujarat Police"),
    # Add more: cam_17 (Rajkot Bus Port hevc), cam_22 (Mervada hevc), cam_26 (TANKAL 2.5K hevc)
]
# Option B: Auto-load ALL live from /api/ingest (overwrites STREAMS above when enabled)
USE_SENTINEL_CATALOG = True  # set False to keep manual STREAMS
SENTINEL_API = "https://live.corp8.cloud/api/ingest"
SENTINEL_MAX_CAMERAS = 10  # 10-cam dry-run; 3-4 on T4, 6-10 on L4/High-RAM
# Dry-run HLS fallback (443, firewall-safe) — set True if RTSP 8554 blocked
SENTINEL_USE_HLS = False  # True → https://live.corp8.cloud/live/stream/<id>/index.m3u8

# Fallback: if you pasted raw strings, convert
if len(STREAMS)==0:
    print("[WARN] STREAMS is empty — add your URLs above before running Cell 6")

CONFIG = AdapterConfig(
    drive_base=Path("/content/drive/MyDrive/cctv-h/camera_recordings"),
    local_fallback_base=Path("/content/camera_recordings"),  # if Drive not mounted
    segment_time_seconds=300,          # 5-min chunks — tweak to 60/600
    sample_interval_seconds=2.0,       # YOLO every 2 sec — lower=more GPU, higher=sparser
    yolo_model="yolov8n.pt",           # n=fastest, s/m for accuracy
    yolo_conf=0.35,
    yolo_classes=None,                 # None=all; e.g. [0,2,5,7]=person/car/bus/truck only
    # yolo_classes=[0,2,5,7],
    yolo_device="0",                   # "0" for CUDA, "cpu" to force CPU
    backoff_base_seconds=1.0,
    backoff_max_seconds=60.0,
    telemetry_interval_seconds=30.0,
    ffmpeg_bin="ffmpeg",
    rtsp_transport="tcp",
    streams=STREAMS,
)

# Sentinel catalog loader (live.corp8.cloud) — also works for HCAM registry
import httpx
if 'USE_SENTINEL_CATALOG' in globals() and USE_SENTINEL_CATALOG:
    try:
        r=httpx.get(SENTINEL_API, timeout=10); r.raise_for_status()
        js=r.json(); cams=js.get("cameras", js.get("items", []))
        live=[c for c in cams if c.get("live", True)]
        # Prefer diverse set for dry-run: include Rajkot(17), Mervada(22), TANKAL(26), kheram(23)
        prefer_ids={"17","22","26","23","6","13","27","29","14","15"}
        prefer=[c for c in live if str(c.get("id")) in prefer_ids]
        rest=[c for c in live if str(c.get("id")) not in prefer_ids]
        ordered=(prefer+rest)[:SENTINEL_MAX_CAMERAS]
        def _url_for(c):
            if globals().get("SENTINEL_USE_HLS"):
                return f"https://live.corp8.cloud/live/stream/{c['id']}/index.m3u8"
            return c.get("rtsp_url") or f"rtsp://live.corp8.cloud:8554/stream/{c['id']}"
        STREAMS=[StreamConfig(camera_id=f"cam_{c['id']}", rtsp_url=_url_for(c), location_label=c.get("location"), department=c.get("department","Gujarat Police")) for c in ordered]
        CONFIG.streams = STREAMS  # sync catalog into CONFIG used by Cells 5-6
        print(f"Auto-loaded {len(STREAMS)} streams from {SENTINEL_API}: {[s.camera_id for s in STREAMS]}")
    except Exception as e:
        print("Sentinel catalog load failed, using manual STREAMS:", e)
# HCAM registry alternative (uncomment if using your hcam-core instead):
# HCAM_API="https://your-hcam-core.example.com"; HCAM_TOKEN=os.environ.get("HCAM_API_TOKEN")
# r=httpx.get(f"{HCAM_API}/cameras", headers={"Authorization": f"Bearer {HCAM_TOKEN}"}, params={"limit": 50}, timeout=10)
# CONFIG.streams=[StreamConfig(camera_id=c["camera_id"], rtsp_url=c["stream"]["selected_url"]) for c in r.json()["items"]]

print("CONFIG:", CONFIG.model_dump_json(indent=2))
print("Effective base:", CONFIG.effective_base())
# Validate writable
base = CONFIG.effective_base()
base.mkdir(parents=True, exist_ok=True)
test_file = base / "_write_test.tmp"
try:
    test_file.write_text("ok")
    test_file.unlink()
    print("Write test OK @", base)
except Exception as e:
    print("Write test FAILED:", e)
    print("Check Drive mount / permissions")

# %% [code] — Cell 5: Validate streams (ffprobe reachability — optional, non-blocking)
import subprocess
for s in CONFIG.streams:
    if not s.enabled: continue
    # Quick ffprobe host check — timeout fast so cell doesn't hang
    cmd=[CONFIG.ffprobe_bin,"-v","error","-rtsp_transport","tcp","-analyzeduration","0","-probesize","512k","-i",s.rtsp_url,"-show_entries","stream=codec_type","-of","csv=p=0"]
    try:
        r=subprocess.run(cmd, capture_output=True, timeout=6, text=True)
        ok=r.returncode==0 and r.stdout.strip()!=""
        print(f"{s.camera_id}: {'REACHABLE' if ok else 'UNREACHABLE (will retry)'} — {s.rtsp_url.split('@')[-1][:60]}")
        if not ok and r.stderr: print("  ffprobe:", r.stderr[:300])
    except Exception as e:
        print(f"{s.camera_id}: probe error {e} — will retry in worker")

# %% [code] — Cell 6: Start orchestrator (blocking — keep cell running)
# This cell runs until you interrupt (Runtime → Interrupt execution).
# It launches 1 thread per camera + 1 telemetry thread.
# Logs go to console + /content/drive/MyDrive/cctv-h/camera_recordings/_telemetry.log

orchestrator = AdapterOrchestrator(cfg=CONFIG, base=base, logger=lambda m: print(m, flush=True))
print("Starting orchestrator...")
orchestrator.start()
print("Workers running. Logs tail every 30s via telemetry.")
print("Segments ->", base)
print("Interrupt this cell (or Runtime → Interrupt) to stop cleanly.")
try:
    orchestrator.wait()
except KeyboardInterrupt:
    print("KeyboardInterrupt — stopping...")
    orchestrator.stop()
finally:
    orchestrator.stop()
    print("All stopped. Check Drive:", base)
    # List recent segments
    import pathlib
    for p in sorted(base.rglob("*.mp4"))[-10:]:
        print(p, f"{p.stat().st_size/1e6:.1f}MB" if p.exists() else "missing")

# %% [code] — Cell 7: (Optional) Inspect results — run after stop
from pathlib import Path
import json, glob
base = CONFIG.effective_base()
print("Base:", base)
print("Segments:", len(list(base.rglob("*.mp4"))))
print("Detections:", len(list(base.rglob("*.json"))))
# Show last 5 detections
for jf in sorted(base.rglob("*.json"))[-5:]:
    try:
        data=json.loads(jf.read_text())
        print(jf.name, "count", data.get("count"), "ts", data.get("ts"))
        for d in data.get("detections",[])[:3]:
            print(" ", d)
    except Exception as e:
        print(jf, e)
# Show disk usage
import shutil
du=shutil.disk_usage(str(base))
print(f"Disk used {du.used/1e9:.1f}GB / total {du.total/1e9:.1f}GB")

# %% [markdown]
# ## Integration with hcam-core backend
# - The same `AdapterConfig`/`StreamConfig` is used in `app/hcam/cam_adapter/` — import and reuse.
# - To auto-populate `STREAMS` from registry: uncomment the HCAM API block in Cell 4 and set `HCAM_API_TOKEN`.
# - To expose adapter status via FastAPI: see `app/hcam/cam_adapter/routes.py` → `GET /cam-adapter/status`.
# - For production (non-Colab): run `python -m hcam.cam_adapter.worker` or deploy as systemd/Docker Sidecar.

