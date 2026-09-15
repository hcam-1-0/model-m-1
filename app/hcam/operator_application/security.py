from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import model_validator

from .contracts import OperatorContractModel


PROHIBITED_KEYS = frozenset(
    {
        "authorization",
        "camera_locator",
        "certificate",
        "credential",
        "hls_url",
        "media_bytes",
        "password",
        "private_key",
        "secret",
        "secret_ref",
        "stream_url",
        "token",
        "username",
    }
)
_PLATE_PATTERN = re.compile(r"\b(?:GJ|MH|DL|RJ)[ -]?\d{1,2}[ -]?[A-Z]{1,3}[ -]?\d{1,4}\b")


class BrowserSecurityBoundaryV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.browser-security-boundary.v1"] = (
        "hcam.operator.browser-security-boundary.v1"
    )
    same_origin_bff_required: Literal[True] = True
    direct_camera_access: Literal[False] = False
    direct_database_access: Literal[False] = False
    direct_broker_access: Literal[False] = False
    direct_model_runtime_access: Literal[False] = False
    direct_provider_access: Literal[False] = False
    persistent_sensitive_browser_storage: Literal[False] = False
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def all_direct_paths_are_closed(self) -> BrowserSecurityBoundaryV1:
        if any(
            (
                self.direct_camera_access,
                self.direct_database_access,
                self.direct_broker_access,
                self.direct_model_runtime_access,
                self.direct_provider_access,
                self.persistent_sensitive_browser_storage,
            )
        ):
            raise ValueError("browser security boundary opened a prohibited direct path")
        return self


def prohibited_paths(value: Any, *, prefix: str = "$") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            path = f"{prefix}.{key}"
            normalized = str(key).casefold()
            if normalized in PROHIBITED_KEYS or normalized.endswith("_password"):
                found.append(path)
            found.extend(prohibited_paths(item, prefix=path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(prohibited_paths(item, prefix=f"{prefix}[{index}]"))
    return tuple(found)


def assert_generated_payload(value: Any) -> None:
    paths = prohibited_paths(value)
    if paths:
        raise ValueError("generated payload contains a prohibited field")
    text = repr(value)
    if _PLATE_PATTERN.search(text):
        raise ValueError("generated payload resembles an issuable registration mark")
    if isinstance(value, Mapping) and value.get("generated_only") is not True:
        raise ValueError("generated payload must declare generated_only=true")
