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
START_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-4-start-authorization-package.json"
START_AUTHORIZATION_PATH = ROOT / "contracts/phase-4/p4-4-start-authorization.json"
EVIDENCE_PATH = ROOT / "contracts/phase-4/p4-4/evidence.json"
EVIDENCE_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-4/evidence-package.json"
ACCEPTANCE_PROPOSAL_PATH = ROOT / "contracts/phase-4/p4-4/acceptance-proposal.json"
ACCEPTANCE_PATH = ROOT / "contracts/phase-4/p4-4/acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = (
    "FBEB48A115ED952945045E8945DE7E27E518915E85605A3247ADBAEA701FDF34"
)
EXPECTED_PLANNING_SHA256 = (
    "42C37E17C73C4708FF3FB6B41532085995C514BA251BAC545DEF2E19632A0205"
)
EXPECTED_PLANNING_ACCEPTANCE_SHA256 = (
    "2AF9E45AA0B98B7AB59108AD3685487093A31E8AFA458A9E2D2F2F3125637547"
)
EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256 = (
    "BDFF9678045E07749C65B523BEF06BE2C53D17CFD079A1FDF6AF20ED336BDA84"
)
EXPECTED_ACCEPTANCE_SHA256 = (
    "2E298EAA88E9F2586633955838FBC367641A807F4635866BCE488DC1E60936AD"
)
EXPECTED_OWNER_STATEMENT_SHA256 = (
    "523AAC5C49C483AE3C365A69EB5869762030B1FA6DABC3BE68963A446CFA0FE3"
)
ACCEPTED_IMPLEMENTATION_COMMIT = "9efacc75336cc942db9615c21e371cb3322aea73"
ACCEPTED_CLOSEOUT_COMMIT = "c8d80bf25d089969f411170ce640b6c373f5e017"
EXPECTED_BRANCH = "codex/phase4-reference-integrations"
EXPECTED_MIGRATION = "0016_reference_integrations"
EXPECTED_PARENT_MIGRATION = "0015_alert_lifecycle_orchestration"
EXPECTED_SCENARIOS = 372
EXPECTED_PATHS = {
    "/reference-integrations/candidate-sets/{candidate_set_id}": {"get"},
    "/reference-integrations/controls": {"get", "post"},
    "/reference-integrations/health": {"get"},
    "/reference-integrations/providers": {"get", "post"},
    "/reference-integrations/providers/{provider_version_id}": {"get"},
    "/reference-integrations/queries": {"post"},
    "/reference-integrations/queries/{job_id}": {"get"},
    "/reference-integrations/queries/{job_id}/cancel": {"post"},
}
EXPECTED_TABLES = {
    "reference_candidate_sets",
    "reference_catalogue_records",
    "reference_catalogue_snapshots",
    "reference_circuit_states",
    "reference_control_revisions",
    "reference_integration_outbox",
    "reference_provider_versions",
    "reference_query_attempts",
    "reference_query_jobs",
    "reference_review_handoffs",
}
PROHIBITED_IMPORTS = frozenset(
    {
        "aiohttp",
        "cv2",
        "ffmpeg",
        "httpx",
        "importlib",
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
        "contracts/phase-4/p4-4/evidence-package.json",
        "contracts/phase-4/p4-4/acceptance-proposal.json",
        "contracts/phase-4/p4-4/acceptance.json",
    }
)
ACCEPTANCE_SYNC_PATHS = frozenset(
    {
        "contracts/phase-4/p4-4/acceptance.json",
        "docs/phase-4/p4-4-evidence-review.md",
        "docs/phase-4/status.md",
        "tests/test_phase44_readiness.py",
        "tools/phase44_readiness.py",
    }
)
IGNORED_USER_PREFIXES = ("output/",)


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


def _json_at(commit: str, path: str) -> dict[str, Any]:
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


def _is_ancestor(ancestor: str) -> bool:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return process.returncode == 0


