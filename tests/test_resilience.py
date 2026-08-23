from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url


def test_database_outage_fails_readiness_and_returns_generic_api_error(
    app,
    viewer_headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    database_path = Path(make_url(app.state.settings.database_url).database or "")
    caplog.set_level(logging.ERROR, logger="hcam.error")

    with TestClient(app) as client:
        app.state.database.dispose()
        database_path.unlink()
        readiness = client.get("/health/ready")
        registry = client.get(
            "/cameras?token=must-not-leak",
            headers=viewer_headers,
        )

    assert readiness.status_code == 503
    assert readiness.json() == {"detail": "Database is not ready"}
    assert registry.status_code == 500
    assert registry.json() == {"detail": "Internal server error"}
    assert "X-Request-ID" in registry.headers
    errors = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "hcam.error"
    ]
    assert errors[-1]["exception_type"] == "OperationalError"
    rendered = json.dumps(errors)
    assert "must-not-leak" not in rendered
    assert str(database_path) not in rendered
    assert viewer_headers["X-HCAM-Actor"] not in rendered
