import pytest

from hcam.operations.platform.contracts import RecoveryAssetV1, RecoveryPlanV1
from hcam.operations.platform.recovery import recovery_order, simulate_recovery


def _plan() -> RecoveryPlanV1:
    first = "ref_" + "1" * 32
    second = "ref_" + "2" * 32
    return RecoveryPlanV1(
        plan_id="ref_" + "3" * 32,
        department="Generated Department",
        revision=1,
        assets=[
            RecoveryAssetV1(asset_ref=first, asset_class="configuration", recovery_tier="metadata", dependencies=[]),
            RecoveryAssetV1(asset_ref=second, asset_class="database", recovery_tier="control_state", dependencies=[first]),
        ],
    )


def test_recovery_is_restore_first_generated_simulation() -> None:
    plan = _plan()
    assert recovery_order(plan) == ["ref_" + "1" * 32, "ref_" + "2" * 32]
    result = simulate_recovery(plan)
    assert result.outcome == "complete"
    assert result.external_action_executed is False
    assert result.observed_rto_seconds is None


def test_recovery_reports_missing_and_corrupt_assets_honestly() -> None:
    plan = _plan()
    missing = simulate_recovery(plan, unavailable=frozenset({"ref_" + "2" * 32}))
    assert missing.outcome == "partial"
    corrupt = simulate_recovery(plan, corrupted=frozenset({"ref_" + "1" * 32}))
    assert corrupt.outcome == "failed"


def test_recovery_graph_and_interruption_bounds_fail_closed() -> None:
    plan = _plan()
    assert simulate_recovery(plan, interrupt_after=1).outcome == "partial"
    with pytest.raises(ValueError):
        simulate_recovery(plan, interrupt_after=3)
    duplicate = plan.model_copy(update={"assets": [plan.assets[0], plan.assets[0]]})
    with pytest.raises(ValueError):
        recovery_order(duplicate)
    unknown = plan.model_copy(
        update={
            "assets": [
                plan.assets[0].model_copy(update={"dependencies": ["ref_" + "9" * 32]})
            ]
        }
    )
    with pytest.raises(ValueError):
        recovery_order(unknown)
    cyclic = plan.model_copy(
        update={
            "assets": [
                plan.assets[0].model_copy(update={"dependencies": [plan.assets[1].asset_ref]}),
                plan.assets[1],
            ]
        }
    )
    with pytest.raises(ValueError):
        recovery_order(cyclic)
