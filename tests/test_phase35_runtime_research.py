from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pytest

from tools import phase35_runtime_research as runtime


def test_authorized_context_is_exact_and_non_runtime() -> None:
    authorization, proposal, acceptance = runtime.load_authorized_context()

    assert authorization["authorization_id"] == "D-P3.5-RUNTIME-RESEARCH"
    assert authorization["implementation_authorized"] is False
    assert authorization["limits"]["runtime_constructors_or_inference"] is False
    assert proposal["proposal_id"] == "P3.5-RUNTIME-REVIEW-PROPOSAL-R0"
    assert acceptance["status"] == "accepted"


def test_authorized_context_rejects_widened_package(tmp_path: Path) -> None:
    authorization = json.loads(runtime.DEFAULT_AUTHORIZATION.read_text(encoding="utf-8"))
    authorization["allowed_direct_packages"].append(
        {"name": "unapproved", "version": "1.0"}
    )
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(runtime.RuntimeResearchError):
        runtime.load_authorized_context(authorization_path=path)


def test_root_must_match_external_authorized_root(tmp_path: Path) -> None:
    authorization, _proposal, _acceptance = runtime.load_authorized_context()

    with pytest.raises(runtime.RuntimeResearchError):
        runtime.validate_root(tmp_path, authorization)


def _write_distribution(
    site_packages: Path,
    *,
    name: str,
    version: str,
    native: bool = False,
) -> None:
    package_dir = site_packages / name.lower()
    package_dir.mkdir(parents=True, exist_ok=True)
    module = package_dir / "__init__.py"
    module.write_text("", encoding="utf-8")
    dist_info = site_packages / f"{name}-{version}.dist-info"
    dist_info.mkdir()
    metadata = dist_info / "METADATA"
    metadata.write_text(
        f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n"
        "License-Expression: Apache-2.0\n",
        encoding="utf-8",
    )
    files = [module, metadata]
    if native:
        native_file = package_dir / "runtime.pyd"
        native_file.write_bytes(b"synthetic-native")
        files.append(native_file)
    record = dist_info / "RECORD"
    with record.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for file_path in files:
            writer.writerow([file_path.relative_to(site_packages).as_posix(), "", ""])
        writer.writerow([record.relative_to(site_packages).as_posix(), "", ""])


def test_inventory_hashes_native_files_without_loading_them(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    _write_distribution(
        site_packages, name="paddlepaddle", version="3.3.1", native=True
    )

    packages, native = runtime._distribution_inventory(site_packages)

    assert packages[0]["name"] == "paddlepaddle"
    assert packages[0]["native_file_count"] == 1
    assert packages[0]["direct"] is True
    assert native[0]["path"] == "paddlepaddle/runtime.pyd"
    assert len(native[0]["sha256"]) == 64


def test_sbom_marks_every_component_runtime_unauthorized() -> None:
    packages = [
        {
            "direct": True,
            "name": "regex",
            "record_sha256": "A" * 64,
            "version": "2026.7.19",
        }
    ]
    native = [
        {
            "distribution": "regex",
            "path": "regex/runtime.pyd",
            "sha256": "B" * 64,
        }
    ]

    sbom = runtime.build_sbom(packages, native)

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert all(
        {item["name"]: item["value"] for item in component["properties"]}[
            "hcam:runtimeAuthorized"
        ]
        == "false"
        for component in sbom["components"]
    )


def test_import_check_requires_exact_versions_and_zero_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "venv" / "Scripts").mkdir(parents=True)
    output = runtime.IMPORT_RESULT_PREFIX + json.dumps(
        {
            "constructors_called": False,
            "imports": {
                "PIL": "12.3.0",
                "paddle": "3.3.1",
                "paddleocr": "3.7.0",
                "regex": "2026.7.19",
            },
            "model_font_or_media_loaded": False,
            "network_attempt_count": 0,
            "network_guard": "socket_creation_and_resolution_denied",
            "status": "pass",
        }
    )

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, stdout=output, stderr="")

    monkeypatch.setattr(runtime, "_run", fake_run)

    result = runtime.run_import_check(tmp_path)

    assert result["status"] == "pass"
    assert result["constructors_called"] is False
    assert (tmp_path / "evidence" / "import-check.json").is_file()


def test_safe_environment_removes_proxy_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://unapproved.invalid")
    monkeypatch.setenv("NO_PROXY", "localhost")

    environment = runtime._safe_environment(tmp_path)

    assert not any(key.lower().endswith("_proxy") for key in environment)
    assert environment["UV_NO_CONFIG"] == "1"
    assert environment["UV_PYTHON_DOWNLOADS"] == "never"
