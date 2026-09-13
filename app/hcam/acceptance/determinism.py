from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from hcam.acceptance.canonical import digest, stable_id
from hcam.acceptance.contracts import ReplayComparisonV1, ScenarioRunV1


class DeterminismError(ValueError):
    pass


@dataclass(slots=True)
class LogicalClock:
    current: datetime

    def advance(self, milliseconds: int) -> datetime:
        if milliseconds < 0 or milliseconds > 86_400_000:
            raise DeterminismError("logical clock advance is outside the bound")
        self.current += timedelta(milliseconds=milliseconds)
        return self.current


@dataclass(frozen=True, slots=True)
class IdentifierProvider:
    namespace: str
    seed: int

    def issue(self, *parts: object, prefix: str = "p47") -> str:
        return stable_id(prefix, self.namespace, self.seed, *parts)


def semantic_projection(run: ScenarioRunV1) -> dict[str, Any]:
    return {
        "contract_type": run.contract_type,
        "scenario_id": run.scenario_id,
        "manifest_digest": run.manifest_digest,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat(),
        "terminal_state": run.terminal_state,
        "observations": [
            {
                "scenario_id": item.scenario_id,
                "step_id": item.step_id,
                "sequence": item.sequence,
                "logical_at": item.logical_at.isoformat(),
                "action": item.action,
                "outcome": item.outcome,
                "reason_code": item.reason_code,
                "state": item.state,
                "output_digest": item.output_digest,
                "mutation_count": item.mutation_count,
            }
            for item in run.observations
        ],
        "assertions": [
            {
                "scenario_id": item.scenario_id,
                "family": item.family,
                "status": item.status,
                "reason_code": item.reason_code,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in run.assertions
        ],
        "side_effects": run.side_effects.model_dump(mode="json"),
        "complete": run.complete,
        "generated_only": run.generated_only,
        "operational": run.operational,
    }


def semantic_digest(run: ScenarioRunV1) -> str:
    return digest(semantic_projection(run), maximum_bytes=16_777_216)


def compare_replays(first: ScenarioRunV1, second: ScenarioRunV1) -> ReplayComparisonV1:
    if first.scenario_id != second.scenario_id:
        raise DeterminismError("replay scenarios differ")
    if (first.replay_index, second.replay_index) != (1, 2):
        raise DeterminismError("replay indexes must be one and two")
    first_digest = semantic_digest(first)
    second_digest = semantic_digest(second)
    equal = first_digest == second_digest
    return ReplayComparisonV1(
        scenario_id=first.scenario_id,
        first_run_id=first.run_id,
        second_run_id=second.run_id,
        first_semantic_digest=first_digest,
        second_semantic_digest=second_digest,
        equal=equal,
        status="passed" if equal else "failed",
        reason_code="replay.semantic_equal" if equal else "replay.semantic_mismatch",
    )
