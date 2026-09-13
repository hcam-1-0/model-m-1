from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.orm import Session

from hcam.intelligence.row_security import apply_department_scope
from hcam.operations.platform.models import (
    PlatformCapacityRecord,
    PlatformDegradationRecord,
    PlatformErrorBudgetRecord,
    PlatformKillSwitchRecord,
    PlatformRecoveryRecord,
    PlatformSecurityEvidenceRecord,
    PlatformServiceObjectiveRecord,
    PlatformSupplyChainRecord,
)
from hcam.operations.platform.persistence import PlatformRepository
from hcam.operations.platform.runtime import GeneratedPlatformRuntime
from hcam.security.auth import (
    OPERATIONS_CAPACITY_READ,
    OPERATIONS_CONTROL_READ,
    OPERATIONS_PLATFORM_READ,
    OPERATIONS_RECOVERY_READ,
    OPERATIONS_SECURITY_READ,
    OPERATIONS_SUPPLY_CHAIN_READ,
    PLATFORM_ADMIN,
    Principal,
)


ViewName = Literal["objectives", "budgets", "degradation", "controls", "recovery", "capacity", "supply-chain", "security"]

VIEW_MODELS = {
    "objectives": (PlatformServiceObjectiveRecord, PlatformServiceObjectiveRecord.updated_at),
    "budgets": (PlatformErrorBudgetRecord, PlatformErrorBudgetRecord.observed_at),
    "degradation": (PlatformDegradationRecord, PlatformDegradationRecord.recorded_at),
    "controls": (PlatformKillSwitchRecord, PlatformKillSwitchRecord.recorded_at),
    "recovery": (PlatformRecoveryRecord, PlatformRecoveryRecord.recorded_at),
    "capacity": (PlatformCapacityRecord, PlatformCapacityRecord.recorded_at),
    "supply-chain": (PlatformSupplyChainRecord, PlatformSupplyChainRecord.observed_at),
    "security": (PlatformSecurityEvidenceRecord, PlatformSecurityEvidenceRecord.recorded_at),
}

VIEW_ROLES: dict[ViewName, frozenset[str]] = {
    "objectives": frozenset({OPERATIONS_PLATFORM_READ, PLATFORM_ADMIN}),
    "budgets": frozenset({OPERATIONS_PLATFORM_READ, PLATFORM_ADMIN}),
    "degradation": frozenset({OPERATIONS_PLATFORM_READ, PLATFORM_ADMIN}),
    "controls": frozenset({OPERATIONS_CONTROL_READ, PLATFORM_ADMIN}),
    "recovery": frozenset({OPERATIONS_RECOVERY_READ, PLATFORM_ADMIN}),
    "capacity": frozenset({OPERATIONS_CAPACITY_READ, PLATFORM_ADMIN}),
    "supply-chain": frozenset({OPERATIONS_SUPPLY_CHAIN_READ, PLATFORM_ADMIN}),
    "security": frozenset({OPERATIONS_SECURITY_READ, PLATFORM_ADMIN}),
}


class PlatformService:
    def __init__(self, session: Session, runtime: GeneratedPlatformRuntime) -> None:
        self.session = session
        self.runtime = runtime
        self.repository = PlatformRepository(session)

    def read(self, view: ViewName, *, principal: Principal, limit: int = 100) -> list[dict[str, Any]]:
        self.runtime.require_enabled()
        if principal.roles.isdisjoint(VIEW_ROLES[view]):
            raise PermissionError("operations view is outside the principal role scope")
        apply_department_scope(self.session, principal)
        model, order_by = VIEW_MODELS[view]
        return self.repository.latest_payloads(
            model,
            departments=principal.allowed_departments,
            order_by=order_by,
            limit=limit,
        )

    def summary(self, *, principal: Principal) -> dict[str, object]:
        self.runtime.require_enabled()
        available_views = [
            view
            for view, roles in VIEW_ROLES.items()
            if not principal.roles.isdisjoint(roles)
        ]
        return {
            "generated_only": True,
            "operational": False,
            "runtime_enabled": self.runtime.enabled,
            "unified_search_enabled": False,
            "otel_export_enabled": False,
            "external_broker_enabled": False,
            "kubernetes_execution_enabled": False,
            "available_views": available_views,
            "counts": {
                view: len(self.read(view, principal=principal, limit=200))
                for view in available_views
            },
        }
