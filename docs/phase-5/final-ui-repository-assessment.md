# `hcam-1-0/final-ui` Repository Assessment

Status date: 2026-09-06

## Purpose And Boundary

This assessment is the read-only Phase 5 intake of the existing H-CAM UI at
`https://github.com/hcam-1-0/final-ui`. The owner has designated that work as
the main UI already built and asked that Phase 5 use it. The assessment pins
the main application to `main` commit
`cd21af3bef132b211bfe2860d25eaf38a94253df` and separately inventories every
observed remote branch.

The repository is accepted here as the **visual and interaction baseline** for
the Command Center shell, Live Monitor, Gujarat GIS, camera registry language,
and shared NETRA SENTINEL design direction. It is not automatically treated as
the canonical Phase 5 architecture, API contract, security boundary,
accessibility evidence, or production implementation. Those claims require
their own validated evidence.

No dependency was installed, no application was built or started, no test was
executed, no camera or media endpoint was contacted, and no remote file or Git
reference was changed during this assessment.

## Exact Repository Snapshot

| Property | Observed value |
| --- | --- |
| Repository | `hcam-1-0/final-ui` (private) |
| Default branch | `main` |
| Remote branches | `main`, `gis`, `api-doc-ui` |
| Tags | None |
| HEAD | `cd21af3bef132b211bfe2860d25eaf38a94253df` |
| Unique commits across branches | 4 |
| Tracked files | 24 |
| Tracked bytes | 579,243 |
| Text/configuration bytes | 410,363 |
| Tree-manifest SHA-256 | `D14594F633C8A894428AC79E1CA29F0BE8CE07A4EE89754D13976276776CFAD5` |
| Application | React 18 + TypeScript 5 + Vite 6 |
| Map | Leaflet 1.9.4, local coordinate grid, no external basemap |
| Live media | Custom receive-only WebRTC/WHEP hook |
| Unit tests | 16 Vitest cases, 129 `expect` calls |
| Browser tests | 2 Playwright definitions across 3 viewports |
| Server/runtime code | None |
| CI workflow | None |
| License file | None |

## Complete Branch Inventory

| Branch | HEAD | Files | Bytes | Relationship and disposition |
| --- | --- | ---: | ---: | --- |
| `main` | `cd21af3` | 24 | 579,243 | Current NETRA Command Center source and primary visual baseline. |
| `gis` | `17ae254` | 20 | 220,375 | Exact ancestor of `main`; all of its content and history are covered by the main assessment. |
| `api-doc-ui` | `78b0d51` | 18 | 291,991 | Diverged after `65a5ad4`; separate read-only API documentation portal and Developer Portal seed. |

The branch-manifest SHA-256 is
`8CE6D0175D493708B228C142CA8E3DB5201D6E02B636F2290E79F96CECBB3F77`.
The snapshot contract records each branch head, file count, byte count, tree
digest, relationship, and every file unique to the divergent documentation
branch.

### `api-doc-ui` Branch

This branch is not an alternate operator dashboard. It contains a small React
contract browser, a FastAPI static/docs host, backend tests, and a bundled
`H-CAM Core` OpenAPI 3.1.0 document at version `0.2.0`. The document has 39
paths, 42 operations, and 59 schemas. Swagger request submission is disabled,
and the host does not implement the described operations.

It is useful as a future Developer Portal seed and an older contract reference,
but it is not canonical for Phase 5. The Phase 4.7 handoff remains
authoritative. Before reuse, its OpenAPI document must be diffed against current
contracts, its documentation assets must be served without unintended external
CDN reliance, response/security headers must be added, and the build-time
contract URL override must be constrained. It has no CI or license file.

The machine-readable inventory, including all paths, byte counts, Git blob
identities, dependencies, contracts, workspaces, and boundaries, is in
`contracts/phase-5/final-ui-repository-snapshot.json`.

## Complete File Inventory

