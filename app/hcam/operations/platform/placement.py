from __future__ import annotations

from hcam.operations.platform.canonical import digest
from hcam.operations.platform.contracts import PlacementDecisionV1, PlacementPlanV1, PlacementRequestV1


def build_placement_plan(request: PlacementRequestV1) -> PlacementPlanV1:
    remaining = {
        profile.profile_id: [profile.cpu_units, profile.memory_mib, profile.accelerator_units]
        for profile in request.profiles
    }
    decisions: list[PlacementDecisionV1] = []
    for service in sorted(request.services, key=lambda item: (item.optional, item.service_id)):
        candidates = []
        unknown = False
        for profile in request.profiles:
            if profile.state in {"unknown", "stale"}:
                unknown = True
                continue
            if profile.state == "unsupported" or not service.mandatory_capabilities <= profile.capabilities:
                continue
            capacity = remaining[profile.profile_id]
            if capacity[0] >= service.cpu_units and capacity[1] >= service.memory_mib and capacity[2] >= service.accelerator_units:
                candidates.append(profile)
        if candidates:
            selected = sorted(candidates, key=lambda item: (-item.accelerator_units, -item.memory_mib, item.profile_id))[0]
            capacity = remaining[selected.profile_id]
            capacity[0] -= service.cpu_units
            capacity[1] -= service.memory_mib
            capacity[2] -= service.accelerator_units
            decisions.append(PlacementDecisionV1(service_id=service.service_id, profile_id=selected.profile_id, reason="placed"))
        elif service.optional:
            decisions.append(PlacementDecisionV1(service_id=service.service_id, profile_id=None, reason="optional_lane_bypassed"))
        else:
            has_known_capability = any(
                profile.state not in {"unknown", "stale", "unsupported"}
                and service.mandatory_capabilities <= profile.capabilities
                for profile in request.profiles
            )
            if has_known_capability:
                reason = "capacity_exhausted"
            elif unknown:
                reason = "capability_unknown"
            else:
                reason = "mandatory_capability_missing"
            decisions.append(PlacementDecisionV1(service_id=service.service_id, profile_id=None, reason=reason))
    payload = {"request_id": request.request_id, "decisions": [item.model_dump(mode="json") for item in decisions]}
    return PlacementPlanV1(request_id=request.request_id, decisions=decisions, plan_digest=digest(payload))
