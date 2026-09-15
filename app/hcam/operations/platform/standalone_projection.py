from __future__ import annotations

from hcam.operations.platform.contracts import PlacementPlanV1


def project_standalone(plan: PlacementPlanV1) -> dict[str, object]:
    return {
        "profile": "hcam.placement.standalone.generated.v1",
        "plan_digest": plan.plan_digest,
        "services": [
            {"service_id": item.service_id, "profile_id": item.profile_id, "reason": item.reason}
            for item in plan.decisions
        ],
        "process_execution_enabled": False,
        "generated_only": True,
    }
