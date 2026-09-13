from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from hcam.intelligence.correlation.metrics import CorrelationMetrics
from hcam.intelligence.guardrails import IntelligenceGuardrailError, validate_intelligence_document
from hcam.main import create_app
from hcam.settings import Settings


CORRELATION_SOURCE = Path("app/hcam/intelligence/correlation")


def test_generated_correlation_defaults_off_and_production_rejects_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HCAM_INTELLIGENCE_GENERATED_CORRELATION_ENABLED", raising=False)
    assert Settings.from_environment().intelligence_generated_correlation_enabled is False
    monkeypatch.setenv("HCAM_INTELLIGENCE_GENERATED_CORRELATION_ENABLED", "true")
    assert Settings.from_environment().intelligence_generated_correlation_enabled is True
    with pytest.raises(ValueError, match="P4.1 correlation runtime"):
        Settings(
            database_url="postgresql+psycopg://localhost/generated-only",
            environment="production",
            intelligence_generated_correlation_enabled=True,
        )


def test_correlation_configuration_bounds_fail_closed() -> None:
    with pytest.raises(ValueError, match="EVENTS_PER_BATCH"):
        Settings(correlation_events_per_batch=1_001)
    with pytest.raises(ValueError, match="LEASE_SECONDS"):
        Settings(correlation_worker_lease_seconds=91)
    with pytest.raises(ValueError, match="RETRY_ATTEMPTS"):
        Settings(correlation_retry_attempts=4)


def test_guardrails_reject_prohibited_content_and_oversized_documents() -> None:
    with pytest.raises(IntelligenceGuardrailError, match="prohibited field"):
        validate_intelligence_document({"password": "generated-placeholder"})
    with pytest.raises(IntelligenceGuardrailError, match="prohibited locator"):
        validate_intelligence_document({"value": "rtsp://generated.invalid/stream"})
    with pytest.raises(ValueError, match="size limit"):
        validate_intelligence_document({"value": "x" * 65_536})


def test_metrics_reject_unbounded_labels() -> None:
    metrics = CorrelationMetrics()
    with pytest.raises(ValueError, match="receipt metric"):
        metrics.record_receipt("generated-camera-id")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="hypothesis metric"):
        metrics.record_hypothesis("hyp_deadbeef")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="queue depth"):
        metrics.set_queue_depth(-1)
    with pytest.raises(ValueError, match="run metric"):
        metrics.record_run("camera-specific")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="window metric"):
        metrics.record_window("camera-specific")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duration"):
        metrics.observe_duration(-0.1)
    metrics.set_queue_depth(2)
    metrics.observe_duration(9.0)
    assert metrics.snapshot()["correlation_queue_depth"] == 2
    assert metrics.snapshot()["correlation_duration_seconds:gt_5"] == 1


def test_correlation_modules_have_no_network_media_model_or_subprocess_imports() -> None:
    prohibited = {
        "cv2",
        "ffmpeg",
        "httpx",
        "onnx",
        "onnxruntime",
        "requests",
        "socket",
        "subprocess",
        "torch",
        "ultralytics",
    }
    imported: set[str] = set()
    for path in CORRELATION_SOURCE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(prohibited)


def test_database_constraints_block_operational_correlation_records(
    tmp_path: Path,
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase41-security.db').as_posix()}",
            create_schema=True,
            environment="test",
            access_log_enabled=False,
        )
    )
    application.state.database.create_schema()
    try:
        with application.state.database.session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO correlation_lane_results "
                        "(lane_result_id, hypothesis_id, department, lane, status, "
                        "payload, lineage_digest, generated_fixture_result, "
                        "generated_only, operational) VALUES "
                        "('lres_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', "
                        "'hyp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'generated-lab', "
                        "'deterministic_cpu', 'completed', '{}', "
                        "'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', "
                        "0, 1, 1)"
                    )
                )
                session.commit()
    finally:
        application.state.database.dispose()


def test_application_does_not_construct_or_start_a_correlation_worker(
    tmp_path: Path,
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase41-startup.db').as_posix()}",
            create_schema=True,
            environment="test",
            intelligence_generated_correlation_enabled=True,
        )
    )
    try:
        assert not hasattr(application.state, "correlation_worker")
    finally:
        application.state.database.dispose()
