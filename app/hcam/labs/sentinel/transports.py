from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from hcam.labs.sentinel.models import CatalogCamera, CatalogEndpoint
from hcam.labs.sentinel.secrets import (
    AuthMode,
    CatalogCredential,
    SecretResolutionError,
)


InferenceTransport = Literal["rtsp_tcp", "whep"]


class TransportSelectionError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class MediaSecretProvider(Protocol):
    """Separate typed credential source for media sessions."""

    def resolve(self, secret_ref: str, auth_mode: AuthMode) -> CatalogCredential: ...


class UnconfiguredMediaSecretProvider:
    def resolve(self, secret_ref: str, auth_mode: AuthMode) -> CatalogCredential:
        del secret_ref, auth_mode
        raise SecretResolutionError("media_secret_provider_unconfigured")


class WhepReceiver(Protocol):
    """Receiver plug-in boundary; Phase 2.5 itself never decodes frames."""

    @property
    def configured(self) -> bool: ...


class UnconfiguredWhepReceiver:
    @property
    def configured(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class InferenceTransportPlan:
    transport: InferenceTransport
    endpoint: CatalogEndpoint
    rtsp_transport: Literal["tcp"] | None
    feature_gate: str | None
    receiver_configured: bool
    analytics_authorized: bool = False

    def sanitized(self) -> dict[str, object]:
        return {
            "analytics_authorized": self.analytics_authorized,
            "endpoint_locator_sha256": self.endpoint.locator_sha256,
            "endpoint_protocol": self.endpoint.protocol,
            "feature_gate": self.feature_gate,
            "receiver_configured": self.receiver_configured,
            "rtsp_transport": self.rtsp_transport,
            "transport": self.transport,
        }


def select_inference_transport(
    camera: CatalogCamera,
    *,
    requested: InferenceTransport = "rtsp_tcp",
    whep_inference_enabled: bool = False,
    whep_receiver: WhepReceiver | None = None,
) -> InferenceTransportPlan:
    if requested == "rtsp_tcp":
        endpoint = next(
            (
                item
                for item in camera.endpoints
                if item.role == "inference" and item.protocol == "rtsp"
            ),
            None,
        )
        if endpoint is None:
            raise TransportSelectionError("rtsp_inference_endpoint_missing")
        return InferenceTransportPlan(
            transport="rtsp_tcp",
            endpoint=endpoint,
            rtsp_transport="tcp",
            feature_gate=None,
            receiver_configured=True,
        )

    if not whep_inference_enabled:
        raise TransportSelectionError("whep_inference_feature_disabled")
    receiver = whep_receiver or UnconfiguredWhepReceiver()
    if not receiver.configured:
        raise TransportSelectionError("whep_inference_receiver_unconfigured")
    endpoint = next(
        (
            item
            for item in camera.endpoints
            if item.role == "preview" and item.protocol in {"http", "https"}
        ),
        None,
    )
    if endpoint is None:
        raise TransportSelectionError("whep_inference_endpoint_missing")
    return InferenceTransportPlan(
        transport="whep",
        endpoint=endpoint,
        rtsp_transport=None,
        feature_gate="HCAM_PHASE2_5_WHEP_INFERENCE_ENABLED",
        receiver_configured=True,
    )
