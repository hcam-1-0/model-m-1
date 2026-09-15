# Phase 5 Operator Application Research Record

Status date: 2026-09-06

Status: official-source research complete for P5.0 owner decisions; planning
only

## Authority And Method

`D-P5.0-PLAN-AUTH` authorizes official primary-source research and read-only
repository analysis for the Phase 5 Operator Application. Sources were used to
derive requirements and decision options, not to claim implementation,
conformance, operational fitness, or deployment readiness.

Research was limited to standards bodies, specification publishers, and
official project documentation. No camera, media, Sentinel, provider,
Government, private-data, model, container, cluster, or deployment endpoint
was contacted.

## Accepted Repository Starting Point

The planning baseline is accepted Phase 4 closeout commit
`96a902315e78c184e92df9ebe5bcef1e336eab38`. The Phase 4 handoff provides:

- 16 canonical HTTP operation contracts;
- 6 event contracts;
- 2 generated workflow contracts;
- 11 UI states;
- 9 accessibility requirements;
- pinned OpenAPI, AsyncAPI, CloudEvents, Arazzo, compatibility, claim,
  limitation, reconstruction, and evidence projections;
- explicit statements that Phase 5 was not implemented and server-side
  authorization remains authoritative.

Earlier accepted APIs also expose camera registry, stream inventory and
health, probe history, capability snapshots, playback-session issuance,
analytics assignment, geometry/rule, generated tracking, alert, integration,
investigation, and operations surfaces. There is no frontend package,
JavaScript lockfile, TypeScript source, or production operator UI in the
accepted baseline.

## Official Primary Sources

### Accessibility And Interaction

