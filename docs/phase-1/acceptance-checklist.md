# Phase 1 Acceptance Checklist

## Automated And Engineering Evidence

- [x] Backend installs from a clean Python 3.12+ environment.
- [x] Alembic upgrades a new database through the current migration head.
- [x] Alembic downgrade and re-upgrade complete without schema drift.
- [x] Liveness and database/schema readiness endpoints are tested.
- [x] Readiness rejects stale migration revisions and missing required columns.
- [x] Database constraints enforce coordinate pairing/ranges, nonnegative
  duration, and positive optimistic-concurrency versions.
- [x] Registry seed import is validated, idempotent, and audited.
- [x] Camera list and detail APIs return normalized records.
- [x] Department, type, source, health, and operational filters are tested.
- [x] Camera create and partial update APIs validate and audit writes.
- [x] Missing, out-of-scope, conflicting, and no-op writes have tested failure
  outcomes and audit evidence.
- [x] Optimistic concurrency rejects missing and stale camera versions.
- [x] Bulk API import requires the administrator role and enforces its Phase 1
  synchronous record limit.
- [x] Registry endpoints fail closed when no identity provider is configured.
- [x] Local development authentication cannot be enabled in production mode.
- [x] Role and department restrictions are tested.
- [x] Stream references are sanitized before storage and response.
- [x] Malformed, overlong, credential-bearing, and token-bearing stream
  references cannot crash the API or leak through responses.
- [x] Request bodies have a streaming-safe size cap and registry responses use
  a no-store cache policy for success and error outcomes.
- [x] Unknown official values remain explicit nulls.
- [x] Synthetic test data is clearly identified and contains no CCTV footage.
- [x] Phase 0 strict readiness remains complete.
- [x] Python CI runs backend, migration, Phase 0, and Phase 1 checks.
- [x] CI tests Python 3.12, 3.13, and 3.14 with branch-aware coverage of at
  least 90%.
- [x] Ruff, dependency consistency, and vulnerability audit gates are enabled.
- [x] Wheel and source distributions build, contain required evidence, and pass
  isolated wheel installation smoke tests.

## Manual Phase Gate

- [ ] Owner accepts Phase 1 and authorizes Phase 2 planning. This approval
  authorizes architecture and safe adapter test planning only; it does not
  authorize production CCTV access, uncontrolled recording, Government data,
  biometrics, watchlists, or AI processing of real people. Track this gate in
  [GitHub issue #20](https://github.com/mayankthakor227/h-cam-2.0/issues/20).
