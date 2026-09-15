# P5.1 Shared Application Foundation Research Record

Status: official primary-source research complete; owner decisions pending

Research date: 2026-09-06

Authority: `D-P5.1-PLAN-AUTH`

## Research Boundary

This record covers only public, official technical, security, accessibility,
browser, framework, standards, and dependency sources. No source repository
was imported, no package was installed, no lockfile was changed, and no
frontend, map, media, provider, or product runtime was executed.

The findings guide a future P5.1 start package. They do not select or authorize
dependencies by themselves. Exact versions, integrity, license, provenance,
vulnerability status, browser support, and build output must be sealed at the
future start gate because those facts can change after this research date.

## Workspace And Runtime

### React

- React's official version page identifies React 19.2 as the current major and
  minor documentation line.
- H-CAM should adopt a currently supported React release only after a pinned
  compatibility and supply-chain review at P5.1 start.
- No React Server Components or compiler capability is required for P5.1.

Sources:

- https://react.dev/versions
- https://react.dev/community/versioning-policy

### Node, Vite, TypeScript, And Workspace Management

- Node recommends production applications use an Active LTS or Maintenance LTS
  release. Node 24 is the current LTS line on the research date.
- Vite supports monorepo-based setups and documents explicit Node and browser
  baselines. Those baselines must become machine-checked start-package inputs.
- TypeScript `strict` enables the family of strict type-checking behavior and
  should be mandatory for shared contracts and portal packages.
- pnpm workspaces provide an explicit workspace root, strict local package
  references through `workspace:`, one shared lockfile, and catalogues for
  centrally managed dependency versions. Cyclic workspace dependencies should
  be prohibited.

Sources:

- https://nodejs.org/en/about/previous-releases
- https://vite.dev/guide/
- https://www.typescriptlang.org/tsconfig/strict.html
- https://pnpm.io/workspaces
- https://pnpm.io/catalogs

## Routing And Independently Buildable Portals

- React Router documents Declarative, Data, and Framework modes. Data Mode adds
  loaders, actions, pending states, and data APIs while retaining control over
  bundling and server abstractions.
- P5.1 can use Data Mode for route manifests, guarded navigation, bootstrap,
  error boundaries, and deep links without turning route loaders into a second
  resource cache.
- Portal boundaries must be verified by dependency-graph checks: applications
  may consume shared packages, but one portal may not import another portal.

Source:

- https://reactrouter.com/start/modes

## API Contracts, Validation, And Errors

- OpenAPI 3.1 aligns schema handling with JSON Schema 2020-12. The exact
  dialect and schema revision must be pinned rather than inferred.
- `openapi-typescript` and `openapi-fetch` provide a small typed client path,
  but generated TypeScript does not validate untrusted runtime responses.
- Ajv supports JSON Schema 2020-12 through a distinct validator class and does
  not allow mixing that dialect with older drafts in one instance. H-CAM should
  compile strict standalone boundary validators for the exact accepted schema
  dialect.
- RFC 9457 defines machine-readable HTTP problem details. The UI must map only
  allowlisted fields and safe H-CAM reason codes; raw upstream details,
  locators, identifiers, stack traces, and payload fragments stay out of the
  browser-visible error model.

Sources:

- https://spec.openapis.org/oas/v3.1.1.html
- https://openapi-ts.dev/openapi-fetch/
- https://ajv.js.org/json-schema.html
- https://datatracker.ietf.org/doc/html/rfc9457

## Server State, Freshness, And Events

- TanStack Query v5 supports colocated typed query definitions, invalidation,
  retries, cancellation, pagination, and network modes.
- Library defaults cannot become H-CAM policy. Every operation needs an
  explicit registry for freshness, cache duration, retry eligibility,
  cancellation, polling fallback, and sensitive-data persistence.
- HTTP remains authoritative. WebSocket or future event messages may only
  invalidate or present bounded non-authoritative projections. Gaps,
  reconnects, unknown versions, duplicates, and ordering uncertainty trigger
  HTTP revalidation.
- Experimental cross-tab query broadcasting and persistent query plugins are
  excluded from the recommended baseline.

Source:

- https://tanstack.com/query/latest/docs/framework/react/guides/query-options

## Security And Session Boundary

- OWASP recommends synchronizer tokens for stateful applications, custom
  request headers for API-driven clients, and SameSite, Origin/Referer, and
  Fetch Metadata checks as defense in depth rather than substitutes for CSRF
  tokens.
- Session identifiers belong in `Secure`, `HttpOnly`, narrowly scoped cookies.
  A `__Host-` cookie is preferred where deployment topology permits its path,
  Secure, and no-Domain requirements.
