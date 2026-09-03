from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.analytics.contracts import ModelDeploymentChangedV1, parse_analytics_event
from hcam.analytics.models import AnalyticsAssignment, AnalyticsAssignmentRevision
from hcam.analytics.runtime import GuardedAnalyticsRuntimeAdapter
from hcam.audit.models import AuditEvent
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64


def assignment_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "capability": "object_detection",
        "desired_state": "paused",
        "pipeline": {"id": "hcam-object-pipeline", "version": DIGEST_A},
        "models": [{"id": "yolo11n-detector", "version": DIGEST_B}],
        "taxonomy_version": "hcam.object.v1",
        "policy_version": DIGEST_C,
        "configuration_digest": DIGEST_D,
        "minimum_confidence": 0.65,
        "sampling_fps": 5.0,
        "maximum_queue_age_ms": 2_000,
        "geometry_refs": [{"id": "synthetic-entry-zone", "version": 1}],
        "retention_class": "derived.analytics.standard",
        "approval_record_id": "DR-P3.0-001",
    }
    payload.update(overrides)
    return payload


def _seed(app, *, count: int = 2) -> str:
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=count)
    return synthetic_stream_id(1)


def _analytics_event_document(event: StreamEventOutbox) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "schema_version": event.schema_version,
        "stream_id": event.stream_id,
        "camera_id": event.camera_id,
        "partition_key": event.stream_id,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": event.payload,
    }


def test_create_read_list_and_event_are_fail_closed(
    app,
    editor_headers: dict[str, str],
    monkeypatch,
) -> None:
    stream_id = _seed(app)

    def unexpected_inference(*_args, **_kwargs):
        raise AssertionError("assignment control-plane must not invoke inference")

    monkeypatch.setattr(GuardedAnalyticsRuntimeAdapter, "infer", unexpected_inference)
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Register blocked synthetic analytics assignment",
            },
        )
        assignment_id = created.json()["assignment_id"]
        fetched = client.get(
            f"/analytics-assignments/{assignment_id}",
            headers=editor_headers,
        )
        listed = client.get(
            "/analytics-assignments",
            params={"stream_id": stream_id, "capability": "object_detection"},
            headers=editor_headers,
        )

    assert created.status_code == 201
    assert created.headers["etag"] == '"1"'
    assert created.headers["location"] == f"/analytics-assignments/{assignment_id}"
    assert created.headers["cache-control"] == "no-store"
    body = created.json()
    assert body["desired_state"] == "paused"
    assert body["lifecycle_state"] == "blocked"
    assert body["reason_code"] == "owner_gates_pending"
    assert body["activation_eligible"] is False
    assert body["blocking_reasons"] == [
        "runtime_unconfigured",
        "taxonomy_unapproved",
        "retention_policy_unapproved",
    ]
    assert "locator" not in created.text.lower()
    assert fetched.status_code == 200
    assert fetched.headers["etag"] == '"1"'
    assert fetched.json() == body
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"] == [body]

    with app.state.database.session_factory() as session:
        assignment = session.get(AnalyticsAssignment, assignment_id)
        revisions = session.scalars(
            select(AnalyticsAssignmentRevision).where(
                AnalyticsAssignmentRevision.assignment_id == assignment_id
            )
        ).all()
        outbox = session.scalars(
            select(StreamEventOutbox).where(
                StreamEventOutbox.event_type
                == "hcam.analytics.model.deployment.changed.v1"
            )
        ).one()
        audit = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "analytics.assignment.create",
                AuditEvent.outcome == "success",
            )
        ).one()

    assert assignment is not None
    assert assignment.desired_state == "paused"
    assert assignment.lifecycle_state == "blocked"
    assert len(revisions) == 1
    parsed = parse_analytics_event(_analytics_event_document(outbox))
    assert isinstance(parsed, ModelDeploymentChangedV1)
    assert parsed.partition_key == stream_id
    assert parsed.payload.current is not None
    assert parsed.payload.previous is None
    assert parsed.payload.lifecycle_state == "blocked"
    assert audit.context["lifecycle_state"] == "blocked"


