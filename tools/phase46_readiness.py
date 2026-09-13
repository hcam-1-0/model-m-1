from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from hcam.main import create_app
from hcam.operations.platform import contracts
from hcam.operations.platform.bounds import (
    MAX_BURN_WINDOWS,
    MAX_CAPABILITY_PROFILES,
    MAX_CAPACITY_STEPS,
    MAX_CIRCUIT_CLASSES,
    MAX_CLOSED_VALUES_PER_LABEL,
    MAX_CONTRACT_BYTES,
    MAX_CONTROL_DEPTH,
    MAX_DOCUMENT_DEPTH,
    MAX_DOCUMENT_ITEMS,
    MAX_GENERATED_SERIES,
    MAX_JOB_ATTEMPTS,
    MAX_JOB_PAYLOAD_BYTES,
    MAX_LABELS_PER_METRIC,
    MAX_METRIC_DEFINITIONS,
    MAX_PLACEMENT_NODES,
    MAX_PLACEMENT_SERVICES,
    MAX_RECOVERY_ASSETS,
    MAX_RECOVERY_DEPENDENCIES,
    MAX_SAFE_FAILURE_PARAMETERS,
    MAX_STRING_BYTES,
    MAX_SUPPLY_CHAIN_COMPONENTS,
    MAX_TRACE_STATE_BYTES,
    MAX_UNIFIED_SEARCH_ITEMS,
    MAX_WORKER_CLASSES,
    WORKER_LEASE_SECONDS,
)
from hcam.operations.platform.registry import (
    CAPACITY_MODES,
    CAPACITY_SCALES,
    FAILURE_REGISTRY,
    METRIC_DEFINITIONS,
    METRIC_LABEL_VALUES,
    PLACEMENT_REASONS,
    RECOVERY_TIERS,
    SERVICE_CLASSES,
    WORKER_CLASSES,
)
from hcam.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
P46_ROOT = ROOT / "contracts/phase-4/p4-6"
START_PACKAGE = ROOT / "contracts/phase-4/p4-6-start-authorization-package.json"
START_AUTHORIZATION = ROOT / "contracts/phase-4/p4-6-start-authorization.json"
EVIDENCE_PATH = P46_ROOT / "evidence.json"
EVIDENCE_PACKAGE_PATH = P46_ROOT / "evidence-package.json"
ACCEPTANCE_PROPOSAL_PATH = P46_ROOT / "acceptance-proposal.json"
ACCEPTANCE_PATH = P46_ROOT / "acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = "2E1D5F921EB7C972192FE460D3B238F39D8D792C7869A8F338E291618314F779"
EXPECTED_PLANNING_SHA256 = "5EF1814AE432FD7C15E3A9BD92EF6344CDA210A2D872A362C45D10CCADA411F5"
EXPECTED_PLANNING_ACCEPTANCE_SHA256 = "F56FC37C6711AA3704145450FC7F8225C24340331A642F8ECD59561944837D9E"
EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256 = "856484AA45BB0775DD1A967AE1AFC0135E64ADC826DAE339A31FB1806CF26AB2"
EXPECTED_BRANCH = "codex/phase4-operations-security-scale"
EXPECTED_MIGRATION = "0018_operations_security_scale"
EXPECTED_PARENT_MIGRATION = "0017_investigation_evidence"
EXPECTED_SCENARIOS = 1_120
EXPECTED_PATHS = {
    "/platform/operations/summary": {"get"},
    "/platform/operations/{view}": {"get"},
}
PLATFORM_TABLES = (
    "platform_capacity_results",
    "platform_circuit_states",
    "platform_degradation_states",
    "platform_error_budgets",
    "platform_kill_switch_revisions",
    "platform_operations_outbox",
    "platform_recovery_results",
    "platform_security_evidence",
    "platform_service_objectives",
    "platform_supply_chain_inventories",
)
PROHIBITED_IMPORTS = frozenset(
    {
        "aiohttp",
        "cv2",
        "ffmpeg",
        "httpx",
        "importlib",
        "kubernetes",
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
        "contracts/phase-4/p4-6/evidence-package.json",
        "contracts/phase-4/p4-6/acceptance-proposal.json",
        "contracts/phase-4/p4-6/acceptance.json",
    }
)
IGNORED_USER_PREFIXES = ("output/",)
BASELINE_CHECKS = frozenset(
    {
        "start_package_exact",
        "start_authorization_effective",
        "planning_exact",
        "planning_acceptance_exact",
        "implementation_branch_exact",
        "implementation_base_ancestor",
        "changed_paths_allowlisted",
        "pre_change_binding_records_well_formed",
        "immutable_history_exact",
        "predecessor_acceptance_exact",
        "predecessor_historical_readiness",
        "fixtures_exact",
        "contract_snapshot_exact",
        "database_snapshot_exact",
        "openapi_snapshot_exact",
        "openapi_paths_exact",
        "migration_identity_exact",
        "prohibited_imports_absent",
        "dependency_pyproject_exact",
        "dependency_lock_exact",
        "runtime_default_off",
        "external_adapters_default_off",
        "table_scope_exact",
    }
)
EVIDENCE_CHECKS = frozenset(
    {
        "evidence_validation_complete",
        "evidence_package_exact",
        "acceptance_proposal_non_effective",
        "acceptance_proposal_bound",
    }
)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.relative_to(ROOT)} is not a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _normalized_bytes(content: bytes) -> bytes:
    return content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _normalized_sha256(path: Path) -> str:
    return hashlib.sha256(_normalized_bytes(path.read_bytes())).hexdigest().upper()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git(*arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=not binary,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("local Git readiness query failed")
    if binary:
        return result.stdout
    return result.stdout.rstrip()


def _is_ancestor(ancestor: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return result.returncode == 0


def _status_paths() -> set[str]:
    paths: set[str] = set()
    status = str(_git("status", "--porcelain=v1", "--untracked-files=all"))
    for line in status.splitlines():
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
        for item in str(_git("diff", "--name-only", checkpoint)).splitlines()
        if item
    }
    return tracked | _status_paths()


def _changed_paths_between(checkpoint: str, commit: str) -> set[str]:
    return {
        item.replace("\\", "/")
        for item in str(_git("diff", "--name-only", checkpoint, commit)).splitlines()
        if item
    }


def _allowed_paths(package: dict[str, Any]) -> set[str]:
    result = set(package["exact_additive_implementation_paths"])
    result.update(item["path"] for item in package["exact_existing_paths_allowed_to_change"])
    result.update(PACKAGE_CONTROL_PATHS)
    return result


def _contract_catalog() -> dict[str, Any]:
    models = sorted(
        name
        for name, value in vars(contracts).items()
        if isinstance(value, type)
        and value.__module__ == contracts.__name__
        and name != "ContractModel"
        and hasattr(value, "model_json_schema")
    )
    return {
        "schema_version": "hcam.phase4.p4_6.operations-contract-catalog.v1",
        "canonical_encoding": "UTF-8 ASCII JSON, sorted keys, compact separators",
        "digest": "SHA-256",
        "pydantic_models": models,
        "bounds": {
            "burn_windows": MAX_BURN_WINDOWS,
            "capability_profiles": MAX_CAPABILITY_PROFILES,
            "capacity_steps": MAX_CAPACITY_STEPS,
            "circuit_classes": MAX_CIRCUIT_CLASSES,
            "closed_values_per_label": MAX_CLOSED_VALUES_PER_LABEL,
            "contract_bytes": MAX_CONTRACT_BYTES,
            "control_depth": MAX_CONTROL_DEPTH,
            "document_depth": MAX_DOCUMENT_DEPTH,
            "document_items": MAX_DOCUMENT_ITEMS,
            "generated_series": MAX_GENERATED_SERIES,
            "job_attempts": MAX_JOB_ATTEMPTS,
            "job_payload_bytes": MAX_JOB_PAYLOAD_BYTES,
            "labels_per_metric": MAX_LABELS_PER_METRIC,
            "metric_definitions": MAX_METRIC_DEFINITIONS,
            "placement_nodes": MAX_PLACEMENT_NODES,
            "placement_services": MAX_PLACEMENT_SERVICES,
            "recovery_assets": MAX_RECOVERY_ASSETS,
            "recovery_dependencies": MAX_RECOVERY_DEPENDENCIES,
            "safe_failure_parameters": MAX_SAFE_FAILURE_PARAMETERS,
            "string_bytes": MAX_STRING_BYTES,
            "supply_chain_components": MAX_SUPPLY_CHAIN_COMPONENTS,
            "tracestate_bytes": MAX_TRACE_STATE_BYTES,
            "unified_search_items": MAX_UNIFIED_SEARCH_ITEMS,
            "worker_classes": MAX_WORKER_CLASSES,
            "worker_lease_seconds": WORKER_LEASE_SECONDS,
        },
        "registries": {
            "capacity_modes": list(CAPACITY_MODES),
            "capacity_scales": dict(CAPACITY_SCALES),
            "failure_codes": sorted(FAILURE_REGISTRY),
            "metric_definitions": sorted(METRIC_DEFINITIONS),
            "metric_label_values": {key: list(value) for key, value in METRIC_LABEL_VALUES.items()},
            "placement_reasons": list(PLACEMENT_REASONS),
            "recovery_tiers": list(RECOVERY_TIERS),
            "service_classes": list(SERVICE_CLASSES),
            "worker_classes": list(WORKER_CLASSES),
        },
        "signal_authority": "operational security audit and evidence lanes remain independent",
        "unified_search": "disabled sanitized non-authoritative projection only",
        "capacity": "deterministic generated C1 C10 C50 simulation, not a hardware claim",
        "placement": "non-executable standalone and Kubernetes projections",
        "generated_only": True,
        "operational": False,
        "runtime_state": "disabled_by_default_and_forbidden_in_production",
    }


def _database_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "hcam.phase4.p4_6.database-snapshot.v1",
        "revision": EXPECTED_MIGRATION,
        "parent_revision": EXPECTED_PARENT_MIGRATION,
        "new_stores": list(PLATFORM_TABLES),
        "postgresql": {
            "authoritative_business_truth": True,
            "forced_row_security": True,
            "policy_scope": "department",
            "protected_new_stores": list(PLATFORM_TABLES),
        },
        "sqlite": {
            "purpose": "single-process generated development and tests",
            "row_security": "application department filters",
        },
        "database_invariants": [
            "all P4.6 rows are generated-only and nonoperational",
            "every P4.6 store is department scoped and forced-RLS protected on PostgreSQL",
            "payloads are bounded and reject prohibited fields",
            "outbox delivery identity is unique per department",
            "no external backend or operational action is available",
        ],
    }


