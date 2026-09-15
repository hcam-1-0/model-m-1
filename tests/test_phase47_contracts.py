from datetime import datetime

import pytest
from pydantic import ValidationError

from hcam.acceptance.contracts import (
    ScenarioDefinitionV1,
    ScenarioManifestV1,
    ScenarioStepV1,
)
from hcam.acceptance.fixtures import build_manifest


def test_contracts_forbid_unknown_fields_and_non_utc_time() -> None:
    manifest = build_manifest()
    with pytest.raises(ValidationError):
        ScenarioManifestV1.model_validate(
            {**manifest.model_dump(mode="json"), "unknown": True}
        )
    with pytest.raises(ValidationError):
        ScenarioManifestV1.model_validate(
            {**manifest.model_dump(), "logical_epoch": datetime(2026, 1, 1)}
        )


def test_scenario_steps_require_contiguous_unique_sequences() -> None:
    step = ScenarioStepV1(
        step_id="p47.test.step",
        sequence=2,
        action="observe_event",
        advance_ms=1,
        input_data={"generated": True},
        expected_outcome="accepted",
        expected_reason="event.observed",
    )
    with pytest.raises(ValidationError):
        ScenarioDefinitionV1(
            scenario_id="S00",
            category="golden",
            title="Generated invalid scenario",
            steps=(step,),
            expected_terminal_state="completed",
        )


def test_manifest_rejects_duplicate_scenario_identifiers() -> None:
    manifest = build_manifest()
    with pytest.raises(ValidationError):
        ScenarioManifestV1.model_validate(
            {
                **manifest.model_dump(mode="json"),
                "scenarios": [manifest.scenarios[0], manifest.scenarios[0]],
            }
        )
