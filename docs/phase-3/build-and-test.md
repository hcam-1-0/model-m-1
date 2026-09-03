# Phase 3 Build And Test

## Authorized Slice

Phase 3 implementation started on 2026-08-24 with model-independent P3.0
contracts and guardrails on branch `codex/phase3-contracts-guardrails`.

Implemented:

- `hcam.analytics` assignment and event contract models;
- observation, local-track, analytic-event, and deployment-change envelopes;
- immutable artifact lineage, UTC time, normalized geometry, scope, and size
  validation;
- prohibited media, locator, credential, biometric, owner-record, Government,
  and watchlist fields;
- deterministic JSON Schema snapshots and generated fixtures; and
- draft taxonomy, normalized line/zone and weekly schedule contracts;
- a guarded, unconfigured runtime adapter boundary with safe failure codes; and
- CI-enforced contract drift and focused compatibility/privacy/misuse tests;
- durable activation-blocked assignments and immutable revisions;
- department-scoped RBAC APIs, reason headers, ETags, optimistic locking, and
  no-store responses;
- audited create/update/failure paths and transactional deployment-change
  outbox events; and
- additive Alembic `0008` plus Phase 3 OpenAPI/database snapshots;
- PostgreSQL migration round-trip/drift and synthetic assignment integration;
- sanitized request-validation errors with no rejected-value echo; and
- aggregate analytics metrics, dashboard, and bounded alert rules.
- six bounded P3.1 dataset, fixture, annotation, candidate-artifact,
  evaluation-run, and metric-report contract families;
- seven deterministic generated-only fixture/QA/split suites with hashes;
- annotation QA, grouped split/leakage validation, and hand-computable metric
  goldens;
- metadata-only records for 11 candidate roles with unresolved blockers and
  zero downloaded artifacts; and
- a 28-artifact P3.1 evidence package, CI drift check, and implementation
  readiness verifier.

Not implemented or authorized:

- model weights, inference runtimes, datasets, or media decoding;
- camera access, Sentinel video, Government data, or private CCTV processing;
- face recognition, person re-identification, watchlists, or owner lookup;
- operational alerts, autonomous action, or production deployment.

## Verification Commands

```powershell
uv run --locked --extra dev python -m compileall -q app tools migrations
uv run --locked --extra dev ruff check app tests tools migrations
uv run --locked --extra dev python tools/release_contracts.py check
uv run --locked --extra dev python tools/analytics_contracts.py check
uv run --locked --extra dev python tools/phase3_readiness.py --run-validation
uv run --locked --extra dev python tools/phase31_readiness.py --run-validation --strict
uv run --locked --extra dev python tools/phase31_contracts.py check --require-clean-source
uv run --locked --extra dev python tools/phase31_implementation_readiness.py --run-validation --strict
uv run --locked --extra dev python tools/phase32_entry_readiness.py
uv run --locked --extra dev pytest tests/test_analytics_evaluation_contracts.py tests/test_analytics_generated_evaluation.py tests/test_phase31_evidence_contracts.py tests/test_phase31_implementation_readiness.py --cov=hcam.analytics.evaluation --cov-branch --cov-report=term-missing --cov-fail-under=90
uv run --locked --extra dev pytest tests/test_analytics_contracts.py tests/test_analytics_taxonomy.py tests/test_analytics_geometry.py tests/test_analytics_runtime.py tests/test_analytics_assignment_api.py tests/test_analytics_assignment_migration.py --cov=hcam.analytics --cov-branch --cov-report=term-missing --cov-fail-under=90
uv run --locked --extra dev pytest --cov=hcam --cov-branch --cov-report=term-missing --cov-fail-under=90
uv run --locked --extra dev python -m build --no-isolation
uv run --locked --extra dev uv pip check
```

With `HCAM_DATABASE_URL` and `HCAM_POSTGRES_TEST_URL` pointing to an explicitly
disposable PostgreSQL database:

```powershell
uv run --locked --extra dev --extra postgres alembic upgrade head
uv run --locked --extra dev --extra postgres alembic check
uv run --locked --extra dev --extra postgres pytest -q -m postgres tests/test_postgres_integration.py
uv run --locked --extra dev --extra postgres alembic downgrade base
uv run --locked --extra dev --extra postgres alembic upgrade head
```

## Evidence

The first focused run found and corrected a generic PEM private-key header case
in the sensitive-value scanner. The rerun passed 37 tests with 96.10% branch
coverage for `hcam.analytics`. The pre-documentation full repository run passed
452 tests and 119 subtests, with four PostgreSQL tests skipped because
`HCAM_POSTGRES_TEST_URL` was not configured.

The final full repository coverage run passed 452 tests and 119 subtests with
four expected PostgreSQL skips, one pre-existing Starlette `httpx` deprecation
warning, and 90.71% total coverage. Compilation, full Ruff checks, Phase 2 and
Phase 3 contract checks, dependency consistency, and source/wheel package builds
also passed. PostgreSQL coverage remains provided by the existing CI service job
rather than by a local database claim.

