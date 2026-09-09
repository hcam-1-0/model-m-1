"""Privacy-safe, bounded observability for the Phase 2.5 lab."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from re import compile
from uuid import uuid4

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

_FORBIDDEN = (
    compile(r"(?i)(?:https?|rtsp)://"),
    compile(r"(?i)\b(?:access[_ -]?token|api[_ -]?key|token|secret|password)\s*[:=]\s*\S+"),
    compile(r"(?i)\bauthorization\s*:\s*\S+"),
    compile(r"(?i)\bbearer\s+[a-z0-9._~+\-/=]+"),
    compile(r"(?i)\b(?:provider[_ -]?(?:payload|locator)|camera[_ -]?id|stream[_ -]?id|session[_ -]?id)\s*[:=]\s*\S+"),
    compile(r"(?i)v=0.*sdp"),
)
_CODES = frozenset(
    {
        "catalog_upstream_failed",
        "catalog_empty",
        "catalog_schema_rejected",
        "mediamtx_unavailable",
        "preview_timeout",
        "cleanup_failed",
    }
)
_COMPONENTS = (
    "provider",
    "catalogue",
    "relay",
    "gateway",
    "preview",
    "cleanup",
)
_OUTCOMES = frozenset({"healthy", "degraded", "failed", "not_started", "unknown"})
_SIGNALS = (
    "catalogue_freshness",
    "schema_rejection_threshold",
    "capacity_exhaustion",
    "cleanup_failure",
    "relay_leakage",
    "retained_media",
)


@dataclass(frozen=True, slots=True)
class SafeEvent:
    correlation_id: str
    component: str
    error_code: str
    outcome: str


class LabObservability:
    """In-memory, no-retention events plus bounded operational signals."""

    schema_rejection_threshold = 3

    def __init__(self, registry: CollectorRegistry, *, version: str) -> None:
        self.events: deque[SafeEvent] = deque(maxlen=50)
        self.version = version
        self.state = Gauge(
            "hcam_phase2_5_component_state",
            "Component state (1 means current state).",
            ("component", "state"),
            registry=registry,
        )
        self.failures = Counter(
            "hcam_phase2_5_failures_total",
            "Bounded Phase 2.5 failures.",
            ("component", "error_code"),
            registry=registry,
        )
        self.duration = Histogram(
            "hcam_phase2_5_operation_duration_seconds",
            "Phase 2.5 operation latency.",
            ("component", "outcome"),
            registry=registry,
        )
        self.operational_signal = Gauge(
            "hcam_phase2_5_operational_signal",
            "Bounded operational safety signals (1 means current state).",
            ("signal", "state"),
            registry=registry,
        )
        self.current: dict[str, str] = {}
        self.current_codes: dict[str, str | None] = {}
        self.signals: dict[str, str] = {}
        self.schema_rejections = 0
        self.zero_retention = "not_checked"

    def correlation_id(self) -> str:
        return uuid4().hex

    def observe(
        self,
        component: str,
        error_code: str,
        outcome: str = "failed",
        correlation_id: str | None = None,
    ) -> SafeEvent:
        if component not in _COMPONENTS or error_code not in _CODES | {"none"}:
            raise ValueError("unapproved observability dimension")
        if outcome not in _OUTCOMES:
            raise ValueError("unapproved observability dimension")
        event = SafeEvent(correlation_id or self.correlation_id(), component, error_code, outcome)
        self.events.append(event)
        self._set_component(component, outcome, None if error_code == "none" else error_code)
        if error_code != "none":
            self.failures.labels(component=component, error_code=error_code).inc()
        if error_code == "catalog_schema_rejected":
            self.schema_rejections += 1
            self._set_signal(
                "schema_rejection_threshold",
                "active" if self.schema_rejections >= self.schema_rejection_threshold else "inactive",
            )
        elif component == "catalogue" and error_code == "none" and outcome == "healthy":
            self.schema_rejections = 0
            self._set_signal("schema_rejection_threshold", "inactive")
        if component == "cleanup":
            self._set_signal("cleanup_failure", "active" if error_code == "cleanup_failed" else "inactive")
            self._set_signal("relay_leakage", "active" if error_code == "cleanup_failed" else "inactive")
        return event

    def catalogue_freshness(self, age_seconds: float | None, threshold_seconds: float) -> str:
        if age_seconds is None:
            state = "not_checked"
        elif age_seconds > threshold_seconds:
            state = "stale"
            self._set_component("catalogue", "degraded", None)
        else:
            state = "fresh"
            if self.current.get("catalogue") == "degraded" and self.current_codes.get("catalogue") is None:
                self._set_component("catalogue", "healthy", None)
        self._set_signal("catalogue_freshness", state)
        return state

    def capacity(self, exhausted: bool) -> None:
        self._set_signal("capacity_exhaustion", "active" if exhausted else "inactive")

    def health(self, *, app_ready: bool) -> dict[str, object]:
        def state(component: str, default: str) -> dict[str, str]:
            return {"state": self.current.get(component, default), "dependency": component}

        return {
            "liveness": {"state": "live", "dependency": "process"},
            "readiness": {
                "state": "ready" if app_ready else "not_ready",
                "dependency": "local_store_and_metrics",
            },
            "catalogue": state("catalogue", "unknown"),
            "provider": state("provider", "unknown"),
            "relay": state("relay", "not_started"),
            "gateway": state("gateway", "not_started"),
            "preview": state("preview", "not_started"),
            "cleanup": state("cleanup", "not_started"),
            "browser_media": {"state": "not_started", "dependency": "browser_decode_evidence"},
        }

    def status(self, *, app_ready: bool) -> dict[str, object]:
        """Deterministic browser-safe status: only allowlisted states and codes."""
        checks = self.health(app_ready=app_ready)
        components = [
            {
                "component": component,
                "state": checks[component]["state"],
                "error_code": self.current_codes.get(component),
            }
            for component in _COMPONENTS
        ]
        return {
            "checks": checks,
            "components": components,
            "errors": [
                {"component": item["component"], "error_code": item["error_code"]}
                for item in components
                if item["error_code"] is not None
            ],
            "signals": [
                {"signal": signal, "state": self.signals.get(signal, "not_checked")}
                for signal in _SIGNALS
            ],
            "zero_retention": {"state": self.zero_retention},
        }

    def check_zero_retention(self, retained_artifacts: int | None) -> str:
        self.zero_retention = "not_checked" if retained_artifacts is None else ("pass" if retained_artifacts == 0 else "fail")
        self._set_signal(
            "retained_media",
            "not_checked"
            if retained_artifacts is None
            else ("inactive" if retained_artifacts == 0 else "active"),
        )
        return self.zero_retention

    def support_bundle(self, *, app_ready: bool) -> dict[str, object]:
        bundle = {
            "format": "hcam.phase2_5.support.v1",
            "versions": {"lab": self.version},
            "safe_settings": {"mode": "lab", "metrics": "bounded", "retention": "none"},
            "health": self.health(app_ready=app_ready),
            "listeners": [{"component": "dashboard", "state": "local"}, {"component": "metrics", "state": "protected"}],
            "recent_errors": [asdict(event) for event in self.events if event.error_code != "none"],
            "signals": self.status(app_ready=app_ready)["signals"],
            "zero_retention": {"state": self.zero_retention},
            "retention": "none",
        }
        scan_support_bundle(bundle)
        bundle["checksum"] = sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
        return bundle

    def _set_component(self, component: str, outcome: str, code: str | None) -> None:
        previous = self.current.get(component)
        if previous and previous != outcome:
            self.state.labels(component=component, state=previous).set(0)
        self.state.labels(component=component, state=outcome).set(1)
        self.current[component] = outcome
        self.current_codes[component] = code

    def _set_signal(self, signal: str, state: str) -> None:
        previous = self.signals.get(signal)
        if previous and previous != state:
            self.operational_signal.labels(signal=signal, state=previous).set(0)
        self.operational_signal.labels(signal=signal, state=state).set(1)
        self.signals[signal] = state


def scan_support_bundle(bundle: object) -> None:
    rendered = repr(bundle)
    if any(pattern.search(rendered) for pattern in _FORBIDDEN):
        raise ValueError("support_bundle_privacy_violation")


FAULT_MATRIX = {
    "provider_502": ("provider", "catalog_upstream_failed", "degraded"),
    "empty_catalogue": ("catalogue", "catalog_empty", "degraded"),
    "schema_drift": ("catalogue", "catalog_schema_rejected", "failed"),
    "mediamtx_unavailable": ("relay", "mediamtx_unavailable", "degraded"),
    "preview_timeout": ("preview", "preview_timeout", "failed"),
    "cleanup_failure": ("cleanup", "cleanup_failed", "failed"),
}
