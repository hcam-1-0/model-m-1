from __future__ import annotations

import hashlib
import sys
import ctypes
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from threading import Timer
from time import perf_counter
from typing import Any

from hcam.analytics.artifacts import VerifiedArtifact, verify_local_artifact
from hcam.analytics.generated import (
    GeneratedFrame,
    GeneratedFrameLeaseError,
    RuntimeFrameResolver,
    generate_det_r0_frame,
)
from hcam.analytics.runtime import (
    RuntimeAdapterDescriptorV1,
    RuntimeBatchRequest,
    RuntimeBatchRequestV2,
    RuntimeBatchResultV1,
    RuntimeObservationCandidateV1,
    failed_runtime_result,
)
from hcam.analytics.contracts import NormalizedBoundingBox


EXPECTED_REFERENCE_OUTPUT_SHA256 = (
    "3562559CAD2DCD1AD0A15C74E3425A371B1725BA5574CDADF5FDB375FE3A519C"
)
EXPECTED_INPUT_SHAPE = [1, 3, 416, 416]
EXPECTED_OUTPUT_SHAPE = [1, 3549, 85]
MAXIMUM_CANDIDATES = 300
MAXIMUM_RUNTIME_MS = 1_000
MAXIMUM_RESIDENT_MEMORY_BYTES = 1_073_741_824
NMS_IOU_THRESHOLD = 0.45
APPROVED_CLASS_MAP = {
    0: "object.person",
    1: "vehicle.bicycle",
    2: "vehicle.car",
    3: "vehicle.motorcycle",
    5: "vehicle.bus",
    7: "vehicle.truck",
}


def _resident_memory_bytes() -> int | None:
    try:
        if sys.platform == "win32":

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            get_current_process = ctypes.windll.kernel32.GetCurrentProcess
            get_current_process.restype = ctypes.c_void_p
            get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_process_memory_info.argtypes = (
                ctypes.c_void_p,
                ctypes.POINTER(ProcessMemoryCounters),
                ctypes.c_ulong,
            )
            get_process_memory_info.restype = ctypes.c_int
            process = get_current_process()
            if not get_process_memory_info(
                process,
                ctypes.byref(counters),
                counters.cb,
            ):
                return None
            return int(counters.WorkingSetSize)
        import resource

        usage = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return usage if sys.platform == "darwin" else usage * 1_024
    except (AttributeError, ImportError, OSError, ValueError):
        return None


class YoloXRuntimeConfigurationError(RuntimeError):
    """A safe local-runtime configuration error without artifact details."""


def _shape(value: object) -> list[int | str | None]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item if isinstance(item, (int, str)) else None for item in value]


def _require_runtime_versions() -> None:
    expected = {
        "numpy": "2.5.2",
        "onnx": "1.22.0",
        "onnxruntime": "1.29.0",
    }
    try:
        observed = {name: version(name) for name in expected}
    except PackageNotFoundError as exc:
        raise YoloXRuntimeConfigurationError(
            "approved analytics runtime dependencies are unavailable"
        ) from exc
    if observed != expected:
        raise YoloXRuntimeConfigurationError(
            "analytics runtime dependency versions are not approved"
        )
    if sys.version_info[:3] != (3, 14, 6):
        raise YoloXRuntimeConfigurationError(
            "analytics runtime Python version is not approved"
        )


def _verify_onnx_model(onnx: Any, artifact: VerifiedArtifact) -> None:
    try:
        model = onnx.load(str(artifact.path), load_external_data=False)
        onnx.checker.check_model(model, full_check=True)
    except Exception as exc:
        raise YoloXRuntimeConfigurationError(
            "analytics model failed ONNX validation"
        ) from exc
    if any(item.external_data for item in model.graph.initializer):
        raise YoloXRuntimeConfigurationError("external ONNX model data is prohibited")
    opsets = {
        str(item.domain or "ai.onnx"): item.version for item in model.opset_import
    }
    if model.ir_version != 6 or opsets != {"ai.onnx": 11}:
        raise YoloXRuntimeConfigurationError("analytics ONNX contract is not approved")


