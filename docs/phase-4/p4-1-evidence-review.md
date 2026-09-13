# P4.1 Evidence Review

Status: technical validation passed and exact owner acceptance recorded.

## Evidence Scope

The P4.1 evidence package covers the closed generated Phase 3 event adapter,
canonical receipts, event-time ordering, watermarks, bounded windows, exact
replay, deterministic AMEC arbitration, canonical evidence graphs, append-only
revisions, migration `0013`, department-scoped read models, forced PostgreSQL
row security tests, low-cardinality observability, production denial, and the
absence of public correlation mutation or startup workers.

It does not cover models, datasets, artifacts, inference, optional model-lane
execution, cameras, media, external providers, credentials, Government/private
data, rule activation, operational alerts, dispatch, enforcement, Kubernetes,
deployment, or remote Git.

## Frozen Acceptance Rule

P4.1-A is worth 4/15 points and requires the complete ingress, ordering,
windowing, and exact-replay gate. P4.1-B is worth 5/15 points and requires the
deterministic AMEC, bounded persistence, concurrency, and observability gate.
P4.1-C is worth 4/15 points and requires canonical hypotheses, revisions,
read-only APIs, catalog synchronization, security negatives, and all technical
validation. P4.1-D is worth 2/15 points and requires separate exact owner
acceptance of the final sealed package.

No partial item receives weighted credit. Technical gates raised P4.1 to 13/15
(86.6667%) and Phase 4 to 23/100 (23.00%). Exact owner acceptance raised P4.1
to 15/15 (100.0000%) and Phase 4 to 25/100 (25.00%).

## Current Verified Results

- Generated fixtures reproduce exactly from the repository-owned generator.
- The focused P4.1 suite passes locally with 57 tests and 92.22% branch-enabled
  correlation-package coverage; PostgreSQL tests remain opt-in through
  `HCAM_POSTGRES_TEST_URL`.
- Actual branch-enabled coverage of the correlation package exceeds the frozen
  90% threshold.
- P4.0 historical readiness passes from its accepted implementation commit;
  its evidence, acceptance, and component digests remain unchanged.
- The unconditional repository regression passes with 3,750 tests, 11
  PostgreSQL-URL-dependent skips, 119 passing subtests, and zero deselections.
- The exact hash-bound legacy migration amendment preserves P4.0 at `0012`,
  recognizes `0013` as head, and passes the `0012 -> 0013 -> 0012 -> 0013`
  compatibility cycle.
- An isolated cached PostgreSQL 18.6 and PostGIS 3.6.4 service passes both
  Alembic drift checks, forced row security and one department policy on all
  five new stores, actual cross-department isolation, and concurrent
  `SKIP LOCKED` claiming. The temporary probe role, container, and internal
  network were removed after validation.
- Ruff, compileall, Git whitespace validation, source and wheel builds, the
  74-package compatibility check, Phase 3 release and analytics contracts,
  Phase 3 readiness, and P4.0 historical readiness pass.
- No camera, media, model, dataset, provider, Government/private data,
  deployment, Kubernetes, or remote-Git action has been performed.

Exact final counts, hashes, full-regression results, packaging results, and the
PostgreSQL disposition are recorded in
`contracts/phase-4/p4-1/evidence.json`. The package digest and proposed owner
statement are recorded in the non-effective acceptance proposal. P4.1-D earns
its final two points through the effective exact owner acceptance record in
`contracts/phase-4/p4-1/acceptance.json`.

## Known Local Limitation

The locked local Python environment lacks its PostgreSQL driver, so the opt-in
P4.1 PostgreSQL tests remain expected skips in the unconditional suite. The
cached H-CAM runtime has `psycopg` but no `pytest`; therefore the exact two test
functions from `tests/test_phase41_postgres.py` were loaded with a marker-only
pytest shim and executed directly against the isolated service. Docker Desktop
Kubernetes was temporarily disabled after its WSL backend crashed during the
first attempt, then restored after the named P4.1 resources were removed. These
environment details do not weaken the executed database assertions, but they
remain explicit in the evidence.
