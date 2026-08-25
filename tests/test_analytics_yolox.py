from __future__ import annotations

import hashlib
from time import sleep
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import hcam.analytics.yolox as yolox_module

from hcam.analytics.artifacts import (
    AnalyticsArtifactError,
    ArtifactRequirement,
    VerifiedArtifact,
    verify_local_artifact,
)
from hcam.analytics.contracts import SourceFrame
from hcam.analytics.generated import (
    GeneratedFrameLeaseError,
    GeneratedFrameLeaseStore,
    generate_det_r0_frame,
)
from hcam.analytics.runtime import (
    GuardedAnalyticsRuntimeAdapter,
    RuntimeBatchRequestV2,
    RuntimeInputDescriptorV1,
)
from hcam.analytics.yolox import (
    EXPECTED_OUTPUT_SHAPE,
    YoloXOnnxCpuAdapter,
    YoloXRuntimeConfigurationError,
    postprocess_yolox,
    preprocess_generated_frame,
)


def _descriptor(*, expires_at: datetime | None = None) -> RuntimeInputDescriptorV1:
    now = datetime.now(UTC)
    return RuntimeInputDescriptorV1(
        input_id="input_" + "1" * 32,
        lease_id="lease_" + "2" * 32,
        stream_id="str_" + "3" * 32,
        camera_id="synthetic:cctv-001",
        source=SourceFrame(
            sequence=7,
            width=416,
            height=416,
            timestamp_source="generated",
            timestamp_confidence=1,
        ),
        observed_at=now,
        issued_at=now,
        expires_at=expires_at or now + timedelta(seconds=5),
        pixel_format="bgr8",
    )


def _request(descriptor: RuntimeInputDescriptorV1) -> RuntimeBatchRequestV2:
    return RuntimeBatchRequestV2(
        request_id="run_" + "4" * 32,
        assignment_id="ana_" + "5" * 32,
        capability="object_detection",
        stream_id=descriptor.stream_id,
        camera_id=descriptor.camera_id,
        deadline_at=descriptor.issued_at + timedelta(seconds=1),
        inputs=[descriptor],
        minimum_confidence=0.5,
    )


