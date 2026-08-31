from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from hcam.labs.sentinel import accelerators, fault_proxy, simulator
from hcam.labs.sentinel.accelerators import (
    AcceleratorError,
    EncoderSelection,
    discover_acceleration,
    encoder_quality_arguments,
)
from hcam.labs.sentinel.lab_adapters import (
    LabAdapterStateError,
    lab_adapter_profile,
    read_active_lab_adapter,
)
from hcam.labs.sentinel.secrets import (
    FileSecretProvider,
    SecretResolutionError,
    UnconfiguredSecretProvider,
)


def test_file_secret_provider_is_typed_rooted_and_fail_closed(tmp_path) -> None:
    root = tmp_path / "secrets"
    root.mkdir()
    provider = FileSecretProvider(root, max_bytes=128)

    (root / "bearer.json").write_text('{"bearer_token":"lab-token"}', encoding="utf-8")
    (root / "basic.json").write_text(
        '{"username":"lab-user","password":"lab-password"}', encoding="utf-8"
    )
    assert provider.resolve("bearer.json", "bearer").bearer_token == "lab-token"
    basic = provider.resolve("basic.json", "basic")
    assert (basic.username, basic.password) == ("lab-user", "lab-password")

    with pytest.raises(SecretResolutionError, match="secret_provider_unconfigured"):
        UnconfiguredSecretProvider().resolve("any", "bearer")
    for reference in ("", "../escape.json", str((root / "basic.json").resolve())):
        with pytest.raises(SecretResolutionError, match="secret_ref_invalid"):
            provider.resolve(reference, "basic")
    with pytest.raises(SecretResolutionError, match="secret_resolution_failed"):
        provider.resolve("missing.json", "basic")

    invalid = root / "invalid.json"
    invalid.write_text("[]", encoding="utf-8")
    with pytest.raises(SecretResolutionError, match="secret_document_invalid"):
        provider.resolve("invalid.json", "bearer")
    invalid.write_text('{"bearer_token":""}', encoding="utf-8")
    with pytest.raises(SecretResolutionError, match="secret_document_invalid"):
        provider.resolve("invalid.json", "bearer")
    invalid.write_text('{"username":"lab-user"}', encoding="utf-8")
    with pytest.raises(SecretResolutionError, match="secret_document_invalid"):
        provider.resolve("invalid.json", "basic")
    invalid.write_text('{"value":"generated"}', encoding="utf-8")
    with pytest.raises(SecretResolutionError, match="secret_auth_mode_invalid"):
        provider.resolve("invalid.json", "none")
    invalid.write_bytes(b"x" * 129)
    with pytest.raises(SecretResolutionError, match="secret_file_invalid"):
        provider.resolve("invalid.json", "bearer")

    not_a_root = tmp_path / "file-root"
    not_a_root.write_text("generated", encoding="ascii")
    with pytest.raises(SecretResolutionError, match="secret_root_invalid"):
        FileSecretProvider(not_a_root)


def test_lab_adapter_and_fault_state_reject_malformed_documents(tmp_path) -> None:
    with pytest.raises(LabAdapterStateError, match="lab_adapter_unknown"):
        lab_adapter_profile("main-adapter")

    state = tmp_path / "adapter-state.json"
    state.write_text("[]", encoding="ascii")
    with pytest.raises(LabAdapterStateError, match="lab_adapter_state_invalid"):
        read_active_lab_adapter(state)

    request = tmp_path / "fault.json"
    request.write_text("not-json", encoding="ascii")
    assert fault_proxy.fault_is_active(request) == (False, "invalid_request")


def selection(encoder: str, *, codec: str = "h264") -> EncoderSelection:
    return EncoderSelection(
        codec=codec,  # type: ignore[arg-type]
        requested="auto",
        accelerator=encoder.rsplit("_", 1)[-1],
        encoder=encoder,
        hardware=encoder not in {"libx264", "libx265"},
        fallback=False,
        validated=True,
    )


