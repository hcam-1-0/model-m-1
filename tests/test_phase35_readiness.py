from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from tools import phase35_readiness as readiness


def test_p3_5_runtime_research_is_authorized_with_one_manual_gate() -> None:
    report = readiness.build_report()

    assert (
        report.status
        == "artifact_review_accepted_runtime_research_authorized_evidence_pending"
    )
    assert report.failures == 0
    assert report.manual_gates == 1
    assert report.package_file_count == 43
    assert len(report.package_digest) == 64


def test_p3_5_technical_checks_pass() -> None:
    checks = (
        readiness.check_required_files(),
        readiness.check_planning_authorization(),
        readiness.check_accepted_p3_4_dependency(),
        readiness.check_candidate_boundary(),
        readiness.check_existing_contract_foundation(),
        readiness.check_research_sources(),
        readiness.check_plan_contract(),
        readiness.check_planning_only_package(),
        readiness.check_artifact_proposal(),
        readiness.check_owner_decisions_record(),
        readiness.check_artifact_research_authorization(),
        readiness.check_artifact_review_evidence(),
        readiness.check_artifact_review_acceptance(),
        readiness.check_artifact_sbom(),
        readiness.check_artifact_model_cards(),
        readiness.check_runtime_review_proposal(),
        readiness.check_runtime_research_authorization(),
        readiness.check_start_intent(),
        readiness.check_documentation_sync(),
    )

    assert all(check.status == readiness.PASS for check in checks)


def test_p3_5_only_final_start_remains_manual() -> None:
    check = readiness.check_owner_gates()

    assert check.status == readiness.MANUAL
    assert check.evidence == ("D-P3.5-START",)


def test_p3_5_owner_decisions_record_exact_recommended_baseline() -> None:
    record = json.loads(readiness.OWNER_DECISIONS_PATH.read_text(encoding="utf-8"))

    assert [item["selected_option"] for item in record["decisions"]] == [
        "A",
        "A",
        "A",
        "A",
    ]
    assert record["technical_decisions_completed"] == 4
    assert record["implementation_authorized"] is False
    assert readiness.check_owner_decisions_record().status == readiness.PASS


def test_p3_5_artifact_research_is_exactly_bounded() -> None:
    record = json.loads(
        readiness.ARTIFACT_RESEARCH_AUTHORIZATION_PATH.read_text(encoding="utf-8")
    )

    assert len(record["allowed_artifacts"]) == 7
    assert record["limits"]["maximum_redirects"] == 0
    assert record["limits"]["environment_proxies"] is False
    assert record["limits"]["runtime_loading_from_quarantine"] is False
    assert record["implementation_authorized"] is False
    assert readiness.check_artifact_research_authorization().status == readiness.PASS


