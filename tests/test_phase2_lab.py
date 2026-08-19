from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import func, select

from hcam.camera_registry.models import Camera
from hcam.streams import lab_publisher
from hcam.streams.lab import SyntheticLabError, seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEndpoint
from tools import phase2_lab
from tools.phase2_lab import prepare


def test_synthetic_lab_seed_is_bounded_idempotent_and_onvif_aware(app) -> None:
    with app.state.database.session_factory() as session:
        first = seed_synthetic_lab(session, count=50)
    with app.state.database.session_factory() as session:
        second = seed_synthetic_lab(session, count=50)
        total = session.scalar(select(func.count()).select_from(StreamEndpoint))
        onvif = session.scalar(
            select(StreamEndpoint).where(StreamEndpoint.adapter_kind == "onvif")
        )

    assert first["created_cameras"] == 50
    assert first["created_streams"] == 50
    assert second["created_cameras"] == 0
    assert second["created_streams"] == 0
    assert total == 50
    assert onvif is not None
    assert onvif.stream_id == synthetic_stream_id(1)
    assert onvif.locator == "http://onvif-simulator:8081/onvif/media_service"


def test_phase2_lab_secret_preparation_does_not_return_secret_values(
    tmp_path: Path,
) -> None:
    secret_root = tmp_path / "phase2-secrets"

    report = prepare(secret_root)

    assert report["files"] == 5
    assert report["contains_government_data"] is False
    assert report["contains_real_video"] is False
    assert "PRIVATE KEY" not in repr(report)
    key = (secret_root / "playback-signing-key.pem").read_text(encoding="ascii")
    assert "BEGIN PRIVATE KEY" in key
    assert len((secret_root / "metrics-token").read_text(encoding="ascii")) >= 32
    assert phase2_lab.load_metrics_token(secret_root) == (
        secret_root / "metrics-token"
    ).read_text(encoding="ascii")
    if os.name == "posix":
        assert secret_root.stat().st_mode & 0o777 == 0o700
        assert all(
            path.stat().st_mode & 0o777 == 0o644 for path in secret_root.iterdir()
        )
        key_path = secret_root / "playback-signing-key.pem"
        key_path.chmod(0o600)
        prepare(secret_root)
        assert key_path.stat().st_mode & 0o777 == 0o644


def test_metrics_token_loader_rejects_missing_or_empty_secret(tmp_path: Path) -> None:
    secret_root = tmp_path / "missing-secrets"
    with pytest.raises(phase2_lab.LabError, match="unavailable"):
        phase2_lab.load_metrics_token(secret_root)

    secret_root.mkdir()
    (secret_root / "metrics-token").write_text("", encoding="ascii")
    with pytest.raises(phase2_lab.LabError, match="empty"):
        phase2_lab.load_metrics_token(secret_root)


def test_phase2_compose_keeps_media_ports_local_and_recording_disabled() -> None:
    root = Path(__file__).resolve().parents[1]
    compose = (root / "deploy" / "compose.phase2.yaml").read_text(encoding="utf-8")
    mediamtx = (root / "deploy" / "mediamtx.phase2.yml").read_text(
        encoding="utf-8"
    )

    assert "127.0.0.1:${HCAM_HLS_PORT:-8888}:8888" in compose
    assert "image: hcam-core:phase2-lab" in compose
    assert ":8554:8554" not in compose
    assert "sha256:e8eda6a884bbb2eaebf0c0454200ddc8087f428e091bae10d20e330a08558778" in compose
    assert "record: false" in mediamtx
    assert "authMethod: jwt" in mediamtx
    assert "authJWTIssuer: hcam-core" in mediamtx
    assert "moq: false" in mediamtx
    assert "live.sentinelgujarat.in" not in compose + mediamtx
    assert compose.count("HCAM_STREAM_PROBE_ALLOWED_HOSTS:") == 2
    assert "HCAM_STREAM_PROBE_ALLOWED_HOSTS: onvif-simulator" in compose


def test_failure_drill_requires_full_fleet_recovery() -> None:
    root = Path(__file__).resolve().parents[1]
    drill = (root / "tools" / "phase2_failure_drill.py").read_text(
        encoding="utf-8"
    )

    assert "def _recover_fleet" in drill
    assert "fleet_recovered" in drill
    assert "verify_metrics" in drill
    assert "len(items) != 50" in drill
    assert 'get("state") != "healthy"' in drill
    assert '"stop", "onvif-simulator"' in drill
    assert '"stop", "publisher"' not in drill


def test_lab_launcher_builds_the_shared_image_once() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "tools" / "phase2_lab.py").read_text(encoding="utf-8")

    assert launcher.count('"build", "api"') == 2
    assert launcher.count('"--no-build"') == 2
    assert '"up",\n                "--build"' not in launcher


