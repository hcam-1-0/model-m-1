from __future__ import annotations

from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import (
    AssignmentId,
    CameraId,
    CapabilityId,
    ClassId,
    Confidence,
    ContractModel,
    ImmutableDigest,
    NormalizedBoundingBox,
    SourceFrame,
    StableName,
    StreamId,
    UtcDateTime,
)


RuntimeRequestId = Annotated[str, Field(pattern=r"^run_[0-9a-f]{32}$")]
RuntimeInputId = Annotated[str, Field(pattern=r"^input_[0-9a-f]{32}$")]
RuntimeLeaseId = Annotated[str, Field(pattern=r"^lease_[0-9a-f]{32}$")]
RuntimeFailureCode = Literal[
    "artifact_rejected",
    "deadline_exceeded",
    "input_expired",
    "invalid_input",
    "resource_exhausted",
    "runtime_internal",
    "runtime_unconfigured",
    "unsupported_capability",
]


class RuntimeAdapterDescriptorV1(ContractModel):
    contract_type: Literal["hcam.analytics.runtime-adapter.v1"] = (
        "hcam.analytics.runtime-adapter.v1"
    )
    adapter_id: StableName
    adapter_version: ImmutableDigest
    supported_capabilities: Annotated[
        list[CapabilityId],
        Field(min_length=1, max_length=32),
    ]
    maximum_batch_size: Annotated[int, Field(ge=1, le=64)]
    input_contract: Literal["hcam.analytics.runtime-input.v1"] = (
        "hcam.analytics.runtime-input.v1"
    )
    output_contract: Literal["hcam.analytics.runtime-result.v1"] = (
        "hcam.analytics.runtime-result.v1"
    )
    network_access: Literal["denied"] = "denied"
    artifact_access: Literal["verified_handle_only"] = "verified_handle_only"
    configured: bool = False

    @field_validator("supported_capabilities")
    @classmethod
    def capabilities_are_unique(
        cls,
        value: list[CapabilityId],
    ) -> list[CapabilityId]:
        if len(set(value)) != len(value):
            raise ValueError("runtime capabilities must be unique")
        return value


class RuntimeInputDescriptorV1(ContractModel):
    input_id: RuntimeInputId
    lease_id: RuntimeLeaseId
    stream_id: StreamId
    camera_id: CameraId
    source: SourceFrame
    observed_at: UtcDateTime
    issued_at: UtcDateTime
    expires_at: UtcDateTime
    pixel_format: Literal["bgr8", "nv12", "rgb8"]

    @model_validator(mode="after")
    def lease_is_short_lived(self) -> RuntimeInputDescriptorV1:
        lifetime = (self.expires_at - self.issued_at).total_seconds()
        if lifetime <= 0 or lifetime > 60:
            raise ValueError("runtime input lease must expire within 60 seconds")
        return self


class RuntimeBatchRequestV1(ContractModel):
    contract_type: Literal["hcam.analytics.runtime-request.v1"] = (
        "hcam.analytics.runtime-request.v1"
    )
    request_id: RuntimeRequestId
    assignment_id: AssignmentId
    capability: CapabilityId
    stream_id: StreamId
    camera_id: CameraId
    deadline_at: UtcDateTime
    inputs: Annotated[
        list[RuntimeInputDescriptorV1], Field(min_length=1, max_length=16)
    ]

    @model_validator(mode="after")
    def inputs_match_scope_and_deadline(self) -> RuntimeBatchRequestV1:
        input_ids = {item.input_id for item in self.inputs}
        lease_ids = {item.lease_id for item in self.inputs}
        if len(input_ids) != len(self.inputs) or len(lease_ids) != len(self.inputs):
            raise ValueError("runtime input and lease IDs must be unique per batch")
        for item in self.inputs:
            if item.stream_id != self.stream_id or item.camera_id != self.camera_id:
                raise ValueError("runtime input scope must match the batch")
            if self.deadline_at <= item.issued_at or self.deadline_at > item.expires_at:
                raise ValueError(
                    "runtime deadline must remain within every input lease"
                )
        return self


