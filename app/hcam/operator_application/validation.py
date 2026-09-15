from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from .contracts import OperatorContractModel
from .generated import generated_contract_cases, generated_gis_parity_cases, unique_case_ids
from .gis_contracts import GisParityMatrixV1
from .security import assert_generated_payload


class PortfolioValidationV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.portfolio-validation.v1"] = (
        "hcam.operator.portfolio-validation.v1"
    )
    contract_case_count: int
    GIS_case_count: int
    identifiers_unique: bool
    generated_payloads_safe: bool
    complete: bool


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest().upper()


def validate_generated_portfolio(matrix: GisParityMatrixV1) -> PortfolioValidationV1:
    contract_cases = generated_contract_cases()
    GIS_cases = generated_gis_parity_cases(matrix)
    identifiers_unique = unique_case_ids((*contract_cases, *GIS_cases))
    for case in (*contract_cases, *GIS_cases):
        assert_generated_payload(case.model_dump(mode="json"))
    complete = len(contract_cases) >= 320 and len(GIS_cases) >= 96 and identifiers_unique
    return PortfolioValidationV1(
        contract_case_count=len(contract_cases),
        GIS_case_count=len(GIS_cases),
        identifiers_unique=identifiers_unique,
        generated_payloads_safe=True,
        complete=complete,
    )
