from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-"
    "acceptance.json"
)
ACTION_SPEC_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-action-spec.json"
)
PROPOSAL_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-"
    "proposal.json"
)
PACKAGE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-"
    "package.json"
)
REVIEW_PATH = (
    DOCS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-"
    "proposal.md"
)
AUTHORIZATION_RECORD_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization.json"
)
RESULT_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-result.json"
)
EVIDENCE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-evidence.json"
)

U3M_PACKAGE_DIGEST = (
    "D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A"
)
U3M_ACCEPTANCE_DIGEST = (
    "25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9"
)
ACTION_SPEC_DIGEST = (
    "BFC7E76431B6532871F6FB65DF8F1F6C1A3FBC243222FE173A4F7F71EEE86702"
)
PROPOSAL_DIGEST = (
    "E9660710FB28910F2ACD61C1BA0EF2EE8F206D16B822E81E67B3608644A3DD87"
)
REVIEW_DIGEST = (
    "6F57E303F05581ECEF216129732C2A08A2021ADACC6E3493FDD6DA5748BCC090"
)
PACKAGE_DIGEST = (
    "E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E"
)
AUTHORIZATION_RECORD_DIGEST = (
    "1218C1C35C58AB253D811044046F2EDD364790A6469150248BFFBAB37AAE395B"
)
RESULT_DIGEST = (
    "AD3A8B62105C4DF85E613024C034CECB8DB66C583E7DB49BDA1D4EB09772A8F7"
)
EVIDENCE_DIGEST = (
    "0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42"
)
OWNER_STATEMENT_DIGEST = (
    "A21ECA40C3DB1558FDEE04A8E53ADF3C73010C51EBE7E109B45296B995DE97DE"
)
U3M_DECISION = "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE"
U3N_DECISION = "D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH"
OWNER_STATEMENT = (
    "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE: I, "
    "mayank-admin, accept the P3.6 U3M generated validation harness R0 "
    "implementation package digest "
    "D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A, "
    "including exact harness SHA-256 "
    "48FC33E1928BA186C11005DBDEC055E5558D58677D51EB864D3740BCFBA208C1, "
    "vector-manifest SHA-256 "
    "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C, "
    "Python-test SHA-256 "
    "E177E6B45D2C9F1E527EA888C0621DCEAAC079F0909178D3D1C9FFA96B6263DB, "
    "accepted byte-exact runner, pure-handler, and Windows-adapter sources, "
    "generated/static evidence, and documented limitations. This accepts "
    "source and generated/static evidence only and authorizes preparation only "
    "of a separate non-effective U3N generated-validation and fresh-runtime-"
    "binding authorization package. It does not authorize PowerShell parsing, "
    "import, or execution; runner or module execution; runtime or hardware "
    "observation; machine, storage, F:, ACL, probe, cleanup, or scanner action; "
    "network, download, artifact, model, inference, camera/media/data, "
    "container/Kubernetes, deployment, or remote Git. Any validation attempt "
    "requires a later current digest-bound "
    "D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH."
)

ACCEPTED_HASHES = {
    "tools/phase36_quarantine_generated_validation.ps1": (
        "48FC33E1928BA186C11005DBDEC055E5558D58677D51EB864D3740BCFBA208C1"
    ),
    "contracts/phase-3/"
    "p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
        "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
    ),
    "tools/phase36_quarantine_transaction_runner.ps1": (
        "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
    ),
    "tools/phase36_quarantine_machine_handlers.psm1": (
        "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
    ),
    "tools/phase36_quarantine_windows_storage_adapter.psm1": (
        "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
    ),
}


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, object]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_U3M_acceptance_is_recorded_and_hash_bound() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(ACCEPTANCE_PATH) == U3M_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == U3M_DECISION
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["owner_statement"] == OWNER_STATEMENT
    assert len(OWNER_STATEMENT.encode()) == 1233
    assert hashlib.sha256(OWNER_STATEMENT.encode()).hexdigest().upper() == (
        OWNER_STATEMENT_DIGEST
    )
    assert acceptance["owner_statement_sha256"] == OWNER_STATEMENT_DIGEST
    assert acceptance["accepted_package"]["sha256"] == U3M_PACKAGE_DIGEST
    assert acceptance["accepted_package"]["accepted_commit"] == (
        "ef75ef019c27cfb7efe1f5ebe8fd9d055c445284"
    )


def test_U3M_acceptance_allows_package_preparation_only() -> None:
    effect = _read(ACCEPTANCE_PATH)["accepted_effect"]

    assert effect["harness_source_accepted"] is True
    assert effect["generated_vector_manifest_accepted"] is True
    assert effect[
        "separate_non_effective_U3N_authorization_package_preparation_authorized"
    ] is True
    for field in (
        "source_or_test_change_authorized",
        "PowerShell_parser_import_or_execution_authorized",
        "runner_or_module_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "machine_storage_F_ACL_probe_cleanup_or_scanner_action_authorized",
        "network_download_artifact_model_media_or_data_action_authorized",
        "container_Kubernetes_deployment_or_remote_git_authorized",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
    ):
        assert effect[field] is False


