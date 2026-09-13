# P4.2 Evidence Review

Status: technical validation passed and exact owner acceptance recorded.

## Evidence Scope

The P4.2 package covers generated-only visual rule documents, canonical typed
AST compilation, bounded constrained CEL, deterministic temporal evaluation,
immutable rule versions and lifecycle records, append-only corrections,
non-operational shadow evidence, migration `0014`, department-scoped APIs,
forced PostgreSQL row-security definitions, low-cardinality observability, and
the absence of public evaluation-start, operational activation, or startup
worker paths.

It does not cover models, datasets, artifacts, inference, cameras, media,
external providers, credentials, Government/private data, operational alerts,
dispatch, enforcement, containers, Kubernetes, deployment, or remote Git.

## Frozen Acceptance Rule

P4.2-A is worth 4/15 points and requires the complete visual graph, canonical
typed AST, version, digest, reachability, bound, and deterministic compilation
gate. P4.2-B is worth 5/15 points and requires the complete temporal, schedule,
watermark, correction, replay, overload, and bounded-state gate. P4.2-C is
worth 4/15 points and requires the closed CEL environment, checked structure,
Boolean result, compile-once binding, abuse, and deterministic evaluation gate.
P4.2-D is worth 2/15 points and requires separate exact owner acceptance of the
sealed evidence package.

No partial item receives weighted credit. Technical completion raised P4.2 to
13/15 (86.6667%) and Phase 4 to 38/100 (38.00%), changes of +86.6667 and
+13.00 percentage points respectively. Exact owner acceptance raised P4.2 to
15/15 (100.0000%) and Phase 4 to 40/100 (40.00%), changes of +13.3333 and
+2.00 percentage points from the technical state.

## Verified Results

- All 110 focused non-PostgreSQL P4.2 tests pass with 90.19% branch-enabled
  coverage across `app/hcam/intelligence/rules`.
- The unconditional repository suite passes with 3,862 tests, 12 expected
  PostgreSQL-URL-dependent skips, 119 passing subtests, zero deselections, and
  one locked-dependency deprecation warning.
- The authorized historical compatibility changes preserve explicit P4.0 at
  `0012`, P4.1 at `0013`, and current head at `0014`, including downgrade and
  upgrade transitions through all three revisions.
- P4.0 and P4.1 readiness now verify accepted historical source from local Git
  objects while current P4.2 readiness binds the three authorized pre-change
  test hashes.
- Generated fixtures, Ruff, compileall, Git whitespace validation, the offline
  source/wheel build, the 74-package compatibility check, Phase 3 release and
  analytics contracts, and the existing Phase 3.4 supply-chain evidence check
  all pass.
- Dependency and lock files remain byte-exact. No install, download, network,
  container, camera, media, model, private/Government data, deployment, or
  remote-Git action occurred.

## Explicit Local Limitations

`HCAM_POSTGRES_TEST_URL` is not configured, and D-P4.2-START does not authorize
starting containers. The P4.2 PostgreSQL forced-row-security test therefore
remains an expected skip, and this package makes no local PostgreSQL execution
claim. The migration and CI test job are present for a separately authorized
environment.

A fresh vulnerability-database refresh and new SBOM generation were also not
performed because they would require network or dependency tooling outside the
authorization. The immutable lockfile, installed-package compatibility, and
existing repository supply-chain evidence were verified offline. The complete
results and limitations are recorded in
`contracts/phase-4/p4-2/evidence.json`.

## Acceptance Boundary

The evidence package and canonical component digest are bound by
`contracts/phase-4/p4-2/evidence-package.json`. The exact non-effective owner
statement remains in `contracts/phase-4/p4-2/acceptance-proposal.json`, and its
effective owner acceptance is recorded in
`contracts/phase-4/p4-2/acceptance.json`. P4.2-D is complete, P4.2 is 15/15,
and Phase 4 is 40/100. P4.3 remains unauthorized.
