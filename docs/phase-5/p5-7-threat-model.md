# P5.7 Quality And Final-Acceptance Threat Model

Status date: 2026-09-12

Status: planning inventory; generated-only verification proposed

## Scope

This threat model covers the P5.7 validation system, its generated fixtures,
browser runs, evidence artifacts, release manifest, claims, and final owner
gate. It complements all accepted product threat models. It does not claim to
replace deployment, infrastructure, provider, camera, model, privacy, legal,
or independent security assessment.

## Trust Boundaries

1. accepted source and historical Git objects;
2. generated fixture and replay inputs;
3. validation tools and browser runtimes;
4. loopback portal processes and browser contexts;
5. normalized result and diagnostic artifacts;
6. evidence package and release manifest;
7. human/manual observations;
8. owner decision and final acceptance.

## Threat Catalogue

### Scope And Evidence Integrity

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T01 | A route, portal, state, or profile is omitted from the quality scope. | Canonical inventory diff against accepted manifests; omission blocks seal. |
| P5.7-T02 | Tests pass against a different commit than the one recorded. | Bind source commit before/after every run and evidence generation. |
| P5.7-T03 | Evidence artifacts are modified after validation. | Per-file SHA-256, canonical component digest, immutable package, clean reseal. |
| P5.7-T04 | A result is linked to the wrong test, environment, or requirement. | Stable IDs, schema validation, referential integrity, and acyclic evidence graph. |
| P5.7-T05 | Generated evidence is represented as real or production evidence. | Mandatory evidence-class field and prohibited-claim scanner. |
| P5.7-T06 | A skipped or unsupported check is counted as passed. | Closed result enum; pass counts exclude every non-pass state. |
| P5.7-T07 | A failed test is hidden by aggregate summaries. | Preserve every terminal result and fail aggregate on unresolved blockers. |
| P5.7-T08 | Old evidence is reused after source, tool, config, or manifest drift. | Input digest and freshness checks; mismatch invalidates evidence. |

### Determinism, Replay, And Flakes

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T09 | Wall-clock, random IDs, locale, or timezone make replay nondeterministic. | Fixed seed, virtual clock, explicit locale/timezone, deterministic IDs. |
| P5.7-T10 | Event order changes between runs. | Materialized event sequence and terminal state digest comparison. |
| P5.7-T11 | Automatic retry hides a product failure. | Retry disabled by default; any retry separately recorded and classified. |
| P5.7-T12 | Environment instability is misclassified as a product pass. | `blocked`/`environment_failure` states; no pass without completed assertions. |
| P5.7-T13 | Snapshot replacement blesses unintended UI changes. | Reviewable semantic assertions; snapshot changes require explicit scope decision. |
| P5.7-T14 | Non-deterministic animation or timers create false failures. | Reduced-motion mode, virtual timers where valid, bounded readiness contracts. |
| P5.7-T15 | Parallel test state leaks between portals or departments. | Isolated browser contexts, fixture namespaces, deterministic worker policy. |
| P5.7-T16 | Cleanup failure contaminates later evidence. | Post-test storage, event, query, media, process, and port cleanliness assertions. |

### Accessibility And Localization

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T17 | Automated accessibility checks are treated as complete conformance. | Separate automated/manual lanes and explicit non-conformance statement. |
| P5.7-T18 | Visual map/graph/video content lacks equivalent authoritative data. | Semantic equivalence tests for ready, stale, partial, error, and selection states. |
| P5.7-T19 | Focus is hidden, lost, trapped, or returned to the wrong element. | Geometry, keyboard, modal, navigation, and recovery focus tests. |
| P5.7-T20 | Dense controls use targets too small for touch or motor access. | Target-size measurement or typed exception evidence. |
| P5.7-T21 | Zoom or long text clips commands, truth qualifiers, or error details. | 200/400 percent reflow and 30/60/100 percent expansion checks. |
| P5.7-T22 | Gujarati or Hindi fallback exposes raw IDs or wrong-language announcements. | Message completeness and active-language semantic checks. |
| P5.7-T23 | Localized dates reorder or misrepresent chronology. | Canonical sequence/UTC values plus explicit locale/timezone formatting. |
| P5.7-T24 | Unicode bidi/control/confusable input deceives an operator. | Bounded sanitization, visible representation, normalization policy, and tests. |

### Browser, Layout, And Performance

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T25 | Validation uses only one Chromium-derived browser. | Selected Chromium/Firefox/WebKit/Edge matrix with explicit blocked cells. |
| P5.7-T26 | Emulated viewport evidence is presented as physical-device proof. | Environment class and limitation in every result and claim. |
| P5.7-T27 | Optional GIS/media/graph code inflates every portal bundle. | Initial/deferred chunk budgets and adapter-disabled absence checks. |
| P5.7-T28 | C50 work causes main-thread starvation and hides urgent state changes. | Long-task, interaction, table-readiness, and bounded-render checks. |
| P5.7-T29 | Map readiness blocks authoritative table access. | Independent table readiness budget and no-map fallback tests. |
| P5.7-T30 | Query fan-out overwhelms a future backend or duplicates sensitive requests. | Exact query count, dedupe, cancellation, and key-scope assertions. |
| P5.7-T31 | Repeated portal/media cycles leak browser memory or grants. | Bounded retained-growth diagnostic and teardown identity checks. |
| P5.7-T32 | Performance numbers are incomparable or selectively reported. | Fixed protocol, iterations, percentiles, cold/warm state, full result retention. |

