import subprocess

from tools import phase46_readiness


PHASE46_ACCEPTANCE_COMMIT = "98234e475e938d7ca1dee5558d2088dabc187845"
AUTHORIZED_LATER_COMPONENT_PATHS = frozenset(
    {
        "README.md",
        "docs/phase-4/README.md",
        "docs/phase-4/status.md",
        "tests/test_phase46_readiness.py",
    }
)
OBSOLETE_MUTABLE_CHECKS = frozenset(
    {
        "implementation_branch_exact",
        "changed_paths_allowlisted",
        "predecessor_historical_readiness",
        "dependency_pyproject_exact",
        "dependency_lock_exact",
    }
)


def _canonical_git_text(reference: str, path: str) -> str:
    process = subprocess.run(
        ["git", "show", f"{reference}:{path}"],
        cwd=phase46_readiness.ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == b""
    return process.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _assert_accepted_dependencies_are_preserved(
    package: dict, accepted_commit: str
) -> None:
    for item in package["immutable_dependency_bindings"]:
        assert len(item["sha256"]) == 64
        assert _canonical_git_text(
            accepted_commit, item["path"]
        ) == _canonical_git_text("HEAD", item["path"])


def test_phase46_snapshots_are_reproducible() -> None:
    assert phase46_readiness._json(
        phase46_readiness.P46_ROOT / "operations-contracts.json"
    ) == phase46_readiness._contract_catalog()
    assert phase46_readiness._json(
        phase46_readiness.P46_ROOT / "database.json"
    ) == phase46_readiness._database_snapshot()
    assert phase46_readiness._json(
        phase46_readiness.P46_ROOT / "openapi.json"
    ) == phase46_readiness._openapi_snapshot()


def test_phase46_readiness_and_owner_acceptance_are_exact() -> None:
    results = phase46_readiness.checks()
    historical_baseline = (
        phase46_readiness.BASELINE_CHECKS - OBSOLETE_MUTABLE_CHECKS
    )
    assert all(results[name] for name in historical_baseline)
    assert all(results[name] for name in phase46_readiness.EVIDENCE_CHECKS)
    assert results["owner_acceptance_exact"] is True

    package = phase46_readiness._json(phase46_readiness.START_PACKAGE)
    authorization = phase46_readiness._json(phase46_readiness.START_AUTHORIZATION)
    acceptance = phase46_readiness._json(phase46_readiness.ACCEPTANCE_PATH)
    accepted_commit = acceptance["accepted_implementation_commit"]
    _assert_accepted_dependencies_are_preserved(package, accepted_commit)
    sealed_paths = phase46_readiness._changed_paths_between(
        authorization["implementation_base_commit"],
        PHASE46_ACCEPTANCE_COMMIT,
    )
    assert sealed_paths
    assert sealed_paths <= phase46_readiness._allowed_paths(package)
    assert phase46_readiness._is_ancestor(PHASE46_ACCEPTANCE_COMMIT)

    evidence_package = phase46_readiness._json(
        phase46_readiness.EVIDENCE_PACKAGE_PATH
    )
    accepted_component_paths = {
        component["path"] for component in evidence_package["components"]
    }
    later_paths = phase46_readiness._changed_paths(PHASE46_ACCEPTANCE_COMMIT)
    assert later_paths & accepted_component_paths <= AUTHORIZED_LATER_COMPONENT_PATHS