def preprocess_generated_frame(frame: GeneratedFrame, np: Any) -> Any:
    try:
        image = np.frombuffer(frame.data, dtype=np.uint8).reshape(
            frame.height,
            frame.width,
            3,
        )
        tensor = np.ascontiguousarray(image.transpose(2, 0, 1), dtype=np.float32)
    except Exception as exc:
        raise ValueError("generated frame preprocessing failed") from exc
    return tensor[None, :, :, :]


def _decode_predictions(output: Any, np: Any) -> Any:
    predictions = np.array(output, dtype=np.float32, copy=True)
    grids = []
    expanded_strides = []
    for stride in (8, 16, 32):
        hsize = 416 // stride
        wsize = 416 // stride
        xv, yv = np.meshgrid(np.arange(wsize), np.arange(hsize))
        grid = np.stack((xv, yv), axis=2).reshape(1, -1, 2)
        grids.append(grid)
        expanded_strides.append(np.full((*grid.shape[:2], 1), stride))
    grid = np.concatenate(grids, axis=1)
    strides = np.concatenate(expanded_strides, axis=1)
    predictions[..., :2] = (predictions[..., :2] + grid) * strides
    predictions[..., 2:4] = np.exp(predictions[..., 2:4]) * strides
    return predictions[0]


def _nms(boxes: Any, scores: Any, np: Any) -> list[int]:
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size > 0 and len(keep) < MAXIMUM_CANDIDATES:
        index = int(order[0])
        keep.append(index)
        xx1 = np.maximum(x1[index], x1[order[1:]])
        yy1 = np.maximum(y1[index], y1[order[1:]])
        xx2 = np.minimum(x2[index], x2[order[1:]])
        yy2 = np.minimum(y2[index], y2[order[1:]])
        width = np.maximum(0.0, xx2 - xx1 + 1)
        height = np.maximum(0.0, yy2 - yy1 + 1)
        intersection = width * height
        overlap = intersection / (areas[index] + areas[order[1:]] - intersection)
        remaining = np.where(overlap <= NMS_IOU_THRESHOLD)[0]
        order = order[remaining + 1]
    return keep


def postprocess_yolox(
    output: Any,
    *,
    input_id: str,
    minimum_confidence: float,
    source_width: int,
    source_height: int,
    np: Any,
) -> list[RuntimeObservationCandidateV1]:
    if list(output.shape) != EXPECTED_OUTPUT_SHAPE or not np.isfinite(output).all():
        raise ValueError("analytics runtime output contract failed")
    predictions = _decode_predictions(output, np)
    boxes = predictions[:, :4]
    scores = predictions[:, 4:5] * predictions[:, 5:]
    class_indexes = scores.argmax(axis=1)
    class_scores = scores[np.arange(len(class_indexes)), class_indexes]
    valid = class_scores > minimum_confidence
    if not valid.any():
        return []
    boxes = boxes[valid]
    class_scores = class_scores[valid]
    class_indexes = class_indexes[valid]

    boxes_xyxy = np.empty_like(boxes)
    boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.0
    boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.0
    boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.0
    boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.0
    boxes_xyxy[:, 0::2] = boxes_xyxy[:, 0::2].clip(0, source_width)
    boxes_xyxy[:, 1::2] = boxes_xyxy[:, 1::2].clip(0, source_height)

    candidates: list[RuntimeObservationCandidateV1] = []
    for index in _nms(boxes_xyxy, class_scores, np):
        x1, y1, x2, y2 = (float(value) for value in boxes_xyxy[index])
        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0:
            continue
        normalized_x = min(max(x1 / source_width, 0.0), 1.0)
        normalized_y = min(max(y1 / source_height, 0.0), 1.0)
        normalized_width = min(width / source_width, 1.0 - normalized_x)
        normalized_height = min(height / source_height, 1.0 - normalized_y)
        if normalized_width <= 0 or normalized_height <= 0:
            continue
        candidates.append(
            RuntimeObservationCandidateV1(
                input_id=input_id,
                class_id=APPROVED_CLASS_MAP.get(
                    int(class_indexes[index]),
                    "object.unknown",
                ),
                confidence=float(class_scores[index]),
                bbox=NormalizedBoundingBox(
                    x=normalized_x,
                    y=normalized_y,
                    width=normalized_width,
                    height=normalized_height,
                ),
            )
        )
        if len(candidates) >= MAXIMUM_CANDIDATES:
            break
    return candidates


