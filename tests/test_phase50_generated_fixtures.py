from __future__ import annotations

import json
from pathlib import Path

from hcam.operator_application import (
    GisParityMatrixV1,
    canonical_sha256,
    generated_contract_cases,
    generated_gis_parity_cases,
    validate_generated_portfolio,
)
from hcam.operator_application.generated import unique_case_ids
from hcam.operator_application.security import assert_generated_payload


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures/phase-5/p5-0"
CONTRACTS = ROOT / "contracts/phase-5"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _GIS_matrix() -> GisParityMatrixV1:
    return GisParityMatrixV1.model_validate_json(
        (CONTRACTS / "operator-ui-gis-parity.v1.json").read_text(encoding="utf-8")
    )


def test_contract_cases_materialize_every_declared_dimension() -> None:
    seeds = _json(FIXTURES / "canonical-positive.json")
    cases = generated_contract_cases()
    assert len(cases) == seeds["expected_materialized_case_count"] == 720
    assert len({case.view_id for case in cases}) == 10
    assert len({case.state for case in cases}) == 8
    assert len({case.resource_profile for case in cases}) == 3
    assert len({case.locale for case in cases}) == 3
    assert unique_case_ids(cases)
    assert all(case.case_id.startswith("syn_case_") for case in cases)


def test_generated_contract_cases_are_deterministic() -> None:
    first = [case.model_dump(mode="json") for case in generated_contract_cases()]
    second = [case.model_dump(mode="json") for case in generated_contract_cases()]
    assert canonical_sha256(first) == canonical_sha256(second)


def test_gis_cases_materialize_exact_parity_cross_product() -> None:
    seeds = _json(FIXTURES / "gis-parity-vectors.json")
    cases = generated_gis_parity_cases(_GIS_matrix())
    assert len(cases) == seeds["expected_materialized_case_count"] == 96
    assert len({case.requirement_id for case in cases}) == 12
    assert {case.geometry_type for case in cases} == {
        "Point",
        "LineString",
        "Polygon",
        "MultiPolygon",
    }
    assert {case.resource_profile for case in cases} == {
        "low_resource",
        "control_room",
    }
    assert unique_case_ids(cases)


def test_full_generated_portfolio_is_safe_and_complete() -> None:
    matrix = _GIS_matrix()
    portfolio = validate_generated_portfolio(matrix)
    assert portfolio.model_dump() == {
        "contract_type": "hcam.operator.portfolio-validation.v1",
        "contract_case_count": 720,
        "GIS_case_count": 96,
        "identifiers_unique": True,
        "generated_payloads_safe": True,
        "complete": True,
    }
    for case in (*generated_contract_cases(), *generated_gis_parity_cases(matrix)):
        assert_generated_payload(case.model_dump(mode="json"))


def test_negative_fixture_has_bounded_unique_non_operational_expectations() -> None:
    fixture = _json(FIXTURES / "canonical-negative.json")
    cases = fixture["cases"]
    assert isinstance(cases, list)
    assert len(cases) == 12
    assert len({item["case_id"] for item in cases}) == 12
    assert all(item["case_id"].startswith("negative.") for item in cases)
    assert fixture["generated_only"] is True
    assert fixture["operational"] is False


def test_journey_walkthroughs_are_generated_and_server_confirmed() -> None:
    fixture = _json(FIXTURES / "journey-walkthroughs.json")
    walkthroughs = fixture["walkthroughs"]
    assert isinstance(walkthroughs, list)
    assert len(walkthroughs) == 4
    assert all(
        len(item["actions"]) == len(item["server_confirmations"])
        and all(item["server_confirmations"])
        for item in walkthroughs
    )
    assert fixture["generated_only"] is True
    assert fixture["operational"] is False
