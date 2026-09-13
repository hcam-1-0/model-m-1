from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from hcam.intelligence.models import (
    Alert,
    CorrelationHypothesis,
    CorrelationHypothesisRevision,
    CorrelationRun,
    IntelligenceRule,
    InvestigationTimeline,
    ReferenceProvider,
)
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


ScopedModel = TypeVar(
    "ScopedModel",
    IntelligenceRule,
    ReferenceProvider,
    CorrelationHypothesis,
    CorrelationHypothesisRevision,
    CorrelationRun,
    Alert,
    InvestigationTimeline,
)


def _authorized(statement: Select, model: type[ScopedModel], principal: Principal) -> Select:
    if principal.allowed_departments is None:
        return statement
    return statement.where(model.department.in_(sorted(principal.allowed_departments)))


class IntelligenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_rule(self, record_id: str, principal: Principal) -> IntelligenceRule | None:
        apply_department_scope(self.session, principal)
        statement = _authorized(
            select(IntelligenceRule).where(IntelligenceRule.rule_record_id == record_id),
            IntelligenceRule,
            principal,
        )
        return self.session.scalar(statement)

    def list_rules(
        self,
        principal: Principal,
        *,
        stream_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[IntelligenceRule], int]:
        apply_department_scope(self.session, principal)
        filters = []
        if stream_id is not None:
            filters.append(IntelligenceRule.stream_id == stream_id)
        if status is not None:
            filters.append(IntelligenceRule.status == status)
        statement = _authorized(select(IntelligenceRule), IntelligenceRule, principal).where(
            *filters
        )
        total = int(
            self.session.scalar(
                _authorized(
                    select(func.count()).select_from(IntelligenceRule),
                    IntelligenceRule,
                    principal,
                ).where(*filters)
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(IntelligenceRule.updated_at.desc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def get_provider(self, provider_id: str, principal: Principal) -> ReferenceProvider | None:
        apply_department_scope(self.session, principal)
        return self.session.scalar(
            _authorized(
                select(ReferenceProvider).where(
                    ReferenceProvider.provider_id == provider_id
                ),
                ReferenceProvider,
                principal,
            )
        )

    def list_providers(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[ReferenceProvider], int]:
        apply_department_scope(self.session, principal)
        statement = _authorized(select(ReferenceProvider), ReferenceProvider, principal)
        total = int(
            self.session.scalar(
                _authorized(
                    select(func.count()).select_from(ReferenceProvider),
                    ReferenceProvider,
                    principal,
                )
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(ReferenceProvider.updated_at.desc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def list_hypotheses(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[CorrelationHypothesis], int]:
        return self._list_scoped(
            CorrelationHypothesis,
            principal,
            order=CorrelationHypothesis.created_at.desc(),
            limit=limit,
            offset=offset,
        )

    def get_hypothesis(
        self, hypothesis_id: str, principal: Principal
    ) -> CorrelationHypothesis | None:
        apply_department_scope(self.session, principal)
        return self.session.scalar(
            _authorized(
                select(CorrelationHypothesis).where(
                    CorrelationHypothesis.hypothesis_id == hypothesis_id
                ),
                CorrelationHypothesis,
                principal,
            )
        )

    def get_run(self, run_id: str, principal: Principal) -> CorrelationRun | None:
        apply_department_scope(self.session, principal)
        return self.session.scalar(
            _authorized(
                select(CorrelationRun).where(CorrelationRun.run_id == run_id),
                CorrelationRun,
                principal,
            )
        )

    def list_runs(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[CorrelationRun], int]:
        return self._list_scoped(
            CorrelationRun,
            principal,
            order=CorrelationRun.created_at.desc(),
            limit=limit,
            offset=offset,
        )

    def list_hypothesis_revisions(
        self,
        hypothesis_id: str,
        principal: Principal,
        *,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[CorrelationHypothesisRevision], int]:
        apply_department_scope(self.session, principal)
        filters = [CorrelationHypothesisRevision.hypothesis_id == hypothesis_id]
        statement = _authorized(
            select(CorrelationHypothesisRevision),
            CorrelationHypothesisRevision,
            principal,
        ).where(*filters)
        total = int(
            self.session.scalar(
                _authorized(
                    select(func.count()).select_from(CorrelationHypothesisRevision),
                    CorrelationHypothesisRevision,
                    principal,
                ).where(*filters)
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(CorrelationHypothesisRevision.revision.asc())
            .limit(limit)
            .offset(offset)
        ).all()
        return rows, total

    def list_alerts(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[Alert], int]:
        return self._list_scoped(
            Alert,
            principal,
            order=Alert.created_at.desc(),
            limit=limit,
            offset=offset,
        )

    def list_timelines(
        self, principal: Principal, *, limit: int, offset: int
    ) -> tuple[Sequence[InvestigationTimeline], int]:
        return self._list_scoped(
            InvestigationTimeline,
            principal,
            order=InvestigationTimeline.updated_at.desc(),
            limit=limit,
            offset=offset,
        )

    def _list_scoped(
        self,
        model: type[ScopedModel],
        principal: Principal,
        *,
        order: object,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[ScopedModel], int]:
        apply_department_scope(self.session, principal)
        statement = _authorized(select(model), model, principal)
        total = int(
            self.session.scalar(
                _authorized(select(func.count()).select_from(model), model, principal)
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(order).limit(limit).offset(offset)
        ).all()
        return rows, total
