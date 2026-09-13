from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .bounds import MAX_VIEWS
from .contracts import OperatorContractModel, OperatorViewContractV1, SchemaVersion


class ContractCatalogueV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.contract-catalogue.v1"] = (
        "hcam.operator.contract-catalogue.v1"
    )
    catalogue_version: SchemaVersion
    views: Annotated[list[OperatorViewContractV1], Field(min_length=1, max_length=MAX_VIEWS)]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def catalogue_is_unique(self) -> ContractCatalogueV1:
        for label, values in (
            ("view", [item.view_id for item in self.views]),
            ("route", [item.route_id for item in self.views]),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} identifiers must be unique")
        return self

    def view(self, view_id: str) -> OperatorViewContractV1:
        for item in self.views:
            if item.view_id == view_id:
                return item
        raise KeyError(view_id)

    def views_for_portal(self, portal_id: str) -> tuple[OperatorViewContractV1, ...]:
        return tuple(item for item in self.views if item.portal_id == portal_id)
