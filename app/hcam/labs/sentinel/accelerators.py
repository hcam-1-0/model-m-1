from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


Accelerator = Literal["auto", "cpu", "nvidia", "intel", "amd", "vaapi"]
Codec = Literal["h264", "hevc"]


class AcceleratorError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class EncoderSelection:
    codec: Codec
    requested: Accelerator
    accelerator: str
    encoder: str
    hardware: bool
    fallback: bool
    validated: bool


@dataclass(frozen=True, slots=True)
class AcceleratorReport:
    ffmpeg: str
    ffmpeg_version: str
    os: str
    machine: str
    cpu_count: int
    requested: Accelerator
    h264: EncoderSelection
    hevc: EncoderSelection
    available_hardware_encoders: tuple[str, ...]

    def document(self) -> dict[str, object]:
        return asdict(self)


_CANDIDATES: dict[Accelerator, dict[Codec, str]] = {
    "nvidia": {"h264": "h264_nvenc", "hevc": "hevc_nvenc"},
    "intel": {"h264": "h264_qsv", "hevc": "hevc_qsv"},
    "amd": {"h264": "h264_amf", "hevc": "hevc_amf"},
    "vaapi": {"h264": "h264_vaapi", "hevc": "hevc_vaapi"},
    "cpu": {"h264": "libx264", "hevc": "libx265"},
    "auto": {},
}


def _run(command: Sequence[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise AcceleratorError("ffmpeg_unavailable") from exc


def _encoder_names(ffmpeg: str) -> tuple[str, set[str]]:
    version = _run((ffmpeg, "-hide_banner", "-version"), timeout=10)
    if version.returncode != 0 or not version.stdout.strip():
        raise AcceleratorError("ffmpeg_unavailable")
    encoders = _run((ffmpeg, "-hide_banner", "-encoders"), timeout=15)
    if encoders.returncode != 0:
        raise AcceleratorError("ffmpeg_encoder_inventory_failed")
    known = {
        encoder
        for group in _CANDIDATES.values()
        for encoder in group.values()
        if encoder in encoders.stdout
    }
    return version.stdout.splitlines()[0].strip(), known


def encoder_quality_arguments(
    selection: EncoderSelection, *, crf: int, bitrate_kbps: int
) -> list[str]:
    encoder = selection.encoder
    bitrate = f"{bitrate_kbps}k"
    maximum = f"{max(bitrate_kbps + 500, round(bitrate_kbps * 1.35))}k"
    buffer_size = f"{max(2 * bitrate_kbps, 2000)}k"
    if encoder in {"libx264", "libx265"}:
        arguments = ["-c:v", encoder, "-preset", "veryfast", "-crf", str(crf)]
        if encoder == "libx265":
            arguments.extend(["-x265-params", "log-level=error"])
        return arguments
    if encoder.endswith("_nvenc"):
        return [
            "-c:v",
            encoder,
            "-preset",
            "p5",
            "-tune",
            "hq",
            "-rc",
            "vbr",
            "-cq",
            str(crf),
            "-b:v",
            bitrate,
            "-maxrate",
            maximum,
            "-bufsize",
            buffer_size,
        ]
    if encoder.endswith("_qsv"):
        return [
            "-c:v",
            encoder,
            "-preset",
            "medium",
            "-global_quality",
            str(crf),
            "-b:v",
            bitrate,
        ]
    if encoder.endswith("_amf"):
        return [
            "-c:v",
            encoder,
            "-quality",
            "quality",
            "-rc",
            "vbr_peak",
            "-qp_i",
            str(crf),
            "-qp_p",
            str(crf),
            "-b:v",
            bitrate,
            "-maxrate",
            maximum,
        ]
    if encoder.endswith("_vaapi"):
        return [
            "-vf",
            "format=nv12,hwupload",
            "-c:v",
            encoder,
            "-global_quality",
            str(crf),
            "-b:v",
            bitrate,
        ]
    raise AcceleratorError("unsupported_encoder")


def _smoke_test(ffmpeg: str, selection: EncoderSelection) -> bool:
    with tempfile.TemporaryDirectory(prefix="hcam-p25-encoder-") as temporary:
        output = Path(temporary) / "probe.mp4"
        command = [
            ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=10",
            "-frames:v",
            "3",
            "-an",
        ]
        if selection.encoder.endswith("_vaapi"):
            command[1:1] = ["-vaapi_device", "/dev/dri/renderD128"]
        command.extend(encoder_quality_arguments(selection, crf=24, bitrate_kbps=500))
        command.extend(["-pix_fmt", "yuv420p", "-y", str(output)])
        completed = _run(command, timeout=20)
        return (
            completed.returncode == 0 and output.is_file() and output.stat().st_size > 0
        )


def _candidate_order(requested: Accelerator) -> tuple[Accelerator, ...]:
    if requested == "auto":
        if platform.system() == "Windows":
            return ("nvidia", "intel", "amd", "cpu")
        return ("nvidia", "intel", "vaapi", "cpu")
    if requested == "cpu":
        return ("cpu",)
    return (requested, "cpu")


def discover_acceleration(
    ffmpeg: str = "ffmpeg",
    *,
    requested: Accelerator = "auto",
    validate: bool = True,
) -> AcceleratorReport:
    if requested not in _CANDIDATES:
        raise AcceleratorError("accelerator_mode_invalid")
    resolved_ffmpeg = shutil.which(ffmpeg) or ffmpeg
    version, encoders = _encoder_names(resolved_ffmpeg)

    def select(codec: Codec) -> EncoderSelection:
        for accelerator in _candidate_order(requested):
            encoder = _CANDIDATES[accelerator][codec]
            if encoder not in encoders:
                continue
            candidate = EncoderSelection(
                codec=codec,
                requested=requested,
                accelerator=accelerator,
                encoder=encoder,
                hardware=accelerator != "cpu",
                fallback=requested not in {"auto", accelerator},
                validated=not validate,
            )
            if validate and not _smoke_test(resolved_ffmpeg, candidate):
                continue
            return EncoderSelection(
                codec=candidate.codec,
                requested=candidate.requested,
                accelerator=candidate.accelerator,
                encoder=candidate.encoder,
                hardware=candidate.hardware,
                fallback=candidate.fallback,
                validated=True,
            )
        raise AcceleratorError(f"{codec}_encoder_unavailable")

    hardware = tuple(
        sorted(
            encoder
            for accelerator, group in _CANDIDATES.items()
            if accelerator not in {"auto", "cpu"}
            for encoder in group.values()
            if encoder in encoders
        )
    )
    return AcceleratorReport(
        ffmpeg=resolved_ffmpeg,
        ffmpeg_version=version,
        os=platform.system(),
        machine=platform.machine(),
        cpu_count=os.cpu_count() or 1,
        requested=requested,
        h264=select("h264"),
        hevc=select("hevc"),
        available_hardware_encoders=hardware,
    )
