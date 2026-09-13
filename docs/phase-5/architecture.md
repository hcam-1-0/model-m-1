# Phase 5 Operator Application Architecture

Status: proposed, non-effective, planning only

## Architecture Goals

1. Build a multi-portal enterprise operator environment from one coherent
   contract, design, security, and observability foundation.
2. Preserve independently buildable surfaces without requiring runtime
   microfrontend infrastructure for the first release.
3. Keep all authorization, department scope, purpose, reason, ETag,
   idempotency, lifecycle, and audit decisions on the server.
4. Prevent browser access to databases, brokers, cameras, ONVIF, raw RTSP,
   evidence stores, model runtimes, and external reference providers.
5. Make every async, failure, freshness, completeness, correction, and
   degradation state part of the typed UI contract.
6. Run functionally on a low-resource laptop and scale visual density on
   stronger workstations without changing semantic behavior or safeguards.
7. Treat accessibility, localization, performance, security, and browser
   compatibility as acceptance gates rather than later visual polish.

## Proposed Logical Architecture

```text
managed browser
  -> H-CAM same-origin web boundary
     -> authenticated session and CSRF boundary
     -> static portal assets and security headers
     -> typed browser-facing API projection
        -> accepted H-CAM service APIs
        -> accepted playback-session issuer
        -> future bounded event delivery adapter
  -> shared application foundation
     -> contract client and safe problem mapper
     -> server-state cache and event invalidation
     -> policy/capability projection
     -> design system and accessibility primitives
     -> GIS adapter
     -> live-media adapter
     -> client observability adapter
     -> localization and time presentation
  -> role-oriented portal applications
     -> Command
     -> Operations
     -> Intelligence
     -> Investigations
     -> Evidence
     -> Admin
     -> Security
```

The browser-facing boundary is a proposed pattern, not an implemented service.
The final authentication topology is an owner decision.

## Proposed Workspace Shape

```text
ui/
  apps/
    command/
    operations/
    intelligence/
    investigations/
    evidence/
    admin/
    security/
  packages/
    app-shell/
    design-system/
    contracts/
    api-client/
    auth-session/
    policy-capabilities/
    server-state/
    realtime/
    gis/
    media/
    timeline/
    data-grid/
    localization/
    observability/
    test-fixtures/
    test-harness/
```

This is a planning projection. Exact paths and package names must be frozen in
a later start package. Shared packages cannot import portal applications.
Portal-to-portal imports are forbidden; navigation and shared records use
versioned contracts.

## Packaging Strategy

The recommended baseline is a modular monorepo with independently buildable
portal applications and shared packages. It provides:

- one lockfile and dependency policy;
- atomic contract and design-system changes;
- per-app build and test boundaries;
- route-level code splitting and lazy feature loading;
- later ability to deploy one combined shell or separate portal bundles;
- no runtime module federation, cross-origin iframe, or remote bundle trust
  problem by default.

Microfrontends remain a future scale option only if team ownership and release
cadence justify their runtime and security cost. Repository count is not used
as a proxy for modularity.

## Portal Shell

The shared shell owns only cross-portal concerns:

- authenticated session state and expiry;
- active department and allowed department switching;
- application navigation and route restoration;
- global time-zone and language presentation;
- safe connection, stale, degraded, and maintenance banners;
- command palette for navigation and allowed read-only search;
- notification center for application state, not operational dispatch;
- consistent focus restoration and skip navigation;
- client capability profile and user display preferences;
- correlation context for safe diagnostics;
- portal boundary error handling.

The shell does not own domain data, review decisions, lifecycle state, evidence
content, camera credentials, or business authorization.

## Authentication And Session Boundary

The recommended architecture is same-origin browser delivery backed by a
server-managed session or backend-for-frontend:

```text
browser
  -> secure, HttpOnly, SameSite session cookie
  -> same-origin UI boundary
  -> server-side token/session handling
  -> H-CAM API with current principal and department scope
```

Required planning controls:

- exact identity provider and protocol selected separately;
- authorization code flow with PKCE where OAuth/OIDC is used;
- no implicit grant or resource-owner password grant;
- bearer and refresh tokens excluded from URLs, logs, local storage, and UI
  state;
- secure, HttpOnly, SameSite cookie policy with explicit CSRF protection;
- bounded idle and absolute session expiry;
- logout, revocation, identity-provider failure, and reauthentication states;
- exact redirect allowlist and no open redirect;
- step-up or separate approval where later policy requires it;
- server-returned role, department, purpose, and capability projection;
- no client-created principal, role, scope, or entitlement.