def test_action_spec_is_exact_single_use_and_seven_step() -> None:
    spec = _read(ACTION_SPEC_PATH)
    actions = spec["exact_action_sequence"]

    assert _sha256(ACTION_SPEC_PATH) == ACTION_SPEC_DIGEST
    assert spec["maximum_attempts"] == 1
    assert spec["authorization_window_seconds"] == 86400
    assert spec["failed_attempt_consumes_authorization"] is True
    assert spec["automatic_retry"] is False
    assert spec["parallel_processes"] is False
    assert [item["action_id"] for item in actions] == [
        "U3N-A01-PACKAGE-AUTHORITY-PREFLIGHT",
        "U3N-A02-AUTHORIZATION-RECORD",
        "U3N-A03-RUNTIME-PATH-CLASSIFY",
        "U3N-A04-RUNTIME-BIND",
        "U3N-A05-SOURCE-BINDINGS-PREFLIGHT",
        "U3N-A06-GENERATED-VALIDATION",
        "U3N-A07-POSTEXECUTION-BINDING-AND-EVIDENCE",
    ]
    assert actions[5]["runner_mode"] == "Contract_only"
    assert actions[5]["windows_adapter_role"].startswith("Parser_ParseFile_only")


def test_action_spec_binds_exact_runtime_sources_vectors_and_outputs() -> None:
    spec = _read(ACTION_SPEC_PATH)
    bindings = {item["path"]: item["sha256"] for item in spec["exact_accepted_inputs"]}

    assert spec["exact_runtime_candidate"]["path"] == (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    )
    assert spec["exact_runtime_candidate"]["alternate_discovery"] is False
    assert bindings == ACCEPTED_HASHES
    assert spec["validation_expectations"]["parser_file_count"] == 4
    assert spec["validation_expectations"][
        "contract_vectors_required_and_passed"
    ] == 20
    assert spec["validation_expectations"][
        "pure_handler_vectors_required_and_passed"
    ] == 64
    assert spec["validation_expectations"][
        "total_generated_vectors_required_and_passed"
    ] == 84
    assert len(spec["exact_future_outputs"]) == 3


def test_action_spec_preserves_process_and_prohibition_bounds() -> None:
    spec = _read(ACTION_SPEC_PATH)
    bounds = spec["process_and_resource_bounds"]
    prohibitions = set(spec["hard_prohibitions"])

    assert bounds["total_attempt_timeout_seconds"] == 300
    assert bounds["UseShellExecute"] is False
    assert bounds["RedirectStandardOutput"] is True
    assert bounds["RedirectStandardError"] is True
    assert bounds["interactive_input"] is False
    assert bounds["raw_stdout_or_stderr_persisted"] is False
    assert "runner_Storage_mode_or_StorageRequestJson" in prohibitions
    assert "windows_adapter_import_or_execution" in prohibitions
    assert any("machine_storage_F_B_ACL" in item for item in prohibitions)
    assert any("remote_Git" in item for item in prohibitions)


def test_proposal_is_non_effective_and_requires_exact_owner_authorization() -> None:
    proposal = _read(PROPOSAL_PATH)

    assert _sha256(PROPOSAL_PATH) == PROPOSAL_DIGEST
    assert proposal["decision_id"] == U3N_DECISION
    assert proposal["preparation_authority"]["acceptance_record_sha256"] == (
        U3M_ACCEPTANCE_DIGEST
    )
    assert proposal["future_authorization"]["authorization_pending"] is True
    assert proposal["future_authorization"]["authorization_is_single_use"] is True
    assert proposal["owner_authorization_statement_template"].startswith(
        f"{U3N_DECISION}:"
    )
    assert "<U3N_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "owner_authorization_statement_template"
    ]
    assert proposal["current_effect"]["runtime_observation_authorized"] is False
    assert proposal["current_effect"][
        "PowerShell_parser_import_or_execution_authorized"
    ] is False


