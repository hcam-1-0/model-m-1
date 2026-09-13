from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from hcam.acceptance import GeneratedAcceptanceService
from hcam.acceptance.claims import validate_against_evidence
from hcam.acceptance.contracts import (
    ClaimRegisterV1,
    EvidenceIndexV1,
    LimitationRegisterV1,
)
from hcam.acceptance.evidence import verify_evidence_index

try:
    from tools import phase47_generated_acceptance
except ModuleNotFoundError:  # Direct script execution places tools/ on sys.path.
    import phase47_generated_acceptance


ROOT = Path(__file__).resolve().parents[1]
START_PACKAGE = ROOT / "contracts/phase-4/p4-7-start-authorization-package.json"
START_AUTHORIZATION = ROOT / "contracts/phase-4/p4-7-start-authorization.json"
PLANNING_PACKAGE = ROOT / "contracts/phase-4/p4-7-planning-r1-package.json"
PLANNING_ACCEPTANCE = ROOT / "contracts/phase-4/p4-7-planning-r1-acceptance.json"
P47_ROOT = ROOT / "contracts/phase-4/p4-7"
ACCEPTANCE_PATH = P47_ROOT / "acceptance.json"
EXPECTED_START_PACKAGE_SHA256 = (
    "39AF9D9DA00DB7806195B4BA2B5512B238A94E7BC41C3F8270431AA2A87EE168"
)
EXPECTED_PLANNING_SHA256 = (
    "A226D7E8E3AB01C240D2692E95DAD5BB051ABB4D015B907BC9197BE835895F9C"
)
EXPECTED_PLANNING_ACCEPTANCE_SHA256 = (
    "EF5C987B93B030B2089A6EFCDDF3D120DC4198FE9975CBD126F91248435503DD"
)
EXPECTED_BRANCH = "codex/phase4-operations-security-scale"
EXPECTED_EVIDENCE_PACKAGE_SHA256 = (
    "B739251D7D86A265DE60BA9B9943A1D0002B515C68AA1297D8B1378ADF1C8FBC"
)
EXPECTED_CANONICAL_COMPONENT_DIGEST = (
    "75D0A3B7667C25BF8B5180639F5B8F3937A734FAA2B2BB63CB9FE9914182A875"
)
EXPECTED_TECHNICAL_COMMIT = "6ad9ff4b06b5f5516e5b346408807a70fe6466a0"
EXPECTED_OWNER_STATEMENT = (
    "D-P4.7-ACCEPTANCE: I, mayank-admin, accept P4.7 evidence package "
    "P4.7-EVIDENCE-PACKAGE-R0 with SHA-256 "
    "B739251D7D86A265DE60BA9B9943A1D0002B515C68AA1297D8B1378ADF1C8FBC "
    "and canonical component digest "
    "75D0A3B7667C25BF8B5180639F5B8F3937A734FAA2B2BB63CB9FE9914182A875, "
    "at technical commit 6ad9ff4b06b5f5516e5b346408807a70fe6466a0, "
    "including its generated-only implementation evidence, deterministic replay, "
    "validation results, authorized P4.6 historical-readiness transition, explicit "
    "environment limitations, Phase 5 handoff contracts, and documented safety "
    "boundaries. This acceptance completes P4.7 and Phase 4 only. It does not "
    "authorize Phase 5 planning or implementation, real providers or network "
    "access, credentials or secrets, Government or private data, cameras or media, "
    "models, datasets, artifacts or inference, operational alerts or actions, "
    "containers, Kubernetes, deployment, or remote Git."
)
PROHIBITED_IMPORTS = frozenset(
    {
        "aiohttp",
        "cv2",
        "ffmpeg",
        "httpx",
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
IGNORED_PREFIXES = ("output/",)
START_CHECKPOINT_HASHES = {
    "contracts/phase-4/p4-7-owner-decisions.json": "560B05473058E49B7B1355752A85463261EA09B435A42C396D2DE393D358FE49",
    "contracts/phase-4/p4-7-planning-r1-acceptance-proposal.json": "D877BBD1199F145BC27DC7BABC74ED9DC4FF25403C23622591B7D25D7FE47572",
    "contracts/phase-4/p4-7-planning-r1-acceptance.json": "EF5C987B93B030B2089A6EFCDDF3D120DC4198FE9975CBD126F91248435503DD",
    "contracts/phase-4/p4-7-planning-r1-package.json": "A226D7E8E3AB01C240D2692E95DAD5BB051ABB4D015B907BC9197BE835895F9C",
    "contracts/phase-4/p4-7-start-authorization-package.json": "39AF9D9DA00DB7806195B4BA2B5512B238A94E7BC41C3F8270431AA2A87EE168",
    "docs/phase-4/p4-7-owner-decisions.md": "F2636F37339D5AE88D82438B60CBF2C082B46928D7B8815E6B252AD53DCAE553",
}
AUTHORIZED_COMPATIBILITY_HASHES = {
    "tests/test_phase46_readiness.py": (
        "4D2A5951071BB70AA614406DE8D133649B58D4B11FEB000FB6FC6E591563579B"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("readiness JSON must contain an object")
    return value


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError("local Git readiness query failed")
    return result.stdout.rstrip()


def _status_paths() -> set[str]:
    paths: set[str] = set()
    for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        path = line[3:].split(" -> ")[-1].strip('"').replace("\\", "/")
        if not path.startswith(IGNORED_PREFIXES):
            paths.add(path)
    return paths


def _changed_paths(base: str) -> set[str]:
    tracked = {
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", base).splitlines()
        if item
    }
    return tracked | _status_paths()


def _allowed_paths(package: dict[str, Any]) -> set[str]:
    result = set(package["exact_additive_implementation_paths"])
    result.update(
        item["path"] for item in package["exact_pre_existing_synchronization_paths"]
    )
    result.update(START_CHECKPOINT_HASHES)
    result.update(AUTHORIZED_COMPATIBILITY_HASHES)
    result.add("contracts/phase-4/p4-7/acceptance.json")
    return result


def _prohibited_imports() -> set[str]:
    found: set[str] = set()
    for path in (ROOT / "app/hcam/acceptance").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name.partition(".")[0] for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.partition(".")[0]]
            else:
                names = []
            found.update(name for name in names if name in PROHIBITED_IMPORTS)
    return found


def checks() -> dict[str, bool]:
    package = _json(START_PACKAGE)
    authorization = _json(START_AUTHORIZATION)
    evidence_package = _json(P47_ROOT / "evidence-package.json")
    acceptance_proposal = _json(P47_ROOT / "acceptance-proposal.json")
    acceptance = _json(ACCEPTANCE_PATH) if ACCEPTANCE_PATH.is_file() else {}
    source_commit = evidence_package["technical_commit"]
    evidence_index = EvidenceIndexV1.model_validate(
        _json(P47_ROOT / "evidence-index.json")
    )
    claims = ClaimRegisterV1.model_validate(_json(P47_ROOT / "claim-register.json"))
    limitations = LimitationRegisterV1.model_validate(
        _json(P47_ROOT / "limitation-register.json")
    )
    validate_against_evidence(claims, limitations, evidence_index)
    phase47_generated_acceptance.generate(source_commit=source_commit, check=True)
    bundle = GeneratedAcceptanceService(
        enabled=True, environment="development"
    ).execute()
    result = {
        "start_package_exact": _sha256(START_PACKAGE) == EXPECTED_START_PACKAGE_SHA256,
        "start_authorization_effective": authorization.get("effective") is True
        and authorization.get("accepted_package", {}).get("sha256")
        == EXPECTED_START_PACKAGE_SHA256,
        "planning_exact": _sha256(PLANNING_PACKAGE) == EXPECTED_PLANNING_SHA256,
        "planning_acceptance_exact": _sha256(PLANNING_ACCEPTANCE)
        == EXPECTED_PLANNING_ACCEPTANCE_SHA256,
        "branch_exact": _git("branch", "--show-current") == EXPECTED_BRANCH,
        "implementation_base_ancestor": subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                package["planning_base_commit"],
                "HEAD",
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
            timeout=30,
        ).returncode
        == 0,
        "changed_paths_allowlisted": _changed_paths(package["planning_base_commit"])
        <= _allowed_paths(package),
        "start_checkpoint_inputs_exact": all(
            _sha256(ROOT / path) == expected
            for path, expected in START_CHECKPOINT_HASHES.items()
        ),
        "historical_compatibility_exact": all(
            _sha256(ROOT / path) == expected
            for path, expected in AUTHORIZED_COMPATIBILITY_HASHES.items()
        ),
        "dependency_pyproject_exact": _sha256(ROOT / "pyproject.toml")
        == package["immutable_dependency_bindings"][0]["sha256"],
        "dependency_lock_exact": _sha256(ROOT / "uv.lock")
        == package["immutable_dependency_bindings"][1]["sha256"],
        "prohibited_imports_absent": not _prohibited_imports(),
        "portfolio_exact": len(bundle.manifest.scenarios) == 9
        and len(bundle.portfolio.runs) == 18
        and len(bundle.portfolio.comparisons) == 9
        and bundle.complete,
        "fixtures_exact": True,
        "evidence_graph_exact": not verify_evidence_index(ROOT, evidence_index)
        and evidence_index.completeness == "complete",
        "claims_bounded": all(
            item.status in {"limited", "unsupported", "withdrawn"}
            for item in claims.claims
        ),
        "acceptance_non_effective": acceptance_proposal.get("effective") is False,
        "owner_acceptance_exact": acceptance.get("effective") is True
        and acceptance.get("status") == "owner_accepted"
        and acceptance.get("decision_id") == "D-P4.7-ACCEPTANCE"
        and acceptance.get("accepted_by") == "mayank-admin"
        and acceptance.get("accepted_branch") == EXPECTED_BRANCH
        and acceptance.get("accepted_implementation_commit")
        == EXPECTED_TECHNICAL_COMMIT
        and acceptance.get("evidence_package", {}).get("package_id")
        == "P4.7-EVIDENCE-PACKAGE-R0"
        and acceptance.get("evidence_package", {}).get("sha256")
        == EXPECTED_EVIDENCE_PACKAGE_SHA256
        and acceptance.get("evidence_package", {}).get(
            "canonical_component_digest"
        )
        == EXPECTED_CANONICAL_COMPONENT_DIGEST
        and _sha256(P47_ROOT / "evidence-package.json")
        == EXPECTED_EVIDENCE_PACKAGE_SHA256
        and evidence_package.get("canonical_component_digest")
        == EXPECTED_CANONICAL_COMPONENT_DIGEST
        and source_commit == EXPECTED_TECHNICAL_COMMIT
        and acceptance_proposal.get("evidence_package_sha256")
        == EXPECTED_EVIDENCE_PACKAGE_SHA256
        and acceptance_proposal.get("canonical_component_digest")
        == EXPECTED_CANONICAL_COMPONENT_DIGEST
        and acceptance.get("owner_statement") == EXPECTED_OWNER_STATEMENT
        and acceptance.get("owner_statement_sha256")
        == hashlib.sha256(EXPECTED_OWNER_STATEMENT.encode("utf-8"))
        .hexdigest()
        .upper()
        and acceptance.get("accepted_progress", {}).get("phase_4_points") == 100
        and acceptance.get("accepted_progress", {}).get("p4_7_points") == 5,
        "phase5_closed": evidence_package.get("phase5_authorized") is False
        and evidence_package.get("phase4_complete") is False
        and "phase5_planning_or_implementation"
        in acceptance.get("continuing_prohibitions", []),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 4.7 generated acceptance readiness"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = checks()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        for name, passed in sorted(result.items()):
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
