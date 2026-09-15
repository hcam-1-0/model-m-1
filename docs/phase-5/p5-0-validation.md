# P5.0 Validation Plan And Record

Status date: 2026-09-06

Authority: exact generated-only validation under `D-P5.0-START`

## Validation Boundary

Validation is local and uses only deterministic generated fixtures. It does
not start a frontend, map renderer, server, worker, container, Kubernetes
cluster, camera connection, media path, provider connection, model, or
inference runtime. It does not use Government, police, private, biometric,
vehicle, owner, registration, watchlist, investigation, case, or evidence data.

No dependency or lockfile change is permitted. The repository's previously
established full virtual environment is used directly for validation. An
earlier offline `uv` invocation materialized a worktree-local environment from
the existing cache before the missing analytics extra was detected; no network
was used. All subsequent checks use the established environment directly, and
the side effect is disclosed in evidence rather than treated as a product
artifact.

## Required Checks

### Focused Contract Suite

The eight exact P5.0 test modules validate:

- strict field, type, identifier, timestamp, size, count, and unknown-field
  bounds;
- catalogue uniqueness, producer coverage, version, authority, freshness,
  department scope, and gap classification;
- route grammar, URL-state minimization, journey reachability, server
  confirmation, conflict, recovery, and correction;
- Point, LineString, Polygon, and MultiPolygon validation, viewport handling,
  confidence/uncertainty pairing, parity completeness, 2D authority, list
  equivalence, and default-off 3D;
- accessibility category coverage, alternatives, contrast, token constraints,
  reduced motion, density, and locale invariants;
- browser boundary closure, capability ordering, prohibited fields,
  registration-like text rejection, and safe problems;
- deterministic materialization of 720 operator cases and 96 GIS cases;
- exact start/planning hashes, authorized paths, prohibited-import absence,
  closed remote and P5.1 gates, and evidence presence behavior.

### Full Repository Regression

The full locked repository test suite must pass from the Phase 5 worktree.
This confirms P5.0 did not alter accepted Phase 0 through Phase 4 behavior.
Skipped or environment-dependent tests are reported as limitations and are
not converted into passes.

### Static Quality

Ruff checks the thirteen operator-application modules, eight P5.0 test modules,
and two P5.0 tools. The readiness tool parses source imports and rejects
network, camera/media, model-runtime, and Kubernetes libraries in the P5.0
package.

### Branch Coverage

The `app/hcam/operator_application` package must reach at least 90 percent
branch coverage. Coverage is measured only with generated fixtures. A high
coverage result does not establish browser, integration, accessibility,
performance, or operational readiness.

### Package Build

The existing locked build tool creates source and wheel artifacts without a
new dependency. Build artifacts are validation outputs only and are not
committed as product source.

### Readiness And Evidence

`tools/phase50_readiness.py` checks exact package hashes, paths, catalogues,
case counts, security boundaries, and closed gates. Before sealing evidence,
its core checks must pass while the evidence-presence gate remains optional.
After sealing, `--require-evidence` must pass.

`tools/phase50_evidence.py` hashes every authorized implementation, contract,
fixture, test, tool, and documentation component. It writes only the exact
allowlisted evidence, evidence package, and non-effective acceptance-proposal
paths. The technical commit, test counts, branch coverage, limitations, and
environment boundary are recorded.

## Commands

The authoritative command forms use the repository's existing interpreter and
tools with the worktree `app` directory on the import path where required:

```powershell
$python = 'C:\Users\Lenovo\Documents\ChatGPT\h cam 2.0\.venv\Scripts\python.exe'
$ruff = 'C:\Users\Lenovo\Documents\ChatGPT\h cam 2.0\.venv\Scripts\ruff.exe'
$env:PYTHONPATH = (Resolve-Path .\app).Path

& $python -m pytest -q tests/test_phase50_contract_bounds.py `
  tests/test_phase50_contract_catalogue.py tests/test_phase50_journeys.py `
  tests/test_phase50_gis_contracts.py tests/test_phase50_accessibility.py `
  tests/test_phase50_security.py tests/test_phase50_generated_fixtures.py `
  tests/test_phase50_readiness.py

& $python -m pytest -q
& $python -m pytest --cov=hcam.operator_application --cov-branch `
  --cov-report=term-missing -q tests/test_phase50_*.py
