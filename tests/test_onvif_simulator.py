from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

from hcam.streams import onvif
from hcam.streams.onvif import (
    OnvifCapabilityDiscovery,
    OnvifResolutionError,
    OnvifStreamResolver,
)
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


def test_controlled_onvif_simulator_discovers_media_capabilities() -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), handler_for("rtsp://127.0.0.1:8554/synthetic-01")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        capabilities = OnvifCapabilityDiscovery(timeout_seconds=2).discover(
            f"http://{host}:{port}/onvif/media_service"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert capabilities.snapshot_uri is True
    assert capabilities.rotation is True
    assert capabilities.video_source_mode is False
    assert capabilities.osd is True
    assert capabilities.maximum_profiles == 8
    assert len(capabilities.profiles) == 2
    main_profile, sub_profile = capabilities.profiles
    assert (
        main_profile.token,
        main_profile.name,
        main_profile.video_encoding,
        main_profile.width,
        main_profile.height,
        main_profile.frame_rate_limit,
        main_profile.audio_encoding,
    ) == ("hcam-main", "Main", "H264", 1920, 1080, 25, "AAC")
    assert main_profile.ptz_configured is True
    assert main_profile.analytics_configured is True
    assert main_profile.metadata_configured is True
    assert sub_profile.video_encoding == "H265"
    assert sub_profile.audio_encoding is None
    assert sub_profile.ptz_configured is False


def test_capability_discovery_accepts_optional_and_attribute_forms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = iter(
        (
            b'<Envelope><Capabilities MaximumNumberOfProfiles="4" /></Envelope>',
            b'<Envelope><Profiles token="minimal" fixed="0" /></Envelope>',
        )
    )
    monkeypatch.setattr(
        onvif,
        "_open_request",
        lambda *_args, **_kwargs: _Response(next(payloads)),
    )

    capabilities = OnvifCapabilityDiscovery().discover(
        "http://camera/onvif/media_service"
    )

    assert capabilities.maximum_profiles == 4
    assert capabilities.snapshot_uri is None
    assert capabilities.profiles[0].fixed is False
    assert capabilities.profiles[0].video_encoding is None


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


def test_onvif_resolver_disables_proxies_and_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handlers: list[object] = []
    payload = b"<Envelope><Uri>rtsp://127.0.0.1:8554/live</Uri></Envelope>"

    class _Opener:
        def open(self, _request, *, timeout: float):
            assert timeout == 3
            return _Response(payload)

    def fake_build_opener(*configured_handlers):
        handlers.extend(configured_handlers)
        return _Opener()

    monkeypatch.setattr(onvif, "build_opener", fake_build_opener)
    assert OnvifStreamResolver(timeout_seconds=3).resolve(
        "http://camera/onvif/media_service"
    ) == "rtsp://127.0.0.1:8554/live"
    assert any(
        isinstance(handler, onvif.ProxyHandler) and handler.proxies == {}
        for handler in handlers
    )
    assert any(isinstance(handler, onvif._NoRedirectHandler) for handler in handlers)


def test_onvif_resolver_does_not_follow_redirects() -> None:
    class RedirectHandler(BaseHTTPRequestHandler):
        target_requests = 0

        def do_POST(self) -> None:
            self.send_response(302)
            self.send_header("Location", "/redirect-target")
            self.end_headers()

        def do_GET(self) -> None:
            type(self).target_requests += 1
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<Envelope><Uri>rtsp://127.0.0.1:8554/live</Uri></Envelope>"
            )

        def log_message(self, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        error: OnvifResolutionError | None = None
        for _attempt in range(3):
            with pytest.raises(OnvifResolutionError) as captured:
                OnvifStreamResolver(timeout_seconds=2).resolve(
                    f"http://{host}:{port}/onvif/media_service"
                )
            error = captured.value
            if error.reason_code != "unreachable":
                break
            sleep(0.05)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert error is not None
    assert error.reason_code == "onvif_redirect_denied"
    assert RedirectHandler.target_requests == 0


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

    monkeypatch.setattr(onvif, "_open_request", fail)
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
    monkeypatch.setattr(
        onvif, "_open_request", lambda *_args, **_kwargs: _Response(payload)
    )
    with pytest.raises(OnvifResolutionError) as error:
        OnvifStreamResolver(max_response_bytes=max_bytes).resolve(
            "http://camera/onvif/media_service"
        )
    assert error.value.reason_code == reason


@pytest.mark.parametrize(
    ("capability_payload", "profile_payload", "reason"),
    [
        (
            b"<Envelope />",
            b"<Envelope />",
            "onvif_invalid_capabilities",
        ),
        (
            b'<Envelope><Capabilities SnapshotUri="sometimes" /></Envelope>',
            b"<Envelope />",
            "onvif_invalid_capabilities",
        ),
        (
            b"<Envelope><Capabilities><MaximumNumberOfProfiles>many"
            b"</MaximumNumberOfProfiles></Capabilities></Envelope>",
            b"<Envelope />",
            "onvif_invalid_capabilities",
        ),
        (
            b"<Envelope><Capabilities><MaximumNumberOfProfiles>0"
            b"</MaximumNumberOfProfiles></Capabilities></Envelope>",
            b"<Envelope />",
            "onvif_invalid_capabilities",
        ),
        (
            b'<Envelope><Capabilities SnapshotUri="true" /></Envelope>',
            b"<Envelope>"
            + b'<Profiles token="profile" />' * 65
            + b"</Envelope>",
            "onvif_too_many_profiles",
        ),
        (
            b'<Envelope><Capabilities SnapshotUri="true" /></Envelope>',
            b'<Envelope><Profiles token="" /></Envelope>',
            "onvif_invalid_capabilities",
        ),
        (
            b'<Envelope><Capabilities SnapshotUri="true" /></Envelope>',
            b'<Envelope><Profiles token="profile"><Name>'
            + b"x" * 256
            + b"</Name></Profiles></Envelope>",
            "onvif_invalid_capabilities",
        ),
    ],
)
def test_capability_discovery_rejects_unbounded_or_invalid_documents(
    monkeypatch: pytest.MonkeyPatch,
    capability_payload: bytes,
    profile_payload: bytes,
    reason: str,
) -> None:
    payloads = iter((capability_payload, profile_payload))
    monkeypatch.setattr(
        onvif,
        "_open_request",
        lambda *_args, **_kwargs: _Response(next(payloads)),
    )

    with pytest.raises(OnvifResolutionError) as error:
        OnvifCapabilityDiscovery().discover("http://camera/onvif/media_service")

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
            ("/onvif/media_service", b"<Unknown />", 400),
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
