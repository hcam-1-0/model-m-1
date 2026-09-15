from __future__ import annotations

from dataclasses import dataclass

from hcam.intelligence.alerts.persistence import AlertControlError


@dataclass(frozen=True, slots=True)
class AlertProblem:
    type: str
    title: str
    status: int
    reason_code: str


def problem_for(error: AlertControlError) -> AlertProblem:
    status = 409
    if error.reason_code == "alert_not_found":
        status = 404
    elif error.reason_code == "alert_control_disabled":
        status = 503
    elif error.reason_code == "alert_precondition_failed":
        status = 412
    elif error.reason_code == "alert_policy_denied":
        status = 422
    return AlertProblem(
        type=f"urn:hcam:problem:{error.reason_code}",
        title="Generated alert request was not accepted",
        status=status,
        reason_code=error.reason_code,
    )
