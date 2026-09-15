# P5.2 Owner Decision Packet

Status: owner decisions pending; every option below is non-effective

Select one letter for each decision. The recommended profile is:

`B / C / A / A / A / A / A / A / A / A / A / A`

## D-P5.2-001: Command Workspace Composition

**A. Dashboard cards.** Familiar and simple, but fragments map, status,
workload, and detail context and encourages decorative nesting.

**B. Dense command workspace with filter/explorer rail, central map, inspector,
workload table, and persistent status strip. Recommended.** Preserves the
accepted GIS information architecture while supporting rapid scan, selection,
and authoritative drill-down.

**C. Map-only primary surface.** Maximizes map area but fails the accessible and
low-resource equivalence goal.

**D. Separate pages only.** Strong isolation, but weak situational continuity
and inefficient repeated navigation.

## D-P5.2-002: GIS Data Delivery

**A. Client-only GeoJSON.** Lowest implementation complexity, but limited for
larger datasets and makes payload/property control harder.

**B. Vector tiles only.** Scales spatial rendering, but exact selection,
accessibility, and authoritative pagination still require another contract.

**C. Hybrid bounded feature query, vector tiles, and authoritative list.
Recommended.** Uses each transport for its proper role and keeps map failure
independent of record access.

**D. Raster tiles only.** Strong rendering isolation, but poor feature
interaction, semantic accessibility, and detail linkage.

## D-P5.2-003: Basemap And Network Policy

**A. Local/offline style and tiles by default with an exact future allowlisted
provider adapter. Recommended.** Supports labs and controlled deployments
without leaking viewport or operational context to a public service.

**B. Direct public basemap.** Fastest visual setup, but creates privacy,
availability, credential, CSP, licensing, and supply-chain dependencies.

**C. No basemap.** Safest network posture but weak geographic context.

**D. Open provider plugin ecosystem.** Flexible but too broad for an initial
public-safety command surface.

## D-P5.2-004: Spatial Aggregation And Clustering

**A. Server-authoritative aggregates plus deterministic display clustering.
Recommended.** Coverage, health, blind spots, and workload stay server-owned;
the map may cluster accepted points only for presentation.

**B. Client clustering and aggregation.** Responsive, but risks inconsistent
or incomplete operational conclusions.

**C. Heatmap-only.** Compact but obscures exact counts, missing data, and
drill-down.

**D. Raw points only.** Semantically simple but does not remain usable at scale.

## D-P5.2-005: Situation Summary Semantics

**A. Versioned server snapshot with per-source freshness, completeness, loss,
degradation, revision, and drill-down. Recommended.** Makes uncertainty and
source disagreement explicit and replayable.

**B. Client joins independent queries into one summary.** Avoids a producer
change but creates incoherent windows and revisions.

**C. Cached summary without per-source state.** Efficient but can hide stale or
missing sources.

**D. One composite threat or health score.** Easy to scan but unacceptable
without transparent semantics and risks overstating certainty.

## D-P5.2-006: Time, Ordering, Corrections, And Replay

**A. Bounded UTC window with accepted operational timezone display, separate
event/recorded time, and visible corrections/retractions. Recommended.** Fits
accepted chronology semantics and avoids local-time ambiguity.

**B. Latest state only.** Simple but hides chronology and late correction.

**C. Browser-local time.** Convenient but inconsistent across control rooms.

**D. Unbounded free-range replay.** Powerful, but outside P5.2 resource and
evidence boundaries.

## D-P5.2-007: Workload Prioritization

**A. Server-provided safe priority bands, age, accepted authority class, and
stable tie-breaker. Recommended.** Keeps ranking explainable and governed.

**B. Client-computed risk score.** Flexible but can become an unreviewed threat
assessment.

**C. Chronological order only.** Deterministic but may not support urgent work.

**D. AI narrative ranking.** Outside current model, evidence, and operational
authority.

## D-P5.2-008: Drill-Down And Workspace Persistence

**A. Opaque bounded URL filters, memory-only selection, and future server-owned
workspaces with ETags. Recommended.** Supports shareable non-sensitive state
and safe concurrency without browser persistence of protected data.

**B. Full state in the URL.** Shareable but leaks identifiers, filters,
coordinates, and operational context.

**C. Full local browser storage.** Easy to implement but unsafe across logout,
scope change, and shared workstations.

**D. No persistence.** Safe but inefficient for repeated command workflows.

## D-P5.2-009: Accessibility Equivalence

**A. Synchronized map plus authoritative list/table, non-color state, complete
keyboard/focus behavior, and bounded live announcements. Recommended.** Gives
all operators a route to the same records and actions.

**B. Accessible map annotations only.** Insufficient for dense or failed maps.

**C. Screen-reader summary only.** Loses record-level exploration.

**D. Remove GIS for assistive-technology users.** Creates unequal capability.

## D-P5.2-010: Dynamic Profiles And Multi-Monitor Operation

**A. One capability set and truth model; profiles vary density, concurrency,
renderer quality, and layout only. Independent windows revalidate authority.
Recommended.** Preserves laptop-to-control-room compatibility without feature
or safety downgrade.

**B. Separate product editions.** Easier to optimize independently but causes
semantic and maintenance drift.

**C. Manual hardware presets only.** Predictable but places compatibility work
on operators.

**D. Automatic benchmark-based tuning.** Potentially adaptive but requires
hardware and stress testing outside current authority.

## D-P5.2-011: GIS Renderer And Dependency Scope

**A. MapLibre 2D behind the renderer-neutral adapter, same-origin worker, built-in
clustering, and no Turf, deck.gl, or 3D in the initial slice. Recommended.**
Meets parity and scaling needs with a controlled dependency surface.

**B. Preserve a Leaflet runtime.** Lower WebGL dependence but weaker vector-tile
and style capabilities for the canonical experience.

**C. deck.gl/WebGL composition.** Powerful for large visualization but adds
complexity and another rendering/security surface.

**D. Custom WebGL renderer.** Maximum control with unacceptable engineering and
accessibility cost for P5.2.

## D-P5.2-012: Validation And Evidence Standard

**A. Generated unit, component, contract, story, browser, visual,
accessibility-static, security, deterministic replay, C1/C10/C50, GIS parity,
and later manual assistive-technology evidence. Recommended.** Broadly covers
truth, usability, security, compatibility, and resource behavior.

**B. Browser end-to-end tests only.** Useful but slow and weak for contract and
boundary enumeration.

**C. Visual regression only.** Detects layout drift but not authority, data, or
keyboard errors.

**D. Manual validation only.** Not deterministic or sufficient for repeated
release evidence.

## Effect Of Selection

Selections define a reconciled planning profile only. They do not authorize
implementation, dependencies, routes, migrations, map runtime, network,
cameras, media, real data, models, operational actions, deployment, P5.3, or
remote Git. After selection, the required sequence is:

1. create and seal a reconciled P5.2 planning package;
2. obtain exact owner acceptance of that package;
3. prepare a separate non-effective start package with exact paths,
   dependencies, fixtures, commands, bounds, evidence, and stop conditions;
4. obtain exact start authorization before implementation.
