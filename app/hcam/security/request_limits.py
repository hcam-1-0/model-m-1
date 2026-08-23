from __future__ import annotations

from collections import deque

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_TOO_LARGE_DETAIL = "Request body exceeds the configured limit"
SENSITIVE_PATH_PREFIXES = ("/cameras", "/camera-imports")


class RequestBodyLimitMiddleware:
    """Reject oversized HTTP bodies before or while the application reads them."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        if max_bytes < 1:
            raise ValueError("Request body limit must be positive")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = self._content_length(scope)
        if content_length is not None and content_length > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        received_bytes = 0
        buffered_messages: deque[Message] = deque()
        while True:
            message = await receive()
            buffered_messages.append(message)
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                break

        async def replay_receive() -> Message:
            if buffered_messages:
                return buffered_messages.popleft()
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    def _content_length(scope: Scope) -> int | None:
        for name, value in scope.get("headers", []):
            if name.lower() != b"content-length":
                continue
            try:
                parsed = int(value)
            except ValueError:
                return None
            return parsed if parsed >= 0 else None
        return None

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            {"detail": REQUEST_TOO_LARGE_DETAIL},
            status_code=413,
            headers={"Cache-Control": "no-store", "Connection": "close"},
        )
        await response(scope, receive, send)


class SensitiveResponseHeadersMiddleware:
    """Prevent registry responses from being retained or mixed by HTTP caches."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith(SENSITIVE_PATH_PREFIXES):
            await self.app(scope, receive, send)
            return

        async def protected_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["Pragma"] = "no-cache"
                headers["Vary"] = (
                    "Authorization, X-HCAM-Actor, X-HCAM-Roles, "
                    "X-HCAM-Departments"
                )
            await send(message)

        await self.app(scope, receive, protected_send)
