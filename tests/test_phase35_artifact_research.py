from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
import pytest

from tools import phase35_artifact_research as research


def records(body: bytes = b"artifact") -> tuple[dict[str, object], dict[str, object], str]:
    blob = hashlib.sha1(usedforsecurity=False)
    blob.update(f"blob {len(body)}\0".encode())
    blob.update(body)
    artifact_ids = ["OCR-TEST-PROPOSED", *(f"OCR-TEST-{index}" for index in range(1, 7))]
    proposal_artifacts = []
    allowed_artifacts = []
    for index, artifact_id in enumerate(artifact_ids):
        url = f"https://raw.githubusercontent.com/owner/repo/revision/file-{index}.bin"
        proposal_artifacts.append(
            {
                "artifact_id": artifact_id,
                "expected_bytes": len(body),
                "git_blob_sha1": blob.hexdigest(),
                "maximum_bytes": 32,
                "proposed_source_url": url,
            }
        )
        allowed_artifacts.append(
            {
                "artifact_id": artifact_id,
                "expected_bytes": len(body),
                "expected_content_types": ["application/octet-stream"],
                "filename": f"file-{index}.bin",
                "maximum_bytes": 32,
                "source_url": url,
            }
        )
    proposal = {
        "proposal_id": "P3.5-EXACT-ARTIFACT-REVIEW-PROPOSAL-R0",
        "artifacts": proposal_artifacts,
    }
    payload = json.dumps(proposal, sort_keys=True).encode()
    proposal_sha256 = hashlib.sha256(payload).hexdigest().upper()
    authorization = {
        "allowed_artifacts": allowed_artifacts,
        "allowed_network_actions": ["https_get_exact_allowlisted_urls_only"],
        "authorization_id": "D-P3.5-ARTIFACT-RESEARCH",
        "implementation_authorized": False,
        "limits": {
            "cumulative_artifact_bytes": 64,
            "environment_proxies": False,
            "maximum_redirects": 0,
            "per_artifact_timeout_seconds": 1,
            "runtime_loading_from_quarantine": False,
        },
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal_sha256,
        "status": "owner_approved_restricted",
    }
    return authorization, proposal, proposal_sha256


def test_acquire_hashes_receipts_and_reuses_verified_artifact(tmp_path: Path) -> None:
    body = b"artifact"
    authorization, proposal, proposal_sha256 = records(body)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-length": str(len(body)),
                "content-type": "application/octet-stream",
            },
            content=body,
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        first = research.acquire_artifact(
            authorization,
            proposal,
            proposal_sha256,
            "OCR-TEST-PROPOSED",
            tmp_path,
            client=client,
        )
        second = research.acquire_artifact(
            authorization,
            proposal,
            proposal_sha256,
            "OCR-TEST-PROPOSED",
            tmp_path,
            client=client,
        )

    assert first["sha256"] == hashlib.sha256(body).hexdigest().upper()
    assert first["git_blob_sha1"] == proposal["artifacts"][0]["git_blob_sha1"]
    assert first["runtime_loading_authorized"] is False
    assert second["reused"] is True


def test_rejects_redirect_and_removes_partial_state(tmp_path: Path) -> None:
    authorization, proposal, proposal_sha256 = records()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            302,
            headers={"location": "https://raw.githubusercontent.com/other"},
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(research.ArtifactResearchError, match="redirects"):
            research.acquire_artifact(
                authorization,
                proposal,
                proposal_sha256,
                "OCR-TEST-PROPOSED",
                tmp_path,
                client=client,
            )
    assert not list(tmp_path.rglob("*.partial"))


def test_rejects_wrong_git_blob_identity(tmp_path: Path) -> None:
    authorization, proposal, proposal_sha256 = records()
    proposal["artifacts"][0]["git_blob_sha1"] = "0" * 40
    body = b"artifact"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-length": str(len(body)),
                "content-type": "application/octet-stream",
            },
            content=body,
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(research.ArtifactResearchError, match="Git blob"):
            research.acquire_artifact(
                authorization,
                proposal,
                proposal_sha256,
                "OCR-TEST-PROPOSED",
                tmp_path,
                client=client,
            )


def test_rejects_proposal_digest_mismatch(tmp_path: Path) -> None:
    authorization, proposal, _ = records()
    with pytest.raises(research.ArtifactResearchError, match="not effective"):
        research.acquire_artifact(
            authorization,
            proposal,
            "0" * 64,
            "OCR-TEST-PROPOSED",
            tmp_path,
        )


def test_rejects_etag_drift(tmp_path: Path) -> None:
    authorization, proposal, proposal_sha256 = records()
    proposal["artifacts"][0]["observed_etag"] = "expected"
    body = b"artifact"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-length": str(len(body)),
                "content-type": "application/octet-stream",
                "etag": '"changed"',
            },
            content=body,
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(research.ArtifactResearchError, match="ETag"):
            research.acquire_artifact(
                authorization,
                proposal,
                proposal_sha256,
                "OCR-TEST-PROPOSED",
                tmp_path,
                client=client,
            )


def test_rejects_size_and_content_type_drift(tmp_path: Path) -> None:
    authorization, proposal, proposal_sha256 = records()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-length": "9",
                "content-type": "text/html",
            },
            content=b"artifact!",
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(research.ArtifactResearchError, match="Content-Length"):
            research.acquire_artifact(
                authorization,
                proposal,
                proposal_sha256,
                "OCR-TEST-PROPOSED",
                tmp_path,
                client=client,
            )


def test_rejects_quarantine_inside_worktree() -> None:
    with pytest.raises(research.ArtifactResearchError, match="outside"):
        research.validate_research_root(research.ROOT / "var" / "p3-5-test")


def test_rejects_unsafe_filename_before_network(tmp_path: Path) -> None:
    authorization, proposal, proposal_sha256 = records()
    authorization["allowed_artifacts"][0]["filename"] = "../file.bin"
    with pytest.raises(research.ArtifactResearchError, match="filename"):
        research.acquire_artifact(
            authorization,
            proposal,
            proposal_sha256,
            "OCR-TEST-PROPOSED",
            tmp_path,
        )
