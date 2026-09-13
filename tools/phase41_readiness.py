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
START_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-1-start-authorization-package.json"
START_AUTHORIZATION_PATH = ROOT / "contracts/phase-4/p4-1-start-authorization.json"
EVIDENCE_PATH = ROOT / "contracts/phase-4/p4-1/evidence.json"
EVIDENCE_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-1/evidence-package.json"
ACCEPTANCE_PROPOSAL_PATH = ROOT / "contracts/phase-4/p4-1/acceptance-proposal.json"
ACCEPTANCE_PATH = ROOT / "contracts/phase-4/p4-1/acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = (
    "43EDF72ADE8328AEABE0F295ACC649F76229D233F8B0FB7E2D1D5C2E43B9ECA6"
)
EXPECTED_ACCEPTANCE_SHA256 = (
    "6E709ADF3BC07904F6CAE3C97A9085B73880642A892569D86A92869C662F1EE3"
)
ACCEPTED_IMPLEMENTATION_COMMIT = "ad44f3e3af292e5a134b45566fc16f09884861a2"
EXPECTED_P4_0_ACCEPTANCE_SHA256 = (
    "09D310D21D724DCA681A45FB32AD81EFC0CD2CB5A929C6C1790666EFEF3ACCDE"
)
P4_0_IMPLEMENTATION_COMMIT = "2e35bd28aa33c2ebed6fa0bd6486fb26a7d9655d"
EXPECTED_BRANCH = "codex/phase4-correlation-foundation"
EXPECTED_MIGRATION = "0013_correlation_foundation"
LEGACY_MIGRATION_TEST_PATH = "tests/test_phase40_migration.py"
EXPECTED_LEGACY_MIGRATION_TEST_SHA256 = (
    "E748B7E8C4D11E0CE7A02E58135D1AFED30D662F84D7306F20231C6931BC9867"
)
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
    }
)
PACKAGE_CONTROL_PATHS = frozenset(
    {
        "contracts/phase-4/p4-1/evidence-package.json",
        "contracts/phase-4/p4-1/acceptance-proposal.json",
        "contracts/phase-4/p4-1/acceptance.json",
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
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _git_json(commit: str, path: str) -> dict[str, Any]:
    return json.loads(_git_bytes("show", f"{commit}:{path}").decode("utf-8"))


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


def _allowed_paths(package: dict[str, Any]) -> set[str]:
    paths = set(package["exact_additive_implementation_paths"])
    paths.update(
        item["path"] for item in package["exact_existing_paths_allowed_to_change"]
    )
    if (
        _git_canonical_text_sha256(
            ACCEPTED_IMPLEMENTATION_COMMIT,
            LEGACY_MIGRATION_TEST_PATH,
        )
        == EXPECTED_LEGACY_MIGRATION_TEST_SHA256
    ):
        paths.add(LEGACY_MIGRATION_TEST_PATH)
    paths.add("contracts/phase-4/p4-1/acceptance.json")
    return paths


def _phase3_is_immutable(checkpoint: str, target: str = "HEAD") -> bool:
    migration_paths = [
        f"migrations/versions/{index:04d}_{name}.py"
        for index, name in (
            (1, "camera_registry"),
            (2, "camera_version"),
            (3, "camera_integrity"),
            (4, "stream_management"),
            (5, "playback_sessions"),
            (6, "onvif_capability_management"),
            (7, "onvif_operations"),
            (8, "analytics_assignments"),
            (9, "generated_analytics"),
            (10, "generated_tracking"),
            (11, "geometry_events"),
            (12, "intelligence_control_plane"),
        )
    ]
    changed = _git(
        "diff",
        "--name-only",
        checkpoint,
        target,
        "--",
        "contracts/phase-3",
        "docs/phase-3",
        *migration_paths,
    )
    return not changed


def _p4_0_readiness_passes() -> bool:
    acceptance_path = ROOT / "contracts/phase-4/p4-0-acceptance.json"
    package_path = ROOT / "contracts/phase-4/p4-0-evidence-package.json"
    if not acceptance_path.is_file() or not package_path.is_file():
        return False
    acceptance = _json(acceptance_path)
    package = _json(package_path)
    if not (
        _sha256(acceptance_path) == EXPECTED_P4_0_ACCEPTANCE_SHA256
        and acceptance.get("effective") is True
        and acceptance.get("decision_id") == "D-P4.0-ACCEPTANCE"
        and acceptance.get("accepted_branch") == "codex/phase4-contracts-guardrails"
        and acceptance.get("accepted_implementation_commit")
        == P4_0_IMPLEMENTATION_COMMIT
        and acceptance.get("evidence_package", {}).get("sha256")
        == _sha256(package_path)
        and acceptance.get("evidence_package", {}).get("canonical_component_digest")
        == package.get("content_digest")
        and _is_ancestor(P4_0_IMPLEMENTATION_COMMIT)
    ):
        return False
    return _evidence_package_is_exact(
        package,
        set(),
        source_commit=P4_0_IMPLEMENTATION_COMMIT,
    )


def _json_result(value: str) -> dict[str, Any]:
    result = json.loads(value)
    if not isinstance(result, dict):
        raise TypeError("readiness output is not an object")
    return result


def _generated_fixtures_are_exact() -> bool:
    process = subprocess.run(
        [sys.executable, str(ROOT / "tools/phase41_generated_correlation.py"), "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return process.returncode == 0


def _correlation_imports_are_closed() -> bool:
    imported: set[str] = set()
    for path in (ROOT / "app/hcam/intelligence/correlation").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    return imported.isdisjoint(PROHIBITED_IMPORTS)


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
    return bool(
        required_components.issubset(paths)
        and package.get("content_digest")
        == _canonical_digest({"components": components})
    )


def _validation_is_complete(evidence: dict[str, Any]) -> bool:
    validation = evidence.get("validation", {})
    required = (
        "focused_generated_suite",
        "coverage",
        "sqlite_migration_cycle",
        "postgresql_postgis",
        "full_regression_suite",
        "static_and_packaging",
        "historical_regression",
    )
    return all(
        isinstance(validation.get(name), dict)
        and validation[name].get("status") == "passed"
        for name in required
    )


def collect_checks() -> dict[str, bool]:
    package = _json(START_PACKAGE_PATH)
    authorization = _json(START_AUTHORIZATION_PATH)
    checkpoint = authorization["planning_checkpoint_commit"]
    changed = _changed_paths(checkpoint)
    allowed = _allowed_paths(package)
    database = _git_json(
        ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/database.json"
    )
    contracts = _git_json(
        ACCEPTED_IMPLEMENTATION_COMMIT,
        "contracts/phase-4/intelligence-contracts.json",
    )
    openapi = _git_json(
        ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/openapi.json"
    )
    delta_database = _json(ROOT / "contracts/phase-4/p4-1/database.json")
    delta_openapi = _json(ROOT / "contracts/phase-4/p4-1/openapi.json")
    migration_source = (
        ROOT / "migrations/versions/0013_correlation_foundation.py"
    ).read_text(encoding="utf-8")
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
        and acceptance.get("decision_id") == "D-P4.1-ACCEPTANCE"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit")
        == ACCEPTED_IMPLEMENTATION_COMMIT
        and acceptance.get("evidence_package", {}).get("sha256")
        == _sha256(EVIDENCE_PACKAGE_PATH)
        and acceptance.get("evidence_package", {}).get("canonical_component_digest")
        == evidence_package.get("content_digest")
    )
    if acceptance_exact:
        changed = _changed_paths_between(checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT)
        required_components = (
            _changed_paths_between(checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT)
            - PACKAGE_CONTROL_PATHS
        )
        source_commit: str | None = ACCEPTED_IMPLEMENTATION_COMMIT
    else:
        required_components = changed - PACKAGE_CONTROL_PATHS
        source_commit = None
    package_exact = bool(evidence_package) and _evidence_package_is_exact(
        evidence_package,
        required_components,
        source_commit=source_commit,
    )
    p4_0_acceptance_path = ROOT / "contracts/phase-4/p4-0-acceptance.json"
    p4_1_paths = openapi.get("p4_1_read_paths", {})
    all_p4_1_methods = [method for methods in p4_1_paths.values() for method in methods]

    return {
        "start_package_exact": _sha256(START_PACKAGE_PATH)
        == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": (
            authorization.get("effective") is True
            and authorization.get("decision_id") == "D-P4.1-START"
            and authorization.get("branch") == EXPECTED_BRANCH
            and authorization.get("package", {}).get("sha256")
            == EXPECTED_START_PACKAGE_SHA256
        ),
        "accepted_branch_binding_exact": (
            acceptance.get("accepted_branch") == EXPECTED_BRANCH
        ),
        "planning_checkpoint_ancestor": _is_ancestor(checkpoint),
        "accepted_implementation_commit_ancestor": _is_ancestor(
            ACCEPTED_IMPLEMENTATION_COMMIT
        ),
        "changed_paths_allowlisted": changed.issubset(allowed),
        "legacy_migration_amendment_exact": (
            _git_canonical_text_sha256(
                ACCEPTED_IMPLEMENTATION_COMMIT,
                LEGACY_MIGRATION_TEST_PATH,
            )
            == EXPECTED_LEGACY_MIGRATION_TEST_SHA256
        ),
        "phase3_and_0012_immutable": _phase3_is_immutable(
            checkpoint,
            ACCEPTED_IMPLEMENTATION_COMMIT if acceptance_exact else "HEAD",
        ),
        "p4_0_acceptance_exact": _sha256(p4_0_acceptance_path)
        == EXPECTED_P4_0_ACCEPTANCE_SHA256,
        "p4_0_historical_readiness": _p4_0_readiness_passes(),
        "generated_fixtures_exact": _generated_fixtures_are_exact(),
        "correlation_imports_closed": _correlation_imports_are_closed(),
        "migration_0013_exact": (
            'revision: str = "0013_correlation_foundation"' in migration_source
            and 'down_revision: str | None = "0012_intelligence_control_plane"'
            in migration_source
        ),
        "database_catalog_exact": (
            database.get("revision") == EXPECTED_MIGRATION
            and delta_database.get("revision") == EXPECTED_MIGRATION
            and len(database.get("new_stores", [])) == 5
            and database.get("new_stores") == delta_database.get("new_stores")
            and database.get("read_only_input_store") == "stream_event_outbox"
        ),
        "contract_catalog_exact": (
            contracts.get("schema_version")
            == "hcam.phase4.p4_1.intelligence-contract-catalog.v1"
            and len(contracts.get("p4_1_contract_types", [])) == 13
            and contracts.get("runtime_state")
            == "disabled_by_default_and_forbidden_in_production"
        ),
        "openapi_read_only": (
            len(p4_1_paths) == 5
            and all_p4_1_methods == ["GET"] * 5
            and delta_openapi.get("paths") == p4_1_paths
            and delta_openapi.get("mutation_paths_added") == 0
        ),
        "evidence_validation_complete": _validation_is_complete(evidence),
        "evidence_package_exact": package_exact,
        "acceptance_proposal_non_effective": (
            proposal.get("effective") is False
            and proposal.get("status") == "owner_acceptance_required"
            and proposal.get("technical_gate_status") == "passed"
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
        description="Validate P4.1 generated-correlation readiness"
    )
    parser.add_argument("--json", action="store_true", help="print one JSON result")
    arguments = parser.parse_args()
    try:
        checks = collect_checks()
        result = {
            "schema_version": "hcam.phase4.p4_1.readiness.v1",
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
            "schema_version": "hcam.phase4.p4_1.readiness.v1",
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
        print("P4.1 readiness: " + ("passed" if result["passed"] else "failed"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
