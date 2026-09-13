from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.repository import AuditRepository
from hcam.intelligence.alerts.bounds import bounded_page_size, bounded_reason
from hcam.intelligence.alerts.canonical import digest, stable_id
from hcam.intelligence.alerts.contracts import (
    AlertAggregateV2,
    AlertIdentityV1,
    AlertLifecycleCommandV1,
    AlertLifecycleEventV2,
    AlertReviewDecisionV1,
    AlertTimerIntentV1,
    ProposedAlertCommandV1,
    ReviewQuorumPolicyV1,
)
from hcam.intelligence.alerts.identity import derive_alert_identity
from hcam.intelligence.alerts.lifecycle import AlertTransitionDenied, apply_transition
from hcam.intelligence.alerts.review import ReviewQuorum
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
    IntelligenceRule,
    IntelligenceRuleEvaluationRevision,
)
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal
from hcam.streams.models import StreamEventOutbox


class AlertControlError(RuntimeError):
    reason_code = "alert_control_error"


class AlertDisabledError(AlertControlError):
    reason_code = "alert_control_disabled"


class AlertNotFoundError(AlertControlError):
    reason_code = "alert_not_found"


class AlertConflictError(AlertControlError):
    reason_code = "alert_conflict"


class AlertPreconditionError(AlertControlError):
    reason_code = "alert_precondition_failed"


class AlertPolicyError(AlertControlError):
    reason_code = "alert_policy_denied"


def _aggregate(row: Alert) -> AlertAggregateV2:
    return AlertAggregateV2.model_validate(row.payload)


def _scoped(statement, model, principal: Principal):
    if principal.allowed_departments is not None:
        statement = statement.where(
            model.department.in_(sorted(principal.allowed_departments))
        )
    return statement


