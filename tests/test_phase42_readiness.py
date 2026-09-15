from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/phase42_readiness.py"
OBSOLETE_MUTABLE_CHECKS = frozenset({"immutable_dependencies_exact"})


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


def _assert_accepted_dependencies_are_preserved(module, package: dict) -> None:
    for item in package["immutable_dependency_bindings"]:
        assert len(item["sha256"]) == 64
        assert _canonical_git_text(
            module.ACCEPTED_IMPLEMENTATION_COMMIT, item["path"]
        ) == _canonical_git_text("HEAD", item["path"])


def _module():
    specification = importlib.util.spec_from_file_location("phase42_readiness", TOOL)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_phase42_readiness_core_checks_fail_closed() -> None:
    checks = _module().collect_checks()
    core = {
        name: value
        for name, value in checks.items()
        if not name.startswith("evidence_")
        and not name.startswith("acceptance_proposal_")
        and name not in OBSOLETE_MUTABLE_CHECKS
    }
    assert core
    assert all(core.values())
    module = _module()
    _assert_accepted_dependencies_are_preserved(
        module, module._json(module.START_PACKAGE_PATH)
    )


def test_phase42_readiness_cli_is_bounded_json() -> None:
    process = subprocess.run(
        [sys.executable, str(TOOL), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    result = json.loads(process.stdout)
    assert process.stderr == ""
    assert result["schema_version"] == "hcam.phase4.p4_2.readiness.v1"
    assert isinstance(result["passed"], bool)
    assert set(result.get("checks", {})) == set(_module().collect_checks())


def test_phase42_readiness_has_no_network_or_remote_git_commands() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "http://" not in source and "https://" not in source
    for command in ("push", "pull", "fetch", "clone", "ls-remote"):
        assert f'"{command}"' not in source


def test_phase42_authorization_and_dependencies_are_exact() -> None:
    module = _module()
    package = module._json(module.START_PACKAGE_PATH)
    authorization = module._json(module.START_AUTHORIZATION_PATH)
    assert module._sha256(module.START_PACKAGE_PATH) == (
        module.EXPECTED_START_PACKAGE_SHA256
    )
    assert authorization["effective"] is True
    assert authorization["authorization_package"]["sha256"] == (
        module.EXPECTED_START_PACKAGE_SHA256
    )
    _assert_accepted_dependencies_are_preserved(module, package)


def test_phase42_historical_compatibility_amendment_is_hash_bound() -> None:
    module = _module()
    authorization = module._json(module.START_AUTHORIZATION_PATH)
    checkpoint = authorization["planning_checkpoint"]
    assert module._historical_compatibility_amendment_is_bound(checkpoint)
    assert set(module.HISTORICAL_COMPATIBILITY_AMENDMENT).issubset(
        module._allowed_paths(module._json(module.START_PACKAGE_PATH), checkpoint)
    )


def test_phase42_evidence_package_requires_every_changed_component() -> None:
    module = _module()
    package = module._json(module.START_AUTHORIZATION_PATH)
    required = module._changed_paths(package["planning_checkpoint"]) - (
        module.PACKAGE_CONTROL_PATHS
    )
    assert required
    assert not module._evidence_package_is_exact(
        {
            "component_digest_mode": "utf8_text_normalized_lf",
            "components": [],
            "content_digest": module._canonical_digest({"components": []}),
        },
        required,
    )


def test_phase42_owner_acceptance_is_exact_and_effective() -> None:
    module = _module()
    acceptance = module._json(module.ACCEPTANCE_PATH)
    assert module._sha256(module.ACCEPTANCE_PATH) == (module.EXPECTED_ACCEPTANCE_SHA256)
    assert acceptance["effective"] is True
    assert acceptance["decision_id"] == "D-P4.2-ACCEPTANCE"
    assert acceptance["accepted_implementation_commit"] == (
        module.ACCEPTED_IMPLEMENTATION_COMMIT
    )
    assert acceptance["evidence_package"]["sha256"] == module._sha256(
        module.EVIDENCE_PACKAGE_PATH
    )
    assert acceptance["owner_statement_sha256"] == (
        module.EXPECTED_OWNER_STATEMENT_SHA256
    )


def test_phase42_readiness_uses_accepted_git_objects_after_acceptance() -> None:
    module = _module()
    checks = module.collect_checks()
    assert checks["accepted_implementation_commit_ancestor"] is True
    assert checks["changed_paths_allowlisted"] is True
    assert checks["evidence_package_exact"] is True
    assert checks["owner_acceptance_exact"] is True
    assert module._catalogs_are_exact(
        source_commit=module.ACCEPTED_IMPLEMENTATION_COMMIT
    )
