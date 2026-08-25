from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "python-ci.yml"
UPLOAD_ARTIFACT_SHA = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
SETUP_UV_SHA = "c771a70e6277c0a99b617c7a806ffedaca235ff9"
POSTGRES_IMAGE = (
    "postgres:18-alpine@sha256:"
    "d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2"
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
    pinned_action = f"astral-sh/setup-uv@{SETUP_UV_SHA} # v9.0.0"

    assert workflow.count(pinned_action) == 6
    assert "astral-sh/setup-uv@v" not in workflow
    assert workflow.count('version: "0.12.3"') == 6
    assert workflow.count("cache-dependency-glob: uv.lock") == 6
    assert workflow.count("uv sync --locked") == 6
    assert "pip install -e" not in workflow


def test_package_job_builds_and_installs_from_locked_hashes() -> None:
    job = _job(_workflow(), "package-build")

    assert "uv sync --locked --extra dev" in job
    assert "python -m build --no-isolation" in job
    assert "uv export --locked --extra analytics --no-dev --no-emit-project" in job
    assert "pip install --require-hashes" in job
    assert "pip install --no-deps dist/*.whl" in job


def test_postgres_job_generates_commit_named_p2_g1_artifact() -> None:
    job = _job(_workflow(), "postgres-integration")

    assert f"image: {POSTGRES_IMAGE}" in job
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
