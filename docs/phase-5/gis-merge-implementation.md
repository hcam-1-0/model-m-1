# Gujarat GIS Merge Implementation

Status date: 2026-09-13

Branch: `codex/phase5-gis-merge`

Base commit: `1b069459eda1fd859b0515ad8e6d7e403f105696`

## Purpose

This change merges the owner's first-party Gujarat GIS from
`hcam-1-0/final-ui` into the accepted H-CAM GIS Center without replacing the
current portal architecture. Command Center remains the primary application,
GIS Center remains a connected specialist application, and `/gis/map` is the
high-density operational workspace.

The merge is additive. Existing Phase 5 routes, grouped navigation, shared
shell, command handoff, dynamic resource profiles, renderer admission,
authoritative table/list alternatives, accessibility contracts, and
generated-only boundaries remain in place.

## Source Provenance

The imported interaction source is the owner-authorized `gis` branch of
`hcam-1-0/final-ui` at commit
`3696231787f93b1174d7e9d870c1c394ab6eda05`. That immutable repository revision
is the provenance reference for this merge.

The merge adopts the bounded H-CAM GIS core rather than the unrelated global
intelligence, ArcGIS, OSINT, deployment, database, or infrastructure modules in
that repository. Next.js route behavior was translated into typed local
generated projections suitable for the current Vite workspace; no source API
or deployment server was copied.

## Merged Capabilities

- Gujarat-first operational extent, reset, fullscreen, coordinate, zoom, and
  place-navigation controls.
- Local district boundaries, district labels, district selection, operational
  context, and selected-territory emphasis.
- Searchable camera catalogue with online, degraded, maintenance, and offline
  status filters.
- Camera clustering, labels, coverage areas, map selection, detail rail,
  metadata-only preview policy, and nearby-camera context.
- Generated operational alert markers, severity/time/lifecycle filtering,
  prioritization, selection, and session-local viewer/operator projections.
- Camera, alert, district, label, coverage, and operational-context layer
  controls.
- Pitched perspective, dark and standard local styles, guarded unavailable
  imagery, display reset, map inspection, places, data, help, and safe view-link
  utilities.
- Polygon, rectangle, radius, and route drawing with area, perimeter, radius,
  and path measurements; undo, finish, cancel, rename, delete, clear, and local
  GeoJSON export behavior.
- Keyboard interactions for reset, fullscreen, search, help, drawing,
  completion, undo, cancellation, and context clearing.
- Dynamic low-resource, enhanced, control-room, and future-server profiles;
  MapLibre, guarded deck.gl, and complete list-only renderer choices.

## Current H-CAM Capabilities Preserved

- All nine existing GIS Center routes remain available.
- Portal navigation and the workspace command palette remain authoritative.
- The existing GIS domain and renderer-admission contracts remain in control.
- List-only mode exposes every generated camera record without WebGL.
- No visual map is the sole source for a camera, alert, status, or selection.
- Resource profiles can change density and rendering capability but cannot
  change operator authority.
- Command Center remains the primary portal and the operational map remains a
  connected specialist view.

## Adaptation And Repair

- Restored the owner-authored CARTO Dark Matter development basemap on loopback
  only, with exact CSP destinations for its style, TileJSON, vector tiles,
  sprites, and glyphs.
- Kept non-loopback map styles and all H-CAM GeoJSON bound to same-origin local
  assets, with automatic local fallback when the public development style fails.
- Bundled the MapLibre worker through Vite and bound it explicitly so browser
  preview never falls through to the application HTML shell for worker code.
- Replaced stream-like preview behavior with an explicit metadata-only policy
  projection; no URL, token, credential, SDP, snapshot, or media is exposed.
- Corrected the source camera fixture identifier mismatch.
- Described the 3D control as pitched perspective, not terrain; elevation is
  explicitly unavailable.
- Added exact accessible names to compact map controls and retained labels for
  every icon-only action.
- Kept the operational sidebar available on small screens as a collapsible
  overlay and made it start collapsed at 620 px and below.
- Added container observation so MapLibre resizes after responsive layout,
  portal, and fullscreen changes.
- Moved the heavy operational workspace behind a lazy route boundary, producing
  a separate approximately 88 kB minified route chunk.
- Removed an ineffective meta-delivered `frame-ancestors` directive. Production
  frame protection must be delivered as an HTTP response header.

## Data And Authority Boundary

The current merge uses eight generated camera records, generated alerts, and
local district/context GeoJSON. On loopback only, the visual basemap may fetch
public CARTO/OpenStreetMap development-reference style and tile resources from
the exact CSP-allowlisted CARTO hosts. Non-loopback execution remains on the
same-origin local Gujarat fallback. Neither mode performs a provider API query,
Sentinel access, camera access, media playback, model inference,
Government/private-data access, operational mutation, or deployment action.

Generated alert lifecycle changes and drawings are session-local. They are not
operational records and are not persisted. The preview control checks only the
local role and generated availability state.

## Validation

The pinned local Node `24.18.0` toolchain completed:

- strict GIS Center TypeScript compilation;
- ESLint for the merged GIS source, shared geometry/drawing domain, and focused
  tests;
- 17 focused Vitest tests across the portal, renderer fallback, map-runtime
  selection, geometry,
  measurements, and drawing reducer;
- the complete frontend regression: 112 test files and 281 tests passed;
- Vite production build with 2,900 transformed modules and a valid bundled
  MapLibre worker asset;
- real-browser desktop and 390 x 844 mobile interaction checks;
- camera selection/detail, nearby cameras, alert queue, drawing tools, renderer
  switching, and complete list-only fallback checks;
- loaded district, context, camera, alert, coverage, and cluster map layers;
- mobile canvas-to-container equality, zero document-width overflow, zero
  unlabeled buttons, and zero visible map-layer failures;
- development-basemap style, TileJSON, sprite, glyph, and vector-tile requests
  returning successfully from only the exact CARTO hosts.

The build still reports the existing shared GIS entry chunk above Vite's 500 kB
warning threshold. The operational workspace itself is split into a separate
route chunk. Further shared renderer/vendor chunking is a follow-up performance
optimization, not a functional merge blocker.

## Remaining Producer Work

Real camera metadata, playback sessions, local production map archives,
provider integrations, persisted alert changes, persisted drawings, server-side
authorization, and operational APIs remain separate backend/deployment work.
They must connect through the accepted typed contracts and must not bypass the
current generated-only UI boundary.
