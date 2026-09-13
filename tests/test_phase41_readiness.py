from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/phase41_readiness.py"


def _module():
    specification = importlib.util.spec_from_file_location("phase41_readiness", TOOL)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_phase41_readiness_core_checks_fail_closed() -> None:
    checks = _module().collect_checks()
    core = {
        name: value
        for name, value in checks.items()
        if not name.startswith("evidence_")
        and not name.startswith("acceptance_proposal_")
    }
    assert core
    assert all(core.values())


def test_phase41_readiness_cli_is_bounded_json() -> None:
    process = subprocess.run(
        [sys.executable, str(TOOL), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    result = json.loads(process.stdout)
    assert process.stderr == ""
    assert result["schema_version"] == "hcam.phase4.p4_1.readiness.v1"
    assert isinstance(result["passed"], bool)
    assert set(result.get("checks", {})) == set(_module().collect_checks())


def test_phase41_readiness_has_no_network_or_remote_git_commands() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "http://" not in source and "https://" not in source
    for command in ("push", "pull", "fetch", "clone", "ls-remote"):
        assert f'"{command}"' not in source


def test_legacy_migration_amendment_is_exactly_hash_bound() -> None:
    module = _module()
    assert module._git_canonical_text_sha256(
        module.ACCEPTED_IMPLEMENTATION_COMMIT,
        module.LEGACY_MIGRATION_TEST_PATH,
    ) == (module.EXPECTED_LEGACY_MIGRATION_TEST_SHA256)
    assert module.LEGACY_MIGRATION_TEST_PATH in module._allowed_paths(
        json.loads(module.START_PACKAGE_PATH.read_text(encoding="utf-8"))
    )


def test_phase41_owner_acceptance_is_exact_and_effective() -> None:
    module = _module()
    acceptance = json.loads(module.ACCEPTANCE_PATH.read_text(encoding="utf-8"))
    assert module._sha256(module.ACCEPTANCE_PATH) == module.EXPECTED_ACCEPTANCE_SHA256
    assert acceptance["effective"] is True
    assert acceptance["decision_id"] == "D-P4.1-ACCEPTANCE"
    assert acceptance["accepted_implementation_commit"] == (
        module.ACCEPTED_IMPLEMENTATION_COMMIT
    )
    assert acceptance["evidence_package"]["sha256"] == module._sha256(
        module.EVIDENCE_PACKAGE_PATH
    )


def test_phase41_readiness_uses_accepted_git_objects_after_phase_transition() -> None:
    module = _module()
    checks = module.collect_checks()
    assert checks["accepted_branch_binding_exact"] is True
    assert checks["accepted_implementation_commit_ancestor"] is True
    assert checks["changed_paths_allowlisted"] is True
    assert checks["p4_0_historical_readiness"] is True
