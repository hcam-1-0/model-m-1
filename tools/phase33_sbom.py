#!/usr/bin/env python3
"""Normalize and verify the P3.3 runtime CycloneDX evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SBOM_PATH = ROOT / "contracts" / "phase-3" / "p3-3-sbom.cdx.json"
REQUIRED_COMPONENTS = {
    "numpy": "2.5.2",
    "onnx": "1.22.0",
    "onnxruntime": "1.29.0",
    "scipy": "1.18.1",
}


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _purl(name: str, version: str) -> str:
    return f"pkg:pypi/{quote(_normalized_name(name))}@{quote(version)}"


def normalized_sbom(raw: dict[str, object]) -> dict[str, object]:
    if raw.get("bomFormat") != "CycloneDX":
        raise ValueError("pip-audit output is not CycloneDX")
    vulnerabilities = raw.get("vulnerabilities", [])
    if vulnerabilities:
        raise ValueError("cannot freeze an SBOM with known vulnerabilities")
    raw_components = raw.get("components")
    if not isinstance(raw_components, list):
        raise ValueError("CycloneDX components are missing")

    components: list[dict[str, str]] = []
    for item in raw_components:
        if not isinstance(item, dict):
            raise ValueError("CycloneDX component must be an object")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("CycloneDX component name/version is missing")
        purl = _purl(name, version)
        components.append(
            {
                "bom-ref": purl,
                "name": _normalized_name(name),
                "purl": purl,
                "type": "library",
                "version": version,
            }
        )
    components.sort(key=lambda item: (item["name"], item["version"]))
    root_ref = "pkg:pypi/hcam-core@0.2.0"
    dependencies = [
        {"dependsOn": [item["bom-ref"] for item in components], "ref": root_ref},
        *({"dependsOn": [], "ref": item["bom-ref"]} for item in components),
    ]
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",
        "bomFormat": "CycloneDX",
        "components": components,
        "dependencies": dependencies,
        "metadata": {
            "component": {
                "bom-ref": root_ref,
                "name": "hcam-core",
                "purl": root_ref,
                "type": "application",
                "version": "0.2.0",
            },
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


def serialized(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def validate(document: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if document.get("bomFormat") != "CycloneDX":
        failures.append("bomFormat")
    if document.get("serialNumber") is not None:
        failures.append("random serialNumber present")
    metadata = document.get("metadata")
    if not isinstance(metadata, dict) or "timestamp" in metadata:
        failures.append("nondeterministic metadata")
    if document.get("vulnerabilities") != []:
        failures.append("known vulnerabilities present")
    components = document.get("components")
    versions = (
        {
            item.get("name"): item.get("version")
            for item in components
            if isinstance(item, dict)
        }
        if isinstance(components, list)
        else {}
    )
    for name, version in REQUIRED_COMPONENTS.items():
        if versions.get(name) != version:
            failures.append(f"{name} version")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--pip-audit-cyclonedx", type=Path, required=True)
    subparsers.add_parser("check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "write":
        raw = json.loads(args.pip_audit_cyclonedx.read_text(encoding="utf-8"))
        document = normalized_sbom(raw)
        failures = validate(document)
        if failures:
            print("[fail] " + ", ".join(failures))
            return 1
        SBOM_PATH.write_text(serialized(document), encoding="utf-8", newline="\n")
        print(f"[write] {SBOM_PATH.relative_to(ROOT)}")
        return 0

    document = json.loads(SBOM_PATH.read_text(encoding="utf-8"))
    failures = validate(document)
    if failures:
        print("[fail] " + ", ".join(failures))
        return 1
    print(f"[pass] {SBOM_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