def _openapi_snapshot() -> dict[str, Any]:
    app = create_app(
        Settings(
            database_url="sqlite:///:memory:",
            environment="test",
            operations_generated_platform_enabled=True,
        )
    )
    schema = app.openapi()
    paths = {
        path: sorted(method.upper() for method in schema["paths"][path] if method != "parameters")
        for path in sorted(EXPECTED_PATHS)
    }
    return {
        "schema_version": "hcam.phase4.p4_6.openapi-surface.v1",
        "feature_flags": ["HCAM_OPERATIONS_GENERATED_PLATFORM_ENABLED"],
        "default_enabled": False,
        "production_allowed": False,
        "paths": paths,
        "views": [
            "objectives",
            "budgets",
            "degradation",
            "controls",
            "recovery",
            "capacity",
            "supply-chain",
            "security",
        ],
        "request_requirements": [
            "authenticated exact read role",
            "authorized department scope",
            "bounded pagination",
            "Cache-Control no-store",
            "generated-only nonoperational responses",
        ],
        "absent_surfaces": [
            "mutations or activation",
            "real telemetry search security or broker backends",
            "backup restore scanner or recovery execution",
            "hardware capacity process container or Kubernetes execution",
            "camera media provider model data or operational action access",
        ],
    }


def write_snapshots() -> None:
    catalog = _contract_catalog()
    database = _database_snapshot()
    openapi = _openapi_snapshot()
    _write_json(P46_ROOT / "operations-contracts.json", catalog)
    _write_json(P46_ROOT / "database.json", database)
    _write_json(P46_ROOT / "openapi.json", openapi)

    combined_database = _json(ROOT / "contracts/phase-4/database.json")
    combined_database.update(
        {
            "schema_version": "hcam.phase4.p4_6.database-snapshot.v1",
            "revision": EXPECTED_MIGRATION,
            "parent_revision": EXPECTED_PARENT_MIGRATION,
            "p4_6": database,
        }
    )
    _write_json(ROOT / "contracts/phase-4/database.json", combined_database)

    combined_openapi = _json(ROOT / "contracts/phase-4/openapi.json")
    flags = list(combined_openapi.get("feature_flags", []))
    flag = "HCAM_OPERATIONS_GENERATED_PLATFORM_ENABLED"
    if flag not in flags:
        flags.append(flag)
    combined_openapi.update(
        {
            "schema_version": "hcam.phase4.p4_6.openapi-surface.v1",
            "feature_flags": flags,
            "p4_6_paths": openapi["paths"],
            "operations_runtime_state": "disabled_by_default_and_forbidden_in_production",
        }
    )
    _write_json(ROOT / "contracts/phase-4/openapi.json", combined_openapi)


