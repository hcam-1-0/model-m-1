# P4.4 Evidence Review

Status date: 2026-09-05

## Result

P4.4 Authorized Reference Integrations is technically complete within the exact
`D-P4.4-START` generated-only scope. The implementation is local, default-off,
production-forbidden, nonoperational, and exactly owner accepted under
`D-P4.4-ACCEPTANCE`. It does not connect to a provider, Sentinel, a camera, a
workflow engine, a secret backend, or a network destination.

## Delivered Boundary

- Closed provider, operation, purpose, field, authentication, destination,
  trust, freshness, resource, retention, and control contracts.
- Immutable compiled generated-provider manifests and static adapter binding.
- Eleven deterministic fixture documents containing 372 generated scenarios.
- Versioned generated catalogue snapshots with stable fingerprints and explicit
  freshness.
- Durable bounded query jobs with semantic and delivery deduplication, leases,
  retries, cancellation, circuits, revocation, quarantine, and zero raw-response
  retention.
- Deterministic field evidence, contradiction handling, top-K ranking,
  ambiguity, abstention, identity state `not_established`, and mandatory review.
- Independent default-off manual-query and generated-hypothesis lanes.
- Hierarchical controls, append-only revisions, transactional outbox records,
  sanitized failure codes, and low-cardinality metrics.
- Migration `0016_reference_integrations` with ten department-scoped stores and
  forced PostgreSQL row-security declarations.
- Eight default-off API paths under `/reference-integrations` with exact RBAC,
  department scope, no-store responses, reasons, and optimistic concurrency.

## Validation

- Generated fixture regeneration: 11 documents and 372 scenarios, byte-exact.
- Focused P4.4 collection: 57 tests, with 56 passing and one expected
  PostgreSQL-URL-dependent skip.
- P4.4 branch coverage: 92.01%, above the required 90%.
- Unconditional repository suite: 3,967 passed, 14 expected PostgreSQL skips,
  119 subtests passed, zero failures, and zero deselections.
- Historical migration compatibility: 14 tests passed through revision `0016`.
- P4.3 historical readiness, Phase 3 release contracts, Phase 3 analytics
  contracts, Ruff, compileall, package build, and dependency compatibility pass.
- Recovery tests cover retry exhaustion, expired leases, circuit-open
  quarantine, revocation-before-execution quarantine, cancellation, duplicate
  delivery, and zero raw-response retention.

## Limitations

Local PostgreSQL execution was unavailable because `HCAM_POSTGRES_TEST_URL` is
not configured and starting a container or service is outside the authorization.
The opt-in test and existing CI PostgreSQL/PostGIS job cover forced row security,
department isolation, concurrent `SKIP LOCKED` claims, circuits, and revocation.
This review therefore makes no local PostgreSQL execution claim.

No fresh vulnerability database was downloaded, and no new SBOM was generated,
because network access, installation, downloads, and dependency changes are
outside the authorization. The locked 74-package environment passes dependency
compatibility. One known Starlette TestClient warning remains in the locked
dependency boundary.

## Progress

Technical completion earned **14/15 P4.4 points (93.3333%)** and moved Phase 4
from **55/100 (55.00%)** to **69/100 (69.00%)**, a change of **+14.00 Phase 4
percentage points**. Exact owner acceptance earns the final **1/15 P4.4 point**,
moving P4.4 to **15/15 (100.0000%)**, a change of **+6.6667 P4.4 percentage
points**, and Phase 4 to **70/100 (70.00%)**, a change of **+1.00 Phase 4
percentage point** from the technical state. No partial credit is used.

The effective acceptance is recorded in
`contracts/phase-4/p4-4/acceptance.json` and is bound to technical commit
`9efacc75336cc942db9615c21e371cb3322aea73`, evidence-package SHA-256
`6AB08EC54C9197E4D96D57B5CEA5F7D87840A3EA16E02108D01CBBEEE574D98A`,
and canonical component digest
`E42E15FEFA36ADC6B58A506BEDC97CC089E54916B04B33E88B4FC070479EFC37`.

## Closed Gates

Real providers, credentials, secrets, authentication extension loading,
external workflow engines, provider or Sentinel network access, Government or
private data, cameras or media, models or datasets, operational alerts or
actions, containers, Kubernetes, deployment, remote Git, and P4.5 remain closed.
