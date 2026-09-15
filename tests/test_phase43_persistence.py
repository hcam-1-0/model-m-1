from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from hcam.intelligence.alerts.canonical import stable_id
from hcam.intelligence.alerts.contracts import (
    AlertLifecycleCommandV1,
    AlertReviewDecisionV1,
    ProposedAlertCommandV1,
)
from hcam.intelligence.alerts.identity import derive_alert_identity
from hcam.intelligence.alerts.persistence import (
    AlertConflictError,
    AlertPersistence,
    AlertPolicyError,
    AlertPreconditionError,
)
from hcam.intelligence.models import (
    Alert,
    AlertAssignmentEvent,
    AlertCommandReceipt,
    AlertLifecycleRecord,
    AlertMergeRelation,
    AlertReviewDecision,
    AlertReviewQuorumPolicy,
    AlertRevision,
    AlertSuppressionEvent,
    AlertTimerIntent,
)
from hcam.intelligence.rules.compiler import compile_rule
from hcam.intelligence.rules.contracts import RuleInputV1, VisualRuleDocumentV1
from hcam.intelligence.rules.persistence import RuleControlService
from hcam.intelligence.rules.runtime import run_and_store_generated_evidence
from hcam.main import create_app
from hcam.security.auth import Principal
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


RULE_FIXTURE = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")
DEPARTMENT = "Engineering Lab"
NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def principal(actor: str = "phase43-admin") -> Principal:
    return Principal(
        actor_id=actor,
        roles=frozenset({"platform.admin", "intelligence.reviewer"}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )


def application(tmp_path: Path, *, enabled: bool = True) -> FastAPI:
    app = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase43.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_control_plane_enabled=True,
            intelligence_generated_rule_evaluation_enabled=True,
            intelligence_generated_alert_lifecycle_enabled=enabled,
        )
    )
    app.state.database.create_schema()
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=2)
    return app


def source_evaluation(app: FastAPI):
    document_value = deepcopy(json.loads(RULE_FIXTURE.read_text(encoding="utf-8"))["documents"][0])
    document_value["department"] = DEPARTMENT
    document = VisualRuleDocumentV1.model_validate(document_value)
    owner = principal()
    with app.state.database.session_factory() as session:
        row = RuleControlService(session, enabled=True).create(
            document,
            [synthetic_stream_id(1)],
            principal=owner,
            reason="Generated Phase 4.3 source rule",
            request_id="generated-request",
        )
        record_id = row.rule_record_id
    compiled = compile_rule(document)
    rule_input = RuleInputV1(
        input_id="generated-phase43-input",
        input_kind="event",
        type_code="generated.vehicle.observed",
        department=DEPARTMENT,
        partition_digest="sha256:" + "2" * 64,
        stream_id=synthetic_stream_id(1),
        occurred_at=NOW,
        watermark_at=NOW + timedelta(minutes=1),
        values={
            "event_kind": "generated.vehicle.observed",
            "object_class": "vehicle.car",
            "confidence": 0.95,
            "uncertainty": 0.05,
            "direction": "forward",
            "count": 1,
            "rate": 1.0,
            "chronology_complete": True,
            "contradiction": False,
        },
    )
    with app.state.database.session_factory() as session:
        return record_id, run_and_store_generated_evidence(
            session,
            rule_record_id=record_id,
            compiled=compiled,
            inputs=[rule_input],
            interval_start=NOW,
            recorded_at=NOW + timedelta(minutes=2),
        )


def proposal(record_id: str, evaluation, *, delivery_id: str = "generated.delivery.1") -> ProposedAlertCommandV1:
    return ProposedAlertCommandV1(
        delivery_id=delivery_id,
        evaluation_id=evaluation.evaluation_id,
        evaluation_revision=evaluation.revision,
        evaluation_digest=evaluation.evaluation_digest,
        rule_record_id=record_id,
        compilation_id=evaluation.compilation_id,
        department=DEPARTMENT,
        partition_digest=evaluation.partition_digest,
        occurred_at=NOW,
        evidence_refs=evaluation.evidence_input_ids,
        incident_key="generated.incident.1",
        severity="high",
        priority="urgent",
        confidence=0.95,
        certainty=0.9,
        chronology_confidence=0.95,
    )