| Source | Guidance used | H-CAM planning implication |
| --- | --- | --- |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Focus not obscured, alternatives to dragging, minimum target size, accessible authentication, names/roles/values, error identification, and programmatic status messages | Target Level AA where applicable; define keyboard, focus, target, contrast, authentication, error, and live-update evidence before visual implementation |
| [WAI-ARIA Authoring Practices patterns](https://www.w3.org/WAI/ARIA/apg/patterns/) | Expected semantics and keyboard behavior for grids, dialogs, tabs, toolbars, feeds, trees, menus, and status patterns | Use native HTML first; where composite widgets are required, define focus ownership and keyboard behavior explicitly |
| [WAI-ARIA Grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) | Interactive grids require managed directional focus and differ materially from ordinary tables | Use semantic tables for read-only results; select an interactive grid only when cell-level interaction justifies the additional focus model |
| [WAI-ARIA Tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) | Tabs require linked tab/tab-panel semantics and defined keyboard activation | Do not use visual tab styling without the complete interaction contract |

WCAG is a conformance standard. APG is design guidance and explicitly is not
itself a W3C Recommendation-track conformance specification. Automated checks
cannot replace manual keyboard, assistive-technology, contrast, zoom, target,
and workflow testing.

### Browser Authentication And Application Security

| Source | Guidance used | H-CAM planning implication |
| --- | --- | --- |
| [RFC 10017, OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017.html) | Browser application threat model, backend-for-frontend patterns, authorization code with PKCE, exact redirects, token risks, and rejection of implicit flow | Prefer a same-origin backend-for-frontend or equivalent server-managed session for the operator UI; do not persist bearer tokens in general browser storage |
| [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html) | Current OAuth attack mitigations, PKCE, CSRF defenses, exact redirect handling, and deprecated grants | Authentication decisions require a separately accepted identity provider and exact flow; implicit and password grants are not options |
| [Content Security Policy Level 3](https://www.w3.org/TR/CSP3/) | Resource and script restrictions as defense in depth against injection | Plan strict CSP, no uncontrolled remote scripts, no inline execution by default, and explicit media/map origins; CSP remains defense in depth |
| [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) | Testable web security requirements across authentication, session, access control, validation, and communications | Use ASVS as a verification input, not a compliance claim; bind the exact version only in a later start package |
| [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | Least privilege, session controls, event logging, privileged-function auditing, and protection of audit information | Preserve server authorization, explicit privileged-action evidence, session boundaries, and separation of security, audit, and evidence records |

The CSP3 document is a working draft as of this research date. A future start
package must pin tested browser behavior and cannot present draft use as a
standards-conformance claim.

### GIS And Spatial Presentation

| Source | Guidance used | H-CAM planning implication |
| --- | --- | --- |
| [OGC API Features](https://www.ogc.org/standards/ogcapi-features/) | Resource-oriented, fine-grained access to spatial features, WGS 84 core behavior, discovery, and bounded query | Plan viewport/bounds/time filters and feature-level retrieval instead of loading a city-scale dataset into the browser |
| [OGC API Tiles](https://ogcapi.ogc.org/tiles/overview.html) | Standard building blocks for vector, map, imagery, and other geospatial tiles | Use a tile-source abstraction and explicit attribution; do not bind Phase 5 to a single commercial tile provider |
| [OGC API Maps](https://ogcapi.ogc.org/maps/overview.html) | Styled map representations with spatial subsetting and reusable web API building blocks | Separate authoritative feature data from rendered base-map imagery and style policy |
| [MapLibre GL JS documentation](https://maplibre.org/maplibre-gl-js/docs/) | WebGL vector-tile rendering, style documents, workers, controls, and CSP requirements | MapLibre is a strong 2D candidate, subject to later dependency, accessibility, browser, CSP, and license review |
| [MapLibre large-data guidance](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/) | Chunking, clustering, vector tiling, bounded zoom, and simpler styles reduce browser workload | Capability profiles should bound features, layers, labels, tiles, and update frequency; full raw GeoJSON is not the scale strategy |

No OGC conformance is claimed. Existing H-CAM camera records provide paired
latitude/longitude fields, but the current API is not an OGC API Features or
Tiles implementation.

### Live Media And Playback

| Source | Guidance used | H-CAM planning implication |
| --- | --- | --- |
| [RFC 8216, HTTP Live Streaming](https://www.rfc-editor.org/rfc/rfc8216.html) | Playlist and segmented media behavior with adaptive bitrate capability | HLS is the compatibility path where supported; playlists and segments must remain behind server-issued playback authority |
| [Media Source Extensions](https://www.w3.org/TR/media-source/) | Browser APIs for JavaScript-managed segmented and adaptive media playback | A future HLS adapter can use native playback or a reviewed MSE-based implementation without exposing camera locators |
| [WebRTC 1.0](https://www.w3.org/TR/webrtc/) | Browser real-time media APIs and privacy/security implications including IP and local-network exposure | Low-latency mode requires explicit transport, privacy, candidate, timeout, and cleanup controls |
| [WHEP Internet-Draft](https://datatracker.ietf.org/doc/draft-ietf-wish-whep/) | Proposed HTTP signaling for WebRTC egress viewers | Treat WHEP as a version-pinned experimental adapter because it remains work in progress, not a published RFC |

H-CAM already has a server-issued playback-session contract. Phase 5 should
consume that contract and never expose raw RTSP, ONVIF, secret references, or
camera management locators to browser code. No media was accessed in this
research.

### Frontend Architecture, Data, And Performance Candidates

| Source | Guidance used | H-CAM planning implication |
| --- | --- | --- |
| [Vite guide](https://vite.dev/guide/) | Modern browser development, typed plugin API, monorepo-resolvable dependencies, multi-page support, and explicit browser targets | Vite is a strong candidate for independently buildable portal applications in one workspace; exact version and target remain undecided |
| [Vite production build guidance](https://vite.dev/guide/build) | Explicit build targets, static asset output, base-path handling, and legacy-browser tradeoffs | Browser support must be an owner decision and tested matrix, not whatever the tool default happens to be |
| [TanStack Query retry guidance](https://tanstack.com/query/latest/docs/framework/react/guides/query-retries) | Query retries and backoff are configurable and can otherwise occur automatically | H-CAM must override generic retry behavior by safe failure class; denied, validation, conflict, and unsafe mutations are never automatically retried |
| [MapLibre performance metrics example](https://maplibre.org/maplibre-gl-js/docs/examples/display-performance-metrics/) | Map load, idle, frame, and resource timing can be observed | Collect low-cardinality client performance evidence without camera, location, operator, or record identifiers |
| [Long Tasks API](https://www.w3.org/TR/longtasks-1/) | Long main-thread tasks can block interaction and can be observed | Define interaction responsiveness and long-task budgets for dense maps, grids, timelines, and multi-video workspaces |
| [Event Timing API](https://www.w3.org/TR/event-timing/) | Measures processing-to-presentation latency for user interactions | Future quality gates should measure interaction latency, not only bundle size or first render |

Candidate project documentation is not a dependency approval. Framework,
package manager, component primitives, data grid, state library, map renderer,
and media adapter remain explicit owner decisions and later start-package
pins.

## Research Conclusions

1. **Use role-oriented applications over shared foundations.** A modular
   monorepo can provide independently buildable portals without the runtime
   complexity of microfrontends on day one.
2. **Prefer a same-origin security boundary.** A backend-for-frontend or
   equivalent server-managed session materially reduces browser token
   exposure and centralizes security headers, CSRF, logout, and API policy.
3. **Server state is authoritative.** HTTP resources and ETags provide current
   truth. Events trigger bounded invalidation; they cannot grant authority or
   become an unverified parallel state store.
4. **The map is a query surface, not decoration.** Viewport, time, layer,
   department, and result bounds must drive retrieval. Clustering and tiling
   prevent unbounded client loading.
5. **Live media needs typed adapters.** HLS is the broad compatibility lane;
   WebRTC/WHEP is a low-latency candidate. Both consume short-lived playback
   sessions, enforce cleanup, and expose bounded health state.
6. **WHEP remains provisional.** The current IETF document is an active draft;
   H-CAM must version-pin the adapter and retain fallback behavior.
7. **High capability cannot mean weaker safety.** Hardware-aware profiles may
   increase visual density and parallel rendering only within server and
   deployment budgets.
8. **Accessibility begins in contracts.** Data grids, maps, timelines, video,
   dialogs, and continuously updating lists need complete keyboard, focus,
   status, error, alternative-view, and reduced-motion behavior.
9. **Generic client retries are unsafe.** Query and mutation retry policy must
   follow H-CAM reason codes, idempotency, ETag, and lifecycle semantics.
10. **No persistent sensitive offline cache by default.** A future service
    worker may cache immutable application assets, but API responses, tokens,
    camera metadata, intelligence records, evidence, and media are excluded
    unless a separate threat model and authority approve them.
11. **Observe the client without identifying the operator or subject.** Client
    telemetry should be low-cardinality, sampled, bounded, and separated from
    audit/evidence records.
12. **Contract gaps must block screens.** A mockup cannot create an implied API
    or operational action. Every view is marked supported, partially
    supported, or blocked until the producer contract exists.

## Explicit Non-Claims

- No frontend stack, package, version, identity provider, map provider, media
  server, tile server, event transport, or deployment topology is selected.
- No UI, API client, test, build, route, component, design token, or generated
  fixture was implemented.
- No browser, accessibility, performance, security, map, media, or multi-
  monitor validation was executed.
- No WCAG, WAI-ARIA, OAuth, OIDC, CSP, OWASP, NIST, OGC, HLS, MSE, WebRTC,
  WHEP, OpenAPI, AsyncAPI, CloudEvents, or Arazzo conformance is claimed.
- No real data, camera, media, model, provider, operational action,
  infrastructure, deployment, or remote Git activity occurred.

## Research Status

P5.0 repository analysis and official-source research are **2/2 planning
items (100.0000%)**. This earns **0 Phase 5 product points**. Phase 5 remains
**0/100 (0.00%)** until a later accepted implementation satisfies frozen
completion criteria.
