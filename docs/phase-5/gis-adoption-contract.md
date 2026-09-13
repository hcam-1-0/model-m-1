# Gujarat GIS Adoption Contract

Status: owner-directed planning only

Decision: `D-P5.0-GIS-ADOPTION-001`

## Binding Direction

The Gujarat GIS already built in
`hcam-1-0/final-ui@cd21af3bef132b211bfe2860d25eaf38a94253df` is
not merely a visual reference. It is the **canonical operator-experience
baseline** for the Phase 5 GIS surface.

Phase 5 must preserve its recognizable layout, interactions, responsive
behavior, safety disclosures, and approved-camera preview workflow. Internal
architecture may be upgraded, but that work must be additive and parity-first.
The GIS must not be replaced by a generic map dashboard or visually downgraded.

## Experience That Must Be Preserved

### Workspace Composition

- Gujarat GIS title and operational context;
- visible-resource totals for cameras, incidents, patrols, and zones;
- layer toolbar and local map-style selection;
- left-side feature explorer and filters;
- central map stage;
- right-side selected-feature inspector and approved live preview;
- coordinate and visible-feature footer;
- desktop focus mode and compact-screen explorer/details controls.

### Search And Filtering

- free-text feature search;
- status filter;
- department filter;
- approved-live versus registry-only availability filter;
- stream-protocol filter;
- camera-type filter;
- active-filter count, clear action, and fit-results action;
- bounded visible result list with explicit empty and loading states.

### Map Interaction

- viewport-bounded data requests;
- camera clustering at lower zoom levels;
- camera, incident, patrol, and zone visual distinction;
- point and polygon interaction;
- fit Gujarat, fit results, reset, zoom, scale, and coordinate feedback;
- selected-feature detail with display-safe properties;
- live-preview initiation only for a camera approved in the current session;
- visible distinction between synthetic lab overlays and camera metadata.

### Safety And Truthfulness

- local-only/default-no-external-basemap posture;
- explicit `LAB DATA` labels for synthetic operational overlays;
- no implication that registry presence proves live availability;
- no stream locator or credential in browser-visible GIS state;
- no automatic device discovery, recording, export, PTZ, or operational
  control from the map;
- no claim that signaling alone proves advancing live media.

## Architecture Upgrade Without Experience Loss

Decision `D-P5.0-005:D` remains unchanged: MapLibre 2D is the target
authoritative renderer and optional 3D is a guarded analysis adapter. This is
an internal implementation decision, not permission to redesign the GIS.

The migration sequence is:

1. Freeze the current Leaflet GIS interaction and visual behavior as generated
   regression fixtures and reference screenshots.
2. Extract GIS domain state, queries, filters, selections, layers, geometry,
   and commands from renderer-specific code.
3. Implement a typed renderer-neutral GIS contract.
4. Port the existing experience to the MapLibre 2D adapter.
5. Run side-by-side behavior, visual, accessibility, and resource comparisons.
6. Retain the current implementation as a controlled compatibility reference
   until all mandatory parity gates pass.
7. Add optional 3D only after authoritative 2D and accessible list paths are
   complete and equivalent.

## Additive Phase 5 GIS Capabilities

The existing GIS is preserved and expanded with:

- complete supported geometry handling, including lines, routes, polygons,
  and multipolygons;
- typed server-authoritative spatial query, tile, clustering, and capability
  contracts;
- explicit loading, empty, partial, stale, degraded, denied, conflict,
  failure, recovery, correction, and success states;
- temporal layers for events, hypotheses, alerts, investigations, corrections,
  and retractions where authorized;
- bounded time-window and replay controls;
- layer freshness, provenance, completeness, and correction indicators;
- saved server-side workspaces and harmless local display preferences;
- English, Gujarati, and Hindi message catalogues;
- keyboard map navigation, logical focus, screen-reader list equivalence,
  measured contrast, zoom/reflow, forced-colors, and reduced-motion support;
- deterministic capability profiles for a basic laptop, GPU lab, server, and
  future Kubernetes deployment without weakening policy or data semantics;
- generated C1/C10/C50 spatial and UI validation with declared hardware limits.

## Optional 3D Boundary

Optional 3D may add terrain, building, line-of-sight, height, or dense spatial
analysis only when supported by authorized data and policy. It must be
default-off unless the server capability and local profile permit it. Every
fact, selection, warning, and operator action available only in 3D must also
have an authoritative 2D or accessible list representation.

## Parity Matrix

| Area | Existing baseline | Required migration evidence |
| --- | --- | --- |
| Layout | Explorer, map, detail inspector, summary, toolbar, footer | Desktop, tablet, and mobile screenshot and geometry comparison |
| Layers | Cameras, incidents, patrols, zones | Equal visibility, toggle, count, label, and disclosure behavior |
| Filters | Search plus five typed filters | Equal result sets, reset behavior, URL/workspace restoration, and keyboard access |
| Selection | Marker/list selection and inspector | Equal selected identity, details, focus, and clear behavior |
| Clustering | Local screen-space camera clusters | Equivalent bounded grouping with deterministic expansion and accessible count |
| Live preview | Approved cameras only | Equal denial behavior plus typed playback and advancing-media proof |
| Responsive use | Compact explorer/details tabs and focus mode | No overflow, overlap, inaccessible controls, or lost context at supported sizes |
| Safety | Local-only, lab labels, no locators | Static and runtime tests proving all disclosures and field exclusions |
| Performance | Current bounded viewport and list limits | Declared C1/C10/C50 latency, frame, memory, and degradation evidence |

## Acceptance Rule

A new GIS implementation cannot replace the existing GIS merely because it
renders a map or uses the selected library. It must pass the complete parity
matrix and all additive contract, security, accessibility, localization, and
resource-profile gates. Any intentional removal or major workflow redesign
requires a new explicit owner decision.

## Current Boundary

This contract records planning intent only. It does not authorize source
import, dependency installation, code or test implementation, application
execution, map/tile/provider network access, camera/media access, real data,
deployment, or remote Git.
