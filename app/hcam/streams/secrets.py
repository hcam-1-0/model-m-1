from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


_MAX_SECRET_BYTES = 16 * 1024
_MAX_USERNAME_LENGTH = 256
_MAX_PASSWORD_LENGTH = 1024


class CameraSecretError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True, repr=False)
class CameraCredentials:
    username: str
    password: str


class CameraSecretProvider(Protocol):
    def get(self, secret_ref: str) -> CameraCredentials: ...


@dataclass(frozen=True, slots=True)
class UnconfiguredCameraSecretProvider:
    def get(self, _secret_ref: str) -> CameraCredentials:
        raise CameraSecretError("camera_secret_provider_unconfigured")


@dataclass(frozen=True, slots=True)
class FileCameraSecretProvider:
    root: Path

    def __post_init__(self) -> None:
        root = self.root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError("camera secret root must be an existing directory")
        object.__setattr__(self, "root", root)

    def get(self, secret_ref: str) -> CameraCredentials:
        relative = Path(secret_ref)
        if relative.is_absolute() or ".." in relative.parts:
            raise CameraSecretError("camera_secret_invalid_reference")
        try:
            candidate = (self.root / relative).resolve(strict=True)
            candidate.relative_to(self.root)
            stat = candidate.stat()
            if not candidate.is_file() or stat.st_size > _MAX_SECRET_BYTES:
                raise CameraSecretError("camera_secret_invalid_file")
            with candidate.open("rb") as secret_file:
                raw = secret_file.read(_MAX_SECRET_BYTES + 1)
            if len(raw) > _MAX_SECRET_BYTES:
                raise CameraSecretError("camera_secret_invalid_file")
        except CameraSecretError:
            raise
        except (OSError, ValueError) as exc:
            raise CameraSecretError("camera_secret_unavailable") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CameraSecretError("camera_secret_invalid_payload") from exc
        if not isinstance(payload, dict) or set(payload) != {"username", "password"}:
            raise CameraSecretError("camera_secret_invalid_payload")
        username = payload.get("username")
        password = payload.get("password")
        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or not username
            or not password
            or len(username) > _MAX_USERNAME_LENGTH
            or len(password) > _MAX_PASSWORD_LENGTH
            or "\x00" in username
            or "\x00" in password
        ):
            raise CameraSecretError("camera_secret_invalid_payload")
        return CameraCredentials(username=username, password=password)


def build_camera_secret_provider(
    provider_name: str,
    root: Path | None,
) -> CameraSecretProvider:
    if provider_name == "unconfigured":
        return UnconfiguredCameraSecretProvider()
    if provider_name == "file" and root is not None:
        return FileCameraSecretProvider(root)
    raise ValueError("camera secret provider configuration is incomplete")
