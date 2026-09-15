# P5.7 Validation Portfolio

Status date: 2026-09-12

Status: proposed only; owner decisions and implementation authorization pending

## Purpose

This portfolio freezes the proposed generated journey, state, matrix, and
evidence coverage for final Phase 5 validation. It is intentionally broader
than a happy-path demonstration and narrower than a production, field,
hardware, Government, or security-accreditation test.

## Canonical Cross-Portal Journeys

| ID | Journey | Required surfaces | Critical terminal assertions |
| --- | --- | --- | --- |
| J01 | Situation to mandatory review | Command, GIS, Intelligence | Proposed alert remains unconfirmed; spatial and table views agree; review policy is server-authored; no operational action exists. |
| J02 | Reviewed proposal to investigation | Intelligence, Investigation | ETag/idempotency are preserved; accepted review is attributable; investigation link is a reference; chronology uses authoritative record sequence. |
| J03 | Investigation to evidence reference | Investigation, Evidence | Evidence stays an opaque unresolved reference; integrity is distinct from truth; provenance and custody tables agree with visual summaries. |
| J04 | Correction and retraction propagation | Intelligence, Investigation, Evidence, Command | Historical state remains visible; impact closure is bounded; corrected projections refetch; no previous record is erased. |
| J05 | GIS to camera diagnostics to live workspace | GIS, Operations camera/live | Camera handoff preserves scope; generated playback uses opaque grant; HLS/no-media state is bounded; table/status alternative remains authoritative. |
| J06 | Monitor-wall admission and profile downgrade | Operations camera/live | C1/C10/C50 admission is deterministic; low-resource mode remains functionally complete; teardown releases generated sessions; authority does not change. |
| J07 | Platform degradation response | Command, Platform Operations, Security | Degradation source/freshness/limitations are visible; route and query behavior downgrades predictably; no maintenance/recovery command becomes effective. |
| J08 | Administrative proposal and separation of duty | Admin, Security | Typed proposal remains non-effective; self-approval is denied when required; conflict/reconsideration is explicit; audit reference is append-only. |
| J09 | Access revocation and department transition | All relevant surfaces | Deep links, queries, caches, drafts, media grants, events, and selected records are cleared or denied; no cross-department residue remains. |
| J10 | Event gap and authoritative recovery | All event-consuming surfaces | Gap is detected; stream pauses or degrades safely; HTTP refetch restores state; duplicate/out-of-order events cannot create false truth. |
| J11 | Session expiry during consequential review | Intelligence, Admin, Investigation | Draft minimization is preserved; action is not retried; focus moves to clear recovery state; reauthentication cannot silently complete the action. |
| J12 | Localized keyboard-only command workflow | Command, GIS, Operations | English/Gujarati/Hindi labels and announcements are complete; focus order and return are deterministic; long text does not hide state or commands. |
| J13 | Security finding to supply-chain evidence | Security, Platform Operations | Finding, observation, vulnerability status, provenance, and compliance remain distinct; stale feeds become limitations; no scanner or update runs. |
| J14 | Offline/no-provider generated demonstration | All surfaces | No provider, map/tile, camera, media, telemetry, or external request occurs; every surface remains inspectable through generated tables and states. |

J01 through J14 are all mandatory in the recommended baseline. J01 through
J11 are critical journeys and receive the deepest browser and resilience
matrix. J12 through J14 receive all-portal semantic coverage and targeted
browser depth.

## Mandatory State Catalogue

Every applicable portal and authoritative list/detail surface must exercise:

1. loading;
2. empty;
3. ready/current;
4. partial/incomplete;
5. stale;
6. degraded;
7. denied;
8. unsupported;
9. conflict;
10. failed;
11. retryable with bounded policy;
12. non-retryable;
13. session expired;
14. capability revoked;
15. department changed;
16. event gap/recovering;
17. corrected;
18. retracted;
19. no-map/no-graph/no-media alternative;
20. recovered/refetched.

State absence requires an explicit `not_applicable` decision linked to the
route contract. It cannot be silently omitted from coverage totals.

## Browser, Locale, Viewport, And Profile Matrix

### Browser projects

