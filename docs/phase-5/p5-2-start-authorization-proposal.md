# P5.2 Start Authorization Proposal

Status: non-effective; exact owner start authorization pending

Package: `P5.2-START-R0`

Package SHA-256:
`24F89F18D52404A4FF1AA4A8A52A9DA8E4D4619B7721107B1A82EEF389805B67`

Bound-input digest:
`3E070D61CC90E969E1A5FA91A9564D1FE151E88293904051B9B2763C5E27A74E`

Planning-preparation component digest:
`7982F382BD06B642524F79A46687547714DF6EDC026E2CC8D5FB92FE633B8A6F`

Prepared: 2026-09-07

Expires if not accepted: 2026-10-07

## Purpose

This package is the bounded implementation gate for P5.2 Command And
Situational Awareness. It converts the accepted R1 architecture into an exact
local generated-only delivery scope. It does not activate that scope.

The product hierarchy is immutable inside this package:

1. Command Center is the primary dashboard and default landing surface.
2. GIS Center is a connected specialist dashboard for deeper spatial work.
3. Both consume one shared GIS domain and one server-authoritative truth model.
4. MapLibre is the stable 2D core; deck.gl is optional and capability-gated.
5. An authoritative list/table/detail path survives any renderer failure.
6. All fourteen missing producer contracts remain blocked or generated-only.

The older `hcam-1-0/final-ui` remains an attributed behavioral and visual
reference. This package does not authorize importing, copying or merging its
source.

## Proposed Effect

Exact owner acceptance would authorize only:

- recording the exact `D-P5.2-START` statement;
- one local checkpoint for the accepted planning/start records before product
  work, with no push;
- guarded resolution and installation of four allowlisted GIS dependencies;
- implementation of the eight frozen P5.2 workstreams in 30 named existing
  files, 99 named additive implementation files and 13 named phase/evidence
  records;
- local generated-only Command/GIS execution over loopback and local assets;
- bounded build, browser, visual, accessibility, security, replay and
  C1/C10/C50 validation;
- up to twelve in-scope remediation, validation and reseal cycles;
- local checkpoint commits without push; and
- preparation of one non-effective exact P5.2 exit-acceptance proposal.

Acceptance would not authorize backend producer implementation, real systems
or data, external provider access, operational actions, deployment or remote
Git.

## Frozen Workstreams

| Workstream | Points | Delivery boundary |
| --- | ---: | --- |
| `P5.2-W1` | 1.5 | Typed Command/GIS projections, layer/data-lane contracts, strict validation and generated fixtures |
| `P5.2-W2` | 1.5 | Primary Command overview with truthful source, freshness, completeness, degradation and unknown states |
| `P5.2-W3` | 2.0 | Shared GIS domain, MapLibre core adapter, optional deck.gl adapter and deterministic fallback |
| `P5.2-W4` | 2.0 | Embedded Command GIS, connected GIS Center, context revalidation and Gujarat GIS parity |
| `P5.2-W5` | 1.5 | Ten Command page families, coverage/health/workload/time views and authoritative drill-down |
| `P5.2-W6` | 1.5 | Accessibility, localization, responsive layout and independent multi-monitor continuity |
| `P5.2-W7` | 1.0 | Security, disabled provider controls, dynamic profiles, safe telemetry and resource bounds |
| `P5.2-W8` | 1.0 | Complete validation, sealed evidence, limitations and exact owner exit acceptance |

No partial product credit is awarded inside a workstream. The final 1.0 point
for W8 remains withheld until exact owner exit acceptance.

## Application Scope

### Command Center

The existing `frontend/apps/command-center` shell becomes the primary
application with ten page families:

- Situation Overview;
- Live Situation;
- Alerts And Mandatory Review Overview;
- Investigation Workload;
- Camera Network;
- Coverage And Blind Spots;
- Operational Workload;
- Platform Health And Degradation;
- Command Briefing; and
- Command Workspaces.

The default page combines a persistent source-status strip, situation summary,
embedded GIS, priority workload, coverage/health, bounded chronology and
authoritative drill-downs. P5.2 remains read-only.

### GIS Center

The additive `frontend/apps/gis-center` application provides nine specialist
page families:

- GIS Overview;
- Operational Map;
- Camera Network Geography;
- Coverage And Blind-Spot Analysis;
- Alerts And Investigations Geography;
- Movement And Time;
- Layer Catalogue;
- Spatial Workspaces; and
- GIS Data And Renderer Health.

Navigation from Command to GIS carries only an opaque bounded context. GIS
Center must independently revalidate the session, department, role,
capability, snapshot revision and operation access.

### Shared Domain

Additive `command-domain`, `gis-domain` and `gis-renderers` packages isolate
projection rules, layer/selection/time state, provider policy and renderer
adapters. Portal code may compose these packages but may not redefine truth,
authorization or fallback semantics. No portal-to-portal source import or
runtime federation is introduced.

## Dependency Gate

Dependency work is prohibited until exact start acceptance. If accepted, only
these new direct runtime packages may be resolved:

- `maplibre-gl` as the required stable 2D renderer;
- `@deck.gl/core`;
- `@deck.gl/layers`; and
- `@deck.gl/mapbox` for the optional MapLibre overlay integration.

All deck.gl packages must resolve to one exact version and must be compatible
with the selected exact MapLibre version. Resolution uses only the official
HTTPS npm registry, no credentials and no alternate package source. Exact
direct/transitive versions, integrity, peer/engine compatibility, license,
advisory, provenance, bundle and SBOM evidence must pass before installation.
Installation must use the frozen lockfile, ignore lifecycle scripts and skip
browser downloads.

