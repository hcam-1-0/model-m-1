from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from hcam.intelligence.rules.bounds import RuleBounds, RuleLimitError
from hcam.intelligence.rules.compiler import RuleCompilationError, compile_rule
from hcam.intelligence.rules.contracts import VisualRuleDocumentV1


FIXTURE = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")


def value(index: int = 0) -> dict[str, object]:
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8"))["documents"][index])


def compile_value(payload: dict[str, object], bounds: RuleBounds | None = None):
    return compile_rule(VisualRuleDocumentV1.model_validate(payload), bounds=bounds)


def test_layout_changes_only_authoring_digest() -> None:
    original = compile_value(value())
    changed = value()
    changed["presentation"]["nodes"][0]["x"] = 999
    changed["presentation"]["nodes"][0]["label"] = "Different generated label"
    modified = compile_value(changed)
    assert (
        original.compilation.authoring_digest != modified.compilation.authoring_digest
    )
    assert original.compilation.semantic_digest == modified.compilation.semantic_digest
    assert original.canonical_bytes == modified.canonical_bytes


def test_authoring_identifiers_and_list_order_do_not_change_semantics() -> None:
    original = compile_value(value(1))
    changed = value(1)
    mapping = {
        "entry": "source-a",
        "departure": "source-b",
        "ordered": "sequence-a",
        "limited": "cooldown-a",
        "review": "output-a",
    }
    nodes = changed["semantics"]["nodes"]
    for node in nodes:
        node["node_id"] = mapping[node["node_id"]]
        node["inputs"] = [mapping[item] for item in node["inputs"]]
    changed["semantics"]["output_node_id"] = "output-a"
    for node in changed["presentation"]["nodes"]:
        node["node_id"] = mapping[node["node_id"]]
    changed["semantics"]["nodes"] = list(reversed(nodes))
    modified = compile_value(changed)
    assert original.compilation.semantic_digest == modified.compilation.semantic_digest
    assert original.canonical_bytes == modified.canonical_bytes


@pytest.mark.parametrize(
    "failure", ["cycle", "dangling", "unreachable", "output", "type"]
)
def test_compiler_rejects_invalid_graphs(failure: str) -> None:
    payload = value()
    nodes = payload["semantics"]["nodes"]
    if failure == "cycle":
        nodes[0]["inputs"] = ["review-output"]
    elif failure == "dangling":
        nodes[1]["inputs"] = ["missing-node"]
    elif failure == "unreachable":
        nodes.append(
            {
                "node_id": "unused",
                "kind": "event_match",
                "inputs": [],
                "parameters": {"event_types": ["generated.unused"]},
            }
        )
        payload["presentation"]["nodes"].append(
            {"node_id": "unused", "x": 0, "y": 0, "label": "Unused"}
        )
    elif failure == "output":
        payload["semantics"]["output_node_id"] = "confidence-check"
    else:
        nodes[1]["kind"] = "not"
        nodes[1]["parameters"] = {}
    with pytest.raises((RuleCompilationError, RuleLimitError)):
        compile_value(payload)


def test_compiler_enforces_frozen_node_depth_and_fan_in_bounds() -> None:
    with pytest.raises(RuleLimitError, match="semantic node"):
        compile_value(value(), RuleBounds(semantic_nodes=2))
    with pytest.raises(RuleLimitError, match="depth"):
        compile_value(value(), RuleBounds(graph_depth=2))


def test_ordered_sequence_changes_semantic_digest_when_reversed() -> None:
    original = compile_value(value(1))
    changed = value(1)
    changed["semantics"]["nodes"][2]["inputs"].reverse()
    modified = compile_value(changed)
    assert original.compilation.semantic_digest != modified.compilation.semantic_digest
