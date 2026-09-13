from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from hcam.intelligence.investigations import contracts
from hcam.intelligence.investigations.bounds import (
    JOB_LEASE_SECONDS,
    MAX_CONTRACT_BYTES,
    MAX_CORRECTION_CHAIN_DEPTH,
    MAX_ENTRIES_PER_TIMELINE,
    MAX_ENTRY_PAYLOAD_BYTES,
    MAX_EXPORT_REFERENCES,
    MAX_IMPACT_TARGETS,
    MAX_JOB_ATTEMPTS,
    MAX_PAGE_SIZE,
    MAX_PROVENANCE_DEPTH,
    MAX_PROVENANCE_EDGES,
    MAX_PROVENANCE_FANOUT,
    MAX_PROVENANCE_NODES,
    MAX_RELATIONSHIP_DEPTH,
    MAX_STRING_BYTES,
)
from hcam.intelligence.row_security import INVESTIGATION_TABLES
from hcam.main import create_app
from hcam.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
START_PACKAGE = ROOT / "contracts/phase-4/p4-5-start-authorization-package.json"
START_AUTHORIZATION = ROOT / "contracts/phase-4/p4-5-start-authorization.json"
P45_ROOT = ROOT / "contracts/phase-4/p4-5"
EVIDENCE_PATH = P45_ROOT / "evidence.json"
EVIDENCE_PACKAGE_PATH = P45_ROOT / "evidence-package.json"
ACCEPTANCE_PROPOSAL_PATH = P45_ROOT / "acceptance-proposal.json"
ACCEPTANCE_PATH = P45_ROOT / "acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = (
    "7DC272A5017C54EC83380A2BD2301CAA737EAB1D196045B9A5D1F40F232F34CF"
)
EXPECTED_PLANNING_SHA256 = (
    "1E32E73885C81499117D84E9F15C5A038066B9BC22C17D1F58F98FBE6A6FEDE4"
)
EXPECTED_PLANNING_ACCEPTANCE_SHA256 = (
    "006FF8AD8B769C243C97DDF29E1CCB4F6CFE88CDD067AAA1D679B35752326282"
)
EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256 = (
    "2E298EAA88E9F2586633955838FBC367641A807F4635866BCE488DC1E60936AD"
)
EXPECTED_ACCEPTANCE_SHA256 = (
    "856484AA45BB0775DD1A967AE1AFC0135E64ADC826DAE339A31FB1806CF26AB2"
)
EXPECTED_OWNER_STATEMENT_SHA256 = (
    "32452039FA7260AE3E85A670DB3D17008BF516309C7F3ADB064B7A30E3FA073D"
)
ACCEPTED_IMPLEMENTATION_COMMIT = "9eb3d2fb3a3fc68b8722d7c4a70369e6f1a8d41e"
ACCEPTED_ACCEPTANCE_COMMIT = "1b54aafc252248eb502cd04ebd2130b0cf1684bf"
EXPECTED_BRANCH = "codex/phase4-investigation-evidence"
EXPECTED_MIGRATION = "0017_investigation_evidence"
EXPECTED_PARENT_MIGRATION = "0016_reference_integrations"
EXPECTED_SCENARIOS = 552
EXPECTED_PATHS = {
    "/investigations/health": {"get"},
    "/investigations/relationships": {"post"},
    "/investigations/timelines": {"get", "post"},
    "/investigations/timelines/{timeline_id}": {"get"},
    "/investigations/timelines/{timeline_id}/corrections": {"post"},
    "/investigations/timelines/{timeline_id}/deletion-simulations": {"post"},
    "/investigations/timelines/{timeline_id}/entries": {"post"},
    "/investigations/timelines/{timeline_id}/evidence": {"get", "post"},
    "/investigations/timelines/{timeline_id}/export-previews": {"post"},
    "/investigations/timelines/{timeline_id}/holds": {"post"},
    "/investigations/timelines/{timeline_id}/integrity": {"post"},
    "/investigations/timelines/{timeline_id}/lifecycle": {"post"},
    "/investigations/timelines/{timeline_id}/provenance": {"post"},
    "/investigations/timelines/{timeline_id}/reconstruction": {"get"},
    "/investigations/timelines/{timeline_id}/retention-evaluations": {"post"},
    "/investigations/timelines/{timeline_id}/reviews": {"post"},
}
CONTRACT_TYPES = (
    "hcam.investigation.case-bridge.v1",
    "hcam.investigation.correction.v1",
    "hcam.investigation.deletion-intent.v1",
    "hcam.investigation.deletion-receipt.v1",
    "hcam.investigation.evidence-reference.v2",
    "hcam.investigation.export-manifest.v1",
    "hcam.investigation.hold-overlay.v1",
    "hcam.investigation.impact-job.v1",
    "hcam.investigation.impact-set.v1",
    "hcam.investigation.integrity-assessment.v1",
    "hcam.investigation.prov-projection.v1",
    "hcam.investigation.provenance-bundle.v1",
    "hcam.investigation.reconstruction.v1",
    "hcam.investigation.relationship-revision.v1",
    "hcam.investigation.retention-evaluation.v1",
    "hcam.investigation.review-decision.v1",
    "hcam.investigation.temporal-assertion.v1",
    "hcam.investigation.timeline-create.v2",
    "hcam.investigation.timeline-entry.v2",
    "hcam.investigation.timeline.v2",
)
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
        "contracts/phase-4/p4-5/evidence-package.json",
        "contracts/phase-4/p4-5/acceptance-proposal.json",
        "contracts/phase-4/p4-5/acceptance.json",
    }
)
ACCEPTANCE_SYNC_PATHS = frozenset(
    {
        "contracts/phase-4/p4-5/acceptance.json",
        "docs/phase-4/README.md",
        "docs/phase-4/p4-5-evidence-review.md",
        "docs/phase-4/status.md",
        "tests/test_phase45_readiness.py",
        "tools/phase45_readiness.py",
    }
)
AUTHORIZED_COMPATIBILITY_PATHS = {
    "tests/test_phase44_persistence.py": (
        "1A752E601994A02F82FE3653DDD20056492741FD414A1BC6AE6F9A6021B0EA47"
    )
}
IGNORED_USER_PREFIXES = ("output/",)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.relative_to(ROOT)} is not a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _normalized_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def _normalized_sha256_bytes(content: bytes) -> str:
    text = content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("local Git readiness query failed")
    return result.stdout.rstrip()


