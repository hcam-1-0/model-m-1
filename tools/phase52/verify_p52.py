from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
START_PACKAGE = ROOT / "contracts/phase-5/p5-2-start-authorization-package.json"
START_ACCEPTANCE = ROOT / "contracts/phase-5/p5-2-start-acceptance.json"
EXPECTED_START_SHA256 = "24F89F18D52404A4FF1AA4A8A52A9DA8E4D4619B7721107B1A82EEF389805B67"
EXPECTED_BOUND_INPUT_DIGEST = "3E070D61CC90E969E1A5FA91A9564D1FE151E88293904051B9B2763C5E27A74E"
EXPECTED_P51_PACKAGE_SHA256 = "74953D5E9239A17E8A4173B72CF7A485BC4B7FDBC0503A31787F2EFE9C1767BC"
EXPECTED_APPS = {
    "admin-center",
    "command-center",
    "evidence-center",
    "gis-center",
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
    "command-domain",
    "contracts",
    "design-tokens",
    "event-invalidation",
    "gis-contracts",
    "gis-domain",
    "gis-renderers",
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
EXIT_RECORDS = (
    "contracts/phase-5/p5-2-evidence.json",
    "contracts/phase-5/p5-2-evidence-package.json",
    "contracts/phase-5/p5-2-acceptance-proposal.json",
    "docs/phase-5/current-status-r11.md",
    "docs/phase-5/p5-2/implementation.md",
    "docs/phase-5/p5-2/validation.md",
    "docs/phase-5/p5-2/evidence.md",
    "docs/phase-5/p5-2/acceptance-proposal.md",
    "frontend/evidence/p5-2-dependency-audit.json",
    "frontend/evidence/p5-2-source-manifest.json",
    "frontend/evidence/p5-2-validation-summary.json",
    "frontend/evidence/p5-2-visual-manifest.json",
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
    path = FRONTEND / "evidence/p5-2-source-manifest.json"
    if not path.is_file():
        return False
    manifest = read_json(path)
    files = [
        {
            "path": item.relative_to(FRONTEND).as_posix(),
            "bytes": item.stat().st_size,
            "sha256": sha256(item),
        }
        for item in _source_files()
    ]
    rendered = "\n".join(f"{item['path']}:{item['sha256']}" for item in files)
    aggregate = hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()
    return (
        manifest.get("schema_version") == "hcam.p5_2.source_manifest.v1"
        and manifest.get("source_file_count") == len(files)
        and manifest.get("files") == files
        and manifest.get("aggregate_sha256") == aggregate
    )


def _authorized_paths_present() -> bool:
    package = read_json(START_PACKAGE)
    additive = package.get("exact_additive_implementation_paths", [])
    existing = package.get("exact_existing_file_changes", [])
    if len(additive) != 99 or len(existing) != 30:
        return False
    return all(
        (ROOT / value).is_file() and not (ROOT / value).is_symlink()
        for value in [*additive, *existing]
    )


def _routes_and_shared_domain_pass() -> bool:
    manifest = read_json(ROOT / "contracts/phase-5/p5-2/route-manifest.v1.json")
    command_routes = (FRONTEND / "apps/command-center/src/routes.tsx").read_text(encoding="utf-8")
    gis_routes = (FRONTEND / "apps/gis-center/src/routes.tsx").read_text(encoding="utf-8")
    app_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (FRONTEND / "apps").rglob("*")
        if path.is_file() and path.suffix in {".ts", ".tsx"}
    )
    command_families = re.findall(
        r'\["/command(?:/[^\"]*)?",\s*"[^\"]+"\]', command_routes
    )
    gis_families = re.findall(r'\["/gis(?:/[^\"]*)?",\s*"[^\"]+"\]', gis_routes)
    return (
        manifest.get("primary") == {"portal": "command", "base": "/command", "page_families": 10}
        and manifest.get("connected") == {"portal": "gis", "base": "/gis", "page_families": 9}
        and len(command_families) == 10
        and len(gis_families) == 9
        and "@hcam/gis-domain" in app_sources
        and "../apps/" not in app_sources
        and manifest.get("mutation_routes") == []
        and manifest.get("backend_routes_added") == []
    )


def _generated_fixtures_pass() -> bool:
    for scale, count in (("C1", 1), ("C10", 10), ("C50", 50)):
        fixture = read_json(ROOT / f"fixtures/phase-5/p5-2/{scale.lower()}.generated.v1.json")
        if (
            fixture.get("marker") != "HCAM-GENERATED-NON-OPERATIONAL"
            or fixture.get("scale") != scale
            or fixture.get("records") != count
            or fixture.get("real_data") is not False
        ):
            return False
    replay = read_json(ROOT / "fixtures/phase-5/p5-2/replay-manifest.generated.v1.json")
    scenarios = read_json(ROOT / "fixtures/phase-5/p5-2/command-scenarios.generated.v1.json")
    required_states = {
        "loading", "empty", "ready", "partial", "stale", "degraded", "denied",
        "conflict", "failure", "recovery", "correction", "unknown", "retracted", "unsupported",
    }
    return (
        replay.get("expected_digest_stable") is True
        and replay.get("network") is False
        and len(replay.get("seeds", [])) == 3
        and set(scenarios.get("scenarios", [])) == required_states
        and scenarios.get("operational_actions") is False
    )


def _producer_and_renderer_boundaries_pass() -> bool:
    fixture_source = (FRONTEND / "packages/test-fixtures/src/p5-2-fixtures.ts").read_text(
        encoding="utf-8"
    )
    producer_match = re.search(
        r"export const unavailableProducers = \[(.*?)\] as const;", fixture_source, re.DOTALL
    )
    renderer = read_json(ROOT / "contracts/phase-5/p5-2/gis-renderer-admission.v1.json")
    profile = read_json(ROOT / "contracts/phase-5/p5-2/generated-resource-profile.v1.json")
    provider = (FRONTEND / "packages/gis-renderers/src/provider-policy.ts").read_text(
        encoding="utf-8"
    )
    return (
        producer_match is not None
        and producer_match.group(1).count('"') // 2 == 14
        and renderer.get("ordered_modes")
        == ["deck_interleaved", "deck_overlaid", "maplibre", "list_only"]
        and renderer.get("rules", [None])[0] == "list_only is always available"
        and set(profile.get("profiles", {}))
        == {"low_resource", "enhanced", "control_room", "future_server"}
        and "export function providerRuntimeAllowed(): false" in provider
        and "return false;" in provider
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
    urls = [
        value
        for path in source_files
        for value in re.findall(r"https?://[^\"'\s<]+", path.read_text(encoding="utf-8"))
    ]
    return (
        fetch_files == {"packages/api-client/src/index.ts"}
        and all(value.startswith(("http://127.0.0.1:4173/", "http://127.0.0.1:4174/")) for value in urls)
    )


def _dependencies_pass() -> bool:
    candidate = read_json(FRONTEND / "dependency-lock-candidate.json")
    evidence = read_json(FRONTEND / "dependency-evidence.json")
    audit_path = FRONTEND / "evidence/p5-2-dependency-audit.json"
    if not audit_path.is_file():
        return False
    audit = read_json(audit_path)
    package = read_json(FRONTEND / "package.json")
    direct = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    external = {name: version for name, version in direct.items() if not str(version).startswith("workspace:")}
    selected = {item["name"]: item["version"] for item in candidate.get("packages", [])}
    required = {
        "maplibre-gl": "6.7.0",
        "@deck.gl/core": "9.4.0",
        "@deck.gl/layers": "9.4.0",
        "@deck.gl/mapbox": "9.4.0",
    }
    return (
        external == selected
        and all(external.get(name) == version for name, version in required.items())
        and evidence.get("stage") == "materialization_and_validation_complete"
        and evidence.get("resolution", {}).get("workspace_projects") == 28
        and evidence.get("resolution", {}).get("alternate_source_count") == 0
        and audit.get("result") == "pass"
        and audit.get("unresolved_high_or_critical") == 0
        and audit.get("registry") == "https://registry.npmjs.org/"
    )


def _validation_pass() -> bool:
    path = FRONTEND / "evidence/p5-2-validation-summary.json"
    if not path.is_file():
        return False
    summary = read_json(path)
    coverage = summary.get("coverage", {})
    critical = coverage.get("critical_contract_branch_coverage", [])
    critical_names = {item.get("file", "").split("/src/")[0] for item in critical}
    return (
        summary.get("result") == "pass"
        and summary.get("workspace") == {"applications": 8, "shared_packages": 19, "dependency_edges": 62}
        and summary.get("unit_and_component", {}).get("tests_failed") == 0
        and summary.get("browser", {}).get("unexpected") == 0
        and summary.get("builds", {}).get("source_maps") == 0
        and summary.get("storybook", {}).get("build") == "pass"
        and summary.get("repository_regression", {}).get("tests_failed") == 0
        and summary.get("repository_regression", {}).get("result") == "pass"
        and coverage.get("statements_percent", 0) >= 90
        and coverage.get("branches_percent", 0) >= 90
        and all(item.get("branches_percent", 0) >= 95 for item in critical)
        and {"command-domain", "gis-domain", "gis-renderers"} <= critical_names
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


def _visual_manifest_pass() -> bool:
    path = FRONTEND / "evidence/p5-2-visual-manifest.json"
    if not path.is_file():
        return False
    manifest = read_json(path)
    captures = manifest.get("captures", [])
    def capture_passes(item: dict[str, Any]) -> bool:
        relative = item.get("path")
        if not isinstance(relative, str) or not relative.startswith("test-results/"):
            return False
        if (
            not re.fullmatch(r"[0-9A-F]{64}", str(item.get("sha256", "")))
            or item.get("bytes", 0) <= 0
            or item.get("width", 0) <= 0
            or item.get("height", 0) <= 0
        ):
            return False
        capture = FRONTEND / relative
        if not capture.exists():
            return True
        return (
            capture.is_file()
            and not capture.is_symlink()
            and capture.stat().st_size == item["bytes"]
            and sha256(capture) == item["sha256"]
        )

    return (
        len(captures) == 4
        and {item.get("portal") for item in captures} == {"command", "gis"}
        and {item.get("profile") for item in captures} == {"desktop", "mobile"}
        and all(capture_passes(item) for item in captures)
    )


def _accepted_p51_history_pass() -> bool:
    acceptance = read_json(ROOT / "contracts/phase-5/p5-1-acceptance.json")
    package = ROOT / acceptance.get("evidence_package", {}).get("path", "")
    commit = acceptance.get("accepted_implementation_commit", "")
    process = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return (
        acceptance.get("effective") is True
        and package.is_file()
        and sha256(package) == EXPECTED_P51_PACKAGE_SHA256
        and process.returncode == 0
        and process.stderr == b""
    )


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
    return not any(
        any(part in GENERATED_DIRS for part in Path(value).parts) for value in tracked if value
    )


def _exit_package_pass() -> bool:
    package_path = ROOT / "contracts/phase-5/p5-2-evidence-package.json"
    proposal_path = ROOT / "contracts/phase-5/p5-2-acceptance-proposal.json"
    if not package_path.is_file() or not proposal_path.is_file():
        return False
    package = read_json(package_path)
    proposal = read_json(proposal_path)
    components = package.get("components", [])
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda item: item["path"])
    )
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()
    return (
        components
        and all(
            (ROOT / item["path"]).is_file()
            and (ROOT / item["path"]).stat().st_size == item["bytes"]
            and sha256(ROOT / item["path"]) == item["sha256"]
            for item in components
        )
        and package.get("canonical_component_digest") == digest
        and proposal.get("evidence_package", {}).get("sha256") == sha256(package_path)
        and proposal.get("effective") is False
        and proposal.get("P5_3_authorized") is False
    )


def checks(*, require_exit_records: bool = False) -> dict[str, bool]:
    start = read_json(START_ACCEPTANCE)
    package = read_json(START_PACKAGE)
    result = {
        "start_package_exact": sha256(START_PACKAGE) == EXPECTED_START_SHA256,
        "start_owner_acceptance_effective": start.get("effective") is True,
        "bound_input_digest_exact": package.get("bound_input_digest") == EXPECTED_BOUND_INPUT_DIGEST,
        "accepted_p5_1_history_intact": _accepted_p51_history_pass(),
        "eight_portals_exact": _workspace_names("apps") == EXPECTED_APPS,
        "nineteen_shared_packages_exact": _workspace_names("packages") == EXPECTED_PACKAGES,
        "authorized_paths_present": _authorized_paths_present(),
        "command_primary_gis_connected": _routes_and_shared_domain_pass(),
        "generated_fixtures_and_states_pass": _generated_fixtures_pass(),
        "producer_and_renderer_boundaries_pass": _producer_and_renderer_boundaries_pass(),
        "network_and_import_boundaries_pass": _network_and_import_boundaries_pass(),
        "dependency_supply_chain_pass": _dependencies_pass(),
        "source_manifest_exact": _source_manifest_matches(),
        "validation_and_coverage_pass": _validation_pass(),
        "sbom_complete": _sbom_pass(),
        "visual_manifest_exact": _visual_manifest_pass(),
        "generated_outputs_untracked": _generated_outputs_untracked(),
    }
    if require_exit_records:
        result["exit_records_present"] = all((ROOT / value).is_file() for value in EXIT_RECORDS)
        result["exit_package_exact"] = _exit_package_pass()
    return result


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
