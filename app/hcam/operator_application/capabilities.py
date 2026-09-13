from __future__ import annotations

from datetime import datetime

from .contracts import (
    CapabilityCeilingV1,
    CapabilityDecisionV1,
    ResourceProfile,
    StableId,
)


PROFILE_ACTION_LIMITS: dict[ResourceProfile, frozenset[str]] = {
    "low_resource": frozenset({"view", "query", "preview_single"}),
    "enhanced": frozenset({"view", "query", "preview_single", "visualize_dense"}),
    "control_room": frozenset(
        {"view", "query", "preview_single", "visualize_dense", "multi_monitor"}
    ),
}


def resolve_capability(
    *,
    action: StableId,
    server_allowed: bool,
    ceiling: CapabilityCeilingV1,
    resource_profile: ResourceProfile,
    observed_at: datetime,
) -> CapabilityDecisionV1:
    if not server_allowed:
        allowed = False
        reason = "server_denied"
    elif action in ceiling.denied_actions or action not in ceiling.allowed_actions:
        allowed = False
        reason = "policy_ceiling_denied"
    elif action in {"visualize_dense", "multi_monitor"} and action not in (
        PROFILE_ACTION_LIMITS[resource_profile]
    ):
        allowed = False
        reason = "resource_profile_unavailable"
    else:
        allowed = True
        reason = "allowed"
    return CapabilityDecisionV1(
        action=action,
        allowed=allowed,
        reason_code=reason,
        policy_version=ceiling.policy_version,
        resource_profile=resource_profile,
        observed_at=observed_at,
    )
