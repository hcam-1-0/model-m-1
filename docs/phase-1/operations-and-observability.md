# Phase 1 Operations And Observability

This document defines the operational controls added to the local camera
registry foundation. They handle metadata only and do not authorize live CCTV,
video storage, Government data, or production deployment.

## File-Mounted Secrets

`HCAM_DATABASE_URL_FILE` supplies the database URL from a UTF-8, single-value
file. It is mutually exclusive with `HCAM_DATABASE_URL`. Production environment
loading fails when neither is explicitly provided. `HCAM_METRICS_TOKEN_FILE`
is the only environment-loading path for the internal scrape credential.

Secret files are limited to 16 KiB and reject empty, multiline, NUL-containing,
or invalid UTF-8 content. Database URLs and metrics tokens are excluded from
the settings representation. File mounting limits accidental environment and
repository exposure; an approved deployment must still provide a secret
manager, access policy, encryption, rotation, revocation, and audit.

## Request Correlation

Every HTTP response includes `X-Request-ID`.

- A caller-provided ID is accepted only when it is 1 to 128 ASCII characters
  using letters, numbers, `.`, `_`, `:`, or `-`.
- Invalid or missing IDs are replaced with a generated UUID and are never
  reflected back.
- Camera create, update, and API import audit events record the validated
  request ID in their structured context.
- Request IDs correlate API responses, access events, and mutation audits; they
  are not credentials and must not contain sensitive information.

The `hcam.access` logger emits one JSON event after each HTTP request. Fields are
limited to request ID, HTTP method, route template, response status, and elapsed
milliseconds. It does not log query strings, request or response bodies,
headers, actor claims, client addresses, stream references, camera IDs, or
exception text. Route templates such as `/cameras/{camera_id}` prevent entity
identifiers from entering access logs.

Unhandled exceptions produce a separate `hcam.error` JSON event containing the
request ID, method, route template, and exception class only. The exception
message and request data are excluded, and the caller receives a generic
correlated `500` response.

Set `HCAM_ACCESS_LOG_ENABLED=false` to suppress these application access events
while retaining request IDs. Invalid boolean values fail application startup.
Uvicorn access logging is separately configured by the deployment command.

## SQLite Backup

The Phase 1 CLI provides online backup and recovery checks for the local SQLite
database:

```powershell
hcam backup-database .\backups\hcam-phase1.db
hcam verify-backup .\backups\hcam-phase1.db
hcam restore-backup .\backups\hcam-phase1.db .\var\hcam-restored.db
```

`backup-database` uses SQLite's online backup API. Before publishing output, it
checks database integrity, foreign keys, required tables, and the exact Alembic
revision. It creates a sidecar file named `<backup>.manifest.json` containing:

- format identifier and UTC creation time;
- SHA-256 digest and byte size;
- Alembic revision;
- camera and audit-event counts.

The manifest contains no database URL, registry records, stream references, or
user information. A backup and manifest are created only when neither output
already exists. Existing paths are never overwritten. On POSIX systems the
published database and manifest are restricted to owner read/write permissions.

`verify-backup` re-runs SQLite integrity, foreign-key, schema-revision, size,
record-count, and SHA-256 checks. `restore-backup` requires a valid manifest and
writes only to a new file. It refuses the configured active database, the
backup file itself, and any existing destination. Operators must separately
protect backup confidentiality, storage permissions, retention, off-device
copies, and encryption according to the approved deployment policy.

The SHA-256 manifest detects accidental corruption or a changed backup only
when the manifest itself remains trusted. It is not a digital signature or
message-authentication code and cannot prove authenticity if an attacker can
replace both files. Production backups require approved signing or immutable
storage controls in addition to encryption and access control.

These commands intentionally reject PostgreSQL URLs. PostgreSQL backup and
restore require deployment-specific tools, credentials, retention, encryption,
and recovery procedures and are not implemented by this local Phase 1 CLI.

## PostgreSQL Compatibility

The optional package extra installs Psycopg 3:

