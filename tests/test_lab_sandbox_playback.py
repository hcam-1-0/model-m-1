from fastapi.testclient import TestClient

from hcam.main import create_app
from hcam.settings import Settings


def test_lab_playback_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("HCAM_ALLOW_LAB_WHEP_SANDBOX", raising=False)
    with TestClient(create_app(Settings(database_url="sqlite://", create_schema=True))) as client:
        assert client.post("/api/cameras/LAB-SANDBOX-001/playback").status_code == 404


def test_lab_playback_returns_loopback_whep_only(monkeypatch):
    monkeypatch.setenv("HCAM_ALLOW_LAB_WHEP_SANDBOX", "true")
    monkeypatch.setenv("HCAM_LAB_WHEP_URL", "http://127.0.0.1:8889/lab/sandbox/whep")
    with TestClient(create_app(Settings(database_url="sqlite://", create_schema=True))) as client:
        response = client.post("/api/cameras/LAB-SANDBOX-001/playback")
    assert response.status_code == 200
    assert response.json() == {"stream_id": "lab-sandbox", "whep_url": "http://127.0.0.1:8889/lab/sandbox/whep"}


def test_lab_playback_rejects_non_sandbox_loopback_url(monkeypatch):
    monkeypatch.setenv("HCAM_ALLOW_LAB_WHEP_SANDBOX", "true")
    monkeypatch.setenv("HCAM_LAB_WHEP_URL", "http://127.0.0.1:8889/other/whep")
    with TestClient(create_app(Settings(database_url="sqlite://", create_schema=True))) as client:
        assert client.post("/api/cameras/LAB-SANDBOX-001/playback").status_code == 500
