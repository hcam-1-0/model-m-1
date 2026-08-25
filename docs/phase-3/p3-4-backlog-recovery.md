# P3.4 Backlog Recovery

Status: `technical_backlog_complete_pending_owner_acceptance` on
`codex/phase3-geometry-events`.

Recorded: 2026-08-26 by the local development session after an interrupted
backlog audit. This record does not grant `D-P3.4-ACCEPTANCE`, P3.5, deployment,
camera/media access, external-data access, or remote Git action.

## Resume Point

The accepted implementation-start boundary remains `D-P3.4-START`. The last
committed checkpoint is `566357a04af45c407cb0f7fcdf814be1a556ea5a`. The
previous frozen P3.4 package digest was
`B840FF0AC50503F13C4D80426097A0FFD18A008465FADBB8A89B9912943C2E88`, but it
must not be accepted after this repair because tracked package files changed.
A replacement clean-source digest must be generated only after validation and a
new local checkpoint commit.

## Reproduced Defects

1. The Phase 3 index still stated that P3.4 implementation evidence was pending,
   while the readiness report and backlog correctly stated that technical
   evidence was complete and only exact-digest owner acceptance remained.
2. A fresh PostGIS `alembic check` proposed destructive removal of PostGIS/Tiger
   extension-owned tables and removal of H-CAM's PostGIS geometry type, GiST
   index, and spatial constraints.
3. The earlier compound PowerShell validation sequence did not fail fast, so a
   nonzero `alembic check` was masked by later successful commands.
4. The P3.4 PostGIS CI job exercised migration and behavior tests but did not run
   schema-drift checks.
5. The Phase 3 PostGIS healthcheck used the local Unix socket, which was ready
   during the image's temporary initialization server. On a truly empty volume,
   Compose could start Alembic before PostGIS initialization finished and then
   lose the migrated schema when that temporary server stopped.
6. Loading extension ownership before Alembic opened its managed transaction
   triggered SQLAlchemy autobegin. Migration logs and exit status reported
   success, but closing the connection rolled the schema transaction back.

## Repair Applied But Not Yet Accepted

- Correct the Phase 3 index and require its current status in the P3.4 planning
  documentation verifier.
- Register the custom PostGIS geometry type for SQLAlchemy reflection.
- Exclude extension-owned tables from Alembic comparison before reflection.
- Keep PostgreSQL-only spatial constraints and the GiST index in ORM metadata,
  with dialect-aware autogenerate filtering for SQLite.
- Run `alembic check` before and after the PostGIS migration round trip in CI.
- Add regression tests for reflected geometry arguments, CI drift gates, and
  stale status text.
- Require TCP loopback in the PostGIS healthcheck so dependent services start
  only after the permanent database server is listening.
- Load extension ownership inside Alembic's managed transaction so migrations
  and drift checks commit normally.

## Validation Completed During Recovery

- Full suite before the repair: 707 passed, 7 expected PostgreSQL skips, 90.22%
  branch coverage.
- Compile, Ruff, release/analytics contract checks, dependency consistency, and
  Phase 1 through P3.4 readiness checks passed before the repair.
- Phase 2 and P3.0 full offline validation passed.
- Focused repair tests: 33 passed.
- Fresh SQLite migration to `0011_geometry_events` and `alembic check` passed
  after dialect filtering was added.
- PostgreSQL 18.6/PostGIS 3.6.4 `alembic check` passed after reflection and
  extension filtering were added.
- A temporary unmanaged table was detected by `alembic check`; the check
  returned clean after that table was removed.
- All 8 PostgreSQL/PostGIS integration tests passed against a fresh disposable
  database after `0011 -> check -> 0010 -> 0011 -> check`.
- A second empty-volume Compose run retained `0011_geometry_events`, reached
  live/readiness, enforced metrics authentication, exposed all four P3.4 route
  families, and ran as `10001:10001`.
- The final full suite passed 711 tests and 119 subtests with 8 expected
  PostgreSQL skips, one pre-existing warning, and 90.22% branch coverage.
- Package build, isolated install, prohibited-payload scan, dependency
  consistency, and the 76-component Python vulnerability audit passed.

## Remaining Backlog

- [x] Start a fresh disposable PostGIS database and run fail-fast:
  `upgrade -> check -> downgrade 0010 -> upgrade 0011 -> check`.
- [x] Run all eight PostgreSQL/PostGIS integration tests against that database.
- [x] Run full compile, Ruff, contract, dependency, and pytest coverage gates
  after the repair.
- [x] Rebuild package artifacts and rerun prohibited-payload and dependency
  evidence checks if package-affecting files remain changed.
- [x] Update P3.4 validation evidence and readiness documentation with the new
  results, without altering historical acceptance records for P3.1-P3.3.
- [x] Commit the bounded repair locally and verify the clean-source package as
  part of the final handoff sequence.
- [x] Record the replacement P3.4 package digest and present the sole remaining
  `D-P3.4-ACCEPTANCE` owner gate.
- [ ] Receive explicit `D-P3.4-ACCEPTANCE` for that exact replacement digest.

## Continuing Independent Blocks

- The pinned PostGIS image's unresolved critical/high vulnerabilities continue
  to block pilot and production deployment.
- P3.5 and all cameras, media, external datasets, identity, cross-camera
  linkage, Government matching, operational alerts, deployment, push, PR, and
  merge actions remain unauthorized.
