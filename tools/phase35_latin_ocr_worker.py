#!/usr/bin/env python3
"""Isolated exact PaddleOCR worker for generated-only P3.5 W5 evaluation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
RUNTIME_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5-runtime")
RESULT_PREFIX = "HCAM_P35_W5_RESULT="
ERROR_PREFIX = "HCAM_P35_W5_ERROR="

_NETWORK_ATTEMPTS: list[str] = []


def _deny_network(operation: str) -> None:
    _NETWORK_ATTEMPTS.append(operation)
    raise RuntimeError("network access denied by H-CAM P3.5 W5 guard")


class _DeniedSocket(socket.socket):
    def __new__(cls, *args: object, **kwargs: object) -> _DeniedSocket:
        del args, kwargs
        _deny_network("socket")


socket.socket = _DeniedSocket  # type: ignore[assignment]
socket.create_connection = lambda *args, **kwargs: _deny_network("connect")  # type: ignore[assignment]
socket.getaddrinfo = lambda *args, **kwargs: _deny_network("resolve")  # type: ignore[assignment]

sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr.contracts import (  # noqa: E402
    LatinOcrCandidateEvaluationV1,
    SyntheticAnprExecutionPolicyV1,
)
from hcam.analytics.anpr.generator import synthetic_corpus_plan_fixture  # noqa: E402
from hcam.analytics.anpr.ocr import (  # noqa: E402
    GeneratedLatinOcrCropV1,
    RawLatinOcrEngineResultV1,
    evaluate_generated_latin_candidate,
)


_PROFILES = {
    "OCR-L0": {
        "directory": "OCR-L0/PP-OCRv6_small_rec_infer",
        "model_name": "PP-OCRv6_small_rec",
        "inventory": "sha256:692cd53d9fb002538e81c9e0b91a6636ade0a82dc9a914809c3598cec686bf84",
        "sizes": {
            "inference.json": 208_004,
            "inference.pdiparams": 21_074_618,
            "inference.yml": 150_579,
        },
    },
    "OCR-L1": {
        "directory": "OCR-L1/PP-OCRv6_medium_rec_infer",
        "model_name": "PP-OCRv6_medium_rec",
        "inventory": "sha256:7a12028567618504b96caf997e7afdf77ceea54dbab142c09299e3844d53fb6f",
        "sizes": {
            "inference.json": 221_814,
            "inference.pdiparams": 76_465_087,
            "inference.yml": 150_580,
        },
    },
}


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _verify_runtime() -> None:
    expected = {
        "Pillow": "12.3.0",
        "paddleocr": "3.7.0",
        "paddlepaddle": "3.3.1",
        "regex": "2026.7.19",
    }
    observed = {name: importlib.metadata.version(name) for name in expected}
    if observed != expected or sys.version_info[:3] != (3, 12, 13):
        raise RuntimeError("exact runtime mismatch")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _model_inventory(model_dir: Path, profile: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    observed: set[str] = set()
    for path in model_dir.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("model inventory contains a symlink")
        if path.is_dir():
            raise RuntimeError("model inventory contains an extra directory")
        if not path.is_file():
            continue
        name = path.relative_to(model_dir).as_posix()
        observed.add(name)
        expected_size = profile["sizes"].get(name)
        if expected_size is None or path.stat().st_size != expected_size:
            raise RuntimeError("model inventory mismatch")
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\0")
    if observed != set(profile["sizes"]):
        raise RuntimeError("model inventory mismatch")
    return f"sha256:{digest.hexdigest()}"


class ExactPaddleLatinOcrAdapter:
    def __init__(
        self,
        *,
        candidate_id: str,
        model_dir: Path,
        extracted_inventory_sha256: str,
    ) -> None:
        profile = _PROFILES[candidate_id]
        resolved_runtime = RUNTIME_ROOT.resolve(strict=True)
        expected_model = (resolved_runtime / "models" / profile["directory"]).resolve(
            strict=True
        )
        resolved_model = model_dir.resolve(strict=True)
        if (
            resolved_model != expected_model
            or not _inside(resolved_model, resolved_runtime / "models")
            or model_dir.is_symlink()
        ):
            raise RuntimeError("model directory boundary mismatch")
        if not all(
            (resolved_model / name).is_file()
            and not (resolved_model / name).is_symlink()
            for name in ("inference.json", "inference.pdiparams", "inference.yml")
        ):
            raise RuntimeError("exact model inventory is incomplete")
        observed_inventory = _model_inventory(resolved_model, profile)
        if (
            extracted_inventory_sha256 != profile["inventory"]
            or observed_inventory != profile["inventory"]
        ):
            raise RuntimeError("exact model inventory digest mismatch")

        import numpy as np
        from paddleocr import TextRecognition

        self._numpy = np
        self.candidate_id = candidate_id
        self.extracted_inventory_sha256 = extracted_inventory_sha256
        self._predictor = TextRecognition(
            model_name=profile["model_name"],
            model_dir=str(resolved_model),
            device="cpu",
            engine="paddle_static",
            enable_hpi=False,
            use_tensorrt=False,
            enable_cinn=False,
            cpu_threads=1,
        )

    def recognize(
        self, crop: GeneratedLatinOcrCropV1
    ) -> RawLatinOcrEngineResultV1:
        image = self._numpy.frombuffer(crop.bgr_bytes, dtype=self._numpy.uint8).reshape(
            (crop.height, crop.width, 3)
        )
        results = self._predictor.predict(input=image, batch_size=1)
        if not isinstance(results, list) or len(results) != 1:
            return RawLatinOcrEngineResultV1(None, None)
        result: Any = results[0]
        try:
            raw_text = result["rec_text"]
            raw_confidence = result["rec_score"]
        except (KeyError, TypeError):
            return RawLatinOcrEngineResultV1(None, None)
        return RawLatinOcrEngineResultV1(raw_text, raw_confidence)

    def close(self) -> None:
        self._predictor.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=sorted(_PROFILES), required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument(
        "--inventory-sha256",
        required=True,
    )
    parser.add_argument("--sample-count", type=int, default=12)
    return parser.parse_args(argv)


def _run(args: argparse.Namespace) -> LatinOcrCandidateEvaluationV1:
    _verify_runtime()
    if not (
        len(args.inventory_sha256) == 71
        and args.inventory_sha256.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in args.inventory_sha256[7:])
    ):
        raise RuntimeError("inventory digest is invalid")
    adapter = ExactPaddleLatinOcrAdapter(
        candidate_id=args.candidate,
        model_dir=args.model_dir,
        extracted_inventory_sha256=args.inventory_sha256,
    )
    try:
        evaluation = evaluate_generated_latin_candidate(
            synthetic_corpus_plan_fixture(),
            adapter,
            policy=SyntheticAnprExecutionPolicyV1(enabled=True, environment="test"),
            sample_count=args.sample_count,
            replay_runs=20,
        )
    finally:
        adapter.close()
    document = evaluation.model_dump(mode="json")
    document["network_attempt_count"] = len(_NETWORK_ATTEMPTS)
    return LatinOcrCandidateEvaluationV1.model_validate(document)


def main(argv: list[str] | None = None) -> int:
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "1"
    args = parse_args(argv)
    try:
        evaluation = _run(args)
    except Exception:
        print(ERROR_PREFIX + "worker_failed", file=sys.stderr)
        return 1
    print(
        RESULT_PREFIX
        + json.dumps(
            evaluation.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