def _git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("local Git historical readiness query failed")
    return result.stdout


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
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
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
    result = set(package["exact_additive_implementation_paths"])
    result.update(
        item["path"] for item in package["exact_existing_paths_allowed_to_change"]
    )
    result.update(AUTHORIZED_COMPATIBILITY_PATHS)
    return result


def _authorized_compatibility_baselines_are_exact(checkpoint: str) -> bool:
    return all(
        _normalized_sha256_bytes(_git_bytes("show", f"{checkpoint}:{path}"))
        == expected
        for path, expected in AUTHORIZED_COMPATIBILITY_PATHS.items()
    )


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
        "contracts/phase-4/p4-4",
        "migrations/versions/0011_geometry_events.py",
        "migrations/versions/0012_intelligence_control_plane.py",
        "migrations/versions/0013_correlation_foundation.py",
        "migrations/versions/0014_rule_authoring_evaluation.py",
        "migrations/versions/0015_alert_lifecycle_orchestration.py",
        "migrations/versions/0016_reference_integrations.py",
    ]
    return not _git("diff", "--name-only", checkpoint, "--", *immutable)


def _pre_change_binding_records_are_well_formed(package: dict[str, Any]) -> bool:
    records = package["exact_existing_paths_allowed_to_change"]
    paths = [item.get("path") for item in records]
    return bool(
        records
        and len(paths) == len(set(paths))
        and all(
            isinstance(item.get("path"), str)
            and isinstance(item.get("reason"), str)
            and len(item.get("pre_change_sha256", "")) == 64
            and all(
                character in "0123456789ABCDEF"
                for character in item["pre_change_sha256"]
            )
            for item in records
        )
    )


def _run_json_tool(path: str, *arguments: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / path), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        return {"passed": False}
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"passed": False}
    return value if isinstance(value, dict) else {"passed": False}


