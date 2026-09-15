# P5.7 Reconciled Planning R1

Status date: 2026-09-12

Status: all twelve owner decisions selected; exact planning acceptance pending;
implementation and runtime remain closed

Selected profile: `A/A/A/A/A/A/A/A/A/A/A/A`

## Reconciled Acceptance Policy

P5.7 uses strict mandatory gates. Every selected mandatory matrix cell must
pass, with zero unresolved blocker or critical failures, no unexplained skips,
immutable predecessor evidence, and a complete limitation and unsupported-claim
register. `blocked`, `unsupported`, `skipped`, `not_applicable`, and
`environment_failure` are distinct terminal states and never count as passed.

An unavailable optional environment may remain `blocked` only when the
accepted profile explicitly permits that limitation. Aggregate pass counts,
weighted scores, or a working demonstration cannot hide a mandatory failure.

## Reconciled Journey Portfolio

All fourteen canonical journeys `J01` through `J14` are mandatory planning
inputs. Each has deterministic success, negative, stale, degraded, conflict,
correction, recovery, and teardown variants where applicable. A bounded
pairwise matrix combines journeys with selected browsers, locales, viewports,
resource profiles, workloads, and states without creating an unbounded full
Cartesian product.

The nine logical operator surfaces remain distinct: Command Center, GIS
Center, Operations camera/live surfaces, Intelligence Center, Investigation
Center, Evidence Desk, Admin Center, Security Center, and Platform Operations.
Command Center remains primary. Cross-portal navigation never grants authority
and every consequential server state requires authoritative HTTP confirmation.

## Reconciled Browser Baseline

Installed Microsoft Edge is the primary local browser target. Approved
Playwright Chromium, Firefox, and WebKit runtimes cover smoke and critical
journeys according to the frozen tier matrix. The implementation must not
download a browser automatically. A missing or unapproved runtime is reported
as blocked or unsupported with its exact evidence limitation, never passed.

Browser target, channel, version, executable source, viewport, locale,
timezone, resource profile, and generated workload belong to every applicable
result. Browser emulation does not become physical-device evidence.

## Reconciled Accessibility Baseline

The target is WCAG 2.2 AA with WCAG-EM-style scope and reporting. Evidence is
layered and attributable:

- axe and ACT-aligned automated checks;
- component semantics and authoritative table/list equivalence;
- keyboard entry, composite navigation, escape, focus movement and return;
- focus visibility and focus-not-obscured geometry;
- 200 and 400 percent zoom/reflow and deterministic text expansion;
- 24-by-24 CSS-pixel target sizing or an explicit typed exception;
- contrast, non-color meaning, reduced motion, status, error, and recovery;
- separately executed and recorded manual screen-reader protocols.

Automated evidence does not establish conformance. A WCAG, GIGW, assistive
technology, or accessibility-conformance claim remains blocked until the exact
declared manual evaluation is performed and accepted.

## Reconciled Localization And Time

The required language profiles are `en-IN`, `gu-IN`, and `hi-IN`, plus
pseudo-expanded and UTC-focused profiles. Validation covers message-ID
completeness, semantic equivalence, fallback visibility, 30/60/100 percent
expansion, wrapping, clipping, occlusion, bidirectional and hostile Unicode,
normalization, confusable display, and active-document language.

Numbers, percentages, lists, dates, times, relative times, and timezones use
explicit `Intl` contracts. Canonical ordering, event identity, decisions,
digests, and server timestamps remain locale independent. Operator displays
qualify `Asia/Kolkata` and UTC rather than silently mixing them.

## Reconciled Viewports And Profiles

Seven deterministic viewports cover mobile, tablet, constrained laptop,
standard desktop, full HD, control room, and a logical dual-display projection.
Resource profiles `R01` through `R06` cover low-resource, enhanced workstation,
control room, GPU lab, future server, and Kubernetes projection. Pairwise
coverage is bounded, while critical low-resource, standard, and control-room
cells are mandatory.

Every profile remains functionally complete. Profiles may alter admitted
streams, rendering quality, optional visualization, pagination, prefetch, and
concurrency only. They cannot alter authorization, department scope, truth,
review rules, action eligibility, accessibility, data minimization, or security
policy. Logical multi-monitor projection is not physical multi-monitor proof.

## Reconciled Performance And Scale

P5.7 uses context-qualified hard budgets for interaction, reference LCP and
CLS, long tasks, route readiness, authoritative table readiness, map idle,
query fan-out, event recovery, generated-media admission and teardown, bounded
Chromium heap diagnostics, initial and deferred bundle size, and profile
convergence. Results include the exact environment, workload, sample method,
percentile, threshold, outcome, and limitation. Thresholds are not relaxed
automatically.

Deterministic generated `C1`, `C10`, and `C50` workloads cover domain work
items, event bursts, pagination, tables, maps, graphs, and generated media
admission. Stable state digests and budgets are compared across profiles. These
results describe generated UI and workflow scale only; they do not establish
production capacity, real-camera throughput, hardware sizing, or deployment
readiness.

## Reconciled Resilience

The required deterministic fault catalogue covers HTTP failures and typed
problem details, duplicate/delayed/out-of-order/gapped events, authoritative
refetch, session expiry, capability revocation, department transition, ETag and
idempotency conflict, stale queries, map failure, generated-media stall,
profile downgrade, and bounded client-storage failure.

