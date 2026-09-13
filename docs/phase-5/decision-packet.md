# P5.0 Owner Decision Packet

Status: owner selections pending

Authority: `D-P5.0-PLAN-AUTH`

These choices define the proposed Phase 5 Operator Application architecture.
They are non-effective until the owner records every decision and accepts a
later reconciled planning package. No option authorizes implementation,
dependency installation, media, data, models, operational action, deployment,
or remote Git.

## Recommended Profile

`B / A / A / A / D / C / A / A / A / A / A / A`

This profile uses independently buildable portals in one TypeScript monorepo,
a React/Vite client foundation, a same-origin backend-for-frontend security
boundary, HTTP-authoritative server state with bounded event invalidation, a
2D MapLibre operational map plus guarded optional 3D analysis, HLS and
provisional WHEP behind one playback-session adapter, an accessible H-CAM
design system, bounded server-backed workspaces with non-sensitive local
preferences, English/Gujarati/Hindi architecture from the start, deterministic
hardware-aware capability profiles, layered quality evidence, and staged
foundation plus vertical-slice delivery.

## D-P5.0-001: Portal Packaging Topology

### A. One application with all routes

One SPA contains every command, operations, intelligence, investigation,
evidence, admin, and security route.

Benefits: simplest build and deployment; easiest local development. Costs:
larger bundle and test surface; weak ownership boundaries; one release couples
every team and portal.

### B. Independently buildable portal apps in one monorepo

Keep role-oriented applications and shared packages in one workspace and
lockfile. Each portal builds and tests independently, while a shared shell can
present them as one platform.

Benefits: strong ownership and bundle boundaries without runtime federation;
atomic contract/design changes; flexible combined or separate deployment.
Costs: requires package-boundary enforcement and compatibility discipline.

### C. Runtime microfrontends

Each portal is independently deployed and loaded through module federation or
another remote-bundle mechanism.

Benefits: independent runtime releases. Costs: remote-code trust, shared-
dependency, version, CSP, failure, accessibility, and integration complexity
are high for the current six-person team.

### D. Separate repositories with independent stacks

Every portal owns its repository and technology.

Benefits: maximum team independence. Costs: duplicated security, contracts,
design, testing, dependency policy, and release evidence; high drift risk.

Recommendation: **B**.

## D-P5.0-002: Frontend Framework And Build Foundation

### A. React, TypeScript, and Vite

Use a client-rendered React/TypeScript foundation with Vite builds, explicit
browser targets, route-level splitting, and independently buildable entries.

Benefits: strong ecosystem for dense data applications, maps, video, testing,
and component composition; Vite supports monorepo and multi-entry patterns.
Costs: architecture discipline is required; React alone does not provide
routing, data, security, or accessible widgets.

### B. Next.js

Use Next.js with its server/client routing and rendering model.

Benefits: mature integrated application framework and server boundary. Costs:
SSR/RSC complexity offers limited value for an authenticated operator tool;
map/video/browser-only modules require careful boundaries; runtime is more
prescriptive.

### C. Angular

Use Angular's full framework, dependency injection, routing, forms, and test
patterns.

Benefits: strong enterprise conventions and batteries included. Costs: larger
learning and framework surface for the current codebase; less sympathy with
the existing lightweight service architecture.

### D. Web Components and minimal framework

Build standards-based components and use only small libraries.

Benefits: portable components and low framework coupling. Costs: dense grids,
forms, routing, async state, accessibility, and test architecture require more
custom code and integration risk.

Recommendation: **A**. Exact versions and packages remain unapproved.

## D-P5.0-003: Browser Authentication Boundary

### A. Same-origin backend-for-frontend with server-managed session

Use a same-origin web boundary, secure HttpOnly/SameSite cookies, explicit
CSRF protection, server-side identity/token handling, and exact logout/session
semantics.

