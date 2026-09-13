# P5.7 Dependency And Toolchain Evaluation

Status date: 2026-09-12

Status: existing locked dependency baseline recommended; no dependency or runtime action authorized

## Decision

The recommended P5.7 implementation should add no frontend or Python runtime
dependency. The accepted workspace already contains the primary tools needed
for contract, component, browser, accessibility, coverage, build, bundle,
localization, map, media, and evidence validation.

P5.7 may extend source, fixtures, manifests, test configuration, and evidence
scripts only under a later exact start authorization. Planning authorization
does not permit executing those tools or changing the lockfile.

## Accepted Locked Baseline

| Capability | Existing exact dependency/tool | Planned use |
| --- | --- | --- |
| Unit/component/generated tests | Vitest 5.0.0, Testing Library, user-event, jsdom | Contract, pure-domain, component, hostile-input, and generated matrix tests |
| Branch coverage | V8 coverage through Vitest | Preserve at least the accepted 90 percent workspace thresholds; define stricter coverage for new final-quality policy logic if added |
| Browser automation | Playwright 1.63.0 | Edge/Chromium baseline, Chromium/Firefox/WebKit projects, viewport/locale/timezone/emulation, traces on failure |
| Automated accessibility | axe-core 4.13.0 and Storybook a11y 10.6.0 | Rule-based automated checks with explicit tool/version and manual-evidence separation |
| Accessible components | React Aria Components 1.21.1 plus native HTML/shared UI | Preserve keyboard/focus semantics; tests remain authoritative, not the dependency name |
| Localization | react-intl 10.1.26 and platform `Intl` | English/Gujarati/Hindi message, expansion, number/date/time/list formatting |
| API/contract validation | Zod patterns, AJV 8.20.0, openapi-fetch 0.17.0, openapi-typescript 7.13.0 | Versioned schemas, safe problems, compatibility, bounded generated inputs |
| GIS | MapLibre 6.7.0 and deck.gl 9.4.0 | Local generated map/overlay behavior with table fallback and no provider/tile network |
| Media | hls.js 1.7.2 and accepted media adapters | Generated HLS admission, fallback, stall, and teardown only |
| Build and lint | Node 24.18.0, pnpm 11.21.0, TypeScript 5.9.3, Vite 8.2.2, ESLint 10.10.0, Prettier 3.9.6 | Exact toolchain identity, typecheck, lint, build, bundle, formatting, repeatability evidence |
| Icons and shared UI | Lucide React 1.41.0, shared design tokens/UI/app shell | Existing visual language and stable accessible controls |
| Python repository verification | Existing pytest/Ruff/JSON/hash tooling | Planning/readiness/history/evidence validation with no new package |

## Browser Runtime Distinction

An npm dependency is not a browser runtime. Playwright's package may be locked
while Chromium, Firefox, or WebKit binaries are absent or a different version.
The later start package must bind:

- exact Playwright package and expected browser revisions;
- actual installed executable source, version, and availability;
- whether a browser is bundled, system-installed, or unavailable;
- whether any download would be required;
- whether Edge channel identity is independently observed;
- the policy for a missing required engine.

Recommended policy: do not download automatically. Stop the required matrix
cell as `blocked_runtime_unavailable` and require a separate exact amendment
for any browser acquisition.

## Existing Tooling Gaps That Do Not Require New Dependencies

