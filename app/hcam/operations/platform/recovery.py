from __future__ import annotations

from hcam.operations.platform.contracts import RecoveryPlanV1, RecoverySimulationResultV1


def recovery_order(plan: RecoveryPlanV1) -> list[str]:
    known = {asset.asset_ref for asset in plan.assets}
    if len(known) != len(plan.assets):
        raise ValueError("recovery asset references must be unique")
    dependencies = {asset.asset_ref: set(asset.dependencies) for asset in plan.assets}
    if any(not values <= known for values in dependencies.values()):
        raise ValueError("recovery dependency is unknown")
    ordered: list[str] = []
    while dependencies:
        ready = sorted(key for key, values in dependencies.items() if values <= set(ordered))
        if not ready:
            raise ValueError("recovery dependency graph contains a cycle")
        for key in ready:
            ordered.append(key)
            dependencies.pop(key)
    return ordered


def simulate_recovery(
    plan: RecoveryPlanV1,
    *,
    unavailable: frozenset[str] = frozenset(),
    corrupted: frozenset[str] = frozenset(),
    interrupt_after: int | None = None,
) -> RecoverySimulationResultV1:
    ordered = recovery_order(plan)
    if interrupt_after is not None and not 0 <= interrupt_after <= len(ordered):
        raise ValueError("interruption point is outside the recovery plan")
    restored: list[str] = []
    missing: list[str] = []
    integrity: list[str] = []
    completed = 0
    for reference in ordered:
        if interrupt_after is not None and completed >= interrupt_after:
            missing.extend(item for item in ordered[completed:] if item not in missing)
            break
        completed += 1
        if reference in unavailable:
            missing.append(reference)
        elif reference in corrupted:
            integrity.append(reference)
        else:
            restored.append(reference)
    if integrity:
        outcome = "failed"
    elif missing:
        outcome = "partial"
    else:
        outcome = "complete"
    return RecoverySimulationResultV1(
        plan_id=plan.plan_id,
        outcome=outcome,
        restored_assets=restored,
        missing_assets=sorted(set(missing)),
        integrity_failures=integrity,
        observed_rpo_seconds=None,
        observed_rto_seconds=None,
    )
