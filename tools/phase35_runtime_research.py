#!/usr/bin/env python3
"""Build bounded P3.5 Python runtime evidence outside the Git worktree."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from email.parser import Parser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTHORIZATION = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-research-authorization.json"
)
DEFAULT_PROPOSAL = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-review-proposal.json"
)
DEFAULT_ACCEPTANCE = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-review-acceptance.json"
)
DEFAULT_PUBLISH_ROOT = ROOT / "contracts" / "phase-3"
EXPECTED_PACKAGE_DIGEST = (
    "54B02B80169604904C9945C1C6E692500CA8AA79253EEC27A63B4C4DB00B395C"
)
EXPECTED_PROPOSAL_SHA256 = (
    "3788950DFA0477DE59B1B135AA1AACDA7584A368C1219B3266F0265E6174A5F1"
)
EXPECTED_DIRECT_PACKAGES = {
    "paddleocr": "3.7.0",
    "paddlepaddle": "3.3.1",
    "pillow": "12.3.0",
    "regex": "2026.7.19",
}
EXPECTED_SOURCE_HOSTS = {"files.pythonhosted.org", "pypi.org"}
NATIVE_SUFFIXES = {".dll", ".dylib", ".pyd", ".so"}
MODEL_OR_MEDIA_SUFFIXES = {
    ".avi",
    ".jpeg",
    ".jpg",
    ".mkv",
    ".mp4",
    ".onnx",
    ".pdiparams",
    ".pdmodel",
    ".png",
    ".traineddata",
    ".ttf",
    ".otf",
}
IMPORT_RESULT_PREFIX = "HCAM_IMPORT_RESULT="
EXPECTED_PACKAGED_SENSITIVE_ASSETS = {
    "networkx": (
        "networkx/drawing/tests/baseline/test_display_complex.png",
        "networkx/drawing/tests/baseline/test_display_empty_graph.png",
        "networkx/drawing/tests/baseline/test_display_house_with_colors.png",
        "networkx/drawing/tests/baseline/test_display_labels_and_colors.png",
        "networkx/drawing/tests/baseline/test_display_shortest_path.png",
        "networkx/drawing/tests/baseline/test_house_with_colors.png",
    )
}


class RuntimeResearchError(RuntimeError):
    """The authorization, environment, or evidence boundary was violated."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeResearchError(f"{path.name} must contain a JSON object")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _canonical_name(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def load_authorized_context(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    proposal_path: Path = DEFAULT_PROPOSAL,
    acceptance_path: Path = DEFAULT_ACCEPTANCE,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorization = _read_json(authorization_path)
    proposal = _read_json(proposal_path)
    acceptance = _read_json(acceptance_path)
    packages = authorization.get("allowed_direct_packages")
    direct = (
        {
            _canonical_name(str(item.get("name"))): str(item.get("version"))
            for item in packages
            if isinstance(item, dict)
        }
        if isinstance(packages, list)
        else {}
    )
    limits = authorization.get("limits")
    if (
        authorization.get("authorization_id") != "D-P3.5-RUNTIME-RESEARCH"
        or authorization.get("status") != "owner_approved_restricted"
        or authorization.get("authorized_by") != "mayank-admin"
        or authorization.get("accepted_evidence_package_digest")
        != EXPECTED_PACKAGE_DIGEST
        or authorization.get("proposal_sha256") != EXPECTED_PROPOSAL_SHA256
        or _sha256(proposal_path) != EXPECTED_PROPOSAL_SHA256
        or acceptance.get("evidence_package_digest") != EXPECTED_PACKAGE_DIGEST
        or acceptance.get("status") != "accepted"
        or direct != EXPECTED_DIRECT_PACKAGES
        or set(authorization.get("allowed_source_hosts", []))
        != EXPECTED_SOURCE_HOSTS
        or authorization.get("implementation_authorized") is not False
        or authorization.get("dependency_or_lockfile_change_authorized") is not False
        or authorization.get("tesseract_runtime_authorized") is not False
        or not isinstance(limits, dict)
        or limits.get("python_version") != "3.12.13"
        or limits.get("binary_wheels_only") is not True
        or limits.get("package_source_builds") is not False
        or limits.get("repository_environment_changes") is not False
        or limits.get("import_network_access") is not False
        or limits.get("runtime_constructors_or_inference") is not False
    ):
        raise RuntimeResearchError(
            "runtime research authorization is missing, changed, or widened"
        )
    return authorization, proposal, acceptance


