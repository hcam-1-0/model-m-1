# P5.2 Reconciled Planning R1

Status: non-effective; exact owner planning acceptance pending

Decision profile: `B+GIS/C/A+guarded-D/A/A/A/A/A/A/A/D/A`

Source package: `P5.2-PLANNING-R0`

## Reconciliation Result

All twelve decisions are selected. The owner clarification establishes this
product hierarchy:

1. **H-CAM Command Center is the primary operational dashboard and default
   command landing surface.**
2. **H-CAM GIS Center is a connected specialist dashboard for deeper spatial
   work.** It is important but not the main product surface.
3. Both consume one shared GIS domain and the same server-authoritative
   contracts. GIS Center does not fork data, authorization, state semantics, or
   operational truth.
4. Command Center receives more grouped pages and detailed views so operators
   do not have to leave the main dashboard for normal command workflows.

The R0 workstream total remains 12 points. The clarification refines W2, W3,
W4 and W5 responsibilities inside the existing P5.2 scope and does not change
the Phase 5 weight model. No product point is earned by decision selection or
planning reconciliation.

## Resolved Application Hierarchy

### Command Center: Primary

The Command application owns the primary navigation and ten planned page
groups:

- Situation Overview;
- Live Situation;
- Alerts And Mandatory Review Overview;
- Investigation Workload;
- Camera Network;
- Coverage And Blind Spots;
- Operational Workload;
- Platform Health And Degradation;
- Command Briefing;
- Command Workspaces.

The default overview combines a persistent source-status strip, situation
summary, embedded command GIS, priority workload, coverage/health, bounded
activity chronology, and authoritative drill-downs. It remains read-only in
P5.2. Mutations stay in their owning later workflows.

### GIS Center: Connected Specialist Dashboard

The GIS application owns nine planned page groups:

- GIS Overview;
- Operational Map;
- Camera Network Geography;
- Coverage And Blind-Spot Analysis;
- Alerts And Investigations Geography;
- Movement And Time;
- Layer Catalogue;
- Spatial Workspaces;
- GIS Data And Renderer Health.

GIS Center provides more map area, layer control, spatial filtering, temporal
views and coverage detail. It is launched from Command Center with an opaque
context reference, then independently revalidates session, department, role,
capability, snapshot revision and operation access.

## Shared GIS Domain

One shared domain owns:

- spatial feature, tile, list, detail, layer and workspace contracts;
- WGS 84 browser boundaries and bounded viewport validation;
- layer registry, source provenance, freshness, completeness and limitations;
- selection, inspector, filter, time-window and correction semantics;
- MapLibre core adapter and optional deck.gl overlay adapter;
- authoritative list/table equivalence;
- provider registry, exact destinations, health, circuit breakers and kill switches;
- safe telemetry and resource-profile policy.

Portals may compose these capabilities but cannot bypass or redefine them.

## Resolved Decisions

### D-P5.2-001: `B+GIS`

Use the dense Command workspace and add grouped Command pages. Add a separate
connected GIS Center, while preserving Command Center as primary. This is a
bounded composite clarification of B, not a selection of map-only or
separate-pages-only operation.

### D-P5.2-002: `C`

Use four coordinated data lanes:

- bounded viewport feature summaries;
- server-authored vector tiles for larger sets;
- authoritative cursor-paginated lists independent of rendering;
- typed detail operations for selected records.

### D-P5.2-003: `A+guarded-D`

Local/offline map styles and tiles are the default. A typed provider registry
is designed for future integrations but remains disabled and cannot introduce
an arbitrary browser destination, credential, provider, tile, style, glyph,
sprite or geocoder.

### D-P5.2-004 Through D-P5.2-010: `A/A/A/A/A/A/A`

- server-authoritative aggregates with display-only clustering;
- versioned situation snapshots with per-source truth state;
- bounded UTC windows and explicit corrections/retractions;
- server-provided safe workload priority bands;
- opaque URL context, memory selection and future ETag workspaces;
- map/list/table accessibility equivalence;
- one semantic capability set across dynamic hardware profiles.

### D-P5.2-011: Revised `D`

The selection refers to the revised adaptive renderer option presented after
R0, not R0's custom-WebGL option:

- MapLibre is the stable 2D GIS core;
- low-resource mode uses MapLibre-only when map rendering is admitted;
- enhanced mode may add deck.gl in overlaid mode;
- qualified control-room mode may use deck.gl interleaved with MapLibre in a
  shared WebGL2 context;
- the server policy ceiling, browser capability and session health determine
  admission;
- reverse-controlled deck.gl and custom WebGL are excluded;
- renderer failure retains the authoritative list/table;
- visual adaptation cannot change authorization, source truth, review,
  freshness, completeness, correction or safety semantics.

### D-P5.2-012: `A`

Require generated contract/unit/component/story/browser/visual,
accessibility-static, security, deterministic replay, C1/C10/C50, GIS parity,
and later manual assistive-technology evidence.

