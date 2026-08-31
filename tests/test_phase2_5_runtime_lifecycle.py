from __future__ import annotations

import asyncio
import json
import signal
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from hcam.labs.sentinel import fault_proxy, publisher
from hcam.labs.sentinel.accelerators import AcceleratorError
from hcam.labs.sentinel.faults import make_fault_request, write_fault_request
from hcam.labs.sentinel.fixtures import generated_media_profiles
from hcam.labs.sentinel.lab_adapters import (
    LAB1_HIGH_ADAPTER,
    LAB2_LOW_ADAPTER,
    write_active_lab_adapter,
)
from hcam.labs.sentinel.publisher import PublisherProcess
from hcam.labs.sentinel.timing import ConnectionEpochState


class FakeChild:
    def __init__(self, *_args, timeout_once: bool = False, **_kwargs) -> None:
        self.running = True
        self.killed = False
        self.timeout_once = timeout_once

    def poll(self) -> int | None:
        return None if self.running else 0

    def terminate(self) -> None:
        self.running = False

    def wait(self, timeout: float | None = None) -> int:
        if self.timeout_once:
            self.timeout_once = False
            raise subprocess.TimeoutExpired("generated-publisher", timeout)
        self.running = False
        return 0

    def kill(self) -> None:
        self.killed = True
        self.running = False


def make_publisher(number: int, *, running: bool = True) -> PublisherProcess:
    child = FakeChild()
    child.running = running
    return PublisherProcess(
        number=number,
        camera_id=f"C{number:02d}",
        command=["ffmpeg", str(number)],
        process=child,  # type: ignore[arg-type]
        epoch=ConnectionEpochState(f"C{number:02d}"),
    )


