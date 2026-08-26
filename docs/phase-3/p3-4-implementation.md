# P3.4 Geometry And Event Primitives Implementation

Status: implemented, technically validated, and accepted under
`D-P3.4-ACCEPTANCE` for the immutable clean-source package.

Scope: `phase3.p3_4.generated_only_geometry_and_event_primitives`.

## Implemented Result

P3.4 converts sealed, anonymous, stream-local P3.3 lifecycle metadata into
deterministic image-space analytic events. It adds no camera, decoder, frame,
media, external dataset, identity, cross-camera association, Government
database, watchlist, alert-dispatch, autonomous-action, or deployment path.

The implementation contains:

- normalized finite 2D line and polygon canonicalization with Shapely 2.1.2;
- canonical JSON, WKB, configuration hashes, precision reduction, validity
  rejection, boundary policy, and hysteresis;
- immutable `GeometryRuleV1`, typed visual rule graphs, and constrained CEL over
  a closed scalar context;
- bounded line crossing, zone entry/exit, dwell, occupancy, schedule,
  event-time ordering, duplicate, late-input, and replay state machines;
- deterministic IDs and state scoped to department, assignment, stream,
  camera, tracker epoch, rule version, and anonymous local track;
- generated-only APIs protected by department RBAC, audit reason, approval,
  ETag, default-off settings, and a production activation rejection;
- five additive stores plus the existing transactional outbox;
- identifier-free metrics for geometry, rules, runs, events, buffer/state
  limits, failures, and cleanup;
- five sealed C10 scenario groups with exact expected events, state evidence,
  and 20 identical replays per scenario.

## Hybrid Geometry

Shapely is the bounded real-time predicate implementation. PostgreSQL/PostGIS
is the authoritative persisted geometry path when PostgreSQL is configured.
Approved records bind normalized JSON, canonical WKB, Shapely/GEOS versions,
and digests. The PostGIS migration requires valid 2D SRID-0 line or polygon
geometry, requires database WKB to equal the canonical WKB, and creates a GiST
administrative index.

This is normalized image-space only. It does not represent geography, physical
distance, speed, calibration, homography, or route intelligence.

## Rules And CEL

The visual graph is authoring data. Runtime behavior comes from the validated,
typed graph and checked CEL representation. The graph has closed spatial,
Boolean, temporal, cooldown, and repeat-limit node types with depth, node,
window, and static-cost ceilings.

CEL receives only allowlisted scalar fields and typed-node results. It cannot
access geometry coordinates, URLs, network, files, environment, secrets,
database operations, camera control, media, identity, alerts, or arbitrary
extensions. Rule approval recomputes geometry and CEL bindings so a stored
digest, WKB, kind, or canonical-definition mismatch fails closed.

## Persistence And API

Alembic revision `0011_geometry_events` adds:

| Table | Purpose |
| --- | --- |
| `analytics_geometries` | Immutable canonical line/zone versions |
| `analytics_geometry_rules` | Typed graph, checked CEL, approval, and digests |
| `analytics_geometry_evaluator_runs` | Generated run scope and bounded outcomes |
| `analytics_track_rule_states` | Current anonymous stream-local state only |
| `analytics_events` | Append-only deterministic primitive events |

The API supports geometry draft/list/read/approve, rule compile preview,
rule draft/list/read/approve, sealed generated run creation/read, and event
listing. It accepts no arbitrary lifecycle, coordinate stream, camera locator,
file, URL, image, clip, or external action request.

Events retain `alert_state: not_evaluated`. Outbox publication is a typed
metadata event, not an operational police alert.

## Activation And Limits

`HCAM_ANALYTICS_GENERATED_GEOMETRY_ENABLED` defaults to `false` and is rejected
in production. Generated execution constructs all inputs server-side from an
allowlisted scenario ID and bounded seed.

Initial hard ceilings include 64 rule versions per assignment, 16 candidate
rules per transition, 16,384 states per stream, 64 reorder inputs, and two
seconds of allowed lateness. Overflow, conflicting sequence, stale scope,
geometry drift, invalid schedule, or persistence conflict fails closed; no
partial event claim is promoted.

## Environment Validation

SQLite and the pinned Alpine PostGIS image both passed `0011 -> 0010 -> 0011`.
The disposable PostGIS run verified PostgreSQL 18.6, PostGIS 3.6.4, GEOS
3.14.1, PROJ 9.8.1, the GiST index, validity constraint, and canonical WKB
binding. Alembic drift checks pass after both upgrades, ignore only
extension-owned tables, and still report an intentionally unmanaged table.

A fresh Compose start exposed two silent-success paths. The PostGIS entrypoint's
temporary Unix-socket server could satisfy the original healthcheck, and the
extension-ownership query could trigger SQLAlchemy autobegin before Alembic's
managed transaction. The healthcheck now requires TCP loopback plus a
successful `postgis_lib_version()` query, and extension inspection runs inside
Alembic's transaction. A second new empty volume then retained revision
`0011_geometry_events` and reached API health/readiness successfully.

## Continuing Boundaries

The PostGIS image scan records 54 findings, including 2 critical and 21 high.
No finding is suppressed and no VEX waiver is applied. The image is allowed
only for disposable loopback generated validation and is blocked from pilot or
production deployment until a cleaner image or remediation is selected and
rescanned.

Final P3.4 acceptance, all real media or camera use, P3.5, external datasets,
identity, correlation, watchlists, alerts, deployment, and remote Git actions
remain separate owner decisions.
