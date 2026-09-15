from __future__ import annotations

from datetime import datetime

from hcam.operations.platform.contracts import KillSwitchRevisionV1


SCOPE_ORDER = {"platform": 0, "department": 1, "service": 2, "lane": 3}


def effective_switches(revisions: list[KillSwitchRevisionV1], *, now: datetime) -> list[KillSwitchRevisionV1]:
    latest: dict[tuple[str, str], KillSwitchRevisionV1] = {}
    for item in revisions:
        key = (item.scope, item.scope_key)
        current = latest.get(key)
        if current is None or item.revision > current.revision:
            latest[key] = item
        elif item.revision == current.revision and item != current:
            raise ValueError("conflicting kill-switch revisions")
    return sorted(
        [item for item in latest.values() if item.expires_at is None or item.expires_at > now],
        key=lambda item: (SCOPE_ORDER[item.scope], item.scope_key),
    )


def capability_allowed(revisions: list[KillSwitchRevisionV1], *, now: datetime) -> bool:
    active = effective_switches(revisions, now=now)
    if any(item.state == "deny" for item in active):
        return False
    return bool(active) and all(item.state == "allow" for item in active)


def protect_mandatory_control(
    revisions: list[KillSwitchRevisionV1], *, now: datetime
) -> None:
    for item in effective_switches(revisions, now=now):
        if item.mandatory_control and item.state == "allow":
            raise ValueError("kill switches cannot bypass mandatory controls")