| ID | Target | Required scope |
| --- | --- | --- |
| B01 | Installed Microsoft Edge on Windows | Every portal, all critical journeys, all viewports selected for Windows operator use |
| B02 | Playwright Chromium | Every portal smoke plus all critical journeys |
| B03 | Playwright Firefox | Every portal smoke plus all critical journeys |
| B04 | Playwright WebKit | Every portal smoke plus all critical journeys |

Browser binaries must be hash/version observed in the later authorized run.
An absent runtime yields `blocked_runtime_unavailable`; no download is implied
by this plan.

### Viewports

| ID | Dimensions | Purpose |
| --- | ---: | --- |
| V01 | 390 x 844 | compact touch/mobile continuity and emergency read-only access |
| V02 | 768 x 1024 | tablet portrait and touch |
| V03 | 1280 x 720 | constrained laptop and low-resource operator baseline |
| V04 | 1440 x 900 | standard enhanced workstation |
| V05 | 1920 x 1080 | full-HD operations display |
| V06 | 2560 x 1440 | control-room single display |
| V07 | 3840 x 1080 logical | dual-display/multi-monitor layout projection |

V07 is a browser viewport projection, not physical multi-monitor proof.

### Locales and time

| ID | Locale | Timezone | Stress behavior |
| --- | --- | --- | --- |
| L01 | `en-IN` | `Asia/Kolkata` | baseline English and Indian numeric formatting |
| L02 | `gu-IN` | `Asia/Kolkata` | Gujarati script, long labels, localized announcements |
| L03 | `hi-IN` | `Asia/Kolkata` | Devanagari script, long labels, localized announcements |
| L04 | `en-IN` | `UTC` | canonical/display timezone separation |
| L05 | pseudo-expanded | fixed UTC | 30/60/100 percent expansion and unbroken identifiers |

### Resource profiles

| ID | Profile | Quality/capacity behavior | Invariants |
| --- | --- | --- | --- |
| R01 | low-resource laptop | fewer optional layers/tiles, lower page density and media admission | complete workflows, same authority, truth, scope, security |
| R02 | enhanced workstation | higher rendering quality and concurrency | same authority, truth, scope, security |
| R03 | control room | dense layout and wall views | same authority, truth, scope, security |
| R04 | GPU lab | optional accelerated visual/media paths when available | no model or inference authority; same semantics |
| R05 | future server | server-capacity projection only | no deployment or runtime activation |
| R06 | Kubernetes | topology/scheduling projection only | no cluster access or execution |

The full Cartesian product is deliberately not required. A pairwise generator
covers interaction factors, while all critical cells explicitly required by
the selected owner decisions remain non-negotiable.

## Generated Workloads

### C1

- one department and one role context;
- one current record per domain;
- one map layer and one admitted generated media tile;
- no backlog, no conflict, one authoritative response revision;
- validates deterministic functional completeness.

### C10

- ten current work items across mixed domains;
- four requested/admitted generated media tiles;
- mixed ready, stale, partial, denied, conflict, and corrected states;
- bounded event burst, duplicate, delay, and one recoverable gap;
- validates ordinary operator density and cross-portal handoffs.

### C50

- fifty current work items across at least five departments with strict active
  department isolation;
- ten requested media tiles subject to deterministic profile admission;
- cursor pagination, bounded relationships, clustered/spatial projections,
  long timelines, queue backlog, and profile downgrade;
- validates bounded scale behavior and graceful degradation, not 50 real
  cameras or production capacity.

## Proposed 2,048 Generated Cases

| Family | Cases |
| --- | ---: |
| Cross-portal journeys, chronology, handoffs, and deterministic replay | 512 |
| Contract, API, event, pagination, compatibility, ETag, and idempotency | 320 |
| Accessibility semantics, keyboard, focus, alternatives, zoom, and motion | 256 |
| English/Gujarati/Hindi, expansion, Unicode, timezone, date, and number formatting | 192 |
| Browser, viewport, layout, multi-monitor, and resource-profile equivalence | 256 |
| Performance, bundle, query, map, media-admission, teardown, and scale budgets | 192 |
| Resilience, degradation, recovery, session, event-gap, and concurrency | 192 |
| Security, redaction, storage, CSP/CSRF projections, supply chain, and claims | 128 |
| Total | 2,048 |

