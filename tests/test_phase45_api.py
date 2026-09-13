from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    CorrectionCommandV1,
    DeletionIntentV1,
    HoldOverlayV1,
    ProvenanceBundleV1,
    ProvenanceEdgeV1,
    ProvenanceNodeV1,
    RelationshipRevisionV1,
    RetentionPolicyReferenceV1,
)
from hcam.intelligence.investigations.evidence import register_reference
from hcam.intelligence.investigations.integrity import assess_generated_digest
from hcam.intelligence.investigations.persistence import InvestigationRepository
from hcam.intelligence.investigations.provenance import validate_graph
from hcam.intelligence.investigations.review import record_review


def test_generated_investigation_api_create_append_and_reconstruct(
    p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    with TestClient(p45_app) as client:
        health = client.get("/investigations/health", headers=p45_headers)
        assert health.status_code == 200
        assert health.json()["source_resolution"] is False
        assert health.headers["cache-control"] == "no-store"

        created = client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        )
        assert created.status_code == 201
        assert created.headers["etag"] == '"1"'
        assert client.get(
            "/investigations/timelines", headers=p45_headers
        ).json()["total"] == 1
        fetched = client.get(
            f"/investigations/timelines/{p45_context['timeline_id']}",
            headers=p45_headers,
        )
        assert fetched.status_code == 200 and fetched.headers["etag"] == '"1"'

        entry = p45_context["entry"]()
        appended = client.post(
            f"/investigations/timelines/{p45_context['timeline_id']}/entries",
            headers={**p45_headers, "If-Match": '"1"'},
            json=entry.model_dump(mode="json"),
        )
        assert appended.status_code == 200
        assert appended.headers["etag"] == '"2"'

        reconstruction = client.get(
            f"/investigations/timelines/{p45_context['timeline_id']}/reconstruction",
            params={"through_revision": 2, "view": "record_sequence"},
            headers=p45_headers,
        )
        assert reconstruction.status_code == 200
        assert reconstruction.json()["entries"][0]["entry_id"] == entry.entry_id


def test_api_requires_matching_reason_and_etag(
    p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    with TestClient(p45_app) as client:
        assert client.post(
            "/investigations/timelines",
            headers={**p45_headers, "X-HCAM-Reason": "Generated mismatched reason"},
            json=p45_context["command"].model_dump(mode="json"),
        ).status_code == 422
        assert client.post(
            f"/investigations/timelines/{p45_context['timeline_id']}/entries",
            headers=p45_headers,
            json=p45_context["entry"]().model_dump(mode="json"),
        ).status_code == 428

        created = client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        )
        assert created.status_code == 201
        conflicting = p45_context["command"].model_copy(
            update={"delivery_id": "generated.p45.conflicting.create"}
        )
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=conflicting.model_dump(mode="json"),
        ).status_code == 412
        assert client.post(
            f"/investigations/timelines/{p45_context['timeline_id']}/entries",
            headers={**p45_headers, "If-Match": '"99"'},
            json=p45_context["entry"]().model_dump(mode="json"),
        ).status_code == 412
        assert client.get(
            "/investigations/timelines/inv_" + "f" * 32,
            headers=p45_headers,
        ).status_code == 404


def test_database_write_race_is_sanitized(
    monkeypatch, p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    def conflict(*_args, **_kwargs):
        raise IntegrityError("generated statement", {}, RuntimeError("generated conflict"))

    monkeypatch.setattr(InvestigationRepository, "create_timeline", conflict)
    with TestClient(p45_app) as client:
        response = client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        )
    assert response.status_code == 412
    assert response.json() == {"detail": "investigation precondition failed"}


