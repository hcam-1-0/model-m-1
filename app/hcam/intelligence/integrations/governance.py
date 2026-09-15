from __future__ import annotations

from datetime import UTC, datetime

from hcam.intelligence.integrations.bounds import bounded_reason
from hcam.intelligence.integrations.canonical import stable_id
from hcam.intelligence.integrations.contracts import (
    ControlRevisionV1,
    ProviderManifestV2,
    QueryIntentV1,
)


class GovernanceError(RuntimeError):
    reason_code = "reference_control_denied"


class ControlRegistry:
    def __init__(self) -> None:
        self._current: dict[tuple[str, str, str], ControlRevisionV1] = {}
        self._history: list[ControlRevisionV1] = []

    def apply(
        self,
        *,
        department: str,
        scope: str,
        scope_key: str,
        state: str,
        expected_version: int,
        actor_id: str,
        reason: str,
        now: datetime | None = None,
    ) -> ControlRevisionV1:
        key = (department, scope, scope_key)
        prior = self._current.get(key)
        actual = prior.version if prior is not None else 0
        if expected_version != actual:
            raise GovernanceError("reference control version does not match")
        revision = ControlRevisionV1(
            revision_id=stable_id("rctl", department, scope, scope_key, actual + 1),
            department=department,
            scope=scope,
            scope_key=scope_key,
            state=state,
            version=actual + 1,
            actor_id=actor_id,
            reason=bounded_reason(reason),
            recorded_at=now or datetime.now(UTC),
        )
        self._current[key] = revision
        self._history.append(revision)
        return revision

    def allows(self, manifest: ProviderManifestV2, intent: QueryIntentV1) -> bool:
        checks = (
            ("organization", "generated.reference"),
            ("department", manifest.department),
            ("provider", manifest.provider_version_id),
            ("operation", intent.operation_id),
            ("purpose", intent.purpose_code),
            ("auth_profile", manifest.auth_profile.profile_id),
        )
        for scope, scope_key in checks:
            current = self._current.get((manifest.department, scope, scope_key))
            if current is not None and current.state != "enabled_generated":
                return False
        return True

    def history(self, *, department: str | None = None) -> list[ControlRevisionV1]:
        values = self._history
        if department is not None:
            values = [item for item in values if item.department == department]
        return list(values)
