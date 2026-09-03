# P3.4 Planning Authorization

Decision: `D-P3.4-PLAN-AUTH`

Status: planning authorized by `mayank-admin` on 2026-08-25.

Machine-readable record:
[`p3-4-planning-authorization.json`](../../contracts/phase-3/p3-4-planning-authorization.json).

## Owner Statement

The owner submitted:

> p3.4 authoriz and continue

The statement followed a request for `D-P3.4-PLAN-AUTH`. It is therefore
recorded as planning authorization only. It does not silently authorize the
implementation gate described by `D-P3.4-START`.

## Authorized Work

- inspect the accepted P3.3 contracts and generated evidence;
- research primary sources for spatial predicates, event time, schedules,
  idempotency, and property-based testing;
- define image-space geometry, rule, event, state, and replay semantics;
- design storage, APIs, RBAC, audit, observability, retention, and resource
  boundaries;
- specify deterministic generated scenarios and acceptance evidence;
- prepare owner decisions and an implementation authorization statement.

## Not Authorized

No runtime geometry or event evaluator may be implemented. No dependency may
be added or downloaded. No migration, API, worker, generated execution, media
path, camera access, external dataset access, identity, ReID, cross-camera
linkage, watchlist, Government database matching, operational alert, autonomous
action, deployment, P3.5 work, or remote Git action is authorized.

## Dependency

P3.3 is accepted under `D-P3.3-ACCEPTANCE` for package digest
`0BE4154E28A4D1A18AC8DA9F8D018CDBEB18F0457DDD1ECC2109D60A956ACA96`.
P3.4 may plan against its anonymous stream-local lifecycle contract without
changing that accepted decision.
