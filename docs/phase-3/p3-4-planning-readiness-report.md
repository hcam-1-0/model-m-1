# P3.4 Planning Readiness Report

Status: `ready_for_implementation_authorization`.

Generated on: 2026-08-25.

Scope: `phase3.p3_4.geometry_and_event_primitives.planning_only`.

Canonical planning-package digest:
`E3D0D0DEB5AE20D68AF6A5CE72229BDC63AE55B4200C7E2A011CFA834AFBEBF0`.

The digest covers 19 authorization, accepted-dependency, owner-decision,
planning,
documentation-index, verifier, test, CI, and unchanged dependency-manifest
files. This report is intentionally excluded from its own digest.

## Result

| Result | Count |
| --- | ---: |
| Technical failures | 0 |
| Accepted technical decisions | 4 |
| Manual owner gates | 1 |
| Focused P3.4 verifier tests | 14 passed |
| Cross-phase readiness regression tests | 77 passed |

The accepted P3.3 PostgreSQL evidence and previous full-suite baseline remain
unchanged. No P3.4 database extension, migration, dependency, runtime, or
generated execution was added by the technical-decision synchronization.

## Technical Checks

- all required planning package files exist;
- `D-P3.4-PLAN-AUTH` authorizes planning only and preserves every prohibited
  action;
- the exact accepted P3.3 package digest and accepted repository head match;
- `D-P3.4-001` binds hybrid authoritative PostGIS geometry and exact Shapely
  2.1.2 worker architecture;
- `D-P3.4-002` binds a visual typed rule graph and constrained CEL;
- `D-P3.4-003` binds the balanced deterministic time and replay defaults;
- `D-P3.4-004` binds bounded PostgreSQL/PostGIS state, transactional outbox,
  inherited retention, and C10 evidence;
- only `D-P3.4-START` remains pending and implementation remains false;
- research links resolve only to the recorded primary-source host allowlist;
- geometry, state-machine, event-time, idempotency, persistence, resource,
  retention, evidence, and claim boundaries are explicit;
- PostGIS, Shapely, and CEL remain uninstalled architecture selections;
- root documentation, Phase 3 index, backlog, decision register, contract index,
  and Python CI contain the P3.4 planning boundary and verifier command;
- historical P3.0, P3.1, P3.2, and accepted P3.3 readiness checks remain at
  zero technical failures.

## Pending Owner Gate

`D-P3.4-START`: separate generated-only implementation authorization.

See [the owner decision packet](p3-4-decision-packet.md) for the recommended
options and exact response language.

## Reproduce

```powershell
uv run --locked --extra dev python tools/phase34_readiness.py --strict --json
uv run --locked --extra dev pytest tests/test_phase34_readiness.py -q
uv run --locked --extra dev --extra analytics pytest tests/test_phase3_readiness.py tests/test_phase31_readiness.py tests/test_phase31_implementation_readiness.py tests/test_phase32_entry_readiness.py tests/test_phase32_implementation_readiness.py tests/test_phase33_implementation_readiness.py tests/test_phase34_readiness.py -q
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
