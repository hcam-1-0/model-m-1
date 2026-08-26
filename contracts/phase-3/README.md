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
- `p3-5-artifact-review-acceptance.json`: exact package-digest and evidence-hash
  owner acceptance with all runtime and implementation boundaries preserved.
- `p3-5-artifact-sbom.cdx.json`: CycloneDX 1.6 inventory for all seven exact
  artifacts, source identities, licenses, and blocked runtime state.
- `p3-5-artifact-model-cards.json`: five OCR roles, intended generated-only use,
  limitations, and continuing execution blocks.
- `p3-5-runtime-review-proposal.json`: Python 3.12 package/runtime proposal with
  no package download, dependency change, or implementation authority.
- `p3-5-runtime-research-authorization.json`: digest-bound authority for an
  external binary-wheel dependency closure, SBOM, scans, audit, and import-only
  proof with no repository dependency or model-runtime authority.
- `p3-5-runtime-research-evidence.json`: exact CPython and binary-wheel closure,
  scan and audit results, guarded import behavior, external evidence hashes,
  and continuing implementation blocks.
- `p3-5-runtime-sbom.cdx.json`: CycloneDX 1.6 inventory of all 67 packages, 67
  wheels, and 185 native files, with every component runtime unauthorized.
- `p3-5-runtime-license-review.json`: normalized metadata for all 67 package
  licenses and review flags; it grants no legal or redistribution approval.
- `p3-5-entry-gates.json`: four approved technical choices, accepted artifact
  and runtime evidence, and the completed final `D-P3.5-START` gate.
- `p3-5-start-authorization.json`: the effective digest-bound generated-only
  start, five exact loadable artifacts, two reviewed-but-blocked Tesseract
  artifacts, an empty network allowlist, and continuing prohibitions.
- `p3-5-anpr-contracts.json`: reviewed W1 schemas and policy constants for the
  seed-only generated request, visible non-issuable `SYN` token, default-off
  execution, prohibited inputs, resource ceilings, and zero retention.
- `fixtures/p3-5-generated-request-v1.json`: canonical seed-only generated
  request with no plate text, file, URL, bytes, camera, or identity field.
- `fixtures/p3-5-sealed-splits-v1.json`: digest-bound 20-entry W3 split
  manifest with independent seed namespaces, final-test-only logical holdouts,
  and no token text or token-derived commitment.
- `fixtures/p3-5-ground-truth-crop-v1.json`: canonical W4 model-free
  localization result and ephemeral-crop descriptor with generated lineage,
  bounded geometry, and no pixels or plate text.
- `p3-5-latin-ocr-evaluation.json`: canonical W5 identifier-free generated
  aggregate evidence for exact `OCR-L0` and `OCR-L1`, with no OCR strings,
  alternatives, samples, regions, pixels, or final-test use.

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
uv run --locked --extra dev python tools/phase35_contracts.py check
uv run --locked python tools/phase35_latin_ocr.py check-evidence
uv run --locked python tools/phase35_artifact_research.py --all --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked python tools/phase35_artifact_inspect.py --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked --extra dev python tools/phase35_runtime_research.py all --root 'E:\h-cam-research-cache\phase-3\p3-5-runtime'
```

Rewriting snapshots requires an explicit review acknowledgement:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/release_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/phase31_contracts.py write --acknowledge-generated-only-evidence
uv run --locked --extra dev python tools/phase35_contracts.py write --acknowledge-reviewed-change
```

Taxonomy and geometry fixtures remain `draft`. The accepted P3.2 and P3.3
runtime slices are generated-only, default-off, and production-forbidden.
P3.4 generated-only local implementation is built, technically validated, and
accepted under `D-P3.4-ACCEPTANCE`. The PostGIS validation image remains
deployment-blocked.
These contracts do not authorize camera access, raw-media persistence, external
datasets, identity, cross-camera association, Government matching, alerts,
or deployment. P3.5 technical choices, exact artifact evidence, and restricted
runtime evidence are owner accepted. The final digest-bound `D-P3.5-START`
authorizes only the enumerated local generated-only work packages, five exact
artifacts, and reviewed external runtime with zero network access. Cameras,
media, real/private/Government data, training, Tesseract execution, deployment,
P3.6, and remote Git operations remain prohibited.
`P35-W1` adds only the reviewed ANPR contracts and fail-closed guardrails. It
does not add a generator, OCR runtime, artifact loader, API, worker, migration,
or persistence path.
`P35-W3` adds deterministic in-memory token generation and token-free sealed
split manifests. Logical holdout labels do not load fonts, render images, run
OCR/models, or widen W2 or later-package authority.
`P35-W4` adds a stdlib-only procedural geometry marker, exact ground-truth
localization, and a bounded ephemeral crop. It loads no model, font, artifact,
or media and persists neither pixels nor generated plate text.
`P35-W5` adds a code-defined generated Latin renderer and exact external
`OCR-L0`/`OCR-L1` adapters. Raw OCR exists only in memory; tracked evidence is
identifier-free aggregate data. Frozen final-test samples remain unopened.