def test_publisher_command_is_stream_copy_and_process_shutdown_is_bounded(
    monkeypatch, tmp_path
) -> None:
    command = publisher.publisher_command(
        "ffmpeg", tmp_path / "fixture.mp4", "rtsp://mediamtx:8554/hcam/test"
    )
    assert command[command.index("-c:v") + 1] == "copy"
    assert "-stream_loop" in command
    assert "-rtsp_transport" in command

    children: list[FakeChild] = []

    def fake_popen(*args, **kwargs):
        child = FakeChild(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(publisher.subprocess, "Popen", fake_popen)
    started = publisher._start(1, command)
    assert started.camera_id == "C01"
    assert started.epoch.connection_epoch == 1
    publisher._stop(started)
    assert children[0].running is False

    timed_out = make_publisher(2)
    timed_out.process = FakeChild(timeout_once=True)  # type: ignore[assignment]
    publisher._stop(timed_out)
    assert timed_out.process.killed is True  # type: ignore[attr-defined]


def test_publisher_reconciliation_changes_concurrency_not_fixture_quality(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(publisher.subprocess, "Popen", FakeChild)
    profiles = generated_media_profiles(50, 30)
    processes: list[PublisherProcess] = []

    publisher.reconcile_publishers(
        processes,
        target_count=LAB1_HIGH_ADAPTER.active_stream_count,
        profiles=profiles,
        ffmpeg="ffmpeg",
        fixture_dir=tmp_path,
        base_url="rtsp://mediamtx:8554/hcam/",
    )
    assert len(processes) == 30
    assert all(
        item.command[item.command.index("-c:v") + 1] == "copy" for item in processes
    )

    publisher.reconcile_publishers(
        processes,
        target_count=LAB2_LOW_ADAPTER.active_stream_count,
        profiles=profiles,
        ffmpeg="ffmpeg",
        fixture_dir=tmp_path,
        base_url="rtsp://mediamtx:8554/hcam/",
    )
    assert [item.camera_id for item in processes] == ["C01", "C02", "C03", "C04"]

    publisher.reconcile_publishers(
        processes,
        target_count=LAB1_HIGH_ADAPTER.active_stream_count,
        profiles=profiles,
        ffmpeg="ffmpeg",
        fixture_dir=tmp_path,
        base_url="rtsp://mediamtx:8554/hcam/",
    )
    assert len(processes) == 30
    assert publisher.publisher_state_document(LAB1_HIGH_ADAPTER, processes) == {
        "classification": "generated-only",
        "adapter_id": "lab1highadapter",
        "active_stream_count": 30,
        "active_camera_ids": [f"C{number:02d}" for number in range(1, 31)],
        "stream_copy": True,
        "quality_downgraded": False,
    }
    with pytest.raises(ValueError, match="outside generated profile capacity"):
        publisher.reconcile_publishers(
            processes,
            target_count=0,
            profiles=profiles,
            ffmpeg="ffmpeg",
            fixture_dir=tmp_path,
            base_url="rtsp://mediamtx:8554/hcam/",
        )


def test_publisher_main_tracks_high_to_low_switch_and_explicit_cleanup(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(
        publisher,
        "discover_acceleration",
        lambda *_args, **_kwargs: SimpleNamespace(ffmpeg="ffmpeg"),
    )
    monkeypatch.setattr(publisher, "prepare_media_fixtures", lambda *_a, **_k: {})
    monkeypatch.setattr(publisher.subprocess, "Popen", FakeChild)
    removed: list[Path] = []
    monkeypatch.setattr(publisher, "remove_media_fixtures", removed.append)

    handlers = {}
    monkeypatch.setattr(
        publisher.signal,
        "signal",
        lambda signum, callback: handlers.__setitem__(signum, callback),
    )
    adapter_state = tmp_path / "active-lab-adapter.json"
    publisher_state = tmp_path / "publisher-state.json"
    heartbeat = tmp_path / "heartbeat"
    cleanup = tmp_path / "cleanup-request.json"
    cleanup.write_text(
        '{"classification":"generated-only","cleanup":true}', encoding="ascii"
    )
    observed_states: list[dict[str, object]] = []
    real_atomic_write = publisher.atomic_write_json

    def record_state(path: Path, document: dict[str, object]) -> None:
        if path == publisher_state:
            observed_states.append(document)
        real_atomic_write(path, document)

    monkeypatch.setattr(publisher, "atomic_write_json", record_state)
    sleep_count = 0

    def advance(_seconds: float) -> None:
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count == 1:
            write_active_lab_adapter(adapter_state, LAB2_LOW_ADAPTER.adapter_id)
        else:
            handlers[signal.SIGTERM]()

    monkeypatch.setattr(publisher, "sleep", advance)
    result = publisher.main(
        [
            "--capacity",
            "50",
            "--active-count",
            "30",
            "--fixture-dir",
            str(tmp_path / "fixtures"),
            "--adapter-state-path",
            str(adapter_state),
            "--publisher-state-path",
            str(publisher_state),
            "--heartbeat-file",
            str(heartbeat),
            "--cleanup-request-path",
            str(cleanup),
            "--cleanup-fixtures",
        ]
    )

    assert result == 0
    assert [
        (item["adapter_id"], item["active_stream_count"]) for item in observed_states
    ] == [
        ("lab1highadapter", 30),
        ("lab2lowadapter", 4),
    ]
    assert all(item["stream_copy"] is True for item in observed_states)
    assert all(item["quality_downgraded"] is False for item in observed_states)
    assert removed == [tmp_path / "fixtures"]
    assert not heartbeat.exists()
    assert not publisher_state.exists()


@pytest.mark.parametrize(
    ("environment", "arguments", "expected"),
    [
        (None, [], 2),
        ("true", ["--active-count", "0"], 2),
        ("true", ["--parallelism", "9"], 2),
    ],
)
def test_publisher_main_rejects_unsafe_startup(
    monkeypatch, environment, arguments, expected
) -> None:
    if environment is None:
        monkeypatch.delenv("HCAM_ALLOW_SYNTHETIC_LAB", raising=False)
    else:
        monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", environment)
    assert publisher.main(arguments) == expected


def test_publisher_main_reports_preparation_and_adapter_state_failures(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(
        publisher,
        "discover_acceleration",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AcceleratorError("no_encoder")),
    )
    assert publisher.main([]) == 1

    monkeypatch.setattr(
        publisher,
        "discover_acceleration",
        lambda *_args, **_kwargs: SimpleNamespace(ffmpeg="ffmpeg"),
    )
    monkeypatch.setattr(publisher, "prepare_media_fixtures", lambda *_a, **_k: {})
    state = tmp_path / "adapter-state.json"
    state.write_text("not-json", encoding="ascii")
    assert publisher.main(["--adapter-state-path", str(state)]) == 1


def test_publisher_fault_scenarios_cover_disconnect_and_epoch_paths(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(
        publisher,
        "analyze_fixture_timing",
        lambda _path: {"monotonic": True, "retained_frames": 0},
    )
    profiles = {profile.camera_id: profile for profile in generated_media_profiles()}
    for scenario in ("F1", "F2", "F3", "F4", "F5", "F7"):
        request = make_fault_request(scenario, now=100, duration_seconds=10)
        item = make_publisher(int(request.camera_id[1:]))
        evidence = publisher.apply_fault(
            request,
            [item],
            fixture_dir=tmp_path,
            profiles_by_camera=profiles,
        )
        assert evidence["classification"] == "generated-only"
        assert evidence["zero_retained_media"] is True
        if scenario in {"F2", "F4", "F5", "F7"}:
            assert item.process.poll() == 0
    with pytest.raises(Exception, match="fault_camera_not_active"):
        publisher.apply_fault(
            make_fault_request("F6", now=100),
            [],
            fixture_dir=tmp_path,
            profiles_by_camera=profiles,
        )


def configure_fake_publisher_runtime(monkeypatch) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(
        publisher,
        "discover_acceleration",
        lambda *_args, **_kwargs: SimpleNamespace(ffmpeg="ffmpeg"),
    )
    monkeypatch.setattr(publisher, "prepare_media_fixtures", lambda *_a, **_k: {})
    monkeypatch.setattr(publisher.subprocess, "Popen", FakeChild)
    handlers = {}
    monkeypatch.setattr(
        publisher.signal,
        "signal",
        lambda signum, callback: handlers.__setitem__(signum, callback),
    )
    monkeypatch.setattr(publisher, "_test_signal_handlers", handlers, raising=False)


def test_publisher_main_records_active_and_expired_fault(monkeypatch, tmp_path) -> None:
    configure_fake_publisher_runtime(monkeypatch)
    fault_request = tmp_path / "fault-request.json"
    fault_status = tmp_path / "fault-status.json"
    write_fault_request(
        fault_request,
        make_fault_request("F6", now=100, duration_seconds=1),
    )
    epochs = iter((100.5, 102.0))
    monkeypatch.setattr(publisher, "time", lambda: next(epochs))
    statuses: list[dict[str, object]] = []
    real_atomic_write = publisher.atomic_write_json

    def record_status(path: Path, document: dict[str, object]) -> None:
        if path == fault_status:
            statuses.append(document)
        real_atomic_write(path, document)

    monkeypatch.setattr(publisher, "atomic_write_json", record_status)
    sleeps = 0

    def advance(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 2:
            publisher._test_signal_handlers[signal.SIGTERM]()

    monkeypatch.setattr(publisher, "sleep", advance)

    assert (
        publisher.main(
            [
                "--active-count",
                "4",
                "--capacity",
                "4",
                "--fixture-dir",
                str(tmp_path / "fixtures"),
                "--fault-request-path",
                str(fault_request),
                "--fault-status-path",
                str(fault_status),
            ]
        )
        == 0
    )
    assert [status["status"] for status in statuses] == ["applied", "expired"]
    assert statuses[0]["inference_transport"] == "blocked-by-private-proxy"
    assert statuses[1]["active_fault"] is False


def test_publisher_main_restarts_one_failed_stream_with_bounded_backoff(
    monkeypatch, tmp_path
) -> None:
    configure_fake_publisher_runtime(monkeypatch)
    clocks = iter((0.0, 1.0, 10.0))
    monkeypatch.setattr(publisher, "monotonic", lambda: next(clocks))
    observed_children: list[FakeChild] = []

    def fake_popen(*args, **kwargs):
        child = FakeChild(*args, **kwargs)
        observed_children.append(child)
        return child

    monkeypatch.setattr(publisher.subprocess, "Popen", fake_popen)
    sleeps = 0

    def advance(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 1:
            observed_children[0].running = False
        elif sleeps == 3:
            publisher._test_signal_handlers[signal.SIGTERM]()

    monkeypatch.setattr(publisher, "sleep", advance)
    assert (
        publisher.main(
            [
                "--active-count",
                "1",
                "--capacity",
                "1",
                "--fixture-dir",
                str(tmp_path / "fixtures"),
            ]
        )
        == 0
    )
    assert len(observed_children) == 2


def test_publisher_main_fails_after_bounded_restart_budget(
    monkeypatch, tmp_path
) -> None:
    configure_fake_publisher_runtime(monkeypatch)

    def exhausted_start(number, command, epoch=None):
        item = make_publisher(number, running=False)
        item.command = command
        item.epoch = epoch or item.epoch
        item.restarts = 3
        return item

    monkeypatch.setattr(publisher, "_start", exhausted_start)
    assert (
        publisher.main(
            [
                "--active-count",
                "1",
                "--capacity",
                "1",
                "--fixture-dir",
                str(tmp_path / "fixtures"),
            ]
        )
        == 1
    )


def test_publisher_main_rejects_live_adapter_and_fault_state_corruption(
    monkeypatch, tmp_path
) -> None:
    configure_fake_publisher_runtime(monkeypatch)
    adapter_state = tmp_path / "adapter-state.json"
    fault_request = tmp_path / "fault-request.json"
    adapter_state.write_text(
        json.dumps(
            {
                "schema": "hcam.phase2_5.lab_adapter_state.v1",
                "classification": "generated-only",
                "adapter_id": "lab2lowadapter",
            }
        ),
        encoding="ascii",
    )
    fault_request.write_text("not-json", encoding="ascii")
    statuses: list[dict[str, object]] = []
    real_atomic_write = publisher.atomic_write_json
    fault_status = tmp_path / "fault-status.json"

    def record_status(path: Path, document: dict[str, object]) -> None:
        if path == fault_status:
            statuses.append(document)
        real_atomic_write(path, document)

    monkeypatch.setattr(publisher, "atomic_write_json", record_status)

    def corrupt_adapter(_seconds: float) -> None:
        adapter_state.write_text("not-json", encoding="ascii")

    monkeypatch.setattr(publisher, "sleep", corrupt_adapter)
    assert (
        publisher.main(
            [
                "--capacity",
                "50",
                "--active-count",
                "30",
                "--fixture-dir",
                str(tmp_path / "fixtures"),
                "--adapter-state-path",
                str(adapter_state),
                "--fault-request-path",
                str(fault_request),
                "--fault-status-path",
                str(fault_status),
            ]
        )
        == 1
    )
    assert statuses == [
        {
            "classification": "generated-only",
            "status": "rejected",
            "safe_reason": "fault_request_invalid",
        }
    ]


class FakeReader:
    def __init__(
        self, chunks: list[bytes] | None = None, *, fail: bool = False
    ) -> None:
        self.chunks = list(chunks or [])
        self.fail = fail

    async def read(self, _size: int) -> bytes:
        if self.fail:
            raise ConnectionError("generated reader disconnected")
        return self.chunks.pop(0) if self.chunks else b""


class FakeWriter:
    def __init__(self, *, fail_wait: bool = False) -> None:
        self.data = bytearray()
        self.closed = False
        self.fail_wait = fail_wait

    def write(self, data: bytes) -> None:
        self.data.extend(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        if self.fail_wait:
            raise ConnectionError("generated writer already closed")


class FakeServer:
    def __init__(self, handler, pairs) -> None:
        self.handler = handler
        self.pairs = pairs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def serve_forever(self) -> None:
        for reader, writer in self.pairs:
            await self.handler(reader, writer)


def test_fault_proxy_copy_and_safety_gates(monkeypatch, tmp_path) -> None:
    writer = FakeWriter(fail_wait=True)
    asyncio.run(fault_proxy._copy(FakeReader([b"generated"]), writer))
    assert bytes(writer.data) == b"generated"
    assert writer.closed is True
    asyncio.run(fault_proxy._copy(FakeReader(fail=True), FakeWriter()))

    monkeypatch.delenv("HCAM_ALLOW_SYNTHETIC_LAB", raising=False)
    with pytest.raises(RuntimeError, match="HCAM_ALLOW_SYNTHETIC_LAB"):
        asyncio.run(
            fault_proxy.run_proxy(
                bind="127.0.0.1",
                port=8555,
                upstream_host="mediamtx",
                upstream_port=8554,
                request_path=tmp_path / "request.json",
                status_path=tmp_path / "status.json",
            )
        )
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    with pytest.raises(RuntimeError, match="exact generated-lab upstream"):
        asyncio.run(
            fault_proxy.run_proxy(
                bind="127.0.0.1",
                port=8555,
                upstream_host="external.invalid",
                upstream_port=8554,
                request_path=tmp_path / "request.json",
                status_path=tmp_path / "status.json",
            )
        )


@pytest.mark.parametrize("mode", ["blocked", "unavailable", "forwarded"])
def test_fault_proxy_generated_paths(monkeypatch, tmp_path, mode) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    request_path = tmp_path / f"{mode}-request.json"
    status_path = tmp_path / f"{mode}-status.json"
    client_writer = FakeWriter()
    pairs = [(FakeReader([b"client"]), client_writer)]
    monkeypatch.setattr(
        fault_proxy.asyncio,
        "start_server",
        lambda handler, _bind, _port: asyncio.sleep(
            0, result=FakeServer(handler, pairs)
        ),
    )
    upstream_writer = FakeWriter()
    if mode == "blocked":
        write_fault_request(
            request_path,
            make_fault_request("F6", now=100, duration_seconds=30),
        )
        monkeypatch.setattr(fault_proxy, "fault_is_active", lambda _path: (True, "f6"))
    else:
        monkeypatch.setattr(fault_proxy, "fault_is_active", lambda _path: (False, None))

        async def open_connection(_host, _port):
            if mode == "unavailable":
                raise OSError("generated upstream unavailable")
            return FakeReader([b"upstream"]), upstream_writer

        monkeypatch.setattr(fault_proxy.asyncio, "open_connection", open_connection)

    asyncio.run(
        fault_proxy.run_proxy(
            bind="127.0.0.1",
            port=8555,
            upstream_host="mediamtx",
            upstream_port=8554,
            request_path=request_path,
            status_path=status_path,
        )
    )
    status = json.loads(status_path.read_text(encoding="ascii"))
    assert status["classification"] == "generated-only"
    assert client_writer.closed is True
    if mode == "forwarded":
        assert bytes(client_writer.data) == b"upstream"
        assert bytes(upstream_writer.data) == b"client"


def test_fault_proxy_main_validates_bind_port_and_keyboard_interrupt(
    monkeypatch, tmp_path
) -> None:
    required = [
        "--request-path",
        str(tmp_path / "request.json"),
        "--status-path",
        str(tmp_path / "status.json"),
    ]
    assert fault_proxy.main(["--bind", "0.0.0.0", *required]) == 2
    assert fault_proxy.main(["--port", "0", *required]) == 2

    def complete_without_server(coroutine) -> None:
        coroutine.close()

    monkeypatch.setattr(fault_proxy.asyncio, "run", complete_without_server)
    assert fault_proxy.main(required) == 0

    def interrupted(coroutine) -> None:
        coroutine.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(fault_proxy.asyncio, "run", interrupted)
    assert fault_proxy.main(required) == 0
