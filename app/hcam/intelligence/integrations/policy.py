from __future__ import annotations

from hcam.intelligence.integrations.canonical import digest
from hcam.intelligence.integrations.contracts import (
    CompiledQueryPlanV1,
    ProviderManifestV2,
    QueryIntentV1,
)
from hcam.intelligence.integrations.destinations import compile_destination
from hcam.intelligence.integrations.manifests import manifest_digest


class PolicyDeniedError(RuntimeError):
    reason_code = "reference_policy_denied"


def _operation(manifest: ProviderManifestV2, operation_id: str):
    for operation in manifest.operations:
        if operation.operation_id == operation_id:
            return operation
    raise PolicyDeniedError("provider operation is not allowlisted")


def compile_query_plan(
    intent: QueryIntentV1,
    manifest: ProviderManifestV2,
    *,
    control_enabled: bool,
) -> CompiledQueryPlanV1:
    if manifest.manifest_digest != manifest_digest(manifest):
        raise PolicyDeniedError("provider manifest integrity failed")
    if manifest.status != "validated_generated" or not control_enabled:
        raise PolicyDeniedError("generated provider is not enabled by control policy")
    if manifest.department != intent.department:
        raise PolicyDeniedError("query and provider departments differ")
    if manifest.provider_version_id != intent.provider_version_id:
        raise PolicyDeniedError("query references another provider version")
    if intent.purpose_code not in manifest.purposes:
        raise PolicyDeniedError("query purpose is not allowlisted")
    operation = _operation(manifest, intent.operation_id)
    if not set(intent.parameters).issubset(operation.request_fields):
        raise PolicyDeniedError("query parameter is not allowlisted")
    if not set(intent.requested_fields).issubset(operation.response_fields):
        raise PolicyDeniedError("query response field is not allowlisted")
    if operation.action != "query.read_generated":
        raise PolicyDeniedError("operation cannot execute a generated query")
    compile_destination(manifest.destination)
    if manifest.auth_profile.mode != "none_generated" or not manifest.auth_profile.enabled:
        raise PolicyDeniedError("provider authentication is not generated-only")

    parameter_digest = digest(intent.parameters)
    semantic_key = digest(
        {
            "provider_version_id": intent.provider_version_id,
            "operation_id": intent.operation_id,
            "department": intent.department,
            "purpose_code": intent.purpose_code,
            "requested_fields": intent.requested_fields,
            "parameter_digest": parameter_digest,
            "lane": intent.lane,
            "hypothesis_id": intent.hypothesis_id,
        }
    )
    delivery_key = digest({"semantic_key": semantic_key, "delivery_id": intent.delivery_id})
    material = {
        "query_id": intent.query_id,
        "provider_id": manifest.provider_id,
        "provider_version_id": manifest.provider_version_id,
        "operation_id": operation.operation_id,
        "department": intent.department,
        "purpose_code": intent.purpose_code,
        "requested_fields": intent.requested_fields,
        "parameter_digest": parameter_digest,
        "adapter_kind": manifest.adapter_kind,
        "auth_profile_id": manifest.auth_profile.profile_id,
        "destination_id": manifest.destination.destination_id,
        "semantic_key": semantic_key,
        "delivery_key": delivery_key,
    }
    return CompiledQueryPlanV1(**material, plan_digest=digest(material))
