from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from hcam.acceptance.adapters import ApplicationBoundary, GeneratedApplicationBoundary
from hcam.acceptance.assertions import evaluate_assertions
from hcam.acceptance.canonical import digest, stable_id
from hcam.acceptance.contracts import (
    ScenarioDefinitionV1,
    ScenarioManifestV1,
    ScenarioRunV1,
    SideEffectLedgerV1,
    StepObservationV1,
)
from hcam.acceptance.determinism import (
    IdentifierProvider,
    LogicalClock,
    semantic_digest,
)


class ScenarioRuntimeError(RuntimeError):
    reason_code = "acceptance.runtime_denied"


AdapterFactory = Callable[[str], ApplicationBoundary]


@dataclass(frozen=True, slots=True)
class GeneratedScenarioRuntime:
    enabled: bool = False
    environment: str = "development"

    def require_enabled(self) -> None:
        environment = self.environment.strip().lower()
        if environment in {"prod", "production"}:
            raise ScenarioRuntimeError(
                "P4.7 generated acceptance is forbidden in production"
            )
        if not self.enabled:
            raise ScenarioRuntimeError(
                "P4.7 generated acceptance is disabled by default"
            )


class ScenarioEngine:
    def __init__(
        self,
        *,
        enabled: bool = False,
        environment: str = "development",
        adapter_factory: AdapterFactory | None = None,
    ) -> None:
        self.runtime = GeneratedScenarioRuntime(
            enabled=enabled, environment=environment
        )
        self.adapter_factory = adapter_factory or GeneratedApplicationBoundary

    def run(
        self,
        manifest: ScenarioManifestV1,
        scenario: ScenarioDefinitionV1,
        *,
        replay_index: int,
    ) -> ScenarioRunV1:
        self.runtime.require_enabled()
        if replay_index not in {1, 2}:
            raise ScenarioRuntimeError("replay index must be one or two")
        manifest_scenarios = {item.scenario_id: item for item in manifest.scenarios}
        if scenario.scenario_id not in manifest_scenarios:
            raise ScenarioRuntimeError("scenario is not in the accepted manifest")
        if scenario != manifest_scenarios[scenario.scenario_id]:
            raise ScenarioRuntimeError(
                "scenario does not match the accepted manifest definition"
            )
        identifiers = IdentifierProvider(manifest.identifier_namespace, manifest.seed)
        clock = LogicalClock(manifest.logical_epoch)
        adapter = self.adapter_factory(scenario.scenario_id)
        observations: list[StepObservationV1] = []
        manifest_digest = digest(manifest, maximum_bytes=16_777_216)
        for step in scenario.steps:
            logical_at = clock.advance(step.advance_ms)
            response = adapter.execute(
                step, logical_at=logical_at, identifiers=identifiers
            )
            observations.append(
                StepObservationV1(
                    observation_id=stable_id(
                        "p47", scenario.scenario_id, "observation", step.sequence
                    ),
                    scenario_id=scenario.scenario_id,
                    step_id=step.step_id,
                    sequence=step.sequence,
                    logical_at=logical_at,
                    action=response.action,
                    outcome=response.outcome,
                    reason_code=response.reason_code,
                    state=response.state,
                    output_digest=digest(response.output),
                    mutation_count=response.mutation_count,
                )
            )
        side_effects = SideEffectLedgerV1()
        assertions = evaluate_assertions(
            scenario,
            observations,
            adapter.snapshot(),
            side_effects,
        )
        terminal_state = adapter.terminal_state()
        complete = terminal_state == scenario.expected_terminal_state and all(
            item.status == "passed" for item in assertions
        )
        candidate = ScenarioRunV1(
            run_id=identifiers.issue(scenario.scenario_id, "run", replay_index),
            scenario_id=scenario.scenario_id,
            replay_index=replay_index,
            manifest_digest=manifest_digest,
            started_at=manifest.logical_epoch,
            completed_at=clock.current,
            terminal_state=terminal_state,
            observations=tuple(observations),
            assertions=assertions,
            side_effects=side_effects,
            semantic_digest="sha256:" + "0" * 64,
            complete=complete,
        )
        return candidate.model_copy(
            update={"semantic_digest": semantic_digest(candidate)}
        )
