from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from tools import phase35_auxiliary_ocr as tool


def _write_archive(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, mode="w") as archive:
        directory = tarfile.TarInfo("model/")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        for name, payload in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))


def _profile(path: Path, members: dict[str, bytes]) -> tool.ModelProfile:
    yml = members["model/inference.yml"]
    inventory = _inventory_digest(members)
    return tool.ModelProfile(
        candidate_id="OCR-D0",
        artifact_id="test",
        archive_relative_path=path.name,
        archive_sha256=tool._sha256(path),
        top_level="model",
        member_sizes={
            name.removeprefix("model/"): len(payload)
            for name, payload in members.items()
        },
        inference_yml_sha256=_payload_sha256(yml),
        extracted_inventory_sha256=inventory,
    )


def _payload_sha256(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest().upper()


def _inventory_digest(members: dict[str, bytes]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for full_name in sorted(members):
        name = full_name.removeprefix("model/")
        payload = members[full_name]
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(len(payload)).encode("ascii"))
        digest.update(b"\0")
        digest.update(_payload_sha256(payload).encode("ascii"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _members() -> dict[str, bytes]:
    return {
        "model/export_result.json": b"{}",
        "model/inference.json": b"{}",
        "model/inference.pdiparams": b"weights",
        "model/inference.yml": b"Global:\n  model_name: test\n",
    }


def test_archive_inspection_accepts_only_exact_regular_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    members = _members()
    archive = tmp_path / "model.tar"
    _write_archive(archive, members)
    monkeypatch.setattr(tool, "MODEL_PROFILE", _profile(archive, members))

    inspected = tool._inspect_archive(archive)

    assert len(inspected) == 5


def test_archive_inspection_rejects_traversal_and_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    traversal = tmp_path / "traversal.tar"
    with tarfile.open(traversal, mode="w") as archive:
        member = tarfile.TarInfo("../escape")
        member.size = 1
        archive.addfile(member, io.BytesIO(b"x"))
    profile = tool.ModelProfile(
        candidate_id="OCR-D0",
        artifact_id="test",
        archive_relative_path=traversal.name,
        archive_sha256=tool._sha256(traversal),
        top_level="model",
        member_sizes={},
        inference_yml_sha256="0" * 64,
        extracted_inventory_sha256="sha256:" + "0" * 64,
    )
    monkeypatch.setattr(tool, "MODEL_PROFILE", profile)
    with pytest.raises(tool.AuxiliaryOcrToolError, match="unsafe path"):
        tool._inspect_archive(traversal)

    link = tmp_path / "link.tar"
    with tarfile.open(link, mode="w") as archive:
        directory = tarfile.TarInfo("model/")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        member = tarfile.TarInfo("model/link")
        member.type = tarfile.SYMTYPE
        member.linkname = "elsewhere"
        archive.addfile(member)
    monkeypatch.setattr(
        tool,
        "MODEL_PROFILE",
        tool.ModelProfile(
            candidate_id="OCR-D0",
            artifact_id="test",
            archive_relative_path=link.name,
            archive_sha256=tool._sha256(link),
            top_level="model",
            member_sizes={},
            inference_yml_sha256="0" * 64,
            extracted_inventory_sha256="sha256:" + "0" * 64,
        ),
    )
    with pytest.raises(tool.AuxiliaryOcrToolError, match="link or special"):
        tool._inspect_archive(link)


def test_model_inventory_is_content_bound_and_rejects_extra_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    members = _members()
    archive = tmp_path / "model.tar"
    _write_archive(archive, members)
    profile = _profile(archive, members)
    monkeypatch.setattr(tool, "MODEL_PROFILE", profile)
    model = tmp_path / "model"
    model.mkdir()
    for name, payload in members.items():
        (model / name.removeprefix("model/")).write_bytes(payload)

    assert tool._model_inventory(model) == profile.extracted_inventory_sha256
    (model / "unexpected").mkdir()
    with pytest.raises(tool.AuxiliaryOcrToolError, match="extra directory"):
        tool._model_inventory(model)


def test_effective_authorization_pins_w6_and_blocks_gujarati_ocr() -> None:
    authorization = tool._load_authorization()

    assert authorization["allowed_network_actions"] == []
    assert authorization["allowed_runtime"]["tesseract_runtime_authorized"] is False
    assert {
        item["candidate_id"]
        for item in authorization["blocked_reviewed_artifacts"]
    } == {"OCR-G0", "OCR-G1"}


def test_tool_paths_never_use_prohibited_b_drive() -> None:
    paths = (
        tool.ARTIFACT_ROOT,
        tool.RUNTIME_ROOT,
        tool.EVIDENCE_PATH,
        tool.WORKER_PATH,
    )

    assert all(path.drive.upper() != "B:" for path in paths)
