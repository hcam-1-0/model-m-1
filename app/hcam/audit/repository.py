from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from hcam.audit.models import AuditEvent


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        action: str,
        target_type: str,
        source: str,
        reason: str,
        outcome: str,
        actor_id: str | None = None,
        target_id: str | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditEvent:
        event_context = dict(context or {})
        if request_id is not None:
            event_context["request_id"] = request_id
        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            source=source,
            reason=reason,
            outcome=outcome,
            context=event_context,
        )
        self.session.add(event)
        self.session.flush()
        return event
