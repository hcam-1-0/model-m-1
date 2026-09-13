from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools import phase50_readiness


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/phase50_readiness.py"


def test_phase50_core_readiness_checks_pass_before_evidence_seal() -> None:
    result = phase50_readiness.checks()
    assert result
    assert all(result.values())


def test_phase50_readiness_fails_closed_when_evidence_is_required_early() -> None:
    result = phase50_readiness.checks(require_evidence=True)
    evidence_paths = (
        ROOT / "contracts/phase-5/p5-0-evidence.json",
        ROOT / "contracts/phase-5/p5-0-evidence-package.json",
        ROOT / "contracts/phase-5/p5-0-acceptance-proposal.json",
        ROOT / "docs/phase-5/p5-0-evidence.md",
    )
    if all(path.is_file() for path in evidence_paths):
        assert result["evidence_paths_present"] is True
    else:
        assert result["evidence_paths_present"] is False
        assert all(value for key, value in result.items() if key != "evidence_paths_present")


def test_phase50_readiness_cli_emits_bounded_json() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "app")
    process = subprocess.run(
        [sys.executable, str(TOOL), "--json"],
        cwd=ROOT,
        capture_output=True,
        env=environment,
        text=True,
        timeout=60,
        check=False,
    )
    result = json.loads(process.stdout)
    assert process.returncode == 0
    assert process.stderr == ""
    assert result == phase50_readiness.checks()


def test_phase50_source_has_no_network_or_remote_git_surface() -> None:
    readiness_source = TOOL.read_text(encoding="utf-8")
    evidence_source = (ROOT / "tools/phase50_evidence.py").read_text(encoding="utf-8")
    combined = readiness_source + evidence_source
    assert "http://" not in combined and "https://" not in combined
    for command in ("push", "pull", "fetch", "clone", "ls-remote"):
        assert f'"{command}"' not in combined
    assert phase50_readiness._prohibited_imports() == set()


def test_phase50_authorization_and_planning_packages_remain_exact() -> None:
    assert phase50_readiness._sha256(phase50_readiness.START_PACKAGE) == (
        phase50_readiness.EXPECTED_START_SHA256
    )
    assert phase50_readiness._sha256(phase50_readiness.PLANNING_PACKAGE) == (
        phase50_readiness.EXPECTED_PLANNING_SHA256
    )


def test_phase50_authorized_paths_are_unique_and_present_as_expected() -> None:
    package = phase50_readiness._json(phase50_readiness.START_PACKAGE)
    paths = package["exact_additive_implementation_paths"]
    assert len(paths) == len(set(paths)) == 40
    assert all(
        path.startswith(
            ("app/", "contracts/", "docs/", "fixtures/", "tests/", "tools/")
        )
        for path in paths
    )
    assert package["remote_git_authorized"] is False
    assert package["separate_exit_acceptance_required"] is True
