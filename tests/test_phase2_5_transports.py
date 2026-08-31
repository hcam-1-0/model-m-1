from __future__ import annotations

import pytest

from hcam.labs.sentinel.dashboard import generated_lab_policy
from hcam.labs.sentinel.fixtures import generated_catalog_document
from hcam.labs.sentinel.models import normalize_catalog_document
from hcam.labs.sentinel.secrets import SecretResolutionError
from hcam.labs.sentinel.transports import (
    TransportSelectionError,
    UnconfiguredMediaSecretProvider,
    select_inference_transport,
)


class ConfiguredReceiver:
    @property
    def configured(self) -> bool:
        return True


def camera_one():
    catalog = normalize_catalog_document(
        generated_catalog_document(mode="compatibility"),
        origin="http://catalog-simulator:8090/api/ingest",
        network_policy=generated_lab_policy(),
    )
    return catalog.cameras[0]


def test_rtsp_tcp_is_the_only_default_inference_transport() -> None:
    plan = select_inference_transport(camera_one())

    assert plan.transport == "rtsp_tcp"
    assert plan.rtsp_transport == "tcp"
    assert plan.feature_gate is None
    assert plan.analytics_authorized is False
    assert "locator" not in plan.sanitized()


def test_whep_inference_is_default_off_and_requires_receiver() -> None:
    camera = camera_one()

    with pytest.raises(TransportSelectionError, match="whep_inference_feature_disabled"):
        select_inference_transport(camera, requested="whep")
    with pytest.raises(TransportSelectionError, match="whep_inference_receiver_unconfigured"):
        select_inference_transport(camera, requested="whep", whep_inference_enabled=True)


def test_whep_inference_plan_is_feature_gated_and_still_non_analytic() -> None:
    plan = select_inference_transport(
        camera_one(),
        requested="whep",
        whep_inference_enabled=True,
        whep_receiver=ConfiguredReceiver(),
    )

    assert plan.transport == "whep"
    assert plan.feature_gate == "HCAM_PHASE2_5_WHEP_INFERENCE_ENABLED"
    assert plan.receiver_configured
    assert plan.analytics_authorized is False


def test_media_credentials_fail_closed_independently_of_catalogue_credentials() -> None:
    with pytest.raises(SecretResolutionError, match="media_secret_provider_unconfigured"):
        UnconfiguredMediaSecretProvider().resolve("media-secret", "bearer")
