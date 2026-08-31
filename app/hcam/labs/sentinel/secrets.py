from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


AuthMode = Literal["none", "bearer", "basic"]


class SecretResolutionError(RuntimeError):
    def __init__(self, code: str = "secret_provider_failure") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class CatalogCredential:
    username: str | None = None
    password: str | None = None
    bearer_token: str | None = None


class CatalogSecretProvider(Protocol):
    def resolve(self, secret_ref: str, auth_mode: AuthMode) -> CatalogCredential: ...


class UnconfiguredSecretProvider:
    def resolve(self, secret_ref: str, auth_mode: AuthMode) -> CatalogCredential:
        del secret_ref, auth_mode
        raise SecretResolutionError("secret_provider_unconfigured")


class FileSecretProvider:
    """Development-only JSON provider constrained to one non-symlink root."""

    def __init__(self, root: Path, *, max_bytes: int = 16 * 1024) -> None:
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise SecretResolutionError("secret_root_invalid")
        self.max_bytes = max_bytes

    def resolve(self, secret_ref: str, auth_mode: AuthMode) -> CatalogCredential:
        if (
            not secret_ref
            or Path(secret_ref).is_absolute()
            or ".." in Path(secret_ref).parts
        ):
            raise SecretResolutionError("secret_ref_invalid")
        candidate = self.root / secret_ref
        try:
            if candidate.is_symlink():
                raise SecretResolutionError("secret_symlink_denied")
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self.root)
            if not resolved.is_file() or resolved.stat().st_size > self.max_bytes:
                raise SecretResolutionError("secret_file_invalid")
            payload = resolved.read_bytes()
            document = json.loads(payload.decode("utf-8"))
        except SecretResolutionError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise SecretResolutionError("secret_resolution_failed") from exc
        if not isinstance(document, dict):
            raise SecretResolutionError("secret_document_invalid")
        if auth_mode == "bearer":
            token = document.get("bearer_token")
            if not isinstance(token, str) or not token:
                raise SecretResolutionError("secret_document_invalid")
            return CatalogCredential(bearer_token=token)
        if auth_mode == "basic":
            username = document.get("username")
            password = document.get("password")
            if (
                not isinstance(username, str)
                or not username
                or not isinstance(password, str)
                or not password
            ):
                raise SecretResolutionError("secret_document_invalid")
            return CatalogCredential(username=username, password=password)
        raise SecretResolutionError("secret_auth_mode_invalid")
