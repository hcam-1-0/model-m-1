# P5.1 Shared Application Foundation Implementation Plan

Status: non-effective bounded plan; owner decisions and start authorization
pending

Authority: `D-P5.1-PLAN-AUTH`

## Objective

Implement the shared application foundation required by all independently
buildable H-CAM operator portals while preserving the accepted final-ui visual
baseline and Gujarat GIS no-downgrade contract. P5.1 does not implement
Command, GIS, live monitoring, intelligence, investigation, evidence, admin,
or security feature workflows beyond foundation contracts and generated
integration fixtures.

## Progress Accounting

P5.1 has 12 frozen Phase 5 product points. Planning, research, owner decision
selection, start-package preparation, and authorization earn no product points.
Each implementation workstream below earns its 1.5 points only when every exit
condition for that workstream passes and its evidence is sealed. No fractional
credit is reported inside a workstream.

| Workstream | P5.1 points | P5.1 cumulative | Phase 5 cumulative |
| --- | ---: | ---: | ---: |
| P5.1-W1 Workspace and build policy | 1.5 | 12.5000% | 9.5000% |
| P5.1-W2 Shell, navigation, and routing | 1.5 | 25.0000% | 11.0000% |
| P5.1-W3 Design system and accessibility | 1.5 | 37.5000% | 12.5000% |
| P5.1-W4 Typed contracts, API, and errors | 1.5 | 50.0000% | 14.0000% |
| P5.1-W5 Session, authorization, and context | 1.5 | 62.5000% | 15.5000% |
| P5.1-W6 Server state, concurrency, and events | 1.5 | 75.0000% | 17.0000% |
| P5.1-W7 Localization, profiles, and windows | 1.5 | 87.5000% | 18.5000% |
| P5.1-W8 Observability, adoption, validation, and acceptance | 1.5 | 100.0000% | 20.0000% |

Any change to these weights requires an explicit rebaseline before a new exact
percentage is reported.

## Preconditions

1. Owner selects `D-P5.1-001` through `D-P5.1-012`.
2. Selections are reconciled into a new immutable planning package.
3. Owner accepts the exact reconciled package and digest.
4. A non-effective start package freezes the exact changed paths, dependency
   versions and hashes, licenses, scripts, browser/runtime baseline, generated
   fixture manifest, commands, resource bounds, compatibility transitions,
   evidence paths, remediation cycles, and stop conditions.
5. Owner authorizes that exact start package.
6. Dependency and source acquisition, if any, is separately within the exact
   start scope and passes provenance and vulnerability gates before use.

The current planning authority satisfies none of the implementation gates.

## Proposed Start Scope

A future start package may authorize only the shared foundation, generated-only
fixtures, and test infrastructure. It should explicitly exclude map rendering,
media playback, real provider connections, cameras, data, models, operations,
deployment, and remote Git.

The start package should bind:

- one implementation branch and base commit;
- exact workspace roots and independently buildable app placeholders;
- exact package graph and forbidden-import rules;
- exact Node/package-manager/runtime and dependency versions;
- registry, integrity, license, provenance, vulnerability, and install-script
  evidence before dependency use;
- exact accepted OpenAPI/event/session/capability inputs;
- generated non-issuable fixtures and prohibited-data scan rules;
- exact test/build/lint/typecheck/evidence commands and time/resource bounds;
- allowed historical test transitions without changing accepted artifacts;
- remediation cycle count, fail-closed criteria, and local commit policy;
- separate technical and owner acceptance records.

## P5.1-W1 Workspace And Build Policy

Planned outputs:

- workspace root, central dependency catalogue, one lockfile, and toolchain
  constraints;
- independently buildable portal entry packages with no product screens;
- shared package public-export boundaries and one-way graph checks;
- strict TypeScript base configurations for browser, library, test, and tooling
  targets;
- reproducible task definitions for lint, typecheck, test, build, evidence, and
  clean-source verification;
- bundle and source-map exclusion policies;
- dependency, license, SBOM, vulnerability, provenance, and build manifest
  format.

Exit conditions:

- each portal placeholder builds independently from a clean authorized source;
- no portal-to-portal import or package cycle exists;
- internal imports use exact public workspace entry points;
- production bundles contain no tests, fixtures, reference source, source maps,
  secrets, locators, or server-only schemas;
- exact toolchain and dependency evidence is sealed.

## P5.1-W2 Shell, Navigation, And Routing

Planned outputs:

- shared application shell, portal registry, navigation model, breadcrumbs,
  command-search entry, session menu, and global banners;
- typed route manifests, route access preflight, lazy boundaries, route errors,
  pending state, and deep-link handling;