def seed_alert(app: FastAPI):
    record_id, evaluation = source_evaluation(app)
    with app.state.database.session_factory() as session:
        alert, duplicate = AlertPersistence(session, enabled=True).propose(
            proposal(record_id, evaluation),
            principal=principal(),
            reason="Generated Phase 4.3 alert proposal",
            request_id="generated-alert-request",
        )
    return alert, evaluation


def test_semantic_and_delivery_idempotency_persist_distinct_receipts(tmp_path: Path) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        owner = principal()
        with app.state.database.session_factory() as session:
            service = AlertPersistence(session, enabled=True)
            first, duplicate = service.propose(
                proposal(record_id, evaluation),
                principal=owner,
                reason="Generated first alert proposal",
                request_id="request-1",
            )
            assert duplicate is False
        with app.state.database.session_factory() as session:
            same, duplicate = AlertPersistence(session, enabled=True).propose(
                proposal(record_id, evaluation),
                principal=owner,
                reason="Generated repeated delivery proposal",
                request_id="request-2",
            )
            assert duplicate is True and same.alert_id == first.alert_id
        with app.state.database.session_factory() as session:
            redelivery, duplicate = AlertPersistence(session, enabled=True).propose(
                proposal(record_id, evaluation, delivery_id="generated.delivery.2"),
                principal=owner,
                reason="Generated semantic duplicate proposal",
                request_id="request-3",
            )
            assert duplicate is True and redelivery.alert_id == first.alert_id
        with app.state.database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Alert)) == 1
            assert session.scalar(select(func.count()).select_from(AlertCommandReceipt)) == 2
            assert session.scalar(select(func.count()).select_from(AlertReviewQuorumPolicy)) == 1
            assert session.scalar(select(func.count()).select_from(AlertRevision)) == 1
            assert session.scalar(select(func.count()).select_from(StreamEventOutbox)) >= 2
    finally:
        app.state.database.dispose()


def test_same_delivery_with_different_semantic_material_fails_closed(tmp_path: Path) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        owner = principal()
        with app.state.database.session_factory() as session:
            AlertPersistence(session, enabled=True).propose(
                proposal(record_id, evaluation),
                principal=owner,
                reason="Generated first alert proposal",
                request_id="request-1",
            )
        changed = proposal(record_id, evaluation).model_copy(
            update={"incident_key": "generated.incident.changed"}
        )
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError):
                AlertPersistence(session, enabled=True).propose(
                    changed,
                    principal=owner,
                    reason="Generated conflicting alert proposal",
                    request_id="request-2",
                )
    finally:
        app.state.database.dispose()


def test_concurrent_proposal_recovery_converges_and_rejects_receipt_drift(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        owner = principal()
        with app.state.database.session_factory() as session:
            first, _ = AlertPersistence(session, enabled=True).propose(
                proposal(record_id, evaluation),
                principal=owner,
                reason="Generated first concurrent proposal",
                request_id="concurrent-first",
            )
        redelivery = proposal(
            record_id, evaluation, delivery_id="generated.delivery.concurrent.2"
        )
        identity = derive_alert_identity(redelivery)
        with app.state.database.session_factory() as session:
            recovered, duplicate = AlertPersistence(
                session, enabled=True
            )._recover_concurrent_proposal(redelivery, identity, owner)
            assert duplicate is True and recovered.alert_id == first.alert_id
        with app.state.database.session_factory() as session:
            recovered, duplicate = AlertPersistence(
                session, enabled=True
            )._recover_concurrent_proposal(redelivery, identity, owner)
            assert duplicate is True and recovered.alert_id == first.alert_id
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError, match="delivery identity"):
                AlertPersistence(session, enabled=True)._recover_concurrent_proposal(
                    redelivery,
                    identity.model_copy(
                        update={"occurrence_digest": "sha256:" + "f" * 64}
                    ),
                    owner,
                )
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError, match="alert identity"):
                AlertPersistence(session, enabled=True)._recover_concurrent_proposal(
                    redelivery,
                    identity.model_copy(update={"semantic_key": "sha256:" + "e" * 64}),
                    owner,
                )
    finally:
        app.state.database.dispose()


