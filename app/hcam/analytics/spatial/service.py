from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.analytics.geometry import GeometryDefinitionV1
from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsGeometry,
    AnalyticsGeometryRule,
)
from hcam.analytics.service import _safe_reason
from hcam.analytics.spatial.cel_policy import ConstrainedCelEnvironment
from hcam.analytics.spatial.contracts import GeometryRuleV1
from hcam.analytics.spatial.evaluator import CompiledGeometryRule
from hcam.analytics.spatial.geometry_engine import canonicalize_geometry
from hcam.analytics.spatial.schemas import (
    GeometryCreate,
    GeometryListResponse,
    GeometryResponse,
    GeometryRuleCreate,
    GeometryRuleListResponse,
    GeometryRuleResponse,
    RuleCompilePreview,
)
from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.security.auth import Principal
from hcam.streams.models import StreamEndpoint


class SpatialNotFoundError(RuntimeError):
    pass


class SpatialConflictError(RuntimeError):
    pass


class SpatialPreconditionError(RuntimeError):
    pass


class SpatialValidationError(RuntimeError):
    pass


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:32]}"


def _canonical_digest(document: dict[str, object]) -> str:
    payload = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _geometry_definition(row: AnalyticsGeometry) -> GeometryDefinitionV1:
    return GeometryDefinitionV1(
        geometry_id=row.geometry_id,
        version=row.geometry_version,
        department=row.department,
        stream_id=row.stream_id,
        camera_id=row.camera_id,
        status=row.status,
        shape=row.shape,
        schedule=row.schedule,
        intended_use=row.intended_use,
        policy_version=row.policy_version,
        owner_id=row.owner_id,
        approval_record_id=row.approval_record_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def geometry_response(row: AnalyticsGeometry) -> GeometryResponse:
    definition = _geometry_definition(row)
    return GeometryResponse(
        geometry_record_id=row.geometry_record_id,
        record_version=row.record_version,
        geometry_id=row.geometry_id,
        version=row.geometry_version,
        department=row.department,
        stream_id=row.stream_id,
        camera_id=row.camera_id,
        status=row.status,
        shape=definition.shape,
        schedule=definition.schedule,
        intended_use=row.intended_use,
        policy_version=row.policy_version,
        configuration_digest=row.configuration_digest,
        wkb_sha256=row.wkb_sha256,
        shapely_version=row.shapely_version,
        geos_version=row.geos_version,
        owner_id=row.owner_id,
        approval_record_id=row.approval_record_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _rule_definition(row: AnalyticsGeometryRule) -> GeometryRuleV1:
    return GeometryRuleV1.model_validate(row.configuration)


def rule_response(row: AnalyticsGeometryRule) -> GeometryRuleResponse:
    definition = _rule_definition(row)
    document = definition.model_dump(exclude={"contract_type"})
    return GeometryRuleResponse(
        rule_record_id=row.rule_record_id,
        record_version=row.record_version,
        geometry_record_id=row.geometry_record_id,
        **document,
        checked_cel_digest=row.checked_cel_digest,
        static_cost=row.static_cost,
    )


class SpatialControlService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cel = ConstrainedCelEnvironment()

    def create_geometry(
        self,
        stream_id: str,
        payload: GeometryCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsGeometry:
        normalized_reason = _safe_reason(reason)
        record_id = _stable_id("geom", stream_id, payload.geometry_id, payload.version)
        try:
            with self.session.begin():
                endpoint, camera = self._stream_scope(stream_id, principal)
                retained = int(
                    self.session.scalar(
                        select(func.count())
                        .select_from(AnalyticsGeometry)
                        .where(AnalyticsGeometry.stream_id == stream_id)
                    )
                    or 0
                )
                if retained >= 256:
                    raise SpatialConflictError("Geometry version limit reached")
                now = utc_now()
                definition = GeometryDefinitionV1(
                    geometry_id=payload.geometry_id,
                    version=payload.version,
                    department=camera.department,
                    stream_id=stream_id,
                    camera_id=endpoint.camera_id,
                    status="draft",
                    shape=payload.shape,
                    schedule=payload.schedule,
                    intended_use=payload.intended_use,
                    policy_version=payload.policy_version,
                    owner_id=principal.actor_id,
                    created_at=now,
                    updated_at=now,
                )
                canonical = canonicalize_geometry(definition.shape)
                row = AnalyticsGeometry(
                    geometry_record_id=record_id,
                    department=camera.department,
                    stream_id=stream_id,
                    camera_id=endpoint.camera_id,
                    geometry_id=definition.geometry_id,
                    geometry_version=definition.version,
                    status="draft",
                    kind=definition.shape.kind,
                    shape=definition.shape.model_dump(mode="json"),
                    schedule=definition.schedule.model_dump(mode="json"),
                    canonical_json=canonical.canonical_json,
                    canonical_wkb=canonical.canonical_wkb,
                    spatial_geometry=canonical.canonical_wkb,
                    configuration_digest=canonical.digest,
                    wkb_sha256=canonical.wkb_sha256,
                    shapely_version=canonical.shapely_version,
                    geos_version=canonical.geos_version,
                    intended_use=definition.intended_use,
                    policy_version=definition.policy_version,
                    owner_id=principal.actor_id,
                    last_change_reason=normalized_reason,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(row)
                self.session.flush()
                self._audit(
                    principal,
                    action="analytics.geometry.create",
                    target_type="analytics_geometry",
                    target_id=record_id,
                    reason=normalized_reason,
                    request_id=request_id,
                    context={"stream_id": stream_id, "status": "draft"},
                )
            return row
        except IntegrityError as exc:
            raise SpatialConflictError("Geometry version already exists") from exc

    def approve_geometry(
        self,
        record_id: str,
        approval_record_id: str,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsGeometry:
        normalized_reason = _safe_reason(reason)
        try:
            with self.session.begin():
                row = self._geometry(record_id, principal)
                if row.record_version != expected_version:
                    raise SpatialPreconditionError("Geometry version ETag does not match")
                if row.status != "draft":
                    raise SpatialConflictError("Only draft geometry can be approved")
                row.status = "approved"
                row.approval_record_id = approval_record_id
                row.owner_id = principal.actor_id
                row.last_change_reason = normalized_reason
                row.updated_at = utc_now()
                self.session.flush()
                _geometry_definition(row)
                self._audit(
                    principal,
                    action="analytics.geometry.approve",
                    target_type="analytics_geometry",
                    target_id=record_id,
                    reason=normalized_reason,
                    request_id=request_id,
                    context={"stream_id": row.stream_id, "status": "approved"},
                )
            return row
        except StaleDataError as exc:
            raise SpatialPreconditionError("Geometry version changed concurrently") from exc

    def compile_rule(
        self,
        geometry_record_id: str,
        payload: GeometryRuleCreate,
        *,
        principal: Principal,
        now: datetime | None = None,
    ) -> tuple[GeometryRuleV1, AnalyticsGeometry, RuleCompilePreview, bytes]:
        geometry = self._geometry(geometry_record_id, principal)
        if geometry.status != "approved":
            raise SpatialConflictError("Rule compilation requires approved geometry")
        assignment = self.session.get(AnalyticsAssignment, payload.assignment_id)
        if (
            assignment is None
            or assignment.department != geometry.department
            or assignment.stream_id != geometry.stream_id
            or assignment.camera_id != geometry.camera_id
        ):
            raise SpatialNotFoundError("Analytics assignment not found")
        timestamp = now or utc_now()
        values = payload.model_dump(mode="json")
        values.update(
            {
                "status": "draft",
                "department": geometry.department,
                "stream_id": geometry.stream_id,
                "camera_id": geometry.camera_id,
                "geometry_id": geometry.geometry_id,
                "geometry_version": geometry.geometry_version,
                "initial_state_policy": "initialize_without_event",
                "configuration_digest": "sha256:" + "0" * 64,
                "owner_id": principal.actor_id,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )
        preliminary = GeometryRuleV1.model_validate(values)
        digest_document = preliminary.model_dump(mode="json")
        for field in (
            "configuration_digest",
            "status",
            "owner_id",
            "approval_record_id",
            "created_at",
            "updated_at",
        ):
            digest_document.pop(field, None)
        digest = _canonical_digest(digest_document)
        definition = preliminary.model_copy(update={"configuration_digest": digest})
        checked = self.cel.compile(definition.cel_condition)
        canonical = canonicalize_geometry(_geometry_definition(geometry).shape)
        CompiledGeometryRule.build(
            definition,
            _geometry_definition(geometry),
            canonical,
            self.cel,
        )
        total_cost = checked.static_cost + definition.graph.static_cost
        if total_cost > 320:
            raise SpatialValidationError("Rule total static cost exceeds 320")
        return (
            definition,
            geometry,
            RuleCompilePreview(
                configuration_digest=digest,
                checked_cel_digest=checked.digest,
                cel_static_cost=checked.static_cost,
                graph_static_cost=definition.graph.static_cost,
                total_static_cost=total_cost,
                geometry_digest=geometry.configuration_digest,
            ),
            checked.serialized,
        )

    def create_rule(
        self,
        geometry_record_id: str,
        payload: GeometryRuleCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsGeometryRule:
        normalized_reason = _safe_reason(reason)
        try:
            with self.session.begin():
                definition, geometry, preview, serialized = self.compile_rule(
                    geometry_record_id,
                    payload,
                    principal=principal,
                )
                retained = int(
                    self.session.scalar(
                        select(func.count())
                        .select_from(AnalyticsGeometryRule)
                        .where(
                            AnalyticsGeometryRule.assignment_id == payload.assignment_id,
                            AnalyticsGeometryRule.status.in_(("draft", "approved")),
                        )
                    )
                    or 0
                )
                if retained >= 64:
                    raise SpatialConflictError("Assignment rule limit reached")
                record_id = _stable_id(
                    "rule", geometry.department, definition.rule_id, definition.version
                )
                row = AnalyticsGeometryRule(
                    rule_record_id=record_id,
                    geometry_record_id=geometry.geometry_record_id,
                    department=definition.department,
                    assignment_id=definition.assignment_id,
                    stream_id=definition.stream_id,
                    camera_id=definition.camera_id,
                    rule_id=definition.rule_id,
                    rule_version=definition.version,
                    status="draft",
                    event_kind=definition.event_kind,
                    configuration=definition.model_dump(mode="json"),
                    visual_graph=definition.graph.model_dump(mode="json"),
                    checked_cel=serialized,
                    checked_cel_digest=preview.checked_cel_digest,
                    configuration_digest=definition.configuration_digest,
                    static_cost=preview.total_static_cost,
                    retention_class=definition.retention_class,
                    owner_id=principal.actor_id,
                    last_change_reason=normalized_reason,
                    effective_from=definition.effective_from,
                    effective_until=definition.effective_until,
                    created_at=definition.created_at,
                    updated_at=definition.updated_at,
                )
                self.session.add(row)
                self.session.flush()
                self._audit(
                    principal,
                    action="analytics.geometry_rule.create",
                    target_type="analytics_geometry_rule",
                    target_id=record_id,
                    reason=normalized_reason,
                    request_id=request_id,
                    context={"assignment_id": row.assignment_id, "status": "draft"},
                )
            return row
        except IntegrityError as exc:
            raise SpatialConflictError("Rule version already exists") from exc

    def approve_rule(
        self,
        record_id: str,
        approval_record_id: str,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsGeometryRule:
        normalized_reason = _safe_reason(reason)
        try:
            with self.session.begin():
                row = self._rule(record_id, principal)
                if row.record_version != expected_version:
                    raise SpatialPreconditionError("Rule version ETag does not match")
                if row.status != "draft":
                    raise SpatialConflictError("Only draft rules can be approved")
                row.status = "approved"
                row.approval_record_id = approval_record_id
                row.owner_id = principal.actor_id
                row.last_change_reason = normalized_reason
                row.updated_at = utc_now()
                configuration = dict(row.configuration)
                configuration.update(
                    {
                        "status": "approved",
                        "approval_record_id": approval_record_id,
                        "owner_id": principal.actor_id,
                        "updated_at": row.updated_at.isoformat(),
                    }
                )
                row.configuration = configuration
                self.session.flush()
                _rule_definition(row)
                self._audit(
                    principal,
                    action="analytics.geometry_rule.approve",
                    target_type="analytics_geometry_rule",
                    target_id=record_id,
                    reason=normalized_reason,
                    request_id=request_id,
                    context={"assignment_id": row.assignment_id, "status": "approved"},
                )
            return row
        except StaleDataError as exc:
            raise SpatialPreconditionError("Rule version changed concurrently") from exc

    def get_geometry(self, record_id: str, principal: Principal) -> AnalyticsGeometry:
        return self._geometry(record_id, principal)

    def list_geometries(
        self,
        *,
        principal: Principal,
        stream_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> GeometryListResponse:
        query = select(AnalyticsGeometry)
        if principal.allowed_departments is not None:
            query = query.where(AnalyticsGeometry.department.in_(principal.allowed_departments))
        if stream_id is not None:
            query = query.where(AnalyticsGeometry.stream_id == stream_id)
        if status is not None:
            query = query.where(AnalyticsGeometry.status == status)
        total = int(self.session.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = self.session.scalars(
            query.order_by(AnalyticsGeometry.updated_at.desc()).limit(limit).offset(offset)
        ).all()
        return GeometryListResponse(
            items=[geometry_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_rule(self, record_id: str, principal: Principal) -> AnalyticsGeometryRule:
        return self._rule(record_id, principal)

    def list_rules(
        self,
        *,
        principal: Principal,
        assignment_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> GeometryRuleListResponse:
        query = select(AnalyticsGeometryRule)
        if principal.allowed_departments is not None:
            query = query.where(
                AnalyticsGeometryRule.department.in_(principal.allowed_departments)
            )
        if assignment_id is not None:
            query = query.where(AnalyticsGeometryRule.assignment_id == assignment_id)
        if status is not None:
            query = query.where(AnalyticsGeometryRule.status == status)
        total = int(self.session.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = self.session.scalars(
            query.order_by(AnalyticsGeometryRule.updated_at.desc()).limit(limit).offset(offset)
        ).all()
        return GeometryRuleListResponse(
            items=[rule_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _stream_scope(
        self, stream_id: str, principal: Principal
    ) -> tuple[StreamEndpoint, Camera]:
        endpoint = self.session.get(StreamEndpoint, stream_id)
        camera = self.session.get(Camera, endpoint.camera_id) if endpoint else None
        if camera is None or not principal.can_access_department(camera.department):
            raise SpatialNotFoundError("Stream not found")
        return endpoint, camera

    def _geometry(self, record_id: str, principal: Principal) -> AnalyticsGeometry:
        row = self.session.get(AnalyticsGeometry, record_id)
        if row is None or not principal.can_access_department(row.department):
            raise SpatialNotFoundError("Geometry not found")
        return row

    def _rule(self, record_id: str, principal: Principal) -> AnalyticsGeometryRule:
        row = self.session.get(AnalyticsGeometryRule, record_id)
        if row is None or not principal.can_access_department(row.department):
            raise SpatialNotFoundError("Rule not found")
        return row

    def _audit(
        self,
        principal: Principal,
        *,
        action: str,
        target_type: str,
        target_id: str,
        reason: str,
        request_id: str | None,
        context: dict[str, object],
    ) -> None:
        AuditRepository(self.session).record(
            actor_id=principal.actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            source="hcam.api",
            reason=reason,
            outcome="success",
            context=context,
            request_id=request_id,
        )
