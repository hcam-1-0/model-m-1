from __future__ import annotations

import json

import pytest

from tools import issue9_browser_evidence as evidence
from tools.issue9_evidence_safety import EvidenceSafetyError, validate


def test_dashboard_fixture_is_display_safe_and_non_previewable_for_hevc() -> None:
    camera = evidence._safe_camera(stale=True)

    assert camera["lifecycle_state"] == "stale"
    assert camera["preview_compatible"] is False
    assert camera["media"] == {"codec": "hevc", "width": 320, "height": 180, "fps": 24}
    assert all("url" not in str(value).lower() for value in camera.values())


def test_media_page_uses_real_html_video_state() -> None:
    page = evidence._video_page("media-h264").decode("utf-8")

    assert "<video" in page
    assert "video.paused" in page
    assert "video.readyState" in page
    assert "video.currentTime" in page
    assert "video.error !== null" in page
    assert "http" not in page


def test_published_browser_evidence_rejects_sensitive_values(tmp_path) -> None:
    path = tmp_path / "evidence.json"
    safe = {
        "schema": "hcam.issue9.browser_evidence.v1",
        "classification": "generated-only",
        "provider_contacted": False,
        "retained_media": False,
    }
    path.write_text(json.dumps(safe), encoding="ascii")
    assert validate(path)["valid"] is True

    path.write_text(json.dumps({**safe, "unexpected": "rtsp://sensitive"}), encoding="ascii")
    with pytest.raises(EvidenceSafetyError, match="evidence_sensitive_content"):
        validate(path)
