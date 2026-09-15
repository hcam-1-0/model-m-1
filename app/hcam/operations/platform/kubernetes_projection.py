from __future__ import annotations

from hcam.operations.platform.contracts import PlacementPlanV1


def project_kubernetes(plan: PlacementPlanV1) -> dict[str, object]:
    return {
        "apiVersion": "hcam.generated/v1",
        "kind": "PlacementProjection",
        "metadata": {"name": "generated-phase46", "plan_digest": plan.plan_digest},
        "spec": {
            "apply": False,
            "scheduler_execution": False,
            "assignments": [
                {"service": item.service_id, "nodeClass": item.profile_id, "reason": item.reason}
                for item in plan.decisions
            ],
        },
        "generated_only": True,
    }
