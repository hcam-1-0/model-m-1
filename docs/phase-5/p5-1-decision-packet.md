# P5.1 Shared Application Foundation Decision Packet

Status: non-effective options; owner selections pending

Authority: `D-P5.1-PLAN-AUTH`

## How To Decide

Select one option for each decision. The recommendation profile is:

`B / A / A / A / A / A / A / A / A / A / A / A`

The recommendation preserves the accepted P5.0 architecture and Gujarat GIS
contract while keeping P5.1 portable from a low-resource laptop to a future
server-backed deployment. Selection does not authorize implementation. After
selection, a reconciled planning package and exact start package remain
required.

## D-P5.1-001: Workspace And Toolchain Baseline

### A. npm Workspaces

Keep the package-manager family used by the pinned final-ui reference. This
minimizes initial migration friction but provides weaker workspace protocol and
central version-governance ergonomics than the recommended option.

### B. pnpm Workspace With Catalogues And Workspace Protocol (Recommended)

Use one lockfile, exact workspace boundaries, `workspace:` for internal
dependencies, central version catalogues, strict peer/dependency checks, and a
supported Node LTS baseline. Preserve source provenance from final-ui without
preserving its package-manager choice as an architectural constraint.

The start package must pin the exact Node, pnpm, React, TypeScript, Vite, and
tool versions; prohibit dependency cycles; define offline/reproducible install
evidence; and inspect install scripts before any package download.

### C. pnpm Plus Nx Or Turborepo Orchestration

Add a task-graph and caching product immediately. This can improve a larger
workspace but expands the supply chain and cache/provenance surface before the
portal graph demonstrates a need.

### D. Runtime Microfrontends

Build and load portals independently at runtime. This maximizes organizational
independence but adds version skew, session, CSP, deployment, accessibility,
and failure coordination complexity. It conflicts with the accepted default of
independently buildable apps without runtime federation.

## D-P5.1-002: Routing And Portal Shell

### A. React Router Data Mode With Static Typed Manifests (Recommended)

Use one route manifest per portal, shared shell boundaries, typed deep links,
and Data Mode for shell bootstrap, access preflight, pending navigation, and
route errors. Keep resource data in the canonical query layer to avoid two
caches.

### B. Declarative Router Only

Use component routes and custom bootstrap/error handling. This is smaller but
moves more cross-cutting behavior into local application code.

### C. React Router Framework Mode

Adopt the framework compiler and route-module conventions. This provides more
integrated data and rendering behavior but gives H-CAM less control over its
existing BFF and independently built portal packaging.

### D. Custom Router

Own route parsing, history, matching, transitions, errors, and accessibility.
This adds high-risk infrastructure with no H-CAM-specific benefit.

## D-P5.1-003: Accessible Component Primitives

### A. Native HTML First, React Aria Components Behind H-CAM APIs (Recommended)

Use native elements wherever possible and wrap React Aria behavior for complex
composites. H-CAM owns tokens, visual design, state vocabulary, test contracts,
and exported APIs. This aligns with the existing interface without accepting a
pre-styled generic dashboard.

### B. Radix Primitives Behind H-CAM APIs

Use unstyled Radix primitives. This is viable, but internationalization and
the complete widget/evidence portfolio require more H-CAM-owned composition.

### C. Entirely In-House APG Components

Implement all widget behavior from WAI-ARIA guidance. It minimizes dependency
surface but creates a large, ongoing accessibility engineering obligation.

### D. Pre-Styled Enterprise Component Suite

Use a comprehensive visual suite. This accelerates basic controls but risks
visual downgrade, bundle growth, restrictive styling, and generic dashboard
composition that conflicts with the approved baseline.

## D-P5.1-004: API Type And Runtime Validation Pipeline

### A. OpenAPI 3.1 To Generated Types Plus Strict Standalone Validation (Recommended)

Pin accepted OpenAPI schemas, generate TypeScript operation types and a small
fetch client, and compile strict Ajv JSON Schema 2020-12 standalone validators
for every untrusted boundary. Add a minimized RFC 9457 problem mapper and exact
compatibility classification.

### B. Handwritten Zod Contracts

Maintain TypeScript and validation schemas in the frontend. This is ergonomic
but introduces a second manually maintained contract source beside accepted
producer schemas.

