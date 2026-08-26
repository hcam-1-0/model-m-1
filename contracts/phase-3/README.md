# Phase 3 Analytics Contracts

This directory contains reviewed, deterministic snapshots for the additive
Phase 0-3 API/database surface and the model-independent P3.0 analytics boundary:

- `analytics-contracts.json`: JSON schemas for assignment, versioned metadata
  events including stream-local lifecycle v2, draft taxonomy, normalized
  geometry/schedules, and the runtime adapter boundary;
- `fixtures/`: generated-only golden documents used for producer/consumer
  compatibility and deterministic serialization tests, including an explicitly
  unconfigured runtime result.
- `openapi.json`: the current FastAPI contract, including the activation-blocked
  analytics-assignment API;
- `database.json`: the current Alembic `0011_geometry_events` schema, including
  assignments, generated runs, anonymous stream-local tracking, normalized
  geometry/rules/events, and database guard constraints.
- `p3-0-owner-decisions.json`: the machine-readable owner approval record for
  P3-G1 through P3-G3, including the exact Tier A scope, synthetic-lab metadata
  policy, accountable owner, optional reviewer, and non-authorization boundary.
  P3-G4 records the accountable-owner self-review exception and effective P3.0
  acceptance; the same owner-review mode now applies to later model promotion,
  operational geometry, datasets, and deployment.
- `p3-1-authorization.json`: the exact `D-P3.1-001` planning authorization,
  generated-only source policy, nine work packages and exit gates, developer
  hardware profile, accountable-owner review mode, and explicit exclusions.
  It authorizes bounded P3.1 implementation but does not claim implementation
  completion or authorize external downloads, inference, cameras/media, P3.2,
  pilots, or deployment.
- `p3-1/`: the generated-only P3.1 implementation package. It contains the six
  versioned evaluation contract schemas, seven generated fixture/QA/split
  suites, 11 metadata-only blocked candidate manifests, source dossier, metric
  golden report, baseline run, and evidence index. All artifacts are JSON,
  bounded to one MiB, canonical, hashed, media-free, and reproducible offline.
- `p3-1-acceptance.json`: the exact `D-P3.1-ACCEPTANCE` owner decision bound to
  the unchanged 28-artifact package digest, clean baseline commit, reviewed
  repository head, accepted limitations, and explicit non-authorization.
- `p3-2-acceptance.json`: the exact accepted generated-input CPU detection
  package and continuing non-authorization boundary.
- `p3-3-*-source.json`, policy/runtime/generated-suite manifests, and
  `p3-3/evaluation-report.json`: exact tracker/evaluator provenance and
  generated-only parity evidence.
- `p3-3-sbom.cdx.json`: deterministic CycloneDX runtime inventory generated
  from the audited lock.
- `p3-3-validation-evidence.json`: bounded local test, PostgreSQL, coverage,
  package, audit, and prohibited-input results.
- `p3-3-acceptance.json`: exact-digest owner acceptance of the immutable
  generated-only P3.3 package and its continuing non-authorization boundary.
- `p3-4-planning-authorization.json`: exact planning-only authorization,
  accepted P3.3 baseline, deliverables, and prohibited actions.
- `p3-4-entry-gates.json`: accepted geometry-engine, rule-semantics,
  event-time, and persistence/evidence decisions plus the pending separate
  implementation-start gate.
- `p3-4-owner-decisions.json`: exact owner-selected hybrid geometry,
  visual/CEL rules, deterministic time, and bounded persistence baseline with
  continuing non-authorization.
- `p3-4-start-authorization.json`: exact baseline-bound generated-only local
  implementation authorization, authorized work, and continuing exclusions.
- `p3-4-c10-evidence.json`: five sealed generated geometry/event scenarios,
  expected outputs, state traces, and deterministic replay hashes.
- `p3-4-dependencies.json`, `p3-4-sbom.cdx.json`, and
  `p3-4-container-vulnerability-review.json`: exact Python/native provenance,
  SBOM, and the unresolved PostGIS image deployment block.
- `p3-4-validation-evidence.json`: test, coverage, migration, packaging,
  dependency-audit, Docker, and prohibited-input evidence.
