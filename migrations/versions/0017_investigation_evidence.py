"""Add the generated-only Phase 4.5 investigation and evidence stores.

Revision ID: 0017_investigation_evidence
Revises: 0016_reference_integrations
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from hcam.database import Base
from hcam.intelligence.row_security import INVESTIGATION_TABLES


revision: str = "0017_investigation_evidence"
down_revision: str | None = "0016_reference_integrations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = INVESTIGATION_TABLES


def _enable_rls(table: str) -> None:
    policy = f"{table}_department_scope"
    predicate = (
        "current_setting('hcam.is_platform_admin', true) = 'true' OR "
        "department = ANY(string_to_array("
        "current_setting('hcam.allowed_departments', true), E'\\x1f'))"
    )
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY "{policy}" ON "{table}" '
        f"USING ({predicate}) WITH CHECK ({predicate})"
    )


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in NEW_TABLES:
        Base.metadata.tables[table_name].create(bind=bind)
    if bind.dialect.name == "postgresql":
        for table_name in NEW_TABLES:
            _enable_rls(table_name)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table_name in reversed(NEW_TABLES):
            policy = f"{table_name}_department_scope"
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table_name}"')
    for table_name in reversed(NEW_TABLES):
        op.drop_table(table_name)
