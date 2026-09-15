# P4.3 Evidence Review

Status: technical validation passed; exact owner acceptance recorded.

## Evidence Scope

The P4.3 package covers deterministic proposed-alert identity, independent
delivery idempotency, collision denial, an orthogonal alert aggregate, typed
lifecycle transitions, optimistic concurrency, append-only review and
correction records, configurable distinct-reviewer quorum, hierarchical
loss-accounted budgets, persistent timer intents, bounded generated workflow
adapters, migration `0015`, department-scoped read and mutation APIs, forced
PostgreSQL row-security definitions, transactional outbox records, and
low-cardinality observability.

Police-intelligence records remain mandatory-review. The only bounded
automation lane is separately typed generated system health, with the exact
allowlisted actions `route`, `suppress_duplicate`, and
`resolve_synthetic_health`. No public proposal route exists.

This package does not cover real workflow engines, Sentinel or other network
access, cameras, streams, images, recording, playback, models, datasets,
credentials, private or Government data, operational alerts, notifications,
dispatch, enforcement, containers, Kubernetes, deployment, or remote Git.

## Frozen Acceptance Rule

P4.3-A is worth 4/15 points and requires deterministic proposed-alert
creation, at-least-once replay, semantic and delivery idempotency, collision
denial, correction, rollback, and bounded concurrency evidence. P4.3-B is
worth 5/15 points and requires the complete transition matrix, orthogonal
workflow records, actor, reason, ETag, RBAC, audit, outbox, merge, correction,
and reconstruction gates. P4.3-C is worth 4/15 points and requires mandatory
review, authority separation, deterministic budgets and collapse, suppression,
timer leases, retries, recovery, and overload gates. P4.3-D is worth 2/15
points and requires exact reproducible evidence, a lifecycle recovery drill,
and separate owner acceptance.

No partial item receives weighted credit. Technical completion raised P4.3 to
13/15 (86.6667%) and Phase 4 to 53/100 (53.00%), changes of +86.6667 and
+13.00 percentage points respectively. Exact owner acceptance raises P4.3 to
15/15 (100.0000%) and Phase 4 to 55/100 (55.00%), changes of +13.3333 and
+2.00 percentage points from the technical state.

## Verified Results

- The final focused P4.3 suite reports 46 passed, one expected PostgreSQL URL
  skip, one locked-dependency warning, and 90.54% branch-enabled coverage over
  `app/hcam/intelligence/alerts`.
- The unconditional repository suite reports 3,910 passed, 13 expected
  PostgreSQL URL skips, 119 passing subtests, zero deselections, and one known
  locked-dependency warning in 808.07 seconds.
- The historical readiness and migration batch reports 20 passed. It preserves
  explicit P4.0, P4.1, and P4.2 revisions while validating the
  `0014 -> 0015 -> 0014 -> 0015` P4.3 cycle.
- The owner-authorized legacy analytics migration assertion changed exactly
  from repository head `0014_rule_authoring_evaluation` to
  `0015_alert_lifecycle_orchestration`; its Phase 3 assertion and all other
  behavior remain unchanged.
- The generated fixture verifier reproduces eight documents containing 16
  proposal cases, 17 lifecycle cases, six quorum cases, four budget cases, two
  timer cases, three workflow cases, 50 sanitized lab cases, and generated
  system-health cases.
- Replay, same-key/different-material denial, command and review idempotency,
  merge-cycle denial, distinct-reviewer quorum, timer lease recovery, retry
  bounds, SQLite single-worker enforcement, and generated lane separation all
  pass.
- Ruff, compileall, Git whitespace validation, offline source/wheel build,
  74-package compatibility, Phase 3 release and analytics contract checks, and
  the existing Phase 3.4 supply-chain evidence check pass.
- Dependency and lock files remain byte-exact. No install, download, network,
  camera, media, model, sensitive data, container, deployment, or remote-Git
  action occurred.

## Explicit Local Limitations

`HCAM_POSTGRES_TEST_URL` is not configured and P4.3 does not authorize starting
containers. The P4.3 PostgreSQL forced-row-security and concurrent timer-claim
test is therefore an expected local skip. The migration, forced-RLS policies,
`FOR UPDATE SKIP LOCKED` path, department-isolation assertions, and CI job are
present, but this package makes no local PostgreSQL execution claim.

A fresh vulnerability-database refresh or new SBOM generation was not
performed because network access, downloads, installations, and dependency
changes are prohibited. The immutable lockfile, installed-package
compatibility, and existing repository supply-chain evidence were checked
offline.

The alert lifecycle remains generated-only, disabled by default, forbidden in
production, and has no startup worker, public proposal endpoint, external
workflow transport, notification, dispatch, or enforcement surface.

## Acceptance Boundary

The evidence package and canonical component digest are bound by
`contracts/phase-4/p4-3/evidence-package.json`. The exact owner statement is
recorded as effective in `contracts/phase-4/p4-3/acceptance.json`, bound to
evidence-package SHA-256
`EC68E3629C9D4036C154F7E587D52DB4611948AC0F129CA120BF03D9EC3E671C`
and canonical component digest
`8797AFFDA2A9CA2F74E78F612F0E4A6B58BAF3394ABA01685B0C64842C36DEE4`.
P4.3-D is complete, P4.3 is 15/15 (100.0000%), and Phase 4 is 55/100
(55.00%). P4.4 remains unauthorized and every excluded boundary stays closed.