- `p3-4-acceptance.json`: exact-digest owner acceptance of the immutable
  generated-only P3.4 package and its continuing non-authorization boundary.
- `p3-5-planning-authorization.json`: exact planning-only authorization based
  on accepted P3.4, with all implementation and artifact actions prohibited.
- `p3-5-research-sources.json`: primary-source, no-download research evidence
  for OCR, Unicode, registration-mark constraints, fonts, and synthetic data.
- `p3-5-artifact-review-proposal.json`: metadata-only recommended `A/A/A/A`
  acquisition proposal with eight blocked artifact slots, exact source
  identities where available, empty network authority, and unresolved hashes.
- `p3-5-owner-decisions.json`: exact owner approval of the recommended
  `A/A/A/A` technical baseline without implementation authority.
- `p3-5-artifact-research-authorization.json`: proposal-digest-bound authority
  for exactly seven HTTPS quarantine downloads with no redirects, proxies,
  extraction, runtime loading, or implementation.
- `p3-5-artifact-review-evidence.json`: exact SHA-256 values, passive archive,
  traineddata/font inspection, Defender evidence, and remaining runtime blocks.
- `p3-5-artifact-sbom.cdx.json`: CycloneDX 1.6 inventory for all seven exact
  artifacts, source identities, licenses, and blocked runtime state.
- `p3-5-artifact-model-cards.json`: five OCR roles, intended generated-only use,
  limitations, and continuing execution blocks.
- `p3-5-runtime-review-proposal.json`: Python 3.12 package/runtime proposal with
  no package download, dependency change, or implementation authority.
- `p3-5-entry-gates.json`: four approved technical choices and the remaining,
  prerequisite-blocked `D-P3.5-START` statement.
- `p3-5-start-authorization.json`: the exact received start intent, four
  satisfied technical prerequisites, the in-progress exact artifact review,
  empty implementation allowlists, and continuing prohibitions.

Verify all tracked snapshots:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py check
uv run --locked --extra dev python tools/release_contracts.py check
uv run --locked --extra dev python tools/phase31_readiness.py --strict
uv run --locked --extra dev python tools/phase31_contracts.py check --require-clean-source
uv run --locked --extra dev python tools/phase31_implementation_readiness.py --strict
uv run --locked --extra dev python tools/phase32_entry_readiness.py
uv run --locked --extra dev --extra analytics python tools/phase32_implementation_readiness.py
uv run --locked --extra dev --extra analytics python tools/phase33_tracking_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase33_sbom.py check
uv run --locked --extra dev --extra analytics python tools/phase33_implementation_readiness.py --require-clean-source --require-acceptance
uv run --locked --extra dev python tools/phase34_readiness.py --strict
uv run --locked --extra dev --extra analytics python tools/phase34_c10_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase34_supply_chain.py check
uv run --locked --extra dev --extra analytics python tools/phase34_implementation_readiness.py --require-clean-source --require-acceptance
uv run --locked --extra dev python tools/phase35_readiness.py --strict
uv run --locked python tools/phase35_artifact_research.py --all --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked python tools/phase35_artifact_inspect.py --root 'E:\h-cam-research-cache\phase-3\p3-5'
```

Rewriting snapshots requires an explicit review acknowledgement:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/release_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/phase31_contracts.py write --acknowledge-generated-only-evidence
```

Taxonomy and geometry fixtures remain `draft`. The accepted P3.2 and P3.3
runtime slices are generated-only, default-off, and production-forbidden.
P3.4 generated-only local implementation is built, technically validated, and
accepted under `D-P3.4-ACCEPTANCE`. The PostGIS validation image remains
deployment-blocked.
These contracts do not authorize camera access, raw-media persistence, external
datasets, identity, cross-camera association, Government matching, alerts,
or deployment. P3.5 technical choices are approved, and only the exact seven
quarantine downloads recorded under `D-P3.5-ARTIFACT-RESEARCH` are authorized.
Receipt of `D-P3.5-START` before exact review completion does not authorize
runtime, dependency, implementation, media, or deployment action.
