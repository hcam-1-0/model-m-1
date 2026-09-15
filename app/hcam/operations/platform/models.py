from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from hcam.database import Base, UTCDateTime


def utc_now() -> datetime:
    return datetime.now(UTC)


class PlatformServiceObjectiveRecord(Base):
    __tablename__ = "platform_service_objectives"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_platform_objective_revision"),
        CheckConstraint("generated_only = true", name="ck_platform_objective_generated"),
        CheckConstraint("operational = false", name="ck_platform_objective_nonoperational"),
        Index("ix_platform_objective_scope", "department", "updated_at"),
    )

    objective_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    service_class: Mapped[str] = mapped_column(String(32), nullable=False)
    target_state: Mapped[str] = mapped_column(String(16), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utc_now)


class PlatformErrorBudgetRecord(Base):
    __tablename__ = "platform_error_budgets"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_budget_generated"),
        CheckConstraint("operational = false", name="ck_platform_budget_nonoperational"),
        UniqueConstraint("department", "objective_id", "content_digest", name="uq_platform_budget_observation"),
        Index("ix_platform_budget_scope", "department", "observed_at"),
    )

    budget_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    objective_id: Mapped[str] = mapped_column(String(36), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformDegradationRecord(Base):
    __tablename__ = "platform_degradation_states"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_platform_degradation_revision"),
        CheckConstraint("generated_only = true", name="ck_platform_degradation_generated"),
        CheckConstraint("operational = false", name="ck_platform_degradation_nonoperational"),
        Index("ix_platform_degradation_scope", "department", "recorded_at"),
    )

    degradation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformCircuitRecord(Base):
    __tablename__ = "platform_circuit_states"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_circuit_generated"),
        CheckConstraint("operational = false", name="ck_platform_circuit_nonoperational"),
        UniqueConstraint("department", "dependency_class", name="uq_platform_circuit_scope"),
        Index("ix_platform_circuit_scope", "department", "updated_at"),
    )

    circuit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    dependency_class: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformKillSwitchRecord(Base):
    __tablename__ = "platform_kill_switch_revisions"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_platform_kill_switch_revision"),
        CheckConstraint("generated_only = true", name="ck_platform_kill_switch_generated"),
        CheckConstraint("operational = false", name="ck_platform_kill_switch_nonoperational"),
        UniqueConstraint("switch_id", "revision", name="uq_platform_kill_switch_revision"),
        Index("ix_platform_kill_switch_scope", "department", "scope", "scope_key", "recorded_at"),
    )

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    switch_id: Mapped[str] = mapped_column(String(36), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformRecoveryRecord(Base):
    __tablename__ = "platform_recovery_results"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_recovery_generated"),
        CheckConstraint("operational = false", name="ck_platform_recovery_nonoperational"),
        Index("ix_platform_recovery_scope", "department", "recorded_at"),
    )

    result_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformCapacityRecord(Base):
    __tablename__ = "platform_capacity_results"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_capacity_generated"),
        CheckConstraint("operational = false", name="ck_platform_capacity_nonoperational"),
        UniqueConstraint("department", "run_id", name="uq_platform_capacity_run"),
        Index("ix_platform_capacity_scope", "department", "recorded_at"),
    )

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(36), nullable=False)
    scale: Mapped[str] = mapped_column(String(8), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformSupplyChainRecord(Base):
    __tablename__ = "platform_supply_chain_inventories"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_supply_chain_generated"),
        CheckConstraint("operational = false", name="ck_platform_supply_chain_nonoperational"),
        Index("ix_platform_supply_chain_scope", "department", "observed_at"),
    )

    inventory_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    freshness: Mapped[str] = mapped_column(String(16), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformSecurityEvidenceRecord(Base):
    __tablename__ = "platform_security_evidence"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_platform_security_evidence_generated"),
        CheckConstraint("operational = false", name="ck_platform_security_evidence_nonoperational"),
        Index("ix_platform_security_evidence_scope", "department", "recorded_at"),
    )

    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(96), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlatformOutboxRecord(Base):
    __tablename__ = "platform_operations_outbox"
    __table_args__ = (
        CheckConstraint("attempt_count >= 0 AND attempt_count <= 3", name="ck_platform_outbox_attempts"),
        CheckConstraint("generated_only = true", name="ck_platform_outbox_generated"),
        CheckConstraint("operational = false", name="ck_platform_outbox_nonoperational"),
        UniqueConstraint("department", "idempotency_key", name="uq_platform_outbox_idempotency"),
        Index("ix_platform_outbox_claim", "state", "available_at", "lease_until"),
    )

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    available_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utc_now)