Direct SPA token handling remains an option in the decision packet but is not
recommended for this high-value operator surface.

## Data Architecture

### Four State Classes

| State class | Examples | Authority and retention |
| --- | --- | --- |
| Server resource state | Camera, alert, timeline, review, evidence reference | API response is authoritative; cache is bounded and freshness-labeled |
| Event hint state | Aggregate changed, correction recorded, degradation changed | Invalidation hint only; never grants authority or becomes final resource state |
| URL workspace state | Selected record, bounded filter, time window, safe sort, map extent | Typed, validated, non-sensitive, shareable only within authorization |
| Ephemeral UI state | Open panel, column width, temporary selection, draft reason | Memory by default; no domain consequence until server accepts a command |

Sensitive data, tokens, media, raw evidence, locators, secret references,
candidate payloads, and free-form operational content are prohibited from URL,
analytics, crash reports, persistent browser storage, and generic logs.

### Query Rules

- Each query key includes contract version, department scope, resource type,
  filters, sort, page or cursor, and bounded freshness class.
- Cache entries retain `observed_at`, `stale_at`, completeness, ETag, and source
  operation.
- Background refresh does not erase a visible stale/partial state.
- Automatic retries are disabled for authorization, validation, not-found,
  conflict, policy, unsupported, and configuration failures.
- GET retries are bounded for explicitly classified transient failures.
- Mutations do not retry unless idempotency and the accepted operation contract
  make the retry safe.
- A conflict loads the current resource and asks the user to reconsider; it
  does not replay a stale command automatically.

### Event Delivery

The proposed event path is:

```text
accepted transactional outbox
  -> future server event-delivery adapter
  -> authenticated browser SSE or WebSocket channel
  -> schema/version/department validation
  -> query invalidation
  -> bounded HTTP refresh
```

Required behavior includes connection identity, heartbeat, last accepted
sequence, gap detection, bounded replay, unknown-version quarantine,
department isolation, reconnect backoff, tab/background behavior, and polling
fallback. The browser never connects to the broker directly.

## API Client Boundary

One generated or hand-written typed client consumes the canonical H-CAM
catalogues and pinned OpenAPI projection. It must provide:

- explicit operation IDs and schema versions;
- typed success, partial, empty, stale, disabled, denied, conflict, failure,
  timeout, unavailable, and unknown results;
- RFC 9457-compatible safe problem mapping;
- ETag capture and `If-Match` submission;
- required reason and idempotency headers;
- request cancellation and timeout;
- cursor/snapshot pagination when contracts support it;
- no raw exception or response-body leakage;
- no permissive unknown-field acceptance for security-relevant contracts;
- compatibility telemetry without record identifiers.

The client cannot invent a missing route or fallback to direct persistence.

## Design System

The design system should be a restrained operational system, not a marketing
theme. It includes:

- neutral and semantic color tokens with non-color state indicators;
- typography and density scales with no viewport-scaled font sizes;
- spacing, sizing, border, elevation, and motion tokens;
- stable icon-button dimensions and Lucide-compatible icon abstraction;
- command bars, segmented controls, tabs, menus, toggles, inputs, date/time
  controls, tables, grids, trees, timelines, status regions, dialogs, drawers,
  split panes, map controls, and media controls;
- accessible names, descriptions, validation, focus, keyboard, and reduced-
  motion contracts for each primitive;
- high contrast and forced-colors behavior;
- English, Gujarati, and Hindi text expansion fixtures;
- light and dark operational themes only if both pass the same semantic and
  contrast evidence.

Native HTML semantics are preferred. ARIA composite widgets are used only
when their keyboard and focus contracts are fully implemented and tested.

## GIS Architecture

The map layer is an adapter over typed spatial contracts:

```text
viewport + time + department + layer filters
  -> bounded feature or tile query
  -> normalized spatial feature set
  -> MapLibre/OpenLayers/other renderer adapter
  -> selected feature -> canonical domain detail route
```

Required boundaries:

- base map, H-CAM features, heatmaps, tracks, routes, zones, and incidents are
  separate layers with independent freshness and attribution;
- WGS 84 coordinates are explicit; coordinate-order mistakes are tested;
- viewport queries have count, byte, geometry, time-window, and zoom bounds;
- clustering and server-side tiles are required for scale, not optional visual
  optimizations;
- every map-only result has a keyboard-accessible list/table alternative;
- selecting a map feature cannot bypass department scope;
- no external tile provider is presumed; offline or private tile topology is a
  future deployment decision;
- 3D is an optional analysis surface, not the default command experience.

## Live Media Architecture

The browser consumes a short-lived playback session, never a raw camera URL:

