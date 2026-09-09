from prometheus_client import CollectorRegistry
from hcam.labs.sentinel.observability import FAULT_MATRIX, LabObservability, scan_support_bundle

def test_faults_are_independent_and_provider_failure_keeps_process_live():
    observability=LabObservability(CollectorRegistry(),version="test")
    assert observability.health(app_ready=True)["liveness"]["state"]=="live"
    for component,code,state in FAULT_MATRIX.values():
        event=observability.observe(component,code,state)
        assert event.correlation_id and len(event.correlation_id)==32
    bundle=observability.support_bundle(app_ready=True)
    assert bundle["retention"]=="none" and len(bundle["recent_errors"])==6
    assert set(bundle) >= {"versions","checksum","safe_settings","health","listeners","recent_errors"}

def test_support_bundle_rejects_sensitive_values():
    for unsafe in (
        "http://provider.internal/live",
        "https://provider.example/api",
        "rtsp://user:pass@host/path",
        "access_token=secret",
        "token=secret",
        "api_key=secret",
        "password=secret",
        "Authorization: Bearer secret",
        "Bearer secret-value",
        "provider_locator=value",
        "provider_payload=value",
        "camera_id=value",
        "stream_id=value",
        "session_id=value",
        "v=0\\r\\nsdp",
    ):
        try:
            scan_support_bundle({"value": unsafe})
        except ValueError as error:
            assert str(error) == "support_bundle_privacy_violation"
        else:
            raise AssertionError("privacy scan must fail")


def test_support_bundle_scanner_allows_fixed_safe_vocabulary_and_is_deterministic():
    registry = CollectorRegistry()
    observability = LabObservability(registry, version="test")
    observability.observe("preview", "preview_timeout", "failed")
    first = observability.support_bundle(app_ready=True)
    second = observability.support_bundle(app_ready=True)
    scan_support_bundle({"words": "WHEP HLS MediaMTX provider camera tokenization"})

    assert first["checksum"] == second["checksum"]
    assert set(first) >= {"format", "versions", "safe_settings", "health", "listeners", "recent_errors", "signals", "zero_retention", "checksum"}
    assert first["safe_settings"] == {"mode": "lab", "metrics": "bounded", "retention": "none"}
    assert len(first["recent_errors"]) == 1
    assert set(first["recent_errors"][0]) == {"correlation_id", "component", "error_code", "outcome"}
    observability.check_zero_retention(0)
    changed = observability.support_bundle(app_ready=True)
    assert first["checksum"] != changed["checksum"]


def test_recent_error_ring_and_zero_retention_signal_are_bounded_and_recover():
    observability = LabObservability(CollectorRegistry(), version="test")
    assert observability.check_zero_retention(None) == "not_checked"
    assert observability.status(app_ready=True)["zero_retention"]["state"] == "not_checked"
    assert observability.check_zero_retention(1) == "fail"
    assert {"signal": "retained_media", "state": "active"} in observability.status(app_ready=True)["signals"]
    assert observability.check_zero_retention(0) == "pass"
    assert {"signal": "retained_media", "state": "inactive"} in observability.status(app_ready=True)["signals"]
    for _ in range(60):
        observability.observe("preview", "preview_timeout", "failed")
    bundle = observability.support_bundle(app_ready=True)
    assert len(bundle["recent_errors"]) == 50

def test_status_is_bounded_and_browser_media_is_not_fabricated():
    observability=LabObservability(CollectorRegistry(),version="test")
    observability.observe("preview","preview_timeout","failed")
    status=observability.status(app_ready=True)
    assert status["checks"]["browser_media"]["state"]=="not_started"
    assert status["errors"]==[{"component":"preview","error_code":"preview_timeout"}]

def test_zero_retention_is_metadata_only_and_bounded():
    observability=LabObservability(CollectorRegistry(),version="test")
    assert observability.check_zero_retention(None)=="not_checked"
    assert observability.check_zero_retention(0)=="pass"
    assert observability.check_zero_retention(1)=="fail"


def test_operational_signal_metrics_have_only_fixed_low_cardinality_labels():
    registry = CollectorRegistry()
    observability = LabObservability(registry, version="test")
    observability.capacity(True)
    observability.capacity(False)
    observability.observe("cleanup", "cleanup_failed", "failed")
    observability.observe("cleanup", "none", "healthy")

    forbidden = {"camera_id", "stream_id", "session_id", "user_id", "correlation_id", "provider_url", "provider_locator", "exception_text"}
    for family in registry.collect():
        if not family.name.startswith("hcam_phase2_5_"):
            continue
        for sample in family.samples:
            assert forbidden.isdisjoint(sample.labels)
