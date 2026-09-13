from datetime import UTC, datetime

from hcam.operations.platform.contracts import SupplyChainComponentV1, SupplyChainInventoryV1
from hcam.operations.platform.supply_chain import inventory_is_clean, project_inventory


def _inventory(state: str = "unknown") -> SupplyChainInventoryV1:
    component = SupplyChainComponentV1(
        component_ref="ref_" + "1" * 32,
        name="generated:component",
        version="generated:1",
        source="lockfile",
        digest="sha256:" + "2" * 64,
        license_state="verified",
        vulnerability_state=state,
        provenance_state=state,
    )
    return SupplyChainInventoryV1(
        inventory_id="ref_" + "3" * 32,
        observed_at=datetime(2026, 9, 5, tzinfo=UTC),
        freshness="unknown",
        components=[component],
        source_digest="sha256:" + "4" * 64,
    )


def test_supply_chain_unknown_never_becomes_clean() -> None:
    assert not inventory_is_clean(_inventory())
    assert inventory_is_clean(_inventory("verified"))


def test_supply_chain_projections_are_loss_accounted() -> None:
    for format_name in ("spdx", "cyclonedx", "slsa"):
        projection = project_inventory(_inventory(), format_name=format_name)
        assert projection["loss_accounting"]["conformance_claimed"] is False
        assert projection["projection_digest"].startswith("sha256:")