class _FakeSession:
    def __init__(self, output: np.ndarray) -> None:
        self.output = output
        self.fallback_disabled = False
        self.last_input: np.ndarray | None = None

    @staticmethod
    def get_inputs() -> list[SimpleNamespace]:
        return [
            SimpleNamespace(name="images", shape=[1, 3, 416, 416], type="tensor(float)")
        ]

    @staticmethod
    def get_outputs() -> list[SimpleNamespace]:
        return [SimpleNamespace(name="output", shape=[1, 3549, 85])]

    @staticmethod
    def get_providers() -> list[str]:
        return ["CPUExecutionProvider"]

    def disable_fallback(self) -> None:
        self.fallback_disabled = True

    def run(self, _outputs: object, inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
        self.last_input = inputs["images"]
        return [self.output.copy()]


class _CancelableSession(_FakeSession):
    def run(
        self,
        _outputs: object,
        inputs: dict[str, np.ndarray],
        *,
        run_options,
    ) -> list[np.ndarray]:
        self.last_input = inputs["images"]
        while not run_options.terminate:
            sleep(0.001)
        raise RuntimeError("terminated")


class _MemoryFailingSession(_FakeSession):
    def run(self, _outputs: object, inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
        self.last_input = inputs["images"]
        raise MemoryError


def _artifact(tmp_path: Path) -> VerifiedArtifact:
    return VerifiedArtifact(
        artifact_id="test-artifact",
        path=tmp_path / "model.onnx",
        bytes=1,
        sha256="A" * 64,
    )


def test_local_artifact_verification_is_path_confined_and_digest_bound(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    artifact = root / "model.onnx"
    artifact.write_bytes(b"approved-generated-test-artifact")
    requirement = ArtifactRequirement(
        artifact_id="test-artifact",
        filename="model.onnx",
        bytes=artifact.stat().st_size,
        sha256=hashlib.sha256(artifact.read_bytes()).hexdigest().upper(),
    )

    verified = verify_local_artifact(
        root,
        Path("model.onnx"),
        requirement=requirement,
    )
    assert verified.path == artifact.resolve()
    assert verified.sha256 == requirement.sha256

    artifact.write_bytes(b"changed")
    with pytest.raises(AnalyticsArtifactError, match="size is not approved"):
        verify_local_artifact(root, Path("model.onnx"), requirement=requirement)
    with pytest.raises(AnalyticsArtifactError, match="path is not permitted"):
        verify_local_artifact(root, Path("../model.onnx"), requirement=requirement)


def test_reference_generated_frame_and_preprocessing_are_deterministic() -> None:
    first = generate_det_r0_frame()
    second = generate_det_r0_frame()
    changed = generate_det_r0_frame(19)
    tensor = preprocess_generated_frame(first, np)

    assert first.data == second.data
    assert first.sha256 == (
        "1700F4AAF14E57603B72C23757B6F288ADB1A749AA4431C790A22DF985B070E1"
    )
    assert changed.sha256 != first.sha256
    assert tensor.shape == (1, 3, 416, 416)
    assert tensor.dtype == np.float32
    assert hashlib.sha256(tensor.tobytes()).hexdigest().upper() == (
        "44CB193894EDA8AE90D170E4960FE6C656ABEF1E8A71CBF6E65E00B5EE206A5B"
    )


def test_generated_frame_leases_are_bounded_and_consume_once() -> None:
    store = GeneratedFrameLeaseStore(maximum_leases=1)
    descriptor = _descriptor()
    frame = generate_det_r0_frame()
    store.issue(descriptor, frame)

    assert store.active_leases == 1
    assert store.consume(descriptor) is frame
    assert store.active_leases == 0
    with pytest.raises(GeneratedFrameLeaseError) as error:
        store.consume(descriptor)
    assert error.value.code == "input_expired"


def test_postprocessor_decodes_nms_and_maps_approved_taxonomy() -> None:
    output = np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32)
    output[0, 0, 0:4] = [10, 10, np.log(5), np.log(5)]
    output[0, 0, 4] = 0.9
    output[0, 0, 7] = 0.8

    candidates = postprocess_yolox(
        output,
        input_id="input_" + "1" * 32,
        minimum_confidence=0.5,
        source_width=416,
        source_height=416,
        np=np,
    )

    assert len(candidates) == 1
    assert candidates[0].class_id == "vehicle.car"
    assert candidates[0].confidence == pytest.approx(0.72)
    assert candidates[0].bbox.x == pytest.approx(60 / 416)
    assert candidates[0].bbox.width == pytest.approx(40 / 416)


@pytest.mark.parametrize(
    "source_class,expected_class",
    (
        (0, "object.person"),
        (1, "vehicle.bicycle"),
        (2, "vehicle.car"),
        (3, "vehicle.motorcycle"),
        (5, "vehicle.bus"),
        (7, "vehicle.truck"),
        (4, "object.unknown"),
    ),
)
def test_postprocessor_maps_every_approved_tier_a_class(
    source_class: int,
    expected_class: str,
) -> None:
    output = np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32)
    output[0, 0, 0:4] = [10, 10, np.log(5), np.log(5)]
    output[0, 0, 4] = 0.9
    output[0, 0, 5 + source_class] = 0.8

    candidates = postprocess_yolox(
        output,
        input_id="input_" + "1" * 32,
        minimum_confidence=0.5,
        source_width=416,
        source_height=416,
        np=np,
    )

    assert candidates[0].class_id == expected_class


def test_cpu_adapter_consumes_generated_lease_and_rejects_replay(
    tmp_path: Path,
) -> None:
    output = np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32)
    output[0, 0, 0:4] = [10, 10, np.log(5), np.log(5)]
    output[0, 0, 4] = 0.9
    output[0, 0, 5] = 0.8
    session = _FakeSession(output)
    store = GeneratedFrameLeaseStore()
    descriptor = _descriptor()
    store.issue(descriptor, generate_det_r0_frame())
    adapter = GuardedAnalyticsRuntimeAdapter(
        YoloXOnnxCpuAdapter(
            artifact=_artifact(tmp_path),
            frame_resolver=store,
            session=session,
            np=np,
            expected_reference_output_sha256=None,
        )
    )

    result = adapter.infer(_request(descriptor))
    replay = adapter.infer(_request(descriptor))

    assert result.status == "succeeded"
    assert result.candidates[0].class_id == "object.person"
    assert session.fallback_disabled is True
    assert session.last_input is not None
    assert replay.status == "failed"
    assert replay.failure_code == "input_expired"


