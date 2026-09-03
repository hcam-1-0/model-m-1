from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from threading import Event
from time import perf_counter

import pytest

from hcam.streams import probe as probe_module
from hcam.streams.network import (
    StreamNetworkPolicy,
    StreamNetworkPolicyError,
    parse_allowed_hosts,
)
from hcam.streams.models import StreamEndpoint
from hcam.streams.onvif import OnvifResolutionError
from hcam.streams.probe import (
    FfprobeRunner,
    ProbeResult,
    ProbeToolError,
    StreamProbeAdapter,
    _frame_rate,
    _drain_bounded_pipe,
    _media_summary,
    _positive_integer,
    _run_bounded_process,
    _terminate_process,
)


def _completed(
    *,
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def test_ffprobe_runner_extracts_bounded_video_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "profile": "High",
                "width": 1280,
                "height": 720,
                "avg_frame_rate": "25/1",
            }
        ],
        "format": {"format_name": "rtsp"},
    }
    captured: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        captured.append(command)
        assert "shell" not in kwargs
        assert kwargs["stdin"] is subprocess.DEVNULL
        return _completed(stdout=json.dumps(payload).encode())

    monkeypatch.setattr(probe_module, "_run_bounded_process", fake_run)
    result = FfprobeRunner(timeout_seconds=3).probe(
        "rtsp://127.0.0.1:8554/cam-01",
        protocol="rtsp",
        transport="tcp",
    )

    assert result.succeeded
    assert result.media == {
        "codec": "h264",
        "profile": "High",
        "container": "rtsp",
        "width": 1280,
        "height": 720,
        "frame_rate": 25.0,
    }
    assert "-rtsp_transport" in captured[0]
    assert captured[0][-1] == "rtsp://127.0.0.1:8554/cam-01"


@pytest.mark.parametrize(
    ("stderr", "reason"),
    [
        (b"401 Unauthorized", "unauthorized"),
        (b"Connection refused", "unreachable"),
        (b"Invalid data found", "misconfigured"),
        (b"Protocol not found", "unsupported"),
        (b"opaque failure", "probe_failed"),
    ],
)
def test_ffprobe_runner_classifies_failures_without_returning_stderr(
    monkeypatch: pytest.MonkeyPatch,
    stderr: bytes,
    reason: str,
) -> None:
    monkeypatch.setattr(
        probe_module,
        "_run_bounded_process",
        lambda *_args, **_kwargs: _completed(returncode=1, stderr=stderr),
    )

    result = FfprobeRunner().probe(
        "http://127.0.0.1/video.m3u8", protocol="hls", transport="tcp"
    )

    assert result.outcome == "failure"
    assert result.reason_code == reason
    assert not result.media


def test_ffprobe_runner_treats_missing_binary_as_runtime_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(probe_module, "_run_bounded_process", missing)
    with pytest.raises(ProbeToolError, match="unavailable"):
        FfprobeRunner(executable="missing-ffprobe").probe(
            "http://127.0.0.1/video.m3u8", protocol="hls", transport="tcp"
        )


@pytest.mark.parametrize("stream_name", ["stdout", "stderr"])
def test_bounded_process_terminates_during_output_flood(stream_name: str) -> None:
    script = (
        "import sys,time; "
        f"stream=sys.{stream_name}.buffer; "
        "stream.write(b'x' * (2 * 1024 * 1024)); stream.flush(); time.sleep(10)"
    )
    started = perf_counter()

    with pytest.raises(ProbeToolError, match="safety limit"):
        _run_bounded_process(
            [sys.executable, "-c", script],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=8,
            check=False,
        )

    assert perf_counter() - started < 5


def test_bounded_process_rejects_unbounded_output() -> None:
    arguments = {
        "stdin": subprocess.DEVNULL,
        "timeout": 1,
        "check": False,
    }
    with pytest.raises(ValueError, match="captured output"):
        _run_bounded_process(
            [sys.executable, "-c", "pass"],
            capture_output=False,
            **arguments,
        )


def test_bounded_process_kills_and_reaps_on_timeout() -> None:
    started = perf_counter()
    with pytest.raises(subprocess.TimeoutExpired):
        _run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=0.05,
            check=False,
        )
    assert perf_counter() - started < 3


