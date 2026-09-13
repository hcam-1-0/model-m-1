from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator

from hcam.operations.platform.bounds import (
    MAX_BURN_WINDOWS,
    MAX_CAPACITY_STEPS,
    MAX_LABELS_PER_METRIC,
    MAX_PLACEMENT_NODES,
    MAX_PLACEMENT_SERVICES,
    MAX_SAFE_FAILURE_PARAMETERS,
    MAX_SUPPLY_CHAIN_COMPONENTS,
    MAX_UNIFIED_SEARCH_ITEMS,
    bounded_text,
    validate_generated_document,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


UtcDateTime = Annotated[datetime, AfterValidator(_utc)]
Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Department = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,119}$")]
StableName = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]
OpaqueRef = Annotated[str, Field(pattern=r"^ref_[0-9a-f]{32}$")]
ReasonCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")]
Revision = Annotated[int, Field(ge=1, le=2_147_483_647)]
Ratio = Annotated[float, Field(ge=0, le=1)]


class MetricDefinitionV1(ContractModel):
    name: Annotated[str, Field(pattern=r"^hcam_[a-z0-9_]{1,119}$")]
    kind: Literal["counter", "gauge", "histogram"]
    unit: StableName
    labels: Annotated[tuple[StableName, ...], Field(max_length=MAX_LABELS_PER_METRIC)]
    description: Annotated[str, Field(min_length=8, max_length=512)]
    deprecated: bool = False

    @model_validator(mode="after")
    def labels_are_unique(self) -> MetricDefinitionV1:
        if len(self.labels) != len(set(self.labels)):
            raise ValueError("metric labels must be unique")
        return self


class TraceContextV1(ContractModel):
    trace_id: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    parent_id: Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]
    sampled: bool
    tracestate: Annotated[str, Field(max_length=512)] | None = None
    grants_authority: Literal[False] = False


class CorrelationContextV1(ContractModel):
    correlation_id: StableName
    causation_id: StableName | None = None
    grants_authority: Literal[False] = False


SignalLane = Literal["operational", "security", "audit", "evidence"]


class SignalEnvelopeV1(ContractModel):
    signal_id: OpaqueRef
    lane: SignalLane
    department: Department
    event_type: ReasonCode
    severity: Literal["debug", "info", "warning", "error", "critical"]
    occurred_at: UtcDateTime
    attributes: Annotated[dict[str, Any], Field(max_length=32)]
    trace: TraceContextV1 | None = None
    correlation: CorrelationContextV1
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @field_validator("attributes")
    @classmethod
    def attributes_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_generated_document(value)
        return value


class SignalProjectionV1(ContractModel):
    signal_id: OpaqueRef
    lane: SignalLane
    department: Department
    event_type: ReasonCode
    severity: Literal["debug", "info", "warning", "error", "critical"]
    occurred_at: UtcDateTime
    safe_facets: Annotated[dict[str, str | int | bool], Field(max_length=16)]
    source_policy_authoritative: Literal[True] = True
    generated_only: Literal[True] = True


class UnifiedSearchProjectionV1(ContractModel):
    profile: Literal["hcam.unified-signal-search.generated.v1"] = (
        "hcam.unified-signal-search.generated.v1"
    )
    enabled: Literal[False] = False
    authoritative: Literal[False] = False
    raw_records_retained: Literal[False] = False
    items: Annotated[list[SignalProjectionV1], Field(max_length=MAX_UNIFIED_SEARCH_ITEMS)]
    result_digest: Digest
    generated_only: Literal[True] = True


class FailureV1(ContractModel):
    code: ReasonCode
    failure_class: Literal[
        "authorization", "policy", "validation", "integrity", "dependency",
        "concurrency", "capacity", "configuration", "unknown"
    ]
    retry: Literal["never", "bounded"]
    safe_parameters: Annotated[dict[StableName, str | int | bool], Field(max_length=MAX_SAFE_FAILURE_PARAMETERS)]
    generated_only: Literal[True] = True

    @field_validator("safe_parameters")
    @classmethod
    def parameters_are_bounded(cls, value: dict[str, str | int | bool]):
        validate_generated_document(value)
        return value


class BurnWindowV1(ContractModel):
    window_seconds: Annotated[int, Field(ge=60, le=2_592_000)]
    good: Annotated[int, Field(ge=0)]
    valid: Annotated[int, Field(ge=0)]
    bad: Annotated[int, Field(ge=0)]
    unknown: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def counts_are_consistent(self) -> BurnWindowV1:
        if self.good + self.bad != self.valid:
            raise ValueError("valid must equal good plus bad")
        return self