class AlertPersistence:
    def __init__(
        self, session: Session, *, enabled: bool, high_impact_quorum: int = 2
    ) -> None:
        if not 1 <= high_impact_quorum <= 5:
            raise ValueError("generated high-impact quorum must be between 1 and 5")
        self.session = session
        self.enabled = enabled
        self.high_impact_quorum = high_impact_quorum

    def propose(
        self,
        command: ProposedAlertCommandV1,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> tuple[AlertAggregateV2, bool]:
        self._require_enabled()
        reason = bounded_reason(reason)
        if not principal.can_access_department(command.department):
            raise AlertNotFoundError("generated evaluation was not found")
        identity = derive_alert_identity(command)
        now = datetime.now(UTC)
        try:
            with self.session.begin():
                apply_department_scope(self.session, principal)
                evaluation = self.session.scalar(
                    select(IntelligenceRuleEvaluationRevision).where(
                        IntelligenceRuleEvaluationRevision.evaluation_id
                        == command.evaluation_id,
                        IntelligenceRuleEvaluationRevision.revision
                        == command.evaluation_revision,
                        IntelligenceRuleEvaluationRevision.department
                        == command.department,
                    )
                )
                if (
                    evaluation is None
                    or evaluation.state != "matched"
                    or evaluation.snapshot_digest != command.evaluation_digest
                    or evaluation.rule_record_id != command.rule_record_id
                    or evaluation.compilation_id != command.compilation_id
                    or evaluation.partition_digest != command.partition_digest
                ):
                    raise AlertPolicyError("generated matched evaluation binding failed")

                receipt = self.session.scalar(
                    select(AlertCommandReceipt).where(
                        AlertCommandReceipt.department == command.department,
                        AlertCommandReceipt.delivery_key == identity.delivery_key,
                    )
                )
                if receipt is not None:
                    if (
                        receipt.semantic_key != identity.semantic_key
                        or receipt.occurrence_digest != identity.occurrence_digest
                    ):
                        raise AlertConflictError(
                            "delivery identity has different occurrence material"
                        )
                    row = self.session.get(Alert, receipt.alert_id)
                    if row is None:
                        raise AlertConflictError("delivery receipt has no alert")
                    return _aggregate(row), True

                row = self.session.scalar(
                    select(Alert).where(
                        Alert.department == command.department,
                        Alert.semantic_key == identity.semantic_key,
                    )
                )
                duplicate = row is not None
                if row is None:
                    policy_digest = digest(
                        {
                            "profile": "hcam.p4-3.authority.v1",
                            "domain": command.domain,
                            "authority_class": command.authority_class,
                        }
                    )
                    aggregate = AlertAggregateV2(
                        alert_id=identity.alert_id,
                        version=1,
                        department=command.department,
                        semantic_key=identity.semantic_key,
                        delivery_key=identity.delivery_key,
                        source_evaluation_id=command.evaluation_id,
                        source_evaluation_revision=command.evaluation_revision,
                        source_evaluation_digest=command.evaluation_digest,
                        incident_key=command.incident_key,
                        state="proposed",
                        domain=command.domain,
                        authority_class=command.authority_class,
                        severity=command.severity,
                        priority=command.priority,
                        confidence=command.confidence,
                        certainty=command.certainty,
                        chronology_confidence=command.chronology_confidence,
                        disposition="unreviewed",
                        evidence_refs=command.evidence_refs,
                        policy_digest=policy_digest,
                        created_at=now,
                        updated_at=now,
                    )
                    row = Alert(
                        alert_id=aggregate.alert_id,
                        version_id=aggregate.version,
                        department=aggregate.department,
                        hypothesis_id=None,
                        dedupe_key=aggregate.semantic_key,
                        semantic_key=aggregate.semantic_key,
                        delivery_key=aggregate.delivery_key,
                        source_evaluation_id=aggregate.source_evaluation_id,
                        source_evaluation_revision=aggregate.source_evaluation_revision,
                        source_evaluation_digest=aggregate.source_evaluation_digest,
                        incident_key=aggregate.incident_key,
                        domain=aggregate.domain,
                        state=aggregate.state,
                        authority_class=aggregate.authority_class,
                        operational=False,
                        generated_only=True,
                        severity=aggregate.severity,
                        priority=aggregate.priority,
                        confidence=aggregate.confidence,
                        certainty=aggregate.certainty,
                        chronology_confidence=aggregate.chronology_confidence,
                        disposition=aggregate.disposition,
                        payload=aggregate.model_dump(mode="json"),
                        content_digest=digest(aggregate),
                        retention_class="derived.intelligence.standard",
                        policy_digest=aggregate.policy_digest,
                        created_at=now,
                        updated_at=now,
                    )
                    self.session.add(row)
                    self.session.flush()
                    self._ensure_default_quorum(aggregate, now)
                    self._append_legacy_revision(
                        row,
                        previous_state="proposed",
                        actor_id=principal.actor_id,
                        reason=reason,
                        now=now,
                    )
                    self._outbox(row, "hcam.intelligence.alert.proposed.v2", now)
                    self._audit(principal, "intelligence.alert.p43.propose", row.alert_id, reason, request_id)
                else:
                    aggregate = _aggregate(row)
                    if aggregate.source_evaluation_digest != command.evaluation_digest:
                        raise AlertConflictError(
                            "semantic identity has different evaluation material"
                        )

                self.session.add(
                    AlertCommandReceipt(
                        receipt_id=stable_id("acpt", command.department, identity.delivery_key),
                        department=command.department,
                        delivery_key=identity.delivery_key,
                        semantic_key=identity.semantic_key,
                        occurrence_digest=identity.occurrence_digest,
                        alert_id=row.alert_id,
                        disposition="duplicate" if duplicate else "accepted",
                        generated_only=True,
                        recorded_at=now,
                    )
                )
            return _aggregate(row), duplicate
        except IntegrityError:
            self.session.rollback()
            return self._recover_concurrent_proposal(command, identity, principal)

    def transition(
        self,
        alert_id: str,
        command: AlertLifecycleCommandV1,
        *,
        principal: Principal,
        request_id: str | None,
    ) -> AlertAggregateV2:
        self._require_enabled()
        if command.actor_id != principal.actor_id:
            raise AlertPolicyError("command actor must match authenticated principal")
        if command.action in {"accept", "reject", "request_information"}:
            raise AlertPolicyError("review outcomes must use the append-only review route")
        now = datetime.now(UTC)
        try:
            with self.session.begin():
                row = self._alert(alert_id, principal)
                aggregate = _aggregate(row)
                command_digest = digest(command)
                command_delivery_key = digest(
                    {
                        "contract": "hcam.p4-3.lifecycle-command-idempotency.v1",
                        "department": aggregate.department,
                        "command_id": command.command_id,
                    }
                )
                receipt = self.session.scalar(
                    select(AlertCommandReceipt).where(
                        AlertCommandReceipt.department == aggregate.department,
                        AlertCommandReceipt.delivery_key == command_delivery_key,
                    )
                )
                if receipt is not None:
                    if (
                        receipt.alert_id != alert_id
                        or receipt.occurrence_digest != command_digest
                    ):
                        raise AlertConflictError(
                            "lifecycle command identity has different material"
                        )
                    revision = self.session.scalar(
                        select(AlertRevision).where(
                            AlertRevision.alert_id == alert_id,
                            AlertRevision.revision == command.expected_version + 1,
                        )
                    )
                    if revision is None:
                        raise AlertConflictError(
                            "lifecycle command receipt has no immutable result"
                        )
                    return AlertAggregateV2.model_validate(revision.snapshot)
                if command.expected_version != aggregate.version:
                    raise AlertPreconditionError("alert version does not match")
                if command.action == "assign":
                    if command.assignee_id is None:
                        raise AlertPreconditionError("assignment requires an assignee")
                    updated = aggregate.model_copy(
                        update={
                            "version": aggregate.version + 1,
                            "assigned_to": command.assignee_id,
                            "updated_at": now,
                        }
                    )
                    event = self._same_state_event(aggregate, command, now)
                    self.session.add(
                        AlertAssignmentEvent(
                            assignment_id=stable_id("aasn", alert_id, updated.version),
                            alert_id=alert_id,
                            department=aggregate.department,
                            assignee_id=command.assignee_id,
                            actor_id=principal.actor_id,
                            reason=bounded_reason(command.reason),
                            generated_only=True,
                            recorded_at=now,
                        )
                    )
                else:
                    if command.action == "merge":
                        self._validate_merge(aggregate, command.target_alert_id, principal)
                    try:
                        updated, event = apply_transition(aggregate, command, now=now)
                    except AlertTransitionDenied as exc:
                        raise AlertConflictError(str(exc)) from exc
                    if command.action == "suppress":
                        self.session.add(
                            AlertSuppressionEvent(
                                suppression_id=stable_id("asup", alert_id, updated.version),
                                alert_id=alert_id,
                                department=aggregate.department,
                                reason_code=updated.suppression_code,
                                collapse_key=None,
                                represented_alerts=1,
                                suppressed_alerts=1,
                                generated_only=True,
                                recorded_at=now,
                            )
                        )
                    elif command.action == "merge":
                        self.session.add(
                            AlertMergeRelation(
                                relation_id=stable_id("amrg", alert_id, command.target_alert_id),
                                source_alert_id=alert_id,
                                target_alert_id=command.target_alert_id,
                                department=aggregate.department,
                                actor_id=principal.actor_id,
                                reason=bounded_reason(command.reason),
                                generated_only=True,
                                recorded_at=now,
                            )
                        )
                self._apply(row, updated)
                self._append_event(event)
                self._append_legacy_revision(
                    row,
                    previous_state=aggregate.state,
                    actor_id=principal.actor_id,
                    reason=command.reason,
                    now=now,
                )
                self.session.add(
                    AlertCommandReceipt(
                        receipt_id=stable_id(
                            "acpt", aggregate.department, command_delivery_key
                        ),
                        department=aggregate.department,
                        delivery_key=command_delivery_key,
                        semantic_key=aggregate.semantic_key,
                        occurrence_digest=command_digest,
                        alert_id=alert_id,
                        disposition="accepted",
                        generated_only=True,
                        recorded_at=now,
                    )
                )
                self._audit(principal, f"intelligence.alert.p43.{command.action}", alert_id, command.reason, request_id)
                self._outbox(row, "hcam.intelligence.alert.lifecycle.v2", now)
            return updated
        except StaleDataError as exc:
            raise AlertPreconditionError("generated alert changed concurrently") from exc
        except IntegrityError as exc:
            raise AlertConflictError("lifecycle command identity conflicts") from exc

    def review(
        self,
        alert_id: str,
        decision: AlertReviewDecisionV1,
        *,
        expected_version: int,
        principal: Principal,
        request_id: str | None,
    ) -> tuple[AlertAggregateV2, str]:
        self._require_enabled()
        if decision.alert_id != alert_id or decision.reviewer_id != principal.actor_id:
            raise AlertPolicyError("review identity does not match request")
        if decision.reviewer_role not in principal.roles:
            raise AlertPolicyError("review role is not held by principal")
        now = datetime.now(UTC)
        with self.session.begin():
            row = self._alert(alert_id, principal)
            aggregate = _aggregate(row)
            prior_decision = self.session.get(AlertReviewDecision, decision.decision_id)
            if prior_decision is not None:
                if self._decision_contract(prior_decision) != decision:
                    raise AlertConflictError(
                        "review decision identity has different material"
                    )
                policy_row = self.session.get(
                    AlertReviewQuorumPolicy, prior_decision.policy_id
                )
                if policy_row is None:
                    raise AlertConflictError("review decision has no policy")
                decisions = self.session.scalars(
                    select(AlertReviewDecision)
                    .where(AlertReviewDecision.alert_id == alert_id)
                    .order_by(AlertReviewDecision.recorded_at)
                ).all()
                quorum = ReviewQuorum(
                    policy=self._policy_contract(policy_row),
                    decisions=[self._decision_contract(item) for item in decisions],
                )
                return aggregate, quorum.outcome
            if expected_version != aggregate.version:
                raise AlertPreconditionError("review If-Match does not match alert version")
            policy_row = self.session.get(AlertReviewQuorumPolicy, decision.policy_id)
            if policy_row is None or policy_row.department != aggregate.department:
                raise AlertPolicyError("review policy was not found")
            policy = self._policy_contract(policy_row)
            existing_rows = self.session.scalars(
                select(AlertReviewDecision)
                .where(AlertReviewDecision.alert_id == alert_id)
                .order_by(AlertReviewDecision.recorded_at)
            ).all()
            quorum = ReviewQuorum(
                policy=policy,
                decisions=[self._decision_contract(item) for item in existing_rows],
            )
            try:
                quorum.add(decision, now=now)
            except ValueError as exc:
                raise AlertPolicyError(str(exc)) from exc
            self.session.add(
                AlertReviewDecision(
                    decision_id=decision.decision_id,
                    alert_id=alert_id,
                    policy_id=decision.policy_id,
                    department=decision.department,
                    policy_version=decision.policy_version,
                    reviewer_id=decision.reviewer_id,
                    reviewer_role=decision.reviewer_role,
                    decision=decision.decision,
                    evidence_digest=decision.evidence_digest,
                    reason=bounded_reason(decision.reason),
                    supersedes_decision_id=decision.supersedes_decision_id,
                    generated_only=True,
                    operational=False,
                    recorded_at=decision.recorded_at,
                )
            )
            updated = aggregate
            action = None
            if quorum.outcome == "approved":
                action = "accept"
            elif quorum.outcome == "rejected":
                action = "reject"
            elif decision.decision == "request_information":
                action = "request_information"
            if action is not None:
                command = AlertLifecycleCommandV1(
                    command_id=stable_id("arvw", decision.decision_id),
                    action=action,
                    expected_version=aggregate.version,
                    actor_id=principal.actor_id,
                    reason=decision.reason,
                    evidence_digest=decision.evidence_digest,
                )
                try:
                    updated, event = apply_transition(aggregate, command, now=now)
                except AlertTransitionDenied as exc:
                    raise AlertConflictError(str(exc)) from exc
                self._apply(row, updated)
                self._append_event(event)
                self._append_legacy_revision(
                    row,
                    previous_state=aggregate.state,
                    actor_id=principal.actor_id,
                    reason=decision.reason,
                    now=now,
                )
                self._outbox(row, "hcam.intelligence.alert.reviewed.v2", now)
            self._audit(principal, "intelligence.alert.p43.review", alert_id, decision.reason, request_id)
        return updated, quorum.outcome

    def get(self, alert_id: str, principal: Principal) -> AlertAggregateV2:
        return _aggregate(self._alert(alert_id, principal))

    def list(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[AlertAggregateV2], int]:
        limit = bounded_page_size(limit)
        apply_department_scope(self.session, principal)
        statement = _scoped(select(Alert), Alert, principal).where(
            Alert.source_evaluation_id.is_not(None)
        )
        total = int(
            self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
        rows = self.session.scalars(
            statement.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return [_aggregate(row) for row in rows], total

    def list_lifecycle(
        self, alert_id: str, principal: Principal, *, limit: int, offset: int
    ) -> tuple[list[AlertLifecycleEventV2], int]:
        self._alert(alert_id, principal)
        limit = bounded_page_size(limit)
        statement = _scoped(
            select(AlertLifecycleRecord).where(AlertLifecycleRecord.alert_id == alert_id),
            AlertLifecycleRecord,
            principal,
        )
        total = int(self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        rows = self.session.scalars(
            statement.order_by(AlertLifecycleRecord.sequence).limit(limit).offset(offset)
        ).all()
        return [
            AlertLifecycleEventV2(
                event_id=row.event_id,
                alert_id=row.alert_id,
                sequence=row.sequence,
                department=row.department,
                previous_state=row.previous_state,
                new_state=row.new_state,
                action=row.action,
                actor_id=row.actor_id,
                reason=row.reason,
                evidence_digest=row.evidence_digest,
                recorded_at=row.recorded_at,
            )
            for row in rows
        ], total

    def get_review_policy(
        self, alert_id: str, principal: Principal
    ) -> ReviewQuorumPolicyV1:
        aggregate = self.get(alert_id, principal)
        policy_id = stable_id(
            "aqpl", aggregate.alert_id, aggregate.source_evaluation_digest
        )
        row = self.session.get(AlertReviewQuorumPolicy, policy_id)
        if row is None or row.department != aggregate.department:
            raise AlertNotFoundError("generated review policy was not found")
        return self._policy_contract(row)

    def schedule_timer(
        self,
        alert_id: str,
        timer_kind: str,
        *,
        due_at: datetime,
        principal: Principal,
    ) -> AlertTimerIntentV1:
        self._require_enabled()
        row = self._alert(alert_id, principal)
        aggregate = _aggregate(row)
        payload_digest = digest(
            {
                "alert_id": alert_id,
                "kind": timer_kind,
                "due_at": due_at.isoformat(),
                "expected_version": aggregate.version,
            }
        )
        contract = AlertTimerIntentV1(
            timer_id=stable_id("atmr", alert_id, timer_kind, due_at.isoformat()),
            alert_id=alert_id,
            department=aggregate.department,
            timer_kind=timer_kind,
            due_at=due_at,
            state="pending",
            expected_alert_version=aggregate.version,
            payload_digest=payload_digest,
        )
        self.session.add(
            AlertTimerIntent(
                **contract.model_dump(mode="python", exclude={"contract_type"}),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def claim_due_timers(
        self, *, worker_id: str, now: datetime, limit: int, worker_count: int = 1
    ) -> Sequence[AlertTimerIntent]:
        self._require_enabled()
        if (
            worker_count != 1
            and self.session.bind is not None
            and self.session.bind.dialect.name == "sqlite"
        ):
            raise AlertPolicyError("SQLite permits exactly one timer worker")
        limit = min(bounded_page_size(limit), 100)
        statement = (
            select(AlertTimerIntent)
            .where(
                AlertTimerIntent.state.in_(["pending", "leased"]),
                AlertTimerIntent.due_at <= now,
                AlertTimerIntent.attempt_count < 3,
                or_(AlertTimerIntent.lease_until.is_(None), AlertTimerIntent.lease_until <= now),
            )
            .order_by(AlertTimerIntent.due_at, AlertTimerIntent.timer_id)
            .limit(limit)
        )
        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        rows = self.session.scalars(statement).all()
        for row in rows:
            row.state = "leased"
            row.attempt_count += 1
            row.lease_owner = worker_id
            row.lease_until = now + timedelta(seconds=90)
            row.updated_at = now
        self.session.flush()
        return rows

    def resolve_claimed_timer(
        self,
        timer_id: str,
        *,
        worker_id: str,
        alert_version: int,
        now: datetime,
        succeeded: bool,
        retryable: bool = False,
    ) -> AlertTimerIntent:
        self._require_enabled()
        row = self.session.get(AlertTimerIntent, timer_id)
        if row is None:
            raise AlertNotFoundError("generated timer was not found")
        if row.state != "leased" or row.lease_owner != worker_id:
            raise AlertConflictError("generated timer lease is not held by worker")
        if row.expected_alert_version != alert_version:
            row.state = "cancelled"
        elif succeeded:
            row.state = "completed"
        elif retryable and row.attempt_count < 3:
            row.state = "pending"
        else:
            row.state = "failed"
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = now
        self.session.flush()
        return row

    def _alert(self, alert_id: str, principal: Principal) -> Alert:
        apply_department_scope(self.session, principal)
        row = self.session.scalar(
            _scoped(
                select(Alert).where(
                    Alert.alert_id == alert_id,
                    Alert.source_evaluation_id.is_not(None),
                ),
                Alert,
                principal,
            )
        )
        if row is None:
            raise AlertNotFoundError("generated alert was not found")
        return row

    def _recover_concurrent_proposal(
        self,
        command: ProposedAlertCommandV1,
        identity: AlertIdentityV1,
        principal: Principal,
    ) -> tuple[AlertAggregateV2, bool]:
        with self.session.begin():
            apply_department_scope(self.session, principal)
            row = self.session.scalar(
                select(Alert).where(
                    Alert.department == command.department,
                    Alert.semantic_key == identity.semantic_key,
                )
            )
            if row is None or row.source_evaluation_digest != command.evaluation_digest:
                raise AlertConflictError("generated alert identity conflicts")
            receipt = self.session.scalar(
                select(AlertCommandReceipt).where(
                    AlertCommandReceipt.department == command.department,
                    AlertCommandReceipt.delivery_key == identity.delivery_key,
                )
            )
            if receipt is not None:
                if (
                    receipt.alert_id != row.alert_id
                    or receipt.semantic_key != identity.semantic_key
                    or receipt.occurrence_digest != identity.occurrence_digest
                ):
                    raise AlertConflictError("generated delivery identity conflicts")
            else:
                self.session.add(
                    AlertCommandReceipt(
                        receipt_id=stable_id(
                            "acpt", command.department, identity.delivery_key
                        ),
                        department=command.department,
                        delivery_key=identity.delivery_key,
                        semantic_key=identity.semantic_key,
                        occurrence_digest=identity.occurrence_digest,
                        alert_id=row.alert_id,
                        disposition="duplicate",
                        generated_only=True,
                        recorded_at=datetime.now(UTC),
                    )
                )
        return _aggregate(row), True

    def _ensure_default_quorum(self, aggregate: AlertAggregateV2, now: datetime) -> None:
        if aggregate.authority_class != "mandatory_review":
            return
        policy_id = stable_id("aqpl", aggregate.alert_id, aggregate.source_evaluation_digest)
        high_impact = aggregate.severity == "critical" and aggregate.priority == "immediate"
        self.session.add(
            AlertReviewQuorumPolicy(
                policy_id=policy_id,
                department=aggregate.department,
                policy_key=(
                    f"generated-high-impact-review.{aggregate.alert_id}"
                    if high_impact
                    else f"ordinary-review.{aggregate.alert_id}"
                ),
                policy_version=1,
                workflow_class="generated_high_impact" if high_impact else "ordinary",
                required_distinct_reviewers=(
                    self.high_impact_quorum if high_impact else 1
                ),
                permitted_roles=["intelligence.reviewer", "intelligence.approver", "platform.admin"],
                evidence_digest=aggregate.source_evaluation_digest,
                effective_at=now,
                expires_at=None,
                generated_only=True,
            )
        )

    def _policy_contract(self, row: AlertReviewQuorumPolicy) -> ReviewQuorumPolicyV1:
        return ReviewQuorumPolicyV1(
            policy_id=row.policy_id,
            policy_version=row.policy_version,
            department=row.department,
            workflow_class=row.workflow_class,
            required_distinct_reviewers=row.required_distinct_reviewers,
            permitted_roles=row.permitted_roles,
            evidence_digest=row.evidence_digest,
            effective_at=row.effective_at,
            expires_at=row.expires_at,
        )

    def _decision_contract(self, row: AlertReviewDecision) -> AlertReviewDecisionV1:
        return AlertReviewDecisionV1(
            decision_id=row.decision_id,
            alert_id=row.alert_id,
            department=row.department,
            policy_id=row.policy_id,
            policy_version=row.policy_version,
            reviewer_id=row.reviewer_id,
            reviewer_role=row.reviewer_role,
            decision=row.decision,
            evidence_digest=row.evidence_digest,
            reason=row.reason,
            supersedes_decision_id=row.supersedes_decision_id,
            recorded_at=row.recorded_at,
        )

    def _validate_merge(
        self, aggregate: AlertAggregateV2, target_id: str | None, principal: Principal
    ) -> None:
        if target_id is None or target_id == aggregate.alert_id:
            raise AlertConflictError("merge target is invalid")
        target = self._alert(target_id, principal)
        if target.department != aggregate.department:
            raise AlertNotFoundError("merge target was not found")
        seen = {aggregate.alert_id}
        current = target
        for _ in range(32):
            if current.alert_id in seen:
                raise AlertConflictError("alert merge cycle is not allowed")
            seen.add(current.alert_id)
            if current.merged_into is None:
                return
            next_row = self.session.get(Alert, current.merged_into)
            if next_row is None or next_row.department != aggregate.department:
                raise AlertConflictError("merge chain is invalid")
            current = next_row
        raise AlertConflictError("alert merge chain exceeds the bound")

    def _same_state_event(
        self,
        aggregate: AlertAggregateV2,
        command: AlertLifecycleCommandV1,
        now: datetime,
    ) -> AlertLifecycleEventV2:
        return AlertLifecycleEventV2(
            event_id=stable_id("alfe", aggregate.alert_id, aggregate.version + 1, command.command_id),
            alert_id=aggregate.alert_id,
            sequence=aggregate.version + 1,
            department=aggregate.department,
            previous_state=aggregate.state,
            new_state=aggregate.state,
            action=command.action,
            actor_id=command.actor_id,
            reason=bounded_reason(command.reason),
            evidence_digest=command.evidence_digest,
            recorded_at=now,
        )

    def _apply(self, row: Alert, aggregate: AlertAggregateV2) -> None:
        row.version_id = aggregate.version
        row.state = aggregate.state
        row.disposition = aggregate.disposition
        row.assigned_to = aggregate.assigned_to
        row.suppression_code = aggregate.suppression_code
        row.merged_into = aggregate.merged_into
        row.payload = aggregate.model_dump(mode="json")
        row.content_digest = digest(aggregate)
        row.updated_at = aggregate.updated_at

    def _append_event(self, event: AlertLifecycleEventV2) -> None:
        self.session.add(
            AlertLifecycleRecord(
                event_id=event.event_id,
                alert_id=event.alert_id,
                sequence=event.sequence,
                department=event.department,
                previous_state=event.previous_state,
                new_state=event.new_state,
                action=event.action,
                actor_id=event.actor_id,
                reason=event.reason,
                evidence_digest=event.evidence_digest,
                generated_only=True,
                operational=False,
                recorded_at=event.recorded_at,
            )
        )

    def _append_legacy_revision(
        self,
        row: Alert,
        *,
        previous_state: str,
        actor_id: str,
        reason: str,
        now: datetime,
    ) -> None:
        self.session.add(
            AlertRevision(
                revision_id=stable_id("alrv", row.alert_id, row.version_id),
                alert_id=row.alert_id,
                department=row.department,
                revision=row.version_id,
                previous_state=previous_state,
                new_state=row.state,
                actor_id=actor_id,
                reason=reason,
                snapshot=row.payload,
                content_digest=row.content_digest,
                recorded_at=now,
            )
        )

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise AlertDisabledError("P4.3 generated alert lifecycle is disabled")

    def _audit(
        self,
        principal: Principal,
        action: str,
        target_id: str,
        reason: str,
        request_id: str | None,
    ) -> None:
        AuditRepository(self.session).record(
            actor_id=principal.actor_id,
            action=action,
            target_type="intelligence_alert",
            target_id=target_id,
            source="hcam.api",
            reason=reason,
            outcome="success",
            context={"generated_only": True, "operational": False},
            request_id=request_id,
        )

    def _outbox(self, row: Alert, event_type: str, now: datetime) -> None:
        rule = self.session.scalar(
            select(IntelligenceRule).where(
                IntelligenceRule.rule_record_id
                == self.session.scalar(
                    select(IntelligenceRuleEvaluationRevision.rule_record_id).where(
                        IntelligenceRuleEvaluationRevision.evaluation_id
                        == row.source_evaluation_id,
                        IntelligenceRuleEvaluationRevision.revision
                        == row.source_evaluation_revision,
                    )
                )
            )
        )
        if rule is None:
            raise AlertPolicyError("alert source rule was not found")
        self.session.add(
            StreamEventOutbox(
                event_id=stable_id("evt", row.alert_id, row.version_id, event_type),
                event_type=event_type,
                schema_version=2,
                stream_id=rule.stream_id,
                camera_id=rule.camera_id,
                occurred_at=now,
                payload={
                    "alert_id": row.alert_id,
                    "version": row.version_id,
                    "state": row.state,
                    "department": row.department,
                    "domain": row.domain,
                    "authority_class": row.authority_class,
                    "generated_only": True,
                    "operational": False,
                },
            )
        )
