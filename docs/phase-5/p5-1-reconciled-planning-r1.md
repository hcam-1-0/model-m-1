# P5.1 Reconciled Planning R1

Status: non-effective; exact owner planning acceptance pending

Decision profile: `B/A/A/A/A/A/A/A/A/A/A/A`

Source package: `P5.1-PLANNING-R0`

## Reconciliation Result

The owner selected all twelve recommended options. P5.1 therefore retains the
architecture, threat controls, implementation workstreams, progress weights,
GIS adoption requirements, and closed gates documented in R0. No composite or
conflicting choice requires precedence rules, and no P5.0 or P5.1 rebaseline is
required.

This R1 document turns the selected options into one unambiguous shared
application foundation profile. It remains planning only. It does not
authorize source creation or import, dependency changes, implementation,
testing, build, runtime, network access, data, media, models, operational
actions, containers, Kubernetes, deployment, P5.2, commit, or remote Git.

## Binding Architecture Profile After Acceptance

### Workspace And Builds

- Use one pnpm workspace with one lockfile, centrally governed catalogues, and
  `workspace:` references for all internal packages.
- Preserve independently buildable Command, Operations, Intelligence,
  Investigation, Evidence, Admin, and Security portal applications.
- Prohibit portal-to-portal imports, cyclic workspace dependencies, undeclared
  dependencies, and internal-path imports that bypass package exports.
- Pin exact supported Node LTS, pnpm, React, TypeScript, Vite, and tool versions
  only in the later start package after current provenance and security review.
- Require independent clean builds, deterministic manifests, bundle budgets,
  source-map controls, license records, SBOM, vulnerability evidence, and
  reproducible build evidence before P5.1 acceptance.

### Shell, Navigation, And Routing

- Use React Router Data Mode with static typed route manifests.
- Use route loaders only for shell bootstrap, compatibility, session, access
  preflight, pending navigation, and route-level failures.
- Keep resource data in the governed query layer to preserve one cache and one
  HTTP authority model.
- Give every route an owning portal, capability requirement, department scope,
  operation set, safe URL contract, localized title, focus behavior, UI states,
  multi-window rule, and data-exposure class.
- Unknown, malformed, incompatible, or unauthorized routes fail closed.

### Design System And Accessibility

- Use native semantic HTML first.
- Wrap React Aria Components behind H-CAM-owned component APIs for complex
  interaction behavior while H-CAM owns visual tokens and state semantics.
- Preserve the approved NETRA SENTINEL visual identity and dense operational
  hierarchy rather than substituting a generic enterprise component theme.
- Treat WCAG 2.2 AA as the target and WAI-ARIA Authoring Practices as
  interaction guidance, with automated and mandatory manual evidence.
- Preserve keyboard, focus, zoom, reflow, forced-colors, reduced-motion,
  target-size, contrast, and list/table equivalence requirements.

### API And Contract Boundary

- Pin accepted OpenAPI 3.1 inputs and their JSON Schema dialect.
- Generate TypeScript operation/path types and a small typed fetch client.
- Compile strict JSON Schema 2020-12 runtime validators for every untrusted
  request, response, event, route, preference, session, capability, and error
  boundary.
- Map RFC 9457 problems to bounded H-CAM error states, retaining no raw payload,
  locator, stack trace, identity, free text, or secret material.
- Permit network access only through same-origin, allowlisted operation IDs.

### Server State, Concurrency, And Events

- Use TanStack Query behind an H-CAM operation policy registry.
- Declare explicit freshness, cache lifetime, retry, cancellation, polling,
  invalidation, redaction, and persistence policy for every operation.
- Default mutation retries off; require reason, ETag, idempotency,
  confirmation, and accepted server outcomes where the producer contract
  requires them.
- Keep HTTP authoritative. Events may invalidate or carry clearly labeled,
  non-authoritative projections only.
- Use bounded HTTP revalidation on event gap, reconnect, duplicate, reorder,
  unknown version, policy change, or department change. Polling remains a
  complete fallback.

### Session, CSRF, Authorization, And Department Context

- Use a same-origin BFF with a `Secure`, `HttpOnly`, `SameSite` host cookie.
- Use a server-issued synchronizer CSRF token held in memory and sent through a
  custom request header, with Origin/Referer and Fetch Metadata defense in
  depth.
- Model idle and absolute expiry, logout, role/department change, and step-up
  reauthentication as explicit states.
- Treat client capabilities as presentation projections only; the server
  reauthorizes every request.
- Cancel requests, disconnect event channels, clear resource and draft memory,
  and complete a new bootstrap before a changed department context can render.

### Localization And Time

- Use React Intl and ICU message syntax.
- Make English, Gujarati, and Hindi catalogues mandatory from the first shared
  component.
- Use stable message IDs, catalogue completeness checks, pseudo-localization,
  long-text, missing-message, script, fallback, and human-review evidence.
- Preserve canonical timestamps and explicit operational timezone projection;
  never derive event ordering or business logic from localized strings.

### Capability And Resource Profiles