def test_generated_api_covers_evidence_corrections_review_retention_and_export(
    p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    timeline_id = p45_context["timeline_id"]
    with TestClient(p45_app) as client:
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        ).status_code == 201
        assert client.post(
            f"/investigations/timelines/{timeline_id}/entries",
            headers={**p45_headers, "If-Match": '"1"'},
            json=p45_context["entry"]().model_dump(mode="json"),
        ).status_code == 200

        reference = register_reference(
            timeline_id=timeline_id,
            department=p45_context["department"],
            source_system_ref=stable_id("ref", "api-system"),
            source_object_ref=stable_id("ref", "api-object"),
            source_version="generated.v1",
            content_digest=digest({"generated": "api-evidence"}),
            canonicalization_profile="generated.json.v1",
            classification="generated.restricted",
            registered_by=p45_context["actor"],
            reason=p45_context["reason"],
            registered_at=p45_context["now"],
        )
        created_reference = client.post(
            f"/investigations/timelines/{timeline_id}/evidence",
            headers=p45_headers,
            json=reference.model_dump(mode="json"),
        )
        assert created_reference.status_code == 201
        listed = client.get(
            f"/investigations/timelines/{timeline_id}/evidence",
            headers=p45_headers,
        )
        assert listed.status_code == 200 and listed.json()["total"] == 1

        assessment = assess_generated_digest(
            reference,
            observed_digest=reference.content_digest,
            outcome="matched",
            assessed_by=p45_context["actor"],
            assessed_at=p45_context["now"],
        )
        assert client.post(
            f"/investigations/timelines/{timeline_id}/integrity",
            headers=p45_headers,
            json=assessment.model_dump(mode="json"),
        ).status_code == 201

        entity = ProvenanceNodeV1(
            node_id=stable_id("ipnd", "api-entity"),
            kind="entity",
            reference_id=stable_id("ref", "api-entity"),
            version=1,
            attributes={"generated_value": "entity"},
        )
        agent = ProvenanceNodeV1(
            node_id=stable_id("ipnd", "api-agent"),
            kind="agent",
            reference_id=stable_id("ref", "api-agent"),
            version=1,
            attributes={},
        )
        edge = ProvenanceEdgeV1(
            edge_id=stable_id("iped", "api-edge"),
            relation="was_attributed_to",
            source_node_id=entity.node_id,
            target_node_id=agent.node_id,
            recorded_at=p45_context["now"],
        )
        candidate = ProvenanceBundleV1(
            bundle_id=stable_id("iprv", "api-bundle"),
            timeline_id=timeline_id,
            department=p45_context["department"],
            nodes=[entity, agent],
            edges=[edge],
            bundle_digest="sha256:" + "0" * 64,
            completeness="partial",
        )
        bundle = candidate.model_copy(update={"bundle_digest": validate_graph(candidate)})
        assert client.post(
            f"/investigations/timelines/{timeline_id}/provenance",
            headers=p45_headers,
            json={
                "bundle": bundle.model_dump(mode="json"),
                "recorded_at": p45_context["now"].isoformat(),
            },
        ).status_code == 201

        target = stable_id("ref", "api-target")
        dependent = stable_id("ref", "api-dependent")
        correction = CorrectionCommandV1(
            correction_id=stable_id("icor", "api-correction"),
            timeline_id=timeline_id,
            department=p45_context["department"],
            kind="retraction",
            target_type="entry",
            target_ref=target,
            target_version=1,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            delivery_id="generated.api.correction",
            recorded_at=p45_context["now"],
        )
        corrected = client.post(
            f"/investigations/timelines/{timeline_id}/corrections",
            headers=p45_headers,
            json={
                "command": correction.model_dump(mode="json"),
                "dependencies": {target: [["review", dependent]]},
            },
        )
        assert corrected.status_code == 201
        assert corrected.json()["impact_set"]["propagation_state"] == "pending"

        review = record_review(
            timeline_id=timeline_id,
            department=p45_context["department"],
            target_ref=target,
            decision="no_conclusion",
            disposition="reviewed",
            revision=1,
            supersedes_review_id=None,
            reviewer_id=p45_context["actor"],
            reason=p45_context["reason"],
            evidence_digest=digest({"review": "generated"}),
            recorded_at=p45_context["now"],
        )
        assert client.post(
            f"/investigations/timelines/{timeline_id}/reviews",
            headers=p45_headers,
            json=review.model_dump(mode="json"),
        ).status_code == 201
        assert client.post(
            f"/investigations/timelines/{timeline_id}/reviews",
            headers=p45_headers,
            json=review.model_dump(mode="json"),
        ).status_code == 201
        after_review_retry = client.get(
            f"/investigations/timelines/{timeline_id}", headers=p45_headers
        )
        assert after_review_retry.json()["revision"] == 3

        closed = client.post(
            f"/investigations/timelines/{timeline_id}/lifecycle",
            headers={**p45_headers, "If-Match": '"3"'},
            json={
                "department": p45_context["department"],
                "lifecycle": "closed",
                "recorded_at": p45_context["now"].isoformat(),
            },
        )
        assert closed.status_code == 200 and closed.json()["lifecycle"] == "closed"
        reopened = client.post(
            f"/investigations/timelines/{timeline_id}/lifecycle",
            headers={**p45_headers, "If-Match": '"4"'},
            json={
                "department": p45_context["department"],
                "lifecycle": "reopened",
                "recorded_at": p45_context["now"].isoformat(),
            },
        )
        assert reopened.status_code == 200 and reopened.json()["revision"] == 5

        second_id = stable_id("inv", "api-second")
        second_command = p45_context["command"].model_copy(
            update={
                "timeline_id": second_id,
                "title": "generated.p45.second",
                "delivery_id": "generated.p45.timeline.second",
            }
        )
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=second_command.model_dump(mode="json"),
        ).status_code == 201
        relation = RelationshipRevisionV1(
            relationship_id=stable_id("irel", second_id, timeline_id),
            department=p45_context["department"],
            source_timeline_id=second_id,
            target_timeline_id=timeline_id,
            kind="merged_into",
            revision=1,
            active=True,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            recorded_at=p45_context["now"],
        )
        assert client.post(
            "/investigations/relationships",
            headers=p45_headers,
            json=relation.model_dump(mode="json"),
        ).status_code == 201

        hold = HoldOverlayV1(
            hold_ref=stable_id("ref", "api-hold"),
            timeline_id=timeline_id,
            department=p45_context["department"],
            state="proposed",
            scope_digest=digest({"scope": "generated"}),
            authority_ref=stable_id("ref", "api-authority"),
            revision=1,
            recorded_at=p45_context["now"],
        )
        assert client.post(
            f"/investigations/timelines/{timeline_id}/holds",
            headers=p45_headers,
            json=hold.model_dump(mode="json"),
        ).status_code == 201
        policy = RetentionPolicyReferenceV1(
            policy_ref=stable_id("ref", "api-policy"),
            policy_version="generated.v1",
            policy_digest=digest({"policy": "generated"}),
            classification="generated.restricted",
        )
        retention = client.post(
            f"/investigations/timelines/{timeline_id}/retention-evaluations",
            headers=p45_headers,
            json={
                "department": p45_context["department"],
                "policy": policy.model_dump(mode="json"),
                "policy_available": True,
                "evaluated_at": p45_context["now"].isoformat(),
            },
        )
        assert retention.status_code == 201
        assert retention.json()["outcome"] == "eligible_for_simulation"

        intent = DeletionIntentV1(
            intent_id=stable_id("idin", "api-intent"),
            timeline_id=timeline_id,
            department=p45_context["department"],
            target_refs=[reference.source_object_ref],
            policy_evaluation_id=retention.json()["evaluation_id"],
            requested_by=p45_context["actor"],
            reason=p45_context["reason"],
            requested_at=p45_context["now"],
        )
        deletion = client.post(
            f"/investigations/timelines/{timeline_id}/deletion-simulations",
            headers=p45_headers,
            json={"intent": intent.model_dump(mode="json"), "residuals": {}},
        )
        assert deletion.status_code == 200
        assert deletion.json()["external_action_executed"] is False
        deletion_retry = client.post(
            f"/investigations/timelines/{timeline_id}/deletion-simulations",
            headers=p45_headers,
            json={"intent": intent.model_dump(mode="json"), "residuals": {}},
        )
        assert deletion_retry.status_code == 200
        assert deletion_retry.json() == deletion.json()

        exported = client.post(
            f"/investigations/timelines/{timeline_id}/export-previews",
            headers=p45_headers,
            json={
                "department": p45_context["department"],
                "purpose_code": "generated.investigation",
                "recipient_class": "generated.reviewer",
                "policy_ref": stable_id("ref", "api-export-policy"),
                "allowed_reference_ids": [reference.reference_id],
                "unresolved_reference_ids": [],
                "prepared_at": p45_context["now"].isoformat(),
            },
        )
        assert exported.status_code == 200
        assert exported.json()["source_payload_included"] is False


