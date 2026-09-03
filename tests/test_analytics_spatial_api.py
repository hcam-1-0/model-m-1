from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsEvent,
    AnalyticsGeometry,
    AnalyticsGeometryEvaluatorRun,
    AnalyticsGeometryRule,
    AnalyticsTrackRuleState,
)
from hcam.analytics.spatial.execution import purge_expired_geometry_events
from hcam.audit.models import AuditEvent
from hcam.camera_registry.models import utc_now
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64


def _seed(app) -> str:
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=2)
    return synthetic_stream_id(1)


def _assignment_payload() -> dict[str, object]:
    return {
        "capability": "object_detection",
        "pipeline": {"id": "hcam-object-pipeline", "version": DIGEST_A},
        "models": [{"id": "generated-detector", "version": DIGEST_B}],
        "taxonomy_version": "hcam.object.v1",
        "policy_version": DIGEST_C,
        "configuration_digest": DIGEST_D,
        "minimum_confidence": 0.5,
        "sampling_fps": 5.0,
        "maximum_queue_age_ms": 2_000,
        "geometry_refs": [],
        "retention_class": "derived.analytics.standard",
        "approval_record_id": "D-P3.4-START",
    }


def _geometry_payload() -> dict[str, object]:
    return {
        "geometry_id": "generated-api-line",
        "version": 1,
        "shape": {
            "kind": "line",
            "start": {"x": 0.5, "y": 0.1},
            "end": {"x": 0.5, "y": 0.9},
            "crossing_direction": "both",
        },
        "schedule": {"mode": "always", "timezone": "UTC", "windows": []},
        "intended_use": "Generated-only API line crossing validation",
        "policy_version": DIGEST_A,
    }


def _rule_payload(assignment_id: str, *, cel: str = "confidence >= 0.5") -> dict[str, object]:
    return {
        "rule_id": "generated-api-crossing",
        "version": 1,
        "assignment_id": assignment_id,
        "event_kind": "hcam.analytics.line.crossing.v1",
        "class_filter": ["vehicle.car"],
        "anchor_policy": "bottom_center",
        "boundary_policy": "inside_inclusive",
        "line_direction": "both",
        "deadband": 0.01,
        "rearm_distance": 0.04,
        "cel_condition": cel,
        "graph": {
            "nodes": [
                {
                    "node_id": "crossing",
                    "kind": "spatial",
                    "signal": "line_crossing",
                }
            ],
            "output_node_id": "crossing",
        },
        "retention_class": "derived.analytics.standard",
        "effective_from": "2026-08-25T00:00:00Z",
    }


def test_geometry_and_rule_control_plane_is_versioned_scoped_and_audited(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate generated geometry control plane",
    }
    with TestClient(app) as client:
        assignment = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=_assignment_payload(),
            headers=headers,
        )
        assignment_id = assignment.json()["assignment_id"]
        created = client.post(
            f"/streams/{stream_id}/analytics-geometries",
            json=_geometry_payload(),
            headers=headers,
        )
        geometry_record_id = created.json()["geometry_record_id"]
        missing_etag = client.post(
            f"/analytics-geometries/{geometry_record_id}/approve",
            json={"approval_record_id": "D-P3.4-GEOMETRY"},
            headers=headers,
        )
        approved = client.post(
            f"/analytics-geometries/{geometry_record_id}/approve",
            json={"approval_record_id": "D-P3.4-GEOMETRY"},
            headers={**headers, "If-Match": created.headers["ETag"]},
        )
        preview = client.post(
            f"/analytics-geometries/{geometry_record_id}/rule-compile-previews",
            json=_rule_payload(assignment_id),
            headers=editor_headers,
        )
        unsafe_preview = client.post(
            f"/analytics-geometries/{geometry_record_id}/rule-compile-previews",
            json=_rule_payload(assignment_id, cel="camera.owner == 'private'"),
            headers=editor_headers,
        )
        created_rule = client.post(
            f"/analytics-geometries/{geometry_record_id}/rules",
            json=_rule_payload(assignment_id),
            headers=headers,
        )
        assert created_rule.status_code == 201, created_rule.text
        rule_record_id = created_rule.json()["rule_record_id"]
        approved_rule = client.post(
            f"/analytics-geometry-rules/{rule_record_id}/approve",
            json={"approval_record_id": "D-P3.4-RULE"},
            headers={**headers, "If-Match": created_rule.headers["ETag"]},
        )
        listed = client.get(
            "/analytics-geometry-rules",
            params={"assignment_id": assignment_id},
            headers=editor_headers,
        )

    assert assignment.status_code == 201
    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    assert created.headers["etag"] == '"1"'
    assert missing_etag.status_code == 428
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.headers["etag"] == '"2"'
    assert preview.status_code == 200
    assert preview.json()["accepted"] is True
    assert preview.json()["total_static_cost"] <= 320
    assert unsafe_preview.status_code == 422
    assert "private" not in unsafe_preview.text
    assert created_rule.status_code == 201
    assert created_rule.json()["status"] == "draft"
    assert approved_rule.status_code == 200
    assert approved_rule.json()["status"] == "approved"
    assert approved_rule.json()["configuration_digest"] == preview.json()[
        "configuration_digest"
    ]
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    with app.state.database.session_factory() as session:
        geometry = session.get(AnalyticsGeometry, geometry_record_id)
        rule = session.get(AnalyticsGeometryRule, rule_record_id)
        actions = set(
            session.scalars(
                select(AuditEvent.action).where(
                    AuditEvent.action.like("analytics.geometry%")
                )
            ).all()
        )
    assert geometry is not None and geometry.canonical_wkb == geometry.spatial_geometry
    assert rule is not None and rule.checked_cel
    assert actions == {
        "analytics.geometry.create",
        "analytics.geometry.approve",
        "analytics.geometry_rule.create",
        "analytics.geometry_rule.approve",
    }


