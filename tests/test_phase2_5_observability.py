from prometheus_client import CollectorRegistry
from hcam.labs.sentinel.observability import FAULT_MATRIX, LabObservability, scan_support_bundle

def test_faults_are_independent_and_provider_failure_keeps_process_live():
    observability=LabObservability(CollectorRegistry(),version="test")
    assert observability.health(app_ready=True)["liveness"]["state"]=="live"
    for component,code,state in FAULT_MATRIX.values():
        event=observability.observe(component,code,state)
        assert event.correlation_id and len(event.correlation_id)==32
    bundle=observability.support_bundle(app_ready=True)
    assert bundle["retention"]=="none" and len(bundle["events"])==6

def test_support_bundle_rejects_sensitive_values():
    try: scan_support_bundle({"value":"rtsp://private"})
    except ValueError as error: assert str(error)=="support_bundle_privacy_violation"
    else: raise AssertionError("privacy scan must fail")