def test_update_requires_etag_digest_and_records_immutable_revision(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    create_headers = {
        **editor_headers,
        "X-HCAM-Reason": "Create synthetic assignment revision baseline",
    }
    update_headers = {
        **editor_headers,
        "X-HCAM-Reason": "Raise synthetic detector confidence threshold",
    }
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=create_headers,
        )
        assignment_id = created.json()["assignment_id"]
        missing_etag = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.7, "configuration_digest": DIGEST_A},
            headers=update_headers,
        )
        malformed_etag = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.7, "configuration_digest": DIGEST_A},
            headers={**update_headers, "If-Match": "1"},
        )
        missing_digest = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.7},
            headers={**update_headers, "If-Match": '"1"'},
        )
        stale = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.7, "configuration_digest": DIGEST_A},
            headers={**update_headers, "If-Match": '"2"'},
        )
        updated = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.7, "configuration_digest": DIGEST_A},
            headers={**update_headers, "If-Match": '"1"'},
        )
        revisions = client.get(
            f"/analytics-assignments/{assignment_id}/revisions",
            headers=editor_headers,
        )

    assert missing_etag.status_code == 428
    assert malformed_etag.status_code == 400
    assert missing_digest.status_code == 422
    assert stale.status_code == 412
    assert updated.status_code == 200
    assert updated.headers["etag"] == '"2"'
    assert updated.json()["version"] == 2
    assert updated.json()["minimum_confidence"] == 0.7
    assert updated.json()["configuration_digest"] == DIGEST_A
    assert updated.json()["desired_state"] == "paused"
    assert updated.json()["activation_eligible"] is False
    assert revisions.status_code == 200
    assert [item["version"] for item in revisions.json()["items"]] == [2, 1]
    assert revisions.json()["items"][1]["snapshot"]["minimum_confidence"] == 0.65

    with app.state.database.session_factory() as session:
        events = session.scalars(
            select(StreamEventOutbox)
            .where(
                StreamEventOutbox.event_type
                == "hcam.analytics.model.deployment.changed.v1"
            )
            .order_by(StreamEventOutbox.occurred_at, StreamEventOutbox.event_id)
        ).all()
        success_audits = session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.action == "analytics.assignment.update",
                AuditEvent.outcome == "success",
            )
        )

    assert len(events) == 2
    parsed_update = parse_analytics_event(_analytics_event_document(events[-1]))
    assert isinstance(parsed_update, ModelDeploymentChangedV1)
    assert parsed_update.payload.previous is not None
    assert parsed_update.payload.current is not None
    assert parsed_update.payload.previous.configuration_digest == DIGEST_D
    assert parsed_update.payload.current.configuration_digest == DIGEST_A
    assert success_audits == 1


def test_assignment_access_validation_conflicts_and_safe_audit(
    app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    reason = "Create department-scoped analytics assignment"
    scoped_editor = {
        **editor_headers,
        "X-HCAM-Departments": "Engineering Lab",
        "X-HCAM-Reason": reason,
    }
    wrong_department = {
        **editor_headers,
        "X-HCAM-Departments": "Traffic",
        "X-HCAM-Reason": reason,
    }
    viewer_mutation = {
        **viewer_headers,
        "X-HCAM-Reason": "Viewer must not create analytics assignments",
    }
    with TestClient(app) as client:
        forbidden = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=viewer_mutation,
        )
        hidden_stream = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=wrong_department,
        )
        invalid_state = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(desired_state="enabled"),
            headers=scoped_editor,
        )
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=scoped_editor,
        )
        assignment_id = created.json()["assignment_id"]
        duplicate = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=scoped_editor,
        )
        hidden_get = client.get(
            f"/analytics-assignments/{assignment_id}",
            headers=wrong_department,
        )
        hidden_list = client.get(
            "/analytics-assignments",
            headers=wrong_department,
        )
        unsafe = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"minimum_confidence": 0.8, "configuration_digest": DIGEST_A},
            headers={
                **scoped_editor,
                "If-Match": '"1"',
                "X-HCAM-Reason": "Use rtsp://operator:secret@host/private",
            },
        )

    assert forbidden.status_code == 403
    assert hidden_stream.status_code == 404
    assert invalid_state.status_code == 422
    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert hidden_get.status_code == 404
    assert hidden_list.status_code == 200
    assert hidden_list.json()["total"] == 0
    assert unsafe.status_code == 422
    assert "operator" not in unsafe.text
    assert "secret" not in unsafe.text

    with app.state.database.session_factory() as session:
        unsafe_audit = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "analytics.assignment.update",
                AuditEvent.outcome == "failure",
                AuditEvent.target_id == assignment_id,
            )
        ).one()
        assignment_count = session.scalar(
            select(func.count()).select_from(AnalyticsAssignment)
        )

    assert unsafe_audit.reason == "Rejected unsafe analytics assignment request"
    assert "operator" not in str(unsafe_audit.context)
    assert "secret" not in str(unsafe_audit.context)
    assert assignment_count == 1


