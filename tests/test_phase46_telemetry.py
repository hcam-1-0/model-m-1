import pytest

from hcam.operations.platform.metrics import OpenTelemetryProjectionAdapter, metric_contracts, validate_labels


def test_metric_registry_is_closed_and_low_cardinality() -> None:
    definitions = metric_contracts()
    assert definitions
    validate_labels("hcam_platform_requests_total", {"outcome": "accepted"})
    with pytest.raises(ValueError):
        validate_labels("hcam_platform_requests_total", {"camera_id": "generated"})
    with pytest.raises(ValueError):
        validate_labels("hcam_unknown", {})


def test_otel_projection_is_default_off_and_non_exporting() -> None:
    adapter = OpenTelemetryProjectionAdapter()
    projection = adapter.project("hcam_platform_jobs", {"worker_state": "queued"}, 1)
    assert projection["exported"] is False
    with pytest.raises(ValueError):
        OpenTelemetryProjectionAdapter(enabled=True)
    with pytest.raises(ValueError):
        OpenTelemetryProjectionAdapter(endpoint_configured=True)
