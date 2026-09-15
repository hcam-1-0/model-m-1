from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
START_PACKAGE = ROOT / "contracts/phase-5/p5-1-start-authorization-package.json"
TOOLCHAIN_PACKAGE = ROOT / "contracts/phase-5/p5-1/toolchain-amendment-r0.json"
EXPECTED_START_SHA256 = "3B4A0CDD44185A94E7C04FB9038032EDDB1EB145E3C551A5A12BA81BD4A2A66E"
EXPECTED_TOOLCHAIN_SHA256 = "70494C243226BE574C6D779D7C03BA9287B3260F278B74B78ADA4D395FE959C6"
EXPECTED_APPS = {
    "admin-center",
    "command-center",
    "evidence-center",
    "intelligence-center",
    "investigation-center",
    "operations-center",
    "security-center",
}
EXPECTED_PACKAGES = {
    "api-client",
    "app-shell",
    "auth-session",
    "capabilities",
    "contracts",
    "design-tokens",
    "event-invalidation",
    "gis-contracts",
    "i18n",
    "navigation",
    "observability",
    "playback-contracts",
    "query-policy",
    "test-fixtures",
    "test-support",
    "ui",
}
GENERATED_DIRS = {"node_modules", "dist", "coverage", "test-results", "storybook-static"}
ALLOWED_ROOT_FILES = {
    ".gitignore",
    ".npmrc",
    "dependency-evidence.json",
    "dependency-lock-candidate.json",
    "eslint.config.mjs",
    "package.json",
    "playwright.config.ts",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "prettier.config.mjs",
    "sbom.cdx.json",
    "tsconfig.base.json",
    "vitest.workspace.ts",
}
EXIT_RECORDS = (
    "contracts/phase-5/p5-1-evidence.json",
    "contracts/phase-5/p5-1-evidence-package.json",
    "contracts/phase-5/p5-1-acceptance-proposal.json",
    "docs/phase-5/current-status-r7.md",
    "docs/phase-5/p5-1-implementation.md",
    "docs/phase-5/p5-1-validation.md",
    "docs/phase-5/p5-1-evidence.md",
    "docs/phase-5/p5-1-acceptance-proposal.md",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path.as_posix()}")
    return value


def _workspace_names(group: str) -> set[str]:
    return {path.name for path in (FRONTEND / group).iterdir() if path.is_dir()}


def _source_files() -> list[Path]:
    result: list[Path] = []
    for directory, names, files in os.walk(FRONTEND):
        current = Path(directory)
        names[:] = [
            name
            for name in names
            if name not in GENERATED_DIRS
            and not (current == FRONTEND and name == "evidence")
        ]
        for name in files:
            path = current / name
            if path.relative_to(FRONTEND).as_posix() != "sbom.cdx.json":
                result.append(path)
    return sorted(result, key=lambda item: item.relative_to(FRONTEND).as_posix())