def test_bounded_process_preserves_output_and_check_semantics() -> None:
    completed = _run_bounded_process(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('out'); sys.stderr.write('err')",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=2,
        check=False,
    )
    assert completed.stdout == b"out"
    assert completed.stderr == b"err"

    with pytest.raises(subprocess.CalledProcessError):
        _run_bounded_process(
            [sys.executable, "-c", "raise SystemExit(7)"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=2,
            check=True,
        )


def test_bounded_pipe_reader_normalizes_read_failure_and_stopped_process() -> None:
    class ProcessStub:
        def __init__(self, returncode: int | None) -> None:
            self.returncode = returncode
            self.killed = False

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            self.killed = True
            self.returncode = -1

    class BrokenPipe:
        def read(self, _size: int) -> bytes:
            raise OSError("pipe failed")

    stopped = ProcessStub(0)
    _terminate_process(stopped)  # type: ignore[arg-type]
    assert stopped.killed is False

    running = ProcessStub(None)
    errors: list[OSError] = []
    _drain_bounded_pipe(
        BrokenPipe(),  # type: ignore[arg-type]
        [],
        process=running,  # type: ignore[arg-type]
        output_limit_exceeded=Event(),
        reader_errors=errors,
    )
    assert running.killed is True
    assert len(errors) == 1


def test_network_policy_defaults_to_loopback_and_supports_exact_allowlist() -> None:
    policy = StreamNetworkPolicy()
    policy.validate("rtsp://127.0.0.1/live")
    policy.validate("rtsp://[::1]/live")
    with pytest.raises(StreamNetworkPolicyError, match="explicitly allowlisted"):
        policy.validate("http://localhost/live/index.m3u8")
    with pytest.raises(StreamNetworkPolicyError, match="explicitly allowlisted"):
        policy.validate("rtsp://camera.internal/live")
    with pytest.raises(StreamNetworkPolicyError, match="outside"):
        policy.validate("rtsp://10.20.30.40/live")
    allowlisted = StreamNetworkPolicy(frozenset({"camera.internal", "localhost"}))
    allowlisted.validate("rtsp://camera.internal/live")
    allowlisted.validate("http://localhost/live/index.m3u8")


def test_network_policy_does_not_trust_dns_loopback_for_unlisted_hostnames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lookups: list[str] = []

    def fake_lookup(host: str, _port):
        lookups.append(host)
        return [(2, 1, 6, "", ("127.0.0.1", 0))]

    monkeypatch.setattr("socket.getaddrinfo", fake_lookup)
    with pytest.raises(StreamNetworkPolicyError, match="explicitly allowlisted"):
        StreamNetworkPolicy().validate("rtsp://rebinding.example/live")

    assert lookups == []


def test_network_allowlist_rejects_wildcards() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        parse_allowed_hosts("*")
    assert parse_allowed_hosts(" MediaMTX, onvif-sim ") == frozenset(
        {"mediamtx", "onvif-sim"}
    )


def test_ffprobe_can_inspect_a_small_local_synthetic_fixture(tmp_path: Path) -> None:
    ffmpeg = pytest.importorskip("shutil").which("ffmpeg")
    ffprobe = pytest.importorskip("shutil").which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for the local media smoke")
    fixture = tmp_path / "synthetic.mp4"
    generated = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=160x90:rate=5",
            "-t",
            "0.5",
            "-c:v",
            "mpeg4",
            "-y",
            str(fixture),
        ],
        capture_output=True,
        check=False,
        timeout=15,
    )
    if generated.returncode != 0:
        pytest.skip("local ffmpeg cannot generate the synthetic fixture")

    result = FfprobeRunner(executable=ffprobe, timeout_seconds=5).probe(
        str(fixture), protocol="http", transport="tcp"
    )

    assert result.succeeded
    assert result.media["width"] == 160
    assert result.media["height"] == 90


@pytest.mark.parametrize(
    ("protocol", "locator", "expected_fragment"),
    [
        ("rtsp", "rtsp://127.0.0.1:8554/live", "token=probe-token"),
        ("hls", "http://127.0.0.1/live.m3u8", "Authorization: Bearer probe-token"),
    ],
)
def test_ffprobe_runner_injects_ephemeral_access_token_only_at_execution(
    monkeypatch: pytest.MonkeyPatch,
    protocol: str,
    locator: str,
    expected_fragment: str,
) -> None:
    captured: list[str] = []
    payload = {
        "streams": [{"codec_type": "video", "codec_name": "h264"}],
        "format": {"format_name": protocol},
    }

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[bytes]:
        captured.extend(command)
        return _completed(stdout=json.dumps(payload).encode())

    monkeypatch.setattr(probe_module, "_run_bounded_process", fake_run)
    result = FfprobeRunner().probe(
        locator,
        protocol=protocol,
        transport="auto",
        access_token="probe-token",
    )

    assert result.succeeded
    assert expected_fragment in " ".join(captured)
    assert locator == locator.split("?", 1)[0]


def test_ffprobe_runner_handles_timeout_output_and_document_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timed_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("ffprobe", 1)

    monkeypatch.setattr(probe_module, "_run_bounded_process", timed_out)
    result = FfprobeRunner(timeout_seconds=0.01).probe(
        "http://127.0.0.1/live", protocol="http", transport="tcp"
    )
    assert result.reason_code == "timeout"

    monkeypatch.setattr(
        probe_module,
        "_run_bounded_process",
        lambda *_args, **_kwargs: _completed(stdout=b"x" * (1024 * 1024 + 1)),
    )
    with pytest.raises(ProbeToolError, match="safety limit"):
        FfprobeRunner().probe(
            "http://127.0.0.1/live", protocol="http", transport="tcp"
        )

    for payload in (b"not-json", b"[]"):
        monkeypatch.setattr(
            probe_module,
            "_run_bounded_process",
            lambda *_args, payload=payload, **_kwargs: _completed(stdout=payload),
        )
        with pytest.raises(ProbeToolError, match="invalid"):
            FfprobeRunner().probe(
                "http://127.0.0.1/live", protocol="http", transport="tcp"
            )

    monkeypatch.setattr(
        probe_module,
        "_run_bounded_process",
        lambda *_args, **_kwargs: _completed(stdout=b'{"streams": []}'),
    )
    unsupported = FfprobeRunner().probe(
        "http://127.0.0.1/live", protocol="http", transport="tcp"
    )
    assert unsupported.reason_code == "unsupported"


