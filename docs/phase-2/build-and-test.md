# Build and Test

## Offline Checks

```powershell
uv sync --locked --extra dev --extra postgres
uv lock --check
uv run --locked --extra dev --extra postgres python -m compileall -q app tools migrations
uv run --locked --extra dev --extra postgres ruff check app tests tools migrations
uv run --locked --extra dev --extra postgres python tools/release_contracts.py check
uv run --locked --extra dev --extra postgres pytest --cov=hcam --cov-branch --cov-report=term-missing --cov-fail-under=90
$env:HCAM_DATABASE_URL = "sqlite:///./var/phase2-check.db"
uv run --locked --extra dev --extra postgres python -m alembic upgrade head
uv run --locked --extra dev --extra postgres python -m alembic check
uv run --locked --extra dev --extra postgres python tools/phase2_readiness.py --run-validation
uv run --locked --extra dev --extra postgres python tools/phase2_publication_evidence.py preflight
```

`uv.lock` is the single reviewed dependency graph for local validation, CI,
package artifacts, and the runtime image. CI pins both the `setup-uv` action
commit and uv `0.12.3`; the Docker build exports locked PostgreSQL runtime
dependencies with hashes and installs the project wheel without re-resolving.

Tests cover API authorization and ETags, locator sanitization, migration,
FFprobe parsing, output limits, fail-closed egress, all four ONVIF auth modes,
WSSE replay rejection, HTTP Digest, real TLS/private CA with pinned DNS and SNI,
secret rotation and confinement, hostile returned URLs, partial discovery,
durable pre-action audit intent, completion-audit failure recovery,
atomic synchronous-discovery lifecycle and snapshot rollback,
reviewed OpenAPI and migrated-schema drift detection,
cache/history/freshness and 90-day pruning that preserves latest inventory,
completion-anchored cooldown, active-job deduplication under concurrent queue
races, retries, lease recovery, RBAC/department scope, synchronous
compatibility, audited preflight terminalization without camera contact,
read-only imaging, bounded event subscriptions, PTZ auto-stop,
controller-role separation, control leases, private-CIDR discovery filtering,
50-stream scheduled load, PostgreSQL concurrent claims, queue admission, and
retention semantics,
outbox delivery, playback scope, and Compose safety.

The 2026-08-21 local run passed 413 tests with four expected PostgreSQL-URL
skips and 90.42% branch coverage. Compile, Ruff, Phase 1
regression, SQLite migration upgrade/drift, lab prepare, lab configuration,
and `git diff --check` all passed. Readiness has zero automated failures;
`--strict` intentionally exits `2` while the grouped extension publication
gate remains open.

Publication readiness also validates the named `P2-G1` through `P2-G4`
gate schema. Checking a gate without a Markdown evidence link, using an unsafe
or missing repository path, omitting or reordering a gate, or declaring an
inconsistent checklist status fails readiness instead of silently completing
the extension.

The publication evidence runner treats a clean Git commit, reviewed contract
hashes, and the exact `uv.lock` SHA-256 as part of the evidence identity.
Those text-file hashes canonicalize CRLF and LF line endings, keeping evidence
portable across Windows review workstations and Linux CI runners.
PostgreSQL downgrade and Compose startup are separately guarded by explicit
disposable/synthetic confirmations. Command output is reduced to bounded, credential-redacted
failure details. The PostgreSQL gate proves major version 18, the Compose gate
requires a structured Linux server, and cleanup runs after every stack-start
attempt.

For remote P2-G1/P2-G2 evidence, `verify-run` checks the exact repository run,
successful expected job, commit-bound unexpired artifact, and downloaded JSON
payload from a clean checkout of the reviewed commit. It uses read-only GitHub
interfaces, does not fetch logs, removes its temporary download, and returns a
blocked result for authentication or network failures rather than trusting a
run URL.

The earlier PostgreSQL 18 run passed both integration tests, including two
concurrent capability workers, and completed a drift-free downgrade/upgrade/
check round trip through migration `0006`. Migration `0007` is covered by the
SQLite upgrade/downgrade test, but current PostgreSQL and Compose revalidation
was not run because Docker Desktop's Linux server was unavailable, its service
and WSL distribution were stopped, and the engine pipe returned HTTP 500. A
normal background launch started Desktop processes but did not start the
service, WSL distribution, or server within the three-minute readiness window.
That environment gap must be cleared before publication.
Lowering Docker API negotiation to 1.47 and 1.45 returned the same engine-pipe
HTTP 500, so the current failure is not a client API-version mismatch. No local
PostgreSQL service, `psql` command, port 5432 listener, or
`HCAM_POSTGRES_TEST_URL` was available as a non-Docker fallback.

## Container Checks

```powershell
python tools/phase2_lab.py prepare --force
python tools/phase2_lab.py config
python tools/phase2_lab.py start
python tools/phase2_lab.py verify --timeout 360
python tools/phase2_failure_drill.py
python tools/phase2_lab.py stop
```

The container gate requires all 50 streams healthy, a fresh background ONVIF
device-and-media snapshot with one change-history entry, path-isolated
playback, full-fleet recovery after an isolated ONVIF outage, and a zero
unpublished outbox backlog after the dispatcher drains.

GitHub CI runs Python 3.12-3.14, SQLite and PostgreSQL migration checks,
reviewed API/database contract checks, dependency audit, package installation
including the capability-worker CLI, Phase 1/2 readiness verification,
non-root image validation, regressions, and the full 50-stream synthetic lab.
The sdist retains the Python tests and JSON fixtures required to reproduce its
offline readiness checks from extracted source, including the reviewed lock.
The PostgreSQL 18 and synthetic-lab jobs generate guarded P2-G1/P2-G2 JSON,
bind it to the PR head, upload it under commit-specific names for seven days,
and preserve unconditional synthetic-stack cleanup.
