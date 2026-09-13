from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.intelligence.integrations.canonical import stable_id
from hcam.intelligence.integrations.contracts import (
    AuthProfileV1,
    DestinationPolicyV1,
    ProviderManifestV2,
    ProviderOperationV1,
    QueryIntentV1,
)
from hcam.intelligence.integrations.manifests import manifest_digest
from tools.phase44_generated_integrations import MINIMUM_SCENARIOS, SPECS


NOW = datetime(2026, 9, 5, 8, 0, tzinfo=UTC)


def manifest(*, department: str = "Generated-Department-0") -> ProviderManifestV2:
    draft = ProviderManifestV2(
        provider_id=stable_id("prov", department, "provider"),
        provider_version_id=stable_id("pver", department, "provider", 1),
        provider_key="generated.reference.alpha",
        version=1,
        department=department,
        status="validated_generated",
        auth_profile=AuthProfileV1(
            profile_id="generated.auth.none.v1",
            mode="none_generated",
            enabled=True,
        ),
        destination=DestinationPolicyV1(
            destination_id="generated.destination.local.v1",
            route_id="generated.route.lookup.v1",
        ),
        purposes=["generated.investigation_support"],
        operations=[
            ProviderOperationV1(
                operation_id="generated.lookup.v1",
                action="query.read_generated",
                request_fields=["record_key", "category"],
                response_fields=["record_key", "category", "region"],
            )
        ],
        manifest_digest="sha256:" + "0" * 64,
    )
    return ProviderManifestV2.model_validate(
        draft.model_copy(update={"manifest_digest": manifest_digest(draft)}).model_dump(
            mode="json"
        )
    )


def intent(
    provider: ProviderManifestV2,
    *,
    actor: str = "generated-admin",
    delivery: str = "generated.delivery.001",
) -> QueryIntentV1:
    return QueryIntentV1(
        query_id=stable_id("qry", provider.department, delivery),
        delivery_id=delivery,
        provider_version_id=provider.provider_version_id,
        operation_id="generated.lookup.v1",
        department=provider.department,
        purpose_code="generated.investigation_support",
        requested_fields=["record_key", "category", "region"],
        parameters={"record_key": "gen_record_001", "category": "gen_category_a"},
        lane="manual_generated",
        requested_by=actor,
        reason="Generated-only bounded reference query",
        requested_at=NOW,
    )


def test_generated_contracts_reject_unknown_realistic_and_inconsistent_fields() -> None:
    provider = manifest()
    with pytest.raises(ValidationError):
        ProviderManifestV2.model_validate(
            {**provider.model_dump(mode="json"), "runtime_url": "gen_not_allowed"}
        )
    with pytest.raises(ValidationError):
        QueryIntentV1.model_validate(
            {
                **intent(provider).model_dump(mode="json"),
                "parameters": {"vehicle_owner": "gen_person"},
            }
        )
    with pytest.raises(ValidationError):
        AuthProfileV1(
            profile_id="generated.auth.secret.v1",
            mode="secret_lease",
            enabled=True,
        )


def test_generated_fixture_manifest_meets_floor_and_has_unique_scenarios() -> None:
    root = Path("contracts/phase-4/p4-4/fixtures")
    total = 0
    identifiers: set[str] = set()
    for filename, family, expected_count in SPECS:
        payload = json.loads((root / filename).read_text(encoding="utf-8"))
        assert payload["family"] == family
        assert payload["scenario_count"] == expected_count
        assert len(payload["vectors"]) == expected_count
        total += expected_count
        for vector in payload["vectors"]:
            assert vector["scenario_id"] not in identifiers
            identifiers.add(vector["scenario_id"])
            assert vector["generated_only"] is True
            assert vector["operational"] is False
            assert vector["generated_value"].startswith("gen_")
    assert total >= MINIMUM_SCENARIOS
