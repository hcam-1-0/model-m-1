from __future__ import annotations

import base64

import pytest

from hcam.intelligence.rules import cel_adapter
from hcam.intelligence.rules.bounds import RuleBounds, RuleLimitError
from hcam.intelligence.rules.cel_adapter import (
    ConstrainedRuleCelEnvironment,
    RuleCelError,
)


def context() -> dict[str, object]:
    return {
        "event_kind": "generated.vehicle.observed",
        "object_class": "vehicle.car",
        "confidence": 0.9,
        "uncertainty": 0.1,
        "direction": "forward",
        "count": 3,
        "rate": 2.0,
        "chronology_complete": True,
        "contradiction": False,
        "schedule_open": True,
        "prior_result": False,
    }


def test_closed_cel_compiles_structurally_and_evaluates_checked_bytes() -> None:
    environment = ConstrainedRuleCelEnvironment()
    checked = environment.compile(
        "confidence >= 0.75 && chronology_complete && !contradiction", "n001"
    )
    assert checked.compilation.profile == "hcam.p4-2.constrained-cel.v1"
    assert checked.compilation.ast_node_count >= 6
    assert checked.compilation.checked_sha256.startswith("sha256:")
    assert environment.evaluate(checked, context()) is True
    assert environment.evaluate(checked.compilation, context()) is True


@pytest.mark.parametrize(
    "source",
    [
        "camera.owner == 'private'",
        "[1, 2].exists(x, x > 0)",
        "object_class.matches('car.*')",
        "has(camera.owner)",
        "{'key': 1}",
        "confidence",
        "count && true",
        "event_kind + 'x' == 'x'",
        "confidence in [0.5, 1.0]",
    ],
)
def test_closed_cel_rejects_dynamic_collections_selectors_macros_and_types(
    source: str,
) -> None:
    with pytest.raises((RuleCelError, RuleLimitError)):
        ConstrainedRuleCelEnvironment().compile(source, "n001")


def test_cel_context_and_checked_integrity_fail_closed() -> None:
    environment = ConstrainedRuleCelEnvironment()
    checked = environment.compile("count >= 2", "n001")
    incomplete = context()
    incomplete.pop("count")
    with pytest.raises(RuleCelError, match="closed schema"):
        environment.evaluate(checked, incomplete)
    wrong = context()
    wrong["count"] = True
    with pytest.raises(RuleCelError, match="invalid scalar"):
        environment.evaluate(checked, wrong)
    corrupted = checked.compilation.model_copy(
        update={"checked_bytes_b64": base64.b64encode(b"corrupt").decode("ascii")}
    )
    with pytest.raises(RuleCelError, match="integrity"):
        environment.evaluate(corrupted, context())


def test_cel_hard_static_limits_are_enforced() -> None:
    with pytest.raises(RuleLimitError, match="node"):
        ConstrainedRuleCelEnvironment(RuleBounds(cel_ast_nodes=3)).compile(
            "confidence > 0.5 && chronology_complete", "n001"
        )
    with pytest.raises(RuleCelError, match="byte"):
        ConstrainedRuleCelEnvironment(RuleBounds(cel_source_bytes=8)).compile(
            "count > 1", "n001"
        )


@pytest.mark.parametrize(
    "source",
    [
        "!(chronology_complete && contradiction)",
        "-count < 0",
        "(confidence + 0.1) / 2.0 >= 0.5",
        "count % 2 == 1",
        "event_kind != 'x' || schedule_open",
        "object_class < 'z'",
    ],
)
def test_closed_cel_supports_the_allowlisted_scalar_operator_set(source: str) -> None:
    checked = ConstrainedRuleCelEnvironment().compile(source, "n001")
    assert checked.compilation.ast_node_count >= 3


@pytest.mark.parametrize(
    "source",
    [
        "",
        "(",
        ")",
        "!count",
        "-event_kind",
        "count ==",
        "count true",
        "event_kind < 1",
        "true < false",
    ],
)
def test_closed_cel_rejects_incomplete_or_mistyped_scalar_syntax(source: str) -> None:
    with pytest.raises((RuleCelError, RuleLimitError)):
        ConstrainedRuleCelEnvironment().compile(source, "n001")


@pytest.mark.parametrize(
    "payload",
    [
        b"\x03",
        b"\x09",
        b"\x0d",
        b"\x0a\x05a",
        b"\x08\x80",
    ],
)
def test_checked_cel_wire_decoder_rejects_malformed_fields(payload: bytes) -> None:
    with pytest.raises(RuleCelError):
        cel_adapter._decode_wire(payload)


def test_checked_cel_wire_helpers_reject_invalid_types_and_wrappers() -> None:
    with pytest.raises(RuleCelError, match="negative"):
        cel_adapter._write_varint(-1)
    with pytest.raises(RuleCelError, match="varint"):
        cel_adapter._encode_wire([cel_adapter._WireField(1, 0, b"bad")])
    with pytest.raises(RuleCelError, match="byte field"):
        cel_adapter._encode_wire([cel_adapter._WireField(1, 2, 1)])
    with pytest.raises(RuleCelError, match="required field"):
        cel_adapter._single([], 1, 0)
    with pytest.raises(RuleCelError, match="wire type"):
        cel_adapter._utf8(cel_adapter._WireField(1, 0, 1))
    with pytest.raises(RuleCelError, match="UTF-8"):
        cel_adapter._utf8(cel_adapter._WireField(1, 2, b"\xff"))
    malformed = cel_adapter.ProtobufAny(
        type_url="unexpected", value=b""
    ).SerializeToString()
    with pytest.raises(RuleCelError, match="unexpected type"):
        cel_adapter._normalize_checked(malformed)


def test_scalar_type_matrix_rejects_incompatible_operands() -> None:
    assert cel_adapter._binary_type("==", "int", "double") == "bool"
    assert cel_adapter._binary_type("/", "int", "int") == "double"
    with pytest.raises(RuleCelError, match="Boolean"):
        cel_adapter._binary_type("&&", "int", "bool")
    with pytest.raises(RuleCelError, match="incompatible"):
        cel_adapter._binary_type("==", "string", "int")
    with pytest.raises(RuleCelError, match="incompatible"):
        cel_adapter._binary_type("<", "bool", "bool")
    with pytest.raises(RuleCelError, match="numeric"):
        cel_adapter._binary_type("+", "string", "string")
    with pytest.raises(RuleCelError, match="not allowed"):
        cel_adapter._binary_type("in", "int", "int")
