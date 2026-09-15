# P5.7 Quality, Scale, And Final Acceptance Architecture

Status date: 2026-09-12

Status: proposed architecture; owner decisions and implementation authorization pending

## Objective

P5.7 creates the final Phase 5 verification and evidence architecture for the
accepted generated-only operator platform. It does not add another operator
portal, backend producer, real integration, data source, model, camera, media
service, administrative executor, operational action, or deployment path.

The objective is to answer five questions with exact evidence:

1. Do the nine accepted operator surfaces work together without changing
   truth, scope, authority, chronology, or accessibility meaning?
2. Are contract, state, concurrency, degradation, recovery, and security
   behaviors deterministic under generated workloads?
3. Is the operator experience usable across the declared browser, locale,
   viewport, and resource-profile matrix?
4. Are performance, bundle, memory, query, map, and media-admission budgets
   measured and honestly qualified?
5. Can every final claim be traced to an accepted requirement, exact source,
   test, result, environment, limitation, and immutable digest?

## Surface Topology

```text
Command Center (primary)
|
+-- GIS Center
+-- Operations Center
|   +-- Camera Catalogue / Detail / Diagnostics
|   +-- Live Workspace / Monitor Wall
|   +-- Platform Operations
+-- Intelligence Center
+-- Investigation Center
+-- Evidence Desk
+-- Admin Center
+-- Security Center
```

The eight applications expose nine logical surfaces because camera/live
operations and Platform Operations have different truth, authority, and test
contracts inside Operations Center. P5.7 validates both without splitting or
merging their accepted ownership.

## Quality Control Plane

P5.7 uses one generated quality control plane composed of immutable manifests
and pure validation logic:

```text
Accepted Phase 0-P5.6 records
        |
        v
Quality scope and requirement manifest
        |
        +-- portal / route / state inventory
        +-- journey and replay manifest
        +-- browser / locale / viewport / profile matrix
        +-- threat / control / test matrix
        +-- performance and bundle budgets
        +-- dependency / SBOM / provenance expectations
        |
        v
Layered generated validation
        |
        +-- static and schema checks
        +-- contract and pure-domain checks
        +-- component and integration checks
        +-- browser and accessibility checks
        +-- deterministic cross-portal replay
        +-- resilience, security, and scale checks
        +-- build, dependency, and history checks
        |
        v
Normalized result records
        |
        +-- pass / fail / blocked / skipped / unsupported / not_applicable
        +-- exact environment and duration
        +-- artifact hashes and bounded diagnostic references
        +-- limitation and claim impact
        |
        v
Evidence graph -> release manifest -> owner acceptance gate
```

No result producer can directly mark Phase 5 accepted. The final state change
requires a sealed package and a separate exact owner acceptance statement.

## Canonical Quality Entities

### Requirement

Every requirement records:

- stable requirement ID and revision;
- source phase/subphase, accepted artifact, and source reference;
- normative strength inside H-CAM: mandatory, conditional, optional, or
  prohibited;
- affected portals, routes, states, roles, departments, locales, viewports,
  profiles, and transports;
- verification method and required evidence class;
- blocking severity and waiver policy;
- linked threats, gaps, tests, results, claims, and limitations.

### Journey

A journey is a bounded ordered graph, not an informal script. It records:

- actor role, active department, purpose, and capability ceiling;
- generated scenario, seed, virtual clock, and initial revisions;
- ordered HTTP projections, event invalidations, UI states, and operator
  actions;
- required focus, announcement, table/list, and route transitions;
- expected ETags, idempotency keys, conflicts, corrections, and terminal state;
- cleanup and teardown assertions;
- prohibited transitions and unsupported claims.

### Matrix Cell

Each browser/locale/viewport/profile/workload cell has one of seven states:

`planned`, `passed`, `failed`, `blocked`, `skipped`, `unsupported`, or
`not_applicable`.

Only `passed` satisfies a mandatory observed cell. `skipped` and `unsupported`
remain visible release limitations. `not_applicable` requires a typed reason
and requirement link.

### Result

Results contain stable low-cardinality fields only:

- test and requirement IDs;
- result class and safe reason code;
- start/end timestamps and duration;
- source commit, manifest digest, tool/version projection, and environment ID;
- browser engine/channel, locale, viewport, profile, and workload where
  applicable;
- bounded counters and percentile summaries;
- artifact references and SHA-256 values;
- retry/attempt identity and flake classification;
- limitation and claim impact.

Raw private data, credentials, tokens, browser profiles, absolute personal
paths, screenshots containing sensitive data, raw console output, and
unbounded traces are prohibited.

### Claim And Limitation

Claims are allowlisted and evidence-bound. A claim records its exact text,
scope, evidence prerequisites, observations, expiration/freshness, and
limitations. Unsupported claim classes are blocked by static validation.

Limitations record whether evidence was not run, unavailable, generated,
emulated, environment-specific, stale, partial, or outside scope. Limitations
are first-class release artifacts and cannot be hidden in narrative prose.

## Evidence Layers

| Layer | Proves | Does not prove |
| --- | --- | --- |
| Static | Paths, schemas, forbidden strings, manifests, hashes, and source invariants | Runtime behavior or usability |
| Contract | Accepted shapes, bounds, discriminants, compatibility, and rejection | Browser rendering or producer correctness |
| Pure domain | Deterministic state, ordering, concurrency, admission, and projection behavior | Network, database, browser, or deployment behavior |
| Component | Rendered states, semantics, interaction, focus, and local error handling | Full browser engine behavior or backend enforcement |
| Integration | Package and portal handoffs over generated producers | Real provider or operational integration |
| Browser | Actual declared engine behavior on loopback generated fixtures | Physical device, field network, or production support |
| Manual protocol | Human-observed keyboard, screen-reader, zoom, language, and usability evidence | Universal accessibility conformance |
| Performance | Bounded lab observations under a named environment and workload | Production capacity or field latency |
| Build/supply chain | Locked inputs, outputs, SBOM, license, provenance, and repeatability observations | SLSA level or vulnerability absence without required trust and refresh |
| Immutable history | Accepted artifacts remain exact and Phase 5 descends from accepted predecessors | Correctness of the accepted behavior itself |

## Browser And Device Architecture

The proposed matrix is tiered to control cost without hiding unsupported
behavior:

- **Tier 0 static:** all portal routes and shared contracts, no browser;
- **Tier 1 operator baseline:** installed Microsoft Edge on Windows, all
  portals, critical and portal-specific journeys;
- **Tier 2 engine compatibility:** Playwright Chromium, Firefox, and WebKit for
  critical cross-portal journeys and every portal smoke path;
- **Tier 3 emulation:** deterministic mobile, tablet, laptop, desktop, and
  control-room viewports with touch, locale, timezone, color scheme, and
  reduced-motion variants;
- **Tier 4 future physical evidence:** real devices and assistive technology,
  outside the initial generated-only implementation unless separately
  authorized.

Missing engine binaries must stop the corresponding required cell or record it
as blocked according to the selected decision. The plan never downloads a
browser without a later exact start authorization.

## Accessibility Architecture

Accessibility evidence is split into three lanes:

1. **Deterministic semantic lane:** axe-core, DOM semantics, names,
   relationships, heading/landmark structure, state attributes, table
   alternatives, status/error associations, and prohibited interaction checks.
2. **Browser interaction lane:** keyboard-only journeys, focus entry/order/
   visibility/return, no traps, zoom/reflow, target sizing, reduced motion,
   contrast tokens, high-contrast/forced-color behavior where supported, and
   stale/error/recovery announcements.
3. **Manual protocol lane:** screen-reader and human evaluation checklist with
   exact browser/AT version, view sample, observed outcome, issue, evidence,
   and limitation. Unperformed manual checks cannot be marked passed.

WCAG-EM-style scoping and reporting governs any future conformance statement.
P5.7 can complete the H-CAM product milestone with documented environment
limitations, but it cannot claim WCAG conformance without the selected and
actually executed evaluation baseline.

## Localization Architecture

English, Gujarati, and Hindi use the same stable message IDs and typed
parameters. Validation covers:

- UTF-8 and declared language;
- no untranslated message IDs in required views;
- no sentence construction by concatenating fragments;
- 30, 60, and 100 percent text expansion fixtures;
- long unbroken identifiers and bounded wrapping;
- plural, list, number, percentage, date, absolute time, relative time, and
  timezone formatting through explicit locale options;
- canonical timestamps and sequence values remaining machine-readable and
  locale-independent;
- search/filter semantics separated from display formatting;
- accessible names and status announcements in the active language;
- layout stability and no clipped action labels at every required viewport.

## Performance And Scale Architecture

P5.7 uses deterministic generated workloads, not production load claims:

- **C1:** one active work item per domain, one admitted generated media tile,
  minimal relationships, and no backlog;
- **C10:** ten active work items per domain, four admitted media tiles, mixed
  stale/conflict/degraded states, and bounded event churn;
- **C50:** fifty active work items per domain, ten requested media tiles under
  deterministic profile admission, paginated tables, bounded maps/graphs, and
  recovery backlog.

Every measurement records cold/warm state, iteration count, percentile,
browser, viewport, locale, profile, CPU-throttle setting if any, and hardware
limitations. Proposed budget classes are:

- interaction response and next-paint latency;
- long-task count and cumulative duration;
- route shell and content readiness;
- GIS map idle and authoritative table readiness;
- query fan-out, duplicate request prevention, and cancellation;
- event invalidation-to-authoritative-refetch completion;
- memory growth and post-teardown recovery where measurable;
- initial, route, GIS, HLS, and other deferred bundle bytes;
- media admission, first generated frame, stall recovery, and teardown;
- profile downgrade/upgrade convergence and semantic invariance.

Budget failure blocks acceptance unless the owner selects a separately
documented exception with scope, reason, expiry, evidence, and risk. A missing
or unsupported metric is not a pass.

## Resilience Architecture

Fault injection is generated and deterministic. The matrix includes:

- event gap, duplicate, out-of-order, delayed, and unsupported event revision;
- HTTP timeout, 429, 5xx, malformed problem, partial page, stale response, and
  aborted request;
- session expiry, reauthentication required, role/department switch, and
  capability revocation;
- ETag conflict, idempotency reuse/mismatch, lost response, and explicit
  reconsideration;
- map adapter unavailable, tile/provider unavailable, and table-only mode;
- generated media stall, unsupported codec, WHEP unavailable, HLS fallback,
  admission denial, and teardown;
- profile downgrade during active work and recovery without authority change;
- storage quota/unavailable projection without retaining protected content;
- route crash containment, safe error boundary, focus recovery, and bounded
  retry.

All recovery converges through authoritative HTTP state. Events invalidate;
they never become authoritative state by themselves.

## Security And Supply-Chain Architecture

P5.7 verifies projections and build evidence for:

- same-origin session assumptions, CSRF defense requirements, safe HTTP
  methods, CSP, framing, referrer, MIME, and permission policy;
- output encoding, no dangerous HTML injection, URL/destination allowlists,
  hostile identifiers, Unicode controls, spreadsheet/formula prefixes, and
  bounded errors;
- no secrets, tokens, private data, evidence payloads, or operational material
  in browser storage, URLs, logs, telemetry, screenshots, clipboard, or
  cross-window messages;
- server-authoritative permission, department isolation, deep-link denial,
  query/cache isolation, event invalidation isolation, and teardown;
- lockfile and installed-tree identity, SBOM completeness, license inventory,
  vulnerability observation freshness, dependency drift, source map absence,
  and forbidden bundled content;
- source commit, build command, environment, input digests, output digests,
  reproducibility comparison, and provenance limitations.

No generated client test can prove backend authorization, PostgreSQL RLS,
production headers, network controls, secret handling, or deployment safety.
Those remain explicit producer/environment gaps.

## Final Acceptance Gate

P5.7 technical completion may reach **11/12 (91.6667%)** only after all
selected mandatory generated/static/browser/manual-protocol/build/history
requirements are sealed with zero unresolved blocking failures. The final
**1/12 (8.3333%)** requires a separate exact owner acceptance of the evidence
package and its limitations.

That owner acceptance completes Phase 5 against its frozen 100-point product
model. It does not authorize deployment, operational use, real data, cameras,
media, models, integrations, or Phase 6.