class RuntimeBatchRequestV2(RuntimeBatchRequestV1):
    contract_type: Literal["hcam.analytics.runtime-request.v2"] = (
        "hcam.analytics.runtime-request.v2"
    )
    minimum_confidence: Confidence


RuntimeBatchRequest = RuntimeBatchRequestV1 | RuntimeBatchRequestV2


class RuntimeObservationCandidateV1(ContractModel):
    input_id: RuntimeInputId
    class_id: ClassId
    confidence: Confidence
    bbox: NormalizedBoundingBox


class RuntimeBatchResultV1(ContractModel):
    contract_type: Literal["hcam.analytics.runtime-result.v1"] = (
        "hcam.analytics.runtime-result.v1"
    )
    request_id: RuntimeRequestId
    status: Literal["succeeded", "degraded", "failed"]
    candidates: Annotated[
        list[RuntimeObservationCandidateV1],
        Field(max_length=1_024),
    ] = Field(default_factory=list)
    failure_code: RuntimeFailureCode | None = None

    @model_validator(mode="after")
    def result_status_is_consistent(self) -> RuntimeBatchResultV1:
        if self.status == "succeeded" and self.failure_code is not None:
            raise ValueError("successful runtime result cannot include a failure code")
        if self.status == "failed":
            if self.failure_code is None:
                raise ValueError("failed runtime result requires a safe failure code")
            if self.candidates:
                raise ValueError("failed runtime result cannot contain candidates")
        if self.status == "degraded" and self.failure_code is None:
            raise ValueError("degraded runtime result requires a safe failure code")
        return self


@runtime_checkable
class AnalyticsRuntimeAdapter(Protocol):
    @property
    def descriptor(self) -> RuntimeAdapterDescriptorV1: ...

    def infer(self, request: RuntimeBatchRequest) -> RuntimeBatchResultV1: ...


def validate_runtime_result(
    request: RuntimeBatchRequest,
    result: RuntimeBatchResultV1,
) -> RuntimeBatchResultV1:
    if result.request_id != request.request_id:
        raise ValueError("runtime result request_id must match the request")
    allowed_inputs = {item.input_id for item in request.inputs}
    if any(candidate.input_id not in allowed_inputs for candidate in result.candidates):
        raise ValueError("runtime result references an input outside the request")
    return result


def failed_runtime_result(
    request: RuntimeBatchRequest,
    code: RuntimeFailureCode,
) -> RuntimeBatchResultV1:
    return RuntimeBatchResultV1(
        request_id=request.request_id,
        status="failed",
        candidates=[],
        failure_code=code,
    )


class UnavailableAnalyticsRuntimeAdapter:
    """Fail-closed adapter used until a reviewed runtime implementation exists."""

    def __init__(self, descriptor: RuntimeAdapterDescriptorV1) -> None:
        if descriptor.configured:
            raise ValueError("unavailable adapter descriptor must not be configured")
        self._descriptor = descriptor

    @property
    def descriptor(self) -> RuntimeAdapterDescriptorV1:
        return self._descriptor

    def infer(self, request: RuntimeBatchRequest) -> RuntimeBatchResultV1:
        return failed_runtime_result(request, "runtime_unconfigured")


class GuardedAnalyticsRuntimeAdapter:
    """Validate adapter boundaries and collapse implementation errors to safe codes."""

    def __init__(self, delegate: AnalyticsRuntimeAdapter) -> None:
        self._delegate = delegate

    @property
    def descriptor(self) -> RuntimeAdapterDescriptorV1:
        return self._delegate.descriptor

    def infer(self, request: RuntimeBatchRequest) -> RuntimeBatchResultV1:
        descriptor = self.descriptor
        if not descriptor.configured:
            return failed_runtime_result(request, "runtime_unconfigured")
        if request.capability not in descriptor.supported_capabilities:
            return failed_runtime_result(request, "unsupported_capability")
        if len(request.inputs) > descriptor.maximum_batch_size:
            return failed_runtime_result(request, "resource_exhausted")
        try:
            result = self._delegate.infer(request)
            return validate_runtime_result(request, result)
        except Exception:
            return failed_runtime_result(request, "runtime_internal")
