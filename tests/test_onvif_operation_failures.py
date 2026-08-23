from __future__ import annotations

import ipaddress
from datetime import timedelta
from unittest.mock import MagicMock
from xml.etree import ElementTree

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from hcam.camera_registry.models import utc_now
from hcam.security.auth import CAMERA_EDITOR, Principal
from hcam.settings import Settings
from hcam.streams import onvif_operations as operations
from hcam.streams.models import OnvifControlLease, OnvifOperationRun, StreamEndpoint
from hcam.streams.network import OnvifEgressRule, OnvifNetworkPolicy
from hcam.streams.onvif import (
    HttpxOnvifTransport,
    OnvifMediaProfile,
    OnvifResolutionError,
    OnvifService,
)
from hcam.streams.schemas import (
    OnvifEventPullRequest,
    OnvifImagingInspectionRequest,
    OnvifPtzCommandRequest,
)
from hcam.streams.secrets import UnconfiguredCameraSecretProvider


def _principal(*, departments: frozenset[str] = frozenset({"*"})) -> Principal:
    return Principal(
        actor_id="operation-tester",
        roles=frozenset({CAMERA_EDITOR}),
        departments=departments,
        authentication_method="test",
    )


def _config(**overrides: object) -> operations.OnvifEndpointConfig:
    values: dict[str, object] = {
        "stream_id": "str_" + "a" * 32,
        "camera_id": "synthetic:test",
        "management_locator": "http://127.0.0.1/onvif/device_service",
        "onvif_auth_mode": "none",
        "secret_ref": None,
        "onvif_control_enabled": True,
        "onvif_max_velocity": 0.5,
        "onvif_max_move_seconds": 1.0,
    }
    values.update(overrides)
    return operations.OnvifEndpointConfig(**values)


def _profile(
    *, source_token: str | None = "source-main", ptz: bool = True
) -> OnvifMediaProfile:
    return OnvifMediaProfile(
        token="main",
        name="Main",
        fixed=True,
        video_encoding="H264",
        width=1920,
        height=1080,
        frame_rate_limit=25,
        audio_encoding=None,
        ptz_configured=ptz,
        analytics_configured=False,
        metadata_configured=False,
        video_source_token=source_token,
    )


def _engine() -> operations.OnvifOperationEngine:
    return operations.OnvifOperationEngine(
        network_policy=OnvifNetworkPolicy(
            rules=(
                OnvifEgressRule(
                    scheme="http",
                    host="127.0.0.1",
                    port=80,
                    approved_addresses=(ipaddress.ip_network("127.0.0.1/32"),),
                ),
            ),
            environment="test",
            lab_http_enabled=True,
        ),
        secret_provider=UnconfiguredCameraSecretProvider(),
        transport=HttpxOnvifTransport(timeout_seconds=0.1),
    )


def _services() -> tuple[OnvifService, ...]:
    return (
        OnvifService(operations._MEDIA_NAMESPACE, "http://127.0.0.1/media", "2.6"),
        OnvifService(
            operations._IMAGING_NAMESPACE, "http://127.0.0.1/imaging", "2.6"
        ),
        OnvifService(operations._EVENTS_NAMESPACE, "http://127.0.0.1/events", "2.6"),
        OnvifService(operations._PTZ_NAMESPACE, "http://127.0.0.1/ptz", "2.6"),
    )


class _Client:
    def __init__(self, responses: list[ElementTree.Element], *, fail_unsubscribe=False):
        self.responses = list(responses)
        self.fail_unsubscribe = fail_unsubscribe

    def request(self, _url: str, body: str, **_kwargs):
        if "Unsubscribe" in body and self.fail_unsubscribe:
            raise OnvifResolutionError("unreachable")
        return self.responses.pop(0)


def test_imaging_inspection_rejects_missing_or_invalid_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine()
    client = _Client([])
    monkeypatch.setattr(
        operations.OnvifOperationEngine,
        "_client_and_services",
        lambda *_args: (client, _services()),
    )
    monkeypatch.setattr(operations, "get_profiles", lambda *_args: ())
    with pytest.raises(operations.OnvifOperationValidationError, match="not found"):
        engine.inspect_imaging(
            _config(),
            OnvifImagingInspectionRequest(profile_token="missing"),
            operation_id="ovf_" + "a" * 32,
        )

    monkeypatch.setattr(
        operations, "get_profiles", lambda *_args: (_profile(source_token=None),)
    )
    with pytest.raises(operations.OnvifOperationValidationError, match="source token"):
        engine.inspect_imaging(
            _config(),
            OnvifImagingInspectionRequest(profile_token="main"),
            operation_id="ovf_" + "b" * 32,
        )

    client.responses.append(ElementTree.fromstring("<Envelope />"))
    monkeypatch.setattr(operations, "get_profiles", lambda *_args: (_profile(),))
    with pytest.raises(operations.OnvifOperationError) as invalid:
        engine.inspect_imaging(
            _config(),
            OnvifImagingInspectionRequest(profile_token="main"),
            operation_id="ovf_" + "c" * 32,
        )
    assert invalid.value.reason_code == "onvif_invalid_imaging_settings"