def _contract_catalog() -> dict[str, Any]:
    models = sorted(
        name
        for name, value in vars(contracts).items()
        if isinstance(value, type)
        and value.__module__ == contracts.__name__
        and hasattr(value, "model_json_schema")
    )
    return {
        "schema_version": "hcam.phase4.p4_5.investigation-evidence-contract-catalog.v1",
        "canonical_encoding": "UTF-8 ASCII JSON, sorted keys, compact separators",
        "digest": "SHA-256",
        "contract_types": list(CONTRACT_TYPES),
        "pydantic_models": models,
        "bounds": {
            "contract_bytes": MAX_CONTRACT_BYTES,
            "entry_payload_bytes": MAX_ENTRY_PAYLOAD_BYTES,
            "string_bytes": MAX_STRING_BYTES,
            "page_size": MAX_PAGE_SIZE,
            "entries_per_timeline": MAX_ENTRIES_PER_TIMELINE,
            "relationship_depth": MAX_RELATIONSHIP_DEPTH,
            "correction_chain_depth": MAX_CORRECTION_CHAIN_DEPTH,
            "provenance_nodes": MAX_PROVENANCE_NODES,
            "provenance_edges": MAX_PROVENANCE_EDGES,
            "provenance_depth": MAX_PROVENANCE_DEPTH,
            "provenance_fanout": MAX_PROVENANCE_FANOUT,
            "impact_targets": MAX_IMPACT_TARGETS,
            "export_references": MAX_EXPORT_REFERENCES,
            "job_attempts": MAX_JOB_ATTEMPTS,
            "job_lease_seconds": JOB_LEASE_SECONDS,
        },
        "timeline_authority": "case-neutral H-CAM investigation timeline",
        "evidence_boundary": "immutable opaque references; no source resolution or payload retention",
        "integrity_boundary": "integrity availability authenticity custody and legal state remain separate",
        "correction_boundary": "append-only exact-version correction and bounded impact closure",
        "retention_boundary": "advisory policy references only; no legal period selected",
        "deletion_boundary": "per-target dry-run receipts with residuals; universal deletion never proven",
        "export_boundary": "purpose-bound reference-only preview; no payload signature timestamp or delivery",
        "case_bridge": "typed disabled contract only",
        "prov_projection": "generated lossy export projection; import disabled and conformance not claimed",
        "generated_only": True,
        "operational": False,
        "runtime_state": "disabled_by_default_and_forbidden_in_production",
    }


def _database_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "hcam.phase4.p4_5.database-snapshot.v1",
        "revision": EXPECTED_MIGRATION,
        "parent_revision": EXPECTED_PARENT_MIGRATION,
        "preserved_v1_stores": ["investigation_timelines", "timeline_entries"],
        "new_stores": sorted(INVESTIGATION_TABLES),
        "postgresql": {
            "authoritative_business_truth": True,
            "forced_row_security": True,
            "policy_scope": "department",
            "concurrent_impact_claim": "FOR UPDATE SKIP LOCKED",
            "protected_new_stores": sorted(INVESTIGATION_TABLES),
        },
        "sqlite": {
            "purpose": "single-process generated development and tests",
            "worker_limit": 1,
            "row_security": "application department filters",
        },
        "database_invariants": [
            "all P4.5 state is generated-only and nonoperational",
            "timeline revisions evidence assessments reviews corrections and receipts are append-only",
            "semantic identity is separate from delivery idempotency",
            "source payloads and locators are never persisted",
            "deletion and export external actions are unavailable",
        ],
    }


def _openapi_snapshot() -> dict[str, Any]:
    app = create_app(
        Settings(
            database_url="sqlite:///:memory:",
            environment="test",
            intelligence_generated_investigations_enabled=True,
        )
    )
    schema = app.openapi()
    paths = {
        path: sorted(method.upper() for method in schema["paths"][path] if method != "parameters")
        for path in sorted(EXPECTED_PATHS)
    }
    return {
        "schema_version": "hcam.phase4.p4_5.openapi-surface.v1",
        "feature_flags": ["HCAM_INTELLIGENCE_GENERATED_INVESTIGATIONS_ENABLED"],
        "default_enabled": False,
        "production_allowed": False,
        "paths": paths,
        "request_requirements": [
            "authenticated exact capability role",
            "authorized department scope",
            "X-HCAM-Reason for mutations",
            "If-Match for aggregate revisions",
            "Cache-Control no-store",
            "generated-only nonoperational contracts",
        ],
        "absent_surfaces": [
            "source reference resolution fetch or copying",
            "real case management or PROV import",
            "hold activation or release",
            "deletion execution",
            "export payload signing timestamping delivery or receipt",
            "camera media provider model or operational action access",
        ],
    }