def _status_paths() -> set[str]:
    paths: set[str] = set()
    for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        normalized = value.replace("\\", "/").strip('"')
        if normalized.startswith(IGNORED_USER_PREFIXES):
            continue
        paths.add(normalized)
    return paths


def _changed_paths(checkpoint: str) -> set[str]:
    tracked = {
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", checkpoint).splitlines()
        if item
    }
    return tracked | _status_paths()


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
    return paths


def _immutable_history_is_exact(checkpoint: str) -> bool:
    immutable = [
        "contracts/phase-3",
        "docs/phase-3",
        "contracts/phase-4/p4-0-acceptance.json",
        "contracts/phase-4/p4-0-evidence.json",
        "contracts/phase-4/p4-0-evidence-package.json",
        "contracts/phase-4/p4-1",
        "contracts/phase-4/p4-2",
        "contracts/phase-4/p4-3",
        "migrations/versions/0011_geometry_events.py",
        "migrations/versions/0012_intelligence_control_plane.py",
        "migrations/versions/0013_correlation_foundation.py",
        "migrations/versions/0014_rule_authoring_evaluation.py",
        "migrations/versions/0015_alert_lifecycle_orchestration.py",
    ]
    return not _git("diff", "--name-only", checkpoint, "--", *immutable)


def _run_json_tool(path: str, *arguments: str) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(ROOT / path), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if process.stderr:
        return {"passed": False}
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError:
        return {"passed": False}
    if process.returncode != 0 or not isinstance(value, dict):
        return {"passed": False}
    return value


def _generated_fixtures_are_exact() -> bool:
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/phase44_generated_integrations.py"),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if process.returncode != 0 or process.stderr:
        return False
    fixture_paths = sorted((ROOT / "contracts/phase-4/p4-4/fixtures").glob("*.json"))
    documents = [_json(path) for path in fixture_paths]
    return bool(
        len(documents) == 11
        and sum(int(item.get("scenario_count", 0)) for item in documents)
        == EXPECTED_SCENARIOS
        and process.stdout.strip()
        == f"P4.4 generated fixtures: {EXPECTED_SCENARIOS} scenarios"
    )


def _integration_imports_are_closed() -> bool:
    imported: set[str] = set()
    calls: set[str] = set()
    source_root = ROOT / "app/hcam/intelligence/integrations"
    for path in source_root.glob("*.py"):
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


def _migration_is_exact() -> bool:
    source = (ROOT / "migrations/versions/0016_reference_integrations.py").read_text(
        encoding="utf-8"
    )
    return bool(
        f'revision: str = "{EXPECTED_MIGRATION}"' in source
        and f'down_revision: str | None = "{EXPECTED_PARENT_MIGRATION}"' in source
        and all(f'"{table}"' in source for table in EXPECTED_TABLES)
        and "ENABLE ROW LEVEL SECURITY" in source
        and "FORCE ROW LEVEL SECURITY" in source
        and "for table in NEW_TABLES" in source
        and "for table in reversed(NEW_TABLES)" in source
    )


