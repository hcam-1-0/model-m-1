from __future__ import annotations

import subprocess
from functools import lru_cache

from tools.phase45_readiness import (
    ACCEPTANCE_PATH,
    ACCEPTANCE_PROPOSAL_PATH,
    ACCEPTED_IMPLEMENTATION_COMMIT,
    EVIDENCE_PATH,
    EXPECTED_ACCEPTANCE_SHA256,
    EXPECTED_OWNER_STATEMENT_SHA256,
    EXPECTED_PATHS,
    EXPECTED_SCENARIOS,
    ROOT,
    START_PACKAGE,
    _json,
    _sha256,
    checks,
    seal_evidence_package,
)

OBSOLETE_MUTABLE_CHECKS = frozenset(
    {
        "predecessor_historical_readiness",
        "dependency_pyproject_exact",
        "dependency_lock_exact",
    }
)


def _canonical_git_text(reference: str, path: str) -> str:
    process = subprocess.run(
        ["git", "show", f"{reference}:{path}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == b""
    return process.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _assert_accepted_dependencies_are_preserved() -> None:
    package = _json(START_PACKAGE)
    for item in package["immutable_dependency_bindings"]:
        assert len(item["sha256"]) == 64
        assert _canonical_git_text(
            ACCEPTED_IMPLEMENTATION_COMMIT, item["path"]
        ) == _canonical_git_text("HEAD", item["path"])


@lru_cache(maxsize=1)
def _checks() -> dict[str, bool]:
    return checks()


def test_phase45_readiness_is_exact() -> None:
    results = _checks()
    assert results
    compatible_results = {
        name: passed
        for name, passed in results.items()
        if name not in OBSOLETE_MUTABLE_CHECKS
    }
    if EVIDENCE_PATH.is_file():
        assert all(compatible_results.values()), [
            name for name, passed in compatible_results.items() if not passed
        ]
        _assert_accepted_dependencies_are_preserved()
        return
    core = {
        name: passed
        for name, passed in compatible_results.items()
        if not name.startswith("evidence_")
        and not name.startswith("acceptance_proposal_")
    }
    assert core and all(core.values()), [
        name for name, passed in core.items() if not passed
    ]
    _assert_accepted_dependencies_are_preserved()


def test_phase45_frozen_surface_counts() -> None:
    assert EXPECTED_SCENARIOS == 552
    assert len(EXPECTED_PATHS) == 16


def test_phase45_owner_acceptance_is_exact_and_effective() -> None:
    acceptance = _json(ACCEPTANCE_PATH)
    proposal = _json(ACCEPTANCE_PROPOSAL_PATH)
    assert _sha256(ACCEPTANCE_PATH) == EXPECTED_ACCEPTANCE_SHA256
    assert acceptance["effective"] is True
    assert acceptance["status"] == "owner_accepted"
    assert acceptance["accepted_implementation_commit"] == (
        ACCEPTED_IMPLEMENTATION_COMMIT
    )
    assert acceptance["owner_statement"] == proposal["owner_acceptance_statement"]
    assert acceptance["owner_statement_sha256"] == (
        EXPECTED_OWNER_STATEMENT_SHA256
    )
    assert acceptance["accepted_progress"] == {
        "phase_4_points": 85,
        "phase_4_total_points": 100,
        "phase_4_percent": 85.0,
        "p4_5_points": 15,
        "p4_5_total_points": 15,
        "p4_5_percent": 100.0,
    }


def test_phase45_accepted_evidence_cannot_be_resealed() -> None:
    try:
        seal_evidence_package()
    except RuntimeError as exc:
        assert str(exc) == "accepted P4.5 evidence cannot be resealed"
    else:
        raise AssertionError("accepted P4.5 evidence was unexpectedly resealed")
