from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.operator_application import (
    JourneyContractV1,
    RouteContractV1,
    advance_journey,
    validate_url_state,
)


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = json.loads(
    (ROOT / "contracts/phase-5/operator-ui-route-journeys.v1.json").read_text(
        encoding="utf-8"
    )
)


def _journeys() -> dict[str, JourneyContractV1]:
    return {
        item.journey_id: item
        for item in (JourneyContractV1.model_validate(raw) for raw in DOCUMENT["journeys"])
    }


def test_routes_accept_only_allowlisted_safe_state() -> None:
    route = RouteContractV1.model_validate(DOCUMENT["routes"][3])
    assert validate_url_state(route, {"window": "15m", "layer": "camera"}) == {
        "layer": "camera",
        "window": "15m",
    }
    with pytest.raises(ValueError, match="unapproved"):
        validate_url_state(route, {"camera_locator": "hidden"})
    with pytest.raises(ValueError, match="unsafe"):
        validate_url_state(route, {"layer": "camera&token=secret"})
    with pytest.raises(ValueError, match="too many"):
        validate_url_state(route, {f"key{index}": "value" for index in range(25)})


def test_route_contract_rejects_unsafe_path_and_duplicates() -> None:
    route = DOCUMENT["routes"][0]
    for path in ("https://example.invalid", "/command/../admin", "/command//admin"):
        with pytest.raises(ValidationError):
            RouteContractV1.model_validate({**route, "path": path})
    with pytest.raises(ValidationError, match="roles"):
        RouteContractV1.model_validate(
            {**route, "required_roles": ["administrator", "administrator"]}
        )
    with pytest.raises(ValidationError, match="query keys"):
        RouteContractV1.model_validate(
            {**route, "allowed_query_keys": ["window", "window"]}
        )


def test_journey_requires_server_confirmation_and_known_transition() -> None:
    journey = _journeys()["journey.alert_review"]
    assert (
        advance_journey(
            journey, state="ready", action_id="review", server_confirmed=True
        )
        == "conflict"
    )
    with pytest.raises(PermissionError, match="server confirmation"):
        advance_journey(
            journey, state="ready", action_id="review", server_confirmed=False
        )
    with pytest.raises(ValueError, match="not allowed"):
        advance_journey(
            journey, state="ready", action_id="dispatch", server_confirmed=True
        )


def test_journey_rejects_duplicate_transitions_and_unreachable_terminal() -> None:
    raw = DOCUMENT["journeys"][0]
    with pytest.raises(ValidationError, match="identifiers"):
        JourneyContractV1.model_validate(
            {**raw, "transitions": [raw["transitions"][0], raw["transitions"][0]]}
        )
    with pytest.raises(ValidationError, match="terminal states"):
        JourneyContractV1.model_validate(
            {**raw, "terminal_states": ["ready", "ready"]}
        )
    with pytest.raises(ValidationError, match="unreachable"):
        JourneyContractV1.model_validate({**raw, "terminal_states": ["stale"]})