def test_cpu_adapter_rejects_provider_fallback(tmp_path: Path) -> None:
    session = _FakeSession(np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32))
    session.get_providers = lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"]

    with pytest.raises(YoloXRuntimeConfigurationError, match="not approved"):
        YoloXOnnxCpuAdapter(
            artifact=_artifact(tmp_path),
            frame_resolver=GeneratedFrameLeaseStore(),
            session=session,
            np=np,
            expected_reference_output_sha256=None,
        )


def test_cpu_adapter_terminates_inference_at_approved_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(yolox_module, "MAXIMUM_RUNTIME_MS", 10)
    session = _CancelableSession(np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32))
    store = GeneratedFrameLeaseStore()
    descriptor = _descriptor()
    store.issue(descriptor, generate_det_r0_frame())
    adapter = YoloXOnnxCpuAdapter(
        artifact=_artifact(tmp_path),
        frame_resolver=store,
        session=session,
        np=np,
        expected_reference_output_sha256=None,
        run_options_factory=lambda: SimpleNamespace(terminate=False),
    )

    result = adapter.infer(_request(descriptor))

    assert result.status == "failed"
    assert result.failure_code == "deadline_exceeded"
    assert store.active_leases == 0


def test_cpu_adapter_maps_memory_and_malformed_output_to_safe_codes(
    tmp_path: Path,
) -> None:
    memory_store = GeneratedFrameLeaseStore()
    memory_descriptor = _descriptor()
    memory_store.issue(memory_descriptor, generate_det_r0_frame())
    memory_adapter = YoloXOnnxCpuAdapter(
        artifact=_artifact(tmp_path),
        frame_resolver=memory_store,
        session=_MemoryFailingSession(
            np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32)
        ),
        np=np,
        expected_reference_output_sha256=None,
    )
    malformed_store = GeneratedFrameLeaseStore()
    malformed_descriptor = _descriptor()
    malformed_store.issue(malformed_descriptor, generate_det_r0_frame())
    malformed_adapter = YoloXOnnxCpuAdapter(
        artifact=_artifact(tmp_path),
        frame_resolver=malformed_store,
        session=_FakeSession(np.zeros((1, 1, 1), dtype=np.float32)),
        np=np,
        expected_reference_output_sha256=None,
    )

    memory = memory_adapter.infer(_request(memory_descriptor))
    malformed = malformed_adapter.infer(_request(malformed_descriptor))

    assert memory.failure_code == "resource_exhausted"
    assert malformed.failure_code == "runtime_internal"


def test_cpu_adapter_fails_closed_above_resident_memory_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        yolox_module,
        "_resident_memory_bytes",
        lambda: yolox_module.MAXIMUM_RESIDENT_MEMORY_BYTES + 1,
    )
    store = GeneratedFrameLeaseStore()
    descriptor = _descriptor()
    store.issue(descriptor, generate_det_r0_frame())
    session = _FakeSession(np.zeros(EXPECTED_OUTPUT_SHAPE, dtype=np.float32))
    adapter = YoloXOnnxCpuAdapter(
        artifact=_artifact(tmp_path),
        frame_resolver=store,
        session=session,
        np=np,
        expected_reference_output_sha256=None,
    )

    result = adapter.infer(_request(descriptor))

    assert result.failure_code == "resource_exhausted"
    assert session.last_input is None
