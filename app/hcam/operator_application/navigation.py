from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .bounds import MAX_ROUTE_STATE_KEYS
from .contracts import OperatorContractModel, RoleName, StableId


_SAFE_PATH = re.compile(r"^/[a-z0-9][a-z0-9_/-]{0,159}$")
_SAFE_VALUE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RouteContractV1(OperatorContractModel):
    route_id: StableId
    path: Annotated[str, Field(min_length=1, max_length=160)]
    portal_id: StableId
    required_roles: Annotated[list[RoleName], Field(min_length=1, max_length=16)]
    allowed_query_keys: Annotated[list[StableId], Field(max_length=MAX_ROUTE_STATE_KEYS)]
    sensitive_state_permitted: Literal[False] = False

    @field_validator("path")
    @classmethod
    def path_is_local_and_canonical(cls, value: str) -> str:
        if not _SAFE_PATH.fullmatch(value):
            raise ValueError("route path is not a canonical local path")
        if "//" in value or "/../" in f"{value}/" or "/./" in f"{value}/":
            raise ValueError("route path contains ambiguous segments")
        return value.rstrip("/") or "/"

    @model_validator(mode="after")
    def route_lists_are_unique(self) -> RouteContractV1:
        if len(self.required_roles) != len(set(self.required_roles)):
            raise ValueError("route roles must be unique")
        if len(self.allowed_query_keys) != len(set(self.allowed_query_keys)):
            raise ValueError("route query keys must be unique")
        return self


def validate_url_state(
    route: RouteContractV1,
    values: dict[str, str],
) -> dict[str, str]:
    if len(values) > MAX_ROUTE_STATE_KEYS:
        raise ValueError("URL state contains too many keys")
    unknown = set(values) - set(route.allowed_query_keys)
    if unknown:
        raise ValueError("URL state contains an unapproved key")
    normalized: dict[str, str] = {}
    for key in sorted(values):
        value = values[key]
        if not _SAFE_VALUE.fullmatch(value):
            raise ValueError("URL state contains an unsafe value")
        normalized[key] = value
    return normalized
