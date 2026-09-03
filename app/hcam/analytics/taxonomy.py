from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import (
    ActorId,
    ClassId,
    ContractModel,
    ImmutableDigest,
    StableName,
    TaxonomyVersion,
    UtcDateTime,
)


TaxonomyStatus = Literal["draft", "approved", "retired"]
ClassState = Literal["active", "deprecated"]
ProhibitedUse = Literal[
    "autonomous_enforcement",
    "biometric_identification",
    "cross_camera_identity",
    "person_reidentification",
    "sensitive_trait_inference",
]

_REQUIRED_PROHIBITED_USES = frozenset(
    {
        "autonomous_enforcement",
        "biometric_identification",
        "cross_camera_identity",
        "person_reidentification",
        "sensitive_trait_inference",
    }
)
_PROHIBITED_CLASS_TOKENS = frozenset(
    {
        "appearance",
        "biometric",
        "caste",
        "criminality",
        "criminal",
        "crosscamera",
        "disability",
        "emotion",
        "ethnicity",
        "face",
        "faceprint",
        "gender",
        "health",
        "identity",
        "identification",
        "intent",
        "political",
        "predictive",
        "profile",
        "profiling",
        "race",
        "reid",
        "religion",
        "risk",
        "sexual",
        "watchlist",
        "owner",
        "ownership",
    }
)


def _tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


class TaxonomyClassV1(ContractModel):
    id: ClassId
    display_name: Annotated[str, Field(min_length=1, max_length=120)]
    parent_id: ClassId | None = None
    purpose: Annotated[str, Field(min_length=1, max_length=500)]
    state: ClassState = "active"

    @field_validator("display_name", "purpose")
    @classmethod
    def text_is_trimmed(cls, value: str) -> str:
        if value.strip() != value or not value:
            raise ValueError("taxonomy text must be non-blank without outer whitespace")
        return value

    @model_validator(mode="after")
    def class_is_not_prohibited(self) -> TaxonomyClassV1:
        checked = _tokens(self.id) | _tokens(self.display_name) | _tokens(self.purpose)
        prohibited = sorted(checked & _PROHIBITED_CLASS_TOKENS)
        if prohibited:
            raise ValueError("taxonomy class uses a prohibited attribute category")
        if self.parent_id == self.id:
            raise ValueError("taxonomy class cannot be its own parent")
        return self


class TaxonomyManifestV1(ContractModel):
    contract_type: Literal["hcam.analytics.taxonomy.v1"] = (
        "hcam.analytics.taxonomy.v1"
    )
    taxonomy_version: TaxonomyVersion
    artifact_digest: ImmutableDigest
    status: TaxonomyStatus
    intended_use: Annotated[str, Field(min_length=1, max_length=1_000)]
    classes: Annotated[list[TaxonomyClassV1], Field(min_length=1, max_length=512)]
    unknown_class_policy: Literal["reject", "emit_unknown"] = "reject"
    prohibited_uses: Annotated[list[ProhibitedUse], Field(min_length=5, max_length=5)]
    owner_id: ActorId
    independent_reviewer_id: ActorId | None = None
    approval_record_id: StableName | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @field_validator("intended_use")
    @classmethod
    def intended_use_is_trimmed(cls, value: str) -> str:
        if value.strip() != value or not value:
            raise ValueError("intended_use must be non-blank without outer whitespace")
        if _tokens(value) & _PROHIBITED_CLASS_TOKENS:
            raise ValueError("intended_use names a prohibited analytics purpose")
        return value

    @field_validator("prohibited_uses")
    @classmethod
    def includes_non_negotiable_prohibitions(
        cls,
        value: list[ProhibitedUse],
    ) -> list[ProhibitedUse]:
        if len(set(value)) != len(value):
            raise ValueError("prohibited_uses must not contain duplicates")
        if set(value) != _REQUIRED_PROHIBITED_USES:
            raise ValueError("taxonomy must preserve every non-negotiable prohibition")
        return value

    @model_validator(mode="after")
    def hierarchy_and_approval_are_consistent(self) -> TaxonomyManifestV1:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")

        by_id = {item.id: item for item in self.classes}
        if len(by_id) != len(self.classes):
            raise ValueError("taxonomy class IDs must be unique")
        for item in self.classes:
            if item.parent_id is not None and item.parent_id not in by_id:
                raise ValueError("taxonomy parent_id must reference a class in the manifest")

        for class_id in by_id:
            visited = {class_id}
            current = class_id
            while (parent := by_id[current].parent_id) is not None:
                if parent in visited:
                    raise ValueError("taxonomy hierarchy must not contain a cycle")
                visited.add(parent)
                current = parent

        if self.status in {"approved", "retired"}:
            if self.approval_record_id is None:
                raise ValueError("approved or retired taxonomy requires approval record")
        return self
