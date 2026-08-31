from __future__ import annotations

from time import time

import pytest

from hcam.labs.sentinel.accelerators import discover_acceleration
from hcam.labs.sentinel.fault_proxy import fault_is_active
from hcam.labs.sentinel.faults import (
    DEFAULT_FAULT_TARGETS,
    FaultRequestError,
    make_fault_request,
    parse_fault_request,
    read_fault_request,
    write_fault_request,
)
from hcam.labs.sentinel.fixtures import (
    GeneratedMediaProfile,
    generated_catalog_document,
    generated_media_profiles,
)
from hcam.labs.sentinel.media import prepare_media_fixtures, remove_media_fixtures
from hcam.labs.sentinel.publisher import PublisherProcess, apply_fault
from hcam.labs.sentinel.timing import (
    FAULT_SCENARIOS,
    ConnectionEpochState,
    classify_loop,
)


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False

    def poll(self) -> int | None:
        return 0 if self.terminated else None

    def terminate(self) -> None:
        self.terminated = True


def variable_profile() -> GeneratedMediaProfile:
    return GeneratedMediaProfile(
        camera_number=11,
        camera_id="C11",
        profile_id="P3-C11",
        fixture_name="small-vfr.mp4",
        actual_codec="h264",
        advertised_codec="h264",
        width=320,
        height=180,
        fps=12.5,
        bitrate_kbps=500,
        crf=22,
        gop=20,
        hue_degrees=47,
        active_by_default=True,
        expected_reachable=True,
        timing_pattern="variable_pts",
    )


def test_variable_pts_fixture_uses_real_timestamp_gaps(tmp_path) -> None:
    evidence = prepare_media_fixtures(
        (variable_profile(),),
        tmp_path / "media",
        discover_acceleration(requested="cpu"),
        duration_seconds=0.8,
        parallelism=1,
    )

    timing = evidence["fixtures"][0]["probe"]["timing"]
    assert timing["monotonic"] is True
    assert timing["unique_delta_count"] >= 2
    assert timing["max_delta"] >= timing["min_delta"] * 1.5
    assert timing["retained_frames"] == 0
    assert remove_media_fixtures(tmp_path / "media") == 2


def test_connection_epochs_and_retry_are_bounded_and_deterministic() -> None:
    first = ConnectionEpochState("generated-stream")
    second = ConnectionEpochState("generated-stream")
    first.on_connected()
    first.on_disconnected()
    first.on_discontinuity()

    first_delays = [first.next_retry_delay() for _ in range(8)]
    second_delays = [second.next_retry_delay() for _ in range(8)]

    assert first.connection_epoch == 1
    assert first.discontinuity_epoch == 1
    assert first_delays == second_delays
    assert first_delays == sorted(first_delays)
    assert max(first_delays) <= 30


def test_loop_classifier_forbids_cross_epoch_state() -> None:
    result = classify_loop([0.0, 0.04, 0.08, 0.0, 0.04])

    assert result["discontinuity_epochs"] == 1
    assert result["cross_epoch_state_allowed"] is False


def test_fault_requests_are_exact_bounded_and_expire(tmp_path) -> None:
    request = make_fault_request("F6", duration_seconds=5, now=100)
    path = tmp_path / "fault-request.json"
    write_fault_request(path, request)

    assert read_fault_request(path) == request
    assert request.active(104.999)
    assert not request.active(105)
    with pytest.raises(FaultRequestError, match="fault_scenario_not_allowed"):
        make_fault_request("F8")
    with pytest.raises(FaultRequestError, match="fault_camera_not_allowed"):
        make_fault_request("F1", camera_id="../../camera")
    with pytest.raises(FaultRequestError, match="fault_duration_out_of_bounds"):
        make_fault_request("F1", duration_seconds=31)


def test_fault_request_parser_rejects_extra_fields_and_missing_confirmation() -> None:
    request = make_fault_request("F1", now=100)
    document = request.document()
    document.pop("expires_at_epoch")
    document["unexpected"] = "field"
    with pytest.raises(FaultRequestError, match="fault_request_invalid"):
        parse_fault_request(document)

    document.pop("unexpected")
    document["confirm_generated_only"] = False
    with pytest.raises(FaultRequestError, match="generated_lab_confirmation_required"):
        parse_fault_request(document)


def test_private_proxy_blocks_only_active_f6_for_camera_four(tmp_path) -> None:
    path = tmp_path / "fault-request.json"
    request = make_fault_request("F6", now=time(), duration_seconds=30)
    write_fault_request(path, request)

    blocked, request_id = fault_is_active(path)

    assert blocked
    assert request_id == request.request_id
    replacement = make_fault_request("F4", now=time(), duration_seconds=30)
    write_fault_request(path, replacement)
    assert fault_is_active(path) == (False, None)


def test_fault_scenarios_have_safe_defaults_and_machine_evidence(tmp_path) -> None:
    assert set(FAULT_SCENARIOS) == {f"F{number}" for number in range(1, 8)}
    assert set(DEFAULT_FAULT_TARGETS) == set(FAULT_SCENARIOS)
    assert all(item["max_cameras"] == 1 for item in FAULT_SCENARIOS.values())

    profile = generated_media_profiles()[3]
    process = FakeProcess()
    publisher = PublisherProcess(
        number=4,
        camera_id="C04",
        command=["ffmpeg"],
        process=process,  # type: ignore[arg-type]
        epoch=ConnectionEpochState("C04"),
    )
    evidence = apply_fault(
        make_fault_request("F6", now=time(), duration_seconds=10),
        [publisher],
        fixture_dir=tmp_path,
        profiles_by_camera={"C04": profile},
    )

    assert evidence["classification"] == "generated-only"
    assert evidence["inference_transport"] == "blocked-by-private-proxy"
    assert evidence["preview_transport"] == "hls-direct-mediamtx"
    assert evidence["hls_fallback_available"] is True
    assert evidence["zero_retained_media"] is True
    assert not process.terminated


def test_camera_four_routes_inference_through_proxy_but_preview_stays_direct() -> None:
    camera = generated_catalog_document()["cameras"][3]

    assert camera["rtsp_url"].startswith("rtsp://rtsp-fault-proxy:8555/")
    assert camera["hls_live_url"].startswith("http://mediamtx:8888/")
    assert camera["webrtc_url"].startswith("http://mediamtx:8889/")