def test_playback_verification_retries_only_transient_health_conflict(
    monkeypatch,
) -> None:
    attempts: list[str] = []

    def request(url: str, **_kwargs) -> dict[str, object]:
        attempts.append(url)
        if len(attempts) == 1:
            raise phase2_lab.LabHttpError(409)
        return {"session_id": "pbs_test"}

    monkeypatch.setattr(phase2_lab, "_json_request", request)
    monkeypatch.setattr(phase2_lab, "sleep", lambda _seconds: None)

    result = phase2_lab._create_playback_session(
        "http://127.0.0.1:8000",
        "str_test",
        {},
    )

    assert result == {"session_id": "pbs_test"}
    assert len(attempts) == 2


def test_playback_verification_does_not_retry_non_conflict(monkeypatch) -> None:
    monkeypatch.setattr(
        phase2_lab,
        "_json_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(phase2_lab.LabHttpError(503)),
    )

    with pytest.raises(phase2_lab.LabHttpError) as error:
        phase2_lab._create_playback_session(
            "http://127.0.0.1:8000",
            "str_test",
            {},
        )

    assert error.value.status_code == 503


def test_synthetic_lab_rejects_bounds_and_identifier_collisions(app) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        synthetic_stream_id(0)
    with app.state.database.session_factory() as session:
        with pytest.raises(SyntheticLabError, match="between 1 and 100"):
            seed_synthetic_lab(session, count=101)

    with app.state.database.session_factory.begin() as session:
        session.add(
            Camera(
                camera_id="phase2:cctv-001",
                source_id="different-source",
                external_id="collision",
                display_name="Collision",
                source_schema="test.v1",
                provenance={},
            )
        )
    with app.state.database.session_factory() as session:
        with pytest.raises(SyntheticLabError, match="collision"):
            seed_synthetic_lab(session, count=1)


def test_publisher_command_maps_every_destination() -> None:
    command = lab_publisher._publisher_command(
        "ffmpeg",
        Path("fixture.mp4"),
        ["rtsp://gateway/a", "rtsp://gateway/b"],
    )
    assert command[:3] == ["ffmpeg", "-nostdin", "-v"]
    assert command.count("0:v:0") == 2
    assert command[-1] == "rtsp://gateway/b"


def test_publisher_fixture_failure_is_normalized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1),
    )
    with pytest.raises(RuntimeError, match="generate"):
        lab_publisher._generate_fixture("ffmpeg", tmp_path / "fixture.mp4")


def test_publisher_main_is_guarded_bounded_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("HCAM_ALLOW_SYNTHETIC_LAB", raising=False)
    assert lab_publisher.main(["--count", "1"]) == 2
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    assert lab_publisher.main(["--count", "101"]) == 2

    fixture = tmp_path / "fixture.mp4"
    heartbeat = tmp_path / "publisher.ready"
    monkeypatch.setattr(
        lab_publisher,
        "_generate_fixture",
        lambda _ffmpeg, path: path.write_bytes(b"synthetic"),
    )
    monkeypatch.setattr(lab_publisher.signal, "signal", lambda *_args: None)
    monkeypatch.setattr(lab_publisher, "sleep", lambda _seconds: None)

    class ProcessStub:
        def __init__(self) -> None:
            self.poll_count = 0
            self.waited = False

        def poll(self) -> int | None:
            self.poll_count += 1
            return None if self.poll_count == 1 else 1

        def terminate(self) -> None:
            raise AssertionError("completed publisher should not be terminated")

        def wait(self, *, timeout: float) -> int:
            assert timeout == 5
            self.waited = True
            return 1

    process = ProcessStub()
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: process,
    )
    assert lab_publisher.main(
        [
            "--count",
            "2",
            "--fixture",
            str(fixture),
            "--heartbeat-file",
            str(heartbeat),
        ]
    ) == 1
    assert process.waited is True
    assert not fixture.exists()
    assert not heartbeat.exists()


def test_publisher_kills_process_that_does_not_stop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "1")
    monkeypatch.setattr(
        lab_publisher,
        "_generate_fixture",
        lambda _ffmpeg, path: path.write_bytes(b"synthetic"),
    )
    monkeypatch.setattr(lab_publisher.signal, "signal", lambda *_args: None)

    class ProcessStub:
        killed = False
        terminated = False
        wait_count = 0

        def poll(self) -> int:
            return 1

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, *, timeout: float) -> int:
            self.wait_count += 1
            if self.wait_count == 1:
                raise subprocess.TimeoutExpired("ffmpeg", timeout)
            return -9

        def kill(self) -> None:
            self.killed = True

    process = ProcessStub()
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: process)
    assert lab_publisher.main(
        ["--count", "1", "--fixture", str(tmp_path / "fixture.mp4")]
    ) == 1
    assert process.killed is True