The count is proposed and becomes frozen only after owner decisions and exact
planning acceptance. Cases use generated identifiers and content only.

## Performance Budget Framework

| Budget | Proposed gate | Qualification |
| --- | --- | --- |
| Interaction to next paint | p75 at most 200 ms on R02/R03; at most 300 ms on R01 under C10 | Generated loopback browser evidence; not field INP |
| Largest contentful paint | p75 at most 2.5 s for cold portal shell on R02; at most 3.5 s on R01 | Local generated content and named browser only |
| Cumulative layout shift | at most 0.10 per measured journey | Excludes intentional user-triggered layout changes using standard metric rules |
| Long tasks | no task over 200 ms; cumulative over-50-ms time at most 500 ms per critical step | Only where the browser exposes supported observation |
| Route readiness | p95 at most 1.5 s C10 and 2.5 s C50 after generated response availability | Separates network simulation from render time |
| Authoritative table readiness | p95 at most 1.0 s C10 and 2.0 s C50 | Table cannot be delayed behind optional map/graph/media |
| GIS idle | p95 at most 2.5 s C10 and 4.0 s C50 on R02; table remains earlier | Generated local style/data only, no tiles/provider |
| Query fan-out | at most 6 concurrent domain requests per route transition; zero duplicate equivalent requests | Exact query key and cancellation accounting required |
| Event recovery | gap detection within 1 s generated time; authoritative convergence within 5 s after service recovery | Virtual clock plus browser observation |
| Media admission | deterministic profile ceiling; first generated frame within 3 s for admitted HLS; teardown within 2 s | No real camera/media or production claim |
| Heap growth | less than 20 percent retained growth after five route/teardown cycles on supporting Chromium runtime | Diagnostic only; unsupported engines report limitation |
| Initial JavaScript | preserve existing per-app budgets and add explicit budgets for every remaining portal | Exact compressed and uncompressed artifacts recorded separately |
| Deferred chunks | GIS/media/graph chunks remain separately budgeted and absent when adapter disabled | No optional feature may silently become initial payload |

Final numeric budgets may be tightened during reconciliation but cannot be
relaxed after start without an explicit rebaseline and owner decision.

## Accessibility Evidence Matrix

Every portal needs:

- automated axe-core result with rule/tool version and exclusions;
- landmarks, page title, heading hierarchy, accessible names, descriptions,
  table headers, status/error announcements, and language attributes;
- complete keyboard path for primary and recovery workflows;
- focus visible, not obscured, ordered, trapped only in modal context, and
  restored after close/navigation;
- 200 percent zoom and 400 percent reflow evidence on representative views;
- 24-by-24 CSS-pixel target-size checks or documented WCAG exception;
- non-color status, minimum contrast, reduced-motion, and animation-stop rules;
- authoritative list/table equivalents for every map, graph, timeline, video,
  chart, matrix, topology, and wall view;
- screen-reader protocol slots for Edge + Narrator and at least one additional
  browser/AT combination in a future explicitly authorized run;
- an exact statement separating automated coverage from human conformance
  evaluation.

## Final Evidence Graph

```text
accepted requirement
  -> threat/gap
  -> test case
  -> execution environment
  -> normalized result
  -> bounded artifact hash
  -> limitation or supported claim
  -> release-manifest entry
  -> final owner acceptance
```

Every node has a stable ID and every edge is acyclic. Orphan tests, orphan
claims, unreferenced failures, missing environments, unbound screenshots, and
mutable latest-result pointers block sealing.

## Acceptance Semantics

Recommended acceptance requires:

- all mandatory cells pass;
- zero unresolved blocker or critical-severity failures;
- no unexplained skips;
- every unsupported/unavailable observation appears in the limitation
  register;
- performance budget exceptions are explicit, scoped, owned, and expiring;
- immutable Phase 0 through P5.6 readiness remains exact;
- dependency, lockfile, SBOM, build, and artifact identities match;
- evidence is sealed and revalidated from the sealed package;
- the owner accepts the exact digest in a separate statement.

Acceptance does not authorize real systems, real data, or deployment.
