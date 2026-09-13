from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from hcam.intelligence.rules.metrics import RuleMetrics
from hcam.main import create_app
from hcam.settings import Settings


SOURCE = Path("app/hcam/intelligence/rules")


def test_generated_rule_boundary_defaults_off_and_production_rejects_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "HCAM_INTELLIGENCE_GENERATED_RULE_EVALUATION_ENABLED", raising=False
    )
    assert (
        Settings.from_environment().intelligence_generated_rule_evaluation_enabled
        is False
    )
    monkeypatch.setenv("HCAM_INTELLIGENCE_GENERATED_RULE_EVALUATION_ENABLED", "true")
    assert (
        Settings.from_environment().intelligence_generated_rule_evaluation_enabled
        is True
    )
    with pytest.raises(ValueError, match="P4.2 rule evaluation"):
        Settings(
            environment="production",
            intelligence_generated_rule_evaluation_enabled=True,
        )


def test_rule_modules_have_no_network_media_model_eval_exec_or_subprocess_imports() -> (
    None
):
    prohibited = {
        "cv2",
        "ffmpeg",
        "httpx",
        "onnx",
        "requests",
        "socket",
        "subprocess",
        "torch",
        "urllib",
    }
    imported: set[str] = set()
    calls: set[str] = set()
    for path in SOURCE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
    assert imported.isdisjoint(prohibited)
    assert calls.isdisjoint({"eval", "exec", "compile", "open", "__import__"})


def test_metrics_accept_only_low_cardinality_labels() -> None:
    metrics = RuleMetrics()
    metrics.record("compile", "succeeded")
    assert metrics.outcomes[("compile", "succeeded")] == 1
    with pytest.raises(ValueError, match="allowlisted"):
        metrics.record("generated-camera-id", "succeeded")
    with pytest.raises(ValueError, match="allowlisted"):
        metrics.record("compile", "rule-deadbeef")


def test_database_constraints_reject_active_or_operational_rule_records(
    tmp_path: Path,
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'p42-security.db').as_posix()}",
            create_schema=True,
            environment="test",
        )
    )
    application.state.database.create_schema()
    try:
        with application.state.database.session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO intelligence_rule_lifecycle_events (event_id, rule_record_id, department, from_status, to_status, actor_id, reason_code, occurred_at, generated_only, operational) VALUES ('rlfe_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'irlr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'generated-lab', 'draft', 'active', 'generated-owner', 'generated_test', CURRENT_TIMESTAMP, 1, 0)"
                    )
                )
                session.commit()
        with application.state.database.session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO intelligence_rule_shadow_comparisons (comparison_id, rule_record_id, department, candidate_compilation_id, baseline_compilation_id, candidate_matches, baseline_matches, disagreement_count, comparison_digest, generated_only, operational, created_at) VALUES ('rshd_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'irlr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'generated-lab', 'rcmp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'rcmp_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 1, 1, 0, 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 1, 1, CURRENT_TIMESTAMP)"
                    )
                )
                session.commit()
    finally:
        application.state.database.dispose()


def test_application_does_not_construct_or_start_a_rule_worker(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'p42-startup.db').as_posix()}",
            create_schema=True,
            environment="test",
            intelligence_generated_rule_evaluation_enabled=True,
        )
    )
    try:
        assert not hasattr(application.state, "rule_worker")
        assert not hasattr(application.state, "rule_scheduler")
    finally:
        application.state.database.dispose()
