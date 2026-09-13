import pytest

from hcam.acceptance.contracts import ScenarioDefinitionV1
from hcam.acceptance.fixtures import build_manifest
from hcam.acceptance.scenarios import ScenarioEngine, ScenarioRuntimeError


def test_scenario_runtime_is_default_off_and_production_forbidden() -> None:
    manifest = build_manifest()
    with pytest.raises(ScenarioRuntimeError):
        ScenarioEngine().run(manifest, manifest.scenarios[0], replay_index=1)
    with pytest.raises(ScenarioRuntimeError):
        ScenarioEngine(enabled=True, environment="production").run(
            manifest, manifest.scenarios[0], replay_index=1
        )


def test_scenario_runtime_rejects_unknown_replay_and_definition() -> None:
    manifest = build_manifest()
    engine = ScenarioEngine(enabled=True)
    with pytest.raises(ScenarioRuntimeError):
        engine.run(manifest, manifest.scenarios[0], replay_index=3)
    altered = ScenarioDefinitionV1.model_validate(
        {
            **manifest.scenarios[0].model_dump(mode="json"),
            "title": "Generated altered scenario title",
        }
    )
    with pytest.raises(ScenarioRuntimeError):
        engine.run(manifest, altered, replay_index=1)


def test_each_mandatory_scenario_completes() -> None:
    manifest = build_manifest()
    engine = ScenarioEngine(enabled=True)
    runs = [
        engine.run(manifest, scenario, replay_index=1)
        for scenario in manifest.scenarios
    ]
    assert all(run.complete for run in runs)
    assert {run.terminal_state for run in runs} == {
        item.expected_terminal_state for item in manifest.scenarios
    }