Benefits: reduces bearer-token exposure to browser JavaScript; centralizes
security headers, API policy, revocation, and identity-provider integration.
Costs: adds a web/BFF service boundary and session infrastructure.

### B. OAuth browser client with Authorization Code and PKCE

The SPA obtains and uses access tokens directly under RFC 10017 and RFC 9700
requirements.

Benefits: fewer server components and standard browser-client model. Costs:
malicious same-origin JavaScript can access tokens; storage and refresh are
harder to secure for a high-value operator application.

### C. Existing development headers in the browser

Continue using local development identity headers.

Benefits: fastest prototype. Costs: unacceptable outside isolated generated
development; no real authentication or session boundary.

### D. Desktop native wrapper as the identity boundary

Place the web UI in Electron/Tauri and store credentials through native APIs.

Benefits: managed desktop integration. Costs: expands supply chain, update,
device, native security, packaging, and deployment scope before web semantics
are proven.

Recommendation: **A**. Development-header auth may remain only in separately
accepted generated local tests.

## D-P5.0-004: Server State And Real-Time Updates

### A. HTTP-authoritative query cache plus bounded event invalidation

Use typed HTTP resources and ETags as truth. An authenticated server event
channel invalidates queries; the client refetches current state. Polling is the
fallback.

Benefits: aligns with P4.7 contracts; handles missed/replayed events safely;
preserves server authority. Costs: additional reads and careful freshness,
gap, and retry logic.

### B. WebSocket-authoritative client store

Apply every event directly to a long-lived browser state model.

Benefits: low apparent latency. Costs: replay, gap, ordering, correction,
authorization, and version errors can create false browser truth.

### C. Polling only

Refresh every screen on fixed intervals.

Benefits: simple and robust. Costs: unnecessary load and slower updates;
foreground/background cadence becomes difficult across many portals.

### D. Direct event-broker subscription

The browser connects to Kafka, NATS, MQTT, or another broker.

Benefits: direct event delivery. Costs: exposes broker credentials and topology
and bypasses the accepted browser security boundary.

Recommendation: **A**.

## D-P5.0-005: GIS And Spatial Rendering

### A. MapLibre 2D only

Use MapLibre GL JS behind a typed GIS package for vector/raster tiles,
features, clusters, tracks, zones, and heatmaps.

Benefits: strong open TypeScript/WebGL map foundation and efficient vector-
tile rendering. Costs: complex 3D/terrain investigation views are limited.

### B. OpenLayers 2D only

Use OpenLayers for broad projections, raster/vector formats, and mapping.

Benefits: mature GIS feature depth. Costs: a different rendering and styling
model; team and UI integration cost must be evaluated.

### C. Cesium 3D first

Use a 3D globe/terrain environment as the primary operational map.

Benefits: advanced 3D, terrain, camera, and temporal visualization. Costs:
heavier GPU/browser requirements, harder accessibility, and unnecessary
complexity for most command and control-room tasks.

### D. Authoritative MapLibre 2D plus guarded optional 3D analysis adapter

Use MapLibre as the default operational map. Preserve renderer-neutral
contracts and add a separately loaded 3D adapter only for accepted use cases
and capable hardware. Lists/tables remain authoritative alternatives.

Benefits: reliable 2D workflow with an upgrade path to high-end 3D; supports
low-resource and control-room profiles without separate domain semantics.
Costs: two renderers eventually require projection, selection, accessibility,
and performance equivalence tests.

Recommendation: **D**, with 3D disabled until separately implemented and
validated. No map or tile provider is selected by this choice.

## D-P5.0-006: Live Media Strategy

### A. HLS compatibility lane only

Consume short-lived playback sessions through native HLS or a reviewed
Media-Source-based HLS player.

Benefits: broad delivery and adaptive streaming. Costs: latency may be higher
than WebRTC and browser codec support varies.

### B. WebRTC/WHEP low-latency lane only

Consume every live session through WebRTC using a version-pinned WHEP adapter.

