from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from hcam.acceptance.canonical import file_sha256, stable_id
from hcam.acceptance.contracts import (
    EvidenceComponentV1,
    EvidenceEdgeV1,
    EvidenceIndexV1,
)


class EvidenceValidationError(ValueError):
    """Raised when generated acceptance evidence is incomplete or cyclic."""


def component_id(path: str) -> str:
    return stable_id("p47", "evidence", path)


def build_component(
    root: Path,
    relative_path: str,
    *,
    kind: str,
    producer: str = "phase47.generator",
) -> EvidenceComponentV1:
    candidate = (root / relative_path).resolve()
    if root.resolve() not in candidate.parents:
        raise EvidenceValidationError("evidence path escapes the repository root")
    if not candidate.is_file():
        raise EvidenceValidationError("evidence component is not a regular file")
    size = candidate.stat().st_size
    return EvidenceComponentV1(
        component_id=component_id(relative_path),
        path=relative_path.replace("\\", "/"),
        kind=kind,
        byte_length=size,
        sha256=file_sha256(candidate.read_bytes()),
        producer=producer,
        producer_version="1.0.0",
        completeness="complete",
        verified=True,
    )


def build_edges(
    relationships: Iterable[tuple[str, str, str]],
) -> tuple[EvidenceEdgeV1, ...]:
    return tuple(
        EvidenceEdgeV1(
            edge_id=stable_id("edge", source, relation, target),
            source_component_id=component_id(source),
            target_component_id=component_id(target),
            relation=relation,
        )
        for source, target, relation in relationships
    )


def validate_acyclic(
    components: Sequence[EvidenceComponentV1],
    edges: Sequence[EvidenceEdgeV1],
) -> None:
    identifiers = {item.component_id for item in components}
    if len(identifiers) != len(components):
        raise EvidenceValidationError("evidence component IDs must be unique")
    graph: dict[str, list[str]] = defaultdict(list)
    indegree = {identifier: 0 for identifier in identifiers}
    for edge in edges:
        if (
            edge.source_component_id not in identifiers
            or edge.target_component_id not in identifiers
        ):
            raise EvidenceValidationError(
                "evidence edge references a missing component"
            )
        graph[edge.source_component_id].append(edge.target_component_id)
        indegree[edge.target_component_id] += 1
    queue = sorted(identifier for identifier, count in indegree.items() if count == 0)
    visited = 0
    while queue:
        identifier = queue.pop(0)
        visited += 1
        for target in sorted(graph[identifier]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    if visited != len(identifiers):
        raise EvidenceValidationError("evidence graph contains a cycle")


def build_evidence_index(
    root: Path,
    *,
    source_commit: str,
    authorization_digest: str,
    files: Mapping[str, str],
    relationships: Iterable[tuple[str, str, str]] = (),
) -> EvidenceIndexV1:
    components = tuple(
        build_component(root, path, kind=kind) for path, kind in sorted(files.items())
    )
    edges = build_edges(relationships)
    validate_acyclic(components, edges)
    return EvidenceIndexV1(
        source_commit=source_commit,
        authorization_digest=authorization_digest,
        components=components,
        edges=edges,
        completeness="complete"
        if components and all(item.verified for item in components)
        else "partial",
    )


def verify_evidence_index(root: Path, index: EvidenceIndexV1) -> tuple[str, ...]:
    failures: list[str] = []
    for item in index.components:
        candidate = (root / item.path).resolve()
        if root.resolve() not in candidate.parents or not candidate.is_file():
            failures.append(f"missing:{item.component_id}")
            continue
        if candidate.stat().st_size != item.byte_length:
            failures.append(f"size:{item.component_id}")
        if file_sha256(candidate.read_bytes()) != item.sha256:
            failures.append(f"digest:{item.component_id}")
    try:
        validate_acyclic(index.components, index.edges)
    except EvidenceValidationError:
        failures.append("graph:invalid")
    return tuple(sorted(failures))
