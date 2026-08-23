# Phase 1 Security And Registry Management

This document defines the Phase 1 identity boundary and write-management
contract. It does not provide a production identity provider.

## Fail-Closed Authentication

Camera registry endpoints fail with `503` unless an authenticator is explicitly
configured. Health endpoints remain available so deployment systems can
distinguish process health from application readiness.

Phase 1 includes one local-only authenticator for deterministic laptop testing.
It is enabled only when both conditions are true:

- `HCAM_DEV_AUTH_ENABLED=true`
- `HCAM_ENVIRONMENT` is `development` or `test`

Application construction fails if local development authentication is enabled
in `production`. The local headers are assertions supplied by the developer;
they are not credentials and must never be accepted by an internet-facing or
production deployment.

Local headers:

| Header | Purpose |
| --- | --- |
| `X-HCAM-Actor` | Stable local test actor identifier |
| `X-HCAM-Roles` | Comma-separated role assertions |
| `X-HCAM-Departments` | Comma-separated department scopes or `*` |
| `X-HCAM-Reason` | Mandatory reason for write and import operations |

## Role Matrix

| Capability | `camera.viewer` | `camera.editor` | `platform.admin` |
| --- | --- | --- | --- |
| List permitted cameras | Yes | Yes | Yes |
| Read permitted camera | Yes | Yes | Yes |
| Create camera | No | Within department scope | Yes |
| Update camera | No | Within department scope | Yes |
| Bulk API import | No | No | Yes |

Out-of-scope camera details return `404` instead of revealing that the camera
exists. A scoped user cannot create a camera without a permitted department or
move an existing camera outside their department scope.

## Registry Write Contract

### Create

`POST /cameras` creates one normalized camera and returns:

- `201 Created`
- a `Location` header
- an `ETag` containing version `1`
- the normalized camera response

Stable camera ID, source ID, and external ID are immutable after creation.
Duplicate identities return `409 Conflict`.

### Update

`PATCH /cameras/{camera_id}` performs a partial update. It requires the current
camera ETag in `If-Match`.

- missing `If-Match`: `428 Precondition Required`
- malformed `If-Match`: `400 Bad Request`
- stale version: `412 Precondition Failed`
- successful update: incremented version and new `ETag`

SQLAlchemy mapper versioning provides a second concurrency check during the
database flush. This prevents a stale process from silently overwriting a
newer registry record.

### Bulk API Import

`POST /camera-imports` accepts `hcam.camera_registry.seed.v1` JSON for an
authorized administrator. The synchronous Phase 1 endpoint is limited to 1,000
cameras. Larger imports require a future queued job contract rather than a
long-running HTTP request.

The local CLI remains available for controlled administrative imports:

```powershell
.\.venv\Scripts\hcam import-registry tests/fixtures/camera-registry-seed.json
```

## Audit Contract

Successful create, update, and bulk import operations record:

- actor ID
- action
- target type and target ID
- UTC timestamp
- source
- mandatory reason
- outcome
- minimal structured context

Audit context does not include stream credentials, query tokens, request bodies,
or raw CCTV data. Registry data and its audit event commit in the same database
transaction for create and update operations.

## Stream Reference Handling

Only relative paths and `http`, `https`, `rtsp`, or `rtsps` references are
accepted for normalized storage. User information, passwords, query strings,
and fragments are removed before persistence and before API responses.

This sanitization is not a secret vault. Future production adapters must store
credentials in a dedicated secret manager and reference them by opaque secret
ID rather than embedding credentials in registry URLs.

Successful registry responses use `Cache-Control: no-store` and vary on identity
headers so camera metadata is not retained or mixed by HTTP caches. Request
bodies are capped at 8 MiB by default, including streamed bodies without a
`Content-Length` header. Override the cap only with a positive
`HCAM_MAX_REQUEST_BODY_BYTES` value and a documented deployment reason.

Every response also receives a validated `X-Request-ID`. Mutation audit events
store that same identifier so an authorized reviewer can correlate an API
outcome with its audit record. Structured application access events contain
only request ID, method, route template, status, and duration; they exclude
query strings, bodies, headers, identity claims, client addresses, camera IDs,
stream references, and exception text. See
[operations-and-observability.md](operations-and-observability.md).

## Configuration And Metrics Secrets

Database URLs may be provided through `HCAM_DATABASE_URL_FILE`; direct and
file-based database configuration cannot be enabled together. The internal
Prometheus endpoint is disabled by default and, when enabled, requires a
32-to-256-character bearer value loaded from `HCAM_METRICS_TOKEN_FILE`.

Settings representations redact both values. Metrics use route templates and
status classes rather than camera IDs, actors, departments, queries, headers,
or client addresses. The scrape credential is a narrow service secret, not a
human identity or replacement for the future production identity provider.

Mounted files are an integration boundary for Docker, Kubernetes, or a future
secret manager. Phase 1 does not implement secret creation, distribution,
rotation, revocation, or production vault policy.

## Production Identity Requirements

Before production use, replace the local authenticator with an approved OpenID
Connect or equivalent Government identity integration that provides:

- cryptographic token validation using issuer and audience restrictions
- short token lifetimes and key rotation
- stable subject identifiers
- centrally managed role and department claims
- account disablement and access-revocation propagation
- MFA policy at the identity provider
- service identities separated from human users
- emergency access with approval, expiry, and enhanced auditing
- immutable security audit export to an authorized monitoring system

No production identity integration is authorized or implemented in Phase 1.
