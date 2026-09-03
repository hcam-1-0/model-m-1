#!/usr/bin/env python3
"""Isolated generated-only P3.5 W6 Devanagari OCR and font worker."""

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
ARTIFACT_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5\artifacts")
RUNTIME_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5-runtime")
RESULT_PREFIX = "HCAM_P35_W6_RESULT="
ERROR_PREFIX = "HCAM_P35_W6_ERROR="

MODEL_INVENTORY = (
    "sha256:e7f6b0b7cf6e937e56540ba5254d6aed9a1958e5b3bca3a3e7c41b29673a2cb6"
)
MODEL_MEMBERS = {
    "export_result.json": 114,
    "inference.json": 217_712,
    "inference.pdiparams": 7_836_203,
    "inference.yml": 5_027,
}
FONT_PATHS = {
    "FONT-D0": ARTIFACT_ROOT
    / "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED"
    / "NotoSansDevanagari-wdth-wght.ttf",
    "FONT-G0": ARTIFACT_ROOT
    / "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED"
    / "NotoSansGujarati-wdth-wght.ttf",
}
FONT_SHA256 = {
    "FONT-D0": "9CE7B04F60E363D8870E5997744CF85CF69D38A4D7D129D364D92A3B14B461D7",
    "FONT-G0": "9901D8552F1DD5D2C50DBD4CAA6F6E174E74E8264F06594AB259AE6E7B1AC428",
}

_NETWORK_ATTEMPTS: list[str] = []


def _deny_network(operation: str) -> None:
    _NETWORK_ATTEMPTS.append(operation)
    raise RuntimeError("network access denied by H-CAM P3.5 W6 guard")


class _DeniedSocket(socket.socket):
    def __new__(cls, *args: object, **kwargs: object) -> _DeniedSocket:
        del args, kwargs
        _deny_network("socket")


socket.socket = _DeniedSocket  # type: ignore[assignment]
socket.create_connection = lambda *args, **kwargs: _deny_network("connect")  # type: ignore[assignment]
socket.getaddrinfo = lambda *args, **kwargs: _deny_network("resolve")  # type: ignore[assignment]

sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr.auxiliary import (  # noqa: E402
    EphemeralAuxiliarySampleV1,
    GeneratedAuxiliaryCropV1,
    RawAuxiliaryOcrEngineResultV1,
    RawRenderedAuxiliaryPixelsV1,
    evaluate_generated_auxiliary_font,
    evaluate_generated_devanagari_candidate,
)
from hcam.analytics.anpr.contracts import (  # noqa: E402
    AuxiliaryScriptGeneratedEvaluationV1,
    SyntheticAnprExecutionPolicyV1,
)


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _verify_runtime() -> None:
    expected = {
        "Pillow": "12.3.0",
        "paddleocr": "3.7.0",
        "paddlepaddle": "3.3.1",
        "regex": "2026.7.19",
    }
    observed = {name: importlib.metadata.version(name) for name in expected}
    if observed != expected or sys.version_info[:3] != (3, 12, 13):
        raise RuntimeError("exact W6 runtime mismatch")


def _model_inventory(model_dir: Path) -> str:
    digest = hashlib.sha256()
    observed: set[str] = set()
    for path in model_dir.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("W6 model inventory contains a symlink")
        if path.is_dir():
            raise RuntimeError("W6 model inventory contains an extra directory")
        if not path.is_file():
            continue
        name = path.relative_to(model_dir).as_posix()
        observed.add(name)
        expected_size = MODEL_MEMBERS.get(name)
        if expected_size is None or path.stat().st_size != expected_size:
            raise RuntimeError("W6 model inventory mismatch")
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\0")
    if observed != set(MODEL_MEMBERS):
        raise RuntimeError("W6 model inventory mismatch")
    return f"sha256:{digest.hexdigest()}"


class ExactPillowAuxiliaryRenderer:
    shaping_backend = "basic_freetype_no_raqm"

    def __init__(self, *, candidate_id: str, font_path: Path) -> None:
        from PIL import ImageFont, features

        if candidate_id not in FONT_PATHS:
            raise RuntimeError("unapproved W6 font candidate")
        expected_path = FONT_PATHS[candidate_id].resolve(strict=True)
        resolved = font_path.resolve(strict=True)
        if (
            resolved != expected_path
            or not _inside(resolved, ARTIFACT_ROOT.resolve(strict=True))
            or font_path.is_symlink()
            or _sha256(resolved) != FONT_SHA256[candidate_id]
        ):
            raise RuntimeError("exact W6 font boundary mismatch")
        if features.check("raqm") or features.check("harfbuzz"):
            raise RuntimeError("W6 reviewed renderer unexpectedly gained complex shaping")

        self.candidate_id = candidate_id
        self.artifact_sha256 = f"sha256:{FONT_SHA256[candidate_id].lower()}"
        self.font_family = (
            "Noto Sans Devanagari"
            if candidate_id == "FONT-D0"
            else "Noto Sans Gujarati"
        )
        self._font = ImageFont.truetype(
            str(resolved),
            size=40,
            layout_engine=ImageFont.Layout.BASIC,
        )
        if self._font.getname() != (self.font_family, "Regular"):
            raise RuntimeError("W6 font identity changed")

    def render(
        self, sample: EphemeralAuxiliarySampleV1
    ) -> RawRenderedAuxiliaryPixelsV1:
        from PIL import Image, ImageDraw

        expected_script = (
            "devanagari" if self.candidate_id == "FONT-D0" else "gujarati"
        )
        if sample.script != expected_script:
            raise RuntimeError("W6 script/font mismatch")
        background = (244, 244, 238)
        foreground = (24, 24, 24)
        if sample.degradation == "low_contrast":
            background = (222, 222, 216)
            foreground = (108, 108, 104)
        image = Image.new("RGB", (320, 64), background)
        draw = ImageDraw.Draw(image)
        bounds = draw.textbbox((0, 0), sample.text, font=self._font)
        text_width = bounds[2] - bounds[0]
        text_height = bounds[3] - bounds[1]
        position = (
            (image.width - text_width) // 2 - bounds[0],
            (image.height - text_height) // 2 - bounds[1],
        )
        draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=(40, 40, 40))
        draw.text(position, sample.text, fill=foreground, font=self._font)
        if sample.degradation == "downscaled":
            image = image.resize((160, 32), Image.Resampling.BILINEAR).resize(
                (320, 64), Image.Resampling.BILINEAR
            )
        return RawRenderedAuxiliaryPixelsV1(
            width=image.width,
            height=image.height,
            bgr_bytes=image.tobytes("raw", "BGR"),
        )


