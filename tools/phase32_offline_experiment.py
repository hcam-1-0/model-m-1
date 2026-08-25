#!/usr/bin/env python3
"""Run a bounded offline structural inference experiment on a quarantined model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import statistics
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterator


DEFAULT_RESEARCH_ROOT = Path(
    os.environ.get(
        "HCAM_P32_RESEARCH_ROOT",
        r"F:\h cam\research-cache\phase-3\p3-2",
    )
)
DEFAULT_ARTIFACT_ID = "DET-R0-ONNX-UPSTREAM-0.1.1RC0"


class ExperimentError(RuntimeError):
    """An offline experiment boundary or runtime failure."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExperimentError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verified_artifact(root: Path, artifact_id: str) -> tuple[Path, dict[str, Any]]:
    root = root.resolve(strict=True)
    receipt_path = root / "receipts" / f"{artifact_id}.json"
    if receipt_path.is_symlink():
        raise ExperimentError("artifact receipt cannot be a symlink")
    receipt = _read_json(receipt_path)
    relative = Path(str(receipt.get("local_path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise ExperimentError("receipt contains an unsafe artifact path")
    unresolved_artifact = root / relative
    if unresolved_artifact.is_symlink():
        raise ExperimentError("artifact cannot be a symlink")
    artifact = unresolved_artifact.resolve(strict=True)
    try:
        artifact.relative_to(root)
    except ValueError as exc:
        raise ExperimentError("artifact escapes the research root") from exc
    if not artifact.is_file():
        raise ExperimentError("artifact must be a regular non-symlink file")
    if artifact.stat().st_size != receipt.get("bytes"):
        raise ExperimentError("artifact size does not match its receipt")
    if _sha256(artifact) != receipt.get("sha256"):
        raise ExperimentError("artifact SHA-256 does not match its receipt")
    return artifact, receipt


@contextmanager
def deny_python_network() -> Iterator[None]:
    original_socket = socket.socket
    original_create_connection = socket.create_connection

    class OfflineSocket(original_socket):
        def connect(self, address: object) -> None:
            raise OSError("network disabled by P3.2 offline experiment policy")

        def connect_ex(self, address: object) -> int:
            raise OSError("network disabled by P3.2 offline experiment policy")

    def denied(*args: object, **kwargs: object) -> None:
        raise OSError("network disabled by P3.2 offline experiment policy")

    socket.socket = OfflineSocket
    socket.create_connection = denied
    try:
        yield
    finally:
        socket.socket = original_socket
        socket.create_connection = original_create_connection


def _shape(value: object) -> list[int | str | None]:
    return [item if isinstance(item, (int, str)) else None for item in value]


def run_experiment(root: Path, artifact_id: str, runs: int) -> dict[str, Any]:
    if not 1 <= runs <= 10:
        raise ExperimentError("runs must be between 1 and 10")
    artifact, receipt = verified_artifact(root, artifact_id)
    try:
        import numpy as np
        import onnx
        import onnxruntime as ort
    except ImportError as exc:
        raise ExperimentError(
            "onnx, onnxruntime, and numpy are required in the isolated research environment"
        ) from exc

    model = onnx.load(str(artifact), load_external_data=False)
    onnx.checker.check_model(model, full_check=True)
    if any(initializer.external_data for initializer in model.graph.initializer):
        raise ExperimentError("external model data is prohibited")
    opsets = {str(item.domain or "ai.onnx"): item.version for item in model.opset_import}

    options = ort.SessionOptions()
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    with deny_python_network():
        session = ort.InferenceSession(
            str(artifact),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        session.disable_fallback()
        inputs = session.get_inputs()
        outputs = session.get_outputs()
        if len(inputs) != 1:
            raise ExperimentError("research runner requires exactly one model input")
        input_meta = inputs[0]
        input_shape = _shape(input_meta.shape)
        if input_shape != [1, 3, 416, 416] or input_meta.type != "tensor(float)":
            raise ExperimentError("model input contract is not [1,3,416,416] float32")

        generated = np.full((1, 3, 416, 416), 114.0, dtype=np.float32)
        generated[:, 0, 104:312, 156:260] = 220.0
        generated[:, 1, 150:260, 80:336] = 64.0
        generated[:, 2, 208:312, 104:312] = 180.0
        durations_ms: list[float] = []
        result_arrays: list[Any] = []
        for _ in range(runs):
            started = time.perf_counter()
            result_arrays = session.run(None, {input_meta.name: generated})
            durations_ms.append((time.perf_counter() - started) * 1000)

    output_records = []
    for metadata, array in zip(outputs, result_arrays, strict=True):
        if not np.isfinite(array).all():
            raise ExperimentError("model output contains non-finite values")
        output_records.append(
            {
                "declared_shape": _shape(metadata.shape),
                "dtype": str(array.dtype),
                "maximum": float(array.max()),
                "minimum": float(array.min()),
                "name": metadata.name,
                "observed_shape": list(array.shape),
                "sha256": hashlib.sha256(array.tobytes()).hexdigest().upper(),
            }
        )

    return {
        "artifact": {
            "artifact_id": artifact_id,
            "bytes": receipt["bytes"],
            "sha256": receipt["sha256"],
        },
        "authorization_id": receipt["authorization_id"],
        "claims": {
            "accuracy": "not_measured",
            "deployment_readiness": "not_assessed",
            "result": "structural_cpu_inference_smoke_only",
        },
        "environment": {
            "machine": platform.node(),
            "numpy": version("numpy"),
            "onnx": version("onnx"),
            "onnxruntime": version("onnxruntime"),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "experiment_id": "P3.2-EXP-DET-R0-GENERATED-001",
        "input": {
            "generation": "deterministic_programmatic_rgb_blocks_no_media_source",
            "name": input_meta.name,
            "shape": input_shape,
            "type": input_meta.type,
        },
        "model": {
            "graph_name": model.graph.name,
            "ir_version": model.ir_version,
            "opsets": opsets,
        },
        "network_policy": "python_socket_access_denied_during_session_and_inference",
        "outputs": output_records,
        "runtime": {
            "execution_providers": session.get_providers(),
            "mean_ms": statistics.fmean(durations_ms),
            "runs": runs,
            "samples_ms": durations_ms,
        },
        "status": "completed_research_only",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded offline P3.2 research experiment."
    )
    parser.add_argument("--artifact-id", default=DEFAULT_ARTIFACT_ID)
    parser.add_argument("--root", type=Path, default=DEFAULT_RESEARCH_ROOT)
    parser.add_argument("--runs", type=int, default=3)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_experiment(args.root, args.artifact_id, args.runs)
        result["completed_at"] = datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        output_dir = args.root.resolve(strict=True) / "experiments"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"{result['experiment_id']}.json"
        output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (ExperimentError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"offline experiment failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
