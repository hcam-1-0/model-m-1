from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from hcam.intelligence.rules.compiler import CompiledRule
from hcam.intelligence.rules.contracts import RuleEvaluationV1, RuleInputV1
from hcam.intelligence.rules.evaluator import EvaluationState, evaluate_generated_rule
from hcam.intelligence.rules.persistence import RuleControlService


def run_and_store_generated_evidence(
    session: Session,
    *,
    rule_record_id: str,
    compiled: CompiledRule,
    inputs: list[RuleInputV1],
    interval_start: datetime,
    recorded_at: datetime,
    state: EvaluationState | None = None,
) -> RuleEvaluationV1:
    """Repository-owned harness entry point; never exposed as an HTTP mutation."""

    evaluation = evaluate_generated_rule(
        compiled,
        inputs,
        interval_start=interval_start,
        state=state,
    )
    with session.begin():
        RuleControlService(session, enabled=True).store_evaluation(
            rule_record_id,
            evaluation,
            recorded_at=recorded_at,
        )
    return evaluation
