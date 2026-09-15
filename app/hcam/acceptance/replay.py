from __future__ import annotations

from dataclasses import dataclass

from hcam.acceptance.bounds import REQUIRED_SCENARIO_IDS
from hcam.acceptance.canonical import stable_id
from hcam.acceptance.contracts import (
    ReconstructionEntryV1,
    ReconstructionManifestV1,
    ReplayComparisonV1,
    ScenarioManifestV1,
    ScenarioRunV1,
)
from hcam.acceptance.determinism import compare_replays
from hcam.acceptance.scenarios import ScenarioEngine


@dataclass(frozen=True, slots=True)
class PortfolioResult:
    runs: tuple[ScenarioRunV1, ...]
    comparisons: tuple[ReplayComparisonV1, ...]

    @property
    def complete(self) -> bool:
        return (
            len(self.runs) == len(REQUIRED_SCENARIO_IDS) * 2
            and len(self.comparisons) == len(REQUIRED_SCENARIO_IDS)
            and all(item.complete for item in self.runs)
            and all(item.status == "passed" for item in self.comparisons)
        )


def run_portfolio(
    engine: ScenarioEngine, manifest: ScenarioManifestV1
) -> PortfolioResult:
    scenarios = {item.scenario_id: item for item in manifest.scenarios}
    if tuple(scenarios) != REQUIRED_SCENARIO_IDS:
        raise ValueError("the accepted nine-scenario portfolio is required")
    runs: list[ScenarioRunV1] = []
    comparisons: list[ReplayComparisonV1] = []
    for scenario_id in REQUIRED_SCENARIO_IDS:
        scenario = scenarios[scenario_id]
        first = engine.run(manifest, scenario, replay_index=1)
        second = engine.run(manifest, scenario, replay_index=2)
        runs.extend((first, second))
        comparisons.append(compare_replays(first, second))
    return PortfolioResult(tuple(runs), tuple(comparisons))


def build_reconstruction_manifest(run: ScenarioRunV1) -> ReconstructionManifestV1:
    entries: list[ReconstructionEntryV1] = []
    previous: str | None = None
    for observation in run.observations:
        entry_id = stable_id(
            "p47", run.scenario_id, "reconstruction", observation.sequence
        )
        state = (
            "retracted"
            if observation.action == "record_retraction"
            else (
                "corrected" if observation.action == "record_correction" else "original"
            )
        )
        entries.append(
            ReconstructionEntryV1(
                entry_id=entry_id,
                order=observation.sequence,
                kind=observation.action,
                source_ref=observation.observation_id,
                previous_entry_id=previous,
                correction_state=state,
            )
        )
        previous = entry_id
    return ReconstructionManifestV1(
        reconstruction_id=stable_id("p47", run.scenario_id, "reconstruction"),
        scenario_id=run.scenario_id,
        entries=tuple(entries),
        chronology_complete=run.complete,
    )
