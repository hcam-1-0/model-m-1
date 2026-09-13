"""Add generated-only Phase 4.6 operations, security, and scale stores.

Revision ID: 0018_operations_security_scale
Revises: 0017_investigation_evidence
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from hcam.database import Base
from hcam.operations.platform.security import postgres_rls_predicate


revision: str = "0018_operations_security_scale"
down_revision: str | None = "0017_investigation_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLATFORM_TABLES = (
    "platform_service_objectives",
    "platform_error_budgets",
    "platform_degradation_states",
    "platform_circuit_states",
    "platform_kill_switch_revisions",
    "platform_recovery_results",
    "platform_capacity_results",
    "platform_supply_chain_inventories",
    "platform_security_evidence",
    "platform_operations_outbox",
)


def _enable_rls(table: str) -> None:
    policy = f"{table}_department_scope"
    predicate = postgres_rls_predicate()
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY "{policy}" ON "{table}" '
        f"USING ({predicate}) WITH CHECK ({predicate})"
    )


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in PLATFORM_TABLES:
        Base.metadata.tables[table_name].create(bind=bind)
    if bind.dialect.name == "postgresql":
        for table_name in PLATFORM_TABLES:
            _enable_rls(table_name)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table_name in reversed(PLATFORM_TABLES):
            policy = f"{table_name}_department_scope"
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table_name}"')
    for table_name in reversed(PLATFORM_TABLES):
        op.drop_table(table_name)
