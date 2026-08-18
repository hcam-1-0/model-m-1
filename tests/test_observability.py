from __future__ import annotations

import json
import logging
import asyncio
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.main import create_app
from hcam.observability import RequestContextMiddleware, request_id_from_scope
from hcam.settings import Settings


def _access_events(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    return [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "hcam.access"
    ]


def test_request_id_is_generated_and_returned(app) -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    UUID(response.headers["X-Request-ID"])


def test_valid_request_id_is_correlated_without_sensitive_log_data(
    imported_app,
    viewer_headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="hcam.access")
    request_id = "trace.integration-test:42"
    with TestClient(imported_app) as client:
        response = client.get(
            "/cameras/synthetic:cctv-001?token=must-not-appear",
            headers={**viewer_headers, "X-Request-ID": request_id},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    event = _access_events(caplog)[-1]
    assert event["request_id"] == request_id
    assert event["route"] == "/cameras/{camera_id}"
    assert event["status_code"] == 200
    rendered = json.dumps(event)
    assert "synthetic:cctv-001" not in rendered
    assert "must-not-appear" not in rendered
    assert viewer_headers["X-HCAM-Actor"] not in rendered


def test_invalid_request_id_is_replaced(app, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="hcam.access")
    with TestClient(app) as client:
        response = client.get(
            "/health/live",
            headers={"X-Request-ID": "invalid request id"},
        )

    generated = response.headers["X-Request-ID"]
    UUID(generated)
    assert "invalid request id" not in json.dumps(_access_events(caplog))


def test_access_logging_can_be_disabled_without_losing_request_ids(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'no-access-log.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
        )
    )
    application.state.database.create_schema()
    caplog.set_level(logging.INFO, logger="hcam.access")
    try:
        with TestClient(application) as client:
            response = client.get("/health/live")
    finally:
        application.state.database.dispose()

    assert response.status_code == 200
    UUID(response.headers["X-Request-ID"])
    assert _access_events(caplog) == []


def test_unhandled_error_returns_correlated_generic_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = FastAPI()

    @application.get("/failure")
    def fail() -> None:
        raise RuntimeError("sensitive internal failure")

    application.add_middleware(RequestContextMiddleware)
    caplog.set_level(logging.ERROR, logger="hcam.error")
    with TestClient(application) as client:
        response = client.get("/failure", headers={"X-Request-ID": "trace.failure:1"})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "trace.failure:1"
    assert response.json() == {"detail": "Internal server error"}
    error_record = next(record for record in caplog.records if record.name == "hcam.error")
    error_event = json.loads(error_record.message)
    assert error_event == {
        "event": "http.request.failed",
        "exception_type": "RuntimeError",
        "method": "GET",
        "request_id": "trace.failure:1",
        "route": "/failure",
    }
    assert "sensitive internal failure" not in error_record.message


def test_request_id_scope_helper_is_fail_closed() -> None:
    assert request_id_from_scope({}) is None
    assert request_id_from_scope({"state": "invalid"}) is None
    assert request_id_from_scope({"state": {"request_id": 123}}) is None
    assert request_id_from_scope({"state": {"request_id": "trace-1"}}) == "trace-1"


def test_non_http_scope_passes_through_without_request_context() -> None:
    called = False

    async def downstream(scope, receive, send) -> None:
        nonlocal called
        called = True

    async def receive():
        return {"type": "websocket.disconnect"}

    async def send(_message) -> None:
        return None

    middleware = RequestContextMiddleware(downstream)
    asyncio.run(
        middleware(
            {"type": "websocket", "path": "/socket", "headers": []},
            receive,
            send,
        )
    )
    assert called is True


def test_exception_after_response_start_is_not_replaced() -> None:
    async def downstream(scope, receive, send) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        raise RuntimeError("response already started")

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_message) -> None:
        return None

    middleware = RequestContextMiddleware(downstream, access_log_enabled=False)
    with pytest.raises(RuntimeError, match="already started"):
        asyncio.run(
            middleware(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/started",
                    "headers": [],
                    "state": {},
                },
                receive,
                send,
            )
        )


def test_import_audit_event_contains_request_id(
    app,
    seed_file: Path,
    admin_headers: dict[str, str],
) -> None:
    request_id = "trace.import:001"
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    with TestClient(app) as client:
        response = client.post(
            "/camera-imports",
            json=payload,
            headers={**admin_headers, "X-Request-ID": request_id},
        )

    assert response.status_code == 200
    with app.state.database.session_factory() as session:
        event = session.scalar(
            select(AuditEvent)
            .where(AuditEvent.action == "camera_registry.import")
            .order_by(AuditEvent.occurred_at.desc())
        )
    assert event is not None
    assert event.context["request_id"] == request_id


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("HCAM_DEV_AUTH_ENABLED", "enabled"),
        ("HCAM_CREATE_SCHEMA", "sometimes"),
        ("HCAM_ACCESS_LOG_ENABLED", "logging"),
    ],
)
def test_invalid_boolean_environment_values_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=name):
        Settings.from_environment()


def test_environment_and_service_name_are_validated() -> None:
    with pytest.raises(ValueError, match="HCAM_ENVIRONMENT"):
        Settings(environment="staging")
    with pytest.raises(ValueError, match="HCAM_SERVICE_NAME"):
        Settings(service_name="  ")
