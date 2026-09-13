# P5.2 Command And Situational Awareness Architecture

Status: proposed, non-effective, implementation unauthorized

Authority: `D-P5.2-PLAN-AUTH`

## Objective

P5.2 turns accepted read-only intelligence, alert, investigation, camera,
stream, and platform-health projections into one command workspace. It must
answer five questions without overstating certainty:

1. What requires attention now?
2. Where is it occurring?
3. Which source and time window support that view?
4. What is missing, stale, degraded, corrected, or unauthorized?
5. Which authoritative list or detail view verifies the aggregate?

The workspace is a situational index and drill-down surface. It is not an
automated threat assessor, dispatch console, identity resolver, camera control
panel, evidence viewer, or substitute for mandatory human review.

## Workspace Composition

The recommended composition is a dense, role-oriented command workspace:

```text
+--------------------------------------------------------------------------+
| Command | Department | UTC/local window | Freshness | Degradation | User |
+------------------+-----------------------------------+-------------------+
| Filters / Layers | Authoritative 2D GIS              | Inspector         |
| Time window      | Selected cameras, alerts,         | Selected record   |
| Source states    | investigations, resources,        | provenance        |
| Saved workspace | coverage and health projections   | source freshness  |
|                  |                                   | safe drill-down   |
+------------------+-----------------------------------+-------------------+
| Workload / review / health / coverage authoritative list or table         |
+--------------------------------------------------------------------------+
```

On constrained screens, regions become sequential landmarks: status, filters,
map or list, inspector, and workload. The map is never the only path to a
record. On multi-monitor systems, independently opened views share only opaque
workspace identifiers and server-confirmed filters; they do not share tokens,
raw records, or map payloads through browser storage.

## Data Flow

```text
Operator
  -> P5.1 session, department, route and capability projection
  -> Command query coordinator
      -> operations summary snapshot
      -> bounded viewport features or vector tiles
      -> authoritative alert/review/investigation/camera/stream lists
      -> platform health and degradation state
  <- typed responses with source window, freshness, completeness and revision
  <- invalidation events only
  -> selected authoritative detail query
```

The browser never queries PostGIS, object storage, cameras, ONVIF, RTSP,
brokers, model runtimes, or external map providers directly. The P5.1 typed
client remains the only HTTP boundary. The accepted event client invalidates
queries and schedules bounded refetches; it never creates or changes an alert,
review, investigation, camera state, or health state.

## Authoritative Situation Snapshot

A future producer contract should return one versioned envelope:

```text
SituationSnapshot
  snapshot_id: opaque
  department_scope: opaque projection
  window: {start_utc, end_utc, display_timezone}
  as_of_utc: timestamp
  revision: opaque
  sources[]:
    source: bounded enum
    observed_at: timestamp or null
    stale_at: timestamp or null
    completeness: complete | partial | unavailable | unknown
    loss_count: bounded integer or null
    reason: sanitized enum or null
  aggregates:
    proposed_alerts
    mandatory_review
    investigations
    camera_coverage
    stream_health
    degradation
```

Rules:

- every aggregate declares the exact source, filter, time window, denominator,
  and authoritative drill-down operation;
- missing and denied sources remain visible as unknown or unavailable;
- counts from different windows are not added together;
- corrected or retracted records are reflected by snapshot revision and detail
  history;
- the client does not compute an overall threat, guilt, identity, coverage, or
  health score;
- no aggregate can trigger notification, dispatch, enforcement, or camera
  action.

## GIS Architecture

### Delivery Lanes

1. **Feature lane:** bounded GeoJSON-like summaries for small result sets and
   exact selected features.
2. **Tile lane:** bounded vector tiles for larger camera, coverage, and
   aggregate layers.
3. **List lane:** authoritative cursor-paginated records independent of map
   rendering.
4. **Detail lane:** one typed operation per selected record; map payloads never
   contain protected detail fields.

Every lane uses the same department, time-window, layer, filter, freshness,
and revision semantics. The list lane remains usable when WebGL, the worker,
tiles, geometry, or the map renderer fails.

### Viewport Contract

- WGS 84 longitude/latitude at the browser boundary;
- west/south/east/north plus bounded zoom and optional cursor;
- finite numbers only, latitude within `[-90, 90]`, longitude within
  `[-180, 180]`, and explicit antimeridian policy;
