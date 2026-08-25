#!/usr/bin/env python3
"""Run the approved P3.2 generated-only API path against a local model artifact."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.analytics.activation import (
    P3_2_APPROVAL_RECORD_ID,
    P3_2_MODEL_ID,
    P3_2_MODEL_VERSION,
    P3_2_PIPELINE_ID,
    P3_2_PIPELINE_VERSION,
    P3_2_POLICY_VERSION,
    P3_2_TAXONOMY_VERSION,
)
from hcam.analytics.artifacts import DET_R0_BYTES, DET_R0_SHA256
from hcam.analytics.models import AnalyticsObservation
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


def _headers(reason: str) -> dict[str, str]:
    return {
        "X-HCAM-Actor": "p3-2-local-validator",
        "X-HCAM-Roles": "platform.admin",
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": reason,
    }


def _assignment_payload() -> dict[str, object]:
    return {
        "capability": "object_detection",
        "desired_state": "paused",
        "pipeline": {"id": P3_2_PIPELINE_ID, "version": P3_2_PIPELINE_VERSION},
        "models": [{"id": P3_2_MODEL_ID, "version": P3_2_MODEL_VERSION}],
        "taxonomy_version": P3_2_TAXONOMY_VERSION,
        "policy_version": P3_2_POLICY_VERSION,
        "configuration_digest": "sha256:" + "d" * 64,
        "minimum_confidence": 0.25,
        "sampling_fps": 1.0,
        "maximum_queue_age_ms": 1_000,
        "geometry_refs": [],
        "retention_class": "derived.analytics.standard",
        "approval_record_id": P3_2_APPROVAL_RECORD_ID,
    }


def _upgrade(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def run_generated_e2e(artifact_root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="hcam-p3-2-") as directory:
        database_path = Path(directory) / "generated-e2e.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        _upgrade(database_url)
        application = create_app(
            Settings(
                database_url=database_url,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
                analytics_generated_runtime_enabled=True,
                analytics_artifact_root=artifact_root,
            )
        )
        try:
            application.state.database.check_ready()
            with application.state.database.session_factory() as session:
                seed_synthetic_lab(session, count=1)
            stream_id = synthetic_stream_id(1)
            with TestClient(application) as client:
                created = client.post(
                    f"/streams/{stream_id}/analytics-assignments",
                    json=_assignment_payload(),
                    headers=_headers(
                        "Register exact P3.2 generated-only validation assignment"
                    ),
                )
                created.raise_for_status()
                assignment_id = created.json()["assignment_id"]
                activated = client.post(
                    f"/analytics-assignments/{assignment_id}/activate",
                    headers={
                        **_headers(
                            "Activate exact P3.2 generated-only validation assignment"
                        ),
                        "If-Match": created.headers["ETag"],
                    },
                )
                activated.raise_for_status()
                executed = client.post(
                    f"/analytics-assignments/{assignment_id}/generated-runs",
                    json={
                        "seed": 0,
                        "sequence": 1,
                        "observed_at": "2026-08-24T12:00:00Z",
                    },
                    headers=_headers(
                        "Execute exact P3.2 generated-only validation input"
                    ),
                )
                executed.raise_for_status()
                replayed = client.post(
                    f"/analytics-assignments/{assignment_id}/generated-runs",
                    json={
                        "seed": 0,
                        "sequence": 1,
                        "observed_at": "2026-08-24T12:00:00Z",
                    },
                    headers=_headers(
                        "Replay exact P3.2 generated-only validation input"
                    ),
                )
                replayed.raise_for_status()
            with application.state.database.session_factory() as session:
                observation_count = int(
                    session.scalar(
                        select(func.count()).select_from(AnalyticsObservation)
                    )
                    or 0
                )
                observation_events = int(
                    session.scalar(
                        select(func.count())
                        .select_from(StreamEventOutbox)
                        .where(
                            StreamEventOutbox.event_type
                            == "hcam.analytics.observation.created.v1"
                        )
                    )
                    or 0
                )
            body = executed.json()
            return {
                "adapter": application.state.analytics_runtime.descriptor.adapter_id,
                "candidate_count": body["candidate_count"],
                "configured": application.state.analytics_runtime.descriptor.configured,
                "duration_ms": body["duration_ms"],
                "execution_scope": body["execution_scope"],
                "frame_leases_after_run": (
                    application.state.analytics_frame_leases.active_leases
                ),
                "idempotent_replay": replayed.json()["reused"],
                "observation_count": observation_count,
                "observation_event_count": observation_events,
                "model_artifact_bytes": DET_R0_BYTES,
                "model_artifact_sha256": DET_R0_SHA256,
                "numpy_version": version("numpy"),
                "onnx_version": version("onnx"),
                "onnxruntime_version": version("onnxruntime"),
                "python_version": ".".join(map(str, sys.version_info[:3])),
                "status": body["status"],
            }
        finally:
            application.state.database.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the local P3.2 generated-only analytics path."
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        required=True,
        help="Root containing the approved DET-R0 artifact directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = run_generated_e2e(args.artifact_root)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
