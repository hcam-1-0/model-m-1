# Phase 1 Deployment Validation

These artifacts validate packaging and runtime controls for the metadata-only
camera registry. They are not a production deployment or authorization to
connect CCTV, Government systems, biometrics, or real watchlists.

## Image Properties

- immutable multi-architecture Python 3.12 base-image digest;
- wheel installation into a minimal runtime stage;
- explicit non-root UID and GID `10001`;
- PostgreSQL driver included without database credentials;
- Alembic migration files available to a separate migration process;
- liveness-only image health check and exec-form server command;
- bounded local JSON log rotation in the Compose validation stack;
- no source fixtures, tests, local databases, `.env` files, or Git metadata in
  the build context.

The image defaults to `HCAM_ENVIRONMENT=production`, which requires an explicit
`HCAM_DATABASE_URL` or `HCAM_DATABASE_URL_FILE`. It does not run migrations at
API startup. A deployment controller must run the migration command once before
starting or rolling out API replicas.

## Local Validation Stack

The Compose file is a disposable engineering stack using PostgreSQL 18,
mounted secret files, a one-shot migration service, and the non-root API image.
It deliberately enables the local development identity adapter and therefore
must not be exposed beyond loopback or treated as production authentication.

Create three untracked files outside the repository:

```powershell
$secretRoot = Join-Path $env:TEMP "hcam-phase1-secrets"
New-Item -ItemType Directory -Force $secretRoot | Out-Null
Set-Content -NoNewline "$secretRoot\postgres-password" "replace-with-random-local-value"
Set-Content -NoNewline "$secretRoot\database-url" "postgresql+psycopg://hcam_phase1:replace-with-random-local-value@database:5432/hcam_phase1"
Set-Content -NoNewline "$secretRoot\metrics-token" "replace-with-at-least-32-random-characters"
$env:HCAM_POSTGRES_PASSWORD_FILE = "$secretRoot\postgres-password"
$env:HCAM_DATABASE_URL_SECRET_FILE = "$secretRoot\database-url"
$env:HCAM_METRICS_TOKEN_SECRET_FILE = "$secretRoot\metrics-token"
docker compose -f deploy/compose.phase1.yaml config -q
docker compose -f deploy/compose.phase1.yaml up --build --wait
```

Validate liveness, readiness, and protected metrics:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-RestMethod http://127.0.0.1:8000/health/ready
$token = Get-Content -Raw $env:HCAM_METRICS_TOKEN_SECRET_FILE
Invoke-WebRequest http://127.0.0.1:8000/internal/metrics -Headers @{Authorization="Bearer $token"}
```

Stop the stack with `docker compose -f deploy/compose.phase1.yaml down`. Add
`--volumes` only when intentionally deleting the disposable validation data.

Docker Compose secrets reduce accidental exposure through committed files and
service environment blocks. They do not replace an approved production secret
manager, rotation policy, workload identity, TLS, network policy, or access
audit.

Secret and recovery files use owner-only modes on POSIX systems. On Windows,
place them in an ACL-restricted directory because POSIX mode bits do not provide
equivalent access control.

## Phase 2 Capability Worker

`deploy/compose.phase2.yaml` adds one capability worker and mounts
`deploy/onvif-egress.phase2.json` read-only. The lab enables HTTP only for the
exact synthetic simulator hostname and private Docker IPv4/IPv6 ranges. The
worker performs read-only ONVIF metadata operations and persists normalized
change snapshots; it never captures images or records video.

Production must use verified HTTPS, the smallest approved device address
ranges, infrastructure egress controls, and an approved external implementation
of `CameraSecretProvider`. `HCAM_CAMERA_SECRET_PROVIDER=file` and
`HCAM_ONVIF_LAB_HTTP_ENABLED=true` are rejected in production.