### C. Generated TypeScript Without Runtime Validation

Trust server responses after compile-time generation. This does not protect a
running client from version drift, malformed payloads, hostile data, or a
misconfigured provider.

### D. General SDK Generator

Generate a full client SDK including transport and models. This may produce
more code than H-CAM needs and can obscure error, retry, redaction, and
compatibility behavior.

## D-P5.1-005: Server State And Event Invalidation

### A. TanStack Query With An H-CAM Operation Policy Registry (Recommended)

Use typed query definitions, but require explicit freshness, retry,
cancellation, cache, polling, invalidation, redaction, and persistence policy
per operation. Events only invalidate or supply labeled non-authoritative
projections. Polling is the complete fallback.

### B. Router Loaders As The Only Data Layer

Put all resource reads in route loaders. This simplifies some screens but is a
poor fit for dense live workspaces, independent panels, pagination, and event
invalidation.

### C. Redux Toolkit For All Remote And Local State

Centralize every state class. This is explicit but can mix server cache,
session policy, local UI state, and event projections into one broad mutable
store.

### D. Custom Cache And Event Store

Build H-CAM-specific caching and invalidation. This creates correctness,
concurrency, cancellation, and lifecycle risk without a proven requirement.

## D-P5.1-006: Session, CSRF, And Reauthentication

### A. Same-Origin BFF With Host Cookie And Synchronizer Token (Recommended)

Use a `Secure`, `HttpOnly`, `SameSite` host cookie, a server-issued
synchronizer token held only in memory and sent in a custom header, plus
Origin/Referer and Fetch Metadata validation. Model idle expiry, absolute
expiry, role/department change, and step-up reauthentication explicitly.

### B. Signed Double-Submit Cookie

Use a session-bound signed CSRF cookie plus request value. This can work, but
the accepted stateful BFF model makes a synchronizer token clearer.

### C. Browser Bearer Tokens

Store access tokens in browser memory or persistent storage. This expands the
XSS and lifecycle surface and contradicts the accepted server-managed session.

### D. SameSite Cookie Only

Rely only on cookie attributes. OWASP treats SameSite as defense in depth, not
a complete stateful CSRF defense.

## D-P5.1-007: Localization And Operational Time

### A. React Intl With ICU Catalogues (Recommended)

Implement stable message IDs, ICU formatting, English/Gujarati/Hindi catalogue
completeness, pseudo-locale and long-text evidence, locale-aware numbers and
dates, and explicit operational timezone display over canonical timestamps.

### B. i18next Catalogue Stack

Use i18next and ICU-compatible plugins. This is viable but introduces a wider
plugin selection and configuration decision.

### C. Custom JSON Lookup

Build basic key/value translation. This appears small but grows into custom
plural, date, number, fallback, extraction, and validation machinery.

### D. English-First Migration

Add Gujarati and Hindi after the shared UI stabilizes. This would repeat the
prototype's hard-coded string structure and create avoidable layout and
component rework.

## D-P5.1-008: Dynamic Resource Profiles

### A. Server Ceiling Plus Coarse Browser Capabilities And Session Health (Recommended)

Intersect safe-low defaults, server policy, operator/department capability,
build support, coarse browser feature checks, and bounded session-local health.
Use WebGL2 only to admit map rendering and Media Capabilities only to advise
future playback. Do not collect raw hardware identity or durable fingerprints.

### B. Manual Static Profiles

Let the operator select low, enhanced, or control-room mode. This is
predictable but can select unsupported behavior and places technical decisions
on operators.

### C. Fully Automatic Performance Tuning

Continuously benchmark and change behavior. This can optimize throughput but
creates unpredictable state, fingerprinting, battery/thermal, and operational
workflow risks.

### D. Server-Selected Profile Only

Trust server deployment class and ignore browser support. This cannot safely
admit WebGL, media decoding, window, or accessibility capabilities.

## D-P5.1-009: Persistence And Multi-Window State

### A. Memory Default, Typed URL, Harmless Preferences, Server Workspaces (Recommended)

Keep resources, session, drafts, events, and errors in memory. Permit only
opaque bounded route state in URLs and versioned, TTL-limited display
preferences locally. Persist real layouts and workspaces on the server with
ETags. Treat control-room windows as independent consumers.

