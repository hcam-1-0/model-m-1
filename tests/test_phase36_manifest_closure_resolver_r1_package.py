from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts/phase-3"
PACKAGE = CONTRACTS / "p3-6-manifest-closure-resolver-r1-implementation-package.json"
EVIDENCE = CONTRACTS / "p3-6-manifest-closure-resolver-r1-implementation-evidence.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_U4F_package_binds_every_core_file_and_review() -> None:
    package = _read(PACKAGE)

    assert package["core_file_count"] == len(package["core_files"]) == 13
    assert len({item["path"] for item in package["core_files"]}) == 13
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    review = package["review_document"]
    assert _sha256(ROOT / review["path"]) == review["sha256"]


def test_U4F_evidence_is_complete_but_does_not_claim_R3_or_Phase_3() -> None:
    evidence = _read(EVIDENCE)
    validation = evidence["generated_validation"]
    local = evidence["bounded_local_diagnostic"]
    remaining = evidence["remaining_gate"]

    assert validation["vector_count"] == 512
    assert validation["full_Phase_3_6_pytest_passed"] == 2573
    assert validation["full_Phase_3_6_pytest_failed"] == 0
    assert local["manifest_directory_candidate_present"] is False
    assert local["PSHome_candidate_present"] is True
    assert local["local_Authenticode_status"] == "Valid"
    assert local["diagnostic_is_not_cache_only_WinVerifyTrust_closeout_evidence"] is True
    assert remaining["U4F_source_and_generated_validation_complete"] is True
    assert remaining["R3_exact_action_spec_and_runtime_closeout_complete"] is False
    assert remaining["U3K_storage_attempt_complete"] is False
    assert remaining["Phase_3_complete"] is False


def test_U4F_package_and_evidence_are_LF_registered() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (PACKAGE, EVIDENCE, Path(__file__)):
        relative = path.relative_to(ROOT).as_posix()
        assert attributes.count(f"{relative} text eol=lf") == 1
        assert b"\r\n" not in path.read_bytes()
