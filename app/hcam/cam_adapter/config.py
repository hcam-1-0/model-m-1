from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StreamConfig(BaseModel):
    """Single camera stream definition — maps 1:1 to HCAM camera registry."""

    camera_id: str = Field(description="Stable HCAM camera_id, also used as folder name")
    rtsp_url: str = Field(description="RTSP or HLS URL; credentials should be pre-injected via env/secret")
    enabled: bool = True
    transport: Literal["tcp", "udp"] = "tcp"
    # Optional metadata forwarded to JSON detections / telemetry
    location_label: str | None = None
    department: str | None = None


class AdapterConfig(BaseModel):
    """Top-level Cam-Adapter runtime config — env-driven, Colab and server share this."""

    # Storage
    drive_base: Path = Field(default=Path("/content/drive/MyDrive/cctv-h/camera_recordings"))
    local_fallback_base: Path = Field(default=Path("./camera_recordings"))

    # Segmentation
    segment_time_seconds: int = Field(default=300, ge=30, le=3600, description="MP4 chunk length")
    segment_format: Literal["mp4"] = "mp4"

    # Analytics sampling
    sample_interval_seconds: float = Field(default=2.0, ge=0.5, le=60)
    yolo_model: str = Field(default="yolov8n.pt", description="ultralytics model id or local path")
    yolo_conf: float = Field(default=0.35, ge=0.1, le=0.95)
    yolo_classes: list[int] | None = Field(default=None, description="None = all COCO classes; e.g. [0,2,7] for person/car/truck")
    yolo_device: str = Field(default="0", description="cuda device id or 'cpu'")

    # Resilience
    max_reconnect_attempts: int = Field(default=0, ge=0, description="0 = infinite")
    backoff_base_seconds: float = Field(default=1.0, ge=0.2)
    backoff_max_seconds: float = Field(default=60.0, ge=5)
    backoff_jitter: float = Field(default=0.4, ge=0, le=1)

    # Telemetry
    telemetry_interval_seconds: float = Field(default=30.0, ge=5)

    # FFmpeg tuning
    ffmpeg_bin: str = Field(default="ffmpeg")
    ffprobe_bin: str = Field(default="ffprobe")
    rtsp_transport: Literal["tcp", "udp"] = "tcp"
    extra_ffmpeg_input_args: list[str] = Field(default_factory=list)
    extra_ffmpeg_output_args: list[str] = Field(default_factory=list)

    # Streams
    streams: list[StreamConfig] = Field(default_factory=list)

    @field_validator("streams")
    @classmethod
    def at_least_one_when_required(cls, v: list[StreamConfig]) -> list[StreamConfig]:
        # Allow empty at import time; validation happens at runtime
        return v

    def drive_camera_dir(self, camera_id: str) -> Path:
        return self.drive_base / camera_id

    def effective_base(self) -> Path:
        # In Colab /content/drive exists after mount; elsewhere use fallback
        if self.drive_base.parent.exists() or self.drive_base.exists():
            return self.drive_base
        return self.local_fallback_base