def test_geometry_resources_are_hidden_across_departments(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Create department scoped generated geometry",
    }
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{stream_id}/analytics-geometries",
            json=_geometry_payload(),
            headers=headers,
        )
        record_id = created.json()["geometry_record_id"]
        hidden = client.get(
            f"/analytics-geometries/{record_id}",
            headers={
                "X-HCAM-Actor": "other-viewer",
                "X-HCAM-Roles": "camera.viewer",
                "X-HCAM-Departments": "other-department",
            },
        )
        hidden_list = client.get(
            "/analytics-geometries",
            headers={
                "X-HCAM-Actor": "other-viewer",
                "X-HCAM-Roles": "camera.viewer",
                "X-HCAM-Departments": "other-department",
            },
        )
    assert hidden.status_code == 404
    assert hidden_list.status_code == 200
    assert hidden_list.json()["total"] == 0


def test_generated_geometry_run_is_default_off_idempotent_and_transactional(
    app,
    editor_headers: dict[str, str],
) -> None:
    stream_id = _seed(app)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Execute sealed generated line crossing scenario",
    }
    original_settings = app.state.settings
    app.state.settings = replace(
        original_settings,
        analytics_generated_geometry_enabled=True,
    )
    try:
        with TestClient(app) as client:
            assignment = client.post(
                f"/streams/{stream_id}/analytics-assignments",
                json=_assignment_payload(),
                headers=headers,
            )
            assignment_id = assignment.json()["assignment_id"]
            geometry = client.post(
                f"/streams/{stream_id}/analytics-geometries",
                json=_geometry_payload(),
                headers=headers,
            )
            geometry_id = geometry.json()["geometry_record_id"]
            client.post(
                f"/analytics-geometries/{geometry_id}/approve",
                json={"approval_record_id": "D-P3.4-GEOMETRY"},
                headers={**headers, "If-Match": geometry.headers["ETag"]},
            )
            rule = client.post(
                f"/analytics-geometries/{geometry_id}/rules",
                json=_rule_payload(assignment_id),
                headers=headers,
            )
            rule_id = rule.json()["rule_record_id"]
            client.post(
                f"/analytics-geometry-rules/{rule_id}/approve",
                json={"approval_record_id": "D-P3.4-RULE"},
                headers={**headers, "If-Match": rule.headers["ETag"]},
            )

            with app.state.database.session_factory() as session, session.begin():
                assignment_row = session.get(AnalyticsAssignment, assignment_id)
                assert assignment_row is not None
                assignment_row.desired_state = "enabled"
                assignment_row.lifecycle_state = "running"
                assignment_row.reason_code = "generated_runtime_active"

            payload = {
                "scenario_id": "c10-line-crossing",
                "rule_record_ids": [rule_id],
                "seed": 7,
                "observed_at": "2026-08-25T12:00:00Z",
            }
            executed = client.post(
                f"/analytics-assignments/{assignment_id}/generated-geometry-runs",
                json=payload,
                headers=headers,
            )
            assert executed.status_code == 201, executed.text
            run_id = executed.json()["run_id"]
            replayed = client.post(
                f"/analytics-assignments/{assignment_id}/generated-geometry-runs",
                json=payload,
                headers=headers,
            )
            events = client.get(
                f"/analytics-geometry-runs/{run_id}/events",
                headers=editor_headers,
            )

        assert executed.json()["status"] == "succeeded"
        assert executed.json()["event_count"] == 1
        assert executed.json()["close_reason"] == "completed"
        assert replayed.status_code == 201
        assert replayed.json()["reused"] is True
        assert replayed.json()["run_id"] == run_id
        assert events.status_code == 200
        assert events.json()["total"] == 1
        document = events.json()["items"][0]
        assert document["event_kind"] == "hcam.analytics.line.crossing.v1"
        assert document["payload"]["alert_state"] == "not_evaluated"
        assert document["payload"]["direction"] == "a_to_b"

        with app.state.database.session_factory() as session:
            assert session.scalar(
                select(func.count()).select_from(AnalyticsGeometryEvaluatorRun)
            ) == 1
            assert session.scalar(
                select(func.count()).select_from(AnalyticsEvent)
            ) == 1
            assert session.scalar(
                select(func.count())
                .select_from(StreamEventOutbox)
                .where(
                    StreamEventOutbox.event_type
                    == "hcam.analytics.line.crossing.v1"
                )
            ) == 1
            assert session.scalar(
                select(func.count()).select_from(AnalyticsTrackRuleState)
            ) == 1

        with app.state.database.session_factory() as session, session.begin():
            deleted = purge_expired_geometry_events(
                session,
                now=utc_now() + timedelta(hours=169),
            )
        assert deleted == 1
        with app.state.database.session_factory() as session:
            assert session.scalar(
                select(func.count()).select_from(AnalyticsEvent)
            ) == 0
            assert session.scalar(
                select(func.count())
                .select_from(StreamEventOutbox)
                .where(
                    StreamEventOutbox.event_type
                    == "hcam.analytics.line.crossing.v1"
                )
            ) == 0
    finally:
        app.state.settings = original_settings
