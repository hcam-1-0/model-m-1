import json
import subprocess
from types import SimpleNamespace

from tools import phase47_generated_acceptance, phase47_readiness

PHASE4_ACCEPTANCE_COMMIT = "96a902315e78c184e92df9ebe5bcef1e336eab38"
OBSOLETE_MUTABLE_CHECKS = frozenset(
    {
        "branch_exact",
        "changed_paths_allowlisted",
        "historical_compatibility_exact",
        "dependency_pyproject_exact",
        "dependency_lock_exact",
        "evidence_graph_exact",
    }
)


def _git_bytes(reference: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{reference}:{path}"],
        cwd=phase47_readiness.ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == b""
    return process.stdout


def _canonical_text(content: bytes) -> str:
    return content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _json_at(reference: str, path: str) -> dict:
    value = json.loads(_git_bytes(reference, path).decode("utf-8"))
    assert isinstance(value, dict)
    return value


def _accepted_generated_paths() -> set[str]:
    path = "contracts/phase-4/p4-7/evidence-package.json"
    package = _json_at(PHASE4_ACCEPTANCE_COMMIT, path)
    paths = set(package["components"])
    paths.update(
        {
            path,
            "contracts/phase-4/p4-7/acceptance-proposal.json",
        }
    )
    assert len(paths) == 32
    return paths


def _assert_accepted_generated_artifacts_are_preserved() -> dict[str, str]:
    preserved: dict[str, str] = {}
    for path in sorted(_accepted_generated_paths()):
        accepted = _canonical_text(_git_bytes(PHASE4_ACCEPTANCE_COMMIT, path))
        current = _canonical_text(_git_bytes("HEAD", path))
        assert current == accepted
        preserved[path] = accepted
    return preserved


def _assert_accepted_dependencies_are_preserved() -> None:
    package = _json_at(
        PHASE4_ACCEPTANCE_COMMIT,
        "contracts/phase-4/p4-7-start-authorization-package.json",
    )
    for item in package["immutable_dependency_bindings"]:
        assert len(item["sha256"]) == 64
        accepted = _canonical_text(
            _git_bytes(phase47_readiness.EXPECTED_TECHNICAL_COMMIT, item["path"])
        )
        assert _canonical_text(_git_bytes("HEAD", item["path"])) == accepted


def _accepted_generation_check(*, source_commit: str, check: bool) -> dict[str, str]:
    assert source_commit == phase47_readiness.EXPECTED_TECHNICAL_COMMIT
    assert check is True
    return _assert_accepted_generated_artifacts_are_preserved()


def test_generated_artifacts_match_accepted_git_objects_canonically() -> None:
    package = phase47_readiness._json(
        phase47_readiness.P47_ROOT / "evidence-package.json"
    )
    evidence = phase47_readiness._json(
        phase47_readiness.P47_ROOT / "evidence.json"
    )
    accepted = _assert_accepted_generated_artifacts_are_preserved()
    assert package["technical_commit"] == phase47_readiness.EXPECTED_TECHNICAL_COMMIT
    assert len(accepted) == 32
    assert package["validation"] == phase47_generated_acceptance.VALIDATION_SUMMARY
    assert evidence["validation"] == phase47_generated_acceptance.VALIDATION_SUMMARY


def test_phase47_readiness_is_exact_and_future_gates_stay_closed(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        phase47_generated_acceptance, "generate", _accepted_generation_check
    )
    results = phase47_readiness.checks()
    compatible_results = {
        name: passed
        for name, passed in results.items()
        if name not in OBSOLETE_MUTABLE_CHECKS
    }
    assert all(compatible_results.values()), {
        name: passed for name, passed in compatible_results.items() if not passed
    }
    _assert_accepted_dependencies_are_preserved()
    assert phase47_readiness._git(
        "merge-base", "--is-ancestor", PHASE4_ACCEPTANCE_COMMIT, "HEAD"
    ) == ""
    assert results["owner_acceptance_exact"] is True
    assert results["phase5_closed"] is True


def test_git_output_preserves_porcelain_status_prefix(monkeypatch) -> None:
    monkeypatch.setattr(
        phase47_readiness.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=" M README.md\n",
        ),
    )

    assert phase47_readiness._git("status") == " M README.md"
    assert phase47_readiness._status_paths() == {"README.md"}
