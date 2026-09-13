from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
START_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-2-start-authorization-package.json"
START_AUTHORIZATION_PATH = ROOT / "contracts/phase-4/p4-2-start-authorization.json"
EVIDENCE_PATH = ROOT / "contracts/phase-4/p4-2/evidence.json"
EVIDENCE_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-2/evidence-package.json"
ACCEPTANCE_PROPOSAL_PATH = ROOT / "contracts/phase-4/p4-2/acceptance-proposal.json"
ACCEPTANCE_PATH = ROOT / "contracts/phase-4/p4-2/acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = (
    "F1C4B64883A23240FB787E5203CD62395AA025304247028392BCF20218C3D263"
)
EXPECTED_ACCEPTANCE_SHA256 = (
    "B5E9AFC50A1D24209F48F1828D6104EC21FACD10A435B8DFBE20FB9EB065BDC6"
)
EXPECTED_OWNER_STATEMENT_SHA256 = (
    "245A65F24451FF181184D21F466B06F32074D18B0802B94F1B64479166A5EB19"
)
ACCEPTED_IMPLEMENTATION_COMMIT = "393ae258e84df8ab542665144a45f8e9b0b83c5b"
EXPECTED_BRANCH = "codex/phase4-rule-authoring-evaluation"
EXPECTED_MIGRATION = "0014_rule_authoring_evaluation"
HISTORICAL_COMPATIBILITY_AMENDMENT = {
    "tests/test_phase40_migration.py": (
        "E748B7E8C4D11E0CE7A02E58135D1AFED30D662F84D7306F20231C6931BC9867"
    ),
    "tests/test_phase41_migration.py": (
        "1561B3DBF0DCE197FFD2BAC82074B7648C2C5CB0EDB9D1A58D96DC709E60A109"
    ),
    "tests/test_phase40_readiness.py": (
        "51A4B45A8D2332FCD3CFA58183ADB8E3FE868635DA9D8D9AE149163A63F205F3"
    ),
}
PROHIBITED_IMPORTS = frozenset(
    {
        "cv2",
        "ffmpeg",
        "httpx",
        "onnx",
        "onnxruntime",
        "requests",
        "socket",
        "subprocess",
        "torch",
        "ultralytics",
        "urllib",
    }
)
PACKAGE_CONTROL_PATHS = frozenset(
    {
        "contracts/phase-4/p4-2/evidence-package.json",
        "contracts/phase-4/p4-2/acceptance-proposal.json",
        "contracts/phase-4/p4-2/acceptance.json",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _canonical_text_sha256(path: Path) -> str:
    normalized = (
        path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _canonical_text_sha256_bytes(content: bytes) -> str:
    normalized = content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("readiness JSON is not an object")
    return value


def _git_json(commit: str, path: str) -> dict[str, Any]:
    value = json.loads(_git_bytes("show", f"{commit}:{path}").decode("utf-8"))
    if not isinstance(value, dict):
        raise TypeError("historical readiness JSON is not an object")
    return value


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("local Git readiness query failed")
    return process.stdout.rstrip()


def _git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("local Git historical readiness query failed")
    return process.stdout


def _git_canonical_text_sha256(commit: str, path: str) -> str:
    return _canonical_text_sha256_bytes(_git_bytes("show", f"{commit}:{path}"))


def _is_ancestor(ancestor: str) -> bool:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return process.returncode == 0


def _changed_paths(checkpoint: str) -> set[str]:
    paths = {
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", checkpoint).splitlines()
        if item
    }
    for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path.replace("\\", "/").strip('"'))
    return paths


def _changed_paths_between(checkpoint: str, commit: str) -> set[str]:
    return {
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", checkpoint, commit).splitlines()
        if item
    }


def _historical_compatibility_amendment_is_bound(checkpoint: str) -> bool:
    return all(
        _git_canonical_text_sha256(checkpoint, path) == expected
        for path, expected in HISTORICAL_COMPATIBILITY_AMENDMENT.items()
    )


def _allowed_paths(package: dict[str, Any], checkpoint: str) -> set[str]:
    paths = set(package["exact_additive_implementation_paths"])
    paths.update(
        item["path"] for item in package["exact_existing_paths_allowed_to_change"]
    )
    if _historical_compatibility_amendment_is_bound(checkpoint):
        paths.update(HISTORICAL_COMPATIBILITY_AMENDMENT)
    paths.add("contracts/phase-4/p4-2/acceptance.json")
    return paths


def _historical_scope_immutable(checkpoint: str) -> bool:
    paths = [
        "contracts/phase-3",
        "docs/phase-3",
        "contracts/phase-4/p4-0-acceptance.json",
        "contracts/phase-4/p4-0-evidence.json",
        "contracts/phase-4/p4-0-evidence-package.json",
        "contracts/phase-4/p4-1",
        "migrations/versions/0011_geometry_events.py",
        "migrations/versions/0012_intelligence_control_plane.py",
        "migrations/versions/0013_correlation_foundation.py",
    ]
    return not _git("diff", "--name-only", checkpoint, "--", *paths)


def _run_json_tool(path: str, *arguments: str) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(ROOT / path), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if process.returncode != 0 or process.stderr:
        return {"passed": False}
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError:
        return {"passed": False}


def _rule_imports_are_closed() -> bool:
    imported: set[str] = set()
    calls: set[str] = set()
    for path in (ROOT / "app/hcam/intelligence/rules").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
    return imported.isdisjoint(PROHIBITED_IMPORTS) and calls.isdisjoint(
        {"eval", "exec", "compile", "open", "__import__"}
    )


def _catalogs_are_exact(*, source_commit: str | None = None) -> bool:
    def load(path: str) -> dict[str, Any]:
        if source_commit is not None:
            return _git_json(source_commit, path)
        return _json(ROOT / path)

    database = load("contracts/phase-4/database.json")
    delta_database = load("contracts/phase-4/p4-2/database.json")
    contracts = load("contracts/phase-4/intelligence-contracts.json")
    delta_contracts = load("contracts/phase-4/p4-2/rule-contracts.json")
    openapi = load("contracts/phase-4/openapi.json")
    delta_openapi = load("contracts/phase-4/p4-2/openapi.json")
    return bool(
        database.get("revision") == EXPECTED_MIGRATION
        and delta_database.get("revision") == EXPECTED_MIGRATION
        and database.get("new_stores") == delta_database.get("new_stores")
        and len(database.get("new_stores", [])) == 7
        and contracts.get("schema_version")
        == "hcam.phase4.p4_2.intelligence-contract-catalog.v1"
        and contracts.get("p4_2_contract_types")
        == delta_contracts.get("contract_types")
        and openapi.get("p4_2_paths") == delta_openapi.get("paths")
        and openapi.get("default_enabled") is False
        and openapi.get("production_allowed") is False
    )


def _runtime_surface_is_closed() -> bool:
    from hcam.main import create_app
    from hcam.settings import Settings

    settings = Settings(
        environment="test",
        intelligence_generated_control_plane_enabled=True,
        intelligence_generated_correlation_enabled=True,
        intelligence_generated_rule_evaluation_enabled=True,
    )
    application = create_app(settings)
    try:
        paths = application.openapi().get("paths", {})
        expected = _json(ROOT / "contracts/phase-4/p4-2/openapi.json")["paths"]
        for path, methods in expected.items():
            if path not in paths or not set(
                method.lower() for method in methods
            ).issubset(paths[path]):
                return False
        prohibited = (
            "/intelligence-rules/{record_id}/activate",
            "/intelligence-rules/{record_id}/evaluate",
            "/intelligence-rule-evaluations",
        )
        return all(path not in paths for path in prohibited)
    finally:
        application.state.database.dispose()


def _settings_are_closed() -> bool:
    from hcam.settings import Settings

    defaults = Settings()
    if defaults.intelligence_generated_rule_evaluation_enabled is not False:
        return False
    try:
        Settings(
            environment="production",
            intelligence_generated_rule_evaluation_enabled=True,
        )
    except ValueError:
        return True
    return False


def _evidence_package_is_exact(
    package: dict[str, Any],
    required_components: set[str],
    *,
    source_commit: str | None = None,
) -> bool:
    if package.get("component_digest_mode") != "utf8_text_normalized_lf":
        return False
    components = package.get("components")
    if not isinstance(components, list) or not components:
        return False
    paths: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            return False
        path_value = component.get("path")
        expected = component.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected, str):
            return False
        path = Path(path_value)
        if path.is_absolute() or ".." in path.parts or path_value in paths:
            return False
        if source_commit is None:
            source = ROOT / path
            if not source.is_file() or _canonical_text_sha256(source) != expected:
                return False
        else:
            try:
                content = _git_bytes("show", f"{source_commit}:{path_value}")
            except RuntimeError:
                return False
            if _canonical_text_sha256_bytes(content) != expected:
                return False
        paths.add(path_value)
    return paths == required_components and package.get(
        "content_digest"
    ) == _canonical_digest({"components": components})


def collect_checks() -> dict[str, bool]:
    package = _json(START_PACKAGE_PATH)
    authorization = _json(START_AUTHORIZATION_PATH)
    checkpoint = authorization["planning_checkpoint"]
    changed = _changed_paths(checkpoint)
    dependency_checks = [
        _sha256(ROOT / item["path"]) == item["sha256"]
        for item in package["immutable_dependency_bindings"]
    ]
    migration_source = (
        ROOT / "migrations/versions/0014_rule_authoring_evaluation.py"
    ).read_text(encoding="utf-8")
    generated = _run_json_tool("tools/phase42_generated_rules.py", "check")
    historical = _run_json_tool("tools/phase41_readiness.py", "--json")
    evidence = _json(EVIDENCE_PATH) if EVIDENCE_PATH.is_file() else {}
    evidence_package = (
        _json(EVIDENCE_PACKAGE_PATH) if EVIDENCE_PACKAGE_PATH.is_file() else {}
    )
    proposal = (
        _json(ACCEPTANCE_PROPOSAL_PATH) if ACCEPTANCE_PROPOSAL_PATH.is_file() else {}
    )
    acceptance = _json(ACCEPTANCE_PATH) if ACCEPTANCE_PATH.is_file() else {}
    acceptance_exact = bool(acceptance) and (
        _sha256(ACCEPTANCE_PATH) == EXPECTED_ACCEPTANCE_SHA256
        and acceptance.get("effective") is True
        and acceptance.get("decision_id") == "D-P4.2-ACCEPTANCE"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit")
        == ACCEPTED_IMPLEMENTATION_COMMIT
        and acceptance.get("evidence_package", {}).get("sha256")
        == _sha256(EVIDENCE_PACKAGE_PATH)
        and acceptance.get("evidence_package", {}).get("canonical_component_digest")
        == evidence_package.get("content_digest")
        and acceptance.get("owner_statement_sha256") == EXPECTED_OWNER_STATEMENT_SHA256
        and hashlib.sha256(str(acceptance.get("owner_statement", "")).encode("utf-8"))
        .hexdigest()
        .upper()
        == EXPECTED_OWNER_STATEMENT_SHA256
    )
    if acceptance_exact:
        required_components = (
            _changed_paths_between(checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT)
            - PACKAGE_CONTROL_PATHS
        )
        source_commit: str | None = ACCEPTED_IMPLEMENTATION_COMMIT
        checked_changes = _changed_paths_between(
            checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT
        )
    else:
        required_components = changed - PACKAGE_CONTROL_PATHS
        source_commit = None
        checked_changes = changed
    validation = evidence.get("validation", {})
    required_validation = (
        "focused_generated_suite",
        "coverage",
        "sqlite_migration_cycle",
        "postgresql_rls",
        "full_regression_suite",
        "static_and_packaging",
        "historical_regression",
    )
    return {
        "start_package_exact": _sha256(START_PACKAGE_PATH)
        == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": (
            authorization.get("effective") is True
            and authorization.get("decision_id") == "D-P4.2-START"
            and authorization.get("authorization_package", {}).get("sha256")
            == EXPECTED_START_PACKAGE_SHA256
        ),
        "branch_exact": acceptance_exact
        or _git("branch", "--show-current") == EXPECTED_BRANCH,
        "planning_checkpoint_ancestor": _is_ancestor(checkpoint),
        "accepted_implementation_commit_ancestor": _is_ancestor(
            ACCEPTED_IMPLEMENTATION_COMMIT
        ),
        "changed_paths_allowlisted": checked_changes.issubset(
            _allowed_paths(package, checkpoint)
        ),
        "historical_compatibility_amendment_bound": (
            _historical_compatibility_amendment_is_bound(checkpoint)
        ),
        "accepted_history_immutable": _historical_scope_immutable(checkpoint),
        "p4_1_historical_readiness": historical.get("passed") is True,
        "immutable_dependencies_exact": all(dependency_checks),
        "generated_fixtures_exact": generated.get("passed") is True,
        "rule_imports_and_dynamic_execution_closed": _rule_imports_are_closed(),
        "migration_0014_exact": (
            'revision: str = "0014_rule_authoring_evaluation"' in migration_source
            and 'down_revision: str | None = "0013_correlation_foundation"'
            in migration_source
        ),
        "catalogs_exact": _catalogs_are_exact(source_commit=source_commit),
        "runtime_surface_closed": _runtime_surface_is_closed(),
        "settings_default_off_and_production_forbidden": _settings_are_closed(),
        "evidence_validation_complete": bool(validation)
        and all(
            isinstance(validation.get(name), dict)
            and validation[name].get("status") in {"passed", "not_available"}
            for name in required_validation
        ),
        "evidence_package_exact": bool(evidence_package)
        and _evidence_package_is_exact(
            evidence_package,
            required_components,
            source_commit=source_commit,
        ),
        "acceptance_proposal_non_effective": (
            proposal.get("effective") is False
            and proposal.get("status") == "owner_acceptance_required"
        ),
        "acceptance_proposal_bound": bool(evidence_package)
        and bool(proposal)
        and (
            proposal.get("evidence_package_sha256") == _sha256(EVIDENCE_PACKAGE_PATH)
            and proposal.get("evidence_content_digest")
            == evidence_package.get("content_digest")
        ),
        "owner_acceptance_exact": acceptance_exact,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate P4.2 generated-rule readiness"
    )
    parser.add_argument("--json", action="store_true", help="print one JSON result")
    arguments = parser.parse_args()
    try:
        checks = collect_checks()
        result = {
            "schema_version": "hcam.phase4.p4_2.readiness.v1",
            "passed": all(checks.values()),
            "checks": checks,
        }
    except (
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
        SyntaxError,
    ) as exc:
        result = {
            "schema_version": "hcam.phase4.p4_2.readiness.v1",
            "passed": False,
            "failure_code": "readiness_validation_failed",
            "detail": type(exc).__name__,
        }
    if arguments.json:
        print(
            json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        )
    else:
        for name, value in result.get("checks", {}).items():
            print(f"{'PASS' if value else 'FAIL'} {name}")
        print("P4.2 readiness: " + ("passed" if result["passed"] else "failed"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
