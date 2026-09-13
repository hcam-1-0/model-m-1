from __future__ import annotations

import json
import logging
import re
from typing import Protocol
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from hcam.operations.platform.tracing import TraceContextError, correlation_context, parse_trace_context


REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ACCESS_LOGGER = logging.getLogger("hcam.access")
_ERROR_LOGGER = logging.getLogger("hcam.error")


class MetricsRecorder(Protocol):
    def observe(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None: ...


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []):
        if name.lower() != b"x-request-id":
            continue
        try:
            candidate = value.decode("ascii").strip()
        except UnicodeDecodeError:
            return None
        return candidate if _REQUEST_ID_PATTERN.fullmatch(candidate) else None
    return None


def _incoming_ascii_header(scope: Scope, expected: bytes, *, maximum: int) -> str | None:
    for name, value in scope.get("headers", []):
        if name.lower() != expected:
            continue
        if len(value) > maximum:
            return None
        try:
            return value.decode("ascii").strip()
        except UnicodeDecodeError:
            return None
    return None


def request_id_from_scope(scope: Scope) -> str | None:
    state = scope.get("state")
    if not isinstance(state, dict):
        return None
    request_id = state.get("request_id")
    return request_id if isinstance(request_id, str) else None


class RequestContextMiddleware:
    """Attach a request ID and emit metadata-only structured access events."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        access_log_enabled: bool = True,
        metrics_recorder: MetricsRecorder | None = None,
    ) -> None:
        self.app = app
        self.access_log_enabled = access_log_enabled
        self.metrics_recorder = metrics_recorder

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or str(uuid4())
        correlation_id = _incoming_ascii_header(
            scope, b"x-correlation-id", maximum=128
        )
        if correlation_id is None or _REQUEST_ID_PATTERN.fullmatch(correlation_id) is None:
            correlation_id = request_id
        traceparent = _incoming_ascii_header(scope, b"traceparent", maximum=55)
        tracestate = _incoming_ascii_header(scope, b"tracestate", maximum=512)
        trace_context = None
        if traceparent is not None:
            try:
                trace_context = parse_trace_context(traceparent, tracestate)
            except TraceContextError:
                trace_context = None
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        state["correlation_context"] = correlation_context(correlation_id).model_dump(mode="json")
        state["trace_context"] = (
            trace_context.model_dump(mode="json") if trace_context is not None else None
        )
        started = perf_counter()
        response_status = 500
        response_started = False

        async def correlated_send(message: Message) -> None:
            nonlocal response_started, response_status
            if message["type"] == "http.response.start":
                response_started = True
                response_status = int(message["status"])
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
                MutableHeaders(scope=message)[CORRELATION_ID_HEADER] = correlation_id
            await send(message)

        try:
            await self.app(scope, receive, correlated_send)
        except Exception as exc:
            if response_started:
                raise
            route = scope.get("route")
            error_event = {
                "event": "http.request.failed",
                "exception_type": type(exc).__name__,
                "method": scope.get("method", "UNKNOWN"),
                "request_id": request_id,
                "route": getattr(route, "path", "<unmatched>"),
            }
            _ERROR_LOGGER.error(
                json.dumps(error_event, separators=(",", ":"), sort_keys=True)
            )
            response = JSONResponse(
                {"detail": "Internal server error"},
                status_code=500,
            )
            await response(scope, receive, correlated_send)
        finally:
            elapsed_seconds = perf_counter() - started
            route = scope.get("route")
            route_template = getattr(route, "path", "<unmatched>")
            if self.metrics_recorder is not None:
                self.metrics_recorder.observe(
                    method=scope.get("method", "UNKNOWN"),
                    route=route_template,
                    status_code=response_status,
                    duration_seconds=elapsed_seconds,
                )
            if self.access_log_enabled:
                event = {
                    "duration_ms": round(elapsed_seconds * 1000, 3),
                    "event": "http.request.completed",
                    "method": scope.get("method", "UNKNOWN"),
                    "request_id": request_id,
                    "route": route_template,
                    "status_code": response_status,
                }
                _ACCESS_LOGGER.info(json.dumps(event, separators=(",", ":"), sort_keys=True))