def lifecycle_command(
    action: str,
    version: int,
    *,
    command_id: str | None = None,
    target_alert_id: str | None = None,
    assignee_id: str | None = None,
    reason: str = "Generated Phase 4.3 lifecycle decision",
) -> AlertLifecycleCommandV1:
    return AlertLifecycleCommandV1(
        command_id=command_id or f"generated.command.{action}.{version}",
        action=action,
        expected_version=version,
        actor_id="phase43-admin",
        reason=reason,
        target_alert_id=target_alert_id,
        assignee_id=assignee_id,
    )


def test_lifecycle_commands_are_idempotent_and_orthogonal_records_are_append_only(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        alert, _ = seed_alert(app)
        owner = principal()
        queue = lifecycle_command("queue_review", 1)
        with app.state.database.session_factory() as session:
            queued = AlertPersistence(session, enabled=True).transition(
                alert.alert_id, queue, principal=owner, request_id="queue-1"
            )
            assert queued.state == "queued_review" and queued.version == 2
        with app.state.database.session_factory() as session:
            replay = AlertPersistence(session, enabled=True).transition(
                alert.alert_id, queue, principal=owner, request_id="queue-replay"
            )
            assert replay == queued
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError, match="different material"):
                AlertPersistence(session, enabled=True).transition(
                    alert.alert_id,
                    lifecycle_command(
                        "queue_review",
                        1,
                        command_id=queue.command_id,
                        reason="Generated different lifecycle decision",
                    ),
                    principal=owner,
                    request_id="queue-conflict",
                )

        with app.state.database.session_factory() as session:
            assigned = AlertPersistence(session, enabled=True).transition(
                alert.alert_id,
                lifecycle_command(
                    "assign", 2, assignee_id="generated-reviewer-one"
                ),
                principal=owner,
                request_id="assign",
            )
            assert assigned.state == "queued_review"
            assert assigned.assigned_to == "generated-reviewer-one"
        with app.state.database.session_factory() as session:
            suppressed = AlertPersistence(session, enabled=True).transition(
                alert.alert_id,
                lifecycle_command("suppress", 3),
                principal=owner,
                request_id="suppress",
            )
            assert suppressed.state == "suppressed"
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertPreconditionError):
                AlertPersistence(session, enabled=True).transition(
                    alert.alert_id,
                    lifecycle_command("reopen", 3),
                    principal=owner,
                    request_id="stale",
                )
            with pytest.raises(AlertPolicyError, match="append-only review"):
                AlertPersistence(session, enabled=True).transition(
                    alert.alert_id,
                    lifecycle_command("accept", 4),
                    principal=owner,
                    request_id="direct-accept",
                )
        with app.state.database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Alert)) == 1
            assert session.scalar(select(func.count()).select_from(AlertRevision)) == 4
            assert session.scalar(select(func.count()).select_from(AlertLifecycleRecord)) == 3
            assert session.scalar(select(func.count()).select_from(AlertAssignmentEvent)) == 1
            assert session.scalar(select(func.count()).select_from(AlertSuppressionEvent)) == 1
            assert session.scalar(select(func.count()).select_from(AlertCommandReceipt)) == 4
    finally:
        app.state.database.dispose()


def test_merge_cycles_and_invalid_targets_fail_closed(tmp_path: Path) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        owner = principal()
        with app.state.database.session_factory() as session:
            first, _ = AlertPersistence(session, enabled=True).propose(
                proposal(record_id, evaluation),
                principal=owner,
                reason="Generated first merge candidate",
                request_id="merge-first",
            )
        second_command = proposal(
            record_id, evaluation, delivery_id="generated.delivery.merge.2"
        ).model_copy(update={"incident_key": "generated.incident.merge.2"})
        with app.state.database.session_factory() as session:
            second, _ = AlertPersistence(session, enabled=True).propose(
                second_command,
                principal=owner,
                reason="Generated second merge candidate",
                request_id="merge-second",
            )
        with app.state.database.session_factory() as session:
            merged = AlertPersistence(session, enabled=True).transition(
                first.alert_id,
                lifecycle_command("merge", 1, target_alert_id=second.alert_id),
                principal=owner,
                request_id="merge",
            )
            assert merged.state == "merged" and merged.merged_into == second.alert_id
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError, match="cycle"):
                AlertPersistence(session, enabled=True).transition(
                    second.alert_id,
                    lifecycle_command("merge", 1, target_alert_id=first.alert_id),
                    principal=owner,
                    request_id="cycle",
                )
            with pytest.raises(AlertConflictError, match="invalid"):
                AlertPersistence(session, enabled=True).transition(
                    second.alert_id,
                    lifecycle_command(
                        "merge",
                        1,
                        command_id="generated.command.self-merge.1",
                        target_alert_id=second.alert_id,
                    ),
                    principal=owner,
                    request_id="self-merge",
                )
        with app.state.database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(AlertMergeRelation)) == 1
    finally:
        app.state.database.dispose()


