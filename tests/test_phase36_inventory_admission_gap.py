from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
GAP_PATH = CONTRACTS / "p3-6-inventory-admission-gap.json"
DECISIONS_PATH = CONTRACTS / "p3-6-inventory-admission-decision-packet.json"
SOURCES_PATH = CONTRACTS / "p3-6-inventory-admission-research-sources.json"
PACKAGE_PATH = CONTRACTS / "p3-6-inventory-admission-package.json"
DOCUMENT_PATH = DOCS / "p3-6-inventory-admission-gap.md"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_historical_inventory_is_preserved_but_not_admission_eligible() -> None:
    gap = _read(GAP_PATH)
    historical = gap["historical_inventory"]

    assert historical["sha256"] == (
        "0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F"
    )
    assert historical["preservation"] == "immutable_historical_record_do_not_overwrite"
    assert historical["shared_contract_conformance"] is False
    assert historical["admission_eligible"] is False


def test_gap_targets_exact_phase_minus_1_inventory_revision() -> None:
    gap = _read(GAP_PATH)
    target = gap["target_shared_contract"]

    assert target["revision"] == "d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8"
    assert target["schema_sha256"] == (
        "C9947BE12888C0A05B29DA0266E2359B107024AF07E536AE10BAC55457C5C7D3"
    )
    assert target["schema_version"] == (
        "hcam.platform.node-capability-inventory/v1alpha1"
    )
    assert gap["gap_count"] == len(gap["field_gaps"]) == 15


def test_missing_freshness_provenance_and_trust_are_explicit() -> None:
    gap = _read(GAP_PATH)
    targets = {item["target"]: item for item in gap["field_gaps"]}

    assert "valid_until_is_missing" in targets["observed_at_and_valid_until"]["r0_state"]
    assert "trust_level_and_collector_version_are_missing" in targets["provenance"][
        "r0_state"
    ]
    assert targets["trust_zone_binding"]["r0_state"].endswith(
        "not_a_field_of_the_shared_inventory_contract"
    )


def test_decision_packet_has_four_independent_a_to_d_choices() -> None:
    packet = _read(DECISIONS_PATH)

    assert packet["status"] == "owner_selection_pending_non_executable"
    assert packet["recommended_selection"] == "A/A/A/A"
    assert [item["decision_id"] for item in packet["decisions"]] == [
        "D-P3.6-U3A-001",
        "D-P3.6-U3A-002",
        "D-P3.6-U3A-003",
        "D-P3.6-U3A-004",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert [option["option"] for option in decision["options"]] == [
            "A",
            "B",
            "C",
            "D",
        ]


def test_recommended_policy_does_not_claim_external_mandate_or_authority() -> None:
    packet = _read(DECISIONS_PATH)
    result = packet["recommended_result_if_selected"]

    assert result["freshness"] == "maximum_24_hours_with_immediate_change_invalidation"
    assert result["provenance"] == "local_read_only_observed"
    assert result["current_R0_state"].endswith("already_stale_under_proposed_policy")
    assert packet["inventory_recollection_authorized"] is False
    assert packet["profile_activation_authorized"] is False
    assert packet["runtime_execution_authorized"] is False
    assert packet["remote_git_authorized"] is False


def test_research_uses_exact_local_and_official_sources_only() -> None:
    sources = _read(SOURCES_PATH)

    assert sources["remote_git_actions"] == 0
    assert sources["artifact_downloads"] == 0
    assert sources["runtime_executions"] == 0
    assert sources["hardware_queries_or_tests"] == 0
    assert len(sources["exact_local_sources"]) == 6
    assert len(sources["official_external_sources"]) == 2
    assert all(
        item["url"].startswith("https://csrc.nist.gov/")
        for item in sources["official_external_sources"]
    )


def test_package_binds_exact_core_files_and_no_executable_authority() -> None:
    package = _read(PACKAGE_PATH)
    expected = {
        "contracts/phase-3/p3-6-inventory-admission-research-sources.json": SOURCES_PATH,
        "contracts/phase-3/p3-6-inventory-admission-gap.json": GAP_PATH,
        "contracts/phase-3/p3-6-inventory-admission-decision-packet.json": DECISIONS_PATH,
        "docs/phase-3/p3-6-inventory-admission-gap.md": DOCUMENT_PATH,
    }
    recorded = {item["path"]: item["sha256"] for item in package["core_files"]}

    assert package["core_file_count"] == 4
    assert recorded == {path: _sha256(file_path) for path, file_path in expected.items()}
    assert package["inventory_recollection_authorized"] is False
    assert package["profile_activation_authorized"] is False
    assert package["runtime_execution_authorized"] is False
    assert package["implementation_authorized"] is False


def test_canonical_ledgers_keep_g2_blocked_and_link_exact_package() -> None:
    digest = "CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A"
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")

    assert gates["inventory_admission_gap_package"]["digest_sha256"] == digest
    assert next(
        gate for gate in gates["gates"] if gate["gate_id"] == "P36-G2"
    )["state"] == "blocked"
    assert policy["inventory_admission_gap"]["package_digest_sha256"] == digest
    assert policy["inventory_admission_gap"]["fresh_R1_required_before_admission"]
    assert unblock["inventory_admission_gap"]["package_digest_sha256"] == digest
    assert unblock["inventory_admission_gap"]["inventory_recollection_authorized"] is False


def test_gap_package_and_later_acceptance_are_both_indexed() -> None:
    phase_readme = (DOCS / "README.md").read_text(encoding="utf-8")
    contracts_readme = (CONTRACTS / "README.md").read_text(encoding="utf-8")
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")

    assert "p3-6-inventory-admission-gap.md" in phase_readme
    assert "p3-6-planning-acceptances.md" in phase_readme
    assert "p3-6-inventory-admission-package.json" in contracts_readme
    assert "DR-0053: P3.6 Inventory And Admission Contract Gap R0" in decision_register
    assert "DR-0054: P3.6 Planning Package And Inventory Policy Acceptances" in (
        decision_register
    )