## Command Center Feature Groups

### Awareness

- department, role, time window, snapshot revision and profile context;
- active situation aggregates with per-source freshness and completeness;
- bounded change against a comparable previous window;
- map/list situation projection;
- source-health and degradation strip;
- visible unknown and unavailable sources.

### Work Management

- proposed-alert and mandatory-review queue summaries;
- safe priority band, age and authority class;
- investigation workload and recent correction state;
- camera, stream and platform-health workload;
- deterministic overflow and authoritative list drill-down;
- no client risk score or operational mutation.

### Camera Network And Coverage

- inventory denominator and revision;
- available, stale, unavailable and unknown camera/stream state;
- capability completeness and stream-health distribution;
- server-authored coverage, uncertain coverage and blind spots;
- methodology, limitations, source state and authoritative drill-down;
- no coverage inference from visible markers.

### Chronology And Briefing

- separate event and recorded time;
- bounded activity sequence;
- corrections, retractions, supersession, replay and event gaps;
- generated briefing projection;
- future shift-handoff stays blocked until a typed producer exists.

### Control-Room Operation

- stable dense layout with responsive sequential landmarks;
- independent multi-monitor windows with fresh authorization;
- saved workspaces only through a future server-owned ETag contract;
- low-resource mode remains functionally complete;
- logout, revocation, scope change and kill switches affect all windows.

## Adaptive Rendering Policy

| Tier | Renderer | Intended use | Mandatory fallback |
| --- | --- | --- | --- |
| Safe low | MapLibre-only or no map | Basic bounded layers on constrained hardware | Authoritative list/table |
| Enhanced | MapLibre plus deck.gl overlaid | High-volume approved overlays with renderer isolation | MapLibre-only plus list/table |
| Control room | MapLibre plus deck.gl interleaved | Precise layer ordering and approved high-density visualization on WebGL2 | Overlaid, then MapLibre-only, then list/table |
| Renderer denied or failed | No map | Unsupported browser, policy denial, health downgrade or failure | Complete list/table and detail access |

deck.gl may visualize accepted point, path, polygon, density and temporal
projections. It cannot generate operational coverage, health, identity, risk,
priority or threat conclusions. 3D remains outside the initial P5.2 slice.

## Provider Registry Policy

A future provider must declare exact scheme, host, port, paths, style and tile
types, attribution, license, bounds, cache, retention, health, rate, circuit
breaker, kill switch and server-side secret reference. Public direct access,
browser credentials and arbitrary URLs remain prohibited. Provider failure
does not change operational truth and cannot remove authoritative lists.

## Preserved Contract Gaps

The fourteen R0 producer/consumer gaps remain open. This reconciliation does
not repair the Command role mismatch, add viewport/tile/snapshot/coverage/
workload/workspace/handoff producers, or widen existing GIS feature types.
Each dependent feature remains blocked or generated-only until separately
implemented and accepted.

## Frozen Workstreams

| Workstream | Points | Reconciled responsibility |
| --- | ---: | --- |
| `P5.2-W1` | 1.5 | Command/GIS projection contracts, layer registry, producer coverage and generated fixtures |
| `P5.2-W2` | 1.5 | Primary Command overview, source-status strip and truthful situation states |
| `P5.2-W3` | 2.0 | Shared GIS domain, bounded data lanes and adaptive renderer adapters |
| `P5.2-W4` | 2.0 | Embedded Command GIS plus connected GIS Center with Gujarat parity/no-downgrade evidence |
| `P5.2-W5` | 1.5 | Command detail pages, coverage, health, workload, time and authoritative drill-down |
| `P5.2-W6` | 1.5 | Accessibility, localization, responsive and multi-monitor continuity across both dashboards |
| `P5.2-W7` | 1.0 | Security, provider controls, dynamic profiles, observability and resource bounds |
| `P5.2-W8` | 1.0 | Complete validation, evidence, technical checkpoint and exact exit acceptance |

Total remains **12.0 points**. No partial credit is earned inside a workstream.

## Non-Authorization

This R1 reconciliation does not authorize source import, implementation,
tests, dependencies, lockfile changes, backend routes, migrations, frontend or
map execution, providers, tiles, network, cameras, media, real data, models,
operational actions, containers, Kubernetes, deployment, P5.3, commit, push or
remote Git.

## Progress And Next Gate

- Owner decisions: **12/12 (100.0000%)**, change **+8.3333 percentage points**.
- P5.2 planning: **8/8 (100.0000%)**, unchanged.
- P5.2 product: **0/12 (0.0000%)**, unchanged.
- Phase 5 product: **20/100 (20.0000%)**, unchanged.

The next gate is exact owner acceptance of the sealed
`P5.2-PLANNING-R1` package. Acceptance may authorize preparation only of a
separate non-effective P5.2 start package; it does not authorize implementation.