| Area | Files | Disposition |
| --- | --- | --- |
| Repository metadata | `.gitignore`, `README.md` | Retain intent; replace README with monorepo and validation instructions during authorized adoption. |
| Build | `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `index.html` | Use as migration input, then move to shared workspace policy and independently buildable portal app. |
| Browser validation | `playwright.config.ts`, `src/browser/command-center.spec.ts` | Preserve scenarios, but repair stale expectations before claiming evidence. |
| Unit validation | `src/App.test.tsx`, `src/test/setup.ts` | Reuse behavioral assertions after splitting by route and contract. |
| Application shell | `src/main.tsx`, `src/App.tsx` | Primary interaction baseline; decompose shell, routing, session, navigation, and command palette. |
| Browser contracts | `src/api.ts`, `src/types.ts` | Replace hand-written casts with generated/validated typed clients and Phase 4.7 error/concurrency semantics. |
| Media | `src/useWhep.ts`, `src/components/LivePlayer.tsx` | Reuse UX/state vocabulary; place behind selected typed HLS/WHEP playback adapter. |
| Operational views | `CommandOverview.tsx`, `LiveMonitor.tsx`, `GisWorkspace.tsx` | Highest-value reusable product work; preserve visual hierarchy and operator flow. |
| Placeholder/readiness views | `ModuleWorkspace.tsx` | Keep visual concepts; replace static readiness copy with bounded vertical portal implementations. |
| Design | `src/styles.css` | Use as visual reference and token source; split into tokens, primitives, layouts, and portal styles. |
| Brand asset | `src/assets/netra-sentinel-emblem.png`, `src/vite-env.d.ts` | Preserve only with an explicit provenance/usage record and responsive asset variants. |

All 24 `main` paths are represented above and recorded individually. All 18
files in the divergent `api-doc-ui` branch are also individually recorded in
the snapshot. The `gis` tree is an ancestor of `main` and is sealed by its
independent tree-manifest digest.

## Implemented User Experience

The application has a dense, control-room-oriented shell with grouped desktop
navigation, a mobile drawer and command dock, a mission/status strip, a
keyboard command palette, hash-based workspace restoration, a full-page
session failure state, and current-workspace document titles.

Fourteen visible workspaces exist:

1. Command Overview
2. Live Monitor
3. Gujarat GIS
4. Corridors
5. Camera Registry
6. AI & ANPR
7. Forensics
8. Audit & Incidents
9. Maintenance
10. ONVIF
11. Developer
12. Telemetry
13. State Blueprint
14. Settings

Command Overview, Live Monitor, and Gujarat GIS have real interaction logic.
The remaining workspaces mainly expose truthful readiness, empty, or protected
states over the same small dashboard contract. They are useful design and
workflow prototypes, but they do not implement the corresponding Phase 4
intelligence, review, investigation, evidence, security, or operations APIs.

## Current Browser Contract

The source directly invokes four same-origin operations:

| Operation | Purpose | Current limitation |
| --- | --- | --- |
| `GET /cam-adapter/dashboard/data` | Adapter status and approved camera list | Hand-written response cast; no runtime schema, ETag, freshness, correlation ID, or typed problem response. |
| `GET /cam-adapter/monitoring-dashboard/map-data` | Bounded camera/operation GeoJSON | Fixed layer request and limit; no cursor, server capability envelope, or OGC contract. |
| `POST /cam-adapter/live/whep/{camera_id}` | Create receive-only playback session | No typed media adapter, HLS fallback, content-type/size guard, or standardized error model. |
| `DELETE /cam-adapter/live/whep/{session_id}` | Best-effort session cleanup | Fire-and-forget cleanup with no visible confirmation or recovery contract. |

This is compatible with decision `D-P5.0-003:A` in principle because requests
use same-origin credentials. It is not yet a complete backend-for-frontend
session design: login/bootstrap, renewal, expiry recovery, CSRF defense,
capability projection, department scope, and reason-bearing mutations are not
implemented.

## GIS Assessment

The GIS is intentionally local-only and does not fetch an external basemap.
It supports viewport-bounded loading, camera/incident/patrol/zone layers,
filtering, local clustering, Point and Polygon rendering, approved-live gates,
responsive explorer/detail drawers, and clear synthetic-lab labels.

The implementation is a valuable UX baseline, but Phase 5 decision
`D-P5.0-005:D` selects authoritative MapLibre 2D plus a guarded optional 3D
analysis adapter. The current Leaflet map therefore remains a reference during
migration, not the target renderer. `MultiPolygon` is present in the TypeScript
type but is not rendered; line/corridor geometry, server-driven styles,
temporal overlays, correction state, stale/degraded layers, accessible list
equivalence, and optional 3D parity are also missing.

## Live Media Assessment

The WHEP hook has several sound boundaries: receive-only transceivers, no
recording code, same-origin signaling, explicit session cleanup, bounded ICE
gathering wait, generation-based stale-attempt rejection, and separation
between signaling connected and advancing-media proof.

It remains a provisional WHEP-only implementation. The selected Phase 5 design
requires one typed playback interface with HLS and WHEP lanes, explicit policy
selection, media/session timeouts, bounded SDP responses, content-type checks,
fallback semantics, telemetry redaction, and capability-based quality. The
player's advancing-time detector also retains its previous `timeRef` across
stream changes, so a new stream can be reported stalled against the old
stream's clock until that state is reset.

## Testing And Evidence Assessment

The unit suite covers navigation, command search, responsive controls, safe
empty/readiness states, session expiry, GIS lab labeling, and the absence of
device/control actions in protected workspaces. This is useful intent-level
coverage.

The Playwright suite is stale against the current redesign. It expects the app
to land on Live Monitor and expects Command Overview and Camera Registry to be
disabled, while the current application lands on Command Overview and enables
both routes. The repository README also omits `npm run test:browser` from its
validation command list. Therefore browser validation cannot be claimed for
the pinned commit without repair and execution.

No current test directly validates successful WHEP signaling/media progress,
cleanup races, HLS fallback, runtime response validation, ETag conflicts,
idempotency, reason capture, browser event gaps, focus restoration, focus
trapping, localization, measured contrast, reduced motion, or automated
accessibility rules. No CI workflow enforces typecheck, tests, build, dependency
review, or artifact provenance.

## Accessibility Assessment

Positive foundations include semantic buttons, headings, labels, visible
focus styles, a skip link, non-color state text/icons, polite status regions,
mobile-specific controls, and accessible names on many icon actions.

The command dialog has no explicit focus trap or focus-return implementation;
several complex widget patterns need keyboard conformance testing; the CSS has
many 6-9px labels; there is no reduced-motion or forced-colors policy; and no
axe, contrast, zoom/reflow, screen-reader, or manual keyboard evidence exists.
The result is an accessibility-aware prototype, not a WCAG conformance claim.

## Security And Privacy Assessment

Positive boundaries include no committed secrets, no external source asset
URLs, same-origin credentials, no browser token storage, no `eval`, no
`dangerouslySetInnerHTML`, escaped data in Leaflet tooltip HTML, no automatic
device discovery, and explicit zero-retention/no-control language.

Required hardening before adoption includes runtime response validation,
content security policy and deployment headers, anti-CSRF design for state
changes and WHEP session creation, bounded payload handling, sanitized RFC
9457-style problems, request correlation, server-returned capability gates,
unknown-event quarantine, dependency/SBOM/provenance controls, and tests that
prove locators and credentials never enter browser-visible state. The Vite
build currently emits source maps and the repository has no license or brand
asset provenance record; both require an explicit release decision.

## Architecture And Maintainability Assessment

The code is compact and readable at prototype scale, but it is concentrated:
`ModuleWorkspace.tsx` is about 51 KiB, `App.tsx` about 20 KiB,
`GisWorkspace.tsx` about 21 KiB, and `styles.css` about 141 KiB. Fourteen routes,
37 static feature definitions, session behavior, navigation, and many portal
surfaces share one application and a small manually typed data model.

The selected multi-app monorepo should extract a shared shell, route manifest,
design tokens, accessible primitives, contract client, query/event layer,
playback adapter, map adapter, policy-capability resolver, localization, and
test fixtures. This keeps the existing visual identity while preventing one
component and one stylesheet from becoming the Phase 5 integration point.

## Phase 4.7 Handoff Coverage

| Handoff area | Existing UI | Required Phase 5 disposition |
| --- | --- | --- |
| 16 HTTP operations | 0 of the 16 are wired; 4 camera-adapter operations exist outside that handoff | Generate and validate typed clients; preserve the adapter routes as a separate camera vertical slice. |
| 6 change events | None | Add scoped browser event gateway; use only as hints/projections under `D-P5.0-004:A+B`. |
| 2 workflows | Static readiness copy only | Implement review/investigate and degradation workflows as bounded vertical slices. |
| 11 UI states | Loading, empty, denied/expired, error, and selected partial states | Add explicit partial, stale, degraded, conflict, recovery, correction, and success models to every relevant resource view. |
| 9 accessibility requirements | Several foundations, no conformance evidence | Add automated and manual evidence portfolio under `D-P5.0-011:A`. |

## Decision Alignment

| Decision | Selection | Existing UI alignment |
| --- | --- | --- |
| D-P5.0-001 | B | Does not align structurally: one standalone app/repo. It becomes the Command Center seed in one multi-app monorepo. |
| D-P5.0-002 | A | Direct match: React, TypeScript, Vite. |
| D-P5.0-003 | A | Partial match: same-origin credentials; BFF/session controls incomplete. |
| D-P5.0-004 | A+B | Not implemented: direct fetch and local state only; no query cache or event channel. |
| D-P5.0-005 | D | UX aligns; renderer differs because current code uses Leaflet, not MapLibre plus optional 3D. |
| D-P5.0-006 | C | Partial match: WHEP lane exists; typed adapter and HLS lane do not. |
| D-P5.0-007 | A | Partial match: H-CAM tokens/native controls exist; accessible headless primitive layer does not. |
| D-P5.0-008 | A | Not implemented: no server workspace or local preference persistence. |
| D-P5.0-009 | A | Not implemented: English-only strings and no message catalogue. |
| D-P5.0-010 | A | Not implemented: no policy-ceiling capability resolver. |
| D-P5.0-011 | A | Partial match: unit/browser test sources exist; browser suite is stale and manual evidence is absent. |
| D-P5.0-012 | A | Compatible: adopt after shared foundation, then deliver bounded vertical slices. |

## Final Disposition

Use the pinned repository as the primary design source, not as a drop-in
production application. Preserve its operational density, shell hierarchy,
command palette, safety labeling, live-proof semantics, GIS explorer/detail
pattern, responsive behavior, and NETRA SENTINEL identity. Refactor its code
into the selected Phase 5 foundation and replace placeholder modules with
contract-backed vertical slices.

Use the divergent `api-doc-ui` branch only as an attributed Developer Portal
and contract-browser seed. Do not combine its FastAPI documentation host with
the operator BFF, and do not let its older OpenAPI export override the accepted
Phase 4.7 handoff.

No existing feature needs to be visually downgraded. Where the current source
conflicts with accepted architecture, security, accessibility, or Phase 4.7
contracts, preserve the user experience and replace the underlying mechanism.
