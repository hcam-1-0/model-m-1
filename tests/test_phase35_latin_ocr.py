from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from tools import phase35_latin_ocr as tool


def _write_archive(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, mode="w") as archive:
        directory = tarfile.TarInfo("model/")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        for name, payload in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))


def _profile(path: Path, members: dict[str, bytes]) -> tool.ArtifactProfile:
    return tool.ArtifactProfile(
        candidate_id="OCR-L0",
        artifact_id="test",
        archive_relative_path=path.name,
        archive_sha256=tool._sha256(path),
        top_level="model",
        member_sizes={
            name.removeprefix("model/"): len(payload)
            for name, payload in members.items()
        },
        inference_yml_sha256=tool._sha256(
            _materialize(path.parent, members["model/inference.yml"])
        ),
    )


def _materialize(parent: Path, payload: bytes) -> Path:
    path = parent / "expected-inference.yml"
    path.write_bytes(payload)
    return path


def test_archive_inspection_accepts_only_exact_regular_inventory(tmp_path: Path) -> None:
    members = {
        "model/inference.json": b"{}",
        "model/inference.pdiparams": b"weights",
        "model/inference.yml": b"Global:\n  model_name: test\n",
    }
    archive = tmp_path / "model.tar"
    _write_archive(archive, members)

    inspected = tool._inspect_archive(archive, _profile(archive, members))

    assert len(inspected) == 4


def test_archive_inspection_rejects_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar"
    with tarfile.open(archive, mode="w") as handle:
        member = tarfile.TarInfo("../escape")
        member.size = 1
        handle.addfile(member, io.BytesIO(b"x"))
    profile = tool.ArtifactProfile(
        candidate_id="OCR-L0",
        artifact_id="test",
        archive_relative_path=archive.name,
        archive_sha256=tool._sha256(archive),
        top_level="model",
        member_sizes={},
        inference_yml_sha256="0" * 64,
    )

    with pytest.raises(tool.LatinOcrToolError, match="unsafe path"):
        tool._inspect_archive(archive, profile)


def test_archive_inspection_rejects_links(tmp_path: Path) -> None:
    archive = tmp_path / "link.tar"
    with tarfile.open(archive, mode="w") as handle:
        directory = tarfile.TarInfo("model/")
        directory.type = tarfile.DIRTYPE
        handle.addfile(directory)
        member = tarfile.TarInfo("model/link")
        member.type = tarfile.SYMTYPE
        member.linkname = "elsewhere"
        handle.addfile(member)
    profile = tool.ArtifactProfile(
        candidate_id="OCR-L0",
        artifact_id="test",
        archive_relative_path=archive.name,
        archive_sha256=tool._sha256(archive),
        top_level="model",
        member_sizes={},
        inference_yml_sha256="0" * 64,
    )

    with pytest.raises(tool.LatinOcrToolError, match="link or special"):
        tool._inspect_archive(archive, profile)


def test_model_inventory_is_content_bound_and_rejects_extra_files(
    tmp_path: Path,
) -> None:
    members = {
        "model/inference.json": b"{}",
        "model/inference.pdiparams": b"weights",
        "model/inference.yml": b"Global:\n  model_name: test\n",
    }
    archive = tmp_path / "model.tar"
    _write_archive(archive, members)
    profile = _profile(archive, members)
    model = tmp_path / "extracted"
    model.mkdir()
    for name, payload in members.items():
        (model / name.removeprefix("model/")).write_bytes(payload)

    first = tool._model_inventory(model, profile)
    second = tool._model_inventory(model, profile)

    assert first == second
    assert first.startswith("sha256:")
    (model / "extra.bin").write_bytes(b"unexpected")
    with pytest.raises(tool.LatinOcrToolError, match="inventory changed"):
        tool._model_inventory(model, profile)


def test_model_inventory_rejects_empty_extra_directory(tmp_path: Path) -> None:
    members = {
        "model/inference.json": b"{}",
        "model/inference.pdiparams": b"weights",
        "model/inference.yml": b"Global:\n  model_name: test\n",
    }
    archive = tmp_path / "model.tar"
    _write_archive(archive, members)
    profile = _profile(archive, members)
    model = tmp_path / "extracted"
    model.mkdir()
    for name, payload in members.items():
        (model / name.removeprefix("model/")).write_bytes(payload)
    (model / "unexpected").mkdir()

    with pytest.raises(tool.LatinOcrToolError, match="extra directory"):
        tool._model_inventory(model, profile)


def test_effective_authorization_pins_exact_w5_pair_and_empty_network_allowlist() -> None:
    authorization = tool._load_authorization()

    assert authorization["allowed_network_actions"] == []
    assert authorization["allowed_runtime"]["network_access"] is False
    assert {item["candidate_id"] for item in authorization["allowed_artifacts"]}.issuperset(
        tool.PROFILES
    )


def test_tool_paths_never_use_prohibited_b_drive() -> None:
    paths = (
        tool.ARTIFACT_ROOT,
        tool.RUNTIME_ROOT,
        tool.EVIDENCE_PATH,
        tool.WORKER_PATH,
    )

    assert all(path.drive.upper() != "B:" for path in paths)