The second focused P3.0 slice passed 72 tests with 94.61% branch coverage for
`hcam.analytics`. It covers taxonomy hierarchy and prohibited purposes,
degenerate/self-intersecting geometry, overlapping schedules, lease and batch
bounds, unrequested runtime outputs, unsupported capabilities, resource limits,
and exception sanitization. The corresponding full repository run passed 487
tests and 119 subtests with four expected PostgreSQL skips, the same pre-existing
Starlette warning, and 90.89% total coverage. Compilation, Ruff, dependency,
contract-drift, source distribution, and wheel checks passed for the expanded
package.

The third P3.0 slice added the activation-blocked assignment control plane. Its
focused assignment/migration/outbox/release suite passed 16 tests. The complete
analytics suite passed 79 tests with 94.67% branch coverage. After PostgreSQL,
observability, and validation-error hardening, the final full repository run
passed 504 tests with five expected PostgreSQL skips, the same pre-existing
Starlette warning, and 91.18% total coverage. Compilation, Ruff, dependency
consistency, analytics-contract drift, additive Phase 3 OpenAPI/database
contract checks, source distribution, and wheel builds passed. No runtime
adapter was invoked and no model, dataset, camera, or media source was
introduced.

Reviewed current release-contract hashes:

- `openapi.json`:
  `877A0C1AAB8EE88A8B9764F7B8760027212EBE21B783EEA6BA2F4C4646FBAB1B`;
- `database.json`:
  `3F0AE92FA304AC0B94E2E664D08D74F23E54CADDE4CBB9806C6C1BDB9D006FD0`.

The P3.0 hardening run used a disposable loopback-only PostgreSQL 18 container.
Five PostgreSQL integration tests passed before and after a complete downgrade-
to-base/restore-to-head cycle, and both post-upgrade schema-drift checks passed.
The initial drift check correctly exposed an unregistered analytics model module
in Alembic metadata; the import was added and a SQLite migration regression now
runs `alembic check`. The container was removed after validation.

Identifier-free metrics, the five-panel Phase 3 Grafana dashboard, three bounded
Prometheus alerts, and validation-value redaction tests also passed. These are
control-plane signals only and do not imply an analytics worker or model exists.

The P3.0 readiness verifier checks 52 required artifacts, structured contracts,
blocked-state invariants, prohibited-data boundaries, observability artifacts,
later-milestone separation, and the canonical Phase 3 documentation digest. Its
twelve focused tests and full offline validation cycle passed. P3-G1 through P3-G3
now have owner-approved, machine-readable repository evidence with exact scope,
policy, role, duplicate-record, and tamper checks. The latest full repository run
passed 506 tests with five expected PostgreSQL skips, the same pre-existing
Starlette warning, and 91.18% total coverage. A separate disposable PostgreSQL
18 run passed all five integration tests before and after a complete downgrade-
to-base/restore-to-head cycle. Source and wheel builds and dependency checks also
passed. The report has zero technical failures and is `accepted` with no manual
gates after the owner-approved P3-G4 self-review exception. Strict mode exits
with code `0`.

The later owner decision also removes cross-person review enforcement from
approved/retired taxonomy and operational-geometry contracts and makes
accountable-owner review sufficient for model promotion, datasets, and
deployment. Approval records and every non-review evidence gate remain required.

## P3.1 Planning And Authorization Validation

P3.1 planning and bounded generated-only implementation authorization are
recorded under `D-P3.1-001`. The dedicated offline verifier checks the exact
owner, review policy, six source tiers, eight authorized scope entries, eleven
non-authorizations, nine work packages, nine exit gates, six planned contract
families, developer hardware limits, P3.0 acceptance dependency, five ordered
planning gates, seven explicitly pending implementation exits, safe local
evidence links, and a deterministic five-artifact package digest.

The focused P3.0/P3.1 readiness suite passed 23 tests. The strict P3.1
validation cycle passed lock, compile, Ruff, focused tests, P3.0 strict
dependency, and diff checks with zero failures and zero manual gates. Status is
`authorized_for_implementation`; it is not `implemented` or `accepted`.

The complete repository branch-coverage run passed 519 tests with five expected
PostgreSQL skips and 91.17% total branch coverage. Full compilation, Ruff,
analytics-contract checks, release-contract checks, and the P3.0
upgrade/drift/downgrade/restore validation cycle passed. P3.1 package digest:
`0EF59F33AC17C336551A2DC8B36FD7FD2D94C1B2BEC017C3AA3C54B974E16DB3`.

No external artifact was downloaded, no model or decoder was executed, and no
camera, media, Government/private data, P3.2 work, pilot, or deployment was
authorized or used by this planning validation.

## P3.1 Implementation Validation

The generated-only implementation package contains 28 deterministic JSON
artifacts: six canonical contract families, seven generated suites, 11 blocked
candidate manifests, and the bound QA, split, metric, run, source-dossier, and
evidence-index records. The evidence index binds 19 digest-bearing records and
records zero downloads, zero model/media artifacts, no network/GPU/secrets, and
zero eligible candidates.