```powershell
uv sync --locked --extra dev --extra postgres
```

CI starts an isolated PostgreSQL 18 service with synthetic credentials, applies
all Alembic migrations, checks for model drift, imports the synthetic registry,
exercises readiness/list/create/update/audit behavior, and completes a full
downgrade and re-upgrade. No external database is contacted.

The connection URL uses the explicit `postgresql+psycopg://` dialect documented
by [SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).
Psycopg's binary package is used for deterministic CI installation according to
its [official installation guidance](https://www.psycopg.org/psycopg3/docs/basic/install.html).
The service follows [GitHub Actions' PostgreSQL service-container pattern](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers).

Passing this integration job proves the current Phase 1 schema and API contract
work on that isolated PostgreSQL version. It does not prove production sizing,
high availability, backup policy, TLS, identity, or deployment approval.

## Synthetic Performance Smoke

Run the bounded smoke test:

```powershell
python tools/phase1_performance.py --cameras 1000 --iterations 100 --json
```

The tool generates registry metadata in a temporary SQLite database, imports
it, warms the API, and measures list and detail requests. It uses no video,
network camera, Sentinel endpoint, Government data, or persistent output. CI
requires the import to finish within 20 seconds and list/detail p95 latency to
remain below 750 milliseconds.

These thresholds detect severe regressions on CI runners. They are not a
production service-level objective, load test, concurrency test, capacity
claim, or evidence for city-scale deployment. Production performance criteria
require approved hardware, realistic metadata volumes, concurrent workloads,
PostgreSQL tuning, and a separately reviewed test plan.

## Concurrent Loopback Load Smoke

Run the bounded concurrent test:

```powershell
python tools/phase1_load.py --cameras 1000 --requests 400 --concurrency 16 --json
```

The tool starts a real Uvicorn server on an ephemeral loopback port, imports
generated metadata into a temporary SQLite database, and mixes list and detail
requests through 16 worker threads. CI permits no request errors and requires
aggregate p95 latency below 1,500 milliseconds. It closes the listener,
database, temporary directory, and worker thread after the run.

This is a bounded concurrency regression check. It uses no external network,
video, Government data, or durable output and is not evidence of production
throughput, write contention, PostgreSQL sizing, or city-scale capacity.

## Recovery Exercise

The automated suite creates a migrated database, imports the two-camera
synthetic fixture, creates and verifies a backup, restores it to a new path,
checks record counts, and runs application readiness against the restored file.
It also verifies backup/manifest mismatch detection and overwrite refusal.

Run an operator-visible drill against the configured SQLite database:

```powershell
hcam recovery-drill .\backups\drill-2026-08-18 --max-recovery-seconds 60
```

The destination must not exist. The command exclusively creates backup,
manifest, restored database, and `report.json` artifacts; then verifies the
restored application database and records measured recovery time. On POSIX,
the directory uses mode `0700` and files use mode `0600`; Windows operators
must choose an ACL-restricted destination. It returns nonzero when the
objective is missed or any operation fails. The report omits database URLs,
absolute paths, camera records, and user information.

The measured time covers one local SQLite snapshot, verification, restore, and
readiness check. It is not a production recovery-time or recovery-point claim.
A real deployment still requires a scheduler, off-device encrypted copies,
retention, PostgreSQL-specific recovery, failure-domain testing, operator
approval records, and approved RTO/RPO values.

## Metrics And Deployment Validation

Protected Prometheus metrics, bounded labels, dashboard queries, and objective
limits are defined in [service-objectives.md](service-objectives.md). The
digest-pinned non-root image and disposable PostgreSQL validation stack are
defined in [deployment validation](../../deploy/README.md).

The metrics implementation follows the official
[Prometheus Python client](https://prometheus.github.io/client_python/) model.
The container follows Docker's
[non-root `USER` guidance](https://docs.docker.com/build/building/best-practices/)
and FastAPI's
[container deployment guidance](https://fastapi.tiangolo.com/deployment/docker/).
