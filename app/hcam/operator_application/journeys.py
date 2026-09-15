from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .bounds import MAX_JOURNEY_STEPS
from .contracts import OperatorContractModel, SafeCode, StableId, SurfaceState


class JourneyTransitionV1(OperatorContractModel):
    transition_id: StableId
    from_state: SurfaceState
    to_state: SurfaceState
    action_id: StableId
    reason_code: SafeCode
    requires_server_confirmation: bool = True


class JourneyContractV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.journey.v1"] = "hcam.operator.journey.v1"
    journey_id: StableId
    initial_state: SurfaceState
    terminal_states: Annotated[list[SurfaceState], Field(min_length=1, max_length=4)]
    transitions: Annotated[
        list[JourneyTransitionV1], Field(min_length=1, max_length=MAX_JOURNEY_STEPS)
    ]
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def transitions_are_valid(self) -> JourneyContractV1:
        transition_ids = [item.transition_id for item in self.transitions]
        if len(transition_ids) != len(set(transition_ids)):
            raise ValueError("journey transition identifiers must be unique")
        if len(self.terminal_states) != len(set(self.terminal_states)):
            raise ValueError("journey terminal states must be unique")
        reachable = {self.initial_state}
        changed = True
        while changed:
            changed = False
            for transition in self.transitions:
                if transition.from_state in reachable and transition.to_state not in reachable:
                    reachable.add(transition.to_state)
                    changed = True
        if not set(self.terminal_states) <= reachable:
            raise ValueError("journey terminal state is unreachable")
        return self


def advance_journey(
    journey: JourneyContractV1,
    *,
    state: SurfaceState,
    action_id: str,
    server_confirmed: bool,
) -> SurfaceState:
    for transition in journey.transitions:
        if transition.from_state == state and transition.action_id == action_id:
            if transition.requires_server_confirmation and not server_confirmed:
                raise PermissionError("journey transition requires server confirmation")
            return transition.to_state
    raise ValueError("journey transition is not allowed")
