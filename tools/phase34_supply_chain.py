#!/usr/bin/env python3
"""Generate and verify deterministic P3.4 supply-chain evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ROOT / "contracts" / "phase-3" / "p3-4-dependencies.json"
SBOM = ROOT / "contracts" / "phase-3" / "p3-4-sbom.cdx.json"
CONTAINER_REVIEW = (
    ROOT / "contracts" / "phase-3" / "p3-4-container-vulnerability-review.json"
)
POSTGIS_INDEX_DIGEST = (
    "sha256:eb2e8b8afd9b0ecee83bc20fd01aca62a5071bada2c0f38763174b653f8eed42"
)
POSTGIS_AMD64_MANIFEST = (
    "sha256:e6e6593f9b5025731edc1fd1c1fc6b47b0730244408e80b147b45557700fc340"
)

PYTHON_DEPENDENCIES = {
    "cel-expr-python": {
        "license": "Apache-2.0",
        "role": "runtime_constrained_expression_engine",
        "source": "https://github.com/cel-expr/cel-python",
        "version": "0.1.3",
    },
    "hypothesis": {
        "license": "MPL-2.0",
        "role": "development_property_and_state_machine_tests",
        "source": "https://github.com/HypothesisWorks/hypothesis",
        "version": "6.165.10",
    },
    "numpy": {
        "license": "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
        "role": "existing_analytics_runtime_transitive_dependency",
        "source": "https://github.com/numpy/numpy",
        "version": "2.5.2",
    },
    "shapely": {
        "license": "BSD-3-Clause",
        "role": "runtime_image_space_geometry_engine",
        "source": "https://github.com/shapely/shapely",
        "version": "2.1.2",
    },
}

TARGET_WHEEL_MARKERS = (
    "cp312-cp312-manylinux",
    "cp312-cp312-win_amd64",
    "cp314-cp314-manylinux",
    "cp314-cp314-win_amd64",
    "cp310-abi3-manylinux_2_17_x86_64",
    "cp310-abi3-win_amd64",
)


def _serialized(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _canonical_digest(document: dict[str, object]) -> str:
    payload = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _lock_packages() -> dict[str, dict[str, object]]:
    document = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = document.get("package")
    if not isinstance(packages, list):
        raise ValueError("uv.lock does not contain packages")
    return {
        str(item["name"]): item for item in packages if isinstance(item, dict)
    }


def _artifact(item: dict[str, object]) -> dict[str, object]:
    result = {
        "sha256": str(item["hash"]).removeprefix("sha256:"),
        "size_bytes": int(item["size"]),
        "url": str(item["url"]),
    }
    if "upload-time" in item:
        result["upload_time"] = str(item["upload-time"])
    return result


def build_dependencies() -> dict[str, object]:
    locked = _lock_packages()
    packages: list[dict[str, object]] = []
    for name, policy in PYTHON_DEPENDENCIES.items():
        item = locked.get(name)
        if item is None or item.get("version") != policy["version"]:
            raise ValueError(f"{name} lock version changed")
        artifacts = []
        sdist = item.get("sdist")
        if isinstance(sdist, dict):
            artifacts.append({"platform": "source", **_artifact(sdist)})
        wheels = item.get("wheels", [])
        if not isinstance(wheels, list):
            raise ValueError(f"{name} wheel records are invalid")
        for wheel in wheels:
            if not isinstance(wheel, dict):
                continue
            url = str(wheel.get("url", ""))
            marker = next(
                (value for value in TARGET_WHEEL_MARKERS if value in url), None
            )
            if marker is not None:
                artifacts.append({"platform": marker, **_artifact(wheel)})
        packages.append(
            {
                "artifacts": artifacts,
                "license": policy["license"],
                "name": name,
                "role": policy["role"],
                "source": policy["source"],
                "version": policy["version"],
            }
        )
    body: dict[str, object] = {
        "audit_boundary": {
            "container_vulnerability_scan_included": True,
            "python_environment_pip_audit_included": True,
            "reason": "Python and container findings are recorded without conflation.",
        },
        "cel_profile": {
            "custom_extensions": False,
            "profile": "hcam.p3-4.constrained-cel.v1",
            "runtime_compilation_of_unapproved_text": False,
        },
        "generated_at_policy": "deterministic_no_wall_clock_timestamp",
        "lockfile": {
            "path": "uv.lock",
            "sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
            "uv_version": "0.12.3",
        },
        "postgis": {
            "container_index_digest": POSTGIS_INDEX_DIGEST,
            "container_linux_amd64_manifest": POSTGIS_AMD64_MANIFEST,
            "container_reference": (
                "postgis/postgis:18-3.6-alpine@" + POSTGIS_INDEX_DIGEST
            ),
            "geos_compiled_version": "not_reported_by_postgis_full_version",
            "geos_runtime_version": "3.14.1",
            "image_platform": "linux/amd64",
            "license": "GPL-2.0-or-later",
            "postgis_runtime_version": "3.6.4",
            "postgresql_major": "18",
            "proj_runtime_version": "9.8.1",
            "source": "https://github.com/postgis/docker-postgis",
            "validated_operations": [
                "extension_creation",
                "geometry_validity_constraint",
                "gist_index",
                "canonical_wkb_round_trip",
                "migration_upgrade_downgrade_upgrade",
            ],
        },
        "python_packages": packages,
        "runtime_bindings": {
            "developer": {
                "geos": "3.13.1",
                "python": "3.14.6",
                "shapely": "2.1.2",
            },
            "docker": {
                "python": "3.12.12",
                "target": "linux/amd64",
            },
        },
        "schema_version": "1.0.0",
    }
    body["content_digest"] = _canonical_digest(body)
    return body


def _normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _purl(name: str, version: str) -> str:
    return f"pkg:pypi/{quote(_normalize_name(name))}@{quote(version)}"


def build_sbom(raw: dict[str, object]) -> dict[str, object]:
    if raw.get("bomFormat") != "CycloneDX":
        raise ValueError("pip-audit input is not CycloneDX")
    if raw.get("vulnerabilities"):
        raise ValueError("cannot freeze a Python SBOM with known vulnerabilities")
    source_components = raw.get("components")
    if not isinstance(source_components, list):
        raise ValueError("pip-audit components are missing")
    components: list[dict[str, object]] = []
    for item in source_components:
        if not isinstance(item, dict):
            raise ValueError("pip-audit component is invalid")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("pip-audit component identity is incomplete")
        purl = _purl(name, version)
        components.append(
            {
                "bom-ref": purl,
                "name": _normalize_name(name),
                "purl": purl,
                "type": "library",
                "version": version,
            }
        )
    container_ref = "pkg:docker/postgis/postgis@18-3.6?digest=" + quote(
        POSTGIS_INDEX_DIGEST, safe=""
    )
    native = (
        ("postgis", "3.6.4", "GPL-2.0-or-later", container_ref),
        ("postgresql", "18", "PostgreSQL", "pkg:generic/postgresql@18"),
        ("geos", "3.14.1", "LGPL-2.1-or-later", "pkg:generic/geos@3.14.1"),
        ("proj", "9.8.1", "MIT", "pkg:generic/proj@9.8.1"),
    )
    for name, version, license_id, purl in native:
        components.append(
            {
                "bom-ref": purl,
                "licenses": [{"license": {"id": license_id}}],
                "name": name,
                "purl": purl,
                "type": "library" if name != "postgis" else "container",
                "version": version,
            }
        )
    components.sort(key=lambda item: (str(item["name"]), str(item["version"])))
    root_ref = "pkg:pypi/hcam-core@0.2.0"
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",
        "bomFormat": "CycloneDX",
        "components": components,
        "dependencies": [
            {
                "dependsOn": [str(item["bom-ref"]) for item in components],
                "ref": root_ref,
            },
            *(
                {"dependsOn": [], "ref": str(item["bom-ref"])}
                for item in components
            ),
        ],
        "metadata": {
            "component": {
                "bom-ref": root_ref,
                "name": "hcam-core",
                "purl": root_ref,
                "type": "application",
                "version": "0.2.0",
            },
            "properties": [
                {"name": "hcam:evidence-scope", "value": "phase3.p3_4"},
                {
                    "name": "hcam:python-vulnerability-audit",
                    "value": "no-known-vulnerabilities",
                },
                {
                    "name": "hcam:container-vulnerability-scan",
                    "value": "recorded-separately-with-deployment-blocked",
                },
            ],
            "tools": [
                {
                    "name": "pip-audit",
                    "vendor": "Python Packaging Authority",
                    "version": "2.10.1",
                }
            ],
        },
        "specVersion": "1.4",
        "version": 1,
        "vulnerabilities": [],
    }


def _message_field(message: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\s*:\s*([^\r\n]+)", message, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def build_container_review(raw: dict[str, object]) -> dict[str, object]:
    runs = raw.get("runs")
    if not isinstance(runs, list) or len(runs) != 1 or not isinstance(runs[0], dict):
        raise ValueError("Docker Scout SARIF must contain exactly one run")
    results = runs[0].get("results")
    if not isinstance(results, list):
        raise ValueError("Docker Scout SARIF results are missing")
    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "LOW": 0,
        "MEDIUM": 0,
        "UNSPECIFIED": 0,
    }
    fix_counts = {"fixed_version_available": 0, "not_fixed": 0}
    critical_high: list[dict[str, str]] = []
    vulnerable_packages: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Docker Scout SARIF result is invalid")
        message_value = result.get("message")
        message = (
            message_value.get("text", "")
            if isinstance(message_value, dict)
            else ""
        )
        severity = _message_field(str(message), "Severity")
        package = _message_field(str(message), "Package")
        fixed_version = _message_field(str(message), "Fixed version")
        if severity not in severity_counts:
            raise ValueError(f"unexpected Docker Scout severity: {severity}")
        severity_counts[severity] += 1
        vulnerable_packages.add(package.split("@", maxsplit=1)[0])
        if fixed_version == "not fixed":
            fix_counts["not_fixed"] += 1
        else:
            fix_counts["fixed_version_available"] += 1
        if severity in {"CRITICAL", "HIGH"}:
            critical_high.append(
                {
                    "cve_id": str(result.get("ruleId", "unknown")),
                    "fixed_version": fixed_version,
                    "package": package,
                    "severity": severity,
                }
            )
    critical_high.sort(
        key=lambda item: (item["severity"], item["cve_id"], item["package"])
    )
    body: dict[str, object] = {
        "container_index_digest": POSTGIS_INDEX_DIGEST,
        "container_reference": "postgis/postgis:18-3.6-alpine@" + POSTGIS_INDEX_DIGEST,
        "critical_high_findings": critical_high,
        "deployment_gate": "blocked_pending_cleaner_image_or_remediation_and_rescan",
        "finding_count": len(results),
        "fix_status_counts": fix_counts,
        "generated_only_local_validation_allowed": True,
        "no_findings_suppressed": True,
        "review_policy": {
            "camera_or_media_access": False,
            "production_or_pilot_deployment": False,
            "runtime_exposure": "loopback_only_disposable_validation_database",
            "vex_applied": False,
        },
        "scanner": {"name": "Docker Scout", "version": "1.24.0"},
        "schema_version": "1.0.0",
        "severity_counts": severity_counts,
        "vulnerable_package_count": len(vulnerable_packages),
    }
    body["content_digest"] = _canonical_digest(body)
    return body


def validate_dependencies(document: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != "1.0.0":
        failures.append("schema_version")
    unsigned = dict(document)
    content_digest = unsigned.pop("content_digest", None)
    if content_digest != _canonical_digest(unsigned):
        failures.append("content_digest")
    packages = document.get("python_packages")
    versions = (
        {item.get("name"): item.get("version") for item in packages if isinstance(item, dict)}
        if isinstance(packages, list)
        else {}
    )
    for name, policy in PYTHON_DEPENDENCIES.items():
        if versions.get(name) != policy["version"]:
            failures.append(name)
    postgis = document.get("postgis")
    if not isinstance(postgis, dict) or postgis.get("container_index_digest") != POSTGIS_INDEX_DIGEST:
        failures.append("postgis")
    return failures


def validate_sbom(document: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if document.get("bomFormat") != "CycloneDX":
        failures.append("bomFormat")
    if document.get("serialNumber") is not None:
        failures.append("random_serial")
    metadata = document.get("metadata")
    if not isinstance(metadata, dict) or "timestamp" in metadata:
        failures.append("metadata")
    if document.get("vulnerabilities") != []:
        failures.append("vulnerabilities")
    components = document.get("components")
    versions = (
        {item.get("name"): item.get("version") for item in components if isinstance(item, dict)}
        if isinstance(components, list)
        else {}
    )
    for name, policy in PYTHON_DEPENDENCIES.items():
        if versions.get(name) != policy["version"]:
            failures.append(name)
    if versions.get("postgis") != "3.6.4" or versions.get("geos") != "3.14.1":
        failures.append("native_components")
    return failures


def validate_container_review(document: dict[str, object]) -> list[str]:
    failures: list[str] = []
    unsigned = dict(document)
    content_digest = unsigned.pop("content_digest", None)
    if content_digest != _canonical_digest(unsigned):
        failures.append("container_content_digest")
    if document.get("container_index_digest") != POSTGIS_INDEX_DIGEST:
        failures.append("container_index_digest")
    if document.get("deployment_gate") != "blocked_pending_cleaner_image_or_remediation_and_rescan":
        failures.append("deployment_gate")
    counts = document.get("severity_counts")
    if (
        not isinstance(counts, dict)
        or int(counts.get("CRITICAL", 0)) < 1
        or int(counts.get("HIGH", 0)) < 1
    ):
        failures.append("critical_high_findings")
    if document.get("no_findings_suppressed") is not True:
        failures.append("suppression")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--pip-audit-cyclonedx", type=Path, required=True)
    write.add_argument("--docker-scout-sarif", type=Path, required=True)
    write.add_argument("--acknowledge-supply-chain-evidence", action="store_true")
    subparsers.add_parser("check")
    args = parser.parse_args()
    expected_dependencies = build_dependencies()
    if args.command == "write":
        if not args.acknowledge_supply_chain_evidence:
            print("[fail] explicit supply-chain evidence acknowledgment is required")
            return 2
        raw = json.loads(args.pip_audit_cyclonedx.read_text(encoding="utf-8"))
        sbom = build_sbom(raw)
        scout = json.loads(args.docker_scout_sarif.read_text(encoding="utf-8"))
        container_review = build_container_review(scout)
        failures = (
            validate_dependencies(expected_dependencies)
            + validate_sbom(sbom)
            + validate_container_review(container_review)
        )
        if failures:
            print("[fail] " + ", ".join(failures))
            return 1
        DEPENDENCIES.write_text(_serialized(expected_dependencies), encoding="utf-8", newline="\n")
        SBOM.write_text(_serialized(sbom), encoding="utf-8", newline="\n")
        CONTAINER_REVIEW.write_text(
            _serialized(container_review), encoding="utf-8", newline="\n"
        )
        print(f"[write] {DEPENDENCIES.relative_to(ROOT)}")
        print(f"[write] {SBOM.relative_to(ROOT)}")
        print(f"[write] {CONTAINER_REVIEW.relative_to(ROOT)}")
        return 0
    try:
        dependencies = json.loads(DEPENDENCIES.read_text(encoding="utf-8"))
        sbom = json.loads(SBOM.read_text(encoding="utf-8"))
        container_review = json.loads(CONTAINER_REVIEW.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[fail] {exc}")
        return 1
    failures = (
        validate_dependencies(dependencies)
        + validate_sbom(sbom)
        + validate_container_review(container_review)
    )
    if dependencies != expected_dependencies:
        failures.append("dependency_drift")
    if failures:
        print("[fail] " + ", ".join(failures))
        return 1
    print(f"[pass] {DEPENDENCIES.relative_to(ROOT)}")
    print(f"[pass] {SBOM.relative_to(ROOT)}")
    print(f"[pass] {CONTAINER_REVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