```text
operator selects authorized stream
  -> POST playback session
  -> short-lived playback URL and access material
  -> selected HLS or WebRTC/WHEP browser adapter
  -> bounded player lifecycle and quality telemetry
  -> explicit teardown on close, scope change, expiry, or logout
```

The media package exposes one normalized player contract:

- `idle`, `authorizing`, `connecting`, `playing`, `buffering`, `stalled`,
  `expired`, `denied`, `unsupported`, `failed`, and `closed` states;
- live-edge delay, dimensions, rendition, muted state, dropped-frame class,
  reconnect attempt, and safe reason code;
- native HLS when supported, reviewed MSE-based HLS fallback, and optional
  low-latency WebRTC/WHEP adapter;
- strict session, source, quality, reconnect, and teardown budgets;
- no automatic recording, screenshot, export, download, or local persistence;
- no background audio and muted-by-default multi-tile playback;
- no upscaling presented as source quality;
- no analytics overlay unless geometry, source frame, time alignment, and
  confidence contracts are accepted.

WHEP remains an active Internet-Draft and must be treated as provisional.

## Adaptive Capability Architecture

The capability resolver computes an effective profile:

```text
effective = minimum(
  server_policy_ceiling,
  deployment_profile,
  browser_capability,
  current_degradation_budget,
  operator_preference
)
```

Inputs are typed and bounded. Possible observations include logical processor
class, available WebGL/WebGPU feature class where permitted, media decoding
capability, reduced-motion/contrast preferences, viewport count and size,
and measured long-task/frame behavior. It must not collect device identifiers,
serials, raw driver data, network addresses, or personal paths.

Profile differences may change:

- maximum simultaneous live tiles;
- preferred stream rendition;
- map layer detail and clustering threshold;
- timeline virtualization window;
- graph layout complexity;
- animation and transition behavior;
- background prefetch and polling interval;
- worker count and local rendering budget.

They may not change:

- query meaning, authorization, department scope, purpose, reason, review,
  lifecycle, correction, or evidence behavior;
- which records the user can access;
- whether denied or degraded state;
- confidence, candidate, or identity semantics;
- audit, security, or zero-retention requirements.

## Client Observability

Allowed low-cardinality measurements include:

- application and contract version;
- portal and route template, not resource ID;
- capability profile;
- result class and safe problem type;
- page-load, interaction, long-task, map-idle, query, and player-state duration
  buckets;
- retry, reconnect, stale, partial, conflict, and error counts;
- accessibility test build result in non-production evidence.

Prohibited labels and payloads include user, camera, stream, alert, timeline,
evidence, provider, department, location, search term, route parameter, token,
reason text, response body, media metadata, raw stack, and free-form exception.

Audit records remain server-side and separate from client performance
telemetry.

## Browser And Responsive Targets

The exact browser matrix is a future owner decision. The planning baseline is:

- managed current and previous major Chromium/Edge for operator workstations;
- one additional standards-based browser for compatibility evidence;
- laptop widths from 1280 pixels upward for full operational workflows;
- bounded tablet read/review layouts where interaction remains safe;
- mobile layouts for triage and read-only acknowledgement only if separately
  accepted;
- 100%, 200%, and 400% zoom/reflow evidence where applicable;
- multi-monitor workspaces as independent windows with no cross-window secret
  storage or unbounded synchronization.

Unsupported browsers must fail clearly before a high-risk workflow begins.

## Compatibility And Release Boundaries

- Canonical H-CAM contracts remain authoritative.
- The UI supports an explicitly declared producer compatibility window.
- Unknown event versions are quarantined; unknown security-relevant fields
  fail closed.
- Optional additive fields remain visible to compatibility checks even if the
  current UI does not render them.
- Security-boundary, authorization, chronology, default, pagination, failure,
  and action changes require explicit classification and review.
- Each portal can be built independently, but a release manifest binds all
  package versions, contract digests, browser targets, feature gates, and
  limitations.

## Architecture Stop Conditions

Future work must stop if it would require:

- a direct browser-to-camera, ONVIF, RTSP, database, broker, model, provider,
  evidence store, or Kubernetes connection;
- storing tokens, media, evidence, candidate data, or sensitive API responses
  in generic persistent browser storage;
- an unaccepted API or event contract;
- a hidden authorization or lifecycle fallback;
- automatic replay of an unsafe command;
- a map or graph query without explicit bounds;
- an external script, tile, media, analytics, or telemetry origin not listed
  in an accepted destination policy;
- real data, media, inference, operational action, deployment, or remote Git
  authority not present in the current exact gate.
