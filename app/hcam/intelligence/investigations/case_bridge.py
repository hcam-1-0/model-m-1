from __future__ import annotations

from hcam.intelligence.investigations.contracts import CaseManagementBridgeContractV1


def validate_disabled_bridge(bridge: CaseManagementBridgeContractV1) -> None:
    if bridge.enabled or bridge.external_connection or bridge.legal_workflow:
        raise ValueError("case-management bridge must remain disabled")


def execute_bridge(_bridge: CaseManagementBridgeContractV1) -> None:
    raise RuntimeError("case-management integration is disabled and not authorized")
