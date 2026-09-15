# P4.0 Evidence Review

Status: technical gates passed and exact owner acceptance recorded.

## Evidence Scope

The evidence covers generated-only contract parsing, canonicalization,
guardrails, SQLite migration cycling, PostgreSQL/PostGIS forced row security,
default-off API behavior, RBAC, department isolation, ETags, reason headers,
audit records, unpublished outbox records, production denial, snapshots,
readiness, lint, build, dependency consistency, and the full regression suite.

It does not cover models, datasets, inference, cameras, media, external
providers, Government or private data, operational alerts, dispatch,
enforcement, Kubernetes, deployment, or remote Git.

## Acceptance Rule

P4.0-B earns three points only when executable contracts, deterministic
fixtures, canonicalization, boundaries, chronology, geometry, provenance, and
privacy negatives all pass. P4.0-C earns two points only when migration,
database constraints, PostgreSQL forced RLS, API roles, ETags, audit, outbox,
department isolation, and production denial all pass.

Passing technical gates can raise P4.0 to 8/10 and Phase 4 to 8/100. The final
two P4.0-D points require exact owner acceptance of the sealed evidence package.
No partial implementation receives points under the frozen accounting method.

`D-P4.0-ACCEPTANCE` satisfies that final gate for the exact package and raises
the accepted state to P4.0 10/10 (100.00%) and Phase 4 10/100 (10.00%). It does
not authorize P4.1 or expand any runtime, data, deployment, or remote-Git scope.

## Verified Results

- Focused generated-only suite: 129 passed and one PostgreSQL-URL-dependent
  test skipped.
- Intelligence package coverage: 97.42% branch-enabled aggregate coverage,
  including 91.30% actual branch outcomes against a 90% requirement.
- Full repository regression: 3,691 passed, nine PostgreSQL-URL-dependent
  tests skipped, and 119 subtests passed.
- SQLite migration cycle: `0011 -> 0012 -> 0011 -> 0012`, with Alembic drift
  check passing.
- Cached PostgreSQL 18/PostGIS 3.6.4 validation: ten forced-RLS tables, ten
  department policies, department isolation, and disabled-provider database
  constraint passed.
- Legacy release contracts: accepted Phase 3 OpenAPI and database snapshots
  pass unchanged at `0011_geometry_events`.
- Phase 4 readiness, Ruff, compileall, source distribution, wheel build, and
  the 74-package dependency consistency check passed.

The full evidence is sealed by package SHA-256
`BB0E726F6C362F2AE29E6D78D36A5E3C289E28E4367DD9E057A092D195AEF5CB`
with canonical component digest
`28527B04231B00B93A7AFB1DAC8D95F3142B6ED88717CB0A9A8657E5E6DAC799`.

## Known Limitation

The local Python environment has no `HCAM_POSTGRES_TEST_URL`, so PostgreSQL
pytest modules skip locally. The exact P4 migration delta was instead executed
against an isolated cached PostgreSQL/PostGIS container, and CI retains the
PostgreSQL integration job. No network download or provider connection was
performed.
