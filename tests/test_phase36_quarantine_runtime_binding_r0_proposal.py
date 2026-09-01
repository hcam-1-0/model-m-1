from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-quarantine-transaction-runner-r0-runtime-binding"
IMPLEMENTATION_PACKAGE_DIGEST = (
    "71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67"
)
IMPLEMENTATION_ACCEPTANCE_DIGEST = (
    "70F2EE1133648F16CA6298C25FB6C46F56AA7C88FBA97553BDD0A2F55D90C63A"
)
SOURCES_DIGEST = (
    "FF2B121DBF42E5334782CFE4FE8C5A3425E27B980C22317BE8B8DE32203DD3F1"
)
ACTION_SPEC_DIGEST = (
    "E4081A71110502C9B617D3F5223A0C4CF6B3ABFDCED249A42C153EB000A45164"
)
PROPOSAL_DIGEST = (
    "5E12495D579F4B2DCBC1369D0DCB8AE7CD5F0D3CB37175E1F2F53D4FC451BBB3"
)
DOCUMENT_DIGEST = (
    "83A7801F678C53858BB51FC5B4AE15FEFE2917859FF813A26634CFAC2D33BB9F"
)
PACKAGE_DIGEST = (
    "37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9"
)
AUTHORIZATION_DIGEST = (
    "1C3144D82EA1B41B3FBBE7E70F5BF74ED5EE5ACC709CAB272E2CBD287253648F"
)
RESULT_DIGEST = (
    "643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7"
)
EVIDENCE_DIGEST = (
    "4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C"
)
RUNNER_SOURCE_DIGEST = (
    "C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15"
)
ACTION_IDS = [
    "U3I-RB-A01-UTC-CLOCK-START",
    "U3I-RB-A02-PACKAGE-AND-AUTHORITY-VERIFY",
    "U3I-RB-A03-AUTHORIZATION-RECORD",
    "U3I-RB-A04-EXACT-RUNTIME-PATH-CLASSIFY",
    "U3I-RB-A05-BOUNDED-METADATA-AND-SHA256",
    "U3I-RB-A06-CACHE-ONLY-WHOLE-CHAIN-TRUST",
    "U3I-RB-A07-RUNNER-SOURCE-BIND",
    "U3I-RB-A08-NORMALIZE-HASH-WRITE",
]


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_implementation_acceptance_is_recorded_without_execution() -> None:
    path = (
        CONTRACTS
        / "p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json"
    )
    acceptance = _read(path)

    assert _sha256(path) == IMPLEMENTATION_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == (
        "D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE"
    )
    assert acceptance["owner_statement_received"] == (
        "D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE"
    )
    assert acceptance["package_digest_sha256"] == IMPLEMENTATION_PACKAGE_DIGEST
    assert acceptance["accepted_evidence"]["runner_source_sha256"] == (
        RUNNER_SOURCE_DIGEST
    )
    assert acceptance["accepted_effect"][
        "runtime_binding_authorization_proposal_preparation_authorized"
    ] is True
    for field in [
        "runtime_binding_observation_authorized",
        "runner_execution_authorized",
        "machine_action_handler_implementation_authorized",
        "final_U3K_package_preparation_authorized",
        "storage_attempt_authorized",
        "F_or_ACL_action_authorized",
        "Defender_or_scanner_action_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert acceptance["accepted_effect"][field] is False


def test_runtime_binding_package_and_every_core_digest_are_exact() -> None:
    package_path = CONTRACTS / f"{STEM}-authorization-package.json"
    package = _read(package_path)
    expected = {
        "contracts/phase-3/p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json": IMPLEMENTATION_ACCEPTANCE_DIGEST,
        f"contracts/phase-3/{STEM}-research-sources.json": SOURCES_DIGEST,
        f"contracts/phase-3/{STEM}-action-spec.json": ACTION_SPEC_DIGEST,
        f"contracts/phase-3/{STEM}-authorization-proposal.json": PROPOSAL_DIGEST,
        f"docs/phase-3/{STEM}-authorization-proposal.md": DOCUMENT_DIGEST,
    }

    assert _sha256(package_path) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(expected)
    assert {
        item["path"]: item["sha256"] for item in package["core_files"]
    } == expected
    for path, digest in expected.items():
        assert _sha256(ROOT / path) == digest
    assert package["future_authorization_decision_id"] == (
        "D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH"
    )
    assert package["fixed_bindings"]["runtime_path"] == (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    )
    assert package["current_gate_effect"][
        "owner_runtime_binding_authorization_pending"
    ] is True
    assert package["current_gate_effect"][
        "runtime_binding_observation_authorized"
    ] is False


def test_action_spec_is_one_attempt_read_only_and_fail_closed() -> None:
    spec = _read(CONTRACTS / f"{STEM}-action-spec.json")

    assert [item["action_id"] for item in spec["action_allowlist"]] == ACTION_IDS
    assert spec["target"]["exact_runtime_path"] == (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    )
    assert spec["target"]["maximum_runtime_file_bytes"] == 268435456
    assert spec["target"]["alternate_runtime_path_allowed"] is False
    assert spec["transaction_bounds"]["maximum_authorized_attempts"] == 1
    assert spec["transaction_bounds"]["network_access"] is False
    assert spec["transaction_bounds"]["automatic_retry"] is False
    assert spec["runtime_binding_pass_policy"]["manual_override"] is False
    assert spec["runtime_binding_pass_policy"][
        "alternate_path_or_runtime_fallback"
    ] is False
    assert spec["runtime_binding_pass_policy"]["partial_binding_accepted"] is False
    assert spec["current_effect"]["owner_runtime_binding_authorization_pending"] is True
    for field in [
        "runtime_path_version_size_hash_or_trust_observation_authorized",
        "runner_execution_authorized",
        "final_U3K_package_preparation_authorized",
        "storage_attempt_authorized",
        "F_or_ACL_action_authorized",
        "Defender_or_scanner_action_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert spec["current_effect"][field] is False


def test_sealed_proposal_remains_non_effective_after_consumed_attempt() -> None:
    proposal = _read(CONTRACTS / f"{STEM}-authorization-proposal.json")
    package = _read(CONTRACTS / f"{STEM}-authorization-package.json")

    assert proposal["future_authorization"]["authorization_pending"] is True
    assert proposal["future_authorization"]["authorization_is_single_use"] is True
    assert proposal["future_authorization"]["automatic_retry"] is False
    assert proposal["success_effect_if_later_authorized_and_observed"][
        "runner_execution_authorized"
    ] is False
    assert proposal["success_effect_if_later_authorized_and_observed"][
        "final_U3K_package_preparation_authorized"
    ] is False
    assert all(value is False for value in proposal["hard_boundaries"].values())
    assert package["future_authorization_effect_if_exactly_accepted"][
        "runtime_or_runner_execution"
    ] is False

    for suffix in ["authorization", "result", "evidence"]:
        assert (CONTRACTS / f"{STEM}-{suffix}.json").is_file()


def test_research_ledger_uses_only_primary_microsoft_sources() -> None:
    ledger = _read(CONTRACTS / f"{STEM}-research-sources.json")

    assert len(ledger["sources"]) == 6
    for source in ledger["sources"]:
        assert source["publisher"] == "Microsoft"
        assert urlparse(source["url"]).hostname == "learn.microsoft.com"
    assert ledger["observed_machine_facts"] is False
    assert ledger["runtime_execution_authorized"] is False
    assert ledger["storage_or_F_access_authorized"] is False


def test_canonical_ledgers_and_human_records_point_to_new_gate() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]
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

    for ledger in ledgers:
        implementation = ledger[
            "quarantine_transaction_runner_r0_implementation_package"
        ]
        assert implementation["owner_implementation_acceptance_pending"] is False
        assert implementation["acceptance_sha256"] == (
            IMPLEMENTATION_ACCEPTANCE_DIGEST
        )
        runtime_binding = ledger[
            "quarantine_transaction_runner_r0_runtime_binding_authorization_package"
        ]
        assert runtime_binding["package_digest_sha256"] == PACKAGE_DIGEST
        assert runtime_binding["authorization_sha256"] == AUTHORIZATION_DIGEST
        assert runtime_binding["result_sha256"] == RESULT_DIGEST
        assert runtime_binding["evidence_sha256"] == EVIDENCE_DIGEST
        assert runtime_binding["owner_authorization_pending"] is False
        assert runtime_binding["runtime_binding_observation_completed"] is True
        assert runtime_binding["owner_evidence_acceptance_pending"] is False
        assert runtime_binding["final_U3K_package_preparation_authorized"] is True
        assert runtime_binding["runtime_binding_observation_authorized"] is False
        assert runtime_binding["runner_execution_authorized"] is False

    action = ledgers[2]["next_portable_planning_action"]
    assert action["decision_ids"] == [
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE"
    ]
    assert action["final_U3K_package_digest_sha256"] == (
        "4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E"
    )
    assert action["owner_runtime_binding_evidence_acceptance_pending"] is False
    assert action["owner_implementation_acceptance_pending"] is False
    assert action["runtime_binding_proposal_preparation_authority"] is True
    assert action["machine_handler_proposal_package_digest_sha256"] == (
        "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
    )
    assert action[
        "owner_machine_handler_implementation_authorization_pending"
    ] is False
    assert action["machine_handler_proposal_preparation_authority"] is False
    assert action["machine_handler_implementation_authority"] is False
    assert action["runtime_binding_observation_authority"] is False
    assert action["transaction_runner_execution_authority"] is False
    assert action["F_or_ACL_action_authority"] is False

    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert PACKAGE_DIGEST in text

    mutable_documents = [
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
        DOCS / f"{STEM}-evidence-review.md",
    ]
    for path in mutable_documents:
        text = path.read_text(encoding="utf-8")
        assert EVIDENCE_DIGEST in text
        assert "D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE" in text
    register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    assert "DR-0071" in register
    assert "DR-0072" in register
    assert "DR-0073" in register