- The browser never receives camera locators, credentials, provider secrets,
  long-lived bearer tokens, raw audit payloads, or source evidence bytes.
- CSP should be delivered as an HTTP header, prohibit inline/eval use by
  default, and explicitly bind workers, media, images, connections, frames,
  and scripts to approved same-origin paths. Exact directives require later
  build evidence.

Sources:

- https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie

## Accessibility And Design Primitives

- WCAG 2.2 is the normative accessibility target. Automated tooling cannot
  establish conformance by itself.
- WAI-ARIA Authoring Practices supplies interaction and keyboard guidance, but
  APG examples are not a replacement for semantic native HTML and testing.
- React Aria Components provide unstyled, accessible, internationalized
  behavior suitable for wrapping behind H-CAM-owned component contracts.
- H-CAM components must preserve native semantics first, expose visible focus,
  support forced colors and reduced motion, and include authoritative list or
  table alternatives for map, graph, timeline, grid, and media surfaces.

Sources:

- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/WAI/ARIA/apg/patterns/
- https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- https://react-aria.adobe.com/getting-started

## Localization And Time

- React Intl builds on the ECMAScript Internationalization APIs and ICU message
  syntax. It is suitable for parameterized, pluralized, date, number, and
  relative-time output across English, Gujarati, and Hindi.
- Message IDs must be stable and descriptive. Source text is not a message ID.
- API timestamps remain canonical UTC instants with explicit timezone metadata;
  the client formats them for the operator locale and selected operational
  timezone without changing event chronology.
- Catalogue completeness, pseudo-localization, long text, missing-message
  failure, script rendering, and fallback behavior require explicit evidence.

Source:

- https://formatjs.github.io/docs/react-intl/

## GIS And Capability Profiles

- The accepted MapLibre target now requires WebGL2. Its current migration
  guidance says map construction fails with `GPUInitializationError` when
  WebGL2 is unavailable.
- Therefore WebGL capability is an admission check, not permission to remove
  functionality. The authoritative accessible list/table and filter workflow
  must remain complete when the map is unavailable.
- The Media Capabilities API can report whether a declared media configuration
  is supported, smooth, and power efficient. It may inform a later playback
  profile but may not grant authorization or prove a real stream will advance.
- Raw hardware details must not be collected for profile selection. Use coarse,
  purpose-bound observations, a server policy ceiling, session-local behavior,
  and a safe low-resource default.

Sources:

- https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/
- https://www.w3.org/TR/media-capabilities/

## Testing And Observability

- Vitest supports multiple test projects; deprecated workspace terminology
  should not be used for new configuration.
- Playwright emulation covers viewport, device, locale, timezone, color scheme,
  reduced motion, forced colors, and related browser conditions.
- Storybook accessibility testing can evaluate rendered component stories, but
  its documentation explicitly notes that automated tools find only a portion
  of WCAG issues. Manual keyboard and assistive-technology evidence remains a
  release gate.
- OpenTelemetry JavaScript documents browser instrumentation as experimental.
  P5.1 should define an internal low-cardinality signal contract and a
  default-off OTel-compatible adapter rather than letting an experimental
  browser SDK become the authoritative application interface.

Sources:

- https://vitest.dev/guide/projects
- https://playwright.dev/docs/emulation
- https://storybook.js.org/docs/writing-tests/accessibility-testing
- https://opentelemetry.io/docs/languages/js/

## Research Conclusions

1. Use one dependency-locked workspace with independently buildable portal
   applications and one-way dependencies into shared packages.
2. Keep HTTP, the BFF session, server authorization, department scope, ETags,
   idempotency, and accepted outcomes authoritative.
3. Validate untrusted boundary data at runtime even when generated TypeScript
   types compile.
4. Keep state, retry, freshness, and invalidation policy operation-specific.
5. Use native-first, unstyled accessible primitives behind H-CAM-owned APIs.
6. Make English, Gujarati, and Hindi catalogues part of the first component,
   not a later translation pass.
7. Default capability selection to the complete low-resource experience;
   acceleration changes density or quality, never authority or core function.
8. Preserve the existing Gujarat GIS experience and its accessible alternative
   under the accepted parity-first, no-downgrade contract.
9. Keep browser observability low-cardinality, minimized, and adapter-based.
10. Require exact dependency, license, SBOM, vulnerability, provenance,
    browser, accessibility, and build evidence before implementation credit.

## Non-Claims

This research does not establish dependency approval, browser compatibility,
WCAG conformance, CSP correctness, production security, GIS parity, map or
media support, performance, operational readiness, or deployment readiness.
Those claims require later implementation and accepted evidence.