- bounded area, feature count, tile count, response size, property count, and
  time window;
- exact layer allowlist and no arbitrary collection, SQL, expression, source,
  style, glyph, sprite, or URL parameters;
- deterministic clipping/generalization metadata where applied;
- no coordinates in client telemetry or URLs.

### Layer Registry

Each layer requires a typed registry entry containing:

- stable layer ID, version, title key, feature kind, geometry type, source
  operation, minimum role, and department behavior;
- time semantics, freshness threshold, completeness behavior, legend, visual
  priority, clustering policy, and maximum detail zoom;
- list/detail route, accessible label template, and empty/error/degraded copy
  keys;
- sensitive-field prohibition, retention behavior, and observability name;
- renderer requirements and low-resource fallback.

Unknown layers fail closed. A style cannot introduce a new source or field.

### Display Clustering And Coverage

Map clustering is a display optimization only. Cluster counts carry the
declared viewport and snapshot window and drill into the authoritative list.
Coverage, blind spots, and health are server-owned projections with stated
denominators, source timestamps, confidence/completeness, and limitations.
The browser may filter or format accepted projections but may not derive an
operational coverage conclusion from camera icons or local geometry.

## Workload And Review Views

The command workload rail combines links to separate authoritative queues:

- proposed alerts awaiting mandatory review;
- review age and safe server-provided priority band;
- investigations by accepted lifecycle state;
- cameras and streams by explicit health/freshness state;
- platform degradation and unavailable dependencies.

The rail may sort by server-provided priority band, age, accepted authority
class, and stable tie-breaker. It must not create a client-only risk score,
identity match, suspicion ranking, or automated recommendation. Mutating
review, alert, and investigation actions remain in P5.4/P5.5 workflows.

## Time, Ordering, And Corrections

- transport and storage timestamps are UTC;
- the operator selects a bounded shared window;
- display uses the accepted operational timezone and explicitly labels it;
- event time and recorded time remain distinct;
- late, corrected, retracted, replayed, or partially ordered records retain
  visible state;
- latest-state summaries link to chronology where available;
- free-range replay is not part of P5.2.

## Resource Profiles

| Profile | Same semantics | Rendering and concurrency policy |
| --- | --- | --- |
| Low resource | All lists, details, status, accessibility, and safety states | List-first admission, reduced visible features, lower tile/query concurrency, static coverage summaries, no animation |
| Enhanced workstation | Same | Interactive 2D map, clustering, bounded prefetch, richer inspector layout |
| Control room | Same | Multi-panel and independent-window layouts, higher bounded concurrency, larger visible workspace, no extra authority |
| Future server | Same | Server-side tiling and aggregation capacity may increase, while browser limits and contracts stay bounded |

Profiles change density, concurrency, rendering quality, and optional
prefetch. They never remove mandatory review, hide degraded state, widen
authorization, change operational meaning, or select a more privileged data
source.

## Responsive And Multi-Monitor Rules

- preserve one H1 and stable landmarks;
- no overlapping toolbar, map, inspector, or table regions;
- fit controls at 200 percent zoom and narrow reflow except the bounded map
  canvas itself;
- maintain a visible hint of list/detail content when the map dominates;
- independent windows revalidate session and department scope;
- scope changes, logout, revocation, or kill switches close or deny every
  window consistently;
- no sensitive state in `localStorage`, `sessionStorage`, broadcast-channel
  payloads, window names, or URL query values.

## Dependency Position

The proposed initial dependency is MapLibre GL JS behind
`@hcam/gis-contracts`. It is not installed by this plan. The implementation
start package must freeze an exact version, integrity/provenance evidence,
license, SBOM entry, bundle budget, same-origin worker strategy, CSP changes,
browser matrix, and rollback. Turf, deck.gl, 3D terrain, public geocoders, and
public basemaps are excluded from the initial slice unless separately decided
and authorized.

## Closed Runtime Boundary

This architecture does not authorize source import, frontend implementation,
dependency changes, browser execution, backend routes, migrations, tiles,
providers, cameras, media, real data, models, operational action, containers,
Kubernetes, deployment, or remote Git.