def test_event_pull_rejects_reference_and_reports_unsubscribe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine()
    missing = _Client([ElementTree.fromstring("<Envelope />")])
    monkeypatch.setattr(
        operations.OnvifOperationEngine,
        "_client_and_services",
        lambda *_args: (missing, _services()),
    )
    with pytest.raises(operations.OnvifOperationError) as invalid:
        engine.pull_events(
            _config(),
            OnvifEventPullRequest(),
            operation_id="ovf_" + "d" * 32,
        )
    assert invalid.value.reason_code == "onvif_invalid_subscription_reference"

    created = ElementTree.fromstring(
        "<Envelope><SubscriptionReference>"
        "<Address>http://127.0.0.1/subscription</Address>"
        "</SubscriptionReference></Envelope>"
    )
    pulled = ElementTree.fromstring(
        "<Envelope><NotificationMessage><Topic>motion</Topic>"
        '<Message UtcTime="invalid" PropertyOperation="Changed">'
        '<SimpleItem Name="" Value="ignored" />'
        '<SimpleItem Name="State" Value="true" />'
        "</Message></NotificationMessage></Envelope>"
    )
    client = _Client([created, pulled], fail_unsubscribe=True)
    monkeypatch.setattr(
        operations.OnvifOperationEngine,
        "_client_and_services",
        lambda *_args: (client, _services()),
    )
    result = engine.pull_events(
        _config(),
        OnvifEventPullRequest(message_limit=2, timeout_seconds=0.1),
        operation_id="ovf_" + "e" * 32,
    )
    assert result.subscription_terminated is False
    assert result.messages[0].utc_time is None
    assert result.messages[0].data == {"State": "true"}


def test_engine_fails_closed_for_credentials_services_and_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine()
    with pytest.raises(operations.OnvifOperationError) as missing:
        engine._client_and_services(
            _config(onvif_auth_mode="http_digest", secret_ref=None)
        )
    assert missing.value.reason_code == "credentials_unavailable"

    with pytest.raises(operations.OnvifOperationError) as provider:
        engine._client_and_services(
            _config(onvif_auth_mode="http_digest", secret_ref="camera/test")
        )
    assert provider.value.reason_code == "camera_secret_provider_unconfigured"

    monkeypatch.setattr(
        operations,
        "get_services",
        lambda *_args: (_ for _ in ()).throw(OnvifResolutionError("unreachable")),
    )
    with pytest.raises(operations.OnvifOperationError) as transport:
        engine._client_and_services(_config())
    assert transport.value.reason_code == "unreachable"

    with pytest.raises(operations.OnvifOperationValidationError, match="advertise"):
        engine._service_url((), operations._IMAGING_NAMESPACE)
    with pytest.raises(operations.OnvifOperationError) as denied:
        engine._validate_url("http://8.8.8.8/onvif/device_service")
    assert denied.value.reason_code == "network_policy_denied"

    endpoint = StreamEndpoint(
        stream_id="str_" + "f" * 32,
        camera_id="synthetic:test",
        name="missing-management",
        adapter_kind="onvif",
        protocol="http",
        locator="http://127.0.0.1/media",
        management_locator=None,
    )
    with pytest.raises(operations.OnvifOperationValidationError, match="management"):
        operations.OnvifEndpointConfig.from_endpoint(endpoint)


def test_operation_service_normalizes_and_records_callback_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = operations.OnvifOperationService(MagicMock(), Settings(environment="test"))
    recorded: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        service,
        "_begin_record",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        service,
        "_complete_record",
        lambda _operation_id, _config, _operation_type, outcome, reason_code, *_args: (
            recorded.append((outcome, reason_code))
        ),
    )
    arguments = {
        "operation_type": "imaging_inspect",
        "parameters": {},
        "principal": _principal(),
        "reason": "Authorized callback normalization test",
        "request_id": "request-1",
    }
    with pytest.raises(operations.OnvifOperationError) as transport:
        service._execute_with_config(
            _config(),
            callback=lambda _operation_id: (_ for _ in ()).throw(
                OnvifResolutionError("unreachable")
            ),
            **arguments,
        )
    assert transport.value.reason_code == "unreachable"
    with pytest.raises(operations.OnvifOperationValidationError):
        service._execute_with_config(
            _config(),
            callback=lambda _operation_id: (_ for _ in ()).throw(
                operations.OnvifOperationValidationError("invalid")
            ),
            **arguments,
        )
    assert (
        service._execute_with_config(
            _config(), callback=lambda _operation_id: "ok", **arguments
        )
        == "ok"
    )
    assert recorded[0] == ("failure", "unreachable")
    assert recorded[1][0] == "failure"
    assert recorded[2] == ("success", None)


