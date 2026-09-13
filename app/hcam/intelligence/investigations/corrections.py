from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime

from hcam.intelligence.investigations.bounds import (
    MAX_CORRECTION_CHAIN_DEPTH,
    MAX_IMPACT_TARGETS,
)
from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    CorrectionCommandV1,
    ImpactRecordV1,
    ImpactSetV1,
)


def build_impact_set(
    correction: CorrectionCommandV1,
    dependencies: dict[str, list[tuple[str, str]]],
    *,
    recorded_at: datetime,
) -> ImpactSetV1:
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for source, targets in dependencies.items():
        adjacency[source].extend(targets)
    queue = deque([(correction.target_ref, 0)])
    seen: set[str] = set()
    impacts: list[ImpactRecordV1] = []
    while queue:
        reference, depth = queue.popleft()
        if depth > MAX_CORRECTION_CHAIN_DEPTH:
            raise ValueError("correction impact closure exceeds the depth bound")
        if reference in seen:
            continue
        seen.add(reference)
        for target_type, target_ref in sorted(adjacency.get(reference, [])):
            if len(impacts) >= MAX_IMPACT_TARGETS:
                raise ValueError("correction impact closure exceeds the target bound")
            impacts.append(
                ImpactRecordV1(
                    impact_id=stable_id(
                        "iimp", correction.correction_id, target_type, target_ref
                    ),
                    correction_id=correction.correction_id,
                    timeline_id=correction.timeline_id,
                    department=correction.department,
                    target_type=target_type,
                    target_ref=target_ref,
                    state="pending",
                    reason_code="correction.impact_pending",
                    recorded_at=recorded_at,
                )
            )
            queue.append((target_ref, depth + 1))
    material = [impact.model_dump(mode="json") for impact in impacts]
    return ImpactSetV1(
        correction_id=correction.correction_id,
        timeline_id=correction.timeline_id,
        department=correction.department,
        impacts=impacts,
        propagation_state="complete" if not impacts else "pending",
        impact_digest=digest(material),
    )


def propagation_state(impacts: list[ImpactRecordV1]) -> str:
    states = {impact.state for impact in impacts}
    if not impacts or states == {"applied"}:
        return "complete"
    if "failed" in states and states <= {"failed"}:
        return "failed"
    if "blocked" in states and states <= {"blocked"}:
        return "blocked"
    if "applied" in states and len(states) > 1:
        return "partial"
    return "pending"