The post-acceptance focused implementation suite passed 72 tests with 91.88%
combined branch coverage; the evaluation package retained approximately 97%
coverage. Snapshot regeneration, Ruff, and `git diff --check` also passed.
After clean-source regeneration, the implementation
verifier reports zero failures and zero manual gates under owner-accepted
package digest
`956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618`.

The subsequent pre-acceptance full repository run passed 589 tests and 119
subtests with five
expected PostgreSQL skips, one pre-existing Starlette `httpx` deprecation
warning, and 92.18% total branch coverage. A fresh temporary SQLite database
upgraded through Alembic `0008` and `alembic check` found no drift. The locked
66-package environment passed dependency consistency checks, and source and
wheel artifacts built successfully.

The final acceptance-closure run passed 591 tests with five expected
PostgreSQL-only skips, the same pre-existing warning, and 92.18% total branch
coverage. The skips reflect an unconfigured `HCAM_POSTGRES_TEST_URL`; they do
not claim a new local PostgreSQL run.

The baseline was regenerated from clean implementation commit
`be7749d4315f46a49370b65f14c6e583e51a0c6e` with
`dirty_worktree=false`. `mayank-admin` accepted that exact generated-only
package and its limitations under `D-P3.1-ACCEPTANCE`. P3.1 is accepted; this
does not authorize P3.2.

## P3.2 Blocked-Entry Governance Validation

The pre-P3.2 entry state is machine-readable under canonical record digest
`382A5ACB82760A434B6373F19DCE42A98564D48A34519F8B6EE8766B736885F2`.
The verifier reports `blocked_pending_owner_decisions`, zero technical
failures, and five manual owner gates. Default mode exits successfully only
when the blocked record, accepted P3.0/P3.1 dependencies, blocked `DET-R0`
candidate, documentation links, and CI command remain intact. Strict mode
intentionally fails while those owner gates remain unresolved.

Ten dedicated tests cover current state, JSON/strict CLI behavior, unauthorized
start, decision promotion, removed non-authorization, P3.1 digest drift,
candidate eligibility, documentation links, and CI integration. The combined
readiness/documentation slice passed 51 tests and 88 subtests. The complete
repository run passed 601 tests with five expected PostgreSQL-only skips, the
same pre-existing Starlette `httpx` deprecation warning, and 92.18% total
branch coverage.

This is governance validation, not P3.2 readiness or authorization. No model,
dataset, runtime, camera, media, Government/private data, or deployment path
was added or exercised.

## Snapshot Review

Check snapshots without modifying them:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py check
uv run --locked --extra dev python tools/phase31_contracts.py check --require-clean-source
```

Regeneration is an explicit review operation:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/phase31_contracts.py write --acknowledge-generated-only-evidence
```

Review the schema and fixture diff before accepting a rewrite. Generated
fixtures are synthetic metadata only and must remain free of media, credentials,
camera locators, biometric templates, Government data, and owner records.

## P3.4 Implementation Validation

The generated-only geometry/event package passed 715 tests and 119 subtests
with eight PostgreSQL tests skipped in the general local suite, one pre-existing
Starlette warning, and 90.24% total branch coverage. Focused evaluator branch
coverage is 94.32%. Five sealed C10 groups have exact logic agreement and 20
stable replays per scenario.

SQLite and pinned PostGIS validation both passed `0011 -> 0010 -> 0011`, with
drift checks after both PostGIS upgrades. All eight PostgreSQL/PostGIS tests
passed on PostgreSQL 18.6, PostGIS 3.6.4, GEOS 3.14.1, and PROJ 9.8.1. A fresh
loopback Compose stack validated database initialization, migration, non-root
API health/readiness, protected metrics, and all P3.4 route families. Its
database healthcheck now requires the permanent TCP server, and extension
inspection runs inside Alembic's managed transaction; this closes both
empty-volume silent-success paths reproduced during recovery.

The source distribution and wheel both build. A hash-locked isolated Python 3.14.6
install starts the application and CLI with Shapely 2.1.2, local GEOS 3.13.1,
NumPy 2.5.2, and CEL 0.1.3. Archive scans found no media, model, or secret
payloads across 99 wheel and 473 source-distribution members. Both CI-equivalent
Python audit profiles found no known vulnerabilities. Bandit found zero
medium-or-higher application issues and the offline production-source secret
profile found zero candidates. Untrusted ONVIF and WS-Discovery XML now uses
defused parsers, with malicious external-entity regression tests. Phase 1
strict validation now gives the full suite a 600-second command bound and
reports timeout/runtime exceptions as checker failures.

The PostGIS image scan records 54 unresolved findings, including 2 critical and
21 high, so deployment remains blocked. These results authorize no camera,
media, external data, identity, alert, deployment, P3.5, or remote Git action.

Verify the accepted bounded evidence and immutable historical binding:

```powershell
uv run --locked --extra dev python tools/phase34_readiness.py --strict
uv run --locked --extra dev --extra analytics python tools/phase34_c10_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase34_supply_chain.py check
uv run --locked --extra dev --extra analytics python tools/phase34_implementation_readiness.py --require-clean-source --require-acceptance
```
