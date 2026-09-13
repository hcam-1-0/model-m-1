import pytest

from hcam.acceptance.handoff import (
    build_event_workflows,
    build_http_catalogue,
    build_ui_accessibility,
    validate_handoff,
)


def test_handoff_catalogues_are_cross_referenced_and_complete() -> None:
    http = build_http_catalogue()
    events = build_event_workflows()
    ui = build_ui_accessibility()
    validate_handoff(http, events, ui)
    assert len(http.operations) == 16
    assert len(ui.states) == 11
    assert ui.UI_implemented is False


def test_handoff_rejects_duplicate_and_missing_operation_references() -> None:
    http = build_http_catalogue()
    events = build_event_workflows()
    ui = build_ui_accessibility()
    with pytest.raises(ValueError):
        validate_handoff(
            http.model_copy(
                update={"operations": (http.operations[0], http.operations[0])}
            ),
            events,
            ui,
        )
    step = (
        events.workflows[0]
        .steps[0]
        .model_copy(update={"operation_ref": "missing.operation"})
    )
    workflow = events.workflows[0].model_copy(update={"steps": (step,)})
    with pytest.raises(ValueError):
        validate_handoff(http, events.model_copy(update={"workflows": (workflow,)}), ui)


def test_handoff_requires_every_ui_and_accessibility_state() -> None:
    http = build_http_catalogue()
    events = build_event_workflows()
    ui = build_ui_accessibility()
    with pytest.raises(ValueError):
        validate_handoff(http, events, ui.model_copy(update={"states": ui.states[:-1]}))
    with pytest.raises(ValueError):
        validate_handoff(
            http, events, ui.model_copy(update={"requirements": ui.requirements[:-1]})
        )
