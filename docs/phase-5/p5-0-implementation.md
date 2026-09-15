# P5.0 Generated Operator-Contract Implementation

Status date: 2026-09-06

Authority: `D-P5.0-START`

Accepted start package: `P5.0-START-R0`

Accepted package SHA-256:
`66F40E71B2E96F2C61C267EF5A14CD709692A0C389AC23560651BC2B9C38B7F8`

## Purpose

P5.0 converts the accepted Phase 5 planning baseline into a bounded,
generated-only contract foundation for future operator applications. It
defines what a command, operations, intelligence, investigation, evidence,
administration, or security surface may display and request. It does not
implement a browser application, API route, GIS renderer, media player,
provider connection, database migration, or operational action.

The package is designed to stop future UI work from inventing authority,
discarding safety state, or downgrading the accepted Gujarat GIS experience.
Server decisions remain authoritative. A client resource profile may reduce
presentation capability but can never expand server authority.

## Implemented Packages

### W1: Canonical UI Contracts And Bounds

`app/hcam/operator_application/contracts.py` defines strict, frozen Pydantic
contracts for producer bindings, server capability decisions and ceilings,
operator actions, views, sanitized problems, and generated contract cases.
Unknown fields are rejected. Identifiers, versions, timestamps, counts,
freshness windows, actions, roles, locales, and states are bounded.

`app/hcam/operator_application/bounds.py` centralizes count and size ceilings.
These ceilings are contract controls, not runtime capacity claims.

### W2: Information Architecture And Journeys

`catalogue.py`, `navigation.py`, `journeys.py`, and `capabilities.py` define:

- ten logical operator views across seven role-oriented portals;
- six bounded local route contracts with allowlisted non-sensitive URL state;
- generated camera-to-live, alert-review, and correction/reconstruction state
  machines;
- loading, empty, ready, partial, stale, degraded, denied, conflict, failure,
  recovery, and correction semantics;
- server-confirmed transitions for all non-navigation decisions;
- low-resource, enhanced, and control-room presentation profiles.

The route contracts prohibit credentials, locators, raw media, or sensitive
records in URL state. The journey contracts are non-operational state models;
they do not issue commands to existing services.

### W3: Design, Localization, And Accessibility

`design_tokens.py` provides bounded semantic design-token contracts, WCAG
relative-luminance contrast calculation, a maximum eight-pixel radius,
zero letter spacing, minimum control sizing, and reduced-motion support.

`accessibility.py` requires all nine accepted accessibility categories and
equivalent list, table, transcript, or summary paths for map, graph, timeline,
data-grid, and media views. Alternatives preserve selection, order, freshness,
corrections, and available actions. English, Gujarati, and Hindi locale
coverage is mandatory in every view contract; canonical audit values remain
language-neutral server values.

These contracts target WCAG 2.2 AA and APG-informed interaction. P5.0 does not
claim conformance because no browser UI or manual assistive-technology testing
is authorized or present.

### W4: Gujarat GIS Parity

`gis_contracts.py` preserves the accepted `GisWorkspace` as the canonical GIS
operator experience using renderer-neutral contracts. It defines bounded
Point, LineString, Polygon, and MultiPolygon shapes, viewport queries, layers,
selection state, freshness, uncertainty, corrections, and parity cases.

The parity matrix has twelve mandatory categories: composition, filter, layer,
selection, focus, responsive behavior, safety, localization, accessibility,
degradation, performance, and preview gating. No category may be downgraded.
MapLibre 2D is a future target only. Authoritative 2D and accessible-list paths
remain mandatory; optional 3D is supplementary, default off, and non-effective.
No renderer, tile, style, glyph, geocoder, routing, or provider access exists.

### W5: Browser Security Boundary

`security.py` defines a same-origin BFF boundary and statically closes direct
browser access to cameras, databases, brokers, model runtimes, and providers.
Persistent sensitive browser storage is prohibited. Recursive payload checks
reject credential, secret, locator, media, and registration-like fields.

Safe problems expose a bounded reason, localized title key, recovery action,
optional retry delay, and sanitized trace reference. Raw exception detail is
not part of the contract.

### W6: Generated Validation And Evidence

`generated.py` deterministically materializes:

- 720 operator cases from ten views, eight states, three resource profiles,
  and three locales;
- 96 GIS parity cases from twelve requirements, four geometry types, and two
  representative resource profiles.

`validation.py` validates unique identifiers, generated-only markers,
prohibited fields, minimum case counts, and canonical SHA-256 projections.
`tools/phase50_readiness.py` checks package hashes, exact source paths,
catalogue coverage, GIS parity, accessibility, capability authority, prohibited
imports, and closed gates. `tools/phase50_evidence.py` seals bounded evidence
only after the technical implementation commit and validation complete.

## Machine-Readable Catalogues

| Catalogue | Contract role |
| --- | --- |
| `operator-ui-contract-catalogue.v1.json` | Canonical portal views, states, actions, and producer bindings |
| `operator-ui-route-journeys.v1.json` | Safe routes and generated journey state machines |
| `operator-ui-capability-matrix.v1.json` | Server-authoritative resource-profile ceilings |
| `operator-ui-producer-coverage.v1.json` | Producer operation, version, freshness, scope, and gap mapping |
| `operator-ui-accessibility.v1.json` | Nine accessibility categories and five complex-view alternatives |
| `operator-ui-gis-parity.v1.json` | Twelve-category no-downgrade Gujarat GIS parity matrix |

## Architectural Guarantees

- All contract models are strict, frozen, and reject unknown fields.
- All data and identifiers are generated and explicitly non-operational.
- Producer references include operation, schema version, freshness, department
  scope, authority, and implementation-gap classification.
- Capability checks are fail closed and remain server authoritative.
- Resource profiles affect rendering eligibility only, never access policy.
- GIS 2D and accessible list semantics are authoritative in every profile.
- Browser contracts do not expose camera, media, provider, database, broker,
  model-runtime, credential, or secret access.
- Errors do not expose raw detail.
- Evidence and acceptance are separate; technical completion cannot award the
  final P5.0 point.

## Deliberate Non-Implementation

P5.0 contains no React, TypeScript, Vite, package-manager, browser, map,
playback, WebSocket, polling, backend, database, worker, container, Kubernetes,
model, inference, media, provider, or deployment runtime. It does not import
source from `hcam-1-0/final-ui`. That repository remains an audited design and
workflow baseline; future source decisions require a separate authorization.

P5.1 remains closed. This package is ready only for separate owner review of
the exact P5.0 evidence package after all validations are sealed.