class ServiceObjectiveV1(ContractModel):
    objective_id: OpaqueRef
    department: Department
    service_class: Literal["api", "worker", "database", "projection"]
    indicator: StableName
    target_state: Literal["unset", "provisional", "approved"] = "unset"
    target_ratio: Ratio | None = None
    windows: Annotated[list[BurnWindowV1], Field(min_length=1, max_length=MAX_BURN_WINDOWS)]
    revision: Revision
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def target_is_explicit(self) -> ServiceObjectiveV1:
        if (self.target_state == "unset") != (self.target_ratio is None):
            raise ValueError("unset targets cannot carry a ratio")
        return self


class ErrorBudgetStateV1(ContractModel):
    objective_id: OpaqueRef
    target_state: Literal["unset", "provisional", "approved"]
    compliance_ratio: Ratio | None
    remaining_ratio: Ratio | None
    burn_rates: Annotated[list[float | None], Field(max_length=MAX_BURN_WINDOWS)]
    data_quality: Literal["complete", "partial", "unknown"]
    status: Literal["unknown", "within_budget", "at_risk", "exhausted"]
    generated_only: Literal[True] = True


class HealthProjectionV1(ContractModel):
    service_class: Literal["api", "worker", "database", "projection"]
    state: Literal["healthy", "constrained", "degraded", "stopped", "unknown"]
    reason_codes: Annotated[list[ReasonCode], Field(max_length=16)]
    grants_authority: Literal[False] = False
    generated_only: Literal[True] = True


class DegradationDecisionV1(ContractModel):
    state: Literal["normal", "constrained", "degraded", "stopped"]
    mandatory_controls_preserved: Literal[True] = True
    optional_lanes_bypassed: Annotated[list[StableName], Field(max_length=32)]
    reasons: Annotated[list[ReasonCode], Field(min_length=1, max_length=16)]
    grants_capability: Literal[False] = False
    generated_only: Literal[True] = True


class WorkerJobV1(ContractModel):
    job_id: OpaqueRef
    department: Department
    worker_class: Literal["telemetry", "recovery", "capacity", "supply_chain"]
    state: Literal["queued", "leased", "succeeded", "failed", "dead_letter"]
    attempt_count: Annotated[int, Field(ge=0, le=3)]
    lease_owner: StableName | None = None
    lease_until: UtcDateTime | None = None
    idempotency_key: Digest
    payload_digest: Digest
    reason_code: ReasonCode
    updated_at: UtcDateTime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def lease_is_consistent(self) -> WorkerJobV1:
        leased = self.state == "leased"
        if leased != (self.lease_owner is not None and self.lease_until is not None):
            raise ValueError("lease fields are inconsistent")
        return self


class CircuitStateV1(ContractModel):
    dependency_class: StableName
    state: Literal["closed", "open", "half_open"]
    consecutive_failures: Annotated[int, Field(ge=0, le=1_000)]
    probe_remaining: Annotated[int, Field(ge=0, le=16)]
    opened_at: UtcDateTime | None = None
    updated_at: UtcDateTime
    generated_only: Literal[True] = True


class KillSwitchRevisionV1(ContractModel):
    switch_id: OpaqueRef
    department: Department
    scope: Literal["platform", "department", "service", "lane"]
    scope_key: StableName
    state: Literal["deny", "allow"]
    mandatory_control: bool = False
    revision: Revision
    actor_id: StableName
    reason_code: ReasonCode
    expires_at: UtcDateTime | None = None
    recorded_at: UtcDateTime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class AuthorizationContextV1(ContractModel):
    actor_id: StableName
    department: Department
    roles: Annotated[frozenset[StableName], Field(min_length=1, max_length=32)]
    purpose_code: ReasonCode
    reason: Annotated[str, Field(min_length=8, max_length=2_000)]
    expected_revision: Revision
    idempotency_key: Digest

    _reason = field_validator("reason")(lambda value: bounded_text(value, minimum=8, maximum=2_000))


class SupplyChainComponentV1(ContractModel):
    component_ref: OpaqueRef
    name: StableName
    version: StableName
    source: Literal["lockfile", "source", "fixture", "package", "evidence"]
    digest: Digest
    license_state: Literal["verified", "unknown", "not_applicable"]
    vulnerability_state: Literal["not_observed", "unknown", "stale", "failed", "verified"]
    provenance_state: Literal["not_observed", "unknown", "stale", "failed", "verified"]


class SupplyChainInventoryV1(ContractModel):
    inventory_id: OpaqueRef
    observed_at: UtcDateTime
    freshness: Literal["fresh", "stale", "unknown"]
    components: Annotated[list[SupplyChainComponentV1], Field(max_length=MAX_SUPPLY_CHAIN_COMPONENTS)]
    source_digest: Digest
    scanners_executed: Literal[False] = False
    conformance_claimed: Literal[False] = False
    generated_only: Literal[True] = True


class RecoveryAssetV1(ContractModel):
    asset_ref: OpaqueRef
    asset_class: Literal["database", "object", "configuration", "secret_reference", "key_reference", "audit", "evidence_reference"]
    recovery_tier: Literal["metadata", "control_state", "derived_state", "reference_only"]
    dependencies: Annotated[list[OpaqueRef], Field(max_length=1_024)]


