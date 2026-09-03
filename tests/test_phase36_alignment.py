from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-6-phase-minus-1-alignment.json"
)
ENTRY_GATES_PATH = ROOT / "contracts" / "phase-3" / "p3-6-entry-gates.json"
PROFILE_POLICY_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-6-capability-profile-policy.json"
)
OWNER_DECISIONS_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-6-owner-decisions.json"
)
ALIGNMENT_DOC_PATH = ROOT / "docs" / "phase-3" / "p3-6-phase-minus-1-alignment.md"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_alignment_binds_exact_phase_minus_1_revisions() -> None:
    record = _read(ALIGNMENT_PATH)
    sources = record["phase_minus_1_sources"]

    assert sources["shared_contracts"]["merge_commit"] == (
        "d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8"
    )
    assert sources["deployment_profiles"]["merge_commit"] == (
        "71095fe89d2b711e4982ddc0130fcaedda8703e7"
    )
    assert sources["deployment_profiles"]["base_profile_digest"] == (
        "sha256:db776a7432e46dcbf0f170efde428002d656faf3b4cc278fc776c8aabd6c94cf"
    )
    assert sources["delivery_evidence"]["merge_commit"] == (
        "809c44c2f32b2420ab954bed994b098bad1d1238"
    )


def test_all_p3_6_owner_decisions_have_shared_contract_owners() -> None:
    record = _read(ALIGNMENT_PATH)
    crosswalk = record["decision_crosswalk"]
    owner_record = _read(OWNER_DECISIONS_PATH)

    assert [item["p3_6_decision"] for item in crosswalk] == [
        "D-P3.6-001",
        "D-P3.6-002",
        "D-P3.6-003",
        "D-P3.6-004",
        "D-P3.6-005",
    ]
    assert all(item["phase_minus_1_contracts"] for item in crosswalk)
    assert [item["selected_option"] for item in owner_record["decisions"]] == [
        "A",
        "A+",
        "A+",
        "A",
        "A",
    ]
    assert owner_record["implementation_authorized"] is False
    assert owner_record["runtime_execution_authorized"] is False


def test_profile_aliases_do_not_create_competing_profile_classes() -> None:
    record = _read(ALIGNMENT_PATH)
    by_term = {item["historical_p3_6_term"]: item for item in record["profile_crosswalk"]}

    assert by_term["portable_cpu"]["effective_phase_minus_1_profile"] == "portable_cpu"
    assert by_term["local_accelerated"]["effective_phase_minus_1_profile"] == (
        "owned_gpu_lab"
    )
    assert by_term["capacity_target"]["classification"] == "evidence_target_only"
    assert by_term["capacity_target"]["effective_phase_minus_1_profile"] is None
    assert by_term["capacity_target"]["allowed_target_profiles"] == [
        "standalone_server",
        "kubernetes_cluster",
    ]


def test_objectives_and_evidence_tiers_are_not_profiles() -> None:
    record = _read(ALIGNMENT_PATH)

    assert record["objective_modes"]["values"] == [
        "balanced",
        "throughput",
        "latency",
    ]
    assert record["objective_modes"]["not_a_deployment_profile"] is True
    assert record["evidence_tiers"]["values"] == ["C1", "C10", "C50"]
    assert record["evidence_tiers"]["not_a_deployment_profile"] is True
    assert record["evidence_tiers"]["not_a_capacity_claim_without_exact_evidence"] is True


def test_authority_partition_is_complete_and_non_overlapping() -> None:
    record = _read(ALIGNMENT_PATH)
    partition = record["authority_partition"]
    shared = set(partition["phase_minus_1_shared_contracts_own"])
    specialized = set(partition["p3_6_specialization_owns"])

    assert len(shared) == 7
    assert len(specialized) == 7
    assert shared.isdisjoint(specialized)


def test_alignment_preserves_blocked_execution_gates() -> None:
    record = _read(ALIGNMENT_PATH)
    gates = _read(ENTRY_GATES_PATH)
    by_gate = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert record["gate_effects"]["alignment_gate"] == {
        "gate_id": "P36-G0A",
        "state": "passed",
        "summary": (
            "P3.6 planning vocabulary and ownership are aligned to the completed "
            "Phase -1 shared contract and deployment-profile baseline."
        ),
    }
    assert by_gate == {
        "P36-G0": "passed",
        "P36-G0A": "passed",
        "P36-G1": "blocked",
        "P36-G2": "blocked",
        "P36-G3": "passed",
        "P36-G4": "blocked",
        "P36-G5": "blocked",
    }
    assert gates["phase_minus_1_alignment"] == (
        "contracts/phase-3/p3-6-phase-minus-1-alignment.json"
    )


def test_alignment_and_profile_policy_grant_no_execution_authority() -> None:
    record = _read(ALIGNMENT_PATH)
    policy = _read(PROFILE_POLICY_PATH)

    assert record["implementation_authorized"] is False
    assert record["runtime_execution_authorized"] is False
    assert record["deployment_authorized"] is False
    assert record["remote_git_authorized"] is False
    assert policy["phase_minus_1_alignment_record"] == (
        "contracts/phase-3/p3-6-phase-minus-1-alignment.json"
    )
    assert policy["effective_profile_model"]["capacity_target_is_profile"] is False
    assert policy["future_operator_controls"]["hardware_profile_class"] == [
        "auto",
        "portable_cpu",
        "owned_gpu_lab",
        "standalone_server",
        "kubernetes_cluster",
    ]


def test_alignment_document_is_indexed_and_preserves_pending_owner_gate() -> None:
    document = ALIGNMENT_DOC_PATH.read_text(encoding="utf-8")
    normalized_document = " ".join(document.split())
    docs_index = (ROOT / "docs" / "phase-3" / "README.md").read_text(
        encoding="utf-8"
    )
    contracts_index = (
        ROOT / "contracts" / "phase-3" / "README.md"
    ).read_text(encoding="utf-8")

    assert "D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE" in document
    assert "does not imply that acceptance" in normalized_document
    assert "P36-G1`: blocked" in document
    assert "P36-G2`: blocked" in document
    assert "P36-G4`: blocked" in document
    assert "P36-G5`: blocked" in document
    assert "p3-6-phase-minus-1-alignment.md" in docs_index
    assert "p3-6-phase-minus-1-alignment.json" in contracts_index
