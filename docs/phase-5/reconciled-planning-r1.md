# P5.0 Reconciled Planning R1

## Inputs

- accepted predecessor: Phase 4 at
  `96a902315e78c184e92df9ebe5bcef1e336eab38`;
- planning authority: `D-P5.0-PLAN-AUTH`;
- initial non-effective package: `P5.0-PLANNING-R0`;
- owner profile: `B/A/A/A+B/D/C/A/A/A/A/A/A`;
- existing UI source: all three branches of `hcam-1-0/final-ui`, with the main
  UI at `cd21af3bef132b211bfe2860d25eaf38a94253df`, `gis` covered as its
  ancestor, and `api-doc-ui@78b0d51` classified as a Developer Portal seed;
- Phase 4.7 handoff: 16 HTTP operations, 6 events, 2 workflows, 11 UI
  states, and 9 accessibility requirements.

## Reconciled Architecture

Phase 5 will be a multi-app React/TypeScript/Vite monorepo with shared packages
for the shell, design system, typed contracts, BFF session, query/event state,
capabilities, localization, GIS, playback, observability, and tests. Logical
portals remain independently buildable but use one identity, authorization,
contract, design, and release-governance foundation.

The existing UI is the main visual baseline and the seed of the Command Center
and camera workflow. It will be migrated through bounded vertical slices after
the shared foundation exists. Its current placeholders are not promoted as
implemented enterprise modules.

HTTP responses are authoritative. A WebSocket lane may accelerate visible
state with sanitized projections and invalidation hints, but every authority,
mutation, conflict, correction, and durable state transition is resolved by
server contracts. This is the binding interpretation of `D-P5.0-004:A+B`.

MapLibre 2D is the authoritative map. Optional 3D is a guarded adapter and must
have a 2D/list equivalent. Live media uses one typed adapter with HLS and
provisional WHEP lanes selected by policy ceiling, server capability, hardware
profile, and current health. The UI may degrade rendering cost, density, media
quality, or optional effects, but not authorization, evidence, correction,
freshness, or operator-decision semantics.

## Reconciled Delivery Order

1. P5.0 seals product journeys, source adoption, contracts, architecture,
   security, accessibility, and start evidence.
2. P5.1 creates the shared foundation and imports the existing UI under exact
   provenance.
3. P5.2 delivers Command Center and situational awareness.
4. P5.3 delivers camera registry, live monitoring, typed playback, and GIS.
5. P5.4 delivers intelligence, alerts, mandatory review, correction, and
   lifecycle conflict handling.
6. P5.5 delivers investigation timelines, evidence references, provenance, and
   controlled case/evidence workflows.
7. P5.6 delivers admin, security, operations, observability, and dynamic
   hardware capability controls.
8. P5.7 validates accessibility, localization, browser/responsive behavior,
   performance, resilience, security, contracts, and final acceptance.

## Existing UI Gap Priority

Before the imported UI can earn product credit, Phase 5 must:

1. repair and execute the stale browser suite;
2. establish asset/license/source provenance;
3. add runtime-validated clients and complete BFF session controls;
4. implement all required Phase 4.7 UI states and problem semantics;
5. extract the shell and design system from monolithic files;
6. add English/Gujarati/Hindi message architecture;
7. implement policy-ceiling capabilities and server-returned action gates;
8. replace Leaflet with MapLibre while preserving the current GIS workflow;
9. place WHEP behind the typed HLS/WHEP adapter and fix media-state reset;
10. add automated and manual accessibility, security, and browser evidence.

## Progress Accounting

Planning remains **8/8 (100.0000%)**. The repository assessment and owner
reconciliation improve planning confidence but do not add product points.

Phase 5 product progress remains **0/100 (0.0000%)**, change **+0.0000
percentage points**, because no implementation, migration, dependency, build,
runtime, or accepted P5.0 deliverable has been authorized or completed.

## Next Gate

The owner may accept the exact `P5.0-PLANNING-R1` package. After that, a
separate P5.0 implementation/start package must define exact paths,
dependencies, generated-only fixtures, tests, evidence, and stop conditions.
Acceptance of planning does not authorize implementation.
