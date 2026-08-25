from __future__ import annotations

import copy
import io
import json
import re
from contextlib import redirect_stdout

from tools import phase34_readiness as readiness


def test_current_planning_state_is_valid_with_only_start_gate_pending() -> None:
    report = readiness.build_readiness_report()

    assert report.status == "ready_for_implementation_authorization"
    assert report.scope == "phase3.p3_4.geometry_and_event_primitives.planning_only"
    assert report.failures == 0
    assert report.manual_gates == 1
    assert re.fullmatch(r"[0-9A-F]{64}", report.package_digest)


def test_default_and_strict_cli_allow_pending_manual_decisions() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        default_exit = readiness.main(["--json"])
        strict_exit = readiness.main(["--strict"])

    payload = json.loads(output.getvalue().split("Phase 3 P3.4")[0])
    assert default_exit == 0
    assert strict_exit == 0
    assert payload["status"] == "ready_for_implementation_authorization"
    assert payload["failures"] == 0
    assert payload["manual_gates"] == 1


def test_require_decisions_reports_manual_gate_exit() -> None:
    assert readiness.main(["--require-decisions"]) == 2


def test_all_technical_checks_pass_and_entry_gate_is_manual() -> None:
    checks = (
        readiness.check_required_files(),
        readiness.check_planning_authorization(),
        readiness.check_accepted_dependency(),
        readiness.check_owner_decisions(),
        readiness.check_entry_gates(),
        readiness.check_research_sources(),
        readiness.check_plan_contract(),
        readiness.check_dependency_boundary(),
        readiness.check_documentation_sync(),
    )

    assert all(check.status != readiness.FAIL for check in checks)
    assert readiness.check_entry_gates().status == readiness.MANUAL


def test_package_digest_is_deterministic_and_manifest_is_relative() -> None:
    first_digest, first_manifest = readiness.package_digest()
    second_digest, second_manifest = readiness.package_digest()

    assert first_digest == second_digest
    assert first_manifest == second_manifest
    assert len(first_manifest) == len(readiness.PACKAGE_FILES)
    assert all(str(readiness.ROOT) not in line for line in first_manifest)


def test_planning_authorization_rejects_implementation_widening(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.AUTHORIZATION:
            value["implementation_authorized"] = True
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_planning_authorization()

    assert result.status == readiness.FAIL
    assert "boundary changed" in result.detail


def test_planning_authorization_rejects_removed_camera_boundary(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.AUTHORIZATION:
            value["prohibited_actions"].remove(
                "physical_camera_onvif_media_or_sentinel_stream_access"
            )
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_planning_authorization()

    assert result.status == readiness.FAIL
    assert "prohibited_actions" in result.evidence


def test_dependency_check_rejects_p3_3_digest_drift(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.P3_3_ACCEPTANCE:
            value["evidence_package_digest"] = "0" * 64
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_accepted_dependency()

    assert result.status == readiness.FAIL
    assert "identity changed" in result.detail


def test_owner_decisions_reject_hybrid_geometry_drift(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.OWNER_DECISIONS:
            value["decisions"][0]["selected_option"] = "shapely_only"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_owner_decisions()

    assert result.status == readiness.FAIL
    assert "technical baseline" in result.detail


def test_owner_decisions_reject_unbounded_dsl_drift(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.OWNER_DECISIONS:
            value["decisions"][1]["selected_option"] = "unrestricted_dsl"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_owner_decisions()

    assert result.status == readiness.FAIL
    assert "technical baseline" in result.detail


def test_entry_gates_reject_silent_implementation_authorization(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_GATES:
            value["decisions"][-1]["status"] = "owner_approved"
            value["implementation_authorized"] = True
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_gates()

    assert result.status == readiness.FAIL
    assert "changed" in result.detail


def test_research_sources_reject_unapproved_host(monkeypatch) -> None:
    original = readiness._read

    def changed(relative_path: str) -> str:
        value = original(relative_path)
        if relative_path == "docs/phase-3/p3-4-research-record.md":
            return value + "\n[untrusted](https://example.com/blog)\n"
        return value

    monkeypatch.setattr(readiness, "_read", changed)
    result = readiness.check_research_sources()

    assert result.status == readiness.FAIL
    assert "unapproved:example.com" in result.evidence


def test_dependency_boundary_rejects_early_shapely_addition(monkeypatch) -> None:
    original = readiness._read

    def changed(relative_path: str) -> str:
        value = original(relative_path)
        if relative_path == "pyproject.toml":
            return value + '\nshapely = "2.1.2"\n'
        return value

    monkeypatch.setattr(readiness, "_read", changed)
    result = readiness.check_dependency_boundary()

    assert result.status == readiness.FAIL
    assert "before implementation authorization" in result.detail


def test_documentation_sync_rejects_missing_ci_command(monkeypatch) -> None:
    original = readiness._read

    def changed(relative_path: str) -> str:
        value = original(relative_path)
        if relative_path == ".github/workflows/python-ci.yml":
            return value.replace("python tools/phase34_readiness.py --strict", "true")
        return value

    monkeypatch.setattr(readiness, "_read", changed)
    result = readiness.check_documentation_sync()

    assert result.status == readiness.FAIL
    assert ".github/workflows/python-ci.yml" in result.evidence
