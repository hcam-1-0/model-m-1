from __future__ import annotations

import copy
from collections.abc import Mapping

import pytest
from pydantic import ValidationError

from hcam.analytics.anpr import (
    AnprBoundaryViolation,
    EphemeralSyntheticTokenV1,
    SyntheticAnprExecutionPolicyV1,
    anpr_contract_bundle,
    authorize_generated_request,
    canonical_anpr_evidence_json,
    validate_ephemeral_synthetic_token,
)
from hcam.analytics.anpr.contracts import generated_request_fixture


def _request() -> dict[str, object]:
    return generated_request_fixture().model_dump(mode="json")


def _enabled_policy() -> SyntheticAnprExecutionPolicyV1:
    return SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


def test_seed_only_generated_request_is_authorized_by_explicit_test_policy() -> None:
    parsed = authorize_generated_request(_request(), policy=_enabled_policy())

    assert parsed.source_id == "DATA-PLATE-GEN-R0"
    assert parsed.input_mode == "deterministic_seed_only"
    assert parsed.token_class == "synthetic_non_issuable"
    assert parsed.synthetic_only is True


def test_generated_anpr_policy_is_default_off_and_production_forbidden() -> None:
    with pytest.raises(AnprBoundaryViolation) as disabled:
        authorize_generated_request(
            _request(),
            policy=SyntheticAnprExecutionPolicyV1(),
        )
    assert disabled.value.code == "runtime_disabled"

    with pytest.raises(ValidationError, match="forbidden in production"):
        SyntheticAnprExecutionPolicyV1(enabled=True, environment="production")


@pytest.mark.parametrize(
    "field",
    [
        "token",
        "text",
        "file_path",
        "url",
        "upload",
        "image_bytes",
        "camera_id",
        "stream_id",
        "owner_record",
        "vehicle_record",
        "watchlist_match",
        "registration_mark",
    ],
)
def test_prohibited_input_fields_fail_before_schema_validation(field: str) -> None:
    document = _request()
    secret = "must-not-echo-7dca"
    document[field] = secret

    with pytest.raises(AnprBoundaryViolation) as exc_info:
        authorize_generated_request(document, policy=_enabled_policy())

    assert exc_info.value.code == "prohibited_input_field"
    assert secret not in str(exc_info.value)


def test_nested_prohibited_field_is_rejected_without_echoing_value() -> None:
    document = _request()
    document["future"] = {"nested": {"watchlist": "must-not-echo"}}

    with pytest.raises(AnprBoundaryViolation) as exc_info:
        authorize_generated_request(document, policy=_enabled_policy())

    assert exc_info.value.code == "prohibited_input_field"
    assert "must-not-echo" not in str(exc_info.value)