| Need | Planned change under future start | Why no new dependency is needed |
| --- | --- | --- |
| Cross-portal journey orchestration | Extend Playwright fixtures and generated manifests | Playwright already supports projects, contexts, emulation, traces, and assertions |
| Pairwise matrix generation | Add a deterministic in-repo pure generator | Factors are bounded; a small reviewed generator is more auditable than a new package |
| Performance observation | Use browser Performance APIs and Playwright timing | Core timings, layout shifts, resource timing, and supported long-task observations are available without a vendor SDK |
| Bundle budgets | Generalize the existing bundle verifier | Current script already inventories artifacts, source maps, markers, and selected budgets |
| Accessibility reporting | Normalize axe output plus manual protocol records | axe-core is present; WCAG-EM-style scoping/reporting is a contract problem, not a package problem |
| SBOM reconciliation | Parse existing JSON with current Node/Python tooling | P5.7 validates an existing SBOM; it does not need to generate a new format through a library |
| Evidence graph | Use bounded canonical JSON manifests and hash scripts | A graph database or provenance SDK would add unnecessary runtime and trust scope |
| Reproducibility comparison | Hash normalized build outputs and manifests | Requires exact process/environment controls, not another package |
| Security header validation | Static expected-policy contract plus loopback response checks if later authorized | No crawler or external scanner is needed for the generated milestone |

## Optional Tools Evaluated And Deferred

### Lighthouse

Potential value:

- standardized browser lab audits;
- familiar performance and accessibility summaries;
- useful diagnostics for load and best-practice regressions.

Why it is not required initially:

- it adds a dependency/tool/runtime surface and Chromium-specific assumptions;
- its score can hide individual metric regressions and is not a production
  field measurement;
- axe, Playwright, browser Performance APIs, and explicit H-CAM budgets provide
  more direct requirement traceability;
- a single aggregate score is unsuitable as an acceptance gate.

Recommendation: keep an optional future diagnostic lane only. Do not make a
Lighthouse score a release claim or replace explicit budgets with it.

### Additional accessibility scanners

Potential value: independent rule implementations and broader issue discovery.

Why deferred: automated scanners overlap, still cannot establish WCAG
conformance, and can multiply false positives and evidence formats. The
recommended baseline is axe plus semantic tests plus manual protocols. An
independent scanner can be introduced later as a separately versioned evidence
lane, never by silently merging scores.

### Visual-regression services

Potential value: hosted baseline management, review workflows, and browser
render comparisons.

Why deferred: external network, account, image retention, privacy, cost, and
baseline-authority concerns conflict with the generated local milestone.
P5.7 should prefer bounded local screenshots for failures and semantic/layout
assertions. Pixel baselines may be evaluated later for a sanitized design
system subset.

### Load-testing tools

Potential value: high concurrency, HTTP load, and distributed capacity tests.

Why deferred: P5.7 C1/C10/C50 is generated client/workflow scale, not backend
or infrastructure capacity. k6, Locust, JMeter, or similar tools would widen
runtime/network scope without an authorized production-like backend.

### Security scanners and browser proxies

Potential value: DAST, dependency refresh, header checks, and attack discovery.

Why deferred: scanner execution, network access, vulnerability refresh, and
production security testing are outside the authorization. P5.7 can validate
static security contracts, generated hostile inputs, and existing dependency
evidence only. Missing scan evidence remains a limitation.

### SBOM/provenance signing tools

Potential value: standard BOM generation, signatures, attestations, and
verification.

Why deferred: tool trust, key custody, builder identity, signing policy, and
artifact distribution need a release-engineering decision. P5.7 can design and
validate exact manifests without claiming signed provenance or a SLSA level.

## Future Dependency Admission Gate

Any new dependency or tool requires a separate exact decision and must record:

- package/tool name, exact version, source, integrity, and acquisition method;
- license and transitive dependency impact;
- lockfile, installed-tree, SBOM, and bundle changes;
- vulnerability observation source and timestamp;
- maintenance, release cadence, platform/browser support, and abandonment risk;
- accessibility, security, privacy, determinism, performance, and retention
  consequences;
- offline/cache behavior and network destinations;
- reproducible invocation, rollback, and removal plan;
- why existing locked tooling is insufficient.

## Recommendation

Select an existing-toolchain-first P5.7 baseline. Expand Playwright projects,
axe/manual protocols, generated manifests, explicit budgets, and canonical
evidence with no dependency change. Treat absent browser engines,
vulnerability refresh, physical devices, assistive technology, independent
builders, and external scanners as explicit gated environments rather than
silently acquiring or simulating them.
