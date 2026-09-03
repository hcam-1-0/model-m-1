from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from tools import phase35_consensus as consensus


def test_w8_generated_consensus_evidence_is_exact_and_fail_closed() -> None:
    evaluation = consensus.build_evaluation()
    scenarios = {item.scenario: item for item in evaluation.scenario_evaluations}

    assert evaluation.replay_runs == 20
    assert evaluation.replay_output_deterministic is True
    assert evaluation.maximum_active_states_observed == 256
    assert evaluation.consensus_execution_count == 281
    assert evaluation.consensus_closed_result_count == 269
    assert evaluation.consensus_abstained_result_count == 269
    assert evaluation.duplicate_rejection_count == 1
    assert evaluation.out_of_order_rejection_count == 1
    assert evaluation.accepted_value_count == 0
    assert evaluation.operational_event_count == 0
    assert evaluation.threshold_configuration_approved is False
    assert scenarios["agreement"].closed_result_count == 1
    assert scenarios["cross_boundary_isolation"].closed_result_count == 4
    assert scenarios["epoch_reset"].closed_result_count == 2
    assert scenarios["overload"].closed_result_count == 257
    assert all(
        item.abstained_result_count == item.closed_result_count
        for item in scenarios.values()
    )


def test_w8_aggregate_evidence_has_no_ephemeral_text_or_identifiers() -> None:
    rendered = consensus.render_evaluation(consensus.build_evaluation())

    assert "SYN-" not in rendered
    assert '"stream_id":' not in rendered
    assert '"tracker_epoch":' not in rendered
    assert '"track_id":' not in rendered
    assert '"winning_candidate":' not in rendered
    assert '"ranked_votes":' not in rendered
    assert "B:\\" not in rendered


def test_w8_replay_is_deterministic_across_independent_builds() -> None:
    first = consensus.render_evaluation(consensus.build_evaluation())
    second = consensus.render_evaluation(consensus.build_evaluation())

    assert first == second


def test_w8_evaluation_rejects_non_abstaining_or_inconsistent_totals() -> None:
    document = consensus.build_evaluation().model_dump(mode="python")
    document["consensus_abstained_result_count"] -= 1

    with pytest.raises(ValidationError):
        consensus.ConsensusGeneratedEvaluationV1.model_validate(document)

    document = consensus.build_evaluation().model_dump(mode="python")
    document["consensus_execution_count"] -= 1
    with pytest.raises(ValidationError, match="execution counts"):
        consensus.ConsensusGeneratedEvaluationV1.model_validate(document)

    document = consensus.build_evaluation().model_dump(mode="python")
    document["duplicate_rejection_count"] = 2
    with pytest.raises(ValidationError, match="rejection counts"):
        consensus.ConsensusGeneratedEvaluationV1.model_validate(document)


def test_w8_evidence_writer_requires_explicit_acknowledgment() -> None:
    assert consensus.main(["evaluate", "--write-evidence"]) == 2


def test_w8_tracked_evidence_is_canonical() -> None:
    assert consensus.check_evidence() == 0


def test_w8_evidence_is_valid_json_object() -> None:
    document = json.loads(
        consensus.render_evaluation(consensus.build_evaluation())
    )

    assert document["contract_type"].endswith("consensus-generated-evaluation.v1")
    assert document["plate_text_retention_hours"] == 0