def validate_root(root: Path, authorization: dict[str, Any]) -> Path:
    limits = authorization["limits"]
    expected = Path(str(limits["external_quarantine_root"]))
    resolved = root.resolve(strict=False)
    expected_resolved = expected.resolve(strict=False)
    if os.path.normcase(str(resolved)) != os.path.normcase(str(expected_resolved)):
        raise RuntimeResearchError("root does not match the authorized quarantine root")
    if _inside(resolved, ROOT.resolve(strict=True)):
        raise RuntimeResearchError("runtime quarantine must be outside the Git worktree")
    return resolved


def _safe_environment(root: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.lower().endswith("_proxy")
    }
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "1",
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "PYTHONNOUSERSITE": "1",
            "TEMP": str(root / "temp"),
            "TMP": str(root / "temp"),
            "TRANSFORMERS_OFFLINE": "1",
            "UV_CACHE_DIR": str(root / "uv-cache"),
            "UV_NO_CONFIG": "1",
            "UV_PYTHON_DOWNLOADS": "never",
        }
    )
    return environment


def _run(
    command: list[str],
    *,
    environment: dict[str, str],
    timeout: int,
    accepted_exit_codes: set[int] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )
    accepted = accepted_exit_codes or {0}
    if completed.returncode not in accepted:
        detail = (completed.stderr or completed.stdout)[-4000:]
        raise RuntimeResearchError(
            f"command failed with exit {completed.returncode}: {detail}"
        )
    return completed


def _venv_python(root: Path) -> Path:
    return root / "venv" / "Scripts" / "python.exe"


def _find_installed_python_312() -> Path:
    candidates: list[Path] = []
    configured = os.environ.get("UV_PYTHON_INSTALL_DIR")
    if configured:
        candidates.extend(Path(configured).glob("cpython-3.12-*/python.exe"))
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.extend(
            (Path(appdata) / "uv" / "python").glob(
                "cpython-3.12-windows-x86_64-none/python.exe"
            )
        )
    for candidate in sorted(set(candidates)):
        if candidate.is_file():
            return candidate.resolve(strict=True)
    raise RuntimeResearchError("installed uv-managed CPython 3.12 was not found")


def prepare_environment(root: Path, authorization: dict[str, Any]) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "temp").mkdir(parents=True, exist_ok=True)
    marker_path = root / "authorization-marker.json"
    marker = {
        "authorization_id": authorization["authorization_id"],
        "proposal_sha256": authorization["proposal_sha256"],
        "accepted_evidence_package_digest": EXPECTED_PACKAGE_DIGEST,
    }
    if marker_path.exists() and _read_json(marker_path) != marker:
        raise RuntimeResearchError("existing quarantine marker does not match")
    _write_json(marker_path, marker)
    environment = _safe_environment(root)
    source_python = _find_installed_python_312()
    version = _run(
        [str(source_python), "-I", "-c", "import sys; print(sys.version.split()[0])"],
        environment=environment,
        timeout=30,
    ).stdout.strip()
    if version != "3.12.13":
        raise RuntimeResearchError(f"expected CPython 3.12.13, found {version}")
    venv_python = _venv_python(root)
    if not venv_python.exists():
        _run(
            [
                str(source_python),
                "-I",
                "-m",
                "venv",
                "--without-pip",
                str(root / "venv"),
            ],
            environment=environment,
            timeout=600,
        )
    direct = [
        f"{item['name']}=={item['version']}"
        for item in authorization["allowed_direct_packages"]
    ]
    wheelhouse = root / "wheels"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    download = _run(
        [
            str(source_python),
            "-I",
            "-m",
            "pip",
            "download",
            "--dest",
            str(wheelhouse),
            "--index-url",
            "https://pypi.org/simple",
            "--only-binary=:all:",
            "--no-cache-dir",
            "--disable-pip-version-check",
            "--progress-bar",
            "off",
            *direct,
        ],
        environment=environment,
        timeout=3600,
    )
    wheel_files = sorted(wheelhouse.iterdir())
    if not wheel_files or any(
        not path.is_file() or path.suffix.lower() != ".whl" for path in wheel_files
    ):
        raise RuntimeResearchError("wheelhouse contains a missing or non-wheel artifact")
    wheel_bytes = sum(path.stat().st_size for path in wheel_files)
    if wheel_bytes > int(authorization["limits"]["cumulative_package_bytes"]):
        raise RuntimeResearchError("resolved wheel closure exceeds the authorized size")
    wheels = [
        {"bytes": path.stat().st_size, "filename": path.name, "sha256": _sha256(path)}
        for path in wheel_files
    ]
    _write_json(root / "evidence" / "wheelhouse.json", {"wheels": wheels})
    install = _run(
        [
            str(source_python),
            "-I",
            "-m",
            "pip",
            "--python",
            str(venv_python),
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "--only-binary=:all:",
            "--no-cache-dir",
            "--no-compile",
            "--disable-pip-version-check",
            "--progress-bar",
            "off",
            *direct,
        ],
        environment=environment,
        timeout=3600,
    )
    check = _run(
        [
            str(source_python),
            "-I",
            "-m",
            "pip",
            "--python",
            str(venv_python),
            "check",
        ],
        environment=environment,
        timeout=300,
    )
    return {
        "direct_packages": direct,
        "download_stdout_tail": download.stdout[-2000:],
        "install_stderr_tail": install.stderr[-2000:],
        "python_executable": str(venv_python),
        "python_version": version,
        "pip_check": check.stdout.strip(),
        "wheel_bytes": wheel_bytes,
        "wheel_count": len(wheels),
    }


