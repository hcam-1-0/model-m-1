from hcam.operations.platform.budgets import calculate_error_budget
from hcam.operations.platform.contracts import (
    BurnWindowV1,
    ErrorBudgetStateV1,
    HealthProjectionV1,
    ServiceObjectiveV1,
)
from hcam.operations.platform.degradation import decide_degradation
from hcam.operations.platform.objectives import compliance_ratio, health_projection


def _objective(
    target_state: str = "approved",
    target_ratio: float | None = 0.99,
    *,
    windows: list[BurnWindowV1] | None = None,
) -> ServiceObjectiveV1:
    return ServiceObjectiveV1(
        objective_id="ref_" + "1" * 32,
        department="Generated Department",
        service_class="api",
        indicator="request:success",
        target_state=target_state,
        target_ratio=target_ratio,
        windows=windows or [BurnWindowV1(window_seconds=300, good=990, valid=1000, bad=10, unknown=0)],
        revision=1,
    )


def test_budget_and_health_are_deterministic() -> None:
    objective = _objective()
    budget = calculate_error_budget(objective)
    assert budget.status == "exhausted"
    assert health_projection(objective).state == "healthy"
    degradation = decide_degradation(budget, health_projection(objective), optional_lanes=["generated-ai"])
    assert degradation.state == "degraded"
    assert degradation.mandatory_controls_preserved is True
    assert degradation.optional_lanes_bypassed == ["generated-ai"]


def test_unset_objective_remains_unknown() -> None:
    objective = _objective("unset", None)
    assert calculate_error_budget(objective).status == "unknown"
    assert health_projection(objective).state == "unknown"


def test_objective_quality_health_and_budget_states_are_explicit() -> None:
    unknown = _objective(
        windows=[BurnWindowV1(window_seconds=300, good=0, valid=0, bad=0, unknown=10)]
    )
    partial = _objective(
        target_ratio=0.95,
        windows=[BurnWindowV1(window_seconds=300, good=96, valid=100, bad=4, unknown=1)],
    )
    stopped = _objective(
        windows=[BurnWindowV1(window_seconds=300, good=0, valid=10, bad=10, unknown=0)]
    )
    assert health_projection(unknown).state == "unknown"
    assert compliance_ratio(unknown.windows[0]) is None
    assert calculate_error_budget(unknown).status == "unknown"
    assert health_projection(partial).state == "healthy"
    assert calculate_error_budget(partial).status == "at_risk"
    assert health_projection(stopped).state == "stopped"


def test_health_reports_degraded_and_budget_reports_within_target() -> None:
    degraded = _objective(
        target_ratio=0.99,
        windows=[BurnWindowV1(window_seconds=300, good=98, valid=100, bad=2, unknown=0)],
    )
    within = _objective(
        target_ratio=0.99,
        windows=[BurnWindowV1(window_seconds=300, good=999, valid=1000, bad=1, unknown=0)],
    )
    assert health_projection(degraded).state == "degraded"
    assert calculate_error_budget(within).status == "within_budget"


def test_budget_handles_perfect_target_and_multiburn_risk() -> None:
    perfect = _objective(
        target_ratio=1.0,
        windows=[BurnWindowV1(window_seconds=300, good=100, valid=100, bad=0, unknown=0)],
    )
    assert calculate_error_budget(perfect).status == "unknown"
    failing_perfect = _objective(
        target_ratio=1.0,
        windows=[BurnWindowV1(window_seconds=300, good=99, valid=100, bad=1, unknown=0)],
    )
    assert calculate_error_budget(failing_perfect).status == "exhausted"
    multiburn = _objective(
        windows=[
            BurnWindowV1(window_seconds=300, good=998, valid=1000, bad=2, unknown=0),
            BurnWindowV1(window_seconds=3600, good=95, valid=100, bad=5, unknown=0),
        ]
    )
    assert calculate_error_budget(multiburn).status == "at_risk"


def test_degradation_covers_normal_unknown_risk_and_stop() -> None:
    healthy = HealthProjectionV1(
        service_class="api", state="healthy", reason_codes=["objective.within_target"]
    )
    unknown = HealthProjectionV1(
        service_class="api", state="unknown", reason_codes=["objective.data_unknown"]
    )
    stopped = HealthProjectionV1(
        service_class="api", state="stopped", reason_codes=["objective.no_good_events"]
    )
    base = ErrorBudgetStateV1(
        objective_id="ref_" + "1" * 32,
        target_state="approved",
        compliance_ratio=1.0,
        remaining_ratio=1.0,
        burn_rates=[0.0],
        data_quality="complete",
        status="within_budget",
    )
    assert decide_degradation(base, healthy, optional_lanes=["lane:z"]).state == "normal"
    assert decide_degradation(base, unknown, optional_lanes=["lane:z"]).state == "constrained"
    assert (
        decide_degradation(
            base.model_copy(update={"status": "at_risk"}),
            healthy,
            optional_lanes=[],
        ).state
        == "constrained"
    )
    assert decide_degradation(base, stopped, optional_lanes=["lane:z", "lane:z"]).state == "stopped"