def test_every_supported_encoder_keeps_quality_oriented_arguments() -> None:
    qsv = encoder_quality_arguments(selection("h264_qsv"), crf=20, bitrate_kbps=1000)
    amf = encoder_quality_arguments(selection("h264_amf"), crf=20, bitrate_kbps=1000)
    vaapi = encoder_quality_arguments(
        selection("h264_vaapi"), crf=20, bitrate_kbps=1000
    )

    assert "-global_quality" in qsv
    assert "vbr_peak" in amf
    assert "format=nv12,hwupload" in vaapi
    with pytest.raises(AcceleratorError, match="unsupported_encoder"):
        encoder_quality_arguments(selection("unknown"), crf=20, bitrate_kbps=1000)


def test_accelerator_inventory_and_execution_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        accelerators.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(AcceleratorError, match="ffmpeg_unavailable"):
        accelerators._run(["missing-ffmpeg"], timeout=1)

    responses = iter(
        [
            SimpleNamespace(returncode=1, stdout=""),
            SimpleNamespace(returncode=0, stdout="ffmpeg generated\n"),
            SimpleNamespace(returncode=1, stdout=""),
        ]
    )
    monkeypatch.setattr(accelerators, "_run", lambda *_a, **_k: next(responses))
    with pytest.raises(AcceleratorError, match="ffmpeg_unavailable"):
        accelerators._encoder_names("ffmpeg")
    with pytest.raises(AcceleratorError, match="encoder_inventory_failed"):
        accelerators._encoder_names("ffmpeg")

    with pytest.raises(AcceleratorError, match="accelerator_mode_invalid"):
        discover_acceleration(requested="quantum")  # type: ignore[arg-type]


def test_accelerator_selection_orders_and_unavailable_codec(monkeypatch) -> None:
    monkeypatch.setattr(accelerators.platform, "system", lambda: "Windows")
    assert accelerators._candidate_order("auto") == ("nvidia", "intel", "amd", "cpu")
    monkeypatch.setattr(accelerators.platform, "system", lambda: "Linux")
    assert accelerators._candidate_order("auto") == (
        "nvidia",
        "intel",
        "vaapi",
        "cpu",
    )
    assert accelerators._candidate_order("cpu") == ("cpu",)
    assert accelerators._candidate_order("nvidia") == ("nvidia", "cpu")

    monkeypatch.setattr(
        accelerators, "_encoder_names", lambda _ffmpeg: ("ffmpeg generated", set())
    )
    with pytest.raises(AcceleratorError, match="h264_encoder_unavailable"):
        discover_acceleration(requested="cpu", validate=False)


def test_simulator_requires_opt_in_and_supports_adapter_etags(monkeypatch) -> None:
    monkeypatch.delenv("HCAM_ALLOW_SYNTHETIC_LAB", raising=False)
    with pytest.raises(RuntimeError, match="HCAM_ALLOW_SYNTHETIC_LAB"):
        with TestClient(simulator.create_simulator_app()):
            pass

    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    with TestClient(simulator.create_simulator_app()) as client:
        assert client.get("/health").json() == {
            "status": "ok",
            "classification": "generated-only",
        }
        high = client.get("/api/ingest/lab1highadapter")
        low = client.get("/api/ingest/lab2lowadapter")
        high_unchanged = client.get(
            "/api/ingest/lab1highadapter",
            headers={"If-None-Match": high.headers["etag"]},
        )
        low_unchanged = client.get(
            "/api/ingest/lab2lowadapter", headers={"If-None-Match": low.headers["etag"]}
        )
    assert high_unchanged.status_code == 304
    assert low_unchanged.status_code == 304
    assert high_unchanged.headers["x-hcam-lab-adapter"] == "lab1highadapter"
    assert low_unchanged.headers["x-hcam-lab-adapter"] == "lab2lowadapter"


def test_simulator_main_restricts_bind_and_port(monkeypatch) -> None:
    assert simulator.main(["--bind", "0.0.0.0"]) == 2
    assert simulator.main(["--port", "70000"]) == 2
    calls = []
    monkeypatch.setattr(
        simulator.uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    assert simulator.main(["--bind", "0.0.0.0", "--allow-non-loopback"]) == 0
    assert calls[0][1] == {"host": "0.0.0.0", "port": 8090, "access_log": False}
