from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera
from hcam.intelligence.models import (
    IntelligenceRule,
    IntelligenceRuleCompilation,
    IntelligenceRuleEvaluationRevision,
    IntelligenceRuleLifecycleEvent,
    IntelligenceRuleSchedule,
    IntelligenceRuleScopeMember,
    IntelligenceRuleShadowComparison,
)
from hcam.intelligence.row_security import apply_department_scope
from hcam.intelligence.rules.canonical import canonical_rule_bytes, rule_sha256
from hcam.intelligence.rules.compiler import CompiledRule, compile_rule
from hcam.intelligence.rules.contracts import RuleEvaluationV1, VisualRuleDocumentV1
from hcam.intelligence.rules.lifecycle import validate_transition
from hcam.security.auth import Principal
from hcam.streams.models import StreamEndpoint, StreamEventOutbox


class RuleControlError(RuntimeError):
    pass


class RuleNotFoundError(RuleControlError):
    pass


class RuleConflictError(RuleControlError):
    pass


class RulePreconditionError(RuleControlError):
    pass


class RuleControlDisabledError(RuleControlError):
    pass


def stable_id(prefix: str, *parts: object) -> str:
    material = "\x00".join(str(item) for item in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:32]}"


def safe_reason(value: str) -> str:
    if value.strip() != value or not 8 <= len(value) <= 1_000:
        raise RuleControlError("reason must be trimmed and 8 to 1000 characters")
    return value


