from __future__ import annotations

import io
import struct
import tarfile
from pathlib import Path

import pytest

from tools import phase35_artifact_inspect as inspect


def test_safe_tar_is_inventoried_without_extraction(tmp_path: Path) -> None:
    archive_path = tmp_path / "model.tar"
    with tarfile.open(archive_path, "w") as archive:
        info = tarfile.TarInfo("model/inference.json")
        payload = b"{}"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    result = inspect.inspect_tar(archive_path)

    assert result["member_count"] == 1
    assert result["file_count"] == 1
    assert result["unpacked_bytes"] == 2
    assert result["extracted"] is False
    assert not (tmp_path / "model").exists()


def test_tar_link_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.tar"
    with tarfile.open(archive_path, "w") as archive:
        info = tarfile.TarInfo("model/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../outside"
        archive.addfile(info)

    with pytest.raises(inspect.InspectionError, match="link or special"):
        inspect.inspect_tar(archive_path)


def _font_payload(*tags: str) -> bytes:
    directory_end = 12 + (len(tags) * 16)
    payload = bytearray(directory_end + len(tags))
    payload[:4] = b"\x00\x01\x00\x00"
    payload[4:6] = struct.pack(">H", len(tags))
    for index, tag in enumerate(tags):
        start = 12 + (index * 16)
        payload[start : start + 16] = struct.pack(
            ">4sIII", tag.encode(), 0, directory_end + index, 1
        )
    return bytes(payload)


def test_sfnt_font_tables_are_bounded(tmp_path: Path) -> None:
    font = tmp_path / "font.ttf"
    font.write_bytes(_font_payload("cmap", "head", "name", "fvar"))

    result = inspect.inspect_font(font)

    assert result["table_count"] == 4
    assert result["variable_font"] is True
    assert result["executed"] is False


def test_sfnt_out_of_bounds_table_is_rejected(tmp_path: Path) -> None:
    font = tmp_path / "font.ttf"
    payload = bytearray(_font_payload("cmap", "head", "name"))
    payload[20:24] = struct.pack(">I", len(payload) + 1)
    font.write_bytes(payload)

    with pytest.raises(inspect.InspectionError, match="file bounds"):
        inspect.inspect_font(font)
