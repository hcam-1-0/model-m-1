# P5.7 Official Research Record

Status date: 2026-09-12

Status: official primary-source research complete; owner decisions and implementation remain closed

## Purpose

This record translates official accessibility, browser-testing, localization,
performance, HTTP, security, observability, secure-development, and software
supply-chain sources into planning constraints for P5.7 Quality, Scale, And
Final Acceptance. It is not a WCAG, GIGW, OWASP, NIST, SLSA, CycloneDX,
browser-support, production-readiness, or security-conformance claim.

The accepted Phase 0 through P5.6 contracts remain authoritative. P5.7 tests
and reports the system that exists; it does not widen operator authority,
invent missing producers, convert generated evidence into real evidence, or
silently redefine earlier acceptance records.

## Research Method

- official primary technical, standards, government, and project sources only;
- current repository and dependency manifests inspected read-only;
- no dependency resolution, download, install, build, browser execution,
  provider access, camera/media access, model execution, container,
  Kubernetes, deployment, or remote Git action;
- source conclusions translated into testable planning requirements;
- draft standards are explicitly identified and cannot support a conformance
  claim by themselves.

## Source Register And P5.7 Consequences

| Source | Primary conclusion | P5.7 consequence |
| --- | --- | --- |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | WCAG 2.2 adds AA requirements including focus not obscured, dragging alternatives, minimum target size, and accessible authentication. | Target WCAG 2.2 AA, preserve keyboard alternatives and visible focus, test 200% and 400% zoom/reflow, and never let a generated automated result alone become a conformance claim. |
| [WCAG-EM 2.0](https://www.w3.org/TR/WCAG-EM/) | Evaluation requires defined scope, target, accessibility-support baseline, representative sampling, evaluation, and reporting. | Freeze portal/view scope, browser and assistive-technology baseline, sampled and universal checks, exceptions, evidence, evaluator identity, and limitations before final acceptance. |
| [W3C ACT Rules](https://www.w3.org/WAI/standards-guidelines/act/rules/) | ACT rules can be automated, semi-automated, or manual and are informative rather than the normative basis of WCAG conformance. | Map automated findings to rule IDs when possible, but keep manual keyboard, focus, semantics, zoom, and screen-reader protocols as separate evidence lanes. |
| [ARIA Authoring Practices keyboard guidance](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) | Composite widgets need predictable keyboard conventions, visible focus, and a clear distinction between focus and selection. | Test every table, tab, menu, dialog, tree-like relationship view, toolbar, and monitor-wall control for entry, internal navigation, escape, focus restoration, and no keyboard trap. |
| [ARIA modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Modal dialogs require focus to move inside, remain contained, and return sensibly on close. | All review, conflict, confirmation, and proposal dialogs require deterministic initial focus, labelled purpose, bounded content, escape/close behavior, and focus return. |
| [GIGW 3.0 accessibility guidance](https://guidelines.india.gov.in/accessibility-guidelines-and-attributes/) | Indian government web guidance adopts WCAG-derived accessibility requirements and text alternatives for non-text content. | GIS, charts, camera status, relationships, timelines, topology, and media status retain complete authoritative table/list alternatives. |
| [W3C Internationalization Quick Tips](https://www.w3.org/International/quicktips/index.en) | Use UTF-8, declare language, support local formats, avoid sentence fragments, and validate localized content. | Test English, Gujarati, and Hindi messages with declared language, Unicode content, expansion, truncation, date/number/time formatting, and no concatenated grammar assumptions. |
| [ECMAScript Internationalization API](https://tc39.es/ecma402/) | Locale-sensitive date, time, number, list, and relative-time behavior is standardized through `Intl` and explicit options such as time zone. | Freeze explicit locale and time-zone fixtures; never infer incident ordering from formatted text; record canonical UTC/event/record time separately from localized display. |
| [Playwright browser guidance](https://playwright.dev/docs/browsers) | Playwright supports Chromium, Firefox, WebKit, Chrome, Edge, and project-based browser configurations. | Use a tiered browser matrix: all critical journeys on Chromium, Firefox, and WebKit; installed Edge as the Windows operator baseline; unavailable engines become explicit limitations, not passes. |
| [Playwright emulation guidance](https://playwright.dev/docs/emulation) | Browser projects can emulate viewport, device, touch, locale, timezone, permissions, and color scheme. | Define deterministic laptop, tablet, mobile, desktop, control-room, locale, timezone, touch, color-scheme, and reduced-motion projects while distinguishing emulation from physical-device evidence. |
| [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds) | LCP, INP, and CLS describe load, responsiveness, and visual stability; the commonly used good thresholds are LCP at most 2.5 s, INP at most 200 ms, and CLS at most 0.1 at the 75th percentile. | Use these as reference budgets for generated loopback evidence, label the evidence synthetic and non-field, and add operator-specific budgets for map idle, query fan-out, table response, and media admission. |
| [Long Tasks API](https://www.w3.org/TR/longtasks-1/) | Tasks of at least 50 ms can block the main thread and degrade interaction responsiveness. | Record count, duration, and phase of long tasks during bounded journeys where the browser supports the API; unsupported attribution is a limitation, never fabricated. |
| [HTTP Semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) | Strong ETags and `If-Match` prevent lost updates; conditional requests have defined precedence. | Test strong ETag propagation, 412 conflict handling, refetch, comparison, reconsideration, and no automatic consequential retry across review and governance workflows. |
| [Problem Details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | Problem Details provides machine-readable HTTP errors and warns against exposing implementation internals. | Validate stable problem type, status, title, safe detail, instance/reference boundaries, retry metadata, localization behavior, and redaction across every portal. |
| [Content Security Policy Level 3](https://www.w3.org/TR/CSP3/) | CSP constrains resources and security-relevant browser behavior; the current Level 3 publication is still a Working Draft. | Validate an explicit production policy projection and report-only-to-enforce transition plan without claiming CSP3 conformance or changing headers during planning. |
| [OWASP CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) | CSP is defense in depth against script injection, framing, and cross-site leaks. | Plan nonce/hash-capable strict policies, `frame-ancestors`, object blocking, scoped media/map destinations, violation sanitization, and tests proving no inline-policy regression. |
| [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) | Cookie-authenticated state changes need framework defenses, tokens or signed patterns, origin/fetch-metadata checks, safe methods, and XSS prevention. | Every consequential command test requires non-GET semantics, CSRF defense projection, same-origin policy, origin/fetch-metadata handling, and rejection evidence; P5.7 does not implement the backend defense. |
| [OWASP HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html) | Browser communication and storage APIs require origin validation, minimization, and careful handling of sensitive information. | Prohibit token, credential, evidence, personal, raw telemetry, and operational payload persistence in local/session storage, IndexedDB, caches, URLs, history, clipboard, or cross-window messages. |
| [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/) | ASVS 5.0 provides versioned, testable web-application security requirements. | Use exact `v5.0.0` requirement references where mapped, keep threat-to-test traceability, and state clearly that P5.7 does not establish ASVS certification or complete production verification. |
| [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final) | Secure software practices belong throughout the SDLC and should address vulnerabilities and their root causes. | Final evidence must bind source, dependencies, tests, known vulnerabilities, unresolved risks, remediation ownership, build inputs, and repeatable procedures rather than only a passing UI run. |
| [OpenTelemetry specification](https://opentelemetry.io/docs/specs/) | Telemetry signals use defined context and schemas, with versioned behavior. | Validate trace/correlation propagation and schema identity while preserving separate operational, security, audit, administrative, and evidence lanes. Adapters remain default-off. |
| [OpenTelemetry attribute limits](https://opentelemetry.io/docs/specs/otel/common/) | Attribute collections need uniqueness and bounds to prevent memory exhaustion and unpredictable processing. | Test allowlisted low-cardinality attributes, bounded value lengths/counts, no resource-specific identifiers as labels, truncation/drop accounting, and redaction before export. |
| [SLSA 1.2](https://slsa.dev/spec/v1.2/) | SLSA defines supply-chain tracks, levels, provenance, and verification expectations. | Bind source commit, build process, inputs, output digest, builder observation, and limitations; do not claim a SLSA level without the required trusted platform and verification. |
| [SLSA artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts) | Provenance only helps when subject, signature, builder identity, source, build type, and external parameters are verified against expectations. | Final release planning separates provenance presence from provenance verification and fails closed on subject/input mismatch or unrecognized build parameters. |
| [CycloneDX specification](https://github.com/CycloneDX/specification) | CycloneDX can represent components, dependencies, services, vulnerabilities, licenses, and attestations in a versioned BOM. | Verify the existing SBOM against the exact lockfile and artifact inventory, record completeness and freshness, and avoid claiming current vulnerability safety when no refresh occurred. |

## Repository Findings

The accepted local workspace currently contains:

- eight independently buildable applications: Command, GIS, Operations,
  Intelligence, Investigation, Evidence, Admin, and Security;
- two distinct Operations domains: camera/live operations and Platform
  Operations;
- 37 shared packages;
- 94 non-browser TypeScript test files and 29 Playwright browser
  specifications;
- locked Playwright 1.63.0, axe-core 4.13.0, Vitest 5.0.0, Vite 8.2.2,
  TypeScript 5.9.3, React 19.2.8, Storybook 10.6.0, MapLibre 6.7.0,
  deck.gl 9.4.0, and hls.js 1.7.2;
- an existing 90 percent branch/function/line/statement coverage threshold;
- existing application bundle budgets for Admin, Security, and Operations,
  but no single final all-portal budget manifest;
- a Playwright baseline that currently uses installed Edge/Chromium-style
  execution and viewport projects, not an accepted three-engine compatibility
  result;
- generated-only data and default-off network/media/telemetry boundaries that
  P5.7 must preserve.

These findings support a final quality layer built mostly with the existing
locked toolchain. They also expose missing final evidence: cross-portal replay,
three-engine compatibility, complete all-portal budgets, WCAG-EM-style scope
and reporting, localization parity, end-to-end resilience, release
provenance, and one canonical limitations register.

## Reconciled Planning Principles

1. **One quality manifest:** every requirement, portal, journey, browser,
   locale, viewport, profile, threat, test, result, limitation, and artifact
   has a stable ID and one source-of-truth manifest.
2. **Generated remains generated:** no synthetic replay, browser emulation,
   fixture, or loopback result is described as field, Government, camera,
   hardware, production, or operational evidence.
3. **Layered evidence:** static, contract, component, integration, browser,
   manual protocol, build, supply-chain, and immutable-history results remain
   distinguishable.
4. **No green-by-omission:** skipped, unsupported, unavailable, blocked,
   stale, unobserved, and not applicable are explicit states, never passes.
5. **Authoritative alternatives:** maps, graphs, timelines, charts, video,
   wall layouts, and topology retain equivalent lists/tables and non-visual
   workflows.
6. **Truth and authority invariance:** browser, locale, viewport, resource
   profile, rendering adapter, and degraded mode cannot change data scope,
   evidence meaning, review requirements, or action eligibility.
7. **Deterministic replay:** a manifest fixes seed, virtual clock, identifiers,
   event order, expected state revisions, evidence digests, and terminal
   assertions.
8. **Risk-based breadth:** every portal receives smoke, accessibility,
   localization, security, and degraded-state coverage; critical journeys get
   full cross-browser and cross-profile depth.
9. **Budgets are gates with context:** every performance result names the
   browser, viewport, profile, workload, warm/cold condition, iteration count,
   statistic, hardware limitation, and unsupported metric.
10. **Final acceptance is project-specific:** owner acceptance closes Phase 5
    against the sealed H-CAM scope and limitations. It does not create a legal,
    regulatory, standards, production, or deployment certification.

## Explicit Non-Claims

P5.7 planning does not claim:

- WCAG, WCAG-EM, ACT, ARIA, GIGW, OWASP ASVS, NIST SSDF, SLSA, CycloneDX,
  CSP3, Core Web Vitals, or OpenTelemetry conformance;
- support for a browser, assistive technology, physical device, language,
  hardware profile, camera count, stream count, or deployment not actually
  observed under a later authorized validation run;
- field performance, production capacity, Government integration, live CCTV,
  operational safety, security accreditation, legal admissibility, or fitness
  for enforcement;
- absence of vulnerabilities because a vulnerability database was not
  refreshed;
- reproducibility merely because two local builds happen to match.

## Research Outcome

P5.7 should be a manifest-driven final verification system, not a new portal.
It should reuse the locked toolchain, add no runtime dependency by default,
exercise all nine operator surfaces through deterministic generated journeys,
and produce an exact evidence graph whose failures, skips, environment gaps,
and unsupported claims are as visible as its passes.

Research and planning earn no product points. P5.7 remains **0/12
(0.0000%)** and Phase 5 remains **88/100 (88.0000%)**.
