from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .bounds import MAX_ACTIONS, MAX_CAPABILITIES, MAX_ROLES


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_utc)]
StableId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.:-]{0,127}$")]
ContractVersion = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]*\.v[1-9][0-9]*$")]
SchemaVersion = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]
SafeCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
RoleName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
LocaleName = Literal["en-IN", "gu-IN", "hi-IN"]
ResourceProfile = Literal["low_resource", "enhanced", "control_room"]
SurfaceState = Literal[
    "loading",
    "empty",
    "ready",
    "partial",
    "stale",
    "degraded",
    "denied",
    "conflict",
    "failure",
    "recovery",
    "correction",
]
GapClass = Literal[
    "ready_for_generated_consumer",
    "partial",
    "blocked",
    "future_operational",
]


class OperatorContractModel(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        strict=True,
    )


class ProducerBindingV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.producer-binding.v1"] = (
        "hcam.operator.producer-binding.v1"
    )
    operation_id: StableId
    schema_version: SchemaVersion
    source_kind: Literal["http", "event", "generated_projection"]
    freshness_seconds: Annotated[int, Field(ge=1, le=86_400)]
    department_scoped: Literal[True] = True
    authoritative: bool
    gap_class: GapClass


class CapabilityDecisionV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.capability-decision.v1"] = (
        "hcam.operator.capability-decision.v1"
    )
    action: StableId
    allowed: bool
    reason_code: SafeCode
    source: Literal["server"] = "server"
    policy_version: SchemaVersion
    resource_profile: ResourceProfile
    observed_at: UtcDateTime


class CapabilityCeilingV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.capability-ceiling.v1"] = (
        "hcam.operator.capability-ceiling.v1"
    )
    policy_version: SchemaVersion
    allowed_actions: Annotated[list[StableId], Field(max_length=MAX_CAPABILITIES)]
    denied_actions: Annotated[list[StableId], Field(max_length=MAX_CAPABILITIES)]

    @model_validator(mode="after")
    def actions_do_not_overlap(self) -> CapabilityCeilingV1:
        if len(self.allowed_actions) != len(set(self.allowed_actions)):
            raise ValueError("allowed actions must be unique")
        if len(self.denied_actions) != len(set(self.denied_actions)):
            raise ValueError("denied actions must be unique")
        if set(self.allowed_actions) & set(self.denied_actions):
            raise ValueError("an action cannot be both allowed and denied")
        return self


class OperatorActionV1(OperatorContractModel):
    action_id: StableId
    command_kind: Literal["navigate", "query", "preview", "propose", "review"]
    required_roles: Annotated[list[RoleName], Field(min_length=1, max_length=MAX_ROLES)]
    requires_reason: bool = False
    requires_etag: bool = False
    operational: Literal[False] = False

    @field_validator("required_roles")
    @classmethod
    def roles_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("required roles must be unique")
        return value


class OperatorViewContractV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.view-contract.v1"] = (
        "hcam.operator.view-contract.v1"
    )
    view_id: StableId
    portal_id: StableId
    route_id: StableId
    title_key: StableId
    required_roles: Annotated[list[RoleName], Field(min_length=1, max_length=MAX_ROLES)]
    supported_states: Annotated[list[SurfaceState], Field(min_length=1, max_length=11)]
    actions: Annotated[list[OperatorActionV1], Field(max_length=MAX_ACTIONS)]
    producer: ProducerBindingV1
    locales: Annotated[list[LocaleName], Field(min_length=3, max_length=3)] = [
        "en-IN",
        "gu-IN",
        "hi-IN",
    ]
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def identifiers_are_unique(self) -> OperatorViewContractV1:
        if len(self.required_roles) != len(set(self.required_roles)):
            raise ValueError("view roles must be unique")
        if len(self.supported_states) != len(set(self.supported_states)):
            raise ValueError("surface states must be unique")
        action_ids = [action.action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("view action identifiers must be unique")
        if self.locales != ["en-IN", "gu-IN", "hi-IN"]:
            raise ValueError("all three accepted locales are required")
        return self


class SafeProblemV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.safe-problem.v1"] = (
        "hcam.operator.safe-problem.v1"
    )
    reason_code: SafeCode
    title_key: StableId
    recovery_action: Literal[
        "none", "retry", "refresh", "reauthenticate", "request_access", "contact_admin"
    ]
    retry_after_seconds: Annotated[int, Field(ge=1, le=3_600)] | None = None
    trace_ref: Annotated[str, Field(pattern=r"^trace_[0-9a-f]{16}$")] | None = None
    raw_detail: None = None

    @model_validator(mode="after")
    def retry_is_consistent(self) -> SafeProblemV1:
        if self.recovery_action == "retry" and self.retry_after_seconds is None:
            raise ValueError("retry recovery requires a bounded retry delay")
        if self.recovery_action != "retry" and self.retry_after_seconds is not None:
            raise ValueError("retry delay is only valid for retry recovery")
        return self


class GeneratedContractCaseV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.generated-case.v1"] = (
        "hcam.operator.generated-case.v1"
    )
    case_id: Annotated[str, Field(pattern=r"^syn_case_[0-9a-f]{20}$")]
    view_id: StableId
    state: SurfaceState
    resource_profile: ResourceProfile
    locale: LocaleName
    expected_outcome: Literal["accepted", "denied"]
    reason_code: SafeCode
    generated_only: Literal[True] = True
    operational: Literal[False] = False
