from __future__ import annotations

from hcam.intelligence.alerts.contracts import ProposedAlertCommandV1, SystemHealthActionV1


POLICE_ACTIONS = frozenset({"queue_review", "start_review", "assign", "suppress"})
SYSTEM_HEALTH_ACTIONS = frozenset(
    {"route", "suppress_duplicate", "resolve_synthetic_health"}
)


class AuthorityDenied(ValueError):
    pass


def validate_proposal_authority(command: ProposedAlertCommandV1) -> None:
    if command.domain == "police_intelligence":
        if command.authority_class != "mandatory_review":
            raise AuthorityDenied("police intelligence cannot use automation")
        return
    if command.domain == "system_health" and command.authority_class == "bounded_automation":
        return
    raise AuthorityDenied("authority and domain do not match")


def authorize_action(command: ProposedAlertCommandV1, action: str) -> None:
    validate_proposal_authority(command)
    allowed = POLICE_ACTIONS if command.domain == "police_intelligence" else SYSTEM_HEALTH_ACTIONS
    if action not in allowed:
        raise AuthorityDenied("action is outside the authority-class allowlist")


def validate_system_health_action(
    command: ProposedAlertCommandV1, action: SystemHealthActionV1
) -> None:
    if command.domain != "system_health" or command.authority_class != "bounded_automation":
        raise AuthorityDenied("system-health action cannot consume police intelligence")
    if action.action not in SYSTEM_HEALTH_ACTIONS:
        raise AuthorityDenied("system-health action is not allowlisted")
