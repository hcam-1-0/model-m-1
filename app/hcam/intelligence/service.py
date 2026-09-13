from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera
from hcam.intelligence.canonical import canonical_json, canonical_sha256
from hcam.intelligence.contracts import IntelligenceRuleV1, ReferenceProviderV1
from hcam.intelligence.guardrails import validate_intelligence_document
from hcam.intelligence.models import IntelligenceRule, ReferenceProvider
from hcam.intelligence.row_security import apply_department_scope
from hcam.intelligence.schemas import IntelligenceRuleCreate, ReferenceProviderCreate
from hcam.security.auth import Principal
from hcam.streams.models import StreamEndpoint, StreamEventOutbox


class IntelligenceNotFoundError(RuntimeError):
    pass


class IntelligenceConflictError(RuntimeError):
    pass


class IntelligencePreconditionError(RuntimeError):
    pass


class IntelligenceDisabledError(RuntimeError):
    pass


class IntelligenceValidationError(RuntimeError):
    pass


def _stable_id(prefix: str, *parts: object) -> str:
    value = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(value).hexdigest()[:32]}"


def _safe_reason(value: str) -> str:
    if value.strip() != value or len(value) < 8 or len(value) > 1000:
        raise IntelligenceValidationError(
            "reason must be trimmed and 8 to 1000 characters"
        )
    return value


def rule_response(row: IntelligenceRule):
    from hcam.intelligence.rules.persistence import p42_rule_response
    from hcam.intelligence.schemas import IntelligenceRuleResponse, P42RuleResponse

    if row.definition.get("contract_type") == "hcam.p4-2.visual-rule-document.v1":
        return P42RuleResponse.model_validate(p42_rule_response(row))

    contract = IntelligenceRuleV1.model_validate(row.definition)
    return IntelligenceRuleResponse(
        **contract.model_dump(),
        rule_record_id=row.rule_record_id,
        record_version=row.version_id,
        stream_id=row.stream_id,
        camera_id=row.camera_id,
    )


def provider_response(row: ReferenceProvider):
    from hcam.intelligence.schemas import ReferenceProviderResponse

    contract = ReferenceProviderV1.model_validate(row.definition)
    return ReferenceProviderResponse(
        **contract.model_dump(), configuration_digest=row.configuration_digest
    )