def test_review_denial_is_idempotent_and_content_drift_is_rejected(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        alert, evaluation = seed_alert(app)
        owner = principal()
        with app.state.database.session_factory() as session:
            service = AlertPersistence(session, enabled=True)
            queued = service.transition(
                alert.alert_id,
                lifecycle_command("queue_review", 1),
                principal=owner,
                request_id="review-queue",
            )
        with app.state.database.session_factory() as session:
            started = AlertPersistence(session, enabled=True).transition(
                alert.alert_id,
                lifecycle_command("start_review", queued.version),
                principal=owner,
                request_id="review-start",
            )
        with app.state.database.session_factory() as session:
            policy = AlertPersistence(session, enabled=True).get_review_policy(
                alert.alert_id, owner
            )
        decision = AlertReviewDecisionV1(
            decision_id=stable_id("ardc", alert.alert_id, "deny"),
            alert_id=alert.alert_id,
            department=alert.department,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            reviewer_id=owner.actor_id,
            reviewer_role="platform.admin",
            decision="deny",
            evidence_digest=evaluation.evaluation_digest,
            reason="Generated denial review decision",
            recorded_at=NOW + timedelta(minutes=5),
        )
        with app.state.database.session_factory() as session:
            rejected, outcome = AlertPersistence(session, enabled=True).review(
                alert.alert_id,
                decision,
                expected_version=started.version,
                principal=owner,
                request_id="deny",
            )
            assert outcome == "rejected" and rejected.state == "rejected"
        with app.state.database.session_factory() as session:
            replay, outcome = AlertPersistence(session, enabled=True).review(
                alert.alert_id,
                decision,
                expected_version=started.version,
                principal=owner,
                request_id="deny-replay",
            )
            assert outcome == "rejected" and replay.version == rejected.version
        with app.state.database.session_factory() as session:
            with pytest.raises(AlertConflictError, match="different material"):
                AlertPersistence(session, enabled=True).review(
                    alert.alert_id,
                    decision.model_copy(update={"reason": "Generated changed review decision"}),
                    expected_version=rejected.version,
                    principal=owner,
                    request_id="deny-conflict",
                )
            assert session.scalar(select(func.count()).select_from(AlertReviewDecision)) == 1
    finally:
        app.state.database.dispose()


def test_generated_high_impact_workflow_uses_configurable_distinct_quorum(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        owner = principal()
        high_impact = proposal(record_id, evaluation).model_copy(
            update={"severity": "critical", "priority": "immediate"}
        )
        with app.state.database.session_factory() as session:
            alert, _ = AlertPersistence(
                session, enabled=True, high_impact_quorum=2
            ).propose(
                high_impact,
                principal=owner,
                reason="Generated high-impact alert proposal",
                request_id="high-impact",
            )
        with app.state.database.session_factory() as session:
            service = AlertPersistence(session, enabled=True, high_impact_quorum=2)
            policy = service.get_review_policy(alert.alert_id, owner)
            assert policy.workflow_class == "generated_high_impact"
            assert policy.required_distinct_reviewers == 2
        with app.state.database.session_factory() as session:
            queued = AlertPersistence(session, enabled=True).transition(
                alert.alert_id,
                lifecycle_command("queue_review", 1),
                principal=owner,
                request_id="high-impact-queue",
            )
        with app.state.database.session_factory() as session:
            started = AlertPersistence(session, enabled=True).transition(
                alert.alert_id,
                lifecycle_command("start_review", queued.version),
                principal=owner,
                request_id="high-impact-start",
            )

        def approval(actor: str) -> AlertReviewDecisionV1:
            return AlertReviewDecisionV1(
                decision_id=stable_id("ardc", alert.alert_id, actor),
                alert_id=alert.alert_id,
                department=alert.department,
                policy_id=policy.policy_id,
                policy_version=policy.policy_version,
                reviewer_id=actor,
                reviewer_role="intelligence.reviewer",
                decision="approve",
                evidence_digest=evaluation.evaluation_digest,
                reason="Generated high-impact approval decision",
                recorded_at=NOW + timedelta(minutes=5),
            )

        first_reviewer = principal("generated-reviewer-one")
        with app.state.database.session_factory() as session:
            pending, outcome = AlertPersistence(session, enabled=True).review(
                alert.alert_id,
                approval(first_reviewer.actor_id),
                expected_version=started.version,
                principal=first_reviewer,
                request_id="first-review",
            )
            assert outcome == "pending" and pending.state == "under_review"
        second_reviewer = principal("generated-reviewer-two")
        with app.state.database.session_factory() as session:
            accepted, outcome = AlertPersistence(session, enabled=True).review(
                alert.alert_id,
                approval(second_reviewer.actor_id),
                expected_version=started.version,
                principal=second_reviewer,
                request_id="second-review",
            )
            assert outcome == "approved" and accepted.state == "accepted"
        with pytest.raises(ValueError, match="between 1 and 5"):
            AlertPersistence(None, enabled=True, high_impact_quorum=6)  # type: ignore[arg-type]
    finally:
        app.state.database.dispose()


def test_generated_system_health_lane_does_not_create_human_review_policy(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        record_id, evaluation = source_evaluation(app)
        health = proposal(record_id, evaluation).model_copy(
            update={
                "domain": "system_health",
                "authority_class": "bounded_automation",
                "incident_key": "generated.system-health.1",
            }
        )
        with app.state.database.session_factory() as session:
            alert, duplicate = AlertPersistence(session, enabled=True).propose(
                health,
                principal=principal(),
                reason="Generated isolated system-health proposal",
                request_id="health",
            )
            assert duplicate is False and alert.domain == "system_health"
        with app.state.database.session_factory() as session:
            assert session.scalar(
                select(func.count()).select_from(AlertReviewQuorumPolicy)
            ) == 0
    finally:
        app.state.database.dispose()


def test_persisted_timer_claim_recovery_resolution_and_sqlite_boundary(
    tmp_path: Path,
) -> None:
    app = application(tmp_path)
    try:
        alert, _ = seed_alert(app)
        owner = principal()
        now = datetime.now(UTC)
        with app.state.database.session_factory.begin() as session:
            timer = AlertPersistence(session, enabled=True).schedule_timer(
                alert.alert_id,
                "review_sla",
                due_at=now,
                principal=owner,
            )
        with app.state.database.session_factory.begin() as session:
            service = AlertPersistence(session, enabled=True)
            with pytest.raises(AlertPolicyError, match="exactly one"):
                service.claim_due_timers(
                    worker_id="worker-1", now=now, limit=1, worker_count=2
                )
            claimed = service.claim_due_timers(worker_id="worker-1", now=now, limit=1)
            assert len(claimed) == 1 and claimed[0].attempt_count == 1
        with app.state.database.session_factory.begin() as session:
            assert not AlertPersistence(session, enabled=True).claim_due_timers(
                worker_id="worker-2", now=now + timedelta(seconds=89), limit=1
            )
        with app.state.database.session_factory.begin() as session:
            recovered = AlertPersistence(session, enabled=True).claim_due_timers(
                worker_id="worker-2", now=now + timedelta(seconds=91), limit=1
            )
            assert len(recovered) == 1 and recovered[0].attempt_count == 2
        with app.state.database.session_factory.begin() as session:
            resolved = AlertPersistence(session, enabled=True).resolve_claimed_timer(
                timer.timer_id,
                worker_id="worker-2",
                alert_version=alert.version + 1,
                now=now + timedelta(seconds=92),
                succeeded=True,
            )
            assert resolved.state == "cancelled"
        with app.state.database.session_factory() as session:
            stored = session.get(AlertTimerIntent, timer.timer_id)
            assert stored is not None and stored.lease_owner is None
    finally:
        app.state.database.dispose()