class YoloXOnnxCpuAdapter:
    def __init__(
        self,
        *,
        artifact: VerifiedArtifact,
        frame_resolver: RuntimeFrameResolver,
        session: Any,
        np: Any,
        expected_reference_output_sha256: str | None,
        run_options_factory: Any | None = None,
    ) -> None:
        self._artifact = artifact
        self._frame_resolver = frame_resolver
        self._session = session
        self._np = np
        self._run_options_factory = run_options_factory
        self._descriptor = RuntimeAdapterDescriptorV1(
            adapter_id="hcam.yolox_tiny.onnxruntime_cpu",
            adapter_version=f"sha256:{artifact.sha256.lower()}",
            supported_capabilities=["object_detection"],
            maximum_batch_size=1,
            configured=True,
        )
        self._validate_session()
        if expected_reference_output_sha256 is not None:
            self._run_reference_self_test(expected_reference_output_sha256)

    @property
    def descriptor(self) -> RuntimeAdapterDescriptorV1:
        return self._descriptor

    def _validate_session(self) -> None:
        inputs = self._session.get_inputs()
        outputs = self._session.get_outputs()
        if (
            self._session.get_providers() != ["CPUExecutionProvider"]
            or len(inputs) != 1
            or inputs[0].name != "images"
            or _shape(inputs[0].shape) != EXPECTED_INPUT_SHAPE
            or inputs[0].type != "tensor(float)"
            or len(outputs) != 1
            or outputs[0].name != "output"
            or _shape(outputs[0].shape) != EXPECTED_OUTPUT_SHAPE
        ):
            raise YoloXRuntimeConfigurationError(
                "analytics runtime session contract is not approved"
            )
        self._session.disable_fallback()

    def _run_reference_self_test(self, expected_sha256: str) -> None:
        tensor = preprocess_generated_frame(generate_det_r0_frame(), self._np)
        try:
            outputs = self._session.run(None, {"images": tensor})
        except Exception as exc:
            raise YoloXRuntimeConfigurationError(
                "analytics runtime reference self-test failed"
            ) from exc
        if len(outputs) != 1 or list(outputs[0].shape) != EXPECTED_OUTPUT_SHAPE:
            raise YoloXRuntimeConfigurationError(
                "analytics runtime reference output is invalid"
            )
        digest = hashlib.sha256(outputs[0].tobytes()).hexdigest().upper()
        if digest != expected_sha256:
            raise YoloXRuntimeConfigurationError(
                "analytics runtime reference output digest changed"
            )

    def infer(self, request: RuntimeBatchRequest) -> RuntimeBatchResultV1:
        if not isinstance(request, RuntimeBatchRequestV2) or len(request.inputs) != 1:
            return failed_runtime_result(request, "invalid_input")
        if datetime.now(UTC) >= request.deadline_at:
            return failed_runtime_result(request, "deadline_exceeded")
        resident_memory = _resident_memory_bytes()
        if resident_memory is None or resident_memory > MAXIMUM_RESIDENT_MEMORY_BYTES:
            return failed_runtime_result(request, "resource_exhausted")
        descriptor = request.inputs[0]
        if (
            descriptor.pixel_format != "bgr8"
            or descriptor.source.width != 416
            or descriptor.source.height != 416
            or descriptor.source.timestamp_source != "generated"
        ):
            return failed_runtime_result(request, "invalid_input")
        try:
            frame = self._frame_resolver.consume(descriptor)
            tensor = preprocess_generated_frame(frame, self._np)
        except GeneratedFrameLeaseError as exc:
            return failed_runtime_result(request, exc.code)
        except (ValueError, MemoryError):
            return failed_runtime_result(request, "invalid_input")

        started = perf_counter()
        run_options = None
        deadline_timer = None
        if self._run_options_factory is not None:
            run_options = self._run_options_factory()
            remaining_seconds = max(
                0.001,
                min(
                    MAXIMUM_RUNTIME_MS / 1_000,
                    (request.deadline_at - datetime.now(UTC)).total_seconds(),
                ),
            )
            deadline_timer = Timer(
                remaining_seconds,
                setattr,
                args=(run_options, "terminate", True),
            )
            deadline_timer.daemon = True
            deadline_timer.start()
        try:
            if run_options is None:
                outputs = self._session.run(None, {"images": tensor})
            else:
                outputs = self._session.run(
                    None,
                    {"images": tensor},
                    run_options=run_options,
                )
        except MemoryError:
            return failed_runtime_result(request, "resource_exhausted")
        except Exception:
            if (run_options is not None and run_options.terminate) or datetime.now(
                UTC
            ) >= request.deadline_at:
                return failed_runtime_result(request, "deadline_exceeded")
            return failed_runtime_result(request, "runtime_internal")
        finally:
            if deadline_timer is not None:
                deadline_timer.cancel()
        duration_ms = (perf_counter() - started) * 1_000
        resident_memory = _resident_memory_bytes()
        if resident_memory is None or resident_memory > MAXIMUM_RESIDENT_MEMORY_BYTES:
            return failed_runtime_result(request, "resource_exhausted")
        if duration_ms > MAXIMUM_RUNTIME_MS or datetime.now(UTC) > request.deadline_at:
            return failed_runtime_result(request, "deadline_exceeded")
        if len(outputs) != 1:
            return failed_runtime_result(request, "runtime_internal")
        try:
            candidates = postprocess_yolox(
                outputs[0],
                input_id=descriptor.input_id,
                minimum_confidence=request.minimum_confidence,
                source_width=descriptor.source.width,
                source_height=descriptor.source.height,
                np=self._np,
            )
        except (ValueError, FloatingPointError, MemoryError):
            return failed_runtime_result(request, "runtime_internal")
        return RuntimeBatchResultV1(
            request_id=request.request_id,
            status="succeeded",
            candidates=candidates,
        )


def build_yolox_cpu_adapter(
    *,
    artifact_root: Path,
    relative_model_path: Path,
    frame_resolver: RuntimeFrameResolver,
) -> YoloXOnnxCpuAdapter:
    _require_runtime_versions()
    artifact = verify_local_artifact(artifact_root, relative_model_path)
    try:
        import numpy as np
        import onnx
        import onnxruntime as ort
    except ImportError as exc:
        raise YoloXRuntimeConfigurationError(
            "approved analytics runtime dependencies are unavailable"
        ) from exc
    _verify_onnx_model(onnx, artifact)
    options = ort.SessionOptions()
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    try:
        session = ort.InferenceSession(
            str(artifact.path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
    except Exception as exc:
        raise YoloXRuntimeConfigurationError(
            "analytics runtime session could not be created"
        ) from exc
    return YoloXOnnxCpuAdapter(
        artifact=artifact,
        frame_resolver=frame_resolver,
        session=session,
        np=np,
        expected_reference_output_sha256=EXPECTED_REFERENCE_OUTPUT_SHA256,
        run_options_factory=ort.RunOptions,
    )
