from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.operator_application import ContractCatalogueV1


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts/phase-5"


def _catalogue() -> ContractCatalogueV1:
    return ContractCatalogueV1.model_validate_json(
        (CONTRACTS / "operator-ui-contract-catalogue.v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_catalogue_has_expected_portals_views_and_locales() -> None:
    catalogue = _catalogue()
    assert len(catalogue.views) == 10
    assert {item.portal_id for item in catalogue.views} == {
        "admin",
        "command",
        "evidence",
        "intelligence",
        "investigations",
        "operations",
        "security",
    }
    assert all(item.locales == ["en-IN", "gu-IN", "hi-IN"] for item in catalogue.views)
    assert catalogue.view("operations.gis_workspace").producer.gap_class == "blocked"
    assert len(catalogue.views_for_portal("operations")) == 3
    assert catalogue.views_for_portal("missing") == ()
    with pytest.raises(KeyError):
        catalogue.view("missing")


def test_catalogue_rejects_duplicate_view_and_route_ids() -> None:
    document = json.loads(
        (CONTRACTS / "operator-ui-contract-catalogue.v1.json").read_text(
            encoding="utf-8"
        )
    )
    duplicate_view = json.loads(json.dumps(document))
    duplicate_view["views"][1]["view_id"] = duplicate_view["views"][0]["view_id"]
    with pytest.raises(ValidationError, match="view identifiers"):
        ContractCatalogueV1.model_validate(duplicate_view)
    duplicate_route = json.loads(json.dumps(document))
    duplicate_route["views"][1]["route_id"] = duplicate_route["views"][0]["route_id"]
    with pytest.raises(ValidationError, match="route identifiers"):
        ContractCatalogueV1.model_validate(duplicate_route)


def test_producer_coverage_matches_catalogue_and_stays_bounded() -> None:
    catalogue = _catalogue()
    coverage = json.loads(
        (CONTRACTS / "operator-ui-producer-coverage.v1.json").read_text(
            encoding="utf-8"
        )
    )
    entries = coverage["entries"]
    assert {item["view_id"] for item in entries} == {
        item.view_id for item in catalogue.views
    }
    assert all(item["department_scoped"] and item["bounded"] for item in entries)
    assert coverage["enforcement"] == {
        "blocked_features_available": False,
        "future_operational_features_available": False,
        "unknown_schema_policy": "fail_closed",
        "raw_provider_or_media_fields_permitted": False,
    }


def test_catalogue_actions_are_non_operational_and_server_bound() -> None:
    catalogue = _catalogue()
    assert all(not action.operational for view in catalogue.views for action in view.actions)
    assert all(view.producer.department_scoped for view in catalogue.views)
    review = catalogue.view("intelligence.alert_review")
    assert review.actions[0].requires_reason is True
    assert review.actions[0].requires_etag is True
