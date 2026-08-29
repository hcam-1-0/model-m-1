from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "python-ci.yml"
UPLOAD_ARTIFACT_SHA = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
SETUP_UV_SHA = "20cfd1bf945f4377ade1205e4dbc17946fc9a30d"
POSTGIS_IMAGE = (
    "postgis/postgis:18-3.6-alpine@sha256:"
    "eb2e8b8afd9b0ecee83bc20fd01aca62a5071bada2c0f38763174b653f8eed42"
)
SOURCE_REPOSITORY_EXPRESSION = (
    "${{ github.event.pull_request.head.repo.full_name || github.repository }}"
)
SOURCE_SHA_EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _job(content: str, name: str) -> str:
    match = re.search(
        rf"^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"workflow job not found: {name}"
    return match.group("body")


def test_publication_evidence_uploads_use_verified_immutable_action() -> None:
    workflow = _workflow()
    pinned_action = f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA} # v7.0.1"

    assert workflow.count(pinned_action) == 2
    assert "actions/upload-artifact@v" not in workflow
    assert workflow.count("retention-days: 7") == 2
    assert workflow.count("if-no-files-found: error") == 2
    assert workflow.count(f"repository: {SOURCE_REPOSITORY_EXPRESSION}") == 2
    assert workflow.count(f"ref: {SOURCE_SHA_EXPRESSION}") == 2


def test_python_jobs_use_pinned_uv_and_the_reviewed_lock() -> None:
    workflow = _workflow()
    pinned_action = f"astral-sh/setup-uv@{SETUP_UV_SHA} # v10.0.1"

    assert workflow.count(pinned_action) == 5
    assert "astral-sh/setup-uv@v" not in workflow
    assert workflow.count('version: "0.12.3"') == 5
    assert workflow.count("cache-dependency-glob: uv.lock") == 5
    assert workflow.count("uv sync --locked") == 5
    assert "pip install -e" not in workflow


def test_package_job_builds_and_installs_from_locked_hashes() -> None:
    job = _job(_workflow(), "package-build")

    assert "uv sync --locked --extra dev" in job
    assert "python -m build --no-isolation" in job
    assert "uv export --locked --no-dev --no-emit-project" in job
    assert "pip install --require-hashes" in job
    assert "pip install --no-deps dist/*.whl" in job


def test_postgres_job_generates_commit_named_p2_g1_artifact() -> None:
    job = _job(_workflow(), "postgres-integration")

    assert f"image: {POSTGIS_IMAGE}" in job
    assert "HCAM_POSTGRES_TEST_URL:" in job
    assert "phase2_publication_evidence.py postgres" in job
    assert "--confirm-disposable-database" in job
    assert "--output var/evidence/p2-g1.json" in job
    assert f"repository: {SOURCE_REPOSITORY_EXPRESSION}" in job
    assert f"ref: {SOURCE_SHA_EXPRESSION}" in job
    assert f"name: phase2-p2-g1-{SOURCE_SHA_EXPRESSION}" in job
    assert "path: var/evidence/p2-g1.json" in job
    assert "alembic downgrade base &&" not in job
    assert "pytest -q -m postgres" not in job
    assert "uv sync --locked --extra dev --extra postgres" in job


def test_compose_job_generates_evidence_and_keeps_defensive_cleanup() -> None:
    job = _job(_workflow(), "phase2-synthetic-lab")

    assert "phase2_publication_evidence.py compose" in job
    assert "--confirm-synthetic-lab" in job
    assert "--output var/evidence/p2-g2.json" in job
    assert f"repository: {SOURCE_REPOSITORY_EXPRESSION}" in job
    assert f"ref: {SOURCE_SHA_EXPRESSION}" in job
    assert f"name: phase2-p2-g2-{SOURCE_SHA_EXPRESSION}" in job
    assert "path: var/evidence/p2-g2.json" in job
    assert "name: Stop the disposable stack\n        if: always()" in job
    assert "tools/phase2_lab.py stop" in job
    assert "docker compose -f deploy/compose.phase2.yaml down" not in job
    assert job.index("name: Stop the disposable stack") < job.index(
        "name: Upload P2-G2 publication evidence"
    )
    assert "phase2_lab.py start" not in job
    assert "phase2_failure_drill.py" not in job
    assert "uv sync --locked --extra dev" in job


def test_publication_jobs_retain_read_only_repository_permissions() -> None:
    workflow = _workflow()

    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow
    assert "pull-requests: write" not in workflow
