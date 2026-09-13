from __future__ import annotations

from typing import Literal

from hcam.operations.platform.canonical import digest
from hcam.operations.platform.contracts import SupplyChainInventoryV1


def project_inventory(
    inventory: SupplyChainInventoryV1,
    *,
    format_name: Literal["spdx", "cyclonedx", "slsa"],
) -> dict[str, object]:
    components = [
        {
            "ref": item.component_ref,
            "name": item.name,
            "version": item.version,
            "digest": item.digest,
            "license_state": item.license_state,
            "vulnerability_state": item.vulnerability_state,
            "provenance_state": item.provenance_state,
        }
        for item in sorted(inventory.components, key=lambda component: component.component_ref)
    ]
    projection = {
        "format": format_name,
        "profile": f"hcam.generated.{format_name}.projection.v1",
        "inventory_id": inventory.inventory_id,
        "components": components,
        "loss_accounting": {
            "external_fields_omitted": True,
            "signatures_present": False,
            "attestations_present": False,
            "conformance_claimed": False,
        },
        "generated_only": True,
    }
    projection["projection_digest"] = digest(projection)
    return projection


def inventory_is_clean(inventory: SupplyChainInventoryV1) -> bool:
    return bool(inventory.components) and all(
        item.vulnerability_state == "verified" and item.provenance_state == "verified"
        for item in inventory.components
    )