def _source_manifest_matches() -> bool:
    manifest = read_json(FRONTEND / "evidence/source-manifest.json")
    files = [
        {
            "path": path.relative_to(FRONTEND).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in _source_files()
    ]
    rendered = "\n".join(f"{item['path']}:{item['sha256']}" for item in files)
    aggregate = hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()
    return (
        manifest.get("source_file_count") == len(files)
        and manifest.get("files") == files
        and manifest.get("aggregate_sha256") == aggregate
    )


def _contract_inputs_exact() -> bool:
    manifest = read_json(ROOT / "contracts/phase-5/p5-1/client-contract-manifest.v1.json")
    inputs = manifest.get("inputs", [])
    if len(inputs) != 3:
        return False
    return all(
        (ROOT / item["path"]).is_file()
        and sha256(ROOT / item["path"]) == item["sha256"]
        and isinstance(item.get("count"), int)
        and item["count"] > 0
        for item in inputs
    )


def _source_adoption_is_reference_only() -> bool:
    record = read_json(ROOT / "contracts/phase-5/p5-1/source-adoption-record.v1.json")
    snapshot = ROOT / record["snapshot_path"]
    product_source = "\n".join(
        path.read_text(encoding="utf-8")
        for group in ("apps", "packages")
        for source_root in (FRONTEND / group).glob("*/src")
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix in {".css", ".ts", ".tsx"}
    )
    return (
        record.get("status") == "reference_only_no_source_import"
        and record.get("imported_paths") == []
        and record.get("build_included_paths") == []
        and snapshot.is_file()
        and sha256(snapshot) == record.get("snapshot_sha256")
        and "hcam-1-0/final-ui" not in product_source
    )


def _fixtures_are_safe() -> bool:
    scenarios = read_json(ROOT / "fixtures/phase-5/p5-1/foundation-scenarios.v1.json")
    session = read_json(ROOT / "fixtures/phase-5/p5-1/session.generated.v1.json")
    return (
        scenarios.get("marker") == "HCAM-GENERATED-NON-OPERATIONAL"
        and scenarios.get("issuable") is False
        and len(scenarios.get("states", [])) == 12
        and set(scenarios.get("locales", [])) == {"en", "gu", "hi", "en-XA"}
        and set(scenarios.get("profiles", []))
        == {"low_resource", "enhanced", "control_room", "future_server"}
        and set(scenarios.get("portal_ids", []))
        == {"command", "operations", "intelligence", "investigations", "evidence", "admin", "security"}
        and str(session.get("operatorRef", "")).startswith("SYN-")
        and str(session.get("sessionRef", "")).startswith("SYN-")
        and str(session.get("csrfToken", "")).startswith("SYN-")
    )


def _dependencies_pass() -> bool:
    candidate = read_json(FRONTEND / "dependency-lock-candidate.json")
    evidence = read_json(FRONTEND / "dependency-evidence.json")
    audit = read_json(FRONTEND / "evidence/dependency-audit.json")
    package = read_json(FRONTEND / "package.json")
    direct = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    external = {name: version for name, version in direct.items() if not str(version).startswith("workspace:")}
    selected = {item["name"]: item["version"] for item in candidate.get("packages", [])}
    forbidden = {"maplibre-gl", "leaflet", "hls.js", "mediasoup-client", "onnxruntime-web"}
    return (
        external == selected
        and not forbidden.intersection(external)
        and evidence.get("stage") == "materialization_and_validation_complete"
        and evidence.get("result") == "pass"
        and evidence.get("resolution", {}).get("workspace_projects") == 24
        and audit.get("result") == "pass"
        and audit.get("unresolved_high_or_critical") == 0
        and audit.get("registry") == "https://registry.npmjs.org/"
    )


def _coverage_pass() -> bool:
    coverage = read_json(FRONTEND / "evidence/validation-summary.json")["coverage"]
    critical = coverage.get("critical_contract_branch_coverage", [])
    return (
        coverage.get("statements_percent", 0) >= 90
        and coverage.get("branches_percent", 0) >= 90
        and critical
        and all(item["branches_percent"] >= 95 for item in critical)
        and coverage.get("result") == "pass"
    )


def _validation_summary_pass() -> bool:
    summary = read_json(FRONTEND / "evidence/validation-summary.json")
    return (
        summary.get("typecheck") == "pass"
        and summary.get("lint", {}).get("warnings") == 0
        and summary.get("formatting") == "pass"
        and summary.get("unit_and_component", {}).get("tests_failed") == 0
        and summary.get("browser", {}).get("unexpected") == 0
        and summary.get("builds", {}).get("source_maps") == 0
        and summary.get("storybook", {}).get("build") == "pass"
        and summary.get("manual_evidence", {}).get("production_accessibility_claim") is False
    )


def _sbom_pass() -> bool:
    sbom = read_json(FRONTEND / "sbom.cdx.json")
    components = sbom.get("components", [])
    return (
        sbom.get("bomFormat") == "CycloneDX"
        and sbom.get("specVersion") == "1.6"
        and len(components) >= 300
        and all(item.get("name") and item.get("version") and item.get("purl") for item in components)
    )


def _network_and_import_boundaries_pass() -> bool:
    source_files = [
        path
        for group in ("apps", "packages")
        for source_root in (FRONTEND / group).glob("*/src")
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix in {".ts", ".tsx", ".js", ".mjs"}
    ]
    fetch_files = {
        path.relative_to(FRONTEND).as_posix()
        for path in source_files
        if "fetch(" in path.read_text(encoding="utf-8")
    }
    app_text = "\n".join(
        path.read_text(encoding="utf-8")
        for source_root in (FRONTEND / "apps").glob("*/src")
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix in {".ts", ".tsx"}
    )
    return fetch_files == {"packages/api-client/src/index.ts"} and "../apps/" not in app_text


def _generated_outputs_untracked() -> bool:
    process = subprocess.run(
        ["git", "ls-files", "-z", "--", "frontend"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )
    if process.returncode != 0 or process.stderr:
        return False
    tracked = process.stdout.decode("utf-8").split("\0")
    return not any(any(part in GENERATED_DIRS for part in Path(path).parts) for path in tracked if path)


def checks(*, require_exit_records: bool = False) -> dict[str, bool]:
    root_files = {path.name for path in FRONTEND.iterdir() if path.is_file()}
    start_acceptance = read_json(ROOT / "contracts/phase-5/p5-1-start-acceptance.json")
    toolchain_acceptance = read_json(
        ROOT / "contracts/phase-5/p5-1/toolchain-amendment-r0-acceptance.json"
    )
    return {
        "start_package_exact": sha256(START_PACKAGE) == EXPECTED_START_SHA256,
        "start_owner_acceptance_effective": start_acceptance.get("effective") is True,
        "toolchain_package_exact": sha256(TOOLCHAIN_PACKAGE) == EXPECTED_TOOLCHAIN_SHA256,
        "toolchain_owner_acceptance_effective": toolchain_acceptance.get("effective") is True,
        "frontend_root_paths_allowlisted": root_files <= ALLOWED_ROOT_FILES,
        "seven_portals_exact": _workspace_names("apps") == EXPECTED_APPS,
        "sixteen_shared_packages_exact": _workspace_names("packages") == EXPECTED_PACKAGES,
        "contract_inputs_exact": _contract_inputs_exact(),
        "source_adoption_reference_only": _source_adoption_is_reference_only(),
        "generated_fixtures_safe": _fixtures_are_safe(),
        "dependency_supply_chain_pass": _dependencies_pass(),
        "source_manifest_exact": _source_manifest_matches(),
        "coverage_thresholds_pass": _coverage_pass(),
        "validation_summary_pass": _validation_summary_pass(),
        "sbom_complete": _sbom_pass(),
        "network_and_import_boundaries_pass": _network_and_import_boundaries_pass(),
        "generated_outputs_untracked": _generated_outputs_untracked(),
        "exit_records_present": (not require_exit_records)
        or all((ROOT / path).is_file() for path in EXIT_RECORDS),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-exit-records", action="store_true")
    args = parser.parse_args()
    result = checks(require_exit_records=args.require_exit_records)
    passed = all(result.values())
    payload = {"status": "pass" if passed else "fail", "checks": result}
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        for name, value in result.items():
            print(f"{'PASS' if value else 'FAIL'} {name}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
