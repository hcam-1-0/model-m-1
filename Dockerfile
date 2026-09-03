# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
ARG UV_VERSION=0.12.3

FROM ${PYTHON_IMAGE} AS builder

ARG UV_VERSION

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build

COPY pyproject.toml README.md uv.lock ./
COPY app ./app
RUN mkdir -p /dist \
    && python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && uv sync --locked --extra dev --no-install-project \
    && uv export --locked --no-dev --extra analytics --extra postgres --no-emit-project \
        --format requirements-txt --output-file /dist/requirements.txt \
    && uv run --locked --extra dev python -m build --no-isolation \
        --wheel --outdir /dist

FROM ${PYTHON_IMAGE} AS runtime

ARG HCAM_UID=10001
ARG HCAM_GID=10001
ARG VCS_REF=unknown

LABEL org.opencontainers.image.title="H-CAM Core" \
      org.opencontainers.image.description="Phase 2 camera and video ingestion foundation" \
      org.opencontainers.image.source="https://github.com/hcam-1-0/model-m-1" \
      org.opencontainers.image.revision="${VCS_REF}"

ENV HCAM_ENVIRONMENT=production \
    PATH="/opt/hcam/.local/bin:${PATH}" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${HCAM_GID}" hcam \
    && useradd --uid "${HCAM_UID}" --gid "${HCAM_GID}" --no-log-init \
        --home-dir /opt/hcam --shell /usr/sbin/nologin hcam \
    && mkdir -p /opt/hcam /var/lib/hcam \
    && chown -R "${HCAM_UID}:${HCAM_GID}" /opt/hcam /var/lib/hcam

WORKDIR /opt/hcam
COPY --from=builder /dist /tmp/dist
RUN python -m pip install --no-cache-dir --require-hashes \
        --requirement /tmp/dist/requirements.txt \
    && python -m pip install --no-cache-dir --no-deps /tmp/dist/*.whl \
    && rm -rf /tmp/dist
COPY --chown=${HCAM_UID}:${HCAM_GID} alembic.ini ./alembic.ini
COPY --chown=${HCAM_UID}:${HCAM_GID} migrations ./migrations

USER ${HCAM_UID}:${HCAM_GID}
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/live', timeout=3).read()"]

CMD ["python", "-m", "uvicorn", "hcam.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
