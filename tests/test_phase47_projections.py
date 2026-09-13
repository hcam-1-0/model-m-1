import pytest

from hcam.acceptance.handoff import (
    build_event_workflows,
    build_http_catalogue,
    build_ui_accessibility,
)
from hcam.acceptance.projections import (
    PROJECTION_NOTICE,
    build_projection_bundle,
    validate_projections,
)


def test_standard_shaped_projections_are_derived_and_non_authoritative() -> None:
    projections = build_projection_bundle(
        build_http_catalogue(), build_event_workflows(), build_ui_accessibility()
    )
    validate_projections(projections)
    assert set(projections) == {
        "openapi",
        "asyncapi",
        "cloudevents",
        "arazzo",
        "rfc8785",
        "prov",
        "slsa",
    }
    assert all(not boundary["conformance_claim"] for boundary in [PROJECTION_NOTICE])


def test_projection_validation_rejects_missing_boundary_and_version() -> None:
    projections = build_projection_bundle(
        build_http_catalogue(), build_event_workflows(), build_ui_accessibility()
    )
    with pytest.raises(ValueError):
        validate_projections(
            {key: value for key, value in projections.items() if key != "slsa"}
        )
    altered = dict(projections)
    altered["openapi"] = {**altered["openapi"], "x-hcam-boundary": {}}
    with pytest.raises(ValueError):
        validate_projections(altered)
    altered = dict(projections)
    altered["asyncapi"] = {**altered["asyncapi"], "asyncapi": "0.0.0"}
    with pytest.raises(ValueError):
        validate_projections(altered)
