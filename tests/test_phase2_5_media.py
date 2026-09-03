from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from hcam.labs.sentinel import accelerators, media
from hcam.labs.sentinel.accelerators import (
    EncoderSelection,
    discover_acceleration,
    encoder_quality_arguments,
)
from hcam.labs.sentinel.fixtures import GeneratedMediaProfile
from hcam.labs.sentinel.media import (
    MediaFixtureError,
    _frame_rate,
    fixture_command,
    prepare_media_fixtures,
    probe_media_fixture,
    remove_media_fixtures,
)
from hcam.labs.sentinel.publisher import publisher_command


def small_profile(codec: str = "h264") -> GeneratedMediaProfile:
    return GeneratedMediaProfile(
        camera_number=1,
        camera_id="C01",
        profile_id="P1-C01",
        fixture_name=f"small-{codec}.mp4",
        actual_codec=codec,  # type: ignore[arg-type]
        advertised_codec=codec,  # type: ignore[arg-type]
        width=320,
        height=180,
        fps=10,
        bitrate_kbps=500,
        crf=22,
        gop=10,
        hue_degrees=37,
        active_by_default=True,
        expected_reachable=True,
    )


def test_accelerator_falls_back_per_codec_when_requested_gpu_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        accelerators,
        "_encoder_names",
        lambda _ffmpeg: (
            "ffmpeg generated test",
            {"h264_nvenc", "hevc_nvenc", "libx264", "libx265"},
        ),
    )
    monkeypatch.setattr(
        accelerators,
        "_smoke_test",
        lambda _ffmpeg, selection: selection.accelerator == "cpu",
    )

    report = discover_acceleration("ffmpeg", requested="nvidia")

    assert report.h264.encoder == "libx264"
    assert report.hevc.encoder == "libx265"
    assert report.h264.fallback
    assert report.hevc.fallback


def test_encoder_arguments_are_quality_oriented_and_bounded() -> None:
    nvenc = EncoderSelection(
        "h264", "nvidia", "nvidia", "h264_nvenc", True, False, True
    )
    cpu = EncoderSelection("hevc", "cpu", "cpu", "libx265", False, False, True)

    assert "p5" in encoder_quality_arguments(nvenc, crf=19, bitrate_kbps=2000)
    assert "hq" in encoder_quality_arguments(nvenc, crf=19, bitrate_kbps=2000)
    assert "veryfast" in encoder_quality_arguments(cpu, crf=20, bitrate_kbps=1500)
    assert "log-level=error" in encoder_quality_arguments(
        cpu, crf=20, bitrate_kbps=1500
    )


def test_cpu_fixture_generation_is_real_and_cleanup_is_zero_retention(tmp_path) -> None:
    report = discover_acceleration(requested="cpu")
    evidence = prepare_media_fixtures(
        (small_profile(),),
        tmp_path / "media",
        report,
        duration_seconds=0.2,
        parallelism=1,
    )

    assert evidence["fixture_count"] == 1
    assert evidence["total_bytes"] > 0
    assert evidence["fixtures"][0]["probe"]["has_b_frames"] == 0
    assert (tmp_path / "media" / "small-h264.mp4").is_file()
    assert remove_media_fixtures(tmp_path / "media") == 2
    assert not (tmp_path / "media").exists()


def test_h264_generation_disables_b_frames_for_whep_compatibility(tmp_path) -> None:
    selection = EncoderSelection("h264", "cpu", "cpu", "libx264", False, False, True)
    command = fixture_command(
        "ffmpeg",
        small_profile(),
        tmp_path / "fixture.mp4",
        selection,
        duration_seconds=0.2,
    )

    assert command[command.index("-bf") + 1] == "0"


def test_hevc_generation_does_not_override_encoder_b_frame_policy(tmp_path) -> None:
    selection = EncoderSelection("hevc", "cpu", "cpu", "libx265", False, False, True)
    command = fixture_command(
        "ffmpeg",
        small_profile("hevc"),
        tmp_path / "fixture.mp4",
        selection,
        duration_seconds=0.2,
    )

    assert "-bf" not in command


def test_reused_fixtures_preserve_the_original_encoding_accelerator(tmp_path) -> None:
    report = discover_acceleration(requested="cpu")
    media_dir = tmp_path / "media"
    prepare_media_fixtures(
        (small_profile(),),
        media_dir,
        report,
        duration_seconds=0.2,
        parallelism=1,
    )
    evidence_path = media_dir / "fixture-evidence.json"
    prior = json.loads(evidence_path.read_text(encoding="ascii"))
    prior["accelerator"] = {"h264": {"accelerator": "intel", "encoder": "h264_qsv"}}
    evidence_path.write_text(json.dumps(prior), encoding="ascii")

    reused = prepare_media_fixtures(
        (small_profile(),),
        media_dir,
        report,
        duration_seconds=0.2,
        parallelism=1,
    )

    assert reused["regenerated_fixture_count"] == 0
    assert reused["reused_fixture_count"] == 1
    assert reused["accelerator"]["h264"]["accelerator"] == "intel"
    assert reused["validation_accelerator"]["h264"]["accelerator"] == "cpu"


