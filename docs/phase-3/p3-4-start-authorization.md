# P3.4 Generated-Only Implementation Authorization

Decision: `D-P3.4-START`.

Status: authorized by `mayank-admin` on 2026-08-25.

Machine-readable record:
[`p3-4-start-authorization.json`](../../contracts/phase-3/p3-4-start-authorization.json).

The owner stated:

> I authorize D-P3.4-START

The statement explicitly identifies the remaining gate and therefore activates
the implementation boundary defined in the accepted
[P3.4 decision packet](p3-4-decision-packet.md). It is bound to planning digest
`E3D0D0DEB5AE20D68AF6A5CE72229BDC63AE55B4200C7E2A011CFA834AFBEBF0`
at repository commit `f9a798f5103da1249ecc5b3e86eb4de7166d8fb9`.

## Authorized

- acquire and audit exact PostGIS, Shapely, GEOS, CEL, and transitive artifacts;
- implement the local default-off and production-forbidden P3.4 geometry,
  typed-rule, event-time, persistence, API, outbox, audit, metrics, retention,
  and generated C10 work in the accepted plan;
- add additive PostgreSQL/PostGIS migration behavior and SQLite compatibility;
- run local generated-only tests, evidence generation, documentation, and local
  checkpoint commits.

## Not Authorized

- physical cameras, ONVIF media, Sentinel video, URLs, paths, or media bytes;
- real, public, private, Government, police, scraped, or external datasets;
- training, fine-tuning, real-world accuracy, or deployment-performance claims;
- face, biometric, identity, ReID, cross-camera linkage, watchlists, vehicle
  owner lookup, or Government database matching;
- operational alerts, autonomous action, enforcement, pilot, production,
  statewide deployment, P3.5, or remote Git operations.

## Acceptance

This authorization permits implementation and evidence generation. It does not
accept the resulting implementation. Final acceptance requires a clean-source,
exact-digest evidence package and a separate owner decision.