### Resilience And Concurrency

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T33 | Duplicate or out-of-order events create duplicate alerts or stale truth. | Event ID/revision dedupe and authoritative refetch convergence. |
| P5.7-T34 | Event gap is ignored and stale UI appears current. | Gap detection, explicit degraded state, refetch, and freshness restoration. |
| P5.7-T35 | Lost command response causes an unsafe automatic retry. | Idempotency receipt lookup and no automatic consequential retry. |
| P5.7-T36 | Weak/stale ETag overwrites another review or proposal. | Strong `If-Match`, 412, comparison, and explicit reconsideration. |
| P5.7-T37 | Session expiry preserves sensitive drafts or permits delayed submission. | Draft minimization, command invalidation, reauthentication, explicit resume. |
| P5.7-T38 | Department switch leaves queries, selections, or subscriptions from prior scope. | Cache namespace, subscription, history, draft, and grant teardown. |
| P5.7-T39 | Profile downgrade changes authority or silently drops required information. | Cross-profile semantic/authority diff and authoritative fallback. |
| P5.7-T40 | Recovery loop repeatedly retries a permanent failure. | Typed retryability, attempt bounds, backoff projection, terminal state. |

### Web Security And Privacy

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T41 | Cross-site request submits a state-changing command. | CSRF contract matrix, safe methods, same-origin/origin/fetch-metadata requirement. |
| P5.7-T42 | Injected content executes through HTML, SVG, map style, URL, or message sinks. | Sink inventory, safe rendering, allowlisted adapters, CSP projection, hostile tests. |
| P5.7-T43 | Permissive CSP or framing policy enables injection/clickjacking. | Strict directive expectations, `frame-ancestors`, report sanitization. |
| P5.7-T44 | Token, secret, private data, or evidence content enters browser storage. | Storage API instrumentation and prohibited-field scanning. |
| P5.7-T45 | Sensitive values leak through URL, title, history, referrer, or clipboard. | Prohibited-field and route-parameter tests; no sensitive copy controls. |
| P5.7-T46 | Cross-window message accepts an untrusted origin or stale source. | Exact origin/source/version/nonce contract and close-time teardown. |
| P5.7-T47 | Telemetry attributes contain identifiers or unbounded attacker content. | Allowlisted low-cardinality keys, length/count bounds, redaction, drop accounting. |
| P5.7-T48 | Screenshots, traces, console, or test reports retain sensitive material. | Generated-only fixture marker, bounded capture, redaction, zero sensitive retention. |

### Authorization And Truth

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T49 | Client visibility or disabled controls are mistaken for authorization. | Server-capability contract required; deep-link and direct-command denial tests. |
| P5.7-T50 | Query cache or aggregate exposes another department. | Department-bound keys, responses, pagination, aggregates, events, and teardown. |
| P5.7-T51 | Resource profile, browser, or locale changes action eligibility. | Invariance matrix across all selected dimensions. |
| P5.7-T52 | Hypothesis, candidate, score, or relationship is shown as confirmed truth. | Typed visual/semantic separation and prohibited-claim assertions. |
| P5.7-T53 | Evidence integrity is presented as proof, guilt, or admissibility. | Orthogonal state labels, limitations, and forbidden wording tests. |
| P5.7-T54 | Review outcome directly triggers notification, dispatch, or enforcement. | No executor adapter/route; command and bundled-string absence checks. |
| P5.7-T55 | Administrative preview appears effective or executable. | Non-effective marker, unavailable action, receipt semantics, no executor. |
| P5.7-T56 | System health or security score is represented as complete safety/compliance. | Source/freshness/completeness/limitation qualifiers and unknown state. |

### Supply Chain, Build, And Acceptance

| ID | Threat | Required control/evidence |
| --- | --- | --- |
| P5.7-T57 | Lockfile and installed dependency tree differ. | Exact lockfile, package manifest, integrity, installed-tree, and SBOM reconciliation. |
| P5.7-T58 | Vulnerability data is stale but described as clean. | Observation timestamp/source and explicit no-refresh limitation. |
| P5.7-T59 | Unlicensed or unexpected transitive dependency enters the build. | License/SBOM allowlist and dependency diff gate. |
| P5.7-T60 | Source maps or forbidden endpoints/data appear in release bundles. | Artifact inventory and forbidden-content scan for every app/chunk. |
| P5.7-T61 | Provenance exists but does not match artifact/source expectations. | Subject digest, source, builder, build type, parameters, and signature/trust status. |
| P5.7-T62 | Repeatable local build is mislabeled reproducible or SLSA compliant. | Exact terminology and independent-builder requirement for stronger claims. |
| P5.7-T63 | Historical Phase 0-P5.6 evidence is rewritten to make final tests pass. | Git-object hash checks and additive compatibility transitions only. |
| P5.7-T64 | Owner acceptance is recorded against the wrong or incomplete package. | Exact package digest, component digest, technical commit, limitations, and separate statement. |

## Severity And Exit Policy

- T01-T08, T17-T24, T33-T56, and T57-T64 are release-blocking when their
  associated requirement applies.
- Performance-budget misses may use an owner-approved, scoped, expiring
  exception only if no authority, privacy, truth, data-loss, or accessibility
  requirement is weakened.
- Accessibility, authorization, department isolation, evidence integrity,
  unsupported-claim, operational-action, and immutable-history failures cannot
  be waived in the recommended baseline.
- A missing runtime or environment is `blocked` or `unsupported`, never a
  pass. Whether it blocks final Phase 5 acceptance is controlled by the owner
  decision profile and recorded limitations.

## Validation Boundary

The planned tests use generated fixtures and loopback-only browser processes.
They cannot prove backend enforcement, PostgreSQL RLS, production headers,
network segmentation, real browser fleet compatibility, physical-device or
assistive-technology support, camera/media behavior, model behavior,
Government integration, security accreditation, or deployment readiness.
