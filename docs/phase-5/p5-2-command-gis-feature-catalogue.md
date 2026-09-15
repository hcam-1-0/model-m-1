# P5.2 Command Center And Connected GIS Feature Catalogue

Status: reconciled planning; non-effective; implementation unauthorized

## Product Hierarchy

```text
H-CAM Command Center              Primary dashboard and default landing
  |-- situation and command views
  |-- embedded command GIS
  |-- workload, coverage and health
  `-- links to authoritative detail workflows

H-CAM GIS Center                  Connected specialist dashboard
  |-- full operational map
  |-- spatial analysis workspaces
  |-- coverage and blind-spot views
  `-- layer, provenance and GIS health views

Shared H-CAM GIS Domain           One implementation and contract authority
  |-- spatial contracts and layer registry
  |-- feature, tile, list and detail clients
  |-- MapLibre and optional deck.gl adapters
  |-- accessible list/table projection
  `-- selection, time, workspace and security policy
```

Command Center remains the first operational signal and primary navigation
destination. GIS Center is reached from Command Center when an operator needs
more map area, more layers, deeper spatial filtering, coverage analysis, or a
dedicated multi-monitor workspace. Neither dashboard owns independent copies
of camera, alert, investigation, review, health, or coverage truth.

## Command Center Navigation

Proposed primary routes are planning identifiers, not implemented routes.

| Page | Purpose | Principal views |
| --- | --- | --- |
| `/command/overview` | Default situational landing | Source-status strip, active situation summary, embedded command GIS, priority workload, coverage and degradation summaries |
| `/command/situation` | Current bounded operational picture | Timeline, region and layer filters, map/list switch, selected-record inspector, event and recorded-time labels |
| `/command/alerts-review` | Read-only command view of proposed alerts and mandatory review | Priority bands, queue age, review state, source freshness, authoritative links to P5.4 |
| `/command/investigations` | Read-only investigation workload | Lifecycle counts, recent changes, assigned/unassigned projection where authorized, correction state, links to P5.5 |
| `/command/camera-network` | Network-level camera and stream status | Available/offline/unknown/stale counts, stream health, capability completeness, maintenance/degradation projection |
| `/command/coverage` | Coverage and blind-spot command summary | Declared denominator, covered/unknown/unavailable regions, limitations, camera and stream drill-down |
| `/command/workload` | Consolidated operational workload | Alert/review/investigation/camera/stream/degradation queues with server-provided bands and deterministic ordering |
| `/command/platform-health` | Operational dependency and degradation view | Service health, queue/backlog state, source freshness, active degradation, recovery state, kill-switch visibility |
| `/command/briefing` | Bounded shift and command briefing view | Snapshot summary, unresolved items, source limitations, correction chronology, generated-only briefing projection |
| `/command/workspaces` | Entry to approved command layouts | Recent and assigned server-owned workspace references, version, ETag, expiry and conflict state |

The briefing and workspace pages remain blocked until their producer contracts
are accepted. A route shell must show an explicit unavailable reason rather
than storing a local substitute.

## Command Overview Detail

The main page is a dense, scan-oriented workspace, not a marketing dashboard
or a collection of nested cards.

### Persistent Command Strip

- active department and role projection;
- selected UTC window and operational timezone;
- snapshot revision and `as_of` time;
- complete, partial, stale, degraded, denied, failed, or recovering state;
- count of unavailable or unknown required sources;
- connection and event-invalidation health;
- profile mode: low-resource, enhanced, control-room, or future-server;
- visible link to source-state details.

The strip cannot display healthy when any required source is unknown,
unavailable, denied, or stale beyond policy.

### Situation Summary Band

- proposed alerts by accepted lifecycle and safe priority band;
- mandatory-review backlog and age distribution;
- active investigation lifecycle counts;
- camera and stream availability/freshness summary;
- coverage and blind-spot projection with declared denominator;
- current platform degradation and recovery state;
- bounded change indicators against the immediately preceding comparable
  window, never against a mismatched time or scope;
- direct authoritative list drill-down for every number.

### Embedded Command GIS

- compact operational map as the central spatial summary;
- synchronized authoritative list/table below or beside the map;
- camera, stream-health, alert, investigation, coverage, resource and
  degradation layers only when their contracts are available;
- deterministic cluster expansion and list filtering;
- selected-record inspector with source, freshness, completeness, correction,
  authority class, and safe detail link;
- button to open the same bounded context in GIS Center through an opaque
  server workspace or safe filter reference;
- list-first low-resource fallback and explicit map unavailable state;
- no camera control, playback, face/plate display, evidence rendering, public
  basemap call, or client-side operational scoring.

### Priority Workload Rail

- server-provided safe priority band;
- queue and record type;
- age and accepted service target where one exists;
- review requirement and current lifecycle state;
- source freshness and degradation marker;
- assigned owner projection only when the role permits it;
- authoritative destination and conflict state;
- deterministic collapse when the bounded visible-item limit is reached.

### Coverage And Health Band

- camera inventory denominator and revision;
- available, stale, unavailable and unknown camera counts;
- stream health and capability-completeness distribution;
- declared coverage, uncertain coverage and blind-spot projections;
- data-loss and source-unavailable indicators;
- map/list/detail drill-down;
- explicit methodology and limitations link.

### Command Activity Timeline

- bounded recent alert, review, investigation, correction and degradation
  changes;
- separate event time and recorded time;
- correction, retraction and supersession markers;
- event gaps and replay indicators;
- type, source and lifecycle filters;
- no unbounded replay or hidden historical mutation.

## Connected GIS Center Navigation

| Page | Purpose | Core features |
| --- | --- | --- |
| `/gis/overview` | GIS domain landing | Spatial source health, available layers, recent workspaces, map capability and provider status |
| `/gis/operational-map` | Full-screen bounded map workspace | Layer tree, advanced filters, map/list/inspector, time window, compare mode, selection set and workspace state |
| `/gis/camera-network` | Camera and stream geography | Camera clusters, stream health, freshness, capability state, authorized camera detail links |
| `/gis/coverage` | Coverage and blind-spot analysis | Server-authored coverage surfaces, denominator, unknown areas, limitations and authoritative camera list |
| `/gis/alerts-investigations` | Spatial intelligence projection | Proposed alerts, review state and investigations with uncertainty, correction and authoritative drill-down |
| `/gis/movement-time` | Bounded temporal spatial view | Accepted anonymous trajectories and chronology only when later producer contracts exist; no identity inference |
| `/gis/layers` | Layer catalogue | Layer source, version, geometry, freshness, completeness, role, legend, visibility, profile admission and provenance |
| `/gis/workspaces` | Spatial workspace catalogue | Server-owned saved filters, viewport, layers, layout, version, ETag, expiry and share policy |
| `/gis/data-health` | GIS source and renderer health | Feature/tile/list lane health, revision mismatch, stale sources, provider status, payload bounds and degraded mode |

GIS Center is not a second command homepage. It does not duplicate the command
summary, own alert/review decisions, or become the default route. It provides
specialist depth around the same selected scope and record references.

## Shared GIS Features

### Layer Explorer

- grouped operational, camera, intelligence, investigation, coverage,
  resource, boundary and health layers;
- role and department admission;
- feature count and freshness state;
- legend, geometry type, source, version and limitations;
- profile-based renderer admission;
- mutually exclusive and dependent-layer rules;
- no arbitrary user-provided tile, style, SQL, URL or expression source.

### Selection And Inspector

- one canonical selected-feature reference;
- map, list and inspector synchronized without duplicating records;
- multi-select only within declared bounds;
- type-specific summary fields from an allowlist;
- source, revision, time, freshness, completeness and correction state;
- exact authoritative detail operation;
- selection cleared on department, role, contract or revision incompatibility.

### Spatial Search And Filters

- approved region, district, zone, camera state, stream state, feature type,
  lifecycle, safe priority band, freshness and time-window filters;
- server-owned geospatial query semantics;
- typed bounded geometry selections where authorized;
- no public geocoder, free-form SQL, arbitrary expression or raw coordinate
  persistence;
- generated-only search fixtures until an exact producer is accepted.

### Time And Comparison

- bounded shared UTC window with operational timezone display;
- current versus previous comparable window;
- split or swipe comparison only when both snapshots declare compatible scope,
  source and denominator;
- corrected and retracted state remains visible;
- animation obeys reduced-motion and profile policy;
- no free-range replay in P5.2.

### Workspace Management

- server-owned opaque workspace ID;
- bounded filters, layer IDs, viewport, panel layout and display preferences;
- department, owner, visibility, version, ETag, expiry and compatibility state;
- duplicate, conflict, revoked, expired and incompatible behavior;
- no token, raw record, camera locator, coordinate set, query payload or
  protected detail in URLs or browser storage.

### Provider Registry

- local/offline provider is the default;
- future providers are typed, exact-destination, license-attributed and
  disabled by default;
- credentials are resolved on the server and never embedded in browser URLs;
- each provider declares styles, tiles, glyphs, sprites, bounds, attribution,
  health, cache, retention, rate, circuit-breaker and kill-switch behavior;
- provider failure preserves authoritative lists and can fall back to an
  approved local style without changing operational truth.

## Adaptive Rendering

| Runtime profile | MapLibre | deck.gl | Behavior |
| --- | --- | --- | --- |
| Low resource | Required when map admitted | Disabled | Bounded native layers, reduced visible features, no animation, list-first fallback |
| Enhanced workstation | Required | Optional overlaid mode | Separate deck.gl canvas for approved high-volume or analytical display layers |
| Control room | Required | Optional interleaved WebGL2 mode | Shared layer stack for approved high-density layers and precise ordering |
| Future server-backed | Required in browser | Optional by client policy | Server may improve tiles and aggregates; browser bounds and semantics remain unchanged |

MapLibre remains the stable base map, navigation, label and standard vector
layer renderer. deck.gl is an optional presentation accelerator for approved
large point, path, polygon, density and temporal layers. Reverse-controlled
deck.gl, custom WebGL, automatic privilege expansion and client-owned
operational conclusions are excluded.

## Cross-Dashboard Continuity

Command Center and GIS Center may exchange only:

- an opaque workspace or selection reference;
- bounded safe filter enums;
- an accepted time-window reference;
- an authoritative detail route identifier;
- a snapshot revision hint that must be revalidated.

They do not exchange bearer tokens, cookies, raw query results, map payloads,
coordinates, locators, credentials, free text, evidence, identities, or
browser cache contents. Opening GIS Center performs a fresh session,
department, capability and operation authorization check.

## Required States On Every Page

- loading;
- empty;
- complete and fresh;
- partial;
- stale;
- degraded;
- denied;
- incompatible or unsupported;
- failed;
- recovering;
- corrected or retracted where applicable;
- session expired or department changed;
- renderer unavailable with list/table preserved.

## Explicitly Unavailable In P5.2

- camera PTZ, configuration, snapshot, recording or playback;
- alert approval, rejection, notification, dispatch or enforcement;
- investigation or evidence mutation;
- biometric, plate, owner, registration or watchlist conclusions;
- source-media rendering or export;
- arbitrary public map providers, geocoders or user tile URLs;
- client-generated threat, risk, guilt, identity, coverage or health scores;
- operational 3D, digital twin, drone control or autonomous routing;
- real providers, Government/private data, deployment and production claims.