The accepted local toolchain remains exact installed Node `24.18.0` and pnpm
`11.21.0` through the existing hash-bound direct invocation. No NVM switch,
global activation, package-manager update or browser download is authorized.

Leaflet, OpenLayers, Cesium, Turf, custom WebGL, react-map-gl, public provider
clients, geocoders, routing clients, media transports, direct backend clients
and telemetry products are excluded.

## Adaptive Rendering

| Profile | Renderer ceiling | Bounded behavior | Mandatory fallback |
| --- | --- | --- | --- |
| Safe low | MapLibre-only or no map | Up to 2,000 visible features, six active layers, no animation | Authoritative list/table |
| Enhanced workstation | MapLibre plus optional deck.gl overlaid | Up to 25,000 visible features and twelve active layers | MapLibre-only, then list/table |
| Control room | Optional qualified deck.gl interleaved over MapLibre | Up to 100,000 visible features and sixteen active layers | Overlaid, MapLibre-only, then list/table |
| Future server | Browser bounds remain | Server tile/aggregate capability remains contract-only | Current client fallback |

These are software admission ceilings, not measured performance claims.
Hardware, stress, thermal and production-capacity testing remain unauthorized.
Higher profiles may improve density, concurrency, rendering quality or layout;
they cannot change authorization, truth, freshness, completeness, review,
correction, safety or accessibility.

## Data And Network Boundary

Only deterministic, generated, non-issuable fixtures may be used. C1, C10 and
C50 represent one, ten and fifty generated camera features with bounded
additional features, layers and chronology. Fixtures may not contain real
places, people, vehicles, plates, owners, registrations, watchlists, cases,
investigations or evidence values.

The local map style must contain no external tile, glyph, sprite, style or
source URL. The vector-tile lane is contract/mock-only until a separately
accepted backend producer exists. Application and browser tests may use only a
bounded loopback fixture service. External application, provider, tile,
geocoder, routing, camera, media, model, broker or operational network access
is prohibited.

## Producer Gaps

The fourteen accepted producer gaps remain fail-closed. P5.2 may implement
typed consumer contracts, blocked states and generated fixtures, but it may not
create backend routes, migrations, workers, databases or false operational
responses. Missing viewport, tile, situation, coverage, workload, layer,
workspace, handoff and related producers must appear as unavailable,
generated-only or not supported.

## Validation

After exact start authorization, the implementation must pass:

- toolchain, workspace, lint, format and strict TypeScript checks;
- unit, component, story and at least 90% new-statement branch coverage;
- at least 95% coverage for authorization, renderer admission and provider
  policy;
- independent Command and GIS builds plus bundle checks;
- browser workflows for primary Command operation, specialist GIS handoff,
  multi-window revalidation and renderer fallback;
- automated accessibility, keyboard, focus, 200% zoom, contrast, reduced
  motion, non-color and map/list equivalence checks;
- English, Gujarati, Hindi, long-text, timezone and correction-state checks;
- hostile destination, malformed payload, department/role denial, scope
  change, kill-switch, no-storage and safe-telemetry checks;
- two byte-deterministic generated replays and C1/C10/C50 policy tests;
- GIS parity evidence against the accepted behavior matrix;
- dependency lock, SBOM, license, integrity, advisory and provenance checks;
- the focused P5.2 verifier, complete repository regression, Ruff and
  `git diff --check`; and
- clean-source reproduction with no tracked build, cache, coverage, screenshot
  or browser artifacts outside the evidence allowlist.

The exact commands and all 22 validation gates are in the machine-readable
package.

## Progress Boundary

- Current P5.2 product: **0/12 (0.0000%)**.
- Current Phase 5 product: **20/100 (20.0000%)**.
- Maximum before exact P5.2 exit acceptance: **11/12 (91.6667%)** and Phase 5
  **31/100 (31.0000%)**.
- After exact exit acceptance: **12/12 (100.0000%)** and Phase 5 **32/100
  (32.0000%)**.

Preparing or accepting this start package awards no product points by itself.

## Stop Conditions

Work stops closed on any bound-input or immutable-history mismatch, path escape,
toolchain mismatch, dependency/security failure, lifecycle script, browser
download, unapproved network requirement, real or issuable data need, backend
change, absent fallback, client-generated operational conclusion, parity
downgrade or twelve-cycle exhaustion.

## Owner Authorization Statement

Normalized owner-statement SHA-256 if accepted exactly:
`857539C261E566C362E02B25BCAFC6FBB39E66F982DE3E44BE5A0A99B0E1A0C1`

```text
D-P5.2-START: I, mayank-admin, accept P5.2 start package P5.2-START-R0 with SHA-256 24F89F18D52404A4FF1AA4A8A52A9DA8E4D4619B7721107B1A82EEF389805B67 and bound-input digest 3E070D61CC90E969E1A5FA91A9564D1FE151E88293904051B9B2763C5E27A74E and authorize its exact bounded local generated-only Command Center and connected GIS Center implementation scope, guarded allowlisted MapLibre and deck.gl dependency resolution and lockfile creation, source and test implementation, local loopback build and browser validation, evidence generation, and local checkpoint commits without push. Command Center remains primary; GIS Center remains connected; one shared GIS domain, authoritative list/table fallback, dynamic resource profiles, fourteen blocked producer gaps, and the Gujarat GIS parity-first no-downgrade contract remain mandatory. This does not authorize source import, unapproved dependencies or network access, backend routes or migrations, real providers or tiles, cameras or media, Government or private data, models, datasets, artifacts or inference, operational actions, hardware or production claims, containers, Kubernetes, deployment, P5.3, or remote Git.
```

The statement must be accepted exactly. A shortened acknowledgement,
`continue`, approval of another package, or the earlier planning acceptance
does not activate this package.