- Start from a functionally complete safe-low profile.
- Intersect it with the server policy ceiling, operator and department
  capability, build support, coarse browser feature checks, and bounded
  session-local health.
- Use WebGL2 checks only to admit map rendering and Media Capabilities only to
  advise later media profile selection.
- Do not collect raw CPU/GPU/vendor identity or create a durable device
  fingerprint.
- Allow enhanced workstation and control-room profiles to increase density,
  quality, and bounded concurrency, but never authority, data access, review
  semantics, freshness, provenance, or accessibility.

### Persistence And Multi-Window Behavior

- Keep session, resource, command draft, event projection, error, and sensitive
  state in memory.
- Permit only bounded opaque identifiers and enums in typed URLs.
- Permit only harmless, versioned, TTL-limited display preferences in local
  browser storage.
- Store meaningful workspaces on the server with version and ETag control.
- Treat control-room windows as independent resource consumers. Do not
  broadcast sensitive state or query caches across windows.

### Observability

- Use an H-CAM-owned, low-cardinality, payload-free client signal contract.
- Provide a default-off OpenTelemetry-compatible adapter rather than making an
  experimental browser SDK the application interface.
- Prohibit identities, resource IDs, URLs, coordinates, search terms, free
  text, payloads, raw errors, credentials, locators, and evidence references in
  client telemetry.

### Testing And Evidence

- Use tiered generated contract/unit/component tests, a governed component and
  UI-state catalogue, automated accessibility checks, browser and visual
  evidence, security tests, and manual accessibility evidence.
- Maintain a quick low-resource development profile and a complete evidence
  profile. Both enforce the same contracts and safety rules.
- Keep planning, technical implementation, evidence acceptance, and owner
  acceptance as separate measurable gates.

### Existing Final-UI Adoption

- Adopt only through a later hash-bound, attributed, exact-scope source
  authorization.
- Keep imported reference source outside production builds.
- Extract tokens, shell behavior, and workflows into governed target packages.
- Port Command, Live, and GIS as separate slices with visual, interaction,
  responsive, accessibility, resource, safety, and security parity evidence.
- Retain the reference until each relevant parity gate is accepted.
- Preserve the existing Gujarat GIS as the canonical operator experience under
  the accepted parity-first, no-downgrade contract.

## Frozen P5.1 Workstreams

| Workstream | Points | Completion after acceptance |
| --- | ---: | ---: |
| P5.1-W1 Workspace and build policy | 1.5 | P5.1 12.5000%; Phase 5 9.5000% |
| P5.1-W2 Shell, navigation, and routing | 1.5 | P5.1 25.0000%; Phase 5 11.0000% |
| P5.1-W3 Design system and accessibility | 1.5 | P5.1 37.5000%; Phase 5 12.5000% |
| P5.1-W4 Typed contracts, API, and errors | 1.5 | P5.1 50.0000%; Phase 5 14.0000% |
| P5.1-W5 Session, authorization, and context | 1.5 | P5.1 62.5000%; Phase 5 15.5000% |
| P5.1-W6 Server state, concurrency, and events | 1.5 | P5.1 75.0000%; Phase 5 17.0000% |
| P5.1-W7 Localization, profiles, and windows | 1.5 | P5.1 87.5000%; Phase 5 18.5000% |
| P5.1-W8 Observability, adoption, validation, and acceptance | 1.5 | P5.1 100.0000%; Phase 5 20.0000% |

No partial product credit is earned inside a workstream. Weight changes require
an explicit rebaseline.

## Required Start Package

After exact R1 planning acceptance, a separate non-effective start package may
freeze:

- implementation branch and base commit;
- exact additive and bounded synchronization paths;
- exact package graph and public exports;
- exact toolchain and dependency versions, integrity, license, provenance,
  scripts, vulnerability state, and browser baseline;
- exact accepted producer-contract inputs and compatibility ranges;
- generated-only fixture manifest and prohibited-field corpus;
- exact lint, typecheck, build, test, browser, accessibility, security,
  supply-chain, evidence, and clean-source commands;
- laptop quick-profile and complete-evidence resource bounds;
- authorized historical compatibility transitions;
- remediation cycle limit, fail-closed stop conditions, evidence paths,
  rollback, and local commit policy.

The start package must remain non-effective until separately accepted by the
owner. Planning acceptance cannot authorize implementation by implication.

## Progress

- P5.1 owner decisions: **12/12 (100.0000%) selected**.
- P5.1 planning reconciliation: **complete as non-effective R1**.
- P5.1 planning acceptance: **pending**.
- P5.1 implementation: **0/12 points (0.0000%)**, change **+0.0000 percentage
  points**.
- Phase 5 product: **8/100 points (8.0000%)**, change **+0.0000 percentage
  points**.

Decision selection and planning reconciliation earn no product points.

## Next Gate

The owner must accept the exact `P5.1-PLANNING-R1` package and its canonical
component digest. That acceptance may permit preparation of one separate,
non-effective P5.1 start package. It does not itself authorize implementation.