class IntelligenceControlService:
    def __init__(self, session: Session, *, enabled: bool) -> None:
        self.session = session
        self.enabled = enabled

    def create_rule(
        self,
        stream_id: str,
        payload: IntelligenceRuleCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> IntelligenceRule:
        self._require_enabled()
        safe_reason = _safe_reason(reason)
        now = datetime.now(UTC)
        rule_id = _stable_id(
            "irule", payload.department, payload.rule_key, payload.version
        )
        record_id = _stable_id("irlr", stream_id, rule_id)
        graph_digest = canonical_sha256(payload.graph)
        contract = IntelligenceRuleV1(
            rule_id=rule_id,
            rule_key=payload.rule_key,
            version=payload.version,
            department=payload.department,
            status="draft",
            graph=payload.graph,
            graph_digest=graph_digest,
            static_cost=len(payload.graph.nodes),
            intended_use=payload.intended_use,
            policy_version=payload.policy_version,
            retention_class=payload.retention_class,
            owner_id=principal.actor_id,
            created_at=now,
            updated_at=now,
        )
        validate_intelligence_document(contract)
        configuration_digest = canonical_sha256(
            {
                "graph": payload.graph.model_dump(mode="json"),
                "policy_version": payload.policy_version,
                "retention_class": payload.retention_class,
            }
        )
        row = IntelligenceRule(
            rule_record_id=record_id,
            department=payload.department,
            stream_id=stream_id,
            camera_id="",
            rule_id=rule_id,
            rule_key=payload.rule_key,
            rule_version=payload.version,
            status="draft",
            authority_class="mandatory_review",
            operational=False,
            generated_only=True,
            definition=contract.model_dump(mode="json"),
            canonical_json=canonical_json(contract),
            configuration_digest=configuration_digest,
            static_cost=len(payload.graph.nodes),
            intended_use=payload.intended_use,
            policy_version=payload.policy_version,
            retention_class=payload.retention_class,
            owner_id=principal.actor_id,
            last_change_reason=safe_reason,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.session.begin():
                apply_department_scope(self.session, principal)
                endpoint = self.session.get(StreamEndpoint, stream_id)
                camera = (
                    self.session.get(Camera, endpoint.camera_id)
                    if endpoint is not None
                    else None
                )
                if endpoint is None or camera is None:
                    raise IntelligenceNotFoundError("Stream was not found")
                if (
                    camera.department != payload.department
                    or not principal.can_access_department(camera.department)
                ):
                    raise IntelligenceNotFoundError("Stream was not found")
                row.camera_id = endpoint.camera_id
                self.session.add(row)
                self.session.flush()
                self._audit(
                    principal,
                    action="intelligence.rule.create",
                    target_type="intelligence_rule",
                    target_id=record_id,
                    reason=safe_reason,
                    request_id=request_id,
                )
                self._outbox(row, now)
            return row
        except IntegrityError as exc:
            raise IntelligenceConflictError("Rule version already exists") from exc

    def update_rule_status(
        self,
        record_id: str,
        status: str,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> IntelligenceRule:
        self._require_enabled()
        safe_reason = _safe_reason(reason)
        now = datetime.now(UTC)
        try:
            with self.session.begin():
                apply_department_scope(self.session, principal)
                statement = select(IntelligenceRule).where(
                    IntelligenceRule.rule_record_id == record_id
                )
                if principal.allowed_departments is not None:
                    statement = statement.where(
                        IntelligenceRule.department.in_(
                            sorted(principal.allowed_departments)
                        )
                    )
                row = self.session.scalar(statement)
                if row is None:
                    raise IntelligenceNotFoundError("Rule was not found")
                if row.authoring_digest is not None:
                    raise IntelligenceConflictError(
                        "P4.2 rules require the versioned lifecycle endpoints"
                    )
                if row.version_id != expected_version:
                    raise IntelligencePreconditionError("Rule version does not match")
                allowed = {
                    "draft": {"validated", "retired"},
                    "validated": {"retired"},
                    "retired": set(),
                }
                if status not in allowed[row.status]:
                    raise IntelligenceConflictError(
                        "Rule status transition is not allowed"
                    )
                contract = IntelligenceRuleV1.model_validate(row.definition).model_copy(
                    update={"status": status, "updated_at": now}
                )
                validate_intelligence_document(contract)
                row.status = status
                row.definition = contract.model_dump(mode="json")
                row.canonical_json = canonical_json(contract)
                row.last_change_reason = safe_reason
                row.updated_at = now
                self.session.flush()
                self._audit(
                    principal,
                    action="intelligence.rule.status.update",
                    target_type="intelligence_rule",
                    target_id=record_id,
                    reason=safe_reason,
                    request_id=request_id,
                )
                self._outbox(row, now)
            return row
        except StaleDataError as exc:
            raise IntelligencePreconditionError(
                "Rule version changed concurrently"
            ) from exc

    def create_provider(
        self,
        payload: ReferenceProviderCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> ReferenceProvider:
        self._require_enabled()
        safe_reason = _safe_reason(reason)
        if not principal.can_access_department(payload.department):
            raise IntelligenceNotFoundError("Department was not found")
        now = datetime.now(UTC)
        provider_id = _stable_id("prov", payload.department, payload.provider_key)
        contract = ReferenceProviderV1(
            provider_id=provider_id,
            provider_key=payload.provider_key,
            version=1,
            department=payload.department,
            policy_ref=payload.policy_ref,
            destination_policy_ref=payload.destination_policy_ref,
            allowed_fields=payload.allowed_fields,
            owner_id=principal.actor_id,
            created_at=now,
            updated_at=now,
        )
        validate_intelligence_document(contract)
        digest = canonical_sha256(contract)
        row = ReferenceProvider(
            provider_id=provider_id,
            department=payload.department,
            provider_key=payload.provider_key,
            status="disabled",
            enabled=False,
            provider_kind="generated_fixture",
            transport_state="absent",
            credential_state="none",
            policy_ref=payload.policy_ref,
            destination_policy_ref=payload.destination_policy_ref,
            allowed_fields=payload.allowed_fields,
            definition=contract.model_dump(mode="json"),
            configuration_digest=digest,
            generated_only=True,
            owner_id=principal.actor_id,
            last_change_reason=safe_reason,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.session.begin():
                apply_department_scope(self.session, principal)
                self.session.add(row)
                self.session.flush()
                self._audit(
                    principal,
                    action="intelligence.provider.create_disabled",
                    target_type="reference_provider",
                    target_id=provider_id,
                    reason=safe_reason,
                    request_id=request_id,
                )
            return row
        except IntegrityError as exc:
            raise IntelligenceConflictError("Provider metadata already exists") from exc

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise IntelligenceDisabledError("P4.0 generated control plane is disabled")

    def _audit(
        self,
        principal: Principal,
        *,
        action: str,
        target_type: str,
        target_id: str,
        reason: str,
        request_id: str | None,
    ) -> None:
        AuditRepository(self.session).record(
            actor_id=principal.actor_id,
            action=action,
            target_type=target_type,
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
                event_type="hcam.intelligence.rule.changed.v1",
                schema_version=1,
                stream_id=row.stream_id,
                camera_id=row.camera_id,
                occurred_at=occurred_at,
                payload={
                    "rule_id": row.rule_id,
                    "status": row.status,
                    "department": row.department,
                    "authority_class": "mandatory_review",
                    "generated_only": True,
                    "operational": False,
                    "configuration_digest": row.configuration_digest,
                },
            )
        )
