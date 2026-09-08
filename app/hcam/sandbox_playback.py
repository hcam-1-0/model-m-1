"""Loopback-only LAB WHEP session fixture; disabled unless explicitly enabled."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["lab-sandbox"])


@router.post("/api/cameras/{camera_id}/playback")
def lab_playback(camera_id: str) -> dict[str, str]:
    if os.getenv("HCAM_ALLOW_LAB_WHEP_SANDBOX", "").lower() != "true":
        raise HTTPException(404, "LAB sandbox disabled")
    if camera_id != os.getenv("HCAM_LAB_WHEP_CAMERA_ID", "LAB-SANDBOX-001"):
        raise HTTPException(404, "LAB camera not found")
    url = os.getenv("HCAM_LAB_WHEP_URL", "http://127.0.0.1:8889/lab/sandbox/whep")
    parsed = urlparse(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != 8889
        or parsed.path != "/lab/sandbox/whep"
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise HTTPException(500, "LAB WHEP URL must be the approved loopback endpoint")
    return {"stream_id": "lab-sandbox", "whep_url": url}