def write_snapshots() -> None:
    catalog = _contract_catalog()
    database = _database_snapshot()
    openapi = _openapi_snapshot()
    _write_json(P45_ROOT / "investigation-evidence-contracts.json", catalog)
    _write_json(P45_ROOT / "database.json", database)
    _write_json(P45_ROOT / "openapi.json", openapi)

    combined_contracts = _json(ROOT / "contracts/phase-4/intelligence-contracts.json")
    combined_contracts.update(
        {
            "schema_version": "hcam.phase4.p4_5.intelligence-contract-catalog.v1",
            "p4_5_contract_types": list(CONTRACT_TYPES),
            "investigation_timeline_authority": catalog["timeline_authority"],
            "investigation_evidence_boundary": catalog["evidence_boundary"],
            "investigation_runtime_state": catalog["runtime_state"],
        }
    )
    _write_json(ROOT / "contracts/phase-4/intelligence-contracts.json", combined_contracts)

    combined_database = _json(ROOT / "contracts/phase-4/database.json")
    combined_database.update(database)
    combined_database["schema_version"] = "hcam.phase4.p4_5.database-snapshot.v1"
    _write_json(ROOT / "contracts/phase-4/database.json", combined_database)

    combined_openapi = _json(ROOT / "contracts/phase-4/openapi.json")
    flags = list(combined_openapi.get("feature_flags", []))
    flag = "HCAM_INTELLIGENCE_GENERATED_INVESTIGATIONS_ENABLED"
    if flag not in flags:
        flags.append(flag)
    combined_openapi.update(
        {
            "schema_version": "hcam.phase4.p4_5.openapi-surface.v1",
            "feature_flags": flags,
            "p4_5_paths": openapi["paths"],
            "investigation_runtime_state": "disabled_by_default_and_forbidden_in_production",
        }
    )
    _write_json(ROOT / "contracts/phase-4/openapi.json", combined_openapi)


def _fixtures_are_exact() -> bool:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/phase45_generated_investigations.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        return False
    files = sorted((P45_ROOT / "fixtures").glob("*.json"))
    if len(files) != 14:
        return False
    total = 0
    for path in files:
        payload = _json(path)
        vectors = payload.get("vectors")
        if not isinstance(vectors, list) or payload.get("scenario_count") != len(vectors):
            return False
        total += len(vectors)
    return total == EXPECTED_SCENARIOS and result.stdout.strip() == (
        f"P4.5 generated fixtures: {EXPECTED_SCENARIOS} scenarios"
    )


def _imports_are_closed() -> bool:
    prohibited_calls = {"__import__", "compile", "eval", "exec", "open"}
    for path in (ROOT / "app/hcam/intelligence/investigations").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(name.split(".", 1)[0] in PROHIBITED_IMPORTS for name in names):
                return False
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in prohibited_calls
            ):
                return False
    return True


def _migration_is_exact() -> bool:
    source = (ROOT / "migrations/versions/0017_investigation_evidence.py").read_text(
        encoding="utf-8"
    )
    return bool(
        f'revision: str = "{EXPECTED_MIGRATION}"' in source
        and f'down_revision: str | None = "{EXPECTED_PARENT_MIGRATION}"' in source
        and "NEW_TABLES = INVESTIGATION_TABLES" in source
        and "ENABLE ROW LEVEL SECURITY" in source
        and "FORCE ROW LEVEL SECURITY" in source
        and "for table_name in NEW_TABLES" in source
        and "for table_name in reversed(NEW_TABLES)" in source
    )


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
        relative = Path(path_value)
        source = ROOT / relative
        source_exists = (
            _git_bytes("cat-file", "-e", f"{source_commit}:{path_value}") == b""
            if source_commit
            else source.is_file()
        )
        actual = (
            _normalized_sha256_bytes(
                _git_bytes("show", f"{source_commit}:{path_value}")
            )
            if source_commit and source_exists
            else _normalized_sha256(source)
            if source_exists
            else ""
        )
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or path_value in paths
            or not source_exists
            or actual != expected
        ):
            return False
        paths.add(path_value)
    return paths == required_components and package.get(
        "content_digest"
    ) == _canonical_digest({"components": components})


