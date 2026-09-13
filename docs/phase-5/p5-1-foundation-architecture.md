# P5.1 Shared Application Foundation Architecture

Status: proposed; owner decisions and implementation authorization pending

Authority: `D-P5.1-PLAN-AUTH`

## Objective

P5.1 provides one governed frontend foundation for every H-CAM operator
portal. It must make portal applications independently buildable while keeping
contracts, session handling, authorization projection, accessibility,
localization, security, capability selection, and observability consistent.

This is shared infrastructure, not a single universal dashboard. Command,
Operations, Intelligence, Investigations, Evidence, Admin, and Security may
present different information densities and workflows, but they must consume
the same authoritative contracts and safety controls.

## Architectural Principles

1. **Server authority:** the browser projects server decisions; it does not
   infer roles, department scope, policy, review authority, or action success.
2. **Independent builds:** every portal has its own entry, route manifest,
   capability manifest, error boundary, and build output.
3. **One-way dependencies:** apps consume shared packages; apps do not import
   other apps, and shared packages do not import apps.
4. **Typed boundaries:** every HTTP response, event envelope, persisted local
   preference, route parameter, and cross-window message has a runtime schema.
5. **Safe minimum:** low-resource mode is functionally complete. Hardware or
   browser acceleration changes density, quality, or concurrency only.
6. **Accessible equivalence:** map, graph, timeline, data-grid, and media
   surfaces retain an equivalent list, table, transcript, or status path.
7. **Truthful state:** loading, empty, partial, stale, degraded, denied,
   conflict, failure, recovery, correction, and success are distinct states.
8. **No hidden integration:** all network access passes through an approved
   same-origin client and an operation registry; no component calls an
   arbitrary URL.
9. **No silent persistence:** server workspaces are authoritative. Local state
   is allowlisted, harmless, versioned, bounded, and expiring.
10. **Parity-first adoption:** existing final-ui workflows are migrated through
    evidence, not replaced by a generic redesign.

## Proposed Workspace Topology

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
  navigation/
  design-tokens/
  ui/
  contracts/
  api-client/
  auth-session/
  query-policy/
  event-invalidation/
  capabilities/
  i18n/
  gis-contracts/
  playback-contracts/
  observability/
  test-fixtures/
  test-support/
tooling/
  workspace-policy/
  contract-generation/
  evidence/
```

These paths are a plan, not authorization to create them. The future start
package must freeze exact paths and package names.

### Dependency Rules

- Portal apps may import only published workspace package entry points.
- Shared packages form a directed acyclic graph with explicit public exports.
- `contracts` contains generated transport types and schemas, not domain UI.
- `api-client` depends on contracts and safe error mapping; it does not depend
  on React.
- `auth-session`, `query-policy`, `event-invalidation`, and `capabilities`
  expose framework-neutral cores with React adapters at explicit entry points.
- `ui` may depend on tokens, i18n interfaces, and accessibility primitives, but
  never on a portal or concrete backend endpoint.
- `gis-contracts` and `playback-contracts` define adapter interfaces. MapLibre,
  HLS, and WHEP packages are introduced only in their authorized subphases.
- Browser bundles must not include source-adoption reference files, test
  fixtures, development diagnostics, schemas marked server-only, or secrets.

## Portal Build Contract

Each portal build must declare:

- portal ID, version, route base, and compatibility range;
- shared package versions and contract manifest digest;
- required and optional server capabilities;
- feature modules and route manifests;
- allowed same-origin operation IDs and event types;
- localization catalogues and completeness status;
- CSP and static asset requirements;
- profile budgets for JavaScript, CSS, route chunks, requests, and workers;
- generated build provenance and source-adoption records;
- unsupported capabilities and visible fallback states.

A portal cannot become available because its navigation entry exists. The BFF
session bootstrap must return both portal and route capabilities for the active
operator, department, purpose, and environment.

## Shared Application Shell

The shell owns only cross-portal behavior:

- NETRA SENTINEL identity, portal switcher, primary navigation, breadcrumbs,
  command search entry, operator/session menu, and global state banners;
- route-level error, denied, incompatible, maintenance, degraded, and session
  expiry boundaries;
- locale, operational timezone, density, theme, reduced-motion, and approved
  window preference controls;
- focus restoration, skip links, title/announcement updates, and keyboard
  navigation;
- feature and capability projection from the current server session;
- safe cross-portal links carrying opaque resource IDs and allowlisted query
  state only;
- logout and department-context change, including complete memory/cache/event
  teardown before the new context becomes usable.

The shell does not own portal resource data, camera playback, map rendering,
alert review, investigation decisions, or administrative mutations.

## Navigation And Routing

The proposed routing model uses static typed route manifests and Data Mode
boundaries. Route loaders are limited to shell bootstrap, compatibility,
session, and access preflight. Resource collections and detail records use the
shared query layer so routing and server state do not become competing caches.

Every route declares:

- route ID and owning portal;
- URL parameters and allowlisted query fields;
- required server capability and department scope;
- required resource-operation IDs;
- breadcrumb and localized title keys;
- safe loading, empty, denied, stale, degraded, failure, and recovery states;
- focus target on entry and restoration target on exit;
- whether multi-window use is allowed;
- data exposure classification and local-persistence policy.

Unknown, malformed, oversized, unauthorized, or stale route state fails to a
safe route boundary. The URL never carries names, plates, faces, watchlist
terms, evidence references, stream locators, tokens, secrets, or free-form
operational reason text.

## Session, Authorization, And Department Context

The proposed BFF boundary uses a same-origin server-managed session. A session
bootstrap projection contains only:

- opaque operator and session references;
- current department and authorized department choices;
- portal, route, action, field, and feature capabilities;
- policy revision, compatibility range, and server time;
- idle, absolute, and reauthentication state;
- reason, ETag, and idempotency requirements by operation;
- safe locale, timezone, and workspace defaults.

Capabilities are a UI projection, not authorization evidence. Every request is
authorized again on the server. A client must deny an action when capability
state is missing, stale, malformed, incompatible, or changed. Department or
role changes cancel requests, disconnect event lanes, destroy caches, clear
sensitive in-memory views, and restart bootstrap before navigation resumes.

## Typed API Boundary

The future contract pipeline is:

```text
accepted OpenAPI 3.1 schema
  -> canonical schema digest and compatibility classification
  -> generated TypeScript operation/path types
  -> strict standalone runtime validators
  -> typed same-origin fetch transport
  -> minimized RFC 9457 problem mapper
  -> operation-specific policy registry
  -> portal query or command adapter