def test_p3_5_artifact_research_rejects_proposal_digest_change(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.ARTIFACT_RESEARCH_AUTHORIZATION_PATH:
            record["proposal_sha256"] = "0" * 64
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_artifact_research_authorization().status == readiness.FAIL


def test_p3_5_artifact_research_rejects_unlisted_url(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.ARTIFACT_RESEARCH_AUTHORIZATION_PATH:
            allowed = record["allowed_artifacts"]
            assert isinstance(allowed, list)
            allowed[0]["source_url"] = "https://example.invalid/model.tar"
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_artifact_research_authorization().status == readiness.FAIL


def test_p3_5_exact_artifact_evidence_is_non_executing() -> None:
    record = json.loads(
        readiness.ARTIFACT_REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8")
    )

    assert record["artifact_count"] == 7
    assert record["inspection"]["artifact_bytes"] == 117617083
    assert record["inspection"]["archive_extraction_performed"] is False
    assert record["inspection"]["runtime_execution_performed"] is False
    assert record["defender_scan"]["finding"] == "no_threats_found"
    assert readiness.check_artifact_review_evidence().status == readiness.PASS


def test_p3_5_exact_artifact_evidence_is_owner_accepted() -> None:
    record = json.loads(
        readiness.ARTIFACT_REVIEW_ACCEPTANCE_PATH.read_text(encoding="utf-8")
    )

    assert (
        record["evidence_package_digest"]
        == "54B02B80169604904C9945C1C6E692500CA8AA79253EEC27A63B4C4DB00B395C"
    )
    assert record["accepted_by"] == "mayank-admin"
    assert record["implementation_authorized"] is False
    assert readiness.check_artifact_review_acceptance().status == readiness.PASS


def test_p3_5_runtime_review_remains_proposal_only() -> None:
    record = json.loads(
        readiness.RUNTIME_REVIEW_PROPOSAL_PATH.read_text(encoding="utf-8")
    )

    assert record["next_decision"]["decision_id"] == "D-P3.5-RUNTIME-RESEARCH"
    assert record["package_downloads_performed"] is False
    assert record["dependency_or_lockfile_change_performed"] is False
    assert record["implementation_authorized"] is False
    assert record["allowed_network_actions"] == []
    assert readiness.check_runtime_review_proposal().status == readiness.PASS


def test_p3_5_runtime_research_authorization_is_external_and_non_runtime() -> None:
    record = json.loads(
        readiness.RUNTIME_RESEARCH_AUTHORIZATION_PATH.read_text(encoding="utf-8")
    )

    assert record["authorization_id"] == "D-P3.5-RUNTIME-RESEARCH"
    assert record["limits"]["python_version"] == "3.12.13"
    assert record["limits"]["binary_wheels_only"] is True
    assert record["limits"]["runtime_constructors_or_inference"] is False
    assert record["dependency_or_lockfile_change_authorized"] is False
    assert record["implementation_authorized"] is False
    assert readiness.check_runtime_research_authorization().status == readiness.PASS


def test_p3_5_start_intent_is_non_effective_and_has_no_authority() -> None:
    record = json.loads(
        readiness.START_AUTHORIZATION_PATH.read_text(encoding="utf-8")
    )

    assert record["owner_statement_received"] == "D-P3.5-START"
    assert record["effective"] is False
    assert record["implementation_authorized"] is False
    assert record["allowed_artifacts"] == []
    assert record["allowed_network_actions"] == []
    assert readiness.check_start_intent().status == readiness.PASS


def test_p3_5_start_intent_rejects_premature_authority(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.START_AUTHORIZATION_PATH:
            record["implementation_authorized"] = True
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_start_intent().status == readiness.FAIL


def test_p3_5_artifact_proposal_has_no_download_or_runtime_authority() -> None:
    record = json.loads(readiness.ARTIFACT_PROPOSAL_PATH.read_text(encoding="utf-8"))

    assert record["download_performed"] is False
    assert record["acquisition_authorized"] is False
    assert record["implementation_authorized"] is False
    assert record["allowed_network_actions"] == []
    assert len(record["artifacts"]) == 8
    assert all(item["expected_sha256"] is None for item in record["artifacts"])
    assert readiness.check_artifact_proposal().status == readiness.PASS


def test_p3_5_artifact_proposal_rejects_premature_hash(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.ARTIFACT_PROPOSAL_PATH:
            artifacts = record["artifacts"]
            assert isinstance(artifacts, list)
            artifacts[0]["expected_sha256"] = "0" * 64
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_artifact_proposal().status == readiness.FAIL


def test_p3_5_require_decisions_exits_two_without_implementation_authority() -> None:
    with redirect_stdout(io.StringIO()):
        exit_code = readiness.main(["--json", "--strict", "--require-decisions"])

    assert exit_code == 2


def test_p3_5_planning_authorization_rejects_implementation_flag(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.AUTHORIZATION_PATH:
            record["implementation_authorized"] = True
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_planning_authorization().status == readiness.FAIL


def test_p3_5_rejects_changed_p3_4_digest(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.P3_4_ACCEPTANCE_PATH:
            record["evidence_package_digest"] = "0" * 64
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_accepted_p3_4_dependency().status == readiness.FAIL


def test_p3_5_research_sources_are_primary_and_no_download() -> None:
    record = json.loads(readiness.RESEARCH_PATH.read_text(encoding="utf-8"))

    assert record["artifact_downloads_performed"] is False
    assert record["dataset_downloads_performed"] is False
    assert record["model_downloads_performed"] is False
    assert len(record["sources"]) == 10
    assert readiness.check_research_sources().status == readiness.PASS


def test_p3_5_candidates_remain_blocked() -> None:
    assert readiness.check_candidate_boundary().status == readiness.PASS


def test_p3_5_package_has_no_runtime_migration_model_or_media() -> None:
    assert readiness.check_planning_only_package().status == readiness.PASS
    assert not any(path.startswith("app/") for path in readiness.PACKAGE_FILES)
    assert not any(path.startswith("migrations/") for path in readiness.PACKAGE_FILES)


def test_p3_5_package_digest_is_deterministic_and_path_relative() -> None:
    first_digest, first_manifest = readiness.package_digest()
    second_digest, second_manifest = readiness.package_digest()

    assert first_digest == second_digest
    assert first_manifest == second_manifest
    assert len(first_manifest) == len(readiness.PACKAGE_FILES)
    assert all(":\\" not in item for item in first_manifest)
    assert all(" sha256=" in item and " bytes=" in item for item in first_manifest)