def _fixtures_are_exact() -> bool:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/phase46_generated_operations.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        return False
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    files = sorted((P46_ROOT / "fixtures").glob("*.json"))
    total = 0
    for path in files:
        payload = _json(path)
        scenarios = payload.get("scenarios")
        if not isinstance(scenarios, list) or payload.get("scenario_count") != len(scenarios):
            return False
        total += len(scenarios)
    return len(files) == 14 and total == EXPECTED_SCENARIOS and output.get("scenario_count") == EXPECTED_SCENARIOS


def _imports_are_closed() -> bool:
    prohibited_calls = {"__import__", "compile", "eval", "exec", "open"}
    for path in (ROOT / "app/hcam/operations/platform").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(name.split(".", 1)[0] in PROHIBITED_IMPORTS for name in names):
                return False
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in prohibited_calls:
                return False
    return True


def _migration_is_exact() -> bool:
    source = (ROOT / "migrations/versions/0018_operations_security_scale.py").read_text(encoding="utf-8")
    return bool(
        f'revision: str = "{EXPECTED_MIGRATION}"' in source
        and f'down_revision: str | None = "{EXPECTED_PARENT_MIGRATION}"' in source
        and "ENABLE ROW LEVEL SECURITY" in source
        and "FORCE ROW LEVEL SECURITY" in source
        and "for table_name in PLATFORM_TABLES" in source
        and "for table_name in reversed(PLATFORM_TABLES)" in source
    )


