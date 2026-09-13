from __future__ import annotations

import pytest

from hcam.intelligence.canonical import MAX_CONTRACT_BYTES
from hcam.intelligence.guardrails import (
    MAX_DOCUMENT_DEPTH,
    MAX_DOCUMENT_NODES,
    PROHIBITED_FIELD_NAMES,
    PROHIBITED_LOCATOR_PREFIXES,
    IntelligenceGuardrailError,
    require_authority_boundary,
    validate_intelligence_document,
)


@pytest.mark.parametrize("field", sorted(PROHIBITED_FIELD_NAMES))
def test_every_sensitive_or_executable_field_is_rejected(field: str) -> None:
    with pytest.raises(IntelligenceGuardrailError, match="prohibited field"):
        validate_intelligence_document({field: "synthetic"})


@pytest.mark.parametrize("prefix", PROHIBITED_LOCATOR_PREFIXES)
def test_every_external_locator_prefix_is_rejected(prefix: str) -> None:
    with pytest.raises(IntelligenceGuardrailError, match="prohibited locator"):
        validate_intelligence_document({"reference": prefix + "not-contacted"})


def test_guardrail_normalizes_field_names_and_walks_lists() -> None:
    with pytest.raises(IntelligenceGuardrailError):
        validate_intelligence_document({"items": [{"Private-Key": "x"}]})


def test_guardrail_enforces_depth_node_and_byte_limits() -> None:
    nested: dict[str, object] = {}
    cursor = nested
    for number in range(MAX_DOCUMENT_DEPTH + 1):
        child: dict[str, object] = {}
        cursor[f"level_{number}"] = child
        cursor = child
    with pytest.raises(IntelligenceGuardrailError, match="nesting"):
        validate_intelligence_document(nested)
    with pytest.raises(IntelligenceGuardrailError, match="node"):
        validate_intelligence_document({"items": list(range(MAX_DOCUMENT_NODES + 1))})
    with pytest.raises(ValueError, match="size"):
        validate_intelligence_document({"summary": "x" * MAX_CONTRACT_BYTES})


def test_guardrail_accepts_bounded_generated_metadata() -> None:
    encoded = validate_intelligence_document(
        {"generated_only": True, "summary_code": "synthetic.event", "count": 1}
    )
    assert encoded.startswith(b'{"count":1')


@pytest.mark.parametrize(
    ("authority", "generated_only", "operational"),
    [
        ("mandatory_review", True, True),
        ("future_autonomous_action", True, False),
        ("bounded_system_health", False, False),
    ],
)
def test_authority_escalation_fails_closed(
    authority: str, generated_only: bool, operational: bool
) -> None:
    with pytest.raises(IntelligenceGuardrailError):
        require_authority_boundary(
            authority, generated_only=generated_only, operational=operational
        )


@pytest.mark.parametrize(
    ("authority", "generated_only"),
    [("mandatory_review", False), ("bounded_system_health", True)],
)
def test_nonoperational_authority_boundaries_are_explicit(
    authority: str, generated_only: bool
) -> None:
    require_authority_boundary(
        authority, generated_only=generated_only, operational=False
    )
