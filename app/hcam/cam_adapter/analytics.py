from __future__ import annotations

import gc
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# TCP enforcement for the analytics capture path as well
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore

try:
    import torch  # type: ignore
except ImportError:
    torch = None  # type: ignore

try:
    from ultralytics import YOLO  # type: ignore
except ImportError:
    YOLO = None  # type: ignore


COCO_LABELS = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck",
}


class FrameSampler:
    """Zero-copy frame sampler — reads 1 frame every N seconds, runs YOLO, writes JSON."""

    def __init__(
        self,
        rtsp_url: str,
        camera_id: str,
        detections_dir: Path,
        *,
        sample_interval: float = 2.0,
        yolo_model: str = "yolov8n.pt",
        yolo_conf: float = 0.35,
        yolo_classes: list[int] | None = None,
        yolo_device: str | None = None,
        rtsp_transport: str = "tcp",
    ) -> None:
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.detections_dir = detections_dir
        self.sample_interval = sample_interval
        self.yolo_model_id = yolo_model
        self.yolo_conf = yolo_conf
        self.yolo_classes = yolo_classes
        self.rtsp_transport = rtsp_transport
        self._cap: Any = None
        self._yolo: Any = None
        self._device = yolo_device or ("0" if (torch is not None and torch.cuda.is_available()) else "cpu")
        self._last_sample_wall = 0.0

    # ---- lazy YOLO load ----
    def _ensure_yolo(self) -> Any:
        if self._yolo is not None:
            return self._yolo
        if YOLO is None:
            raise RuntimeError("ultralytics not installed — pip install ultralytics")
        model = YOLO(self.yolo_model_id)
        # Warm up device selection; ultralytics handles cuda automatically
        self._yolo = model
        return model

    # ---- capture ----
    def _ensure_capture(self) -> Any:
        if cv2 is None:
            raise RuntimeError("opencv-python not installed")
        if self._cap is not None and self._cap.isOpened():
            return self._cap
        # Reopen with TCP
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
        # Set FFMPEG options before open
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{self.rtsp_transport}"
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        # Low-latency tuning
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self._cap = cap
        return cap

    def _read_frame(self) -> Any | None:
        cap = self._ensure_capture()
        if not cap.isOpened():
            return None
        # Grab latest frame, drop buffered frames to reduce latency
        # Do a single read; if we want to flush buffer, we could grab() a few times
        ok, frame = cap.read()
        if not ok or frame is None:
            # Try reopen once
            try:
                cap.release()
            except Exception:
                pass
            self._cap = None
            return None
        return frame

    # ---- inference ----
    def sample_once(self) -> dict[str, Any] | None:
        """Attempt one sampled inference if interval elapsed. Returns detection dict or None."""
        now = time.monotonic()
        if now - self._last_sample_wall < self.sample_interval:
            return None
        self._last_sample_wall = now

        frame = self._read_frame()
        if frame is None:
            return None

        try:
            yolo = self._ensure_yolo()
            # autocast for CUDA
            use_cuda = torch is not None and torch.cuda.is_available() and self._device != "cpu"
            if use_cuda:
                with torch.cuda.amp.autocast():  # type: ignore[union-attr]
                    results = yolo.predict(
                        source=frame, conf=self.yolo_conf, classes=self.yolo_classes,
                        verbose=False, device=self._device,
                    )
            else:
                results = yolo.predict(
                    source=frame, conf=self.yolo_conf, classes=self.yolo_classes,
                    verbose=False, device=self._device,
                )

            # results[0] is the single frame
            r = results[0]
            detections: list[dict[str, Any]] = []
            if r.boxes is not None and len(r.boxes) > 0:
                xyxy = r.boxes.xyxy.cpu().numpy()  # type: ignore[union-attr]
                conf = r.boxes.conf.cpu().numpy()  # type: ignore[union-attr]
                cls = r.boxes.cls.cpu().numpy().astype(int)  # type: ignore[union-attr]
                for (x1, y1, x2, y2), c, k in zip(xyxy, conf, cls):
                    detections.append({
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "conf": float(c),
                        "class_id": int(k),
                        "label": COCO_LABELS.get(int(k), str(int(k))),
                    })

            payload: dict[str, Any] = {
                "camera_id": self.camera_id,
                "ts": datetime.now(timezone.utc).isoformat(),
                "rtsp_url_redacted": self.rtsp_url.split("@")[-1] if "@" in self.rtsp_url else self.rtsp_url,
                "model": self.yolo_model_id,
                "conf_thresh": self.yolo_conf,
                "detections": detections,
                "count": len(detections),
            }
            return payload
        finally:
            # Zero-copy / memory protection: dereference frame, collect
            try:
                del frame  # type: ignore
            except Exception:
                pass
            gc.collect()
            if torch is not None and torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()  # type: ignore[union-attr]
                except Exception:
                    pass

    def write_detection(self, payload: dict[str, Any]) -> Path:
        """Write detection payload to timestamped JSON in detections_dir. Returns path."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]
        # Also include sample timestamp for uniqueness
        fname = f"{self.camera_id}_{ts}.json"
        out = self.detections_dir / fname
        out.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(out)
        return out

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