def test_assignment_patch_rejects_empty_noop_and_invalid_approval_id(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate blocked assignment update controls",
    }
    with TestClient(app) as client:
        invalid_approval = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(approval_record_id="invalid approval id"),
            headers=headers,
        )
        prohibited_extra = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(
                owner_details="Sensitive owner value must-not-appear"
            ),
            headers=headers,
        )
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=headers,
        )
        assignment_id = created.json()["assignment_id"]
        empty = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={},
            headers={**headers, "If-Match": '"1"'},
        )
        paused_noop = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"desired_state": "paused"},
            headers={**headers, "If-Match": '"1"'},
        )
        unchanged_digest = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={"configuration_digest": DIGEST_D},
            headers={**headers, "If-Match": '"1"'},
        )

    assert invalid_approval.status_code == 422
    assert "invalid approval id" not in invalid_approval.text
    assert prohibited_extra.status_code == 422
    assert "must-not-appear" not in prohibited_extra.text
    assert prohibited_extra.headers["cache-control"] == "no-store"
    assert empty.status_code == 422
    assert paused_noop.status_code == 422
    assert unchanged_digest.status_code == 422


def test_update_all_configuration_fields_remains_blocked(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate complete blocked configuration revision",
    }
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=assignment_payload(),
            headers=headers,
        )
        assignment_id = created.json()["assignment_id"]
        updated = client.patch(
            f"/analytics-assignments/{assignment_id}",
            json={
                "desired_state": "paused",
                "pipeline": {"id": "hcam-object-pipeline-v2", "version": DIGEST_B},
                "models": [{"id": "detector-candidate-b", "version": DIGEST_C}],
                "taxonomy_version": "hcam.object.v2",
                "policy_version": DIGEST_B,
                "configuration_digest": DIGEST_A,
                "minimum_confidence": 0.75,
                "sampling_fps": 10.0,
                "maximum_queue_age_ms": 1_000,
                "geometry_refs": [
                    {"id": "synthetic-entry-zone", "version": 2},
                    {"id": "synthetic-exit-line", "version": 1},
                ],
                "retention_class": "derived.analytics.restricted",
                "approval_record_id": "DR-P3.0-002",
            },
            headers={**headers, "If-Match": created.headers["ETag"]},
        )

    assert updated.status_code == 200
    body = updated.json()
    assert body["version"] == 2
    assert body["pipeline"] == {
        "id": "hcam-object-pipeline-v2",
        "version": DIGEST_B,
    }
    assert body["models"] == [
        {"id": "detector-candidate-b", "version": DIGEST_C}
    ]
    assert body["taxonomy_version"] == "hcam.object.v2"
    assert body["policy_version"] == DIGEST_B
    assert body["geometry_refs"] == [
        {"id": "synthetic-entry-zone", "version": 2},
        {"id": "synthetic-exit-line", "version": 1},
    ]
    assert body["retention_class"] == "derived.analytics.restricted"
    assert body["approval_record_id"] == "DR-P3.0-002"
    assert body["desired_state"] == "paused"
    assert body["lifecycle_state"] == "blocked"
    assert body["activation_eligible"] is False


def test_missing_assignment_and_stream_are_hidden(
    app,
    editor_headers: dict[str, str],
) -> None:
    _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate hidden analytics resources",
    }
    with TestClient(app) as client:
        missing_stream = client.post(
            "/streams/str_ffffffffffffffffffffffffffffffff/analytics-assignments",
            json=assignment_payload(),
            headers=headers,
        )
        missing_assignment = client.patch(
            "/analytics-assignments/ana_ffffffffffffffffffffffffffffffff",
            json={"configuration_digest": DIGEST_A},
            headers={**headers, "If-Match": '"1"'},
        )
        empty_scope = client.get(
            "/analytics-assignments",
            headers={
                "X-HCAM-Actor": "empty-scope-viewer",
                "X-HCAM-Roles": "camera.viewer",
            },
        )

    assert missing_stream.status_code == 404
    assert missing_assignment.status_code == 404
    assert empty_scope.status_code == 200
    assert empty_scope.json()["total"] == 0