def _catalogs_are_exact() -> bool:
    database = _json_at(ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/database.json")
    delta_database = _json_at(
        ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/p4-4/database.json"
    )
    contracts = _json_at(
        ACCEPTED_IMPLEMENTATION_COMMIT,
        "contracts/phase-4/intelligence-contracts.json",
    )
    delta_contracts = _json_at(
        ACCEPTED_IMPLEMENTATION_COMMIT,
        "contracts/phase-4/p4-4/reference-integration-contracts.json",
    )
    openapi = _json_at(ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/openapi.json")
    delta_openapi = _json_at(
        ACCEPTED_IMPLEMENTATION_COMMIT, "contracts/phase-4/p4-4/openapi.json"
    )
    return bool(
        database.get("revision") == EXPECTED_MIGRATION
        and delta_database.get("revision") == EXPECTED_MIGRATION
        and set(database.get("new_stores", [])) == EXPECTED_TABLES
        and database.get("new_stores") == delta_database.get("new_stores")
        and contracts.get("p4_4_contract_types")
        == delta_contracts.get("contract_types")
        and openapi.get("p4_4_paths") == delta_openapi.get("paths")
        and delta_openapi.get("default_enabled") is False
        and delta_openapi.get("production_allowed") is False
        and delta_contracts.get("identity_state") == "not_established"
        and delta_contracts.get("review_authority") == "mandatory_review"
    )


def _runtime_surface_is_closed() -> bool:
    from hcam.main import create_app
    from hcam.settings import Settings

    default_app = create_app(Settings(environment="test"))
    enabled_app = create_app(
        Settings(
            environment="test",
            intelligence_generated_reference_integrations_enabled=True,
        )
    )
    try:
        default_paths = default_app.openapi().get("paths", {})
        enabled_paths = enabled_app.openapi().get("paths", {})
        if any(path in default_paths for path in EXPECTED_PATHS):
            return False
        for path, methods in EXPECTED_PATHS.items():
            if path not in enabled_paths or not methods.issubset(enabled_paths[path]):
                return False
        prohibited_fragments = (
            "/execute",
            "/worker",
            "/dispatch",
            "/enforce",
            "/confirm-identity",
        )
        return not any(
            fragment in path
            for path in enabled_paths
            for fragment in prohibited_fragments
        )
    finally:
        default_app.state.database.dispose()
        enabled_app.state.database.dispose()


def _settings_are_closed() -> bool:
    from hcam.settings import Settings

    defaults = Settings()
    names = (
        "intelligence_generated_reference_integrations_enabled",
        "intelligence_generated_reference_manual_queries_enabled",
        "intelligence_generated_reference_hypothesis_enrichment_enabled",
    )
    if any(getattr(defaults, name) for name in names):
        return False
    for name in names:
        try:
            Settings(environment="production", **{name: True})
        except ValueError:
            continue
        return False
    return True


def _evidence_package_is_exact(
    package: dict[str, Any],
    required_components: set[str],
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
        source = ROOT / path
        source_exists = (
            _git_bytes("cat-file", "-e", f"{source_commit}:{path_value}") == b""
            if source_commit
            else source.is_file()
        )
        actual = (
            _canonical_text_sha256_bytes(
                _git_bytes("show", f"{source_commit}:{path_value}")
            )
            if source_commit and source_exists
            else _canonical_text_sha256(source)
            if source_exists
            else ""
        )
        if (
            path.is_absolute()
            or ".." in path.parts
            or path_value in paths
            or not source_exists
            or actual != expected
        ):
            return False
        paths.add(path_value)
    return paths == required_components and package.get(
        "content_digest"
    ) == _canonical_digest({"components": components})


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def seal_evidence_package() -> tuple[str, str]:
    if ACCEPTANCE_PATH.is_file():
        raise RuntimeError("accepted P4.4 evidence cannot be resealed")
    package = _json(START_PACKAGE_PATH)
    authorization = _json(START_AUTHORIZATION_PATH)
    changed = _changed_paths(authorization["implementation_base_commit"])
    required = changed - PACKAGE_CONTROL_PATHS
    if not required or not required.issubset(_allowed_paths(package)):
        raise RuntimeError("P4.4 evidence scope is not exact")
    if not EVIDENCE_PATH.is_file():
        raise RuntimeError("P4.4 evidence record is absent")
    components = [
        {"path": path, "sha256": _canonical_text_sha256(ROOT / path)}
        for path in sorted(required)
    ]
    content_digest = _canonical_digest({"components": components})
    evidence_package = {
        "schema_version": "hcam.phase4.p4_4.evidence-package.v1",
        "package_id": "P4.4-EVIDENCE-PACKAGE-R0",
        "status": "technical_validation_passed_owner_acceptance_pending",
        "generated_on": "2026-09-05",
        "branch": EXPECTED_BRANCH,
        "start_package_sha256": EXPECTED_START_PACKAGE_SHA256,
        "component_digest_mode": "utf8_text_normalized_lf",
        "component_count": len(components),
        "components": components,
        "content_digest": content_digest,
        "generated_only": True,
        "operational": False,
        "remote_git_performed": False,
    }
    _write_json(EVIDENCE_PACKAGE_PATH, evidence_package)
    package_sha256 = _sha256(EVIDENCE_PACKAGE_PATH)
    statement = (
        "D-P4.4-ACCEPTANCE: I, mayank-admin, accept P4.4 evidence package "
        f"P4.4-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha256} and canonical "
        f"component digest {content_digest}, including its generated-only "
        "implementation evidence, validation results, authorized P4.3 historical "
        "readiness transition, explicit PostgreSQL and vulnerability-refresh "
        "limitations, and documented safety boundaries. This acceptance completes "
        "P4.4 only. It does not authorize P4.5, real providers, credentials or "
        "secrets, authentication extension loading, external workflow engines, "
        "provider or Sentinel network access, Government or private data, cameras "
        "or media, models or datasets, operational alerts or actions, containers, "
        "Kubernetes, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase4.p4_4.acceptance-proposal.v1",
        "decision_id": "D-P4.4-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "prepared_on": "2026-09-05",
        "branch": EXPECTED_BRANCH,
        "evidence_package_path": "contracts/phase-4/p4-4/evidence-package.json",
        "evidence_package_sha256": package_sha256,
        "evidence_content_digest": content_digest,
        "owner_acceptance_statement_sha256": hashlib.sha256(statement.encode("utf-8"))
        .hexdigest()
        .upper(),
        "owner_acceptance_statement": statement,
        "authorization_effect": "complete_P4_4_only_after_exact_owner_acceptance",
        "generated_only": True,
        "operational": False,
    }
    _write_json(ACCEPTANCE_PROPOSAL_PATH, proposal)
    return package_sha256, content_digest


def collect_checks() -> dict[str, bool]:
    package = _json(START_PACKAGE_PATH)
    authorization = _json(START_AUTHORIZATION_PATH)
    checkpoint = authorization["implementation_base_commit"]
    changed = _changed_paths(checkpoint)
    allowed = _allowed_paths(package)
    historical = _run_json_tool("tools/phase43_readiness.py", "--json")
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
        and acceptance.get("status") == "owner_accepted"
        and acceptance.get("decision_id") == "D-P4.4-ACCEPTANCE"
        and acceptance.get("accepted_by") == "mayank-admin"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit")
        == ACCEPTED_IMPLEMENTATION_COMMIT
        and acceptance.get("evidence_package", {}).get("package_id")
        == "P4.4-EVIDENCE-PACKAGE-R0"
        and acceptance.get("evidence_package", {}).get("path")
        == "contracts/phase-4/p4-4/evidence-package.json"
        and acceptance.get("evidence_package", {}).get("sha256")
        == _sha256(EVIDENCE_PACKAGE_PATH)
        and acceptance.get("evidence_package", {}).get("canonical_component_digest")
        == evidence_package.get("content_digest")
        and acceptance.get("accepted_progress", {}).get("phase_4_points") == 70
        and acceptance.get("accepted_progress", {}).get("p4_4_points") == 15
        and acceptance.get("owner_statement_sha256") == EXPECTED_OWNER_STATEMENT_SHA256
        and acceptance.get("owner_statement")
        == proposal.get("owner_acceptance_statement")
        and hashlib.sha256(acceptance.get("owner_statement", "").encode("utf-8"))
        .hexdigest()
        .upper()
        == EXPECTED_OWNER_STATEMENT_SHA256
    )
    validation = evidence.get("validation", {})
    required_validation = (
        "generated_contracts",
        "focused_suite",
        "coverage",
        "sqlite_migration_cycle",
        "postgresql_rls_and_concurrency",
        "full_regression_suite",
        "static_and_packaging",
        "historical_compatibility",
        "security_recovery",
        "dependency_validation",
    )
    source_commit = ACCEPTED_IMPLEMENTATION_COMMIT if acceptance_exact else None
    implementation_changed = (
        _changed_paths_between(checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT)
        if acceptance_exact
        else changed
    )
    required_components = implementation_changed - PACKAGE_CONTROL_PATHS
    return {
        "start_package_exact": _sha256(START_PACKAGE_PATH)
        == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": (
            authorization.get("effective") is True
            and authorization.get("decision_id") == "D-P4.4-START"
            and authorization.get("accepted_package", {}).get("sha256")
            == EXPECTED_START_PACKAGE_SHA256
        ),
        "branch_exact": acceptance_exact
        or _git("branch", "--show-current") == EXPECTED_BRANCH,
        "implementation_base_ancestor": _is_ancestor(checkpoint),
        "accepted_implementation_commit_ancestor": (
            not acceptance_exact or _is_ancestor(ACCEPTED_IMPLEMENTATION_COMMIT)
        ),
        "changed_paths_allowlisted": implementation_changed.issubset(allowed),
        "acceptance_sync_paths_allowlisted": (
            not acceptance_exact
            or _changed_paths_between(
                ACCEPTED_IMPLEMENTATION_COMMIT, ACCEPTED_CLOSEOUT_COMMIT
            ).issubset(ACCEPTANCE_SYNC_PATHS)
        ),
        "immutable_history_exact": _immutable_history_is_exact(checkpoint),
        "predecessor_acceptance_exact": _sha256(
            ROOT / "contracts/phase-4/p4-3/acceptance.json"
        )
        == EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256,
        "predecessor_historical_readiness": historical.get("passed") is True,
        "planning_package_exact": _sha256(
            ROOT / "contracts/phase-4/p4-4-planning-r1-package.json"
        )
        == EXPECTED_PLANNING_SHA256,
        "planning_acceptance_exact": _sha256(
            ROOT / "contracts/phase-4/p4-4-planning-r1-acceptance.json"
        )
        == EXPECTED_PLANNING_ACCEPTANCE_SHA256,
        "immutable_dependencies_exact": all(
            _sha256(ROOT / item["path"]) == item["sha256"]
            for item in package["immutable_dependency_bindings"]
        ),
        "generated_fixtures_exact": _generated_fixtures_are_exact(),
        "integration_imports_and_dynamic_execution_closed": (
            _integration_imports_are_closed()
        ),
        "migration_0016_and_forced_rls_exact": _migration_is_exact(),
        "catalogs_exact": _catalogs_are_exact(),
        "runtime_surface_default_off_and_bounded": _runtime_surface_is_closed(),
        "settings_default_off_and_production_forbidden": _settings_are_closed(),
        "evidence_validation_complete": bool(validation)
        and all(
            isinstance(validation.get(name), dict)
            and validation[name].get("status") in {"passed", "not_available"}
            for name in required_validation
        ),
        "evidence_package_exact": bool(evidence_package)
        and _evidence_package_is_exact(
            evidence_package, required_components, source_commit
        ),
        "acceptance_proposal_non_effective": (
            proposal.get("effective") is False
            and proposal.get("status") == "owner_acceptance_required"
            and proposal.get("decision_id") == "D-P4.4-ACCEPTANCE"
        ),
        "acceptance_proposal_bound": bool(evidence_package)
        and bool(proposal)
        and proposal.get("evidence_package_sha256") == _sha256(EVIDENCE_PACKAGE_PATH)
        and proposal.get("evidence_content_digest")
        == evidence_package.get("content_digest"),
        "owner_acceptance_exact": acceptance_exact,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate P4.4 generated reference-integration readiness"
    )
    parser.add_argument("--json", action="store_true", help="print one JSON result")
    parser.add_argument(
        "--seal-evidence",
        action="store_true",
        help="write the bounded evidence package and non-effective acceptance proposal",
    )
    arguments = parser.parse_args()
    try:
        if arguments.seal_evidence:
            seal_evidence_package()
        checks = collect_checks()
        result = {
            "schema_version": "hcam.phase4.p4_4.readiness.v1",
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
            "schema_version": "hcam.phase4.p4_4.readiness.v1",
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
        print("P4.4 readiness: " + ("passed" if result["passed"] else "failed"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