& $ruff check app/hcam/operator_application tests/test_phase50_*.py `
  tools/phase50_evidence.py tools/phase50_readiness.py
& $python -m build
& $python tools/phase50_readiness.py --json
```

The final evidence command is run only after the local technical commit exists
and exact validation counts are known.

## Acceptance Criteria

- All 40 exact additive paths exist and only five authorized status files may
  be synchronized.
- The accepted planning and start package hashes remain exact.
- At least 320 generated operator cases pass; the implementation provides 720.
- Exactly 96 GIS parity cases pass across all twelve categories.
- Operator-application branch coverage is at least 90 percent.
- Focused tests, full regression, Ruff, build, and readiness pass offline.
- No credential, secret, locator, raw media, registration-like identifier,
  provider address, or operational action enters generated fixtures.
- No frontend, map, media, backend, provider, model, container, Kubernetes,
  deployment, P5.1, or remote Git gate opens.
- Evidence is reproducible and separately accepted by the owner.

## Current Validation Checkpoint

The focused P5.0 implementation is healthy:

- 47 focused tests passed;
- operator-application branch coverage is 97.53 percent;
- Ruff passed for all exact P5.0 source, test, and tool paths;
- readiness passed before evidence was required;
- source and wheel package builds completed with no dependency or lock change;
- 720 deterministic operator cases and 96 deterministic GIS parity cases
  passed the generated-payload boundary.

The monolithic 4,234-test repository run exceeded its 600-second process
limit. A deterministic, non-overlapping file-shard rerun used `F:` temporary
storage after `C:` exhausted its free space during the first attempt. That
rerun accounted for every collected test: **4,208 passed, 16 skipped, and 10
failed**.

All ten failures are historical Phase 4 readiness checks rather than P5.0
contract tests:

- P4.2: two failures from current-working-tree immutable dependency hashes;
- P4.3: two failures from the inherited `pyproject.toml` dependency hash;
- P4.4: two failures from the same dependency-hash design;
- P4.5: one downstream predecessor-readiness failure;
- P4.6: one downstream historical-baseline failure;
- P4.7: two generated-artifact byte comparisons affected by checkout line
  endings.

The Phase 4 checks combine historical acceptance with mutable working-tree byte
hashes. Some expected Python-file hashes represent CRLF bytes while the Git
blobs and current checkout use LF; P4.7 generated JSON has the inverse checkout
conversion. The shared `pyproject.toml` expected hash in the P4.2 through P4.4
chain does not match its current LF or CRLF form and was not found in a
committed `pyproject.toml` revision. Git reports these historical files as
unmodified.

The P5.0 start allowlist does not permit edits to those historical tools,
tests, packages, or accepted artifacts. Therefore the full-regression gate,
evidence seal, 7/8 technical credit, and owner acceptance proposal remain
closed until a separate narrow compatibility amendment is authorized and
validated. P5.0 source must not be weakened to hide the historical failure.

The host policy also declined recursive cleanup of the worktree-local cached
environment and earlier pytest temporary directories. They remain ignored,
uncommitted environment artifacts. Subsequent regression temporary storage was
redirected to `F:\HCAM-P5-TestTemp` as previously approved by the owner.

## Progress Rule

Passing technical validation and sealing the exact evidence package may earn
at most **7/8 P5.0 points**, which is **87.5000% of P5.0** and **7/100
(7.0000%) of Phase 5**. The final point is withheld until the owner accepts the
exact evidence package. P5.0 acceptance would reach **8/8 (100.0000%)** and
Phase 5 would reach **8/100 (8.0000%)**. P5.1 remains a separate future gate.