def _distribution_inventory(site_packages: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packages: list[dict[str, Any]] = []
    native_files: list[dict[str, Any]] = []
    for dist_info in sorted(site_packages.glob("*.dist-info"), key=lambda path: path.name.lower()):
        metadata_path = dist_info / "METADATA"
        if not metadata_path.is_file():
            continue
        metadata = Parser().parsestr(metadata_path.read_text(encoding="utf-8", errors="replace"))
        name = metadata.get("Name", dist_info.name)
        version = metadata.get("Version", "UNKNOWN")
        record_path = dist_info / "RECORD"
        record_sha256 = _sha256(record_path) if record_path.is_file() else None
        installed_files = 0
        installed_bytes = 0
        sensitive_assets: list[str] = []
        native_for_package = 0
        if record_path.is_file():
            with record_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                for row in csv.reader(handle):
                    if not row:
                        continue
                    relative = Path(row[0].replace("/", os.sep))
                    candidate = (site_packages / relative).resolve(strict=False)
                    if not _inside(candidate, site_packages.resolve(strict=True)) or not candidate.is_file():
                        continue
                    installed_files += 1
                    installed_bytes += candidate.stat().st_size
                    suffix = candidate.suffix.lower()
                    relative_name = candidate.relative_to(site_packages).as_posix()
                    if suffix in MODEL_OR_MEDIA_SUFFIXES:
                        sensitive_assets.append(relative_name)
                    if suffix in NATIVE_SUFFIXES:
                        native_for_package += 1
                        native_files.append(
                            {
                                "bytes": candidate.stat().st_size,
                                "distribution": name,
                                "path": relative_name,
                                "sha256": _sha256(candidate),
                            }
                        )
        license_expression = metadata.get("License-Expression")
        license_text = metadata.get("License")
        license_classifiers = [
            value
            for value in metadata.get_all("Classifier", [])
            if value.startswith("License ::")
        ]
        packages.append(
            {
                "direct": _canonical_name(name) in EXPECTED_DIRECT_PACKAGES,
                "installed_bytes": installed_bytes,
                "installed_file_count": installed_files,
                "license": {
                    "classifiers": license_classifiers,
                    "expression": license_expression,
                    "raw": license_text,
                },
                "name": name,
                "native_file_count": native_for_package,
                "record_sha256": record_sha256,
                "requires_dist": metadata.get_all("Requires-Dist", []),
                "sensitive_asset_paths": sorted(sensitive_assets),
                "version": version,
            }
        )
    return packages, sorted(native_files, key=lambda item: item["path"])


def _license_name(package: dict[str, Any]) -> str:
    license_evidence = package["license"]
    if license_evidence.get("expression"):
        return str(license_evidence["expression"])
    raw = license_evidence.get("raw")
    if raw and len(str(raw)) <= 256:
        return " ".join(str(raw).split())
    classifiers = license_evidence.get("classifiers", [])
    if classifiers:
        return " | ".join(str(item) for item in classifiers)
    return "SEE-INSTALLED-METADATA" if raw else "UNDECLARED"


def build_license_review(packages: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for package in packages:
        evidence = package["license"]
        raw = evidence.get("raw")
        searchable = " ".join(
            (
                str(evidence.get("expression") or ""),
                str(raw or ""),
                " ".join(str(item) for item in evidence.get("classifiers", [])),
            )
        ).upper()
        review_flags = [
            flag
            for flag in ("GPL", "LGPL", "MPL", "PUBLIC DOMAIN", "DUAL LICENSE")
            if flag in searchable
        ]
        records.append(
            {
                "classifiers": evidence.get("classifiers", []),
                "license_expression": evidence.get("expression"),
                "license_summary": _license_name(package),
                "name": package["name"],
                "raw_license_sha256": hashlib.sha256(str(raw).encode()).hexdigest().upper()
                if raw
                else None,
                "review_flags": review_flags,
                "version": package["version"],
            }
        )
    missing = [item["name"] for item in records if item["license_summary"] == "UNDECLARED"]
    return {
        "authorization_id": "D-P3.5-RUNTIME-RESEARCH",
        "contract_format": "hcam.phase3.p3_5.runtime-license-review.v1",
        "evidence_id": "P3.5-RUNTIME-LICENSE-REVIEW-R1",
        "implementation_or_redistribution_authorized": False,
        "legal_approval_performed": False,
        "metadata_missing_count": len(missing),
        "package_count": len(records),
        "packages": records,
        "review_note": "Package metadata is inventoried; flagged licenses require normal product redistribution review before deployment.",
        "status": "metadata_complete_legal_review_deferred"
        if not missing
        else "metadata_incomplete",
    }


def build_sbom(
    packages: list[dict[str, Any]],
    native_files: list[dict[str, Any]],
    wheels: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    for package in packages:
        components.append(
            {
                "bom-ref": f"pkg:pypi/{_canonical_name(package['name'])}@{package['version']}",
                "hashes": [
                    {
                        "alg": "SHA-256",
                        "content": package["record_sha256"] or "0" * 64,
                    }
                ],
                "licenses": [{"license": {"name": _license_name(package)}}],
                "name": package["name"],
                "properties": [
                    {"name": "hcam:direct", "value": str(package["direct"]).lower()},
                    {
                        "name": "hcam:distInfoRecordSha256",
                        "value": package["record_sha256"] or "unavailable",
                    },
                    {"name": "hcam:runtimeAuthorized", "value": "false"},
                ],
                "purl": f"pkg:pypi/{_canonical_name(package['name'])}@{package['version']}",
                "type": "library",
                "version": package["version"],
            }
        )
    for wheel in wheels or []:
        components.append(
            {
                "bom-ref": f"hcam:p3.5:wheel:{wheel['sha256']}",
                "hashes": [{"alg": "SHA-256", "content": wheel["sha256"]}],
                "name": wheel["filename"],
                "properties": [
                    {"name": "hcam:bytes", "value": str(wheel["bytes"])},
                    {"name": "hcam:runtimeAuthorized", "value": "false"},
                ],
                "type": "file",
            }
        )
    for native in native_files:
        components.append(
            {
                "bom-ref": f"hcam:p3.5:native:{native['sha256']}",
                "hashes": [{"alg": "SHA-256", "content": native["sha256"]}],
                "name": native["path"],
                "properties": [
                    {"name": "hcam:distribution", "value": native["distribution"]},
                    {"name": "hcam:runtimeAuthorized", "value": "false"},
                ],
                "type": "file",
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "components": components,
        "metadata": {
            "properties": [
                {"name": "hcam:authorizationId", "value": "D-P3.5-RUNTIME-RESEARCH"},
                {"name": "hcam:modelLoadingPerformed", "value": "false"},
                {"name": "hcam:implementationAuthorized", "value": "false"},
            ]
        },
        "specVersion": "1.6",
        "version": 1,
    }


def inspect_environment(root: Path) -> dict[str, Any]:
    site_packages = root / "venv" / "Lib" / "site-packages"
    if not site_packages.is_dir():
        raise RuntimeResearchError("isolated site-packages does not exist")
    packages, native_files = _distribution_inventory(site_packages)
    wheelhouse = _read_json(root / "evidence" / "wheelhouse.json")
    wheels = wheelhouse.get("wheels")
    if not isinstance(wheels, list) or not wheels:
        raise RuntimeResearchError("exact wheelhouse evidence is missing")
    observed = {
        _canonical_name(str(item["name"])): str(item["version"])
        for item in packages
        if item["direct"]
    }
    if observed != EXPECTED_DIRECT_PACKAGES:
        raise RuntimeResearchError("installed direct package set changed")
    report = {
        "direct_packages": observed,
        "implementation_authorized": False,
        "model_font_or_media_loading_performed": False,
        "native_file_count": len(native_files),
        "native_files": native_files,
        "package_count": len(packages),
        "packages": packages,
        "status": "pass",
        "tesseract_runtime_present": False,
    }
    _write_json(root / "evidence" / "installed-environment.json", report)
    _write_json(
        root / "evidence" / "runtime-sbom.cdx.json",
        build_sbom(packages, native_files, wheels),
    )
    return report


def run_import_check(root: Path) -> dict[str, Any]:
    code = r'''
import importlib
import importlib.metadata
import json
import socket
import ssl

attempts = []

def denied(*args, **kwargs):
    attempts.append(repr(args[:2]))
    raise RuntimeError("network access denied by H-CAM P3.5 import guard")

class DeniedSocket(socket.socket):
    def __new__(cls, *args, **kwargs):
        attempts.append(repr(args[:2]))
        raise RuntimeError("socket creation denied by H-CAM P3.5 import guard")

socket.socket = DeniedSocket
socket.create_connection = denied
socket.getaddrinfo = denied

modules = {}
for module_name, distribution_name in (
    ("paddle", "paddlepaddle"),
    ("paddleocr", "paddleocr"),
    ("PIL", "Pillow"),
    ("regex", "regex"),
):
    importlib.import_module(module_name)
    modules[module_name] = importlib.metadata.version(distribution_name)

print("HCAM_IMPORT_RESULT=" + json.dumps({
    "blocked_network_attempts": attempts,
    "constructors_called": False,
    "imports": modules,
    "model_font_or_media_loaded": False,
    "network_access_performed": False,
    "network_attempt_count": len(attempts),
    "network_guard": "socket_creation_and_resolution_denied",
    "status": "pass",
}, sort_keys=True))
'''
    completed = _run(
        [str(_venv_python(root)), "-I", "-c", code],
        environment=_safe_environment(root),
        timeout=600,
    )
    result_line = next(
        (
            line[len(IMPORT_RESULT_PREFIX) :]
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(IMPORT_RESULT_PREFIX)
        ),
        None,
    )
    if result_line is None:
        raise RuntimeResearchError("import check did not emit a result record")
    result = json.loads(result_line)
    if (
        result.get("status") != "pass"
        or result.get("constructors_called") is not False
        or result.get("model_font_or_media_loaded") is not False
        or result.get("network_access_performed") is not False
        or result.get("network_attempt_count")
        != len(result.get("blocked_network_attempts", []))
        or result.get("network_guard")
        != "socket_creation_and_resolution_denied"
        or result.get("imports")
        != {
            "PIL": "12.3.0",
            "paddle": "3.3.1",
            "paddleocr": "3.7.0",
            "regex": "2026.7.19",
        }
    ):
        raise RuntimeResearchError(
            "network-denied direct imports did not pass: "
            + json.dumps(result, sort_keys=True)
        )
    result["stderr_tail"] = completed.stderr[-2000:]
    _write_json(root / "evidence" / "import-check.json", result)
    return result


def run_vulnerability_audit(root: Path) -> dict[str, Any]:
    site_packages = root / "venv" / "Lib" / "site-packages"
    completed = _run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--path",
            str(site_packages),
            "--format",
            "json",
            "--progress-spinner",
            "off",
            "--desc",
            "off",
            "--aliases",
            "on",
            "--strict",
            "--cache-dir",
            str(root / "pip-audit-cache"),
            "--timeout",
            "30",
        ],
        environment=_safe_environment(root),
        timeout=1800,
        accepted_exit_codes={0, 1},
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeResearchError("pip-audit did not emit JSON") from exc
    dependencies = payload.get("dependencies", []) if isinstance(payload, dict) else []
    vulnerability_count = sum(
        len(item.get("vulns", []))
        for item in dependencies
        if isinstance(item, dict) and isinstance(item.get("vulns"), list)
    )
    result = {
        "audit_exit_code": completed.returncode,
        "dependency_count": len(dependencies),
        "raw_result": payload,
        "status": "pass_no_known_vulnerabilities"
        if vulnerability_count == 0 and completed.returncode == 0
        else "review_required",
        "vulnerability_count": vulnerability_count,
    }
    _write_json(root / "evidence" / "vulnerability-audit.json", result)
    return result


def _defender_executable() -> Path:
    candidates = sorted(
        (Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft" / "Windows Defender" / "Platform").glob("*/MpCmdRun.exe"),
        reverse=True,
    )
    if not candidates:
        raise RuntimeResearchError("Microsoft Defender command-line scanner not found")
    return candidates[0]


def _defender_versions(environment: dict[str, str]) -> dict[str, Any]:
    completed = _run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-MpComputerStatus | Select-Object AMEngineVersion,AntivirusSignatureVersion,AntivirusSignatureLastUpdated,RealTimeProtectionEnabled | ConvertTo-Json -Compress",
        ],
        environment=environment,
        timeout=60,
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeResearchError("Microsoft Defender status did not return an object")
    return value


def run_defender_scan(root: Path) -> dict[str, Any]:
    environment = _safe_environment(root)
    versions = _defender_versions(environment)
    completed = _run(
        [
            str(_defender_executable()),
            "-Scan",
            "-ScanType",
            "3",
            "-File",
            str(root),
            "-DisableRemediation",
        ],
        environment=environment,
        timeout=3600,
    )
    result = {
        "engine": "Microsoft Defender",
        "engine_version": versions.get("AMEngineVersion"),
        "exit_code": completed.returncode,
        "finding": "no_threats_found",
        "output_tail": (completed.stdout + completed.stderr)[-4000:],
        "real_time_protection_enabled": versions.get("RealTimeProtectionEnabled"),
        "signature_last_updated": versions.get("AntivirusSignatureLastUpdated"),
        "signature_version": versions.get("AntivirusSignatureVersion"),
        "status": "pass",
    }
    _write_json(root / "evidence" / "defender-scan.json", result)
    return result


def finalize_existing(root: Path) -> dict[str, Any]:
    evidence_root = root / "evidence"
    wheelhouse = _read_json(evidence_root / "wheelhouse.json")
    inventory = _read_json(evidence_root / "installed-environment.json")
    audit = _read_json(evidence_root / "vulnerability-audit.json")
    imports = _read_json(evidence_root / "import-check.json")
    defender = _read_json(evidence_root / "defender-scan.json")
    wheels = wheelhouse.get("wheels")
    packages = inventory.get("packages")
    if not isinstance(wheels, list) or not isinstance(packages, list):
        raise RuntimeResearchError("runtime wheel or package evidence is incomplete")
    missing_licenses = [
        str(package.get("name"))
        for package in packages
        if isinstance(package, dict) and _license_name(package) == "UNDECLARED"
    ]
    packaged_sensitive_assets = {
        str(package.get("name")): tuple(package.get("sensitive_asset_paths", []))
        for package in packages
        if isinstance(package, dict) and package.get("sensitive_asset_paths")
    }
    if (
        len(wheels) != 67
        or sum(int(item["bytes"]) for item in wheels if isinstance(item, dict))
        != 213980084
        or inventory.get("package_count") != 67
        or inventory.get("native_file_count") != 185
        or inventory.get("status") != "pass"
        or audit.get("status") != "pass_no_known_vulnerabilities"
        or audit.get("vulnerability_count") != 0
        or imports.get("status") != "pass"
        or imports.get("network_access_performed") is not False
        or imports.get("constructors_called") is not False
        or imports.get("model_font_or_media_loaded") is not False
        or defender.get("status") != "pass"
        or defender.get("finding") != "no_threats_found"
        or missing_licenses
        or packaged_sensitive_assets != EXPECTED_PACKAGED_SENSITIVE_ASSETS
    ):
        raise RuntimeResearchError(
            "existing runtime research evidence is incomplete or requires remediation"
        )
    result = {
        "artifact_or_model_loading_performed": False,
        "authorization_id": "D-P3.5-RUNTIME-RESEARCH",
        "defender": {
            "exit_code": defender["exit_code"],
            "finding": defender["finding"],
            "status": defender["status"],
        },
        "dependency_or_lockfile_change_performed": False,
        "implementation_authorized": False,
        "imports": {
            "blocked_network_attempts": imports["blocked_network_attempts"],
            "imports": imports["imports"],
            "network_access_performed": False,
            "network_attempt_count": imports["network_attempt_count"],
            "status": "pass_with_all_network_attempts_blocked",
        },
        "inventory": {
            "license_metadata_missing_count": 0,
            "native_file_count": inventory["native_file_count"],
            "packaged_sensitive_asset_count": sum(
                len(paths) for paths in packaged_sensitive_assets.values()
            ),
            "package_count": inventory["package_count"],
            "wheel_bytes": sum(int(item["bytes"]) for item in wheels),
            "wheel_count": len(wheels),
        },
        "runtime_constructors_or_inference_performed": False,
        "status": "complete_pass_final_owner_review_pending",
        "tesseract_runtime_present": False,
        "vulnerability_audit": {
            "dependency_count": audit["dependency_count"],
            "status": audit["status"],
            "vulnerability_count": audit["vulnerability_count"],
        },
    }
    _write_json(evidence_root / "runtime-research-result.json", result)
    return result


def publish_repository_evidence(root: Path, output_root: Path) -> dict[str, Any]:
    result = finalize_existing(root)
    evidence_root = root / "evidence"
    wheelhouse = _read_json(evidence_root / "wheelhouse.json")
    inventory = _read_json(evidence_root / "installed-environment.json")
    audit = _read_json(evidence_root / "vulnerability-audit.json")
    imports = _read_json(evidence_root / "import-check.json")
    defender = _read_json(evidence_root / "defender-scan.json")
    sbom = _read_json(evidence_root / "runtime-sbom.cdx.json")
    wheels = wheelhouse["wheels"]
    packages = inventory["packages"]
    external_files = (
        "wheelhouse.json",
        "installed-environment.json",
        "runtime-sbom.cdx.json",
        "vulnerability-audit.json",
        "import-check.json",
        "defender-scan.json",
        "runtime-research-result.json",
    )
    evidence_hashes = {
        name: _sha256(evidence_root / name) for name in external_files
    }
    direct_packages = [
        {"name": item["name"], "version": item["version"]}
        for item in packages
        if item.get("direct") is True
    ]
    package_versions = [
        {"name": item["name"], "version": item["version"]}
        for item in packages
    ]
    packaged_sensitive_assets = [
        {
            "name": item["name"],
            "paths": item["sensitive_asset_paths"],
            "version": item["version"],
        }
        for item in packages
        if item.get("sensitive_asset_paths")
    ]
    published_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    evidence = {
        "accepted_artifact_evidence_id": "P3.5-EXACT-ARTIFACT-REVIEW-R1",
        "accepted_artifact_package_digest": EXPECTED_PACKAGE_DIGEST,
        "authorization_id": "D-P3.5-RUNTIME-RESEARCH",
        "contract_format": "hcam.phase3.p3_5.runtime-research-evidence.v1",
        "defender_scan": {
            "engine_version": defender.get("engine_version"),
            "exit_code": defender["exit_code"],
            "finding": defender["finding"],
            "signature_version": defender.get("signature_version"),
        },
        "dependency_or_lockfile_change_performed": False,
        "direct_packages": sorted(direct_packages, key=lambda item: item["name"].lower()),
        "evidence_id": "P3.5-RUNTIME-RESEARCH-EVIDENCE-R1",
        "external_evidence_sha256": evidence_hashes,
        "external_quarantine_root": str(root),
        "implementation_authorized": False,
        "import_check": {
            "blocked_network_attempts": imports["blocked_network_attempts"],
            "imports": imports["imports"],
            "model_font_or_media_loaded": False,
            "network_access_performed": False,
            "runtime_constructors_or_inference_performed": False,
            "status": "pass_with_all_network_attempts_blocked",
        },
        "inventory": {
            "license_metadata_missing_count": 0,
            "native_file_count": inventory["native_file_count"],
            "packaged_sensitive_asset_count": sum(
                len(item["paths"]) for item in packaged_sensitive_assets
            ),
            "packaged_sensitive_assets": packaged_sensitive_assets,
            "package_count": inventory["package_count"],
            "packages": sorted(package_versions, key=lambda item: item["name"].lower()),
            "wheel_bytes": sum(int(item["bytes"]) for item in wheels),
            "wheel_count": len(wheels),
            "wheelhouse_fingerprint_sha256": hashlib.sha256(
                json.dumps(wheels, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest().upper(),
        },
        "model_artifact_extraction_or_loading_performed": False,
        "published_at": published_at,
        "python_runtime": {
            "implementation": "CPython",
            "version": "3.12.13",
        },
        "remaining_blocks": [
            "exact_Tesseract_5_engine_and_native_SBOM_unresolved",
            "OCR-G0_and_OCR-G1_execution_blocked",
            "reviewed_model_and_font_artifacts_not_authorized_for_extraction_or_loading",
            "PLATE-D0_internal_detector_not_built_or_authorized",
            "synthetic_generation_training_and_inference_not_authorized",
            "runtime_license_metadata_not_a_legal_or_redistribution_approval",
            "final_digest_bound_D-P3.5-START_confirmation_pending",
        ],
        "status": result["status"],
        "vulnerability_audit": {
            "dependency_count": audit["dependency_count"],
            "status": audit["status"],
            "vulnerability_count": audit["vulnerability_count"],
        },
    }
    output_root.mkdir(parents=True, exist_ok=True)
    _write_json(output_root / "p3-5-runtime-research-evidence.json", evidence)
    _write_json(output_root / "p3-5-runtime-sbom.cdx.json", sbom)
    _write_json(
        output_root / "p3-5-runtime-license-review.json",
        build_license_review(packages),
    )
    return {
        "evidence_id": evidence["evidence_id"],
        "output_files": [
            "p3-5-runtime-research-evidence.json",
            "p3-5-runtime-sbom.cdx.json",
            "p3-5-runtime-license-review.json",
        ],
        "status": "published_owner_review_pending",
    }


def run_all(root: Path, authorization: dict[str, Any]) -> dict[str, Any]:
    prepare_environment(root, authorization)
    inspect_environment(root)
    run_vulnerability_audit(root)
    run_import_check(root)
    run_defender_scan(root)
    return finalize_existing(root)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "validate",
            "prepare",
            "inspect",
            "audit",
            "import-check",
            "scan",
            "finalize",
            "publish",
            "all",
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_PUBLISH_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        authorization, _proposal, _acceptance = load_authorized_context(
            args.authorization, args.proposal, args.acceptance
        )
        root = validate_root(args.root, authorization)
        if args.command == "validate":
            result: object = {
                "authorization_id": authorization["authorization_id"],
                "root": str(root),
                "status": "pass",
            }
        elif args.command == "prepare":
            result = prepare_environment(root, authorization)
        elif args.command == "inspect":
            result = inspect_environment(root)
        elif args.command == "audit":
            result = run_vulnerability_audit(root)
        elif args.command == "import-check":
            result = run_import_check(root)
        elif args.command == "scan":
            result = run_defender_scan(root)
        elif args.command == "finalize":
            result = finalize_existing(root)
        elif args.command == "publish":
            result = publish_repository_evidence(root, args.output_root)
        else:
            result = run_all(root, authorization)
    except (OSError, RuntimeResearchError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
