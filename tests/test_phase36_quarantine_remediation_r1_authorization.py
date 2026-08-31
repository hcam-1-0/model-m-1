from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-quarantine-remediation-r1"
ACCEPTANCE_PATH = CONTRACTS / f"{STEM}-owner-decisions.json"
ACTION_SPEC_PATH = CONTRACTS / f"{STEM}-action-spec.json"
PROPOSAL_PATH = CONTRACTS / f"{STEM}-authorization-proposal.json"
DOCUMENT_PATH = DOCS / f"{STEM}-authorization-proposal.md"
PACKAGE_PATH = CONTRACTS / f"{STEM}-authorization-package.json"
DECISION_PACKAGE_DIGEST = (
    "9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78"
)
ACCEPTANCE_DIGEST = (
    "BDA7E9C6B8ACF4ECB8641B61F47A45E4E02768B58C7E3A08179507B7ABAFDF1F"
)
ACTION_SPEC_DIGEST = (
    "31179542F3C0729895BB40FF766FAF1F7AECE9E9080821742BE45ACF60F10F77"
)
PROPOSAL_DIGEST = (
    "C72D3278D413208DE104BB15A6AC3988F42ABA934C4F196CAD38DB8C5DB4E2EC"
)
DOCUMENT_DIGEST = (
    "54D9860666A61601F80BD8ADD54F90CBF8305359930A78C53B42D4D6C6C7EBCE"
)
PACKAGE_DIGEST = "C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_U3F_acceptance_is_exact_non_effective_and_separate() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["package_digest_sha256"] == DECISION_PACKAGE_DIGEST
    assert acceptance["owner_statement_received"] == "\n".join(
        f"D-P3.6-U3F-{index:03d}: A" for index in range(1, 7)
    )
    assert [item["selected_option"] for item in acceptance["selections"]] == [
        "A"
    ] * 6
    assert acceptance["accepted_effect"][
        "new_digest_bound_authorization_package_preparation_authorized"
    ] is True
    assert acceptance["accepted_effect"]["another_attempt_authorized"] is False
    for field in [
        "another_attempt_authorized",
        "F_or_ACL_action_authorized",
        "Defender_query_hash_or_trust_verification_authorized",
        "scanner_query_install_or_execution_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert acceptance[field] is False


def test_package_binds_exact_four_core_files() -> None:
    package = _read(PACKAGE_PATH)
    expected = {
        f"contracts/phase-3/{STEM}-owner-decisions.json": ACCEPTANCE_DIGEST,
        f"contracts/phase-3/{STEM}-action-spec.json": ACTION_SPEC_DIGEST,
        f"contracts/phase-3/{STEM}-authorization-proposal.json": PROPOSAL_DIGEST,
        f"docs/phase-3/{STEM}-authorization-proposal.md": DOCUMENT_DIGEST,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == expected
    for path, digest in expected.items():
        assert _sha256(ROOT / path) == digest
    assert package["owner_decision_id"] == "D-P3.6-U3G-BINDING-R1-AUTH"


def test_target_and_transaction_are_one_attempt_exact_and_offline() -> None:
    spec = _read(ACTION_SPEC_PATH)
    target = spec["target"]
    bounds = spec["transaction_bounds"]

    assert target["candidate_volume"] == "F:"
    assert target["candidate_root"] == "F:\\HCAM-Quarantine"
    assert target["excluded_existing_project_root"] == "F:\\h cam"
    assert target["owner_prohibited_volume"] == "B:"
    assert target["required_initial_candidate_state"] == "absent"
    assert target["remote_or_alternate_target_allowed"] is False
    assert bounds["maximum_authorized_attempts"] == 1
    assert bounds["authorization_use_window_seconds_after_owner_acceptance"] == 86400
    assert bounds["storage_attestation_validity_seconds_after_success"] == 3600
    assert bounds["maximum_probe_bytes"] == 4096
    assert bounds["maximum_Defender_candidate_bytes"] == 128 * 1024**2
    assert bounds["maximum_direct_Defender_platform_directories"] == 64
    assert bounds["network_access"] is False
    assert bounds["automatic_retry"] is False


def test_DACL_policy_is_security_at_create_and_exact() -> None:
    policy = _read(ACTION_SPEC_PATH)["platform_and_identity_policy"]
    rules = policy["required_explicit_allow_rules"]

    assert policy["security_at_create_API"] == (
        "System.IO.FileSystemAclExtensions.CreateDirectory(DirectorySecurity,String)"
    )
    assert policy["ACL_protection_call"] == "SetAccessRuleProtection(true,false)"
    assert policy["current_process_identity_source"] == (
        "WindowsIdentity.GetCurrent().User"
    )
    assert policy["current_process_identity_persisted"] is False
    assert policy["account_name_translation_allowed"] is False
    assert [(item["principal"], item["rights"]) for item in rules] == [
        ("ephemeral_current_process_SID", "Modify"),
        ("S-1-5-18", "FullControl"),
        ("S-1-5-32-544", "FullControl"),
    ]
    assert all(
        item["inheritance"] == "ContainerInherit,ObjectInherit" for item in rules
    )
    assert policy["inherited_rules_allowed"] is False
    assert policy["deny_rules_allowed"] is False
    assert policy["additional_explicit_rules_allowed"] is False
    assert policy["fallback_create_then_rewrite_allowed"] is False


def test_actions_are_ordered_and_authorization_precedes_machine_access() -> None:
    actions = _read(ACTION_SPEC_PATH)["action_allowlist"]
    expected_suffixes = [
        "UTC-CLOCK-START",
        "PACKAGE-VERIFY",
        "AUTHORIZATION-RECORD",
        "F-DRIVE-INFO",
        "CANONICAL-PATH-AND-ABSENCE",
        "PROTECTED-DACL-CONSTRUCT",
        "SECURITY-AT-CREATE-ROOT",
        "EXACT-DACL-VERIFY",
        "ATOMIC-CAPABILITY-PROBE",
        "DEFENDER-STATUS-METADATA",
        "DEFENDER-BINARY-CANDIDATE",
        "DEFENDER-CACHE-ONLY-WINVERIFYTRUST",
        "NORMALIZE-HASH-WRITE",
    ]

    assert [item["action_id"] for item in actions] == [
        f"U3G-A{index:02d}-{suffix}"
        for index, suffix in enumerate(expected_suffixes, start=1)
    ]
    assert actions[2]["output_path"] == (
        "contracts/phase-3/p3-6-quarantine-remediation-r1-authorization.json"
    )
    assert actions[2]["failure_effect"] == "abort_before_F_or_Defender_access"


def test_absence_creation_verification_and_probe_are_fail_closed() -> None:
    actions = {
        item["action_id"]: item
        for item in _read(ACTION_SPEC_PATH)["action_allowlist"]
    }
    absence = actions["U3G-A05-CANONICAL-PATH-AND-ABSENCE"]
    create = actions["U3G-A07-SECURITY-AT-CREATE-ROOT"]
    verify = actions["U3G-A08-EXACT-DACL-VERIFY"]
    probe = actions["U3G-A09-ATOMIC-CAPABILITY-PROBE"]

    assert absence["existing_object_effect"] == (
        "fail_closed_without_ACL_or_content_modification"
    )
    assert create["existing_target"] == "fail_closed_without_modification"
    assert create["other_directory_creation_allowed"] is False
    assert "exactly_three_explicit_allow_ACE" in verify["exact_action"]
    assert verify["identity_names_SIDs_raw_ACL_or_security_descriptor_persisted"] is False
    assert probe["probe_bytes"] == 4096
    assert probe["probe_or_content_retention"] == (
        "zero_after_success_or_bounded_failure_cleanup"
    )
    assert probe["other_file_or_directory_access_allowed"] is False


def test_Defender_binding_is_bounded_hash_only_and_cache_only_trust() -> None:
    actions = {
        item["action_id"]: item
        for item in _read(ACTION_SPEC_PATH)["action_allowlist"]
    }
    status = actions["U3G-A10-DEFENDER-STATUS-METADATA"]
    candidate = actions["U3G-A11-DEFENDER-BINARY-CANDIDATE"]
    trust = actions["U3G-A12-DEFENDER-CACHE-ONLY-WINVERIFYTRUST"]

    assert status["scan_or_remediation_allowed"] is False
    assert status["signature_or_platform_update_allowed"] is False
    assert candidate["recursive_enumeration"] is False
    assert candidate["ProgramFiles_fallback_allowed"] is False
    assert candidate["multiple_or_no_matching_candidates"] == "fail_closed"
    assert candidate["executable_invocation_allowed"] is False
    for token in [
        "WINTRUST_ACTION_GENERIC_VERIFY_V2",
        "WTD_UI_NONE",
        "WTD_REVOKE_WHOLECHAIN",
        "WTD_CHOICE_FILE",
        "WTD_STATEACTION_VERIFY",
        "WTD_CACHE_ONLY_URL_RETRIEVAL",
        "WTD_STATEACTION_CLOSE",
        "ERROR_SUCCESS",
    ]:
        assert token in trust["exact_action"]
    assert trust["network_retrieval_allowed"] is False
    assert trust["UI_allowed"] is False
    assert trust["executable_invocation_allowed"] is False
    assert trust["cached_chain_or_revocation_unavailable"] == "fail_closed"


def test_ModelScan_and_runtime_remain_outside_the_attempt() -> None:
    spec = _read(ACTION_SPEC_PATH)
    result = spec["result_policy"]
    prohibited = spec["continuing_non_authorization"]

    assert result["ModelScan_state"] == (
        "deferred_to_separate_pinned_bootstrap_package"
    )
    assert result["passive_inspector_state"] == (
        "not_implemented_not_bound_not_executed"
    )
    assert result["scanner_chain_ready"] is False
    assert result["artifact_acquisition_authorized"] is False
    assert "ModelScan_query_install_import_execution_or_hostile_fixture_bootstrap" in prohibited
    assert "artifact_acquisition_checkpoint_load_unpickle_import_conversion_or_export" in prohibited
    assert "inference_calibration_validation_benchmark_or_hardware_test" in prohibited


def test_proposal_and_manifest_grant_no_current_action() -> None:
    proposal = _read(PROPOSAL_PATH)
    package = _read(PACKAGE_PATH)

    assert proposal["status"] == "owner_review_pending_non_effective"
    assert proposal["decision_id"] == "D-P3.6-U3G-BINDING-R1-AUTH"
    assert proposal["current_effect"]["effective"] is False
    assert package["status"] == "sealed_non_effective_owner_authorization_pending"
    assert package["owner_acceptance_may_be_inferred_from_continue_prior_U3E_authority_or_U3F_selections"] is False
    for field in [
        "storage_or_hardware_query_authorized",
        "storage_directory_creation_ACL_write_probe_or_cleanup_authorized",
        "Defender_query_hash_or_WinVerifyTrust_authorized",
        "scanner_install_update_or_execution_authorized",
        "ModelScan_bootstrap_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert package[field] is False


def test_canonical_ledgers_point_to_exact_pending_U3G_package() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]

    for ledger in ledgers:
        accepted = ledger["quarantine_remediation_r1_decision_package"]
        pending = ledger["quarantine_remediation_r1_authorization_package"]
        accepted_hash = accepted.get(
            "acceptance_sha256", accepted.get("accepted_policy_sha256")
        )
        pending_digest = pending.get(
            "digest_sha256", pending.get("package_digest_sha256")
        )
        assert accepted["selected_options"] == "A/A/A/A/A/A"
        assert accepted["owner_selections_pending"] is False
        assert accepted_hash == ACCEPTANCE_DIGEST
        assert pending_digest == PACKAGE_DIGEST
        assert pending["decision_id"] == "D-P3.6-U3G-BINDING-R1-AUTH"
        assert pending["owner_authorization_pending"] is True
        assert pending["another_attempt_authorized"] is False
        assert pending["F_or_ACL_action_authorized"] is False
        assert pending["Defender_query_hash_or_WinVerifyTrust_authorized"] is False
        assert pending["artifact_or_dependency_acquisition_authorized"] is False
        assert pending["profile_activation_authorized"] is False

    action = ledgers[2]["next_portable_planning_action"]
    assert action["decision_id"] == "D-P3.6-U3G-BINDING-R1-AUTH"
    assert action["package_digest_sha256"] == PACKAGE_DIGEST
    assert action["owner_authorization_pending"] is True
    assert action["another_attempt_authority"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    paths = [
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ]

    for path in paths:
        assert PACKAGE_DIGEST in path.read_text(encoding="utf-8")
    decision_register = (DOCS / "decision-register.md").read_text(
        encoding="utf-8"
    )
    assert "DR-0063" in decision_register
    assert "D-P3.6-U3G-BINDING-R1-AUTH" in decision_register
    assert f"{STEM}-authorization-package.json" in (
        CONTRACTS / "README.md"
    ).read_text(encoding="utf-8")
