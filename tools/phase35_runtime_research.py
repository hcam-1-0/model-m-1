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
            "PYTHONNOUSERSITE": "1",
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


def prepare_environment(root: Path, authorization: dict[str, Any]) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
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
    python_find = _run(
        ["uv", "python", "find", "3.12.13", "--no-python-downloads"],
        environment=environment,
        timeout=30,
    )
    source_python = Path(python_find.stdout.strip())
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
                "uv",
                "venv",
                "--python",
                str(source_python),
                "--no-project",
                "--no-python-downloads",
                "--link-mode",
                "copy",
                str(root / "venv"),
            ],
            environment=environment,
            timeout=300,
        )
    direct = [
        f"{item['name']}=={item['version']}"
        for item in authorization["allowed_direct_packages"]
    ]
    install = _run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(venv_python),
            "--no-python-downloads",
            "--no-config",
            "--default-index",
            "https://pypi.org/simple",
            "--only-binary",
            ":all:",
            "--no-build",
            "--link-mode",
            "copy",
            "--strict",
            *direct,
        ],
        environment=environment,
        timeout=3600,
    )
    check = _run(
        [
            "uv",
            "pip",
            "check",
            "--python",
            str(venv_python),
            "--no-python-downloads",
            "--offline",
            "--no-config",
        ],
        environment=environment,
        timeout=300,
    )
    return {
        "direct_packages": direct,
        "install_stderr_tail": install.stderr[-2000:],
        "python_executable": str(venv_python),
        "python_version": version,
        "uv_pip_check": check.stdout.strip(),
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


def build_sbom(packages: list[dict[str, Any]], native_files: list[dict[str, Any]]) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    for package in packages:
        components.append(
            {
                "bom-ref": f"pkg:pypi/{_canonical_name(package['name'])}@{package['version']}",
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
    _write_json(root / "evidence" / "runtime-sbom.cdx.json", build_sbom(packages, native_files))
    return report


def run_import_check(root: Path) -> dict[str, Any]:
    code = r'''
import importlib
import importlib.metadata
import json
import socket

attempts = []

def denied(*args, **kwargs):
    attempts.append(repr(args[:2]))
    raise RuntimeError("network access denied by H-CAM P3.5 import guard")

socket.socket = denied
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
    "constructors_called": False,
    "imports": modules,
    "model_font_or_media_loaded": False,
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
        or result.get("network_attempt_count") != 0
        or result.get("imports")
        != {
            "PIL": "12.3.0",
            "paddle": "3.3.1",
            "paddleocr": "3.7.0",
            "regex": "2026.7.19",
        }
    ):
        raise RuntimeResearchError("network-denied direct imports did not pass")
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


def run_defender_scan(root: Path) -> dict[str, Any]:
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
        environment=_safe_environment(root),
        timeout=3600,
    )
    result = {
        "engine": "Microsoft Defender",
        "exit_code": completed.returncode,
        "finding": "no_threats_found",
        "output_tail": (completed.stdout + completed.stderr)[-4000:],
        "status": "pass",
    }
    _write_json(root / "evidence" / "defender-scan.json", result)
    return result


def run_all(root: Path, authorization: dict[str, Any]) -> dict[str, Any]:
    environment = prepare_environment(root, authorization)
    inventory = inspect_environment(root)
    audit = run_vulnerability_audit(root)
    imports = run_import_check(root)
    defender = run_defender_scan(root)
    result = {
        "artifact_or_model_loading_performed": False,
        "authorization_id": "D-P3.5-RUNTIME-RESEARCH",
        "defender": defender,
        "dependency_or_lockfile_change_performed": False,
        "environment": environment,
        "implementation_authorized": False,
        "imports": imports,
        "inventory": {
            "native_file_count": inventory["native_file_count"],
            "package_count": inventory["package_count"],
        },
        "runtime_constructors_or_inference_performed": False,
        "status": "complete_review_required"
        if audit["vulnerability_count"]
        else "complete_pass",
        "tesseract_runtime_present": False,
        "vulnerability_audit": {
            "dependency_count": audit["dependency_count"],
            "status": audit["status"],
            "vulnerability_count": audit["vulnerability_count"],
        },
    }
    _write_json(root / "evidence" / "runtime-research-result.json", result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("validate", "prepare", "inspect", "audit", "import-check", "scan", "all")
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
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
        else:
            result = run_all(root, authorization)
    except (OSError, RuntimeResearchError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
