from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
import pytest

from tools import phase32_research_acquire as acquire
from tools import phase32_offline_experiment as experiment


def manifest(url: str = "https://official.example/model.onnx") -> dict[str, object]:
    return {
        "authorization_id": "D-P3.2-001-TEST",
        "limits": {
            "cumulative_artifact_bytes": 32,
            "maximum_artifact_bytes": 16,
            "redirect_limit": 1,
            "timeout_seconds": 1,
        },
        "artifacts": [
            {
                "allowed_redirect_hosts": [
                    "official.example",
                    "assets.example",
                ],
                "artifact_id": "DET-TEST",
                "expected_content_types": ["application/octet-stream"],
                "expected_sha256": None,
                "filename": "model.onnx",
                "maximum_bytes": 16,
                "research_status": "research_only",
                "source_url": url,
            }
        ],
    }


def test_acquire_records_digest_and_reuses_verified_artifact(tmp_path: Path) -> None:
    body = b"model-bytes"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=body,
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        first = acquire.acquire_artifact(manifest(), "DET-TEST", tmp_path, client=client)
        second = acquire.acquire_artifact(manifest(), "DET-TEST", tmp_path, client=client)

    assert first["sha256"] == hashlib.sha256(body).hexdigest().upper()
    assert first["bytes"] == len(body)
    assert first["reused"] is False
    assert second["reused"] is True
    assert (tmp_path / first["local_path"]).read_bytes() == body


def test_acquire_revalidates_redirect_host(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://unapproved.example/model.onnx"},
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(acquire.AcquisitionError, match="not allowlisted"):
            acquire.acquire_artifact(manifest(), "DET-TEST", tmp_path, client=client)


def test_sanitized_url_removes_signed_query_and_fragment() -> None:
    assert (
        acquire._sanitized_url("https://assets.example/model.onnx?token=secret#part")
        == "https://assets.example/model.onnx"
    )


def test_acquire_rejects_size_limit_and_removes_partial(tmp_path: Path) -> None:
    body = b"x" * 17
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=body,
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(acquire.AcquisitionError, match="per-file"):
            acquire.acquire_artifact(manifest(), "DET-TEST", tmp_path, client=client)

    assert not list(tmp_path.rglob("*.partial"))


def test_acquire_rejects_unsafe_filename(tmp_path: Path) -> None:
    value = manifest()
    value["artifacts"][0]["filename"] = "../model.onnx"

    with pytest.raises(acquire.AcquisitionError, match="one plain path component"):
        acquire.acquire_artifact(value, "DET-TEST", tmp_path)


def test_verified_artifact_rejects_receipt_hash_drift(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "DET-TEST" / "model.onnx"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"changed")
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    (receipt_dir / "DET-TEST.json").write_text(
        json.dumps(
            {
                "bytes": len(b"changed"),
                "local_path": "artifacts/DET-TEST/model.onnx",
                "sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(experiment.ExperimentError, match="SHA-256"):
        experiment.verified_artifact(tmp_path, "DET-TEST")


def test_network_guard_denies_connections() -> None:
    with experiment.deny_python_network():
        with pytest.raises(httpx.ConnectError, match="network disabled"):
            httpx.get("https://example.com")
