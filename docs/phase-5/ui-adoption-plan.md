# Existing UI Adoption Plan

Status: reconciled planning only; implementation is not authorized.

## Adoption Decision

`hcam-1-0/final-ui@cd21af3bef132b211bfe2860d25eaf38a94253df`
is the approved Phase 5 visual and interaction baseline. It will seed the
Command Center and camera-monitoring experience while the accepted Phase 4.7
contracts remain authoritative for intelligence, review, investigation,
evidence, and operations behavior.

This avoids two failure modes: discarding substantial UI work or forcing a
single prototype to carry every enterprise portal and contract.

## Target Placement

The selected `D-P5.0-001:B` topology is an independently buildable multi-app
monorepo. The proposed target is:

```text
apps/
  command-center/
  operations-center/
  intelligence-center/
  investigation-center/
  evidence-center/
  admin-center/
  security-center/
packages/
  app-shell/
  ui/
  design-tokens/
  contracts/
  api-client/
  query-events/
  auth-session/
  capabilities/
  i18n/
  gis/
  playback/
  observability/
  test-fixtures/
```

This is a proposed implementation shape, not an authorization to create these
paths.

The divergent `api-doc-ui` branch may later seed a separately built Developer
Portal surface or shared contract-browser package. Its FastAPI docs host must
remain separate from the operator BFF, and its OpenAPI 0.2.0 export is a
reference that must be reconciled with current canonical contracts before use.

## What Is Preserved

- NETRA SENTINEL visual identity and dense control-room information hierarchy;
- grouped navigation, mission strip, mobile drawer, and mobile command dock;
- command palette workflow and approved-camera search concept;
- Command Overview readiness and operator-sequence composition;
- Live Monitor three-column workflow, focus mode, and advancing-media proof;
- GIS explorer, filters, layer controls, selection inspector, and lab labels;
- truthful empty, unavailable, gated, local-only, and zero-retention language;
- icon-led controls, compact panels, and responsive operator ergonomics;
- current unit-test intent where it remains behaviorally valid.

## What Is Replaced Or Extracted

- hash routing becomes typed app routing with guarded deep links;
- the monolithic `App.tsx` becomes a shared shell plus route registry;
- `ModuleWorkspace.tsx` becomes bounded portal features, not static master data;
- the large stylesheet becomes versioned tokens, primitives, layouts, and
  portal styles;
- manual response casts become schema-validated generated clients;
- direct fetch state becomes HTTP-authoritative query state;
- event delivery becomes a scoped, non-authoritative projection/invalidation
  lane;
- Leaflet becomes the accepted MapLibre 2D adapter while preserving the GIS UX;
- the WHEP hook becomes one lane in a typed HLS/WHEP playback interface;
- hard-coded English strings become English, Gujarati, and Hindi catalogues;
- browser-selected features become server-ceiling capabilities with visible
  denied/degraded explanations;
- test sources become layered contract, unit, accessibility, browser, visual,
  security, and manual evidence.

## `D-P5.0-004:A+B` Reconciliation

The two selected options are combined without creating two sources of truth:

1. HTTP responses are authoritative resource state.
2. Mutations are confirmed only by authoritative HTTP responses carrying the
   required ETag, idempotency key, reason, and server authorization result.
3. WebSocket messages may carry sanitized state projections and invalidation
   hints for low-latency rendering.
4. A WebSocket projection is always labeled by freshness and sequence state.
5. Gaps, unknown versions, reconnects, duplicates, reordering, or policy
   changes force bounded HTTP revalidation.
6. Events never enable a control, expand department scope, grant a role,
   finalize a review, or confirm an operational action.
7. The operator can continue with stale-read policy only where the server
   contract explicitly permits it; writes fail closed.

This gives the responsive behavior intended by option B while retaining the
correctness, replay recovery, and authority guarantees of option A.

## Migration Waves

### Wave 0: Evidence Freeze

- pin the source commit and tree manifest;
- record source ownership and emblem provenance;
- capture current desktop, tablet, and mobile visual references;
- execute the existing validation commands in an authorized isolated build;
- classify browser-test drift before moving source.

### Wave 1: Shared Foundation

- create workspace, package, dependency, and build policies;
- implement shell, routing, error boundaries, session boundary, capability
  resolver, localization, design tokens, and accessible primitives;
- introduce generated-only test fixtures and Phase 4.7 contract clients;
- keep all operational integrations default-off.

### Wave 2: Command Center Seed

- migrate brand, navigation, mission strip, command search, full-page states,
  and Command Overview;
- preserve visual behavior while adding server-returned capabilities,
  freshness, degraded state, and correlation context;
- repair unit and browser tests before this slice earns product credit.

### Wave 3: Camera And Playback

- migrate camera explorer and display-safe details;
- implement the typed HLS/WHEP playback adapter and policy-based lane selection;
- reset media-proof state on every stream, bound signaling payloads, and prove
  cleanup/recovery;
- preserve no-recording defaults and explicit media-proof semantics.

### Wave 4: GIS

- port the current workflow to MapLibre 2D;
- add complete supported geometry, bounded server queries, temporal/freshness
  state, list equivalence, and accessible selection;
- add optional 3D only behind a separate capability and parity gate.

### Wave 5: Intelligence And Review

- replace AI/ANPR and Audit placeholders with hypothesis, run, alert, review,
  lifecycle, correction, and degradation contracts;
- implement the mandatory human-review path with ETag and idempotency conflict
  handling;
- never infer permissions from navigation visibility.

### Wave 6: Investigation And Evidence

- replace Forensics placeholders with timeline, reconstruction, provenance,
  correction, evidence-reference, and controlled export/hold preparation views;
- retain media-reference-without-copying defaults;
- distinguish source facts, hypotheses, decisions, corrections, and retractions.

### Wave 7: Admin, Security, Operations, And Acceptance

- build independently deployable administrative, security, and operations
  surfaces over shared packages;
- add accessibility, localization, responsive, browser, performance,
  resilience, supply-chain, and threat-model evidence;
- complete clean-source validation and exact acceptance evidence.

## Per-Wave Exit Rule

A migrated surface is complete only when its UI states, authoritative contracts,
department and role boundaries, keyboard/focus behavior, localization,
responsive behavior, security controls, and generated-only tests pass together.
Visual similarity alone earns no completion credit.

## Source-History Strategy

At implementation authorization, prefer a one-time history-preserving import or
a clearly attributed source migration rather than copying anonymous files. The
import must pin the source commit and tree digest, preserve authorship, exclude
build outputs, and add an explicit asset/license/provenance record. It must not
merge or change either remote repository without separate remote-Git authority.

## Current Gate

This plan does not authorize importing source, installing dependencies, changing
either repository, executing the application, or contacting a camera, map,
media, provider, or operational endpoint.