Benefits: low latency. Costs: WHEP remains an Internet-Draft; ICE, privacy,
network, reconnect, and browser behavior are more complex; no fallback.

### C. One typed playback adapter with HLS and provisional WHEP lanes

Use HLS as compatibility fallback and WHEP as a low-latency option when server
policy, stream capability, browser support, and effective profile permit it.
Both use server-issued sessions and one normalized state/teardown contract.

Benefits: best capability range without exposing camera protocols; dynamic
selection across laptops and stronger workstations. Costs: two adapters and a
strict equivalence/browser matrix are required.

### D. WebSocket JPEG or custom frame transport

Send images/frames over a custom socket protocol.

Benefits: easy first picture in a demo. Costs: inefficient, poor adaptive
behavior, custom protocol/security burden, and likely performance downgrade.

Recommendation: **C**. Recording, download, snapshot, and camera control stay
absent.

## D-P5.0-007: Design System And Complex Components

### A. H-CAM tokens plus reviewed accessible headless primitives

Own semantic tokens, operational styling, contracts, and domain components;
use reviewed headless primitives for difficult focus/keyboard behavior. Use a
separate virtualized table/grid foundation only where needed.

Benefits: domain-specific and accessible without building every primitive;
portable across portals. Costs: integration and version governance remain
H-CAM responsibilities.

### B. Material UI as the complete design system

Use MUI components, theme, and data grid.

Benefits: rapid enterprise UI delivery. Costs: strong visual/product coupling,
bundle/licensing considerations for advanced grid features, and customization
can become complex.

### C. IBM Carbon as the complete design system

Use Carbon components and interaction patterns.

Benefits: mature enterprise conventions and accessibility investment. Costs:
strong brand/layout assumptions and potentially heavy adaptation for video,
GIS, and police-domain workflows.

### D. Fully custom components from native elements

Implement every component internally.

Benefits: maximum control. Costs: high accessibility, keyboard, maintenance,
testing, and delivery risk with little domain benefit.

Recommendation: **A**. Exact primitive and grid packages remain a later
dependency decision.

## D-P5.0-008: Workspace And Preference Persistence

### A. Typed server workspaces plus local non-sensitive display preferences

Persist saved filters/layouts on the server only through a future scoped
contract. Store only harmless device-local preferences such as theme, density,
language, and reduced motion. Never persist query results, tokens, media, or
sensitive terms.

Benefits: portable operator workspaces with clear ownership and safe local
fallback. Costs: requires a new server contract and retention policy.

### B. Local storage for all workspace state

Store filters, selected records, layouts, and drafts in the browser.

Benefits: easy and offline-friendly. Costs: leaks protected context on shared
devices and creates stale unauthorized state.

### C. URL-only workspace state

Represent every filter, panel, map, and selected record in the URL.

Benefits: reproducible navigation. Costs: browser history, logs, referrers, and
screenshots can expose sensitive context; URLs become unwieldy.

### D. No persistence

Reset every workspace on navigation or reload.

Benefits: minimal retention risk. Costs: poor control-room ergonomics and lost
context during safe refresh or reauthentication.

Recommendation: **A**, with server workspaces blocked until their contract is
accepted.

## D-P5.0-009: Language And Localization Baseline

### A. English, Gujarati, and Hindi architecture from the first component

Use message keys, locale-aware date/time/number formatting, text-expansion
fixtures, fallback rules, and canonical timestamp visibility from P5.1.

Benefits: prevents late layout and content-model rework; fits Gujarat operator
needs. Costs: translation governance and terminology review are required.

### B. English implementation first, localization later

Benefits: faster initial implementation. Costs: hard-coded strings, layout
assumptions, date/time ambiguity, and substantial rework risk.

### C. English and Gujarati only

Benefits: smaller initial language scope. Costs: excludes Hindi workflows and
still requires full localization architecture.

### D. Machine translation at runtime