- skip links, title/live announcements, focus entry/restoration, mobile drawer,
  compact navigation, and multi-window route behavior;
- generated route fixtures for every P5.0 state and capability condition.

Exit conditions:

- all portal routes render generated loading, empty, partial, stale, degraded,
  denied, conflict, failure, recovery, correction, and success states;
- unknown or unauthorized routes fail closed;
- navigation never grants capability;
- protected fields never enter URLs or browser history;
- keyboard, focus, zoom, reflow, reduced-motion, and forced-colors tests pass.

## P5.1-W3 Design System And Accessibility

Planned outputs:

- semantic color, typography, spacing, elevation, density, motion, and status
  tokens preserving the approved identity;
- native-first buttons, links, inputs, selection controls, disclosures,
  tooltips, dialogs, menus, tabs, comboboxes, tables, trees, and notification
  regions;
- full-page and panel state patterns;
- stable operator layouts and list/table alternatives for complex surfaces;
- component state catalogue and accessibility acceptance matrix.

Exit conditions:

- core components pass semantics, accessible-name, keyboard, focus, disabled,
  readonly, validation, and state tests;
- no color-only status or motion-only meaning exists;
- text fits across supported locale/zoom/density combinations;
- automated accessibility checks pass and manual evidence obligations are
  explicitly open, not falsely claimed complete;
- visual behavior remains consistent with the pinned final-ui baseline.

## P5.1-W4 Typed Contracts, API, And Errors

Planned outputs:

- canonical OpenAPI input manifest and generated TypeScript projections;
- strict runtime validators for every used request, response, route, event,
  preference, and problem shape;
- same-origin fetch transport with operation IDs, bounds, timeout,
  cancellation, and no arbitrary destination API;
- minimized RFC 9457 mapper and typed incompatibility/error taxonomy;
- contract compatibility and unknown-field policy.

Exit conditions:

- all network calls are statically reachable only through the typed transport;
- malformed, oversized, unknown-version, hostile, partial, and incompatible
  generated responses fail to the correct visible state;
- raw errors and prohibited fields are discarded;
- generated types and runtime schemas bind the same accepted contract digest;
- producer gaps remain disabled instead of being mocked as product capability.

## P5.1-W5 Session, Authorization, And Context

Planned outputs:

- same-origin session bootstrap and capability projection;
- synchronizer CSRF contract, cookie and header expectations, Origin/Fetch
  Metadata error states, reauthentication, idle/absolute expiry, and logout;
- department selector and complete context-transition state machine;
- capability resolver for portal, route, action, field, feature, reason, ETag,
  and idempotency requirements;
- generated cross-scope, stale-capability, expiry, and misuse scenarios.

Exit conditions:

- client capabilities never substitute for server authorization;
- missing, stale, malformed, or incompatible capability state denies action;
- department/role/session changes cancel requests, close events, clear memory,
  and block rendering until bootstrap completes;
- credentials and session identifiers never enter JavaScript-readable
  persistence, URLs, logs, source maps, or telemetry;
- CSRF, clickjacking, XSS, cross-scope, and reauthentication tests pass.

## P5.1-W6 Server State, Concurrency, And Events

Planned outputs:

- operation policy registry for freshness, cache, retry, polling,
  cancellation, redaction, and persistence;
- typed query keys scoped by contract, department, and resource;
- mutation interface enforcing reason, ETag, idempotency, confirmation, and
  accepted server outcome;
- typed event invalidation adapter and generated polling/event simulator;
- gap, duplicate, reorder, reconnect, unknown-version, and downgrade behavior.

Exit conditions:

- commands never retry automatically;
- HTTP is the only authoritative resource and mutation state;
- stale, partial, offline, degraded, and revalidating state remains visible;
- event failure cannot enable a control or hide a correction;
- query cancellation, teardown, concurrency conflict, and bounded recovery
  evidence passes.

## P5.1-W7 Localization, Profiles, And Windows

Planned outputs:

- English, Gujarati, and Hindi catalogue tooling and generated complete
  catalogues for foundation messages;
- ICU formatting, operational timezone, canonical timestamp, and locale
  fallback contracts;
- responsive/container layout contracts and independent window behavior;
- deterministic low-resource, enhanced-workstation, control-room, and future
  server-backed profile resolver;
- coarse capability checks, session-health downgrade, and safe fallback;
- harmless versioned display preference schema plus server-workspace contract.

Exit conditions:

- all foundation UI renders in all three catalogues and pseudo-locale;
- business logic never parses localized output;
- low-resource mode retains every foundation function and accessible path;
- enhancement cannot expand authorization, data, or persistence;
- unsupported WebGL returns the complete GIS alternative contract;
- profile and multi-window behavior retain no sensitive cross-window data.

## P5.1-W8 Observability, Adoption, Validation, And Acceptance

Planned outputs:

- low-cardinality typed client signal registry and default-off
  OpenTelemetry-compatible adapter;
- final-ui source-adoption intake contract, provenance record, build exclusion,
  and parity evidence framework without feature migration;
- generated service mock and deterministic state/error/security fixtures;
- tiered unit, component, story, contract, browser, visual, accessibility,
  localization, security, compatibility, bundle, and clean-source suites;
- exact P5.1 evidence package, limitation register, rollback/compatibility
  bundle, readiness verifier, and owner acceptance proposal.

Exit conditions:

- telemetry contains no identities, resource IDs, URLs, coordinates, free text,
  payloads, errors, tokens, or locators;
- reference source cannot enter portal build output;
- Gujarat GIS parity requirements remain byte-exact and explicitly carried to
  P5.2;
- quick laptop and complete evidence profiles pass on declared environments;
- source, dependencies, contracts, generated output, tests, and evidence are
  reproducible and hash-bound;
- owner exactly accepts the evidence package and implementation commit.

## Test Matrix

| Layer | Planned proof |
| --- | --- |
| Workspace | independent builds, graph, exports, cycles, exact versions, clean source |
| Contract | schema/type parity, hostile payloads, compatibility, bounds, error minimization |
| Unit | capability, query policy, route, locale, profile, telemetry, state machines |
| Component | semantics, keyboard, focus, validation, all UI states, responsive containers |
| Story | complete component/state/locale/profile catalogue and automated accessibility |
| Browser | session, CSRF, routing, context teardown, events, windows, persistence absence |
| Visual | pinned baseline, density, desktop/tablet/mobile, zoom, forced colors, long text |
| Security | XSS, URL/storage/log/telemetry fields, CSP, scope, retries, source-map/bundle scans |
| Supply chain | integrity, scripts, license, SBOM, vulnerabilities, provenance, reproducibility |
| Manual | keyboard, screen reader, zoom, contrast, targets, motion, operator workflow review |

## Resource And Build Profiles

The future start package should define two local validation modes:

- **Quick:** changed packages, unit/contract/component checks, one browser,
  generated C1 state, and strict low-resource bounds suitable for the current
  laptop.
- **Evidence:** all portals and packages, all generated states, three locales,
  managed browser matrix, C1/C10/C50 state volume, screenshots, bundle checks,
  complete security/supply-chain evidence, and declared enhanced hardware when
  separately authorized.

Both modes must evaluate identical contracts and safety rules. The quick mode
may reduce test breadth per iteration, but it cannot define weaker product
behavior or become final acceptance evidence by itself.

## Compatibility And Rollback

- each portal binds the shared foundation and accepted producer contract range;
- the previous accepted P5.0-only backend remains compatible because P5.1 adds
  no backend route or migration;
- a portal that lacks a required operation shows an unavailable route state;
- the compatibility bundle preserves the last accepted source, lockfile,
  generated clients, schemas, browser matrix, evidence, and rollback commands;
- rollback never restores stale credentials, local caches, or event state;
- final-ui reference retention continues until each adopted surface passes its
  parity acceptance.

## Stop Conditions

Stop and require a new exact authorization if implementation would:

- touch a path, dependency, contract, command, environment, or remediation
  cycle outside the accepted start package;
- import source or download/install a dependency before its exact gate;
- alter an accepted P5.0, Phase 4, or GIS parity artifact;
- require a backend route, migration, operational endpoint, real data, media,
  camera, provider, model, container, Kubernetes, deployment, or remote Git;
- weaken session, CSRF, department, role, reason, ETag, idempotency, review,
  correction, evidence, accessibility, localization, or no-persistence rules;
- claim build, browser, security, accessibility, parity, performance, or
  operational readiness without accepted evidence.

## Current Progress

- P5.1 planning authorization: **complete**.
- Read-only repository analysis: **complete**.
- Official primary-source research: **complete**.
- Architecture, threat model, decisions, and bounded implementation plan:
  **complete as non-effective planning**.
- Owner decision selection: **pending**.
- Reconciled planning acceptance: **pending**.
- Start package and implementation authorization: **pending**.
- P5.1 product: **0/12 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **8/100 (8.0000%)**, change **+0.0000 percentage points**.

No product or test code, dependency, lockfile, build, runtime, source import,
network, data, media, model, container, deployment, P5.2, or remote Git action
is authorized by this document.