def seal_evidence_package() -> tuple[str, str]:
    if ACCEPTANCE_PATH.is_file():
        raise RuntimeError("accepted P4.5 evidence cannot be resealed")
    package = _json(START_PACKAGE)
    authorization = _json(START_AUTHORIZATION)
    changed = _changed_paths(authorization["implementation_base_commit"])
    required = changed - PACKAGE_CONTROL_PATHS
    if not required or not required.issubset(_allowed_paths(package)):
        raise RuntimeError("P4.5 evidence scope is not exact")
    if not EVIDENCE_PATH.is_file():
        raise RuntimeError("P4.5 evidence record is absent")
    components = [
        {"path": path, "sha256": _normalized_sha256(ROOT / path)}
        for path in sorted(required)
    ]
    content_digest = _canonical_digest({"components": components})
    evidence_package = {
        "schema_version": "hcam.phase4.p4_5.evidence-package.v1",
        "package_id": "P4.5-EVIDENCE-PACKAGE-R0",
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
        "D-P4.5-ACCEPTANCE: I, mayank-admin, accept P4.5 evidence package "
        f"P4.5-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha256} and canonical "
        f"component digest {content_digest}, including its generated-only "
        "implementation evidence, validation results, authorized P4.4 historical "
        "readiness transition, explicit PostgreSQL and vulnerability-refresh "
        "limitations, and documented safety boundaries. This acceptance completes "
        "P4.5 only. It does not authorize P4.6, source or evidence copying or "
        "resolution, real investigations or case systems, external PROV import or "
        "conformance claims, retention-period or legal-policy decisions, hold "
        "activation or release, deletion or export execution, providers or network "
        "access, credentials or secrets, Government or private data, cameras or "
        "media, models or datasets, inference, operational alerts or actions, "
        "containers, Kubernetes, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase4.p4_5.acceptance-proposal.v1",
        "decision_id": "D-P4.5-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "prepared_on": "2026-09-05",
        "branch": EXPECTED_BRANCH,
        "evidence_package_path": "contracts/phase-4/p4-5/evidence-package.json",
        "evidence_package_sha256": package_sha256,
        "evidence_content_digest": content_digest,
        "owner_acceptance_statement_sha256": hashlib.sha256(
            statement.encode("utf-8")
        ).hexdigest().upper(),
        "owner_acceptance_statement": statement,
        "authorization_effect": "complete_P4_5_only_after_exact_owner_acceptance",
        "generated_only": True,
        "operational": False,
    }
    _write_json(ACCEPTANCE_PROPOSAL_PATH, proposal)
    return package_sha256, content_digest