```

Every operation registry entry declares method, same-origin path template,
request and response schema, department behavior, reason/ETag/idempotency
requirements, timeout, retry class, cancellation, freshness, cache lifetime,
event invalidators, redaction, telemetry fields, and compatibility range.

Unknown response fields follow the accepted producer compatibility policy, but
known security, authority, and state discriminators are strict. A validation
failure is a typed incompatible-response state and never falls through to a
partial JavaScript cast.

## Server State And Event Invalidation

The proposed server-state layer uses one query policy registry. It distinguishes:

- immutable reference data;
- slowly changing configuration;
- operational summaries;
- paginated work queues;
- freshness-critical detail;
- commands requiring ETags and idempotency;
- non-cacheable session, playback, evidence, or security material.

Retries are default-off for commands and for authorization, validation,
conflict, policy, and incompatibility failures. Read retries are bounded and
operation-specific. Stale data is visible and retains its observation time,
source window, completeness, and revalidation state.

The event adapter accepts only typed, versioned, department-scoped envelopes.
Events may invalidate query keys or update an explicitly non-authoritative
projection. Sequence gaps, reconnects, duplicates, reordering, unknown event
versions, policy changes, or department changes force bounded HTTP
revalidation. Polling remains a complete fallback.

## Client State And Persistence

State classes are explicit:

| State class | Authority | Default lifetime | Storage rule |
| --- | --- | --- | --- |
| Server resources | HTTP | Query policy | Memory only unless a contract explicitly permits otherwise |
| Session/capabilities | BFF bootstrap | Session | Memory only |
| Route state | URL contract | Navigation | Allowlisted opaque IDs and bounded enums only |
| Server workspace | Server | Policy-defined | Persisted by server, not browser |
| Display preference | Operator | Bounded | Versioned allowlist, TTL, no sensitive context |
| Draft command | Operator | View | Memory only; clear on context change |
| Event projection | Event lane | Until revalidation | Memory only and labeled non-authoritative |
| Diagnostics | Client contract | Bounded aggregate | Sanitized, low-cardinality, no payload retention |

Browser caches, service workers, IndexedDB, persistent query caches, and
cross-tab resource synchronization are not in the recommended P5.1 baseline.
Multi-window operation uses independent server sessions and resource fetches;
only harmless display preferences may be shared.

## Design System And Accessibility

The design system comprises semantic tokens, native-first primitives,
composite components, operator layouts, and state patterns. It preserves the
existing visual identity while replacing prototype-specific styling with
governed contracts.

Mandatory primitive behavior includes:

- stable dimensions for toolbar, icon, status, counter, tile, grid, player,
  and map controls;
- visible focus, logical focus order, skip links, and focus restoration;
- keyboard-complete menus, tabs, dialogs, comboboxes, trees, grids, and
  disclosure patterns;
- minimum target sizing, zoom/reflow, text resize, high contrast, forced
  colors, reduced motion, and non-color status indicators;
- deterministic loading, empty, stale, partial, degraded, denied, conflict,
  failure, correction, recovery, and success presentations;
- accessible names for icon controls and localized descriptions for unfamiliar
  actions;
- equivalent non-visual/list workflows for spatial, graph, timeline, and
  media-oriented information.

Automated accessibility checks are necessary but insufficient. Manual
keyboard, screen-reader, zoom, contrast, target-size, and motion evidence is a
future acceptance requirement.

## Localization

English, Gujarati, and Hindi are first-class catalogues from the first shared
component. All user-facing strings, status reasons, relative times, dates,
numbers, counts, units, and validation messages use stable message IDs and ICU
formatting.

The platform stores canonical timestamps and displays the operator locale plus
the selected operational timezone. Event chronology never depends on a
localized string. Missing catalogues fail visibly in development/evidence and
fall back to the approved base locale in a production projection without
showing internal IDs.

## Responsive And Multi-Monitor Model

Responsive behavior is based on container needs and operator tasks, not device
names. The same portal supports:

- compact single-column use with explicit explorer/detail modes;
- laptop density with a stable navigation rail and bounded side panels;
- enhanced workstation layouts with controlled split views;
- control-room windows with independently routable list, map, detail, and
  monitoring views.

No viewport may hide authorization, freshness, degradation, correction, or
mandatory-review state. Opening a second window does not duplicate authority or
transfer memory state implicitly. Workspaces saved across devices are
server-side records with versions and optimistic concurrency.

## Dynamic Capability Profiles

The effective profile is an intersection:

```text
safe low-resource defaults
AND server policy ceiling
AND operator/department capabilities
AND build-supported features
AND coarse browser capabilities
AND session-local measured health
```

Profiles:

| Profile | Required behavior | Optional enhancement |
| --- | --- | --- |
| Low resource | Full lists, filters, review, details, accessible GIS alternative, one bounded workspace | Reduced motion, lower density, fewer concurrent visual surfaces |
| Enhanced workstation | All low-resource behavior | Map acceleration, higher list density, bounded parallel panels |
| Control room | All low-resource behavior | Multiple independent windows, higher information density, supervisor layouts |
| Future server-backed | Same client authority rules | Server-prepared aggregates, tiles, media variants, or rendered products when separately authorized |

Raw hardware inventory, persistent fingerprinting, vendor/GPU identity, and
automatic policy escalation are prohibited. A profile downgrade must preserve
the operator's task, announce the reason, and release optional resources.

## GIS Preservation

P5.1 owns only renderer-neutral GIS contracts, shell integration, capability
admission, state patterns, and test fixtures. It does not implement the map.
The accepted Gujarat GIS remains the canonical operator experience.

MapLibre admission must detect unsupported WebGL2 and return a typed unavailable
state while the full explorer, filters, result list, selected-feature detail,
counts, freshness, and commands remain available. Optional 3D remains outside
P5.1 and cannot replace authoritative 2D or list behavior.

## Observability

The client emits an internal typed signal model with bounded dimensions:

- portal and route class;
- operation ID and outcome class;
- UI state class;
- profile class and degradation reason;
- contract/version compatibility outcome;
- event lane state and invalidation outcome;
- accessibility or focus invariant failure class;
- duration and size buckets.

Operator IDs, department names, camera/resource IDs, locators, search terms,
free text, response payloads, coordinates, URLs, tokens, evidence references,
and raw errors are prohibited telemetry fields. An OpenTelemetry-compatible
browser adapter is default-off until separately configured and accepted.

## Compatibility Strategy

Compatibility is checked at build and session bootstrap:

- every portal publishes supported server contract and event ranges;
- the server publishes current schema, operation, capability, and policy
  revisions;
- additive unknown fields are ignored only where the contract permits them;
- unknown enums affecting authority or state fail closed;
- unsupported required operations disable the route, not just its submit
  button;
- deprecated operations retain an explicit removal date and usage evidence;
- a compatibility bundle binds source, dependencies, generated clients,
  schemas, browsers, fixtures, and known limitations.

## Source Adoption Boundary

The pinned `hcam-1-0/final-ui` commit remains the approved visual and
interaction baseline. A future authorized adoption must:

1. import or copy only through a hash-bound, attributed source record;
2. exclude dependency directories, generated output, credentials, and runtime
   configuration;
3. preserve reference source outside production bundles;
4. extract tokens, shell behavior, and workflows into target packages;
5. port Command, Live, and GIS as separately accepted slices;
6. compare visual, interaction, responsive, accessibility, resource, and
   security parity;
7. retain the reference until the relevant parity gate is accepted.

P5.1 planning does not authorize that adoption.

## P5.1 Exit Conditions

P5.1 can earn its 12 product points only when a future accepted start package
proves all of the following together:

- independently buildable portals and a cycle-free one-way package graph;
- typed, runtime-validated API, problem, event, route, preference, session, and
  capability boundaries;
- server-authoritative authorization, department, concurrency, and mutation
  outcomes;
- complete low-resource behavior plus deterministic enhancement and downgrade;
- shared accessible primitives and English/Gujarati/Hindi catalogues;
- no protected data in URLs, persistent storage, logs, errors, or telemetry;
- source-adoption provenance and Gujarat GIS no-downgrade preservation;
- exact dependency, license, SBOM, vulnerability, provenance, bundle, browser,
  accessibility, security, and reproducible-build evidence;
- complete focused and repository regression evidence;
- exact owner acceptance of the sealed evidence package.

## Current Boundary

This architecture is non-effective planning. It authorizes no path creation,
source import, dependency change, product/test implementation, build, runtime,
network access, data/media/model use, container, Kubernetes, deployment, P5.2,
or remote Git operation.
