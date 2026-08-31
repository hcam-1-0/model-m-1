from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-quarantine-remediation-r1"
SOURCES_PATH = CONTRACTS / f"{STEM}-research-sources.json"
DECISIONS_PATH = CONTRACTS / f"{STEM}-decision-packet.json"
PROPOSAL_PATH = CONTRACTS / f"{STEM}-proposal.json"
DOCUMENT_PATH = DOCS / f"{STEM}-proposal.md"
PACKAGE_PATH = CONTRACTS / f"{STEM}-decision-package.json"
PACKAGE_DIGEST = "9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78"
ACCEPTANCE_DIGEST = (
    "BDA7E9C6B8ACF4ECB8641B61F47A45E4E02768B58C7E3A08179507B7ABAFDF1F"
)
U3G_PACKAGE_DIGEST = (
    "C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B"
)
U3E_PACKAGE_DIGEST = (
    "9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39"
)
U3E_AUTHORIZATION_SHA256 = (
    "0DB03056BEF964D0B5C830DE01C3FE91DA87592BFAF1905D7C8307AC71FA5208"
)
U3E_RESULT_SHA256 = (
    "3DE3B1E08CF39D9348BD9873C378E0CA0FE6EC8806AB27E0C48A6BB975A72BF2"
)
U3E_EVIDENCE_SHA256 = (
    "2FB06243003FF4C4E48C7E7BEF67C2B79C4BCA65826E1B09769AF688AE536376"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_core_files() -> None:
    package = _read(PACKAGE_PATH)
    expected_paths = {
        f"contracts/phase-3/{STEM}-research-sources.json": SOURCES_PATH,
        f"contracts/phase-3/{STEM}-decision-packet.json": DECISIONS_PATH,
        f"contracts/phase-3/{STEM}-proposal.json": PROPOSAL_PATH,
        f"docs/phase-3/{STEM}-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["recommended_selection"] == "A/A/A/A/A/A"


def test_all_six_decisions_are_unselected_A_through_D_choices() -> None:
    packet = _read(DECISIONS_PATH)
    decisions = packet["decisions"]

    assert [item["decision_id"] for item in decisions] == [
        f"D-P3.6-U3F-{index:03d}" for index in range(1, 7)
    ]
    for decision in decisions:
        assert decision["recommended_option"] == "A"
        assert decision["selected_option"] is None
        assert [option["option"] for option in decision["options"]] == [
            "A",
            "B",
            "C",
            "D",
        ]


def test_recommended_effect_is_bounded_and_non_executable() -> None:
    packet = _read(DECISIONS_PATH)
    effect = packet["effect_if_recommended_AAAAAA_is_later_accepted"]

    assert effect["secure_root_policy"] == "protected_security_at_create_DACL"
    assert effect["existing_root_policy"] == "absent_root_required"
    assert effect["Defender_binding_policy"] == (
        "exact_version_path_SHA256_cache_only_WinVerifyTrust"
    )
    assert effect["ModelScan_policy"] == (
        "separate_pinned_bootstrap_and_hostile_fixture_validation"
    )
    assert effect["retry_scope"] == "storage_remediation_and_Defender_binding_only"
    for field in [
        "immediate_attempt_authority",
        "immediate_F_or_ACL_authority",
        "immediate_scanner_query_or_execution_authority",
        "immediate_install_download_or_artifact_authority",
        "immediate_implementation_authority",
    ]:
        assert effect[field] is False


def test_research_used_only_primary_sources_and_performed_zero_actions() -> None:
    sources = _read(SOURCES_PATH)

    assert sources["status"] == "primary_source_research_complete_planning_only"
    assert len(sources["primary_sources"]) == 9
    assert {item["publisher"] for item in sources["primary_sources"]} == {
        "Microsoft Learn",
        "Protect AI",
        "Protect AI GitHub issue tracker",
        "Python Package Index",
    }
    assert all(count == 0 for count in sources["research_actions"].values())
    assert all(
        authority is False for authority in sources["current_authority"].values()
    )


def test_consumed_U3E_evidence_and_failure_facts_are_preserved() -> None:
    sources = _read(SOURCES_PATH)
    attempt = sources["consumed_attempt"]
    observations = sources["bounded_observations"]

    assert attempt["package_digest_sha256"] == U3E_PACKAGE_DIGEST
    assert attempt["authorization_sha256"] == U3E_AUTHORIZATION_SHA256
    assert attempt["result_sha256"] == U3E_RESULT_SHA256
    assert attempt["evidence_sha256"] == U3E_EVIDENCE_SHA256
    assert attempt["attempt_consumed"] is True
    assert attempt["retry_authorized"] is False
    assert observations["volume_policy_passed"] is True
    assert observations["path_policy_passed"] is True
    assert observations["acl_policy_passed"] is False
    assert observations["acl_failure_code"] == "broad_write_principal_present"
    assert observations["atomic_probe_executed"] is False
    assert observations["probe_content_retained"] is False
    assert observations["candidate_root_retained"] is False
    assert observations["scanner_chain_ready"] is False


def test_proposal_and_manifest_grant_no_current_authority() -> None:
    proposal = _read(PROPOSAL_PATH)
    package = _read(PACKAGE_PATH)

    assert proposal["status"] == "owner_decisions_pending_non_effective"
    assert proposal["current_effect"]["owner_selections_pending"] is True
    assert proposal["current_effect"]["new_action_spec_exists"] is False
    assert proposal["current_effect"]["new_authorization_package_exists"] is False
    assert package["effect_of_owner_selections"] == (
        "authorize_only_preparation_of_a_new_digest_bound_one_attempt_action_and_"
        "authorization_package"
    )
    assert package["owner_selection_may_be_inferred_from_continue_or_prior_authorization"] is False
    assert package["current_effect"]["owner_selections_pending"] is True
    for field, value in package["current_effect"].items():
        if field != "owner_selections_pending":
            assert value is False


def test_canonical_ledgers_record_U3E_and_U3G_consumed_and_U3F_accepted() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]

    for ledger in ledgers:
        consumed = ledger["quarantine_scanner_binding_r0_authorization_package"]
        accepted = ledger["quarantine_remediation_r1_decision_package"]
        U3G_consumed = ledger["quarantine_remediation_r1_authorization_package"]
        consumed_digest = consumed.get(
            "digest_sha256", consumed.get("package_digest_sha256")
        )
        accepted_digest = accepted.get(
            "digest_sha256", accepted.get("package_digest_sha256")
        )
        U3G_digest = U3G_consumed.get(
            "digest_sha256", U3G_consumed.get("package_digest_sha256")
        )
        assert consumed_digest == U3E_PACKAGE_DIGEST
        assert consumed["attempt_consumed"] is True
        assert consumed["retry_authorized"] is False
        assert accepted_digest == PACKAGE_DIGEST
        assert accepted["selected_options"] == "A/A/A/A/A/A"
        assert accepted["owner_selections_pending"] is False
        assert accepted["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert U3G_digest == U3G_PACKAGE_DIGEST
        assert U3G_consumed["owner_authorization_pending"] is False
        assert U3G_consumed["attempt_consumed"] is True
        assert U3G_consumed["retry_authorized"] is False
        assert U3G_consumed["another_attempt_authorized"] is False
        assert U3G_consumed["F_or_ACL_action_authorized"] is False
        assert U3G_consumed["Defender_query_hash_or_WinVerifyTrust_authorized"] is False
        assert U3G_consumed["scanner_install_update_or_execution_authorized"] is False
        assert U3G_consumed["artifact_or_dependency_acquisition_authorized"] is False
        assert U3G_consumed["profile_activation_authorized"] is False


def test_entry_gates_remain_blocked_after_non_effective_package() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert states["P36-G1"] == "blocked"
    assert states["P36-G2"] == "blocked"
    assert states["P36-G4"] == "blocked"
    assert states["P36-G5"] == "blocked"
    assert gates["implementation_authorized"] is False
    assert gates["runtime_execution_authorized"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    plan = (DOCS / "p3-6-plan.md").read_text(encoding="utf-8")
    planning_acceptances = (DOCS / "p3-6-planning-acceptances.md").read_text(
        encoding="utf-8"
    )
    unblock = (DOCS / "p3-6-unblock-plan.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    for text in [
        decision_register,
        backlog,
        phase_index,
        plan,
        planning_acceptances,
        unblock,
    ]:
        assert PACKAGE_DIGEST in text
    assert "DR-0062" in decision_register
    assert "DR-0063" in decision_register
    assert "DR-0064" in decision_register
    assert "D-P3.6-U3F-001" in backlog
    assert "consumed U3G authorization" in backlog
    assert f"{STEM}-decision-package.json" in contracts_index
