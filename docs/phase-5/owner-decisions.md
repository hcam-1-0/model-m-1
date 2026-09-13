# P5.0 Owner Decisions

Recorded on 2026-09-06 from the owner's explicit selections.

## Resolved Profile

`B / A / A / A+B / D / C / A / A / A / A / A / A`

| Decision | Selected result |
| --- | --- |
| D-P5.0-001 | **B.** Independently buildable portal applications in one monorepo. |
| D-P5.0-002 | **A.** React, TypeScript, and Vite. |
| D-P5.0-003 | **A.** Same-origin backend-for-frontend with server-managed session. |
| D-P5.0-004 | **A+B.** HTTP-authoritative query cache plus a bounded, non-authoritative WebSocket projection and invalidation lane. |
| D-P5.0-005 | **D.** Authoritative MapLibre 2D plus a guarded optional 3D analysis adapter. |
| D-P5.0-006 | **C.** One typed playback adapter with HLS and provisional WHEP lanes. |
| D-P5.0-007 | **A.** H-CAM tokens plus reviewed accessible headless primitives. |
| D-P5.0-008 | **A.** Typed server workspaces plus local non-sensitive display preferences. |
| D-P5.0-009 | **A.** English, Gujarati, and Hindi architecture from the first component. |
| D-P5.0-010 | **A.** Deterministic policy-ceiling capability resolver. |
| D-P5.0-011 | **A.** Layered automated plus manual evidence. |
| D-P5.0-012 | **A.** Shared foundation followed by bounded vertical portal slices. |

## Combined State Rule

`D-P5.0-004:A+B` does not create competing authority. HTTP and server-side
authorization remain authoritative. WebSocket messages provide low-latency,
scoped projections and invalidation hints only. They cannot grant permissions,
enable commands, confirm writes, or override ETags. Unknown versions, gaps,
duplicates, reordering, reconnects, or stale sequence state trigger bounded
HTTP revalidation, and writes remain fail closed.

## Existing UI Direction

The owner also directed Phase 5 to use the previously built
`hcam-1-0/final-ui`. The exact accepted planning interpretation is:

- use commit `cd21af3bef132b211bfe2860d25eaf38a94253df` as the visual and
  interaction baseline;
- preserve the Command Center, Live Monitor, GIS, navigation, responsive
  patterns, safety language, and NETRA SENTINEL visual identity;
- migrate it into the selected multi-app monorepo after implementation is
  separately authorized;
- do not treat its four browser operations as substitutes for the Phase 4.7
  handoff contracts;
- improve its architecture, accessibility, security, localization, state
  management, GIS engine, playback abstraction, and validation without
  degrading its operator experience.

## Effect

These decisions authorize planning reconciliation only under
`D-P5.0-PLAN-AUTH`. They do not authorize Phase 5 implementation, source import,
dependency installation, build or runtime execution, cameras or media,
Government/private data, models/inference, operational actions, deployment, or
remote Git.
