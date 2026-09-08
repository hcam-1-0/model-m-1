"""Privacy-safe, bounded observability for the Phase 2.5 lab.

This module intentionally records only stable component/outcome/error-code
dimensions.  It never accepts locators, media payloads, credentials, or IDs.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from hashlib import sha256
from re import compile
from time import time
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry

_FORBIDDEN = compile(r"(?i)(https?://|rtsp://|whep|sdp|token|secret|password|authorization|camera[_ -]?id|provider[_ -]?(payload|locator))")
_CODES = frozenset({"catalog_upstream_failed", "catalog_empty", "catalog_schema_rejected", "mediamtx_unavailable", "preview_timeout", "cleanup_failed"})

@dataclass(frozen=True, slots=True)
class SafeEvent:
    correlation_id: str
    component: str
    error_code: str
    outcome: str

class LabObservability:
    """In-memory, no-retention event ring and bounded metrics."""
    def __init__(self, registry: CollectorRegistry, *, version: str) -> None:
        self.events: deque[SafeEvent] = deque(maxlen=50)
        self.version = version
        self.state = Gauge("hcam_phase2_5_component_state", "Component state (1 means current state).", ("component", "state"), registry=registry)
        self.failures = Counter("hcam_phase2_5_failures_total", "Bounded Phase 2.5 failures.", ("component", "error_code"), registry=registry)
        self.duration = Histogram("hcam_phase2_5_operation_duration_seconds", "Phase 2.5 operation latency.", ("component", "outcome"), registry=registry)

    def correlation_id(self) -> str:
        return uuid4().hex

    def observe(self, component: str, error_code: str, outcome: str = "failed") -> SafeEvent:
        if component not in {"catalogue", "provider", "relay", "gateway", "preview", "cleanup"} or error_code not in _CODES | {"none"} or outcome not in {"healthy", "degraded", "failed", "not_started"}:
            raise ValueError("unapproved observability dimension")
        event = SafeEvent(self.correlation_id(), component, error_code, outcome)
        self.events.append(event)
        self.state.labels(component=component, state=outcome).set(1)
        if error_code != "none": self.failures.labels(component=component, error_code=error_code).inc()
        return event

    def health(self, *, app_ready: bool) -> dict[str, object]:
        # Provider/relay failures are dependencies, never process liveness.
        return {"liveness":{"state":"live","dependency":"process"}, "readiness":{"state":"ready" if app_ready else "not_ready","dependency":"database_and_auth"}, "catalogue":{"dependency":"provider"}, "provider":{"dependency":"external"}, "relay":{"dependency":"mediamtx"}, "gateway":{"dependency":"gateway"}, "browser_media":{"dependency":"browser_only"}}

    def support_bundle(self, *, app_ready: bool) -> dict[str, object]:
        bundle={"format":"hcam.phase2_5.support.v1","versions":{"lab":self.version},"safe_settings":{"mode":"lab","metrics":"bounded","retention":"none"},"health":self.health(app_ready=app_ready),"listeners":[{"component":"dashboard","state":"local"},{"component":"metrics","state":"protected"}],"recent_errors":[asdict(event) for event in self.events],"retention":"none"}
        scan_support_bundle(bundle)
        bundle["checksum"]=sha256(repr(bundle).encode()).hexdigest()
        return bundle

def scan_support_bundle(bundle: object) -> None:
    if _FORBIDDEN.search(repr(bundle)):
        raise ValueError("support_bundle_privacy_violation")

FAULT_MATRIX={
    "provider_502":("provider","catalog_upstream_failed","degraded"),
    "empty_catalogue":("catalogue","catalog_empty","degraded"),
    "schema_drift":("catalogue","catalog_schema_rejected","failed"),
    "mediamtx_unavailable":("relay","mediamtx_unavailable","degraded"),
    "preview_timeout":("preview","preview_timeout","failed"),
    "cleanup_failure":("cleanup","cleanup_failed","failed"),
}
