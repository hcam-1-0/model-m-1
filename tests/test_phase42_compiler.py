from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from hcam.intelligence.rules.bounds import RuleBounds, RuleLimitError
from hcam.intelligence.rules.compiler import RuleCompilationError, compile_rule
from hcam.intelligence.rules.contracts import VisualRuleDocumentV1


FIXTURE = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")


def payload() -> dict[str, object]:
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8"))["documents"][0])


def test_compilation_binds_versions_digests_map_and_checked_cel() -> None:
    result = compile_rule(VisualRuleDocumentV1.model_validate(payload()))
    compilation = result.compilation
    assert compilation.generated_only is True
    assert compilation.operational is False
    assert compilation.canonical_ast.compiler_version == "hcam.p4-2.compiler.v1"
    assert compilation.canonical_ast.temporal_version == "hcam.p4-2.temporal.v1"
    assert compilation.canonical_ast.cel_environment_version == (
        "hcam.p4-2.constrained-cel.v1"
    )
    assert len(compilation.cel_compilations) == 1
    assert set(compilation.diagnostic_map) == {
        "vehicle-source",
        "confidence-check",
        "review-output",
    }
    assert compilation.ast_digest == compilation.semantic_digest
    assert compilation.compilation_id.startswith("rcmp_")


@pytest.mark.parametrize(
    ("node_index", "mutation"),
    [
        (0, {"event_types": None}),
        (0, {"event_types": ["generated.vehicle.observed"], "threshold": 1}),
        (1, {"cel_source": None}),
        (2, {"output_code": None}),
    ],
)
def test_node_parameter_families_are_exact(
    node_index: int, mutation: dict[str, object]
) -> None:
    value = payload()
    value["semantics"]["nodes"][node_index]["parameters"].update(mutation)
    with pytest.raises(RuleCompilationError):
        compile_rule(VisualRuleDocumentV1.model_validate(value))


def test_compilation_rejects_duplicate_input_and_multiple_output_shape() -> None:
    value = payload()
    value["semantics"]["nodes"][2]["inputs"] = ["confidence-check", "confidence-check"]
    with pytest.raises(ValueError):
        VisualRuleDocumentV1.model_validate(value)


@pytest.mark.parametrize(
    ("node_index", "inputs", "message"),
    [
        (1, [], "cel_predicate requires exactly one"),
        (2, [], "propose_review_candidate requires exactly one"),
    ],
)
def test_compiler_rejects_invalid_node_arity(
    node_index: int,
    inputs: list[str],
    message: str,
) -> None:
    value = payload()
    value["semantics"]["nodes"][node_index]["inputs"] = inputs
    with pytest.raises(RuleCompilationError, match=message):
        compile_rule(VisualRuleDocumentV1.model_validate(value))


def test_compiler_rejects_source_inputs_before_type_projection() -> None:
    value = payload()
    value["semantics"]["nodes"].insert(
        0,
        {
            "node_id": "base-source",
            "kind": "event_match",
            "inputs": [],
            "parameters": {"event_types": ["generated.base"]},
        },
    )
    value["semantics"]["nodes"][1]["inputs"] = ["base-source"]
    value["presentation"]["nodes"].append(
        {"node_id": "base-source", "x": 0, "y": 0, "label": "Base source"}
    )
    with pytest.raises(RuleCompilationError, match="source nodes"):
        compile_rule(VisualRuleDocumentV1.model_validate(value))


def test_compiler_rejects_boolean_temporal_and_output_type_mismatches() -> None:
    boolean_value = payload()
    boolean_value["semantics"]["nodes"][1]["kind"] = "not"
    boolean_value["semantics"]["nodes"][1]["parameters"] = {}
    with pytest.raises(RuleCompilationError, match="Boolean nodes"):
        compile_rule(VisualRuleDocumentV1.model_validate(boolean_value))

    temporal_value = payload()
    temporal_value["semantics"]["nodes"][2] = {
        "node_id": "temporal",
        "kind": "within",
        "inputs": ["confidence-check"],
        "parameters": {"duration_ms": 1_000},
    }
    temporal_value["semantics"]["output_node_id"] = "temporal"
    temporal_value["presentation"]["nodes"][2]["node_id"] = "temporal"
    with pytest.raises(RuleCompilationError, match="temporal node"):
        compile_rule(VisualRuleDocumentV1.model_validate(temporal_value))

    output_value = payload()
    output_value["semantics"]["nodes"].append(
        {
            "node_id": "second-output",
            "kind": "propose_review_candidate",
            "inputs": ["review-output"],
            "parameters": {"output_code": "generated.second-review"},
        }
    )
    output_value["semantics"]["output_node_id"] = "second-output"
    output_value["presentation"]["nodes"].append(
        {"node_id": "second-output", "x": 0, "y": 0, "label": "Second output"}
    )
    with pytest.raises(RuleCompilationError, match="output requires"):
        compile_rule(VisualRuleDocumentV1.model_validate(output_value))


def test_compiler_enforces_input_fan_in_bound() -> None:
    document = VisualRuleDocumentV1.model_validate(payload())
    document.semantics.nodes[2].inputs.append("confidence-check")
    with pytest.raises(RuleLimitError, match="input limit"):
        compile_rule(document, bounds=RuleBounds(inputs_per_node=1))
