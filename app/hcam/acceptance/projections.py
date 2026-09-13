from __future__ import annotations

from typing import Any

from hcam.acceptance.canonical import digest
from hcam.acceptance.contracts import (
    EventWorkflowCatalogueV1,
    HttpCatalogueV1,
    UiAccessibilityCatalogueV1,
)


PROJECTION_NOTICE = {
    "generated_only": True,
    "canonical": False,
    "conformance_claim": False,
    "operational": False,
}


def openapi_projection(http: HttpCatalogueV1) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for operation in http.operations:
        paths.setdefault(operation.path_template, {})[operation.method.lower()] = {
            "operationId": operation.operation_id,
            "summary": operation.purpose,
            "responses": {
                "200": {"description": "Generated contract success projection"},
                "default": {"$ref": "#/components/responses/SafeProblem"},
            },
            "x-hcam-generated-only": True,
        }
    return {
        "openapi": "3.2.0",
        "info": {"title": "H-CAM Phase 5 handoff projection", "version": "1.0.0"},
        "paths": paths,
        "components": {
            "responses": {
                "SafeProblem": {
                    "description": "Sanitized RFC 9457-shaped problem projection",
                    "content": {
                        "application/problem+json": {"schema": {"type": "object"}}
                    },
                }
            }
        },
        "x-hcam-boundary": PROJECTION_NOTICE,
    }


def asyncapi_projection(events: EventWorkflowCatalogueV1) -> dict[str, Any]:
    return {
        "asyncapi": "3.1.0",
        "info": {"title": "H-CAM event handoff projection", "version": "1.0.0"},
        "channels": {
            item.event_type: {
                "address": item.event_type,
                "messages": {
                    "generated": {"$ref": f"#/components/messages/{item.event_type}"}
                },
            }
            for item in events.events
        },
        "components": {
            "messages": {
                item.event_type: {
                    "name": item.event_type,
                    "payload": {"type": "object", "additionalProperties": False},
                    "x-hcam-grants-authority": False,
                }
                for item in events.events
            }
        },
        "x-hcam-boundary": PROJECTION_NOTICE,
    }


def cloudevents_projection(events: EventWorkflowCatalogueV1) -> dict[str, Any]:
    return {
        "specversion": "1.0.2",
        "mapping": [
            {
                "type": item.event_type,
                "source": "urn:hcam:generated:p47",
                "subject": "generated-contract",
                "semantic_identity_remains_hcam_canonical": True,
            }
            for item in events.events
        ],
        "boundary": PROJECTION_NOTICE,
    }


def arazzo_projection(events: EventWorkflowCatalogueV1) -> dict[str, Any]:
    return {
        "arazzo": "1.1.0",
        "info": {"title": "H-CAM generated workflow projection", "version": "1.0.0"},
        "sourceDescriptions": [
            {
                "name": "generatedOpenApi",
                "type": "openapi",
                "url": "urn:hcam:generated:openapi",
            }
        ],
        "workflows": [
            {
                "workflowId": workflow.workflow_id,
                "summary": "Generated non-operational consumer journey",
                "steps": [
                    {
                        "stepId": step.step_id,
                        "operationId": step.operation_ref,
                        "successCriteria": [{"condition": f"$statusCode != {500}"}],
                    }
                    for step in workflow.steps
                ],
            }
            for workflow in events.workflows
        ],
        "x-hcam-boundary": PROJECTION_NOTICE,
    }


def rfc8785_projection(payload: Any) -> dict[str, Any]:
    return {
        "profile": "RFC8785-shaped-canonical-json",
        "canonical_digest": digest(payload, maximum_bytes=16_777_216),
        "external_conformance_validated": False,
        "boundary": PROJECTION_NOTICE,
    }


def prov_projection() -> dict[str, Any]:
    return {
        "prefix": {"hcam": "urn:hcam:generated:p47:"},
        "entity": {
            "hcam:scenario-results": {"prov:type": "generated-scenario-evidence"}
        },
        "activity": {
            "hcam:deterministic-replay": {"prov:type": "generated-validation"}
        },
        "wasGeneratedBy": {
            "hcam:relation": {
                "prov:entity": "hcam:scenario-results",
                "prov:activity": "hcam:deterministic-replay",
            }
        },
        "boundary": PROJECTION_NOTICE,
    }


def slsa_projection(component_digests: dict[str, str]) -> dict[str, Any]:
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": name, "digest": {"sha256": value.removeprefix("sha256:").lower()}}
            for name, value in sorted(component_digests.items())
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "urn:hcam:generated:p47",
                "externalParameters": {},
            },
            "runDetails": {"builder": {"id": "urn:hcam:generated:local"}},
        },
        "boundary": PROJECTION_NOTICE,
    }


def validate_projections(projections: dict[str, dict[str, Any]]) -> None:
    required = {
        "openapi",
        "asyncapi",
        "cloudevents",
        "arazzo",
        "rfc8785",
        "prov",
        "slsa",
    }
    if set(projections) != required:
        raise ValueError("the exact projection set is required")
    for projection in projections.values():
        boundary = projection.get("x-hcam-boundary", projection.get("boundary"))
        if boundary != PROJECTION_NOTICE:
            raise ValueError("projection boundary is missing or has changed")
    if projections["openapi"].get("openapi") != "3.2.0":
        raise ValueError("OpenAPI projection version is not pinned")
    if projections["asyncapi"].get("asyncapi") != "3.1.0":
        raise ValueError("AsyncAPI projection version is not pinned")
    if projections["cloudevents"].get("specversion") != "1.0.2":
        raise ValueError("CloudEvents projection version is not pinned")


def build_projection_bundle(
    http: HttpCatalogueV1,
    events: EventWorkflowCatalogueV1,
    ui: UiAccessibilityCatalogueV1,
) -> dict[str, dict[str, Any]]:
    payload = {"http": http, "events": events, "ui": ui}
    projections = {
        "openapi": openapi_projection(http),
        "asyncapi": asyncapi_projection(events),
        "cloudevents": cloudevents_projection(events),
        "arazzo": arazzo_projection(events),
        "rfc8785": rfc8785_projection(payload),
        "prov": prov_projection(),
        "slsa": slsa_projection({"handoff": digest(payload, maximum_bytes=16_777_216)}),
    }
    validate_projections(projections)
    return projections
