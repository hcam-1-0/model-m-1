from __future__ import annotations

from hcam.acceptance.contracts import (
    AccessibilityRequirementV1,
    EventOperationV1,
    EventWorkflowCatalogueV1,
    HttpCatalogueV1,
    HttpOperationV1,
    UiAccessibilityCatalogueV1,
    UiStateV1,
    WorkflowStepV1,
    WorkflowV1,
)


def _http(
    operation_id: str,
    method: str,
    path: str,
    *,
    purpose: str,
    command: bool = False,
    pagination: str = "none",
    freshness: str = "current",
) -> HttpOperationV1:
    return HttpOperationV1(
        operation_id=operation_id,
        method=method,
        path_template=path,
        purpose=purpose,
        audience=("phase5.operator_ui",),
        authorization_roles=("intelligence.viewer", "intelligence.reviewer")
        if not command
        else ("intelligence.reviewer",),
        department_scope_required=True,
        reason_required=command,
        etag_mode="if_match" if command else "response",
        idempotency_mode="required" if command else "none",
        pagination=pagination,
        freshness=freshness,
        success_states=("success", "empty", "partial")
        if not command
        else ("accepted", "conflict"),
        failure_codes=(
            "authorization.denied",
            "resource.not_found",
            "request.invalid",
            "service.unavailable",
        ),
        compatibility_class="stable",
    )


def build_http_catalogue() -> HttpCatalogueV1:
    operations = (
        _http(
            "intelligence.health.read",
            "GET",
            "/intelligence-health",
            purpose="read_intelligence_health",
            freshness="fresh_stale_unknown",
        ),
        _http(
            "hypotheses.list",
            "GET",
            "/correlation-hypotheses",
            purpose="list_hypotheses",
            pagination="cursor",
            freshness="fresh_stale_unknown",
        ),
        _http(
            "runs.list",
            "GET",
            "/correlation-runs",
            purpose="list_correlation_runs",
            pagination="cursor",
        ),
        _http(
            "runs.detail",
            "GET",
            "/correlation-runs/{run_id}",
            purpose="read_correlation_run",
        ),
        _http(
            "alerts.list",
            "GET",
            "/generated-alerts",
            purpose="list_generated_alerts",
            pagination="cursor",
            freshness="fresh_stale_unknown",
        ),
        _http(
            "alerts.detail",
            "GET",
            "/generated-alerts/{alert_id}",
            purpose="read_generated_alert",
        ),
        _http(
            "alerts.review",
            "POST",
            "/generated-alerts/{alert_id}/reviews",
            purpose="review_generated_alert",
            command=True,
        ),
        _http(
            "alerts.lifecycle",
            "POST",
            "/generated-alerts/{alert_id}/lifecycle",
            purpose="transition_generated_alert",
            command=True,
        ),
        _http(
            "reference.health",
            "GET",
            "/reference-integrations/health",
            purpose="read_reference_health",
            freshness="fresh_stale_unknown",
        ),
        _http(
            "reference.queries.detail",
            "GET",
            "/reference-integrations/queries/{job_id}",
            purpose="read_reference_query",
            freshness="fresh_stale_unknown",
        ),
        _http(
            "timelines.list",
            "GET",
            "/timelines",
            purpose="list_investigation_timelines",
            pagination="cursor",
        ),
        _http(
            "timelines.detail",
            "GET",
            "/timelines/{timeline_id}",
            purpose="read_investigation_timeline",
        ),
        _http(
            "timelines.reconstruction",
            "GET",
            "/timelines/{timeline_id}/reconstruction",
            purpose="read_timeline_reconstruction",
        ),
        _http(
            "timelines.entries.create",
            "POST",
            "/timelines/{timeline_id}/entries",
            purpose="append_timeline_entry",
            command=True,
        ),
        _http(
            "timelines.corrections.create",
            "POST",
            "/timelines/{timeline_id}/corrections",
            purpose="append_timeline_correction",
            command=True,
        ),
        _http(
            "operations.summary",
            "GET",
            "/operations/summary",
            purpose="read_operations_summary",
            freshness="fresh_stale_unknown",
        ),
    )
    return HttpCatalogueV1(operations=operations)


