from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = ROOT / "contracts/phase-4/p4-0-start-authorization-package.json"
AUTHORIZATION_PATH = ROOT / "contracts/phase-4/p4-0-start-authorization.json"
EXPECTED_PACKAGE_SHA256 = (
    "58E490D767B810743FAF47B3709DF12B0071EEDDD5E50C96A3A7D1CE8E38DFB2"
)
EXPECTED_PLANNING_SHA256 = (
    "B8F4371A8DDD350F44321E70F5FB8CEE0DD27299A26082A40460086E80DDEA63"
)
EXPECTED_ACCEPTANCE_SHA256 = (
    "46749F00F04F2FA755136EBB524B2C16FCB2BC6DE63E49642BF64B182D642D87"
)
P4_0_ACCEPTANCE_PATH = ROOT / "contracts/phase-4/p4-0-acceptance.json"
EXPECTED_P4_0_ACCEPTANCE_SHA256 = (
    "09D310D21D724DCA681A45FB32AD81EFC0CD2CB5A929C6C1790666EFEF3ACCDE"
)
P4_0_BRANCH = "codex/phase4-contracts-guardrails"
P4_0_IMPLEMENTATION_COMMIT = "2e35bd28aa33c2ebed6fa0bd6486fb26a7d9655d"
P4_1_PACKAGE_PATH = ROOT / "contracts/phase-4/p4-1-start-authorization-package.json"
EXPECTED_P4_1_PACKAGE_SHA256 = (
    "43EDF72ADE8328AEABE0F295ACC649F76229D233F8B0FB7E2D1D5C2E43B9ECA6"
)
P4_1_AUTHORIZATION_PATH = ROOT / "contracts/phase-4/p4-1-start-authorization.json"
P4_1_BRANCH = "codex/phase4-correlation-foundation"
CHECKPOINT = "a00b677ac120c33c4045b37b8350e816b1e3b11b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _canonical_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _canonical_text_sha256_bytes(content: bytes) -> str:
    text = content.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _evidence_package_is_exact(package: dict[str, Any]) -> bool:
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
        paths.add(path_value)
        try:
            content = _git_bytes("show", f"{P4_0_IMPLEMENTATION_COMMIT}:{path_value}")
        except RuntimeError:
            return False
        if _canonical_text_sha256_bytes(content) != expected:
            return False
    return package.get("content_digest") == _canonical_digest(
        {"components": components}
    )


