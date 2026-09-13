from pathlib import Path

import pytest

from hcam.acceptance.evidence import (
    EvidenceValidationError,
    build_evidence_index,
    build_edges,
    component_id,
    validate_acyclic,
    verify_evidence_index,
)


def test_evidence_index_is_hash_bound_and_acyclic(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text("{}\n", encoding="ascii")
    (tmp_path / "b.json").write_text("{}\n", encoding="ascii")
    index = build_evidence_index(
        tmp_path,
        source_commit="a" * 40,
        authorization_digest="A" * 64,
        files={"a.json": "fixture", "b.json": "result"},
        relationships=(("a.json", "b.json", "derived_from"),),
    )
    assert index.completeness == "complete"
    assert verify_evidence_index(tmp_path, index) == ()
    (tmp_path / "b.json").write_text("changed\n", encoding="ascii")
    assert verify_evidence_index(tmp_path, index)


def test_evidence_rejects_missing_escape_and_cycles(tmp_path: Path) -> None:
    with pytest.raises(EvidenceValidationError):
        build_evidence_index(
            tmp_path,
            source_commit="a" * 40,
            authorization_digest="A" * 64,
            files={"missing": "source"},
        )
    outside = tmp_path.parent / "outside-p47.json"
    outside.write_text("{}", encoding="ascii")
    try:
        with pytest.raises(EvidenceValidationError):
            build_evidence_index(
                tmp_path,
                source_commit="a" * 40,
                authorization_digest="A" * 64,
                files={"../outside-p47.json": "source"},
            )
    finally:
        outside.unlink()
    components = []
    edges = build_edges((("a", "b", "supports"),))
    with pytest.raises(EvidenceValidationError):
        validate_acyclic(components, edges)


def test_evidence_cycle_is_rejected(tmp_path: Path) -> None:
    for name in ("a", "b"):
        (tmp_path / name).write_text(name, encoding="ascii")
    index = build_evidence_index(
        tmp_path,
        source_commit="a" * 40,
        authorization_digest="A" * 64,
        files={"a": "source", "b": "result"},
    )
    edges = build_edges((("a", "b", "supports"), ("b", "a", "supports")))
    with pytest.raises(EvidenceValidationError):
        validate_acyclic(index.components, edges)
    assert component_id("a") != component_id("b")


def test_evidence_duplicate_and_verifier_graph_failures_are_visible(
    tmp_path: Path,
) -> None:
    (tmp_path / "a").write_text("a", encoding="ascii")
    index = build_evidence_index(
        tmp_path,
        source_commit="a" * 40,
        authorization_digest="A" * 64,
        files={"a": "source"},
    )
    with pytest.raises(EvidenceValidationError):
        validate_acyclic((index.components[0], index.components[0]), ())
    invalid_edge = build_edges((("a", "missing", "supports"),))[0]
    assert "graph:invalid" in verify_evidence_index(
        tmp_path, index.model_copy(update={"edges": (invalid_edge,)})
    )
    (tmp_path / "a").unlink()
    failures = verify_evidence_index(tmp_path, index)
    assert any(item.startswith("missing:") for item in failures)
