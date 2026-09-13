import pytest

from hcam.acceptance.runbooks import (
    build_generated_runbook,
    build_production_prerequisites,
    validate_non_operational,
)


def test_runbook_and_prerequisites_remain_non_operational() -> None:
    runbook = build_generated_runbook()
    outline = build_production_prerequisites()
    validate_non_operational(runbook, outline)
    assert len(runbook.steps) == 10
    assert all(
        item.status == "not_operationally_validated" for item in outline.prerequisites
    )


def test_runbook_validation_fails_closed() -> None:
    runbook = build_generated_runbook()
    outline = build_production_prerequisites()
    with pytest.raises(ValueError):
        validate_non_operational(
            runbook.model_copy(update={"production_use": True}), outline
        )
    altered = outline.model_copy(update={"operationally_validated": True})
    with pytest.raises(ValueError):
        validate_non_operational(runbook, altered)
    altered_item = outline.prerequisites[0].model_copy(update={"status": "invalid"})
    with pytest.raises(ValueError):
        validate_non_operational(
            runbook,
            outline.model_copy(update={"prerequisites": (altered_item,)}),
        )
    executable_item = outline.prerequisites[0].model_copy(update={"executable": True})
    with pytest.raises(ValueError):
        validate_non_operational(
            runbook,
            outline.model_copy(update={"prerequisites": (executable_item,)}),
        )