def test_generated_api_rejects_scope_chain_and_path_violations(
    p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    timeline_id = p45_context["timeline_id"]
    with TestClient(p45_app) as client:
        restricted_headers = {
            **p45_headers,
            "X-HCAM-Roles": "investigation.write_generated",
            "X-HCAM-Departments": p45_context["department"],
        }
        inaccessible = p45_context["command"].model_copy(
            update={
                "timeline_id": stable_id("inv", "inaccessible"),
                "department": "Generated-Department-Denied",
                "delivery_id": "generated.p45.inaccessible",
            }
        )
        assert client.post(
            "/investigations/timelines",
            headers=restricted_headers,
            json=inaccessible.model_dump(mode="json"),
        ).status_code == 404
        wrong_actor = p45_context["command"].model_copy(
            update={
                "timeline_id": stable_id("inv", "wrong-actor"),
                "actor_id": "generated-other-actor",
                "delivery_id": "generated.p45.wrong-actor",
            }
        )
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=wrong_actor.model_dump(mode="json"),
        ).status_code == 422
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        ).status_code == 201
        assert client.get(
            f"/investigations/timelines/{timeline_id}/reconstruction",
            params={"through_revision": 1},
            headers=p45_headers,
        ).status_code == 412
        assert client.get(
            f"/investigations/timelines/{timeline_id}/reconstruction",
            params={"through_revision": 2},
            headers=p45_headers,
        ).status_code == 412

        wrong_path = stable_id("inv", "wrong-path")
        entry = p45_context["entry"]()
        assert client.post(
            f"/investigations/timelines/{wrong_path}/entries",
            headers={**p45_headers, "If-Match": '"1"'},
            json=entry.model_dump(mode="json"),
        ).status_code == 422

        broken_review = record_review(
            timeline_id=timeline_id,
            department=p45_context["department"],
            target_ref=stable_id("ref", "broken-api-review"),
            decision="no_conclusion",
            disposition="reviewed",
            revision=2,
            supersedes_review_id=stable_id("irev", "missing-review"),
            reviewer_id=p45_context["actor"],
            reason=p45_context["reason"],
            evidence_digest=digest({"review": "broken"}),
            recorded_at=p45_context["now"],
        )
        assert client.post(
            f"/investigations/timelines/{timeline_id}/reviews",
            headers=p45_headers,
            json=broken_review.model_dump(mode="json"),
        ).status_code == 412

        second_id = stable_id("inv", "chain-second")
        second_command = p45_context["command"].model_copy(
            update={
                "timeline_id": second_id,
                "delivery_id": "generated.p45.chain-second",
            }
        )
        assert client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=second_command.model_dump(mode="json"),
        ).status_code == 201
        skipped_relation = RelationshipRevisionV1(
            relationship_id=stable_id("irel", "skipped-api-relation"),
            department=p45_context["department"],
            source_timeline_id=second_id,
            target_timeline_id=timeline_id,
            kind="related",
            revision=2,
            active=True,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            recorded_at=p45_context["now"],
        )
        assert client.post(
            "/investigations/relationships",
            headers=p45_headers,
            json=skipped_relation.model_dump(mode="json"),
        ).status_code == 412

        skipped_hold = HoldOverlayV1(
            hold_ref=stable_id("ref", "skipped-api-hold"),
            timeline_id=timeline_id,
            department=p45_context["department"],
            state="proposed",
            scope_digest=digest({"scope": "api"}),
            authority_ref=stable_id("ref", "api-hold-authority"),
            revision=2,
            recorded_at=p45_context["now"],
        )
        assert client.post(
            f"/investigations/timelines/{timeline_id}/holds",
            headers=p45_headers,
            json=skipped_hold.model_dump(mode="json"),
        ).status_code == 412