def checks() -> dict[str, bool]:
    package = _json(START_PACKAGE)
    authorization = _json(START_AUTHORIZATION)
    openapi = _openapi_snapshot()
    actual_paths = {
        path: {method.lower() for method in methods}
        for path, methods in openapi["paths"].items()
    }
    dependency_bindings = {
        item["path"]: item["sha256"]
        for item in package["immutable_dependency_bindings"]
    }
    checkpoint = authorization["implementation_base_commit"]
    changed = _changed_paths(checkpoint)
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
        and acceptance.get("decision_id") == "D-P4.5-ACCEPTANCE"
        and acceptance.get("accepted_by") == "mayank-admin"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit")
        == ACCEPTED_IMPLEMENTATION_COMMIT
        and acceptance.get("evidence_package", {}).get("package_id")
        == "P4.5-EVIDENCE-PACKAGE-R0"
        and acceptance.get("evidence_package", {}).get("path")
        == "contracts/phase-4/p4-5/evidence-package.json"
        and acceptance.get("evidence_package", {}).get("sha256")
        == _sha256(EVIDENCE_PACKAGE_PATH)
        and acceptance.get("evidence_package", {}).get(
            "canonical_component_digest"
        )
        == evidence_package.get("content_digest")
        and acceptance.get("accepted_progress", {}).get("phase_4_points") == 85
        and acceptance.get("accepted_progress", {}).get("p4_5_points") == 15
        and acceptance.get("owner_statement_sha256")
        == EXPECTED_OWNER_STATEMENT_SHA256
        and acceptance.get("owner_statement")
        == proposal.get("owner_acceptance_statement")
        and hashlib.sha256(acceptance.get("owner_statement", "").encode("utf-8"))
        .hexdigest()
        .upper()
        == EXPECTED_OWNER_STATEMENT_SHA256
    )
    source_commit = ACCEPTED_IMPLEMENTATION_COMMIT if acceptance_exact else None
    implementation_changed = (
        _changed_paths_between(checkpoint, ACCEPTED_IMPLEMENTATION_COMMIT)
        if acceptance_exact
        else changed
    )
    required_components = implementation_changed - PACKAGE_CONTROL_PATHS
    historical = _run_json_tool("tools/phase44_readiness.py", "--json")
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
    return {
        "start_package_exact": _sha256(START_PACKAGE) == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": authorization.get("effective") is True,
        "planning_exact": _sha256(ROOT / "contracts/phase-4/p4-5-planning-r1-package.json") == EXPECTED_PLANNING_SHA256,
        "planning_acceptance_exact": _sha256(ROOT / "contracts/phase-4/p4-5-planning-r1-acceptance.json") == EXPECTED_PLANNING_ACCEPTANCE_SHA256,
        "implementation_branch_exact": acceptance_exact
        or _git("branch", "--show-current") == EXPECTED_BRANCH,
        "implementation_base_ancestor": _is_ancestor(checkpoint),
        "accepted_implementation_commit_ancestor": (
            not acceptance_exact or _is_ancestor(ACCEPTED_IMPLEMENTATION_COMMIT)
        ),
        "changed_paths_allowlisted": implementation_changed.issubset(
            _allowed_paths(package)
        ),
        "acceptance_sync_paths_allowlisted": (
            not acceptance_exact
            or (
                _is_ancestor(ACCEPTED_ACCEPTANCE_COMMIT)
                and _changed_paths_between(
                    ACCEPTED_IMPLEMENTATION_COMMIT,
                    ACCEPTED_ACCEPTANCE_COMMIT,
                ).issubset(ACCEPTANCE_SYNC_PATHS)
            )
        ),
        "authorized_compatibility_baselines_exact": (
            _authorized_compatibility_baselines_are_exact(checkpoint)
        ),
        "pre_change_binding_records_well_formed": (
            _pre_change_binding_records_are_well_formed(package)
        ),
        "immutable_history_exact": _immutable_history_is_exact(checkpoint),
        "predecessor_acceptance_exact": _sha256(
            ROOT / "contracts/phase-4/p4-4/acceptance.json"
        )
        == EXPECTED_PREDECESSOR_ACCEPTANCE_SHA256,
        "predecessor_historical_readiness": historical.get("passed") is True,
        "fixtures_exact": _fixtures_are_exact(),
        "contract_snapshot_exact": _json(P45_ROOT / "investigation-evidence-contracts.json") == _contract_catalog(),
        "database_snapshot_exact": _json(P45_ROOT / "database.json") == _database_snapshot(),
        "openapi_snapshot_exact": _json(P45_ROOT / "openapi.json") == openapi,
        "openapi_paths_exact": actual_paths == EXPECTED_PATHS,
        "migration_identity_exact": _migration_is_exact(),
        "prohibited_imports_absent": _imports_are_closed(),
        "dependency_pyproject_exact": _sha256(ROOT / "pyproject.toml") == dependency_bindings["pyproject.toml"],
        "dependency_lock_exact": _sha256(ROOT / "uv.lock") == dependency_bindings["uv.lock"],
        "runtime_default_off": Settings().intelligence_generated_investigations_enabled is False,
        "table_scope_exact": len(INVESTIGATION_TABLES) == 17,
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
            and proposal.get("decision_id") == "D-P4.5-ACCEPTANCE"
        ),
        "acceptance_proposal_bound": bool(evidence_package)
        and bool(proposal)
        and proposal.get("evidence_package_sha256") == _sha256(EVIDENCE_PACKAGE_PATH)
        and proposal.get("evidence_content_digest")
        == evidence_package.get("content_digest"),
        "owner_acceptance_exact": acceptance_exact,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the generated-only P4.5 boundary")
    parser.add_argument("--write-snapshots", action="store_true")
    parser.add_argument("--seal-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    if arguments.write_snapshots:
        write_snapshots()
    if arguments.seal_evidence:
        seal_evidence_package()
    results = checks()
    if arguments.json:
        print(json.dumps(results, ensure_ascii=True, sort_keys=True))
    else:
        for name, passed in sorted(results.items()):
            print(f"{'PASS' if passed else 'FAIL'} {name}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