### B. Persist Query Cache And Synchronize Tabs

Improve resume behavior through IndexedDB/localStorage and cross-tab events.
This increases data-remanence, scope-change, logout, versioning, and disclosure
risk.

### C. No Persistence Of Any Kind

Keep all state in memory and do not save display preferences. This is safest
but unnecessarily harms repeated operator workflows.

### D. Offline-First Service Worker

Cache application and resource data for offline operation. This introduces a
large security, invalidation, deployment, and retention boundary that P5.1 does
not require.

## D-P5.1-010: Client Observability

### A. H-CAM Typed Signals With Default-Off OTel Adapter (Recommended)

Define low-cardinality, minimized, payload-free client signals and a default-
off adapter compatible with future OpenTelemetry export. Keep the internal
contract stable while browser instrumentation remains experimental.

### B. Full OpenTelemetry Browser Auto-Instrumentation

Adopt broad automatic tracing now. This is quick to demonstrate but may collect
URLs, attributes, errors, and timings outside H-CAM's minimization contract.

### C. Vendor Browser SDK

Use a hosted observability vendor. This creates external network, data,
credential, procurement, and deployment dependencies outside current scope.

### D. No Client Observability

Rely on server signals only. This loses browser compatibility, accessibility,
rendering, route, capability, and degradation evidence.

## D-P5.1-011: Test And Evidence Portfolio

### A. Tiered Unit, Component, Story, Browser, Visual, Security, And Manual Evidence (Recommended)

Use Vitest projects and Testing Library for generated unit/component work,
Storybook for governed component/state catalogues and automated accessibility,
and Playwright for browser, responsive, locale, timezone, visual, security, and
critical-flow evidence. Maintain quick laptop and full evidence profiles.
Manual keyboard and assistive-technology evidence remains mandatory.

### B. Vitest And Playwright Only

Cover unit and browser flows without a persistent state catalogue. This is
smaller but makes design-system review and exhaustive UI state coverage harder.

### C. Storybook As Primary Verification

Center testing on isolated component stories. This does not prove portal
routing, session teardown, server-state policy, or cross-boundary workflows.

### D. Manual Testing First

Use human walkthroughs as the primary gate. This is slow, inconsistent, and
does not provide deterministic contract or regression evidence.

## D-P5.1-012: Existing Final-UI Source Adoption

### A. Hash-Bound Staged Adoption With Parity Gates (Recommended)

Under a later exact authorization, place the pinned source in a build-excluded,
attributed reference area; extract tokens, shell behavior, and route concepts;
then port Command, Live, and GIS separately. Compare visual, interaction,
responsive, accessibility, resource, safety, and security behavior. Never ship
the reference tree in a production bundle.

### B. Drop-In Copy As The Initial Frontend

Copy the existing app into the new workspace and refactor in place. This starts
quickly but risks carrying prototype routing, direct fetches, hard-coded text,
large styling, and architecture coupling into the foundation.

### C. Screenshot-Led Rewrite

Recreate the appearance without importing source. This loses interaction,
responsive, test, attribution, and hidden-state details and can silently
downgrade GIS behavior.

### D. Keep Final-UI As A Separate Runtime Frontend

Run it beside the new portals. This creates two shells, two session/state
models, divergent contracts, and a runtime integration problem.

## Reconciliation Rules

- Composite selections require an explicit precedence rule and closed default.
- Any option that changes the accepted P5.0 multi-portal, same-origin BFF,
  HTTP-authoritative, GIS, media, accessibility, localization, capability, or
  source-adoption direction requires a P5.0 rebaseline.
- Exact dependency versions and hashes are deliberately absent from this
  decision packet. They belong in the start package after current verification.
- Owner selection authorizes reconciliation only, not implementation.

## Selection Template

```text
D-P5.1-001: B
D-P5.1-002: A
D-P5.1-003: A
D-P5.1-004: A
D-P5.1-005: A
D-P5.1-006: A
D-P5.1-007: A
D-P5.1-008: A
D-P5.1-009: A
D-P5.1-010: A
D-P5.1-011: A
D-P5.1-012: A
```
