from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.engine import Connection

from hcam.audit.models import AuditEvent
from hcam.camera_registry.models import Camera
from hcam.database import Database
from hcam.intelligence.models import IntelligenceRule, IntelligenceRuleCompilation
from hcam.intelligence.row_security import apply_department_scope
from hcam.intelligence.rules.contracts import VisualRuleDocumentV1
from hcam.intelligence.rules.persistence import RuleControlService, stable_id
from hcam.security.auth import Principal
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
PROBE_ROLE = "hcam_p42_rls_probe"
P42_TABLES = (
    "intelligence_rule_compilations",
    "intelligence_rule_scope_members",
    "intelligence_rule_schedules",
    "intelligence_rule_lifecycle_events",
    "intelligence_rule_state_checkpoints",
    "intelligence_rule_evaluation_revisions",
    "intelligence_rule_shadow_comparisons",
)
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def _admin() -> Principal:
    return Principal(
        actor_id="phase42-postgres-test",
        roles=frozenset({"platform.admin"}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )


def _document(*, department: str, rule_key: str) -> VisualRuleDocumentV1:
    source = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")
    payload = deepcopy(json.loads(source.read_text(encoding="utf-8"))["documents"][0])
    payload["department"] = department
    payload["rule_key"] = rule_key
    return VisualRuleDocumentV1.model_validate(payload)


def _drop_probe_role(connection: Connection) -> None:
    exists = connection.scalar(
        text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
        {"role": PROBE_ROLE},
    )
    if exists:
        connection.execute(text(f"DROP OWNED BY {PROBE_ROLE}"))
        connection.execute(text(f"DROP ROLE {PROBE_ROLE}"))


def test_phase42_postgres_forced_rls_and_department_isolation() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    principal = _admin()
    rule_keys = ("generated.p42.rls.engineering", "generated.p42.rls.other")
    record_ids = tuple(
        stable_id(
            "irlr",
            stable_id("irule", department, key),
            1,
        )
        for department, key in zip(
            ("Engineering Lab", "Another Department"),
            rule_keys,
            strict=True,
        )
    )
    stream_ids = (synthetic_stream_id(1), synthetic_stream_id(2))
    try:
        database.check_ready()
        with database.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = ANY(:tables)"
                ),
                {"tables": list(P42_TABLES)},
            ).all()
            policies = connection.execute(
                text(
                    "SELECT tablename, count(*) FROM pg_policies "
                    "WHERE tablename = ANY(:tables) GROUP BY tablename"
                ),
                {"tables": list(P42_TABLES)},
            ).all()
        assert {row[0]: row[1:] for row in rows} == {
            table: (True, True) for table in P42_TABLES
        }
        assert {row[0]: row[1] for row in policies} == {
            table: 1 for table in P42_TABLES
        }

        with database.session_factory() as session:
            seed_synthetic_lab(session, count=2)
        with database.session_factory.begin() as session:
            apply_department_scope(session, principal)
            session.execute(
                delete(IntelligenceRule).where(
                    IntelligenceRule.rule_record_id.in_(record_ids)
                )
            )
            session.execute(
                update(Camera)
                .where(Camera.camera_id == "phase2:cctv-002")
                .values(department="Another Department")
            )
        for department, key, stream_id in zip(
            ("Engineering Lab", "Another Department"),
            rule_keys,
            stream_ids,
            strict=True,
        ):
            with database.session_factory() as session:
                RuleControlService(session, enabled=True).create(
                    _document(department=department, rule_key=key),
                    [stream_id],
                    principal=principal,
                    reason="Validate generated-only PostgreSQL department isolation",
                    request_id=None,
                )

        with database.engine.begin() as connection:
            _drop_probe_role(connection)
            connection.execute(text(f"CREATE ROLE {PROBE_ROLE} NOLOGIN"))
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {PROBE_ROLE}"))
            connection.execute(
                text(f"GRANT SELECT ON intelligence_rule_compilations TO {PROBE_ROLE}")
            )
            connection.execute(text(f"SET LOCAL ROLE {PROBE_ROLE}"))
            connection.execute(
                text("SELECT set_config('hcam.is_platform_admin', 'false', true)")
            )
            connection.execute(
                text(
                    "SELECT set_config('hcam.allowed_departments', "
                    "'Engineering Lab', true)"
                )
            )
            visible = (
                connection.execute(
                    select(IntelligenceRuleCompilation.department).where(
                        IntelligenceRuleCompilation.rule_record_id.in_(record_ids)
                    )
                )
                .scalars()
                .all()
            )
            connection.execute(text("RESET ROLE"))
        assert visible == ["Engineering Lab"]
    finally:
        with database.session_factory.begin() as session:
            apply_department_scope(session, principal)
            session.execute(
                delete(IntelligenceRule).where(
                    IntelligenceRule.rule_record_id.in_(record_ids)
                )
            )
            session.execute(
                delete(AuditEvent).where(AuditEvent.target_id.in_(record_ids))
            )
            session.execute(
                delete(StreamEventOutbox).where(
                    StreamEventOutbox.event_type
                    == "hcam.intelligence.rule.lifecycle.v2",
                    StreamEventOutbox.stream_id.in_(stream_ids),
                )
            )
            session.execute(
                update(Camera)
                .where(Camera.camera_id == "phase2:cctv-002")
                .values(department="Engineering Lab")
            )
        with database.engine.begin() as connection:
            _drop_probe_role(connection)
        database.dispose()
