from __future__ import annotations

from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

from hcam.streams import onvif
from hcam.streams.onvif import OnvifResolutionError, OnvifStreamResolver
from hcam.streams.onvif_simulator import handler_for, main


def test_controlled_onvif_simulator_resolves_stream_uri() -> None:
    expected = "rtsp://127.0.0.1:8554/synthetic-01"
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(expected))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        actual = OnvifStreamResolver(timeout_seconds=2).resolve(
            f"http://{host}:{port}/onvif/media_service"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert actual == expected


def test_onvif_resolver_rejects_non_stream_response() -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), handler_for("http://127.0.0.1/not-rtsp")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with pytest.raises(OnvifResolutionError, match="onvif_invalid_stream_uri"):
            OnvifStreamResolver(timeout_seconds=2).resolve(
                f"http://{host}:{port}/onvif/media_service"
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_simulator_requires_explicit_non_loopback_opt_in() -> None:
    with pytest.raises(SystemExit, match="allow-non-loopback"):
        main(["--bind", "0.0.0.0"])


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.payload


@pytest.mark.parametrize(
    ("exception", "reason"),
    [
        (HTTPError("http://camera", 401, "denied", {}, None), "unauthorized"),
        (HTTPError("http://camera", 500, "error", {}, None), "onvif_http_error"),
        (URLError("offline"), "unreachable"),
    ],
)
def test_onvif_resolver_normalizes_transport_failures(
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    reason: str,
) -> None:
    def fail(*_args, **_kwargs):
        raise exception

    monkeypatch.setattr(onvif, "urlopen", fail)
    with pytest.raises(OnvifResolutionError) as error:
        OnvifStreamResolver().resolve("http://camera/onvif/media_service")
    assert error.value.reason_code == reason


@pytest.mark.parametrize(
    ("payload", "max_bytes", "reason"),
    [
        (b"x" * 10, 2, "onvif_response_too_large"),
        (b"<not-closed", 256, "onvif_invalid_response"),
        (
            b"<Envelope><Uri>rtsp://operator:secret@camera/live</Uri></Envelope>",
            256,
            "onvif_invalid_stream_uri",
        ),
        (b"<Envelope><MediaUri /></Envelope>", 256, "onvif_invalid_stream_uri"),
    ],
)
def test_onvif_resolver_rejects_bounded_or_unsafe_payloads(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    max_bytes: int,
    reason: str,
) -> None:
    monkeypatch.setattr(onvif, "urlopen", lambda *_args, **_kwargs: _Response(payload))
    with pytest.raises(OnvifResolutionError) as error:
        OnvifStreamResolver(max_response_bytes=max_bytes).resolve(
            "http://camera/onvif/media_service"
        )
    assert error.value.reason_code == reason


def test_simulator_handler_rejects_wrong_path_and_invalid_body() -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), handler_for("rtsp://127.0.0.1:8554/live")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        for path, body, expected in (
            ("/wrong", b"x", 404),
            ("/onvif/media_service", b"", 400),
        ):
            request = Request(f"http://{host}:{port}{path}", data=body, method="POST")
            with pytest.raises(HTTPError) as error:
                urlopen(request, timeout=2)
            assert error.value.code == expected
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_simulator_handler_rejects_invalid_content_length() -> None:
    handler = handler_for("rtsp://127.0.0.1:8554/live")
    instance = object.__new__(handler)
    instance.headers = {"Content-Length": "invalid"}
    instance.path = "/onvif/media_service"
    errors: list[int] = []
    instance.send_error = lambda code: errors.append(code)

    instance.do_POST()

    assert errors == [400]


def test_simulator_main_validates_arguments_and_closes_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(SystemExit, match="credential-free"):
        main(["--stream-uri", "rtsp://user:secret@camera/live"])
    with pytest.raises(SystemExit, match="between 1 and 65535"):
        main(["--port", "0"])

    class ServerStub:
        closed = False

        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            self.closed = True

    server = ServerStub()
    monkeypatch.setattr(
        "hcam.streams.onvif_simulator.ThreadingHTTPServer",
        lambda *_args, **_kwargs: server,
    )
    assert main(["--port", "8082"]) == 0
    assert server.closed is True
