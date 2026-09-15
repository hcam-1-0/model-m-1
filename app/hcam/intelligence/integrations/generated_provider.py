from __future__ import annotations

from copy import deepcopy

from hcam.intelligence.integrations.contracts import (
    CompiledQueryPlanV1,
    GeneratedProviderPayload,
)


class StaticGeneratedProvider:
    def __init__(
        self,
        provider_version_id: str,
        records: list[dict[str, str]],
        *,
        fault: str = "none",
        completeness: str = "complete",
    ) -> None:
        self.provider_version_id = provider_version_id
        self._records = GeneratedProviderPayload(
            records=records,
            fault=fault,
            completeness=completeness,
        )

    def execute(
        self,
        plan: CompiledQueryPlanV1,
        parameters: dict[str, str],
    ) -> GeneratedProviderPayload:
        if plan.provider_version_id != self.provider_version_id:
            raise ValueError("compiled plan references another generated provider")
        records = [
            record
            for record in self._records.records
            if all(record.get(key) == value for key, value in parameters.items())
        ]
        projected = [
            {key: record[key] for key in plan.requested_fields if key in record}
            for record in records
        ]
        return GeneratedProviderPayload(
            records=deepcopy(projected),
            fault=self._records.fault,
            completeness=self._records.completeness,
        )