Each case has a stable injected cause, bounded retry policy, explicit degraded
state, focus and draft policy, teardown requirements, recovery transition, and
terminal digest. Consequential commands are never automatically retried.
Random exploration and real outage exercises may be future non-gating evidence
only after deterministic validation and separate authorization.

## Reconciled Security And Privacy

The final generated-only security layer inventories hostile content and every
HTML, URL, style, SVG, map-style, message, and media-adjacent sink. It validates
CSP and CSRF expectations, safe rendering, browser storage, logout and scope
teardown, department isolation, telemetry cardinality and redaction, denial of
secret/private fields, dependency and bundled-content identity, SBOM and
license consistency, and vulnerability observation age.

Client evidence never replaces backend authorization or PostgreSQL RLS proof.
Stale vulnerability data remains an explicit limitation. No generated result
is described as a production penetration test, operational security assurance,
privacy certification, or legal compliance determination.

## Reconciled Build And Provenance

The final release manifest binds source and evidence commits, Node and package
manager identity, lockfile, installed dependency tree, build commands,
environment projection, application outputs, SBOM and license state, and
artifact hashes. When runtime is separately authorized, two clean builds in
the same controlled local environment are compared after documented
normalization.

That evidence may establish local repeatability only. Independent
reproducibility, signed provenance, SLSA compliance, trusted-builder claims,
and cross-machine equivalence remain blocked without separately authorized and
validated environments, signing identity, and verification policy.

## Reconciled Evidence And Final Gate

The evidence graph binds requirements, journeys, matrix cells, results,
environments, tools, artifacts, limitations, claims, release manifest, and
source/evidence commits through exact IDs and SHA-256 values. The graph must be
acyclic, complete for every selected mandatory cell, and independently
revalidated from the sealed package.

Technical completion is capped at **11/12 (91.6667%)**. The final point is
earned only through an exact owner statement naming the final P5.7 package
SHA-256 and canonical component digest. Green tests, a quality score, a short
acknowledgement, or a demo cannot imply final acceptance.

## Frozen Validation Portfolio

The selected implementation baseline remains exactly 2,048 generated cases:

| Category | Cases |
| --- | ---: |
| Cross-portal journeys and replay | 512 |
| Contract, API, event, and concurrency | 320 |
| Accessibility | 256 |
| Localization, time, and Unicode | 192 |
| Browser, layout, and resource profiles | 256 |
| Performance, scale, and bundles | 192 |
| Resilience | 192 |
| Security, privacy, and supply chain | 128 |
| **Total** | **2,048** |

The portfolio preserves 14 journeys, 20 mandatory states, 7 viewports, 5
locale/time profiles, 6 resource profiles, 64 gaps, and 64 threats. The 64 gaps
remain 59 blocking, 4 conditional, and 1 limitation. Selection does not close
any gap or threat.

## Frozen Workstreams

| Workstream | Weight | Selected purpose |
| --- | ---: | --- |
| P5.7-W1 | 1.25 | Final quality contracts, manifests, and generated fixtures |
| P5.7-W2 | 2.00 | Cross-portal journeys, chronology, and deterministic replay |
| P5.7-W3 | 1.50 | Accessibility, localization, time, and Unicode validation |
| P5.7-W4 | 1.25 | Browser, viewport, device, and resource-profile compatibility |
| P5.7-W5 | 1.50 | C1/C10/C50 scale, performance, memory, media, and bundle budgets |
| P5.7-W6 | 1.50 | Resilience, security, privacy, and supply-chain validation |
| P5.7-W7 | 2.00 | Full regression, history, repeatability, evidence, and release manifest |
| P5.7-W8 | 1.00 | Exact digest-bound owner final acceptance |
| **Total** | **12.00** | **P5.7 product weight** |

## Preserved Boundaries

- all accepted Phase 0 through P5.6 contracts, evidence, decisions, commits,
  product behavior, and safety boundaries remain unchanged;
- Command Center remains primary and all specialist surfaces retain their
  ownership and authorization boundaries;
- generated-only validation cannot become a claim about real providers,
  networks, cameras, media, identities, data, models, operations, hardware,
  capacity, deployment, security, accessibility conformance, or production;
- no source import, dependency resolution, download, installation, lockfile
  change, backend route, migration, product/test implementation, browser/runtime
  execution, container, Kubernetes, deployment, final acceptance, or remote Git
  is authorized by decision selection or this reconciliation;
- the consumed P5.7 planning checkpoint does not authorize another commit.

## Exact Progress

- Owner decisions: **12/12 (100.0000%)**, change **+100.0000 percentage
  points**; no product points awarded.
- P5.7 planning: **8/8 (100.0000%)**, change **+0.0000 percentage points**; no
  product points awarded.
- P5.7 product: **0/12 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **88/100 (88.0000%)**, change **+0.0000 percentage points**.

No scope or weight rebaseline occurred.

## Remaining Gates

1. Seal and validate `P5.7-PLANNING-R1`.
2. Obtain exact owner acceptance of that package.
3. Prepare one separate non-effective, digest-bound P5.7 start package.
4. Obtain exact P5.7 start authorization before implementation or runtime.
5. Complete technical work to the 11/12 cap under the future accepted scope.
6. Obtain exact final owner acceptance for the final 1/12 point and Phase 5
   completion.
