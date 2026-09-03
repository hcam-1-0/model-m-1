from __future__ import annotations

from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.audit.repository import AuditRepository
from hcam.audit.schemas import AuditEventRecord


def test_system_audit_event_serializes_without_user_actor(app) -> None:
    with app.state.database.session_factory() as session, session.begin():
        event = AuditRepository(session).record(
            action="camera_registry.test",
            target_type="camera_registry",
            target_id="synthetic-reference",
            source="tests",
            reason="Verify the audit foundation",
            outcome="success",
            context={"synthetic": True},
        )
        event_id = event.event_id

    with app.state.database.session_factory() as session:
        stored = session.scalars(
            select(AuditEvent).where(AuditEvent.event_id == event_id)
        ).one()
        record = AuditEventRecord.model_validate(stored)

    assert record.actor_id is None
    assert record.action == "camera_registry.test"
    assert record.context == {"synthetic": True}
