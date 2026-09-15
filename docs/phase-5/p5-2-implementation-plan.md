# P5.2 Bounded Implementation Plan

Status: proposed and non-effective; owner decisions and start authorization pending

Product weight: 12 Phase 5 points

## Preconditions

Implementation may begin only after all of the following:

1. `D-P5.2-001` through `D-P5.2-012` are selected.
2. Selections are reconciled into an exact planning package.
3. The owner accepts the exact reconciled package and digest.
4. A separate start package freezes paths, dependency versions, source
   adoption method, producer-gap treatment, fixtures, commands, resource
   bounds, evidence, stop conditions, and rollback.
5. The owner authorizes that exact start package.
6. Every producer gap required by the initial slice is implemented and
   accepted, or its consumer capability remains visibly blocked.

## Frozen Proposed Workstreams

| Workstream | Weight | Deliverables | Completion evidence |
| --- | ---: | --- | --- |
| `P5.2-W1` Command projection contracts and fixtures | 1.5 | Situation snapshot, layer registry, feature/tile/list/detail references, time window, source state, workload, selection, and blocked-gap fixtures | Schema snapshots, generated vectors, prohibited-field scan, producer coverage |
| `P5.2-W2` Situational overview and truthful states | 1.5 | Status strip, bounded summary, source completeness/freshness/loss, degradation, empty/partial/stale/denied/failure/recovery behavior | Component and state matrix, deterministic aggregate fixtures, no-false-green assertions |
| `P5.2-W3` GIS domain, delivery, and adapter extension | 2.0 | Additive feature kinds/statuses, viewport bounds, layer registry, renderer admission, feature/tile/list lanes, safe detail references | Contract tests, hostile geometry/payload vectors, renderer failure fallback |
| `P5.2-W4` Gujarat GIS parity workspace | 2.0 | Explorer, map, inspector, summary, toolbar, footer, filters, layers, clustering, selection, responsive controls, truthful generated-lab labels | Parity matrix, stories, screenshots, interaction tests, no-downgrade review |
| `P5.2-W5` Coverage, health, workload, time, and drill-down | 1.5 | Coverage/health panels, safe workload bands, bounded time controls, authoritative list/detail navigation, correction state | Generated chronology and drill-down vectors, role/scope/ETag tests where applicable |
| `P5.2-W6` Accessibility, localization, responsive and multi-monitor | 1.5 | List/table equivalence, landmarks, focus, keyboard, announcements, non-color state, zoom/reflow, profile layouts, independent-window policy | Static/component/browser tests, locale checks, screenshot matrix, later manual AT gate |
| `P5.2-W7` Security, profiles, observability and resource bounds | 1.0 | Same-origin map policy, CSP proposal, safe telemetry, abort/dedupe, profile caps, kill-switch and scope-change behavior | Threat-control trace, static policy, generated C1/C10/C50, dependency evidence |
| `P5.2-W8` Validation, evidence and exact exit acceptance | 1.0 | Complete validation, immutable evidence package, limitations, technical commit, owner acceptance proposal and record | Clean focused/full tests, package digest, component manifest, exact owner acceptance |

Total: **12.0 points**. Workstream points are all-or-nothing. Planning does not
earn product points. Any scope or weight change requires an explicit rebaseline.

## Delivery Sequence

### Stage 1: Contracts And Generated Truth

- implement additive frontend-only types against accepted producer contracts;
- preserve generated-only identifiers and zero real-data fixtures;
- encode all gaps as disabled capabilities with sanitized reasons;
- freeze layer, state, time, freshness, completeness and drill-down semantics;
- do not add backend routes or migrations unless separately authorized.

Exit: W1 contract snapshots and generated boundary vectors pass.

### Stage 2: Overview And Authoritative Lists

- implement status strip, situation summary and source-state details;
- implement the authoritative workload/list surface before map rendering;
- preserve denied, partial, stale, degraded, failure and recovery states;
- ensure low-resource profile is functionally complete.

Exit: W2 and the list portion of W5 pass without a map dependency.

### Stage 3: GIS Adapter And Parity Workspace

- extend `@hcam/gis-contracts` additively;
- integrate the exact accepted renderer behind the adapter only after dependency
  authorization and evidence;
- reproduce the canonical Gujarat GIS structure and interactions without source
  import unless separately authorized;
- keep all map resources same-origin and generated-only;
- preserve list/detail operation when renderer admission fails.

Exit: W3 and W4 pass parity, geometry, payload, teardown, fallback and profile tests.

### Stage 4: Drill-Down, Profiles And Accessibility

- connect generated authoritative detail transitions;
- apply bounded time-window and correction semantics;
- validate keyboard, focus, live updates, non-color cues, zoom, reflow,
  localization and independent-window policy;