class RecoveryPlanV1(ContractModel):
    plan_id: OpaqueRef
    department: Department
    revision: Revision
    target_state: Literal["unset", "provisional", "approved"] = "unset"
    target_rpo_seconds: Annotated[int, Field(ge=0)] | None = None
    target_rto_seconds: Annotated[int, Field(ge=0)] | None = None
    assets: Annotated[list[RecoveryAssetV1], Field(max_length=256)]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def targets_are_explicit(self) -> RecoveryPlanV1:
        has_targets = self.target_rpo_seconds is not None and self.target_rto_seconds is not None
        if (self.target_state == "unset") == has_targets:
            raise ValueError("recovery targets must match target state")
        return self


class RecoverySimulationResultV1(ContractModel):
    plan_id: OpaqueRef
    outcome: Literal["complete", "partial", "failed", "unknown"]
    restored_assets: Annotated[list[OpaqueRef], Field(max_length=256)]
    missing_assets: Annotated[list[OpaqueRef], Field(max_length=256)]
    integrity_failures: Annotated[list[OpaqueRef], Field(max_length=256)]
    external_action_executed: Literal[False] = False
    observed_rpo_seconds: int | None = None
    observed_rto_seconds: int | None = None
    generated_only: Literal[True] = True


class CapabilityProfileV1(ContractModel):
    profile_id: OpaqueRef
    profile_class: Literal["developer_laptop", "owned_gpu_lab", "server_node", "kubernetes_node_class"]
    state: Literal["declared", "observed", "attested", "stale", "unsupported", "unknown"]
    cpu_units: Annotated[int, Field(ge=1, le=65_536)]
    memory_mib: Annotated[int, Field(ge=256, le=16_777_216)]
    accelerator_units: Annotated[int, Field(ge=0, le=1_024)]
    capabilities: Annotated[frozenset[StableName], Field(max_length=128)]
    profile_digest: Digest
    generated_only: Literal[True] = True


class CapacityRunV1(ContractModel):
    run_id: OpaqueRef
    profile_id: OpaqueRef
    scale: Literal["C1", "C10", "C50"]
    mode: Literal["latency", "balanced", "throughput"]
    steps: Annotated[int, Field(ge=1, le=MAX_CAPACITY_STEPS)]
    completed_steps: Annotated[int, Field(ge=0, le=MAX_CAPACITY_STEPS)]
    latency_ms_p50: Annotated[float, Field(ge=0)] | None
    latency_ms_p95: Annotated[float, Field(ge=0)] | None
    throughput_per_second: Annotated[float, Field(ge=0)] | None
    backlog_high_water: Annotated[int, Field(ge=0)]
    saturation_ratio: Ratio
    loss_count: Annotated[int, Field(ge=0)]
    recovery_steps: Annotated[int, Field(ge=0)]
    resource_projection: Annotated[dict[str, float], Field(max_length=16)]
    limitations: Annotated[list[ReasonCode], Field(min_length=1, max_length=16)]
    status: Literal["complete", "incomplete", "failed"]
    generated_only: Literal[True] = True
    hardware_tested: Literal[False] = False

    @model_validator(mode="after")
    def result_is_honest(self) -> CapacityRunV1:
        if self.status == "complete" and self.completed_steps != self.steps:
            raise ValueError("complete capacity runs require every step")
        if self.status != "complete" and any(
            value is not None for value in (self.latency_ms_p50, self.latency_ms_p95, self.throughput_per_second)
        ):
            raise ValueError("incomplete capacity runs cannot publish capacity measurements")
        return self


class PlacementServiceV1(ContractModel):
    service_id: StableName
    cpu_units: Annotated[int, Field(ge=1, le=65_536)]
    memory_mib: Annotated[int, Field(ge=1, le=16_777_216)]
    accelerator_units: Annotated[int, Field(ge=0, le=1_024)]
    mandatory_capabilities: Annotated[frozenset[StableName], Field(max_length=64)]
    optional: bool = False


class PlacementRequestV1(ContractModel):
    request_id: OpaqueRef
    profiles: Annotated[list[CapabilityProfileV1], Field(min_length=1, max_length=MAX_PLACEMENT_NODES)]
    services: Annotated[list[PlacementServiceV1], Field(min_length=1, max_length=MAX_PLACEMENT_SERVICES)]
    generated_only: Literal[True] = True


class PlacementDecisionV1(ContractModel):
    service_id: StableName
    profile_id: OpaqueRef | None
    reason: Literal["placed", "optional_lane_bypassed", "mandatory_capability_missing", "capacity_exhausted", "capability_unknown"]


class PlacementPlanV1(ContractModel):
    request_id: OpaqueRef
    decisions: Annotated[list[PlacementDecisionV1], Field(max_length=MAX_PLACEMENT_SERVICES)]
    plan_digest: Digest
    executable: Literal[False] = False
    generated_only: Literal[True] = True
