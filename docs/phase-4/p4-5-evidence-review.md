# P4.5 Evidence Review

Status date: 2026-09-05

## Result

P4.5 Investigation Timeline And Evidence is technically complete within the
exact `D-P4.5-START` generated-only scope and the separately authorized
`D-P4.5-PHASE44-CLOCK-TEST-AMENDMENT`. It is exactly owner accepted under
`D-P4.5-ACCEPTANCE`. The implementation is local, default-off,
production-forbidden, nonoperational, and does not resolve a source locator,
copy evidence or media, connect to a case system or provider, choose a legal
policy, execute deletion or export, or perform a network operation.

## Delivered Boundary

- Additive V2 investigation timelines, typed entries, revisions, temporal
  assertions, deterministic chronology, reconstruction, and V1 read
  compatibility.
- Immutable reference-only evidence records with separate availability,
  provenance, preservation, authenticity, custody, and legal-state dimensions.
- Bounded provenance graphs and a disabled, derived, non-authoritative
  generated PROV projection.
- Append-only corrections and retractions with durable bounded impact jobs,
  retries, lease recovery, dead-letter outcomes, audit, and transactional
  outbox records.
- Attributable review and disposition chains, non-destructive merge aliases,
  cycle prevention, single active merge target, and reopen history.
- Policy-reference retention evaluations, separate hold overlays, simulated
  residual-aware deletion receipts, and purpose-bound reference-only exports.
- A disabled generated case-management bridge contract with no external
  adapter, case workflow, or legal authority.
- Migration `0017_investigation_evidence` with 17 department-scoped stores and
  forced PostgreSQL row-security declarations.
- Eighteen default-off API operations on 16 paths with exact RBAC, department
  scope, bounded inputs, no-store responses, and sanitized problem details.

## Validation

- Generated fixture regeneration: 14 documents and 552 scenarios, byte-exact.
- Focused P4.5 collection: 62 tests, with 61 passing and one expected
  PostgreSQL-URL-dependent skip.
- P4.5 branch-enabled aggregate coverage: 90.71%, above the required 90%.
- Unconditional repository suite: 4,030 passed, 15 expected PostgreSQL skips,
  119 subtests passed, zero failures, zero deselections, and one warning.
- Phase 4.4 focused regression: 58 passed and one expected PostgreSQL skip.
- SQLite migration compatibility preserves the V1 stores and validates the
  `0016 -> 0017 -> 0016 -> 0017` cycle with one linear Alembic head.
- Ruff, compileall, generated fixture checks, historical P4.4 readiness,
  offline wheel/sdist build, dependency compatibility, and readiness pass.
- Recovery and abuse tests cover exact idempotency, semantic/delivery
  collisions, stale revisions, correction closure, retry exhaustion, lease
  recovery, merge cycles, multiple active targets, cross-department denial,
  incomplete exports, and sanitized API failures.

## Authorized Compatibility Amendment

The owner authorized one test-only Phase 4.4 clock correction. The changed
test now derives simulated worker times from each persisted query job's
`created_at` value instead of a fixed `2026-09-05 08:00 UTC` timestamp. Its
accepted pre-change normalized SHA-256 is
`1A752E601994A02F82FE3653DDD20056492741FD414A1BC6AE6F9A6021B0EA47`.
No Phase 4.4 production behavior or historical evidence changed.

## Limitations

Local PostgreSQL execution was unavailable because `HCAM_POSTGRES_TEST_URL` is
not configured and starting a container or service is outside the
authorization. The opt-in test and CI PostgreSQL/PostGIS job cover forced row
security, department isolation, concurrent impact claims, and correction
propagation. This review makes no local PostgreSQL execution claim.

No fresh vulnerability database was downloaded and no new SBOM was generated,
because network access, installation, downloads, and dependency changes are
outside the authorization. The locked 74-package environment passes dependency
compatibility. One known Starlette TestClient warning remains.

The accepted start package's existing-path `pre_change_sha256` records are
structurally valid planning records but do not all correspond to the recorded
implementation-base commit. The readiness verifier therefore relies on exact
changed-path allowlisting, immutable predecessor-history verification, and the
separately hash-bound clock amendment rather than treating those records as
byte bindings. This limitation is explicit and no accepted package was edited.

No source locator was resolved and no evidence or media content was fetched,
copied, inspected, verified, or retained. The generated PROV projection and
case-management bridge are disabled, non-authoritative capability surfaces.
No PROV conformance, legal admissibility, authenticity, custody certification,
retention-period correctness, universal deletion, operational scale, or
deployment claim is made.

## Progress

Technical completion earned **14/15 P4.5 points (93.3333%)** and moved Phase 4
from **70/100 (70.00%)** to **84/100 (84.00%)**, a change of **+14.00 Phase 4
percentage points** and **+93.3333 P4.5 percentage points**. Exact owner
acceptance earns the final **1/15 P4.5 point**, moving P4.5 to **15/15
(100.0000%)**, a change of **+6.6667 P4.5 percentage points**, and Phase 4 to
**85/100 (85.00%)**, a change of **+1.00 Phase 4 percentage point** from the
technical state. Frozen items use no partial credit.

The effective acceptance is recorded in
`contracts/phase-4/p4-5/acceptance.json` and is bound to technical commit
`9eb3d2fb3a3fc68b8722d7c4a70369e6f1a8d41e`, evidence-package SHA-256
`02F0439B2034ECBB0481E854236DAE0991C6A5DC9A3B04AD3AA3E5C03507D980`,
and canonical component digest
`118C40D319653F8D9E6CD21CB216F7F43B073BE58823CA36A96ACE9AE36986C2`.

## Closed Gates

P4.6, source or evidence resolution/copying, real investigations or case
systems, external PROV import, legal or retention-period decisions, real holds,
deletion/export execution, providers, network, credentials, Government or
private data, cameras/media, models/datasets, inference, operational actions,
containers, Kubernetes, deployment, and remote Git remain closed.
