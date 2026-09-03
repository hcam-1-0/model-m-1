from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

RESEARCH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-bootstrap-"
    "remediation-research-sources.json"
)
ANALYSIS = CONTRACTS / "p3-6-quarantine-generated-validation-failure-analysis-r1.json"
REMEDIATION = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-bootstrap-"
    "remediation-contract.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-bootstrap-remediation-"
    "implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-bootstrap-remediation-"
    "implementation-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-harness-r2-bootstrap-"
    "remediation-authorization-proposal.md"
)

DECISION = (
    "D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-"
    "IMPLEMENTATION-AUTH"
)
PACKAGE_DIGEST = (
    "5EC2889439E81B9F955FE7C3864A0931466458EAFA77C5797E44B24DC9AB0B47"
)
U3P_RESULT_DIGEST = (
    "44450DF4D5A199DA34E5343AE043E138B8E046EF4E6FE6EAD6836AC96F7085F4"
)
U3P_EVIDENCE_DIGEST = (
    "634674D4C50BB63AAF1A73FFEABB804AC51439002787542E76EB66627A9AD3DE"
)
IMMUTABLE = {
    "tools/phase36_quarantine_generated_validation.ps1": (
        "F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3"
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


def test_consumed_U3P_failure_is_bound_without_raw_diagnostics() -> None:
    research = _read(RESEARCH)
    analysis = _read(ANALYSIS)

    observed = research["repository_observations"]
    assert observed["failed_U3P_result_sha256"] == U3P_RESULT_DIGEST
    assert observed["failed_U3P_evidence_sha256"] == U3P_EVIDENCE_DIGEST
    assert observed["attempt_stdout_bytes"] == 0
    assert observed["raw_stderr_inspected_or_retained"] is False
    facts = analysis["confirmed_facts"]
    assert facts["sanitized_reason_code"] == "result_contract_invalid"
    assert facts["all_five_source_hashes_matched_before_and_after"] is True
    assert analysis["attempt_evidence"]["retry_authorized"] is False
    assert facts["U3K_authorized"] is False


def test_R2_contract_is_exact_path_allowlisted_and_fail_closed() -> None:
    contract = _read(REMEDIATION)
    source = contract["exact_source_remediation"]

    assert source["new_contract_version"].endswith("R2-1.2.0")
    assert source["exact_Utility_cmdlet_allowlist"] == [
        "Compare-Object",
        "ConvertFrom-Json",
        "ConvertTo-Json",
        "ForEach-Object",
        "Measure-Object",
        "Sort-Object",
        "Where-Object",
    ]
    path_policy = source["module_path_policy"]
    assert path_policy["root"] == "$PSHOME\\Modules"
    assert path_policy["fully_qualified_path_required"] is True
    assert path_policy["module_name_resolution"] is False
    assert path_policy["PSModulePath_read_or_search"] is False
    assert source["import_policy"]["Scope"] == "Local"
    assert source["import_policy"]["NoClobber"] is True
    assert source["bootstrap_failure_contract"][
        "uses_only_language_primitives_System_Console_and_a_fixed_ASCII_JSON_literal"
    ] is True
    assert contract["future_runtime_binding_prerequisites"][
        "exact_runtime_module_manifest_and_nested_implementation_closure_binding"
    ] is True


def test_package_is_complete_non_effective_and_hash_bound() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 13
    for item in package["core_files"]:
        if item["path"] != "tools/phase36_quarantine_generated_validation.ps1":
            assert _sha256(ROOT / item["path"]) == item["sha256"]
    historical = {item["path"]: item["sha256"] for item in package["core_files"]}
    assert historical["tools/phase36_quarantine_generated_validation.ps1"] == (
        "F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3"
    )
    gate = package["current_gate_effect"]
    assert gate["owner_U3Q_authorization_pending"] is True
    assert gate[
        "D_P3_6_U3Q_VALIDATION_HARNESS_R2_BOOTSTRAP_REMEDIATION_"
        "IMPLEMENTATION_AUTH_requestable"
    ] is True
    assert gate["implementation_authorized"] is False
    assert gate["PowerShell_parser_import_or_execution_authorized"] is False
    assert gate["retry_or_U3R_package_preparation_authorized"] is False
    assert gate["U3K_authorized"] is False
    assert package[
        "authorization_may_be_inferred_from_continue_planning_or_prior_U3P_authorization"
    ] is False


def test_proposal_requests_only_source_and_generated_static_authority() -> None:
    proposal = _read(PROPOSAL)

    assert proposal["decision_id"] == DECISION
    requested = proposal["requested_authority"]
    assert requested["source_only_harness_R2_remediation"] is True
    assert requested["generated_static_Python_tests"] is True
    assert requested["PowerShell_parse_import_or_execution"] is False
    assert requested["runtime_or_hardware_observation"] is False
    assert requested["runtime_retry_or_U3R_package_preparation"] is False
    statement = proposal["owner_authorization_statement_template"]
    assert statement.startswith(f"{DECISION}:")
    assert "<U3Q_R2_BOOTSTRAP_REMEDIATION_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in statement


def test_accepted_sources_remain_byte_exact() -> None:
    for path, digest in IMMUTABLE.items():
        if path != "tools/phase36_quarantine_generated_validation.ps1":
            assert _sha256(ROOT / path) == digest
    source = (ROOT / "tools/phase36_quarantine_generated_validation.ps1").read_text(
        encoding="utf-8"
    )
    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R2-1.2.0" in source
    assert _sha256(
        ROOT / "tools/phase36_quarantine_generated_validation.ps1"
    ) != IMMUTABLE["tools/phase36_quarantine_generated_validation.ps1"]


def test_canonical_ledgers_and_docs_are_synchronized() -> None:
    key = (
        "quarantine_generated_validation_harness_r2_bootstrap_remediation_"
        "implementation_authorization_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        state = ledger[key]
        assert state["package_digest_sha256"] == PACKAGE_DIGEST
        assert state["owner_decision_id"] == DECISION
        assert state["owner_U3Q_authorization_pending"] is False
        assert state["implementation_authorized"] is False
        assert state["implementation_authority_consumed"] is True
        assert state["source_only_implementation_complete"] is True
        assert state["owner_implementation_acceptance_pending"] is True
        assert state["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

    for path in (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
        REVIEW,
    ):
        text = path.read_text(encoding="utf-8")
        assert DECISION in text
        if path != REVIEW:
            assert PACKAGE_DIGEST in text


def test_line_endings_are_explicit() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (RESEARCH, ANALYSIS, REMEDIATION, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        assert f"{path.name} text eol=lf" in attributes
