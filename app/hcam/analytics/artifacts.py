from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


DET_R0_ARTIFACT_ID = "DET-R0-ONNX-UPSTREAM-0.1.1RC0"
DET_R0_FILENAME = "yolox_tiny.onnx"
DET_R0_BYTES = 20_219_662
DET_R0_SHA256 = "427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7"


class AnalyticsArtifactError(RuntimeError):
    """A safe artifact-policy failure without exposing a configured path."""


@dataclass(frozen=True, slots=True)
class ArtifactRequirement:
    artifact_id: str
    filename: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class VerifiedArtifact:
    artifact_id: str
    path: Path
    bytes: int
    sha256: str


DET_R0_REQUIREMENT = ArtifactRequirement(
    artifact_id=DET_R0_ARTIFACT_ID,
    filename=DET_R0_FILENAME,
    bytes=DET_R0_BYTES,
    sha256=DET_R0_SHA256,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AnalyticsArtifactError("analytics artifact could not be read") from exc
    return digest.hexdigest().upper()


def verify_local_artifact(
    root: Path,
    relative_path: Path,
    *,
    requirement: ArtifactRequirement = DET_R0_REQUIREMENT,
) -> VerifiedArtifact:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise AnalyticsArtifactError("analytics artifact path is not permitted")
    try:
        verified_root = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise AnalyticsArtifactError("analytics artifact root is unavailable") from exc
    if not verified_root.is_dir():
        raise AnalyticsArtifactError("analytics artifact root is unavailable")

    unresolved = verified_root / relative_path
    if unresolved.is_symlink():
        raise AnalyticsArtifactError("analytics artifact symlinks are prohibited")
    try:
        artifact = unresolved.resolve(strict=True)
        artifact.relative_to(verified_root)
    except (OSError, ValueError) as exc:
        raise AnalyticsArtifactError("analytics artifact is unavailable") from exc
    if not artifact.is_file() or artifact.name != requirement.filename:
        raise AnalyticsArtifactError("analytics artifact is not the approved file")
    try:
        size = artifact.stat().st_size
    except OSError as exc:
        raise AnalyticsArtifactError(
            "analytics artifact could not be inspected"
        ) from exc
    if size != requirement.bytes:
        raise AnalyticsArtifactError("analytics artifact size is not approved")
    digest = _sha256(artifact)
    if digest != requirement.sha256:
        raise AnalyticsArtifactError("analytics artifact digest is not approved")
    return VerifiedArtifact(
        artifact_id=requirement.artifact_id,
        path=artifact,
        bytes=size,
        sha256=digest,
    )