def test_media_summary_rejects_malformed_optional_metadata() -> None:
    assert _frame_rate(None) is None
    assert _frame_rate("0/0") is None
    assert _frame_rate("not-a-rate") is None
    assert _frame_rate("-1/1") is None
    assert _positive_integer(True) is None
    assert _positive_integer("bad") is None
    assert _positive_integer(0) is None
    assert _media_summary({"streams": "invalid", "format": "invalid"}) == {}
    assert _media_summary(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "x" * 100,
                    "width": "640",
                    "height": -1,
                    "r_frame_rate": "30000/1001",
                }
            ],
            "format": {"format_name": "f" * 100},
        }
    ) == {
        "codec": "x" * 80,
        "container": "f" * 80,
        "width": 640,
        "frame_rate": 29.97,
    }


class _RunnerStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str | None]] = []

    def probe(
        self,
        locator: str,
        *,
        protocol: str,
        transport: str,
        access_token: str | None = None,
    ) -> ProbeResult:
        self.calls.append((locator, protocol, transport, access_token))
        return ProbeResult("success", None, 1.0, {"codec": "h264"})


class _ResolverStub:
    def __init__(self, value: str | Exception) -> None:
        self.value = value

    def resolve(self, _locator: str) -> str:
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def _endpoint(**overrides: object) -> StreamEndpoint:
    values: dict[str, object] = {
        "stream_id": "str_" + "a" * 32,
        "camera_id": "camera-1",
        "name": "primary",
        "adapter_kind": "rtsp",
        "protocol": "rtsp",
        "locator": "rtsp://camera.internal/live",
        "secret_ref": None,
        "transport": "tcp",
        "is_primary": True,
        "enabled": True,
    }
    values.update(overrides)
    return StreamEndpoint(**values)


def test_stream_probe_adapter_enforces_credentials_network_and_onvif_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _RunnerStub()
    allowed = StreamNetworkPolicy(frozenset({"camera.internal", "resolved.internal"}))
    adapter = StreamProbeAdapter(
        runner=runner,  # type: ignore[arg-type]
        network_policy=allowed,
        access_token="ephemeral",
    )
    assert adapter.probe(_endpoint(secret_ref="vault/camera-1")).reason_code == (
        "credentials_unavailable"
    )

    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("10.1.2.3", 0))],
    )
    denied = StreamProbeAdapter(
        runner=runner,  # type: ignore[arg-type]
        network_policy=StreamNetworkPolicy(),
    ).probe(_endpoint(locator="rtsp://denied.internal/live"))
    assert denied.reason_code == "network_policy_denied"

    onvif = StreamProbeAdapter(
        runner=runner,  # type: ignore[arg-type]
        network_policy=allowed,
        onvif_resolver=_ResolverStub(  # type: ignore[arg-type]
            "rtsps://resolved.internal/live"
        ),
        access_token="ephemeral",
    )
    assert onvif.probe(
        _endpoint(
            adapter_kind="onvif",
            protocol="http",
            locator="http://camera.internal/onvif/media_service",
        )
    ).succeeded
    assert runner.calls[-1] == (
        "rtsps://resolved.internal/live",
        "rtsps",
        "tcp",
        "ephemeral",
    )

    failed_resolution = StreamProbeAdapter(
        runner=runner,  # type: ignore[arg-type]
        network_policy=allowed,
        onvif_resolver=_ResolverStub(  # type: ignore[arg-type]
            OnvifResolutionError("onvif_invalid_response")
        ),
    ).probe(
        _endpoint(
            adapter_kind="onvif",
            protocol="http",
            locator="http://camera.internal/onvif/media_service",
        )
    )
    assert failed_resolution.reason_code == "onvif_invalid_response"

    resolved_denied = StreamProbeAdapter(
        runner=runner,  # type: ignore[arg-type]
        network_policy=StreamNetworkPolicy(frozenset({"camera.internal"})),
        onvif_resolver=_ResolverStub(  # type: ignore[arg-type]
            "rtsp://resolved.internal/live"
        ),
    ).probe(
        _endpoint(
            adapter_kind="onvif",
            protocol="http",
            locator="http://camera.internal/onvif/media_service",
        )
    )
    assert resolved_denied.reason_code == "network_policy_denied"


def test_network_policy_rejects_missing_unlisted_and_empty_destinations() -> None:
    policy = StreamNetworkPolicy()
    with pytest.raises(StreamNetworkPolicyError, match="no host"):
        policy.validate("relative/path")

    with pytest.raises(StreamNetworkPolicyError, match="explicitly allowlisted"):
        policy.validate("rtsp://unresolvable.internal/live")
    assert parse_allowed_hosts(None) == frozenset()
