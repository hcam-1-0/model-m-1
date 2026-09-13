from __future__ import annotations

import re
from difflib import SequenceMatcher

from hcam.intelligence.integrations.canonical import digest, stable_id
from hcam.intelligence.integrations.contracts import (
    CandidateSetV1,
    CandidateV1,
    FieldEvidenceV1,
)


_SPACE = re.compile(r"\s+")


def normalize_generated_value(value: str) -> str:
    return _SPACE.sub(" ", value.strip().casefold().replace("-", " "))


def compare_field(field: str, query_value: str, candidate_value: str | None) -> FieldEvidenceV1:
    query_digest = digest({"value": query_value})
    if candidate_value is None:
        return FieldEvidenceV1(
            field=field,
            comparator_version="generated.comparator.v1",
            state="missing",
            score=0,
            query_value_digest=query_digest,
        )
    candidate_digest = digest({"value": candidate_value})
    if query_value == candidate_value:
        state, score = "exact", 1.0
    else:
        left = normalize_generated_value(query_value)
        right = normalize_generated_value(candidate_value)
        if left == right:
            state, score = "normalized", 0.95
        else:
            similarity = SequenceMatcher(None, left, right, autojunk=False).ratio()
            if similarity >= 0.8:
                state, score = "approximate", round(similarity * 0.85, 6)
            else:
                state, score = "contradicts", 0.0
    return FieldEvidenceV1(
        field=field,
        comparator_version="generated.comparator.v1",
        state=state,
        score=score,
        query_value_digest=query_digest,
        candidate_value_digest=candidate_digest,
    )


def build_candidate_set(
    *,
    query_id: str,
    department: str,
    query_fields: dict[str, str],
    records: list[dict[str, str]],
    minimum_evidence: int = 2,
    minimum_score: float = 0.7,
    minimum_separation: float = 0.05,
) -> CandidateSetV1:
    evaluated: list[tuple[str, list[FieldEvidenceV1], float, int]] = []
    for record in records:
        evidence = [
            compare_field(field, value, record.get(field))
            for field, value in sorted(query_fields.items())
        ]
        usable = [item.score for item in evidence if item.state not in {"missing", "invalid", "stale"}]
        score = sum(usable) / len(usable) if usable else 0.0
        contradictions = sum(item.state == "contradicts" for item in evidence)
        record_digest = digest(record)
        evaluated.append((record_digest, evidence, score, contradictions))
    evaluated.sort(key=lambda item: (-item[2], item[0]))

    outcome = "candidates"
    reasons = ["candidate.generated"]
    exposed = evaluated[:25]
    if not exposed or len([x for x in exposed[0][1] if x.score > 0]) < minimum_evidence:
        outcome, reasons, exposed = "abstain", ["candidate.insufficient_evidence"], []
    elif exposed[0][2] < minimum_score:
        outcome, reasons, exposed = "no_match", ["candidate.minimum_score"], []
    elif exposed[0][3] > 0:
        outcome, reasons, exposed = "abstain", ["candidate.contradiction"], []
    elif len(exposed) > 1 and exposed[0][2] - exposed[1][2] < minimum_separation:
        outcome, reasons, exposed = "ambiguous", ["candidate.ambiguous"], []

    candidates = [
        CandidateV1(
            candidate_id=stable_id("cand", query_id, record_digest),
            rank=index,
            evidence=evidence,
            aggregate_score=round(score, 6),
            contradiction_count=contradictions,
        )
        for index, (record_digest, evidence, score, contradictions) in enumerate(exposed, 1)
    ]
    material = {
        "query_id": query_id,
        "department": department,
        "outcome": outcome,
        "reason_codes": reasons,
        "candidates": [item.model_dump(mode="json") for item in candidates],
    }
    return CandidateSetV1(
        candidate_set_id=stable_id("cset", query_id, digest(material)),
        query_id=query_id,
        department=department,
        outcome=outcome,
        reason_codes=reasons,
        candidates=candidates,
        candidate_set_digest=digest(material),
    )
