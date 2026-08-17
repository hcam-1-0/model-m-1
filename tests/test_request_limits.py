from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hcam.main import create_app
from hcam.security.request_limits import (
    REQUEST_TOO_LARGE_DETAIL,
    RequestBodyLimitMiddleware,
)
from hcam.settings import Settings


def _limited_app(tmp_path: Path):
    return create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'limited.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            max_request_body_bytes=128,
        )
    )


def test_content_length_request_limit_rejects_body_before_routing(
    tmp_path: Path,
    admin_headers: dict[str, str],
) -> None:
    app = _limited_app(tmp_path)
    with TestClient(app) as client:
        response = client.post(
            "/camera-imports",
            content=b"x" * 129,
            headers={**admin_headers, "Content-Type": "application/json"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": REQUEST_TOO_LARGE_DETAIL}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["connection"] == "close"


def test_asgi_chunked_request_limit_cannot_be_bypassed() -> None:
    request_messages = [
        {"type": "http.request", "body": b"x" * 64, "more_body": True},
        {"type": "http.request", "body": b"y" * 65, "more_body": False},
    ]
    response_messages = []

    async def receive():
        return request_messages.pop(0)

    async def send(message):
        response_messages.append(message)

    async def consume_body(_scope, app_receive, app_send):
        while True:
            message = await app_receive()
            if not message.get("more_body", False):
                break
        await app_send(
            {"type": "http.response.start", "status": 200, "headers": []}
        )
        await app_send({"type": "http.response.body", "body": b"ok"})

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/camera-imports",
        "raw_path": b"/camera-imports",
        "query_string": b"",
        "headers": [],
        "client": ("test", 1),
        "server": ("test", 80),
        "root_path": "",
    }
    middleware = RequestBodyLimitMiddleware(consume_body, max_bytes=128)
    asyncio.run(middleware(scope, receive, send))

    assert response_messages[0]["status"] == 413
    body = b"".join(
        message.get("body", b"")
        for message in response_messages
        if message["type"] == "http.response.body"
    )
    assert json.loads(body) == {"detail": REQUEST_TOO_LARGE_DETAIL}


def test_fastapi_chunked_request_returns_content_too_large(
    tmp_path: Path,
    admin_headers: dict[str, str],
) -> None:
    app = _limited_app(tmp_path)

    def chunks():
        yield b"x" * 64
        yield b"y" * 65

    with TestClient(app) as client:
        response = client.post(
            "/camera-imports",
            content=chunks(),
            headers={**admin_headers, "Content-Type": "application/json"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": REQUEST_TOO_LARGE_DETAIL}


def test_invalid_request_limit_environment_value_fails_fast(monkeypatch) -> None:
    monkeypatch.setenv("HCAM_MAX_REQUEST_BODY_BYTES", "not-an-integer")

    with pytest.raises(ValueError, match="HCAM_MAX_REQUEST_BODY_BYTES"):
        Settings.from_environment()