def p42_rule_response(row: IntelligenceRule) -> dict[str, object]:
    document = VisualRuleDocumentV1.model_validate(row.definition)
    return {
        "contract_type": "hcam.p4-2.intelligence-rule-response.v1",
        "rule_record_id": row.rule_record_id,
        "record_version": row.version_id,
        "rule_id": row.rule_id,
        "rule_key": row.rule_key,
        "version": row.rule_version,
        "department": row.department,
        "status": row.status,
        "authority_class": row.authority_class,
        "operational": False,
        "generated_only": True,
        "authoring_digest": row.authoring_digest,
        "semantic_digest": row.semantic_digest,
        "compilation_id": row.compilation_id,
        "schedule_digest": row.schedule_digest,
        "document": document.model_dump(mode="json"),
        "runtime_state": "generated_evidence_only",
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def compilation_response(row: IntelligenceRuleCompilation) -> dict[str, object]:
    return {
        "compilation_id": row.compilation_id,
        "department": row.department,
        "rule_key": row.rule_key,
        "rule_version": row.rule_version,
        "authoring_digest": row.authoring_digest,
        "semantic_digest": row.semantic_digest,
        "ast_digest": row.ast_digest,
        "schedule_digest": row.schedule_digest,
        "canonical_ast": row.canonical_ast,
        "cel_compilations": row.cel_compilations,
        "diagnostic_map": row.diagnostic_map,
        "status": row.status,
        "generated_only": True,
        "operational": False,
    }


class RuleControlService:
    def __init__(self, session: Session, *, enabled: bool) -> None:
        self.session = session
        self.enabled = enabled

    def preview(self, document: VisualRuleDocumentV1) -> CompiledRule:
        self._require_enabled()
        return compile_rule(document)

    def create(
        self,
        document: VisualRuleDocumentV1,
        scope_stream_ids: list[str],
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> IntelligenceRule:
        self._require_enabled()
        reason = safe_reason(reason)
        if not principal.can_access_department(document.department):
            raise RuleNotFoundError("generated rule scope was not found")
        compiled = compile_rule(document)
        now = datetime.now(UTC)
        rule_id = stable_id("irule", document.department, document.rule_key)
        record_id = stable_id("irlr", rule_id, document.version)
        try:
            with self.session.begin():
                apply_department_scope(self.session, principal)
                endpoints = self.session.scalars(
                    select(StreamEndpoint).where(
                        StreamEndpoint.stream_id.in_(scope_stream_ids)
                    )
                ).all()
                if len(endpoints) != len(set(scope_stream_ids)):
                    raise RuleNotFoundError("generated rule scope was not found")
                cameras = {
                    camera.camera_id: camera
                    for camera in self.session.scalars(
                        select(Camera).where(
                            Camera.camera_id.in_([item.camera_id for item in endpoints])
                        )
                    ).all()
                }
                if any(
                    endpoint.camera_id not in cameras
                    or cameras[endpoint.camera_id].department != document.department
                    for endpoint in endpoints
                ):
                    raise RuleNotFoundError("generated rule scope was not found")
                primary = sorted(endpoints, key=lambda item: item.stream_id)[0]
                row = IntelligenceRule(
                    rule_record_id=record_id,
                    department=document.department,
                    stream_id=primary.stream_id,
                    camera_id=primary.camera_id,
                    rule_id=rule_id,
                    rule_key=document.rule_key,
                    rule_version=document.version,
                    status="draft",
                    authority_class="mandatory_review",
                    operational=False,
                    generated_only=True,
                    definition=document.model_dump(mode="json"),
                    canonical_json=canonical_rule_bytes(document).decode("ascii"),
                    configuration_digest=compiled.compilation.semantic_digest,
                    static_cost=compiled.compilation.canonical_ast.static_cost,
                    intended_use="Generated-only Phase 4.2 rule evaluation evidence",
                    policy_version=rule_sha256(
                        {"policy": "hcam.p4-2.mandatory-review.v1"}
                    ),
                    retention_class="derived.intelligence.standard",
                    owner_id=principal.actor_id,
                    last_change_reason=reason,
                    created_at=now,
                    updated_at=now,
                    authoring_digest=compiled.compilation.authoring_digest,
                    semantic_digest=compiled.compilation.semantic_digest,
                    compilation_id=compiled.compilation.compilation_id,
                    schedule_digest=compiled.compilation.schedule_digest,
                )
                self.session.add(row)
                self.session.flush()
                self._store_compilation(record_id, compiled, now)
                for endpoint in endpoints:
                    self.session.add(
                        IntelligenceRuleScopeMember(
                            scope_member_id=stable_id(
                                "rsco", record_id, endpoint.stream_id
                            ),
                            rule_record_id=record_id,
                            department=document.department,
                            stream_id=endpoint.stream_id,
                            camera_id=endpoint.camera_id,
                            created_at=now,
                        )
                    )
                if document.schedule is not None:
                    self.session.add(
                        IntelligenceRuleSchedule(
                            schedule_record_id=stable_id("rsch", record_id),
                            rule_record_id=record_id,
                            department=document.department,
                            schedule_digest=compiled.compilation.schedule_digest,
                            definition=document.schedule.model_dump(mode="json"),
                            created_at=now,
                        )
                    )
                self._audit(
                    principal,
                    "intelligence.rule.p42.create",
                    record_id,
                    reason,
                    request_id,
                )
                self._outbox(row, now)
            return row
        except IntegrityError as exc:
            raise RuleConflictError("generated rule version already exists") from exc

    def transition(
        self,
        record_id: str,
        target: str,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> IntelligenceRule:
        self._require_enabled()
        reason = safe_reason(reason)
        now = datetime.now(UTC)
        try:
            with self.session.begin():
                row = self._scoped_rule(record_id, principal)
                if row is None or row.authoring_digest is None:
                    raise RuleNotFoundError("generated rule was not found")
                if row.version_id != expected_version:
                    raise RulePreconditionError("generated rule version does not match")
                try:
                    validate_transition(
                        row.status,
                        target,
                        has_compilation=row.compilation_id is not None,
                    )
                except ValueError as exc:
                    raise RuleConflictError(
                        "generated rule lifecycle transition is not allowed"
                    ) from exc
                previous = row.status
                row.status = target
                row.version_id += 1
                row.last_change_reason = reason
                row.updated_at = now
                self.session.add(
                    IntelligenceRuleLifecycleEvent(
                        event_id=f"rlfe_{uuid4().hex}",
                        rule_record_id=row.rule_record_id,
                        department=row.department,
                        from_status=previous,
                        to_status=target,
                        actor_id=principal.actor_id,
                        reason_code="owner_reviewed_transition",
                        compilation_digest=row.semantic_digest,
                        occurred_at=now,
                    )
                )
                self.session.flush()
                self._audit(
                    principal,
                    f"intelligence.rule.p42.{target}",
                    record_id,
                    reason,
                    request_id,
                )
                self._outbox(row, now)
            return row
        except StaleDataError as exc:
            raise RulePreconditionError("generated rule changed concurrently") from exc

    def get_rule(self, record_id: str, principal: Principal) -> IntelligenceRule | None:
        return self._scoped_rule(record_id, principal)

    def list_versions(
        self, record_id: str, principal: Principal
    ) -> Sequence[IntelligenceRule]:
        row = self._scoped_rule(record_id, principal)
        if row is None:
            raise RuleNotFoundError("generated rule was not found")
        statement = select(IntelligenceRule).where(
            IntelligenceRule.department == row.department,
            IntelligenceRule.rule_key == row.rule_key,
            IntelligenceRule.authoring_digest.is_not(None),
        )
        if principal.allowed_departments is not None:
            statement = statement.where(
                IntelligenceRule.department.in_(sorted(principal.allowed_departments))
            )
        return self.session.scalars(
            statement.order_by(IntelligenceRule.rule_version)
        ).all()

    def get_compilation(
        self, compilation_id: str, principal: Principal
    ) -> IntelligenceRuleCompilation | None:
        apply_department_scope(self.session, principal)
        statement = select(IntelligenceRuleCompilation).where(
            IntelligenceRuleCompilation.compilation_id == compilation_id
        )
        if principal.allowed_departments is not None:
            statement = statement.where(
                IntelligenceRuleCompilation.department.in_(
                    sorted(principal.allowed_departments)
                )
            )
        return self.session.scalar(statement)

    def list_evaluations(
        self, record_id: str, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[IntelligenceRuleEvaluationRevision], int]:
        return self._list_child(
            IntelligenceRuleEvaluationRevision,
            record_id,
            principal,
            limit=limit,
            offset=offset,
        )

    def list_shadow_comparisons(
        self, record_id: str, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[IntelligenceRuleShadowComparison], int]:
        return self._list_child(
            IntelligenceRuleShadowComparison,
            record_id,
            principal,
            limit=limit,
            offset=offset,
        )

    def store_evaluation(
        self,
        rule_record_id: str,
        evaluation: RuleEvaluationV1,
        *,
        recorded_at: datetime,
    ) -> IntelligenceRuleEvaluationRevision:
        row = IntelligenceRuleEvaluationRevision(
            revision_id=stable_id(
                "rrev", evaluation.evaluation_id, evaluation.revision
            ),
            evaluation_id=evaluation.evaluation_id,
            rule_record_id=rule_record_id,
            compilation_id=evaluation.compilation_id,
            department=evaluation.department,
            partition_digest=evaluation.partition_digest,
            revision=evaluation.revision,
            state=evaluation.state,
            reason_code=evaluation.reason_code,
            snapshot=evaluation.model_dump(mode="json"),
            snapshot_digest=evaluation.evaluation_digest,
            idempotency_key=rule_sha256(
                {
                    "evaluation_id": evaluation.evaluation_id,
                    "revision": evaluation.revision,
                    "digest": evaluation.evaluation_digest,
                }
            ),
            recorded_at=recorded_at,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def _store_compilation(
        self, record_id: str, compiled: CompiledRule, now: datetime
    ) -> None:
        item = compiled.compilation
        self.session.add(
            IntelligenceRuleCompilation(
                compilation_id=item.compilation_id,
                rule_record_id=record_id,
                department=item.department,
                rule_key=item.rule_key,
                rule_version=item.rule_version,
                status="compiled",
                authoring_digest=item.authoring_digest,
                semantic_digest=item.semantic_digest,
                ast_digest=item.ast_digest,
                schedule_digest=item.schedule_digest,
                canonical_ast=item.canonical_ast.model_dump(mode="json"),
                canonical_bytes=compiled.canonical_bytes.decode("ascii"),
                cel_compilations=[
                    value.model_dump(mode="json") for value in item.cel_compilations
                ],
                diagnostic_map=item.diagnostic_map,
                static_cost=item.canonical_ast.static_cost,
                created_at=now,
            )
        )

    def _scoped_rule(
        self, record_id: str, principal: Principal
    ) -> IntelligenceRule | None:
        apply_department_scope(self.session, principal)
        statement = select(IntelligenceRule).where(
            IntelligenceRule.rule_record_id == record_id
        )
        if principal.allowed_departments is not None:
            statement = statement.where(
                IntelligenceRule.department.in_(sorted(principal.allowed_departments))
            )
        return self.session.scalar(statement)

    def _list_child(
        self, model, record_id: str, principal: Principal, *, limit: int, offset: int
    ):
        if self._scoped_rule(record_id, principal) is None:
            raise RuleNotFoundError("generated rule was not found")
        statement = select(model).where(model.rule_record_id == record_id)
        if principal.allowed_departments is not None:
            statement = statement.where(
                model.department.in_(sorted(principal.allowed_departments))
            )
        total = int(
            self.session.scalar(select(func.count()).select_from(statement.subquery()))
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(
                model.created_at.desc()
                if hasattr(model, "created_at")
                else model.recorded_at.desc()
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return rows, total

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise RuleControlDisabledError(
                "P4.2 generated rule control plane is disabled"
            )

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
            target_type="intelligence_rule",
            target_id=target_id,
            source="hcam.api",
            reason=reason,
            outcome="success",
            context={"generated_only": True, "operational": False},
            request_id=request_id,
        )

    def _outbox(self, row: IntelligenceRule, occurred_at: datetime) -> None:
        self.session.add(
            StreamEventOutbox(
                event_id=f"evt_{uuid4().hex}",
                event_type="hcam.intelligence.rule.lifecycle.v2",
                schema_version=2,
                stream_id=row.stream_id,
                camera_id=row.camera_id,
                occurred_at=occurred_at,
                payload={
                    "rule_record_id": row.rule_record_id,
                    "status": row.status,
                    "department": row.department,
                    "authority_class": "mandatory_review",
                    "generated_only": True,
                    "operational": False,
                    "semantic_digest": row.semantic_digest,
                },
            )
        )