def _run_historical_readiness() -> bool:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/phase45_readiness.py"), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        return False
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    return payload.get("owner_acceptance_exact") is True and all(payload.values())


def _evidence_package_is_exact(package: dict[str, Any], source_commit: str) -> bool:
    components = package.get("components")
    if not isinstance(components, list) or not components:
        return False
    paths: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            return False
        path = component.get("path")
        expected = component.get("sha256")
        if not isinstance(path, str) or not isinstance(expected, str) or path in paths:
            return False
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts:
            return False
        try:
            content = _git("show", f"{source_commit}:{path}", binary=True)
        except RuntimeError:
            return False
        if hashlib.sha256(_normalized_bytes(content)).hexdigest().upper() != expected:
            return False
        paths.add(path)
    authorization = _json(START_AUTHORIZATION)
    required = _changed_paths_between(authorization["implementation_base_commit"], source_commit) - PACKAGE_CONTROL_PATHS
    return (
        paths == required
        and package.get("component_digest_mode") == "utf8_text_normalized_lf"
        and package.get("content_digest") == _canonical_digest({"components": components})
    )


def seal_evidence_package(source_commit: str) -> tuple[str, str]:
    if ACCEPTANCE_PATH.is_file():
        raise RuntimeError("accepted P4.6 evidence cannot be resealed")
    authorization = _json(START_AUTHORIZATION)
    package = _json(START_PACKAGE)
    source_commit = str(_git("rev-parse", f"{source_commit}^{{commit}}"))
    required = _changed_paths_between(authorization["implementation_base_commit"], source_commit) - PACKAGE_CONTROL_PATHS
    if not required or not required.issubset(_allowed_paths(package)):
        raise RuntimeError("P4.6 evidence scope is not exact")
    components = []
    for path in sorted(required):
        content = _git("show", f"{source_commit}:{path}", binary=True)
        components.append(
            {"path": path, "sha256": hashlib.sha256(_normalized_bytes(content)).hexdigest().upper()}
        )
    content_digest = _canonical_digest({"components": components})
    evidence_package = {
        "schema_version": "hcam.phase4.p4_6.evidence-package.v1",
        "package_id": "P4.6-EVIDENCE-PACKAGE-R0",
        "status": "technical_validation_passed_owner_acceptance_pending",
        "generated_on": "2026-09-05",
        "branch": EXPECTED_BRANCH,
        "technical_commit": source_commit,
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
        "D-P4.6-ACCEPTANCE: I, mayank-admin, accept P4.6 evidence package "
        f"P4.6-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha256}, canonical component "
        f"digest {content_digest}, and technical commit {source_commit}, including its generated-only "
        "implementation evidence, validation results, explicit PostgreSQL, vulnerability-refresh, "
        "hardware-capacity, backup-restore, and Kubernetes-execution limitations, and documented safety "
        "boundaries. This acceptance completes P4.6 only. It does not authorize P4.7, real telemetry, "
        "search, security, observability, or broker backends; production SLO/RPO/RTO/capacity targets; "
        "scanners; backup, restore, recovery, hardware, performance, stress, or thermal execution; "
        "providers or operational network access; cameras or media; credentials or secrets; Government "
        "or private data; models, datasets, or inference; operational alerts or actions; containers, "
        "Kubernetes execution, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase4.p4_6.acceptance-proposal.v1",
        "decision_id": "D-P4.6-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "prepared_on": "2026-09-05",
        "branch": EXPECTED_BRANCH,
        "technical_commit": source_commit,
        "evidence_package_path": "contracts/phase-4/p4-6/evidence-package.json",
        "evidence_package_sha256": package_sha256,
        "evidence_content_digest": content_digest,
        "owner_acceptance_statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest().upper(),
        "owner_acceptance_statement": statement,
        "authorization_effect": "complete_P4_6_only_after_exact_owner_acceptance",
        "generated_only": True,
        "operational": False,
    }
    _write_json(ACCEPTANCE_PROPOSAL_PATH, proposal)
    return package_sha256, content_digest


