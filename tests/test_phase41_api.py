from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import CorrelationIngressEventV1, CorrelationProfileV1
from hcam.intelligence.correlation.persistence import CorrelationPersistence
from hcam.intelligence.correlation.runtime import run_generated_batch
from hcam.main import create_app
from hcam.settings import Settings


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _headers(department: str = "generated-lab") -> dict[str, str]:
    return {
        "X-HCAM-Actor": "phase41-viewer",
        "X-HCAM-Roles": "intelligence.viewer",
        "X-HCAM-Departments": department,
    }


def _application(tmp_path: Path, *, enabled: bool = True) -> FastAPI:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase41-api.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_correlation_enabled=enabled,
        )
    )
    application.state.database.create_schema()
    return application


def _stored_batch(application: FastAPI):
    profile = CorrelationProfileV1(
        profile_id="api-profile",
        profile_version=canonical_sha256({"profile": "api"}),
        allowed_event_types=["hcam.analytics.observation.created.v1"],
        subject_kind="vehicle",
        partition_dimensions=["generated_reference"],
        window_seconds=10,
        allowed_lateness_seconds=1,
        minimum_supporting_events=2,
        maximum_events_per_window=100,
        maximum_active_windows=8,
    )

    def event(identifier: int, seconds: int) -> CorrelationIngressEventV1:
        instant = BASE + timedelta(seconds=seconds)
        return CorrelationIngressEventV1(
            event_id=f"api-event-{identifier}",
            event_type="hcam.analytics.observation.created.v1",
            schema_version=1,
            department="generated-lab",
            stream_id="str_" + "6" * 32,
            camera_id="cam-6",
            profile_id=profile.profile_id,
            subject_kind="vehicle",
            signals={
                "object_class": "car",
                "confidence": 0.9,
                "generated_reference": "vehicle-a",
                "source_sequence": identifier,
            },
            chronology={
                "occurred_at": instant,
                "observed_at": instant,
                "received_at": instant,
                "recorded_at": instant,
            },
        )

    result = run_generated_batch(
        [event(1, 1), event(2, 2), event(3, 20)],
        profile,
    )
    with application.state.database.session_factory() as session:
        CorrelationPersistence(session).store_batch(result)
    return result


def test_read_only_correlation_surfaces_are_scoped_and_no_store(tmp_path: Path) -> None:
    application = _application(tmp_path)
    result = _stored_batch(application)
    hypothesis = result.hypotheses[0]
    try:
        with TestClient(application) as client:
            runs = client.get("/correlation-runs", headers=_headers())
            assert runs.status_code == 200
            assert runs.headers["cache-control"] == "no-store"
            assert runs.json()["items"][0]["run_id"] == result.run_id
            assert runs.json()["items"][0]["operational"] is False

            run = client.get(f"/correlation-runs/{result.run_id}", headers=_headers())
            assert run.status_code == 200
            assert run.json()["accepted_count"] == 3

            listed = client.get("/correlation-hypotheses", headers=_headers())
            assert listed.status_code == 200
            assert listed.json()["items"][0]["contract_type"] == (
                "hcam.intelligence.correlation-hypothesis.v2"
            )

            graph = client.get(
                f"/correlation-hypotheses/{hypothesis.hypothesis_id}/graph",
                headers=_headers(),
            )
            assert graph.status_code == 200
            assert graph.json()["graph_digest"] == hypothesis.graph_digest

            projection = client.get(
                f"/correlation-hypotheses/{hypothesis.hypothesis_id}/projection",
                headers=_headers(),
            )
            assert projection.status_code == 200
            assert projection.json()["projection"]["graph_digest"] == hypothesis.graph_digest

            revisions = client.get(
                f"/correlation-hypotheses/{hypothesis.hypothesis_id}/revisions",
                headers=_headers(),
            )
            assert revisions.status_code == 200
            assert revisions.json()["total"] == 1
            assert revisions.json()["items"][0]["new_state"] == hypothesis.state

            hidden = client.get(
                f"/correlation-runs/{result.run_id}",
                headers=_headers("another-department"),
            )
            assert hidden.status_code == 404
    finally:
        application.state.database.dispose()


def test_p41_routes_are_absent_when_disabled_and_have_no_runtime_mutations(
    tmp_path: Path,
) -> None:
    disabled = _application(tmp_path, enabled=False)
    try:
        with TestClient(disabled) as client:
            assert client.get("/correlation-runs", headers=_headers()).status_code == 404
    finally:
        disabled.state.database.dispose()

    enabled = _application(tmp_path)
    try:
        paths = enabled.openapi()["paths"]
        assert set(paths["/correlation-runs"]) == {"get"}
        assert set(paths["/correlation-runs/{run_id}"]) == {"get"}
        assert set(paths["/correlation-hypotheses/{hypothesis_id}/graph"]) == {"get"}
        assert set(paths["/correlation-hypotheses/{hypothesis_id}/projection"]) == {"get"}
        assert set(paths["/correlation-hypotheses/{hypothesis_id}/revisions"]) == {"get"}
        serialized = str(paths).lower()
        assert "correlation-start" not in serialized
        assert "correlation-replay" not in serialized
        assert "correlation-correction" not in serialized
    finally:
        enabled.state.database.dispose()
