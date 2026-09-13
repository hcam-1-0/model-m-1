from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.intelligence.rules.canonical import (
    RuleCanonicalizationError,
    canonical_rule_bytes,
    rule_sha256,
    strict_json_loads,
)
from hcam.intelligence.rules.contracts import VisualRuleDocumentV1


FIXTURE = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")


def documents() -> list[dict[str, object]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["documents"]


def test_generated_rule_documents_are_strict_and_nonoperational() -> None:
    parsed = [VisualRuleDocumentV1.model_validate(item) for item in documents()]
    assert len(parsed) == 2
    assert all(item.generated_only and not item.operational for item in parsed)
    assert {item.rule_key for item in parsed} == {
        "generated.vehicle-review",
        "generated.sequence-review",
    }


def test_visual_document_rejects_unknown_fields_and_presentation_drift() -> None:
    value = deepcopy(documents()[0])
    value["credential"] = "forbidden"
    with pytest.raises(ValidationError):
        VisualRuleDocumentV1.model_validate(value)
    value = deepcopy(documents()[0])
    value["presentation"]["nodes"].pop()
    with pytest.raises(ValidationError, match="every semantic node"):
        VisualRuleDocumentV1.model_validate(value)


def test_schedule_rejects_overlap_and_naive_cross_midnight() -> None:
    value = deepcopy(documents()[1])
    value["schedule"]["intervals"].append(
        {"weekday": 0, "start_minute": 600, "end_minute": 700}
    )
    with pytest.raises(ValidationError, match="overlap"):
        VisualRuleDocumentV1.model_validate(value)
    value = deepcopy(documents()[1])
    value["schedule"]["intervals"][0] = {
        "weekday": 0,
        "start_minute": 1200,
        "end_minute": 200,
    }
    with pytest.raises(ValidationError):
        VisualRuleDocumentV1.model_validate(value)


def test_strict_json_rejects_duplicate_keys_nonfinite_and_oversize() -> None:
    with pytest.raises(RuleCanonicalizationError, match="duplicate"):
        strict_json_loads('{"rule":1,"rule":2}')
    with pytest.raises(RuleCanonicalizationError, match="non-finite"):
        strict_json_loads('{"value":NaN}')
    with pytest.raises(RuleCanonicalizationError, match="size"):
        strict_json_loads('{"value":"' + ("x" * 200) + '"}', maximum_bytes=32)


def test_canonical_json_rejects_invalid_encoding_shape_and_output_size() -> None:
    with pytest.raises(RuleCanonicalizationError, match="strict UTF-8 JSON"):
        strict_json_loads(b"\xff")
    with pytest.raises(RuleCanonicalizationError, match="strict UTF-8 JSON"):
        strict_json_loads(b'{"value":')
    with pytest.raises(RuleCanonicalizationError, match="canonical JSON"):
        canonical_rule_bytes({"value": {1, 2}})
    with pytest.raises(RuleCanonicalizationError, match="canonical JSON"):
        canonical_rule_bytes({"value": float("nan")})
    with pytest.raises(RuleCanonicalizationError, match="size"):
        canonical_rule_bytes({"value": "x" * 200}, maximum_bytes=32)
    assert rule_sha256({"value": 1}).startswith("sha256:")