def checks() -> dict[str, bool]:
    package = _json(START_PACKAGE)
    authorization = _json(START_AUTHORIZATION)
    dependency_bindings = {item["path"]: item["sha256"] for item in package["immutable_dependency_bindings"]}
    checkpoint = authorization["implementation_base_commit"]
    changed = _changed_paths(checkpoint)
    immutable_prefixes = (
        "contracts/phase-3/",
        "docs/phase-3/",
        "contracts/phase-4/p4-0",
        "contracts/phase-4/p4-1/",
        "contracts/phase-4/p4-2/",
        "contracts/phase-4/p4-3/",
        "contracts/phase-4/p4-4/",
        "contracts/phase-4/p4-5/",
    )
    evidence = _json(EVIDENCE_PATH) if EVIDENCE_PATH.is_file() else {}
    evidence_package = _json(EVIDENCE_PACKAGE_PATH) if EVIDENCE_PACKAGE_PATH.is_file() else {}
    proposal = _json(ACCEPTANCE_PROPOSAL_PATH) if ACCEPTANCE_PROPOSAL_PATH.is_file() else {}
    acceptance = _json(ACCEPTANCE_PATH) if ACCEPTANCE_PATH.is_file() else {}
    source_commit = proposal.get("technical_commit", "") if proposal else ""
    required_validation = (
        "generated_contracts",
        "focused_suite",
        "coverage",
        "sqlite_migration_cycle",
        "postgresql_rls_and_isolation",
        "full_regression_suite",
        "static_and_packaging",
        "historical_compatibility",
        "security_recovery_capacity",
        "dependency_validation",
    )
    validation = evidence.get("validation", {})
    acceptance_exact = bool(acceptance) and bool(proposal) and (
        acceptance.get("effective") is True
        and acceptance.get("status") == "owner_accepted"
        and acceptance.get("decision_id") == "D-P4.6-ACCEPTANCE"
        and acceptance.get("accepted_by") == "mayank-admin"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit") == source_commit
        and acceptance.get("evidence_package", {}).get("sha256") == _sha256(EVIDENCE_PACKAGE_PATH)
        and acceptance.get("owner_statement") == proposal.get("owner_acceptance_statement")
        and hashlib.sha256(acceptance.get("owner_statement", "").encode("utf-8")).hexdigest().upper()
        == proposal.get("owner_acceptance_statement_sha256")
        and acceptance.get("accepted_progress", {}).get("phase_4_points") == 95
        and acceptance.get("accepted_progress", {}).get("p4_6_points") == 10
    )
    openapi = _openapi_snapshot()
    actual_paths = {
        path: {method.lower() for method in methods}
        for path, methods in openapi["paths"].items()
    }
    return {
        "start_package_exact": _sha256(START_PACKAGE) == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": authorization.get("effective") is True,
        "planning_exact": _sha256(ROOT / "contracts/phase-4/p4-6-planning-r1-package.json") == EXPECTED_PLANNING_SHA256,
        "planning_acceptance_exact": _sha256(ROOT / "contracts/phase-4/p4-6-planning-r1-acceptance.json") == EXPECTED_PLANNING_ACCEPTANCE_SHA256,
        "implementation_branch_exact": str(_git("branch", "--show-current")) == EXPECTED_BRANCH,
        "implementation_base_ancestor": _is_ancestor(checkpoint),
        "changed_paths_allowlisted": changed.issubset(_allowed_paths(package)),
        "pre_change_binding_records_well_formed": all(
            isinstance(item.get("path"), str)
            and isinstance(item.get("reason"), str)
            and len(item.get("pre_change_sha256", "")) == 64
            for item in package["exact_existing_paths_allowed_to_change"]
        ),
        "immutable_history_exact": not any(path.startswith(immutable_prefixes) for path in changed),
        "predecessor_acceptance_exact": _sha256(ROOT / "contracts/phase-4/p4-5/acceptance.json") == EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256,
        "predecessor_historical_readiness": _run_historical_readiness(),
        "fixtures_exact": _fixtures_are_exact(),
        "contract_snapshot_exact": (P46_ROOT / "operations-contracts.json").is_file() and _json(P46_ROOT / "operations-contracts.json") == _contract_catalog(),
        "database_snapshot_exact": (P46_ROOT / "database.json").is_file() and _json(P46_ROOT / "database.json") == _database_snapshot(),
        "openapi_snapshot_exact": (P46_ROOT / "openapi.json").is_file() and _json(P46_ROOT / "openapi.json") == openapi,
        "openapi_paths_exact": actual_paths == EXPECTED_PATHS,
        "migration_identity_exact": _migration_is_exact(),
        "prohibited_imports_absent": _imports_are_closed(),
        "dependency_pyproject_exact": _sha256(ROOT / "pyproject.toml") == dependency_bindings["pyproject.toml"],
        "dependency_lock_exact": _sha256(ROOT / "uv.lock") == dependency_bindings["uv.lock"],
        "runtime_default_off": Settings().operations_generated_platform_enabled is False,
        "external_adapters_default_off": all(
            getattr(Settings(), name) is False
            for name in (
                "operations_unified_search_enabled",
                "operations_otel_export_enabled",
                "operations_external_broker_enabled",
                "operations_kubernetes_execution_enabled",
            )
        ),
        "table_scope_exact": len(PLATFORM_TABLES) == 10,
        "evidence_validation_complete": bool(validation)
        and all(
            isinstance(validation.get(name), dict)
            and validation[name].get("status") in {"passed", "not_available"}
            for name in required_validation
        ),
        "evidence_package_exact": bool(evidence_package)
        and bool(source_commit)
        and _evidence_package_is_exact(evidence_package, source_commit),
        "acceptance_proposal_non_effective": proposal.get("effective") is False
        and proposal.get("status") == "owner_acceptance_required"
        and proposal.get("decision_id") == "D-P4.6-ACCEPTANCE",
        "acceptance_proposal_bound": bool(evidence_package)
        and bool(proposal)
        and proposal.get("evidence_package_sha256") == _sha256(EVIDENCE_PACKAGE_PATH)
        and proposal.get("evidence_content_digest") == evidence_package.get("content_digest"),
        "owner_acceptance_exact": acceptance_exact,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the generated-only P4.6 boundary")
    parser.add_argument("--write-snapshots", action="store_true")
    parser.add_argument("--seal-evidence", action="store_true")
    parser.add_argument("--source-commit", default="HEAD")
    parser.add_argument("--require-evidence", action="store_true")
    parser.add_argument("--require-acceptance", action="store_true")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    if arguments.write_snapshots:
        write_snapshots()
    if arguments.seal_evidence:
        seal_evidence_package(arguments.source_commit)
    results = checks()
    required = set(BASELINE_CHECKS)
    if arguments.require_evidence or arguments.require_acceptance:
        required.update(EVIDENCE_CHECKS)
    if arguments.require_acceptance:
        required.add("owner_acceptance_exact")
    if arguments.json:
        print(json.dumps(results, ensure_ascii=True, sort_keys=True))
    else:
        for name, passed in sorted(results.items()):
            required_marker = "*" if name in required else " "
            print(f"{required_marker} {'PASS' if passed else 'FAIL'} {name}")
    return 0 if all(results[name] for name in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
