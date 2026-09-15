# P5.2 Command And Situational Awareness Research Record

Status date: 2026-09-07

Status: official primary-source research complete; no runtime or implementation performed

Authority: `D-P5.2-PLAN-AUTH`

## Research Questions

The research answers the decisions that materially affect a command-center GIS:

1. How should a large, bounded 2D feature set be transported and rendered?
2. What equivalent experience is required when a map cannot be used?
3. Which state remains authoritative when events, caches, or sources disagree?
4. How should concurrency, failures, and stale data be represented?
5. Which browser, security, accessibility, and observability constraints must be frozen before implementation?

## Official Sources And Findings

| Source | Planning finding | P5.2 application |
| --- | --- | --- |
| [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Keyboard access, visible and unobscured focus, reflow, non-text contrast, status messages, and non-color cues are independently testable requirements. | Map controls, filters, drill-downs, tables, banners, and workload updates require explicit keyboard, focus, zoom, contrast, and announcement behavior. |
| [W3C Reflow understanding](https://www.w3.org/WAI/WCAG22/Understanding/reflow) | A two-dimensional map can qualify for a limited reflow exception, but the exception does not remove the obligation to keep surrounding content usable or to provide an alternative where needed. | The map may pan in two dimensions; the rest of the workspace must reflow, and the synchronized list/table remains a complete route to the same records. |
| [W3C Non-text Contrast understanding](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | Meaningful graphical objects and states need adequate contrast; a data table may communicate the same information when a complex graphic cannot. | Camera health, coverage, freshness, alert state, and selection must not depend on hue alone. Patterns, icons, labels, borders, and the authoritative list carry equivalent meaning. |
| [WAI-ARIA APG Grid Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) | An interactive grid is a composite widget with application-managed focus and keyboard behavior. A plain table is simpler where cell-level interaction is unnecessary. | Default to semantic tables and ordinary controls. Use a grid only for a proven dense interaction and implement its complete keyboard model. |
| [MapLibre GL JS documentation](https://maplibre.org/maplibre-gl-js/docs/) | MapLibre GL JS is a TypeScript/WebGL renderer for vector-tile maps with a style specification and extensible controls. Its current guidance documents same-origin worker configuration for strict CSP deployments. | Keep MapLibre behind the accepted renderer-neutral adapter. Use a same-origin worker asset, local style manifest, no direct provider credentials, and no required public basemap. Exact version remains a start-package decision. |
| [MapLibre large-data guide](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/) | Reduce feature properties, load data by URL where appropriate, use vector tiling for larger data, and use clustering to reduce rendered points. | Use bounded summaries for small viewports and server-generated vector tiles for larger sets. Keep detail out of map payloads and resolve it through authoritative detail operations. |
| [MapLibre clustering example](https://maplibre.org/maplibre-gl-js/docs/examples/cluster/) | Point clustering is an established display technique. | Clusters may reduce visual load but never become operational facts, counts outside their declared window, or a substitute for server-owned coverage analytics. |
| [OGC API Features](https://ogcapi.ogc.org/features/) | The Core building block defines read-only discovery and query of spatial features over web APIs. | Shape a bounded, read-only viewport feature contract with explicit collection, extent, CRS, pagination, and time filters, without claiming conformance before testing an exact implementation. |
| [OGC API Tiles](https://ogcapi.ogc.org/tiles/) | The standard defines interoperable tiled resources and tile-set metadata for maps, features, and coverages. | Plan a typed tile-set/style manifest and bounded vector-tile route. The browser does not choose arbitrary tile origins. |
| [RFC 7946 GeoJSON](https://www.rfc-editor.org/rfc/rfc7946.html) | GeoJSON uses WGS 84 longitude/latitude coordinates and defines feature, geometry, and bounding-box structures. | Normalize viewport exchange to WGS 84 longitude/latitude, validate bounds and geometry type, and reject ambiguous coordinate order. Internal PostGIS geometry may use an explicit SRID. |
| [PostGIS ST_MakeEnvelope](https://www.postgis.net/docs/ST_MakeEnvelope.html) and [ST_Intersects](https://postgis.net/docs/en/ST_Intersects.html) | PostGIS provides explicit bounding envelopes and spatial predicates; spatial predicates can participate in indexed queries. | A future producer can enforce viewport bounds with an envelope and index-aware predicates. P5.2 planning does not add the route or migration. |
| [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) | Problem Details provides a machine-readable HTTP error shape while warning against leaking implementation detail. | Reuse the P5.1 safe problem mapping and add only typed P5.2 reason codes; no raw provider, SQL, tile, locator, or security detail reaches the browser. |
| [RFC 9110 If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match) | `If-Match` supports conditional requests and prevents lost updates for state-changing operations. | P5.2 overview remains read-only. A future saved workspace or handoff mutation must use ETags and explicit conflict handling rather than last-write-wins. |
| [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) and [attribute guidance](https://opentelemetry.io/docs/specs/semconv/how-to-write-conventions/) | Stable semantic attributes improve interoperability; unbounded and sensitive values should not become telemetry dimensions. | Client signals use low-cardinality portal, view, operation, state, renderer, and profile names. Camera IDs, coordinates, query text, departments, users, and record identifiers are excluded from labels. |
| [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | Authorization should be deny-by-default, validated on every request, and tested for horizontal and vertical privilege failures. | UI route visibility is only a projection. Every summary, feature, list, detail, and future workspace request remains department-scoped and server-authorized. |
| [W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/) | CSP is a browser enforcement layer for controlling resource destinations and script execution. | A future map implementation must bind worker, style, glyph, sprite, tile, image, and connection origins explicitly. It must not widen the P5.1 no-arbitrary-destination policy. |

## Repository Evidence Considered

- P5.1 implements the independently buildable Command portal shell, capability profiles, typed client, query policy, authorization projection, localization, observability, generated mock service, and renderer-neutral GIS contract.
- `D-P5.0-GIS-ADOPTION-001` makes the existing Gujarat GIS experience the canonical Phase 5 GIS UX under parity-first, no-downgrade adoption.
- Phase 4.7 hands off 16 generated-only HTTP operations, 6 invalidation events, 2 workflows, 11 UI states, and 9 accessibility requirements.
- Camera and stream catalogue, detail, health, probe, and capability APIs exist under department-scoped server authorization, but browser-safe command aggregates do not yet cover every P5.2 need.

## Conclusions

1. Use a hybrid delivery model: bounded feature queries for small interactive viewports, vector tiles for larger spatial sets, and authoritative paginated lists for complete record access.
2. Keep server responses authoritative. Events invalidate cached queries; they do not mutate operational truth directly.
3. Treat freshness, completeness, source loss, corrections, and degradation as first-class fields. Never infer an overall healthy state from missing sources.
4. Preserve GIS parity in information architecture and interactions, while replacing unsafe or unbounded source assumptions with typed H-CAM contracts.
5. Keep the initial map 2D and renderer-neutral. Do not require 3D, public basemaps, client-side geometry analytics, or a second geospatial library.
6. Keep the command surface read-only in P5.2. Human review and lifecycle mutations remain in their authoritative workflows.

## Non-Claims

- No MapLibre, OGC, WCAG, PostGIS, or OpenTelemetry conformance is claimed.
- No dependency was installed or executed.
- No map, tile, provider, camera, media, private, or Government endpoint was contacted.
- No browser, performance, hardware, accessibility-technology, or multi-monitor runtime test was performed.
- No production capacity, latency, SLO, or coverage accuracy is claimed.
