# P3.4 Planning Readiness Report

Status: `ready_for_owner_decisions`.

Generated on: 2026-08-25.

Scope: `phase3.p3_4.geometry_and_event_primitives.planning_only`.

Canonical planning-package digest:
`8EA8423EE301BBBDC1AE37E5A45173D2D0A6563025E4ACD7DE235EB8E66B7D3D`.

The digest covers 17 authorization, accepted-dependency, planning,
documentation-index, verifier, test, CI, and unchanged dependency-manifest
files. This report is intentionally excluded from its own digest.

## Result

| Result | Count |
| --- | ---: |
| Technical failures | 0 |
| Manual owner gates | 5 |
| Focused verifier tests | 12 passed |
| Full repository tests | 672 passed |
| Full repository subtests | 119 passed |
| Skipped PostgreSQL integration tests | 6 |

The six PostgreSQL tests require `HCAM_POSTGRES_TEST_URL` and were skipped in
the full local suite. Accepted P3.3 PostgreSQL evidence remains unchanged. The
full run also reported one existing Starlette deprecation warning concerning
the compatibility test client; it is not introduced by P3.4 planning.

## Technical Checks

- all required planning package files exist;
- `D-P3.4-PLAN-AUTH` authorizes planning only and preserves every prohibited
  action;
- the exact accepted P3.3 package digest and accepted repository head match;
- all five P3.4 entry gates remain pending and implementation remains false;
- research links resolve only to the recorded primary-source host allowlist;
- geometry, state-machine, event-time, idempotency, persistence, resource,
  retention, evidence, and claim boundaries are explicit;
- Shapely remains a researched candidate and is absent from `pyproject.toml`
  and `uv.lock`;
- root documentation, Phase 3 index, backlog, decision register, contract index,
  and Python CI contain the P3.4 planning boundary and verifier command;
- historical P3.0, P3.1, P3.2, and accepted P3.3 readiness checks remain at
  zero technical failures.

## Pending Owner Gates

1. `D-P3.4-001`: geometry engine and precision model.
2. `D-P3.4-002`: spatial and event semantics.
3. `D-P3.4-003`: event time, schedules, replay, and deduplication.
4. `D-P3.4-004`: persistence, limits, retention, and validation.
5. `D-P3.4-START`: separate generated-only implementation authorization.

See [the owner decision packet](p3-4-decision-packet.md) for the recommended
options and exact response language.

## Reproduce

```powershell
uv run --locked --extra dev python tools/phase34_readiness.py --strict --json
uv run --locked --extra dev pytest tests/test_phase34_readiness.py -q
uv run --locked --extra dev --extra analytics pytest -q
```

`--strict` fails only on technical planning errors. Add `--require-decisions`
when a workflow should return exit code 2 until all owner gates are resolved.

## Claim Boundary

This package proves planning consistency and preserves prior accepted behavior.
It does not prove an implemented geometry evaluator, real-camera accuracy,
operational performance, legal approval, production readiness, or deployment.
It authorizes no dependency acquisition, migration, API, runtime event
execution, media/data access, identity, ReID, cross-camera linkage, Government
matching, operational alerting, autonomous action, P3.5, or remote Git action.
