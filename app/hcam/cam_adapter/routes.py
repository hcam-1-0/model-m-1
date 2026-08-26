from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from hcam.database import get_session
from hcam.security.auth import Principal, RoleGuard, CAMERA_VIEWER, PLATFORM_ADMIN
from .config import AdapterConfig

router = APIRouter(prefix="/cam-adapter", tags=["cam-adapter"])


class AdapterStatus(BaseModel):
    enabled: bool
    base: str
    segment_time: int
    streams_configured: int
    streams_enabled: int
    yolo_model: str
    sample_interval: float


def _get_adapter_config() -> AdapterConfig:
    # Lightweight: read from env/file or return defaults
    # For now return defaults; in production wire to Settings or DB
    return AdapterConfig()


@router.get("/status", response_model=AdapterStatus)
def adapter_status(
    principal: Principal = Depends(RoleGuard(CAMERA_VIEWER, PLATFORM_ADMIN)),
    cfg: AdapterConfig = Depends(_get_adapter_config),
) -> AdapterStatus:
    return AdapterStatus(
        enabled=True,
        base=str(cfg.effective_base()),
        segment_time=cfg.segment_time_seconds,
        streams_configured=len(cfg.streams),
        streams_enabled=sum(1 for s in cfg.streams if s.enabled),
        yolo_model=cfg.yolo_model,
        sample_interval=cfg.sample_interval_seconds,
    )


@router.get("/streams")
def adapter_streams(
    principal: Principal = Depends(RoleGuard(CAMERA_VIEWER, PLATFORM_ADMIN)),
    cfg: AdapterConfig = Depends(_get_adapter_config),
) -> list[dict[str, Any]]:
    # Redact URLs
    out = []
    for s in cfg.streams:
        out.append({
            "camera_id": s.camera_id,
            "enabled": s.enabled,
            "location_label": s.location_label,
            "department": s.department,
            "url_redacted": s.rtsp_url.split("@")[-1] if "@" in s.rtsp_url else s.rtsp_url[:80],
        })
    return out