def test_operation_persistence_failures_are_not_silently_ignored() -> None:
    session = MagicMock()
    session.begin.side_effect = SQLAlchemyError("database unavailable")
    service = operations.OnvifOperationService(session, Settings(environment="test"))
    with pytest.raises(operations.OnvifOperationError) as release:
        service._release_control_lease("str_" + "a" * 32, "ovl_test")
    assert release.value.reason_code == "control_lease_release_failed"
    with pytest.raises(operations.OnvifOperationError) as audit:
        service._begin_record(
            "ovf_" + "a" * 32,
            _config(),
            "imaging_inspect",
            {},
            _principal(),
            "Authorized audit persistence failure test",
            "request-audit",
            utc_now(),
        )
    assert audit.value.reason_code == "operation_audit_unavailable"
    callback = MagicMock(return_value="must-not-run")
    with pytest.raises(operations.OnvifOperationError) as blocked:
        service._execute_with_config(
            _config(),
            operation_type="imaging_inspect",
            parameters={},
            principal=_principal(),
            reason="Authorized fail-closed intent test",
            request_id="request-intent",
            callback=callback,
        )
    assert blocked.value.reason_code == "operation_audit_unavailable"
    callback.assert_not_called()


def test_operation_completion_failure_preserves_pending_intent(
    imported_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with imported_app.state.database.session_factory() as session:
        stream_id = session.scalar(select(StreamEndpoint.stream_id))
        session.rollback()
        assert stream_id is not None
        service = operations.OnvifOperationService(session, imported_app.state.settings)
        config = _config(stream_id=stream_id)
        operation_id = "ovf_" + "e" * 32
        requested_at = utc_now()
        service._begin_record(
            operation_id,
            config,
            "imaging_inspect",
            {},
            _principal(),
            "Authorized pending intent preservation test",
            "request-pending",
            requested_at,
        )

        def fail_completion(*_args, **_kwargs):
            raise SQLAlchemyError("audit sink unavailable")

        monkeypatch.setattr(operations.AuditRepository, "record", fail_completion)
        with pytest.raises(operations.OnvifOperationError) as captured:
            service._complete_record(
                operation_id,
                config,
                "imaging_inspect",
                "success",
                None,
                {},
                _principal(),
                "Authorized pending intent preservation test",
                "request-pending",
                requested_at,
                0.0,
            )
        assert captured.value.reason_code == "operation_audit_unavailable"
        run = session.get(OnvifOperationRun, operation_id)
        assert run is not None
        assert run.outcome == "pending"
        assert run.finished_at is None
        assert run.duration_ms is None


def test_operation_helpers_handle_empty_oversized_and_invalid_values() -> None:
    assert operations._first(None, "Value") is None
    assert operations._text(None) is None
    assert operations._number(ElementTree.fromstring("<Root />"), "Value") is None
    with pytest.raises(operations.OnvifOperationError) as oversized:
        operations._text(ElementTree.fromstring(f"<Value>{'x' * 501}</Value>"))
    assert oversized.value.reason_code == "onvif_response_value_too_large"
    with pytest.raises(operations.OnvifOperationError) as invalid:
        operations._number(
            ElementTree.fromstring("<Root><Value>not-number</Value></Root>"),
            "Value",
        )
    assert invalid.value.reason_code == "onvif_invalid_numeric_value"
    messages = operations._parse_events(
        ElementTree.fromstring(
            "<Root><NotificationMessage><Topic>status</Topic>"
            "</NotificationMessage></Root>"
        ),
        1,
    )
    assert messages[0].data == {}
    assert messages[0].property_operation is None


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "relative", "profile_token": "main"},
        {"action": "continuous", "profile_token": "main", "pan": 0.1},
        {"action": "goto_preset", "profile_token": "main"},
        {"action": "stop", "profile_token": "main", "preset_token": "p1"},
        {"action": "stop", "profile_token": "main", "duration_seconds": 1},
        {"action": "stop", "profile_token": "main", "pan": 0.1},
    ],
)
def test_ptz_schema_rejects_action_specific_field_mismatches(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        OnvifPtzCommandRequest.model_validate(payload)


def test_operation_authorization_and_control_lease_conflict(imported_app) -> None:
    settings = imported_app.state.settings
    with imported_app.state.database.session_factory() as session:
        service = operations.OnvifOperationService(session, settings)
        with pytest.raises(operations.OnvifOperationNotFoundError):
            service._authorized_config(
                "str_" + "0" * 32, _principal(departments=frozenset())
            )
        with pytest.raises(operations.OnvifOperationNotFoundError):
            service._authorized_config("str_" + "0" * 32, _principal())
        legacy_stream_id = session.scalar(select(StreamEndpoint.stream_id))
        session.rollback()
        assert legacy_stream_id is not None
        with pytest.raises(operations.OnvifOperationValidationError, match="enabled ONVIF"):
            service._authorized_config(legacy_stream_id, _principal())

        config = _config(stream_id=legacy_stream_id)
        now = utc_now()
        with session.begin():
            session.add(
                OnvifControlLease(
                    stream_id=legacy_stream_id,
                    lease_id="ovl_existing",
                    actor_id="other-controller",
                    acquired_at=now,
                    expires_at=now + timedelta(minutes=1),
                )
            )
        with pytest.raises(operations.OnvifOperationConflictError):
            service._acquire_control_lease(config, _principal())
