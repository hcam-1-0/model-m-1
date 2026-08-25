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
- `database.json`: the current Alembic `0010_generated_tracking` schema,
  including assignments, generated runs, anonymous stream-local tracking, and
  database guard constraints.
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
```

Rewriting snapshots requires an explicit review acknowledgement:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/release_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/phase31_contracts.py write --acknowledge-generated-only-evidence
```

Taxonomy and geometry fixtures remain `draft`. The accepted P3.2 and P3.3
runtime slices are generated-only, default-off, and production-forbidden.
P3.4 generated-only local implementation is authorized by `D-P3.4-START` under
the accepted decisions. Final implementation acceptance remains pending.
These contracts do not authorize camera access, raw-media persistence, external
datasets, identity, cross-camera association, Government matching, alerts,
deployment, or P3.4 implementation.