def _git(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("local Git readiness query failed")
    return process.stdout.rstrip()


def _git_bytes(*args: str) -> bytes:
    process = subprocess.run(
        ["git", *args],
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


def _is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return process.returncode == 0


def _p4_1_authorization_is_effective() -> bool:
    if not P4_1_PACKAGE_PATH.is_file() or not P4_1_AUTHORIZATION_PATH.is_file():
        return False
    if _sha256(P4_1_PACKAGE_PATH) != EXPECTED_P4_1_PACKAGE_SHA256:
        return False
    package = _json(P4_1_PACKAGE_PATH)
    authorization = _json(P4_1_AUTHORIZATION_PATH)
    return bool(
        authorization.get("effective") is True
        and authorization.get("decision_id") == "D-P4.1-START"
        and authorization.get("branch") == P4_1_BRANCH
        and authorization.get("package", {}).get("sha256")
        == EXPECTED_P4_1_PACKAGE_SHA256
        and package.get("package_id") == "P4.1-START-R0"
        and _git("branch", "--show-current") == P4_1_BRANCH
        and _is_ancestor(authorization["planning_checkpoint_commit"])
    )


def _allowed_changed_paths(package: dict[str, Any]) -> set[str]:
    allowed = set(package["exact_additive_implementation_paths"])
    allowed.update(item["path"] for item in package["exact_existing_paths_allowed_to_change"])
    allowed.add("tools/release_contracts.py")
    if _p4_1_authorization_is_effective():
        p4_1_package = _json(P4_1_PACKAGE_PATH)
        allowed.update(p4_1_package["exact_additive_implementation_paths"])
        allowed.update(
            item["path"] for item in p4_1_package["exact_existing_paths_allowed_to_change"]
        )
    return allowed


def _changed_paths() -> set[str]:
    paths: set[str] = set()
    for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path.replace("\\", "/").strip('"'))
    return paths


def collect_checks() -> dict[str, bool]:
    package = _json(PACKAGE_PATH)
    authorization = _json(AUTHORIZATION_PATH)
    allowed = _allowed_changed_paths(package)
    changed = _changed_paths()
    evidence_record = _json(ROOT / "contracts/phase-4/p4-0-evidence.json")
    database_snapshot = _git_json(
        P4_0_IMPLEMENTATION_COMMIT, "contracts/phase-4/database.json"
    )
    contract_snapshot = _git_json(
        P4_0_IMPLEMENTATION_COMMIT, "contracts/phase-4/intelligence-contracts.json"
    )
    openapi_snapshot = _git_json(
        P4_0_IMPLEMENTATION_COMMIT, "contracts/phase-4/openapi.json"
    )
    evidence_package = _json(ROOT / "contracts/phase-4/p4-0-evidence-package.json")
    fixture_components = [
        item for item in evidence_package.get("components", [])
        if str(item.get("path", "")).startswith("contracts/phase-4/fixtures/")
    ]
    fixtures_valid = bool(fixture_components)
    for component in fixture_components:
        try:
            fixture = _git_json(P4_0_IMPLEMENTATION_COMMIT, component["path"])
        except (KeyError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError):
            fixtures_valid = False
            break
        if not isinstance(fixture, dict):
            fixtures_valid = False
            break
        if component["path"].endswith("chronology-v1.json"):
            fixtures_valid = set(fixture) == {
                "occurred_at",
                "observed_at",
                "received_at",
                "recorded_at",
                "corrected_at",
            }
        elif "contract_type" not in fixture:
            fixtures_valid = False
        if not fixtures_valid:
            break
    immutable_diff = _git(
        "diff",
        "--name-only",
        CHECKPOINT,
        "--",
        "contracts/phase-3",
        "docs/phase-3",
        "migrations/versions/0001_camera_registry.py",
        "migrations/versions/0002_camera_version.py",
        "migrations/versions/0003_camera_integrity.py",
        "migrations/versions/0004_stream_management.py",
        "migrations/versions/0005_playback_sessions.py",
        "migrations/versions/0006_onvif_capability_management.py",
        "migrations/versions/0007_onvif_operations.py",
        "migrations/versions/0008_analytics_assignments.py",
        "migrations/versions/0009_generated_analytics.py",
        "migrations/versions/0010_generated_tracking.py",
        "migrations/versions/0011_geometry_events.py",
    )
    evidence_paths = [
        ROOT / "contracts/phase-4/p4-0-evidence.json",
        ROOT / "contracts/phase-4/p4-0-evidence-package.json",
        ROOT / "contracts/phase-4/p4-0-acceptance-proposal.json",
    ]
    evidence_present = all(path.is_file() for path in evidence_paths)
    evidence_non_effective = False
    evidence_package_exact = False
    acceptance_proposal_bound = False
    if evidence_present:
        evidence_package = _json(evidence_paths[1])
        proposal = _json(evidence_paths[-1])
        evidence_non_effective = (
            proposal.get("effective") is False
            and proposal.get("status") == "owner_acceptance_required"
        )
        evidence_package_exact = _evidence_package_is_exact(evidence_package)
        acceptance_proposal_bound = (
            proposal.get("evidence_package_sha256") == _sha256(evidence_paths[1])
            and proposal.get("evidence_content_digest")
            == evidence_package.get("content_digest")
        )

    current_branch = _git("branch", "--show-current")
    accepted_branch = current_branch == P4_0_BRANCH or _p4_1_authorization_is_effective()
    acceptance = _json(P4_0_ACCEPTANCE_PATH)
    validation = evidence_record.get("validation", {})

    return {
        "authorization_package_exact": _sha256(PACKAGE_PATH) == EXPECTED_PACKAGE_SHA256,
        "planning_package_exact": _sha256(ROOT / "docs/phase-4/planning-package.json")
        == EXPECTED_PLANNING_SHA256,
        "planning_acceptance_exact": _sha256(
            ROOT / "contracts/phase-4/p4-planning-r2-acceptance.json"
        )
        == EXPECTED_ACCEPTANCE_SHA256,
        "authorization_effective": authorization.get("effective") is True,
        "owner_acceptance_exact": (
            _sha256(P4_0_ACCEPTANCE_PATH) == EXPECTED_P4_0_ACCEPTANCE_SHA256
            and acceptance.get("effective") is True
            and acceptance.get("accepted_implementation_commit")
            == P4_0_IMPLEMENTATION_COMMIT
            and acceptance.get("evidence_package", {}).get("sha256")
            == _sha256(ROOT / "contracts/phase-4/p4-0-evidence-package.json")
        ),
        "branch_exact": accepted_branch,
        "changed_paths_allowlisted": changed.issubset(allowed),
        "accepted_implementation_commit_ancestor": _is_ancestor(
            P4_0_IMPLEMENTATION_COMMIT
        ),
        "phase3_immutable": not immutable_diff,
        "fixtures_valid": fixtures_valid,
        "contract_catalog_exact": (
            contract_snapshot.get("schema_version")
            == "hcam.phase4.p4_0.intelligence-contract-catalog.v1"
            and len(contract_snapshot.get("contract_types", [])) == 14
        ),
        "openapi_snapshot_exact": (
            openapi_snapshot.get("schema_version")
            == "hcam.phase4.p4_0.openapi-surface.v1"
            and len(openapi_snapshot.get("paths", {})) == 9
        ),
        "database_snapshot_exact": (
            database_snapshot["revision"] == "0012_intelligence_control_plane"
            and len(database_snapshot["new_stores"]) == 10
            and set(database_snapshot["new_stores"])
            == set(database_snapshot["postgresql"]["protected_stores"])
        ),
        "runtime_default_off": "the Phase 4 route surface is absent unless the generated control plane is explicitly enabled"
        in evidence_record.get("security_properties", []),
        "production_enablement_denied": "production rejects generated intelligence control-plane enablement"
        in evidence_record.get("security_properties", []),
        "accepted_validation_recorded": all(
            validation.get(name, {}).get("status", validation.get(name)) == "passed"
            for name in (
                "focused_generated_suite",
                "coverage",
                "sqlite_migration_cycle",
                "postgresql_postgis",
                "full_regression_suite",
            )
        ),
        "evidence_records_present": evidence_present,
        "evidence_package_exact": evidence_package_exact,
        "acceptance_proposal_non_effective": evidence_non_effective,
        "acceptance_proposal_bound": acceptance_proposal_bound,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate P4.0 generated-only readiness")
    parser.add_argument("--json", action="store_true", help="print one JSON result")
    arguments = parser.parse_args()
    try:
        checks = collect_checks()
        passed = all(checks.values())
        result = {"schema_version": "hcam.phase4.p4_0.readiness.v1", "passed": passed, "checks": checks}
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        result = {
            "schema_version": "hcam.phase4.p4_0.readiness.v1",
            "passed": False,
            "failure_code": "readiness_validation_failed",
            "detail": type(exc).__name__,
        }
    if arguments.json:
        print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    else:
        for name, value in result.get("checks", {}).items():
            print(f"{'PASS' if value else 'FAIL'} {name}")
        print("P4.0 readiness: " + ("passed" if result["passed"] else "failed"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