- apply profile-specific density/concurrency without semantic downgrade.

Exit: W5, W6 and W7 pass their exact matrices.

### Stage 5: Evidence And Acceptance

- run focused frontend tests and build;
- run deterministic browser and screenshot checks at frozen viewports;
- run generated C1/C10/C50 profile cases without hardware claims;
- run complete repository regression and historical readiness;
- create evidence manifest and technical checkpoint commit without push;
- prepare exact owner acceptance proposal.

Exit: W8 technical evidence is sealed. The final product point is awarded only
after exact owner acceptance.

## Proposed Start-Package Allowlist Categories

The later start package should enumerate exact paths under these categories:

- `frontend/apps/command-center/` command routes, views, generated stories and tests;
- additive shared contracts under `frontend/packages/gis-contracts/`,
  `api-client/`, `operator-contracts/`, `capabilities/`, `observability/`, and
  `test-harness/` only where justified;
- generated P5.2 fixtures and mock-service projections;
- exact Phase 5 documentation, evidence, package and status records;
- exact dependency and lockfile entries if option `D-P5.2-011:A` is selected;
- narrow historical compatibility tests only when pre-hashed and separately
  described in the start package.

No wildcard path authorizes source import, backend work, maps/tiles/network,
real data, media, models, operational actions, deployment, or remote Git.

## Dependency Gate

Before adding a GIS runtime dependency, the start package must record:

- exact package and transitive versions;
- official source and license;
- integrity and lockfile diff;
- SBOM and vulnerability state with refresh timestamp;
- ESM/build/browser compatibility;
- worker packaging and CSP requirements;
- bundle-size budget by portal/profile;
- supported-browser and WebGL admission matrix;
- renderer-neutral rollback and list-only fallback.

A vulnerability database that cannot be refreshed is reported as an explicit
limitation, not a clean security result.

## Generated Fixture Plan

All fixtures remain synthetic and non-issuable. The minimum catalogue should cover:

- C1, C10 and C50 cameras/streams plus bounded high-feature spatial cases;
- complete, partial, stale, degraded, denied, failed and recovering snapshots;
- alerts, reviews and investigations using anonymous synthetic IDs;
- corrected/retracted records and event/recorded-time differences;
- antimeridian, invalid coordinate, oversized geometry and unknown-layer cases;
- duplicate, delayed, burst and out-of-order invalidation events;
- role and department denials, session expiry and scope changes;
- renderer unavailable, worker failure, tile failure and list-only fallback;
- English, Gujarati and Hindi labels with long-text and missing-key cases;
- 200 percent zoom, narrow viewport and multi-monitor projection cases.

Fixtures contain no real locations, Government identifiers, camera locators,
credentials, faces, plates, media, owner data, evidence, or operational alerts.

## Validation Matrix

| Layer | Required later validation |
| --- | --- |
| Contract | Schema, version, unknown field, bound, protected field, operation mapping and deterministic snapshot tests |
| Unit | State reducers, source truth, time, priority, viewport, selection, admission, profile and error mapping |
| Component | Keyboard, focus, labels, status announcements, list/map synchronization, partial and denied states |
| Story/visual | All state variants, locales, profiles, themes, narrow/desktop/control-room viewports and no overlap |
| Browser | Route/session/scope, CSP, same-origin worker, query abort/dedupe, renderer teardown, failure fallback, multi-window revocation |
| Security | Role/department denial, hostile payload, destination, URL/storage/log/telemetry leakage, injection and dependency evidence |
| Resource | Generated C1/C10/C50 query, feature, tile, memory, render and recovery bounds by declared profile |
| Repository | Frontend build/test/lint, Python regression, migration head unchanged, historical acceptance unchanged, clean changed-path allowlist |
| Manual later gate | Keyboard walkthrough, zoom/reflow, contrast, screen reader, control-room layout and public-safety terminology review |

## Stop Conditions

Stop closed and do not silently degrade if:

- an exact path, dependency, digest or immutable predecessor changes outside the start package;
- a producer contract is absent, role-incompatible, unversioned or not department-scoped;
- a map resource requires an unapproved destination or exposes credentials;
- a generated fixture contains a real or plausibly operational identifier;
- a protected value reaches a URL, storage API, log, error or telemetry label;
- map failure removes authoritative list/detail access;
- low-resource mode changes authority, review, freshness, completeness or safety semantics;
- any runtime test would require cameras, media, Government/private data,
  models, providers, deployment or another unauthorized capability;
- deterministic tests, historical readiness or exact digest validation fail.

## Progress Accounting

Current P5.2 product progress remains **0/12 (0.0000%)**. Phase 5 remains
**20/100 (20.0000%)**. Completing this planning package changes planning
progress only and awards no product credit.
