from __future__ import annotations

import pytest
from pydantic import ValidationError

from hcam.camera_registry.importer import sanitize_stream_reference
from hcam.camera_registry.schemas import CameraSeed, RegistrySeed


def valid_camera() -> dict:
    return {
        "camera_id": "synthetic:cctv-001",
        "source": "synthetic-reference",
        "external_id": "cctv-001",
        "display_name": "Synthetic Camera",
        "location": {"latitude": 23.0, "longitude": 72.0},
    }


def test_camera_schema_accepts_valid_gis_coordinates() -> None:
    camera = CameraSeed.model_validate(valid_camera())
    assert camera.location.latitude == 23.0
    assert camera.location.longitude == 72.0


@pytest.mark.parametrize(
    "field,value",
    [("camera_id", "missing-namespace"), ("source", "INVALID SOURCE")],
)
def test_camera_schema_rejects_malformed_identity(field: str, value: str) -> None:
    payload = valid_camera()
    payload[field] = value
    with pytest.raises(ValidationError):
        CameraSeed.model_validate(payload)


def test_camera_schema_rejects_partial_or_invalid_coordinates() -> None:
    payload = valid_camera()
    payload["location"] = {"latitude": 91, "longitude": 72}
    with pytest.raises(ValidationError):
        CameraSeed.model_validate(payload)

    payload["location"] = {"latitude": 23}
    with pytest.raises(ValidationError):
        CameraSeed.model_validate(payload)


def test_registry_schema_rejects_duplicate_camera_keys() -> None:
    camera = valid_camera()
    payload = {
        "schema": "hcam.camera_registry.seed.v1",
        "generated_at": "2026-08-18T00:00:00Z",
        "source": {
            "adapter": "synthetic-reference",
            "safe_use": "Synthetic metadata only.",
        },
        "cameras": [camera, camera],
    }
    with pytest.raises(ValidationError, match="duplicate camera_id"):
        RegistrySeed.model_validate(payload)


def test_stream_reference_sanitizer_removes_credentials_and_tokens() -> None:
    assert sanitize_stream_reference(
        "https://operator:secret@example.invalid/live/1?token=secret#fragment"
    ) == "https://example.invalid/live/1"
    assert sanitize_stream_reference("/live/1?token=secret") == "/live/1"
    assert sanitize_stream_reference("file:///private/video.mp4") is None


@pytest.mark.parametrize(
    "reference",
    [
        "http://example.invalid:bad/live",
        "http://[broken/live",
        "https://example.invalid/line\nbreak",
        "x" * 4097,
    ],
)
def test_stream_reference_sanitizer_never_raises_for_malformed_input(
    reference: str,
) -> None:
    assert sanitize_stream_reference(reference) is None