@pytest.mark.parametrize(
    "value",
    [
        "https://example.invalid/plate.png",
        "rtsp://user:secret@example.invalid/live",
        "file:///tmp/plate.png",
        "data:image/png;base64,AAAA",
        "C:\\private\\plate.png",
        "\\\\server\\share\\plate.png",
        "../private/plate.png",
        "Bearer must-not-echo",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_prohibited_string_sources_are_value_redacted(value: str) -> None:
    document = _request()
    document["future_note"] = value

    with pytest.raises(AnprBoundaryViolation) as exc_info:
        authorize_generated_request(document, policy=_enabled_policy())

    assert exc_info.value.code == "prohibited_input_value"
    assert value not in str(exc_info.value)


def test_arbitrary_bytes_depth_node_and_size_limits_fail_closed() -> None:
    document = _request()
    document["future"] = b"not-an-image-but-still-prohibited"
    with pytest.raises(AnprBoundaryViolation) as binary:
        authorize_generated_request(document, policy=_enabled_policy())
    assert binary.value.code == "arbitrary_bytes_prohibited"

    deep: dict[str, object] = _request()
    cursor: dict[str, object] = deep
    for index in range(10):
        nested: dict[str, object] = {}
        cursor[f"level_{index}"] = nested
        cursor = nested
    with pytest.raises(AnprBoundaryViolation) as too_deep:
        authorize_generated_request(deep, policy=_enabled_policy())
    assert too_deep.value.code == "document_too_deep"

    many = _request()
    many["future"] = list(range(300))
    with pytest.raises(AnprBoundaryViolation) as too_many:
        authorize_generated_request(many, policy=_enabled_policy())
    assert too_many.value.code == "document_too_many_nodes"

    large = _request()
    large["future_note"] = "x" * 4_096
    with pytest.raises(AnprBoundaryViolation) as too_large:
        authorize_generated_request(large, policy=_enabled_policy())
    assert too_large.value.code == "document_too_large"


def test_unknown_fields_and_invalid_values_collapse_to_safe_reason() -> None:
    document = _request()
    document["future_note"] = "must-not-echo"

    with pytest.raises(AnprBoundaryViolation) as extra:
        authorize_generated_request(document, policy=_enabled_policy())
    assert extra.value.code == "invalid_generated_request"
    assert "must-not-echo" not in str(extra.value)
    assert extra.value.__cause__ is None
    assert extra.value.__context__ is None

    invalid = _request()
    invalid["seed"] = -1
    with pytest.raises(AnprBoundaryViolation) as seed:
        authorize_generated_request(invalid, policy=_enabled_policy())
    assert seed.value.code == "invalid_generated_request"


@pytest.mark.parametrize(
    "token",
    ["SYN-A0B1-C2D3", "SYN-O0I1-B8Z9", "SYN-1234-ABCD"],
)
def test_visible_synthetic_namespace_accepts_only_bounded_mixed_tokens(
    token: str,
) -> None:
    parsed = validate_ephemeral_synthetic_token(
        {
            "request_id": "anprreq_11111111111111111111111111111111",
            "token": token,
            "layout": "single_line",
        }
    )

    assert parsed.token == token
    assert parsed.persistence == "prohibited"


@pytest.mark.parametrize(
    "token",
    [
        "GJ01AB1234",
        "SYN-ABCD-EFGH",
        "SYN-1234-5678",
        "SYN-ab12-CD34",
        "SYN-A1B2-C3D4-extra",
        "SYN-A1B2-ક૩D4",
    ],
)
def test_real_looking_or_malformed_tokens_are_rejected_without_echo(token: str) -> None:
    with pytest.raises(AnprBoundaryViolation) as exc_info:
        validate_ephemeral_synthetic_token(
            {
                "request_id": "anprreq_11111111111111111111111111111111",
                "token": token,
                "layout": "single_line",
            }
        )

    assert exc_info.value.code == "invalid_synthetic_token"
    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_ephemeral_token_document_is_structurally_bounded() -> None:
    document: dict[str, object] = {
        "request_id": "anprreq_11111111111111111111111111111111",
        "token": "SYN-A0B1-C2D3",
        "layout": "single_line",
        "future": b"must-not-echo",
    }
    with pytest.raises(AnprBoundaryViolation) as binary:
        validate_ephemeral_synthetic_token(document)
    assert binary.value.code == "arbitrary_bytes_prohibited"
    assert "must-not-echo" not in str(binary.value)

    deep: dict[str, object] = {
        "request_id": "anprreq_11111111111111111111111111111111",
        "token": "SYN-A0B1-C2D3",
        "layout": "single_line",
    }
    cursor = deep
    for index in range(10):
        nested: dict[str, object] = {}
        cursor[f"level_{index}"] = nested
        cursor = nested
    with pytest.raises(AnprBoundaryViolation) as too_deep:
        validate_ephemeral_synthetic_token(deep)
    assert too_deep.value.code == "document_too_deep"


def test_ephemeral_plate_text_cannot_enter_canonical_evidence() -> None:
    token = validate_ephemeral_synthetic_token(
        {
            "request_id": "anprreq_11111111111111111111111111111111",
            "token": "SYN-A0B1-C2D3",
            "layout": "two_line",
        }
    )
    assert isinstance(token, EphemeralSyntheticTokenV1)

    with pytest.raises(AnprBoundaryViolation) as direct:
        canonical_anpr_evidence_json(token)
    assert direct.value.code == "plate_text_persistence_prohibited"

    for field in ("plate_text", "raw_text", "normalized_text", "alternatives"):
        with pytest.raises(AnprBoundaryViolation) as nested:
            canonical_anpr_evidence_json({"aggregate": {field: "must-not-echo"}})
        assert nested.value.code == "plate_text_persistence_prohibited"
        assert "must-not-echo" not in str(nested.value)

    for alias in ("plateText", "Plate Text", "registration-mark", "ocr.text"):
        with pytest.raises(AnprBoundaryViolation) as aliased:
            canonical_anpr_evidence_json({"aggregate": {alias: "must-not-echo"}})
        assert aliased.value.code == "plate_text_persistence_prohibited"


def test_contract_bundle_exposes_no_arbitrary_input_or_retention_path() -> None:
    bundle = anpr_contract_bundle()
    contracts = bundle["contracts"]
    assert isinstance(contracts, Mapping)
    request = contracts["generated_request"]
    assert isinstance(request, Mapping)
    properties = request["properties"]
    assert isinstance(properties, Mapping)

    assert set(properties) == {
        "contract_type",
        "generator_version",
        "input_mode",
        "layout",
        "policy_id",
        "policy_version",
        "request_id",
        "sample_index",
        "script",
        "seed",
        "source_id",
        "synthetic_only",
        "token_class",
    }
    assert bundle["source_policy"]["external_text_allowed"] is False
    assert bundle["source_policy"]["file_url_upload_or_media_allowed"] is False
    assert bundle["persistence_policy"]["plate_text_retention_hours"] == 0


def test_request_contract_is_frozen() -> None:
    parsed = authorize_generated_request(_request(), policy=_enabled_policy())
    changed = copy.copy(parsed)

    with pytest.raises(ValidationError):
        changed.seed = 9
