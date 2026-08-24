from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.analytics.contracts import canonical_contract_json
from hcam.analytics.runtime import (
    AnalyticsRuntimeAdapter,
    GuardedAnalyticsRuntimeAdapter,
    RuntimeAdapterDescriptorV1,
    RuntimeBatchRequestV1,
    RuntimeBatchResultV1,
    RuntimeObservationCandidateV1,
    UnavailableAnalyticsRuntimeAdapter,
    validate_runtime_result,
)


FIXTURE_ROOT = Path(__file__).parents[1] / "contracts" / "phase-3" / "fixtures"


def _document(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name,model",
    [
        ("runtime-adapter-unconfigured-v1.json", RuntimeAdapterDescriptorV1),
        ("runtime-request-v1.json", RuntimeBatchRequestV1),
        ("runtime-result-unconfigured-v1.json", RuntimeBatchResultV1),
    ],
)
def test_runtime_contract_fixtures_are_deterministic(name: str, model: type) -> None:
    parsed = model.model_validate(_document(name))
    assert canonical_contract_json(parsed) == (FIXTURE_ROOT / name).read_text(
        encoding="utf-8"
    )


def test_unavailable_runtime_adapter_is_fail_closed() -> None:
    descriptor = RuntimeAdapterDescriptorV1.model_validate(
        _document("runtime-adapter-unconfigured-v1.json")
    )
    request = RuntimeBatchRequestV1.model_validate(_document("runtime-request-v1.json"))
    adapter = UnavailableAnalyticsRuntimeAdapter(descriptor)

    assert isinstance(adapter, AnalyticsRuntimeAdapter)
    result = adapter.infer(request)
    assert result.status == "failed"
    assert result.failure_code == "runtime_unconfigured"
    assert result.candidates == []


def test_unavailable_adapter_rejects_configured_descriptor() -> None:
    document = _document("runtime-adapter-unconfigured-v1.json")
    document["configured"] = True
    descriptor = RuntimeAdapterDescriptorV1.model_validate(document)

    with pytest.raises(ValueError, match="must not be configured"):
        UnavailableAnalyticsRuntimeAdapter(descriptor)


@pytest.mark.parametrize("field", ["input_id", "lease_id"])
def test_runtime_batch_ids_must_be_unique(field: str) -> None:
    document = _document("runtime-request-v1.json")
    inputs = document["inputs"]
    assert isinstance(inputs, list) and isinstance(inputs[0], dict)
    duplicate = copy.deepcopy(inputs[0])
    duplicate["input_id"] = "input_22222222222222222222222222222222"
    duplicate["lease_id"] = "lease_22222222222222222222222222222222"
    duplicate[field] = inputs[0][field]
    inputs.append(duplicate)

    with pytest.raises(ValidationError, match="IDs must be unique"):
        RuntimeBatchRequestV1.model_validate(document)


def test_runtime_input_scope_must_match_batch() -> None:
    document = _document("runtime-request-v1.json")
    inputs = document["inputs"]
    assert isinstance(inputs, list) and isinstance(inputs[0], dict)
    inputs[0]["camera_id"] = "synthetic:cctv-002"

    with pytest.raises(ValidationError, match="scope must match"):
        RuntimeBatchRequestV1.model_validate(document)


def test_runtime_deadline_cannot_outlive_input_lease() -> None:
    document = _document("runtime-request-v1.json")
    inputs = document["inputs"]
    assert isinstance(inputs, list) and isinstance(inputs[0], dict)
    document["deadline_at"] = "2026-08-24T12:01:00Z"

    with pytest.raises(ValidationError, match="within every input lease"):
        RuntimeBatchRequestV1.model_validate(document)

    inputs[0]["expires_at"] = "2026-08-24T12:02:00Z"
    with pytest.raises(ValidationError, match="expire within 60 seconds"):
        RuntimeBatchRequestV1.model_validate(document)


@pytest.mark.parametrize(
    "document,message",
    [
        (
            {
                "request_id": "run_11111111111111111111111111111111",
                "status": "succeeded",
                "failure_code": "runtime_internal",
            },
            "successful runtime result",
        ),
        (
            {
                "request_id": "run_11111111111111111111111111111111",
                "status": "failed",
            },
            "requires a safe failure code",
        ),
        (
            {
                "request_id": "run_11111111111111111111111111111111",
                "status": "degraded",
            },
            "requires a safe failure code",
        ),
    ],
)
def test_runtime_result_status_and_failure_code_are_consistent(
    document: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        RuntimeBatchResultV1.model_validate(document)


class _Delegate:
    def __init__(
        self,
        descriptor: RuntimeAdapterDescriptorV1,
        result: RuntimeBatchResultV1 | Exception,
    ) -> None:
        self.descriptor = descriptor
        self.result = result

    def infer(self, request: RuntimeBatchRequestV1) -> RuntimeBatchResultV1:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _configured_descriptor(**changes: object) -> RuntimeAdapterDescriptorV1:
    document = _document("runtime-adapter-unconfigured-v1.json")
    document["configured"] = True
    document.update(changes)
    return RuntimeAdapterDescriptorV1.model_validate(document)


def test_runtime_result_must_reference_the_request_and_its_inputs() -> None:
    request = RuntimeBatchRequestV1.model_validate(_document("runtime-request-v1.json"))
    mismatched = RuntimeBatchResultV1(
        request_id="run_22222222222222222222222222222222",
        status="succeeded",
    )
    with pytest.raises(ValueError, match="request_id must match"):
        validate_runtime_result(request, mismatched)

    foreign_candidate = RuntimeObservationCandidateV1(
        input_id="input_22222222222222222222222222222222",
        class_id="vehicle.car",
        confidence=0.9,
        bbox={"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.2},
    )
    foreign = RuntimeBatchResultV1(
        request_id=request.request_id,
        status="succeeded",
        candidates=[foreign_candidate],
    )
    with pytest.raises(ValueError, match="outside the request"):
        validate_runtime_result(request, foreign)


def test_guarded_runtime_enforces_capability_batch_and_error_boundaries() -> None:
    request_document = _document("runtime-request-v1.json")
    request = RuntimeBatchRequestV1.model_validate(request_document)
    successful = RuntimeBatchResultV1(request_id=request.request_id, status="succeeded")

    unsupported_descriptor = _configured_descriptor(
        supported_capabilities=["plate_ocr"]
    )
    unsupported = GuardedAnalyticsRuntimeAdapter(
        _Delegate(unsupported_descriptor, successful)
    ).infer(request)
    assert unsupported.failure_code == "unsupported_capability"

    limited_descriptor = _configured_descriptor(maximum_batch_size=1)
    inputs = request_document["inputs"]
    assert isinstance(inputs, list) and isinstance(inputs[0], dict)
    second = copy.deepcopy(inputs[0])
    second["input_id"] = "input_22222222222222222222222222222222"
    second["lease_id"] = "lease_22222222222222222222222222222222"
    inputs.append(second)
    oversized = RuntimeBatchRequestV1.model_validate(request_document)
    exhausted = GuardedAnalyticsRuntimeAdapter(
        _Delegate(limited_descriptor, successful)
    ).infer(oversized)
    assert exhausted.failure_code == "resource_exhausted"

    secret_error = RuntimeError("rtsp://user:password@camera/private")
    failed = GuardedAnalyticsRuntimeAdapter(
        _Delegate(limited_descriptor, secret_error)
    ).infer(request)
    assert failed.failure_code == "runtime_internal"
    assert "rtsp" not in failed.model_dump_json()