def test_authorization_package_is_exact_non_effective_and_complete() -> None:
    package = _read(PACKAGE_PATH)

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["future_authorization_decision_id"] == U3N_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 12
    for item in package["core_files"]:
        if item["path"] != "tools/phase36_quarantine_generated_validation.ps1":
            assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["fixed_bindings"]["harness_mode"] == "Aggregate"
    assert package["fixed_bindings"]["runner_mode"] == "Contract_only"
    gate = package["current_gate_effect"]
    assert gate["owner_U3N_authorization_pending"] is True
    assert gate[
        "D_P3_6_U3N_GENERATED_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable"
    ] is True
    assert gate["runtime_observation_authorized"] is False
    assert gate["PowerShell_parser_import_or_execution_authorized"] is False
    assert gate["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_U3N_immutable_inputs_remain_exact_and_harness_binding_is_historical() -> None:
    for path, expected in ACCEPTED_HASHES.items():
        if path != "tools/phase36_quarantine_generated_validation.ps1":
            assert _sha256(ROOT / path) == expected
    assert ACCEPTED_HASHES["tools/phase36_quarantine_generated_validation.ps1"] == (
        "48FC33E1928BA186C11005DBDEC055E5558D58677D51EB864D3740BCFBA208C1"
    )


def test_single_attempt_outputs_are_sealed_failed_closed_and_consumed() -> None:
    spec = _read(ACTION_SPEC_PATH)

    assert [ROOT / path for path in spec["exact_future_outputs"]] == [
        AUTHORIZATION_RECORD_PATH,
        RESULT_PATH,
        EVIDENCE_PATH,
    ]
    assert _sha256(AUTHORIZATION_RECORD_PATH) == AUTHORIZATION_RECORD_DIGEST
    assert _sha256(RESULT_PATH) == RESULT_DIGEST
    assert _sha256(EVIDENCE_PATH) == EVIDENCE_DIGEST

    authorization = _read(AUTHORIZATION_RECORD_PATH)
    result = _read(RESULT_PATH)
    evidence = _read(EVIDENCE_PATH)

    assert authorization["effective_for_additional_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["status"] == "failed_attempt_consumed"
    assert result["authorization_consumed"] is True
    assert result["automatic_retry_authorized"] is False
    assert result["runtime_binding"]["reason_code"] == (
        "generated_validation_process_failed"
    )
    assert result["execution_and_access"][
        "outer_exact_pwsh_invocation_count"
    ] == 1
    assert result["accepted_source_bindings"][
        "all_five_match_before_execution"
    ] is True
    assert result["generated_validation"]["succeeded"] is False
    assert result["generated_validation"]["raw_process_output_retained"] is False
    assert result["generated_validation"]["raw_exception_retained"] is False
    assert all(
        count == 0
        for name, count in result["execution_and_access"].items()
        if name != "outer_exact_pwsh_invocation_count"
    )
    assert evidence["attempt_summary"]["attempts_consumed"] == 1
    assert evidence["attempt_summary"]["automatic_retry"] is False
    assert all(
        count == 0 for count in evidence["prohibited_action_counters"].values()
    )
    assert evidence["gate_effect"][
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable"
    ] is False


def test_canonical_ledgers_show_U3M_accepted_and_U3N_consumed() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        u3m = ledger[
            "quarantine_generated_validation_harness_r0_implementation_"
            "authorization_package"
        ]
        u3n = ledger[
            "quarantine_generated_validation_runtime_binding_r1_authorization_package"
        ]
        assert u3m["implementation_acceptance_sha256"] == U3M_ACCEPTANCE_DIGEST
        assert u3m["owner_implementation_acceptance_pending"] is False
        assert u3m["harness_source_and_generated_static_evidence_accepted"] is True
        assert u3n["package_digest_sha256"] == PACKAGE_DIGEST
        assert u3n["owner_decision_id"] == U3N_DECISION
        assert u3n["owner_U3N_authorization_pending"] is False
        assert u3n["authorization_record_sha256"] == AUTHORIZATION_RECORD_DIGEST
        assert u3n["result_sha256"] == RESULT_DIGEST
        assert u3n["evidence_sha256"] == EVIDENCE_DIGEST
        assert u3n["attempts_consumed"] == 1
        assert u3n["failed_attempt_consumed"] is True
        assert u3n["retry_authorized"] is False
        assert u3n[
            "D_P3_6_U3N_GENERATED_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable"
        ] is False
        assert u3n["runtime_observation_authorized"] is False
        assert u3n["PowerShell_parser_import_or_execution_authorized"] is False
        assert u3n["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_generated_validation_runtime_binding_action"
    ]
    assert action["decision_id"] == (
        "D-P3.6-U3P-GENERATED-VALIDATION-RUNTIME-BINDING-R2-AUTH"
    )
    assert action["failed_U3N_evidence_sha256"] == EVIDENCE_DIGEST
    assert action["owner_U3O_authorization_pending"] is False
    assert action["owner_implementation_acceptance_pending"] is False
    assert action["U3P_non_effective_package_preparation_authority"] is True
    assert action[
        "D_P3_6_U3P_GENERATED_VALIDATION_RUNTIME_BINDING_R2_AUTH_requestable"
    ] is False


def test_human_records_and_line_endings_are_synchronized() -> None:
    documents = [
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
    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert U3M_DECISION in text
        assert U3M_PACKAGE_DIGEST in text
        assert U3N_DECISION in text
        assert PACKAGE_DIGEST in text

    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert _sha256(REVIEW_PATH) == REVIEW_DIGEST
    assert "U3N Generated Validation and Runtime Binding R1" in review
    assert "sealed non-effective proposal" in review
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for name in (
        "p3-6-quarantine-generated-validation-harness-r0-implementation-acceptance.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-action-spec.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-proposal.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-package.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-proposal.md",
        "test_phase36_quarantine_generated_validation_runtime_binding_r1_authorization.py",
    ):
        assert f"{name} text eol=lf" in attributes