Benefits: broad apparent language coverage. Costs: network/data leakage,
uncontrolled police terminology, nondeterminism, and operational ambiguity.

Recommendation: **A**. Planning does not authorize translation services or
claim that translations are approved.

## D-P5.0-010: Hardware-Aware UI Capability Profiles

### A. Deterministic policy-ceiling capability resolver

Resolve `safe_minimum`, `balanced`, `enhanced`, or `control_room` from server
policy, deployment profile, coarse browser capability, live degradation, and
user preference. The lowest ceiling wins.

Benefits: functionally complete laptop mode plus automatic upgrades for GPU
workstations and future control rooms; explicit and testable. Costs: requires
profile matrices and hardware/browser evidence.

### B. User manually chooses quality

Benefits: simple and transparent. Costs: users can overload systems or select
unsupported behavior; poor defaults on unfamiliar machines.

### C. Browser auto-detection only

Benefits: automatic. Costs: cannot know server/network policy, can fingerprint
devices, and may choose unsafe fan-out.

### D. One fixed lowest-common-denominator UI

Benefits: simplest testing. Costs: wastes capable hardware and conflicts with
the platform-wide dynamic scaling objective.

Recommendation: **A**. Profiles may change rendering/resource budgets only,
never authorization or semantics.

## D-P5.0-011: Validation And Accessibility Evidence

### A. Layered automated plus manual evidence

Require contract, unit, component, browser E2E, visual, localization,
performance, security, storage, and compatibility tests plus manual keyboard,
screen-reader, zoom, target, contrast, motion, map, graph, timeline, and media
workflow review.

Benefits: strongest evidence across dynamic enterprise workflows; prevents an
automated accessibility score from becoming a false conformance claim. Costs:
larger test harness and human review effort.

### B. Automated tests only

Benefits: fast and repeatable. Costs: misses many keyboard, focus, screen-
reader, cognitive, map/video, and real browser issues.

### C. Manual acceptance only

Benefits: direct human experience. Costs: non-deterministic, expensive, weak
regression protection, and difficult to reproduce.

### D. Visual screenshots as acceptance

Benefits: catches layout drift. Costs: does not validate semantics,
authorization, keyboard, accessibility, state, or workflow behavior.

Recommendation: **A**.

## D-P5.0-012: Delivery And Acceptance Model

### A. Shared foundation followed by bounded vertical portal slices

Implement P5.0 and P5.1 first, then deliver command, camera/live,
intelligence/review, investigation/evidence, and admin/security as end-to-end
contract-bound slices. Each subphase has generated evidence and exact owner
acceptance; final P5.7 validates cross-portal behavior.

Benefits: reusable foundation plus visible, testable product increments;
contract gaps are closed before screen reliance. Costs: foundation needs
discipline to avoid over-generalization.

### B. Build every screen visually, then connect APIs

Benefits: fast screenshots. Costs: mock behavior becomes implicit contract;
security, state, accessibility, and producer gaps arrive late.

### C. Build backend gaps for all portals before any UI

Benefits: complete API surface first. Costs: delays operator feedback and may
build unused abstractions.

### D. One continuous Phase 5 implementation with final acceptance only

Benefits: fewer gates. Costs: large review surface, unclear progress, and late
detection of architecture or safety failures.

Recommendation: **A**.

## Required Owner Response

Record exactly one option for every decision:

```text
D-P5.0-001: B
D-P5.0-002: A
D-P5.0-003: A
D-P5.0-004: A
D-P5.0-005: D
D-P5.0-006: C
D-P5.0-007: A
D-P5.0-008: A
D-P5.0-009: A
D-P5.0-010: A
D-P5.0-011: A
D-P5.0-012: A
```

Composite selections require explicit reconciliation and cannot silently merge
incompatible authorities. After selection, only a non-effective reconciled
planning package may be prepared. Implementation remains closed until a later
exact start package is separately authorized.
