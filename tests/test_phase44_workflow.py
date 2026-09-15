from __future__ import annotations

import pytest

from hcam.intelligence.integrations.jobs import JobQueue
from hcam.intelligence.integrations.policy import compile_query_plan
from hcam.intelligence.integrations.workflow import (
    DisabledWorkflowDispatchAdapter,
    GeneratedWorkflowExecutor,
)
from tests.test_phase44_contracts import NOW, intent, manifest


def test_generated_workflow_simulates_bounded_outcomes_and_duplicates() -> None:
    provider = manifest()
    plan = compile_query_plan(intent(provider), provider, control_enabled=True)
    job, _ = JobQueue().submit(plan, now=NOW)
    executor = GeneratedWorkflowExecutor()
    assert executor.execute(job).outcome == "accepted"
    assert executor.execute(job).outcome == "duplicate"
    with pytest.raises(ValueError):
        GeneratedWorkflowExecutor().execute(job, outcome="dispatch")
    assert DisabledWorkflowDispatchAdapter().execute(job).outcome == "disabled"