def test_publisher_uses_parallel_lossless_remux_over_rtsp_tcp() -> None:
    command = publisher_command(
        "ffmpeg",
        Path("generated.mp4"),
        "rtsp://mediamtx:8554/hcam/str_0001",
    )

    assert command[command.index("-c:v") + 1] == "copy"
    assert command[command.index("-rtsp_transport") + 1] == "tcp"
    assert "-stream_loop" in command
    assert "libx264" not in command


def test_fixture_command_validates_duration_and_vaapi_device(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(media, "default_font_file", lambda: None)
    vaapi = EncoderSelection("h264", "vaapi", "vaapi", "h264_vaapi", True, False, True)
    command = fixture_command(
        "ffmpeg",
        small_profile(),
        tmp_path / "fixture.mp4",
        vaapi,
        duration_seconds=0.2,
    )
    device_index = command.index("-vaapi_device")
    assert command[device_index : device_index + 2] == [
        "-vaapi_device",
        "/dev/dri/renderD128",
    ]
    assert "drawtext" not in command[command.index("-i") + 1]
    with pytest.raises(ValueError, match="fixture duration"):
        fixture_command(
            "ffmpeg",
            small_profile(),
            tmp_path / "fixture.mp4",
            vaapi,
            duration_seconds=0.01,
        )


def test_frame_rate_parser_handles_fraction_decimal_and_invalid_values() -> None:
    assert _frame_rate("25") == 25
    assert _frame_rate("30000/1001") == pytest.approx(29.97, rel=0.001)
    assert _frame_rate(None) is None
    assert _frame_rate(25) is None
    assert _frame_rate("") is None
    assert _frame_rate("1/0") is None
    assert _frame_rate("invalid") is None


def probe_document(
    *,
    codec="h264",
    width=320,
    height=180,
    fps="10/1",
    has_b_frames=0,
    duration="1.0",
):
    return json.dumps(
        {
            "streams": [
                {
                    "codec_name": codec,
                    "width": width,
                    "height": height,
                    "avg_frame_rate": fps,
                    "has_b_frames": has_b_frames,
                }
            ],
            "format": {"duration": duration},
        }
    )


@pytest.mark.parametrize(
    ("completed", "timing", "expected_code"),
    [
        (SimpleNamespace(returncode=0, stdout="not-json"), {}, "fixture_probe_invalid"),
        (
            SimpleNamespace(returncode=1, stdout=probe_document()),
            {},
            "fixture_probe_failed",
        ),
        (
            SimpleNamespace(returncode=0, stdout=probe_document(codec="hevc")),
            {},
            "fixture_media_mismatch",
        ),
        (
            SimpleNamespace(returncode=0, stdout=probe_document(has_b_frames=2)),
            {},
            "fixture_h264_b_frames_present",
        ),
        (
            SimpleNamespace(returncode=0, stdout=probe_document()),
            {"monotonic": False},
            "fixture_non_monotonic_timestamps",
        ),
        (
            SimpleNamespace(returncode=0, stdout=probe_document(fps="9/1")),
            {"monotonic": True},
            "fixture_frame_rate_mismatch",
        ),
        (
            SimpleNamespace(returncode=0, stdout=probe_document(duration="5")),
            {"monotonic": True},
            "fixture_duration_mismatch",
        ),
    ],
)
def test_media_probe_rejects_invalid_or_incompatible_results(
    monkeypatch, tmp_path, completed, timing, expected_code
) -> None:
    monkeypatch.setattr(media.subprocess, "run", lambda *_a, **_k: completed)
    monkeypatch.setattr(media, "analyze_fixture_timing", lambda *_a, **_k: timing)
    with pytest.raises(MediaFixtureError, match=expected_code):
        probe_media_fixture(
            small_profile(),
            tmp_path / "fixture.mp4",
            ffprobe="ffprobe",
            expected_duration=1,
        )


def test_media_probe_wraps_execution_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        media.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("ffprobe unavailable")),
    )
    with pytest.raises(MediaFixtureError, match="fixture_probe_failed"):
        probe_media_fixture(
            small_profile(),
            tmp_path / "fixture.mp4",
            ffprobe="ffprobe",
            expected_duration=1,
        )


def test_remove_media_fixtures_preserves_unrelated_files(tmp_path) -> None:
    output = tmp_path / "media"
    output.mkdir()
    (output / "keep.txt").write_text("generated lab note", encoding="ascii")
    assert remove_media_fixtures(output) == 0
    assert output.is_dir()
    assert remove_media_fixtures(tmp_path / "missing") == 0