class ExactPaddleDevanagariOcrAdapter:
    candidate_id = "OCR-D0"

    def __init__(
        self,
        *,
        model_dir: Path,
        extracted_inventory_sha256: str,
    ) -> None:
        expected = (
            RUNTIME_ROOT
            / "models"
            / "OCR-D0"
            / "devanagari_PP-OCRv5_mobile_rec_infer"
        ).resolve(strict=True)
        resolved = model_dir.resolve(strict=True)
        if (
            resolved != expected
            or not _inside(resolved, (RUNTIME_ROOT / "models").resolve(strict=True))
            or model_dir.is_symlink()
        ):
            raise RuntimeError("exact W6 model directory boundary mismatch")
        observed_inventory = _model_inventory(resolved)
        if (
            extracted_inventory_sha256 != MODEL_INVENTORY
            or observed_inventory != MODEL_INVENTORY
        ):
            raise RuntimeError("exact W6 model inventory digest mismatch")
        if _sha256(resolved / "inference.yml") != (
            "9BD172DD26440C8CE94D1CDE5D5BAEA6AEFDC7CF3C5C8492E0BEEDEF656D4E54"
        ):
            raise RuntimeError("exact W6 dictionary configuration changed")

        import numpy as np
        from paddleocr import TextRecognition

        self._numpy = np
        self.extracted_inventory_sha256 = extracted_inventory_sha256
        self._predictor = TextRecognition(
            model_name="devanagari_PP-OCRv5_mobile_rec",
            model_dir=str(resolved),
            device="cpu",
            engine="paddle_static",
            enable_hpi=False,
            use_tensorrt=False,
            enable_cinn=False,
            cpu_threads=1,
        )

    def recognize(
        self, crop: GeneratedAuxiliaryCropV1
    ) -> RawAuxiliaryOcrEngineResultV1:
        if crop.sample.script != "devanagari":
            raise RuntimeError("W6 OCR script mismatch")
        image = self._numpy.frombuffer(crop.bgr_bytes, dtype=self._numpy.uint8).reshape(
            (crop.height, crop.width, 3)
        )
        results = self._predictor.predict(input=image, batch_size=1)
        if not isinstance(results, list) or len(results) != 1:
            return RawAuxiliaryOcrEngineResultV1(None, None)
        result: Any = results[0]
        try:
            return RawAuxiliaryOcrEngineResultV1(
                result["rec_text"],
                result["rec_score"],
            )
        except (KeyError, TypeError):
            return RawAuxiliaryOcrEngineResultV1(None, None)

    def close(self) -> None:
        self._predictor.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--inventory-sha256", required=True)
    parser.add_argument("--font-d0", type=Path, required=True)
    parser.add_argument("--font-g0", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=12)
    return parser.parse_args(argv)


def _run(args: argparse.Namespace) -> AuxiliaryScriptGeneratedEvaluationV1:
    _verify_runtime()
    if args.inventory_sha256 != MODEL_INVENTORY:
        raise RuntimeError("W6 inventory argument is not the reviewed digest")
    font_d0 = ExactPillowAuxiliaryRenderer(
        candidate_id="FONT-D0",
        font_path=args.font_d0,
    )
    font_g0 = ExactPillowAuxiliaryRenderer(
        candidate_id="FONT-G0",
        font_path=args.font_g0,
    )
    engine = ExactPaddleDevanagariOcrAdapter(
        model_dir=args.model_dir,
        extracted_inventory_sha256=args.inventory_sha256,
    )
    policy = SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")
    try:
        devanagari = evaluate_generated_devanagari_candidate(
            font_d0,
            engine,
            policy=policy,
            sample_count=args.sample_count,
            replay_runs=20,
        )
        font_evaluations = (
            evaluate_generated_auxiliary_font(
                font_d0,
                policy=policy,
                sample_count=args.sample_count,
                replay_runs=20,
                ocr_execution_performed=True,
            ),
            evaluate_generated_auxiliary_font(
                font_g0,
                policy=policy,
                sample_count=args.sample_count,
                replay_runs=20,
                ocr_execution_performed=False,
            ),
        )
    finally:
        engine.close()
    devanagari_document = devanagari.model_dump(mode="json")
    devanagari_document["network_attempt_count"] = len(_NETWORK_ATTEMPTS)
    return AuxiliaryScriptGeneratedEvaluationV1(
        devanagari_ocr=devanagari.__class__.model_validate(devanagari_document),
        font_rendering=font_evaluations,
    )


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