def build_event_workflows() -> EventWorkflowCatalogueV1:
    events = tuple(
        EventOperationV1(
            event_type=event_type,
            producer=producer,
            consumer_intent=intent,
            ordering="aggregate",
            delivery="transactional_outbox",
            correction_supported=True,
            unknown_version="quarantine",
        )
        for event_type, producer, intent in (
            (
                "hcam.correlation.hypothesis.changed.v1",
                "correlation.service",
                "refresh_hypothesis_views",
            ),
            (
                "hcam.intelligence.alert.changed.v1",
                "alert.service",
                "refresh_alert_views",
            ),
            (
                "hcam.intelligence.review.recorded.v1",
                "review.service",
                "refresh_review_state",
            ),
            (
                "hcam.investigation.timeline.changed.v1",
                "investigation.service",
                "refresh_timeline_views",
            ),
            (
                "hcam.investigation.correction.recorded.v1",
                "investigation.service",
                "show_correction_state",
            ),
            (
                "hcam.operations.degradation.changed.v1",
                "operations.service",
                "show_degradation_state",
            ),
        )
    )
    investigation_steps = (
        WorkflowStepV1(
            step_id="load_alert",
            operation_ref="alerts.detail",
            depends_on=(),
            success_state="success",
            failure_codes=("authorization.denied", "resource.not_found"),
        ),
        WorkflowStepV1(
            step_id="review_alert",
            operation_ref="alerts.review",
            depends_on=("load_alert",),
            success_state="accepted",
            failure_codes=("authorization.denied", "request.invalid"),
        ),
        WorkflowStepV1(
            step_id="load_timeline",
            operation_ref="timelines.detail",
            depends_on=("review_alert",),
            success_state="success",
            failure_codes=("resource.not_found", "service.unavailable"),
        ),
        WorkflowStepV1(
            step_id="reconstruct",
            operation_ref="timelines.reconstruction",
            depends_on=("load_timeline",),
            success_state="success",
            failure_codes=("resource.not_found", "service.unavailable"),
        ),
    )
    workflows = (
        WorkflowV1(
            workflow_id="phase5.review_and_investigate", steps=investigation_steps
        ),
        WorkflowV1(
            workflow_id="phase5.observe_degradation",
            steps=(
                WorkflowStepV1(
                    step_id="load_health",
                    operation_ref="operations.summary",
                    depends_on=(),
                    success_state="partial",
                    failure_codes=("service.unavailable",),
                ),
            ),
        ),
    )
    return EventWorkflowCatalogueV1(events=events, workflows=workflows)


def build_ui_accessibility() -> UiAccessibilityCatalogueV1:
    messages = {
        "loading": "Loading the latest generated intelligence state.",
        "empty": "No records match the current bounded query.",
        "partial": "Some generated results are available; completeness is limited.",
        "stale": "The displayed generated state is stale.",
        "degraded": "A supporting generated service is degraded.",
        "denied": "Access to this generated resource was denied.",
        "conflict": "The generated record changed before this action completed.",
        "failure": "The generated request failed without exposing internal detail.",
        "recovery": "The generated service recovered; refresh is available.",
        "correction": "A correction changed the generated record chronology.",
        "success": "The generated operation completed.",
    }
    states = tuple(
        UiStateV1(
            state_id=f"phase5.alerts.{state}",
            view="phase5.alerts",
            state=state,
            source_fact=f"alerts.{state}",
            visible_message=message,
            actions=("refresh",) if state not in {"loading", "denied"} else (),
            focus_rule="preserve_trigger_focus"
            if state in {"conflict", "failure", "denied"}
            else "preserve_context",
            announcement="assertive"
            if state == "failure"
            else ("polite" if state not in {"loading", "success"} else "none"),
        )
        for state, message in messages.items()
    )
    requirements = tuple(
        AccessibilityRequirementV1(
            requirement_id=f"phase5.accessibility.{category}",
            applies_to="phase5.operator_surfaces",
            category=category,
            requirement=requirement,
            evidence_kind="future_manual"
            if category in {"contrast", "motion", "target"}
            else "static",
        )
        for category, requirement in (
            (
                "keyboard",
                "Every action and state transition must be operable through a logical keyboard sequence.",
            ),
            (
                "focus",
                "Focus must remain visible and return to the initiating control after bounded overlays close.",
            ),
            (
                "name_role_value",
                "Controls and dynamic components must expose stable accessible names, roles, and values.",
            ),
            (
                "status",
                "Routine asynchronous updates must use non-interrupting status announcements.",
            ),
            (
                "error",
                "Errors must identify the affected field or operation and provide a recovery action.",
            ),
            (
                "non_color",
                "Severity and state must use text or icons in addition to color.",
            ),
            (
                "target",
                "Interactive target dimensions and spacing require validation in the implemented interface.",
            ),
            (
                "contrast",
                "Text, controls, focus indicators, and non-text content require measured contrast validation.",
            ),
            (
                "motion",
                "The implemented interface must honor reduced-motion preferences without hiding state changes.",
            ),
        )
    )
    return UiAccessibilityCatalogueV1(states=states, requirements=requirements)


def validate_handoff(
    http: HttpCatalogueV1,
    events: EventWorkflowCatalogueV1,
    ui: UiAccessibilityCatalogueV1,
) -> None:
    operation_ids = {item.operation_id for item in http.operations}
    if len(operation_ids) != len(http.operations):
        raise ValueError("HTTP operation IDs must be unique")
    for workflow in events.workflows:
        step_ids = {item.step_id for item in workflow.steps}
        for step in workflow.steps:
            if step.operation_ref not in operation_ids:
                raise ValueError("workflow references an unknown HTTP operation")
            if set(step.depends_on) - step_ids:
                raise ValueError("workflow dependency is missing")
    required_states = {
        "loading",
        "empty",
        "partial",
        "stale",
        "degraded",
        "denied",
        "conflict",
        "failure",
        "recovery",
        "correction",
        "success",
    }
    if {item.state for item in ui.states} != required_states:
        raise ValueError("the complete Phase 5 UI-state inventory is required")
    required_accessibility = {
        "keyboard",
        "focus",
        "name_role_value",
        "status",
        "error",
        "non_color",
        "target",
        "contrast",
        "motion",
    }
    if {item.category for item in ui.requirements} != required_accessibility:
        raise ValueError("the complete accessibility handoff inventory is required")
