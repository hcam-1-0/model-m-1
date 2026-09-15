# P5.4 Dependency Evaluation

Status: planning evaluation only; no dependency installation or lockfile change

## Existing Foundation

The accepted frontend already includes React, React Router, TanStack Query,
React Aria Components, React Intl, Zod-equivalent generated contract checks,
OpenAPI tooling, MapLibre, deck.gl, Lucide, Vitest, Playwright, Storybook,
axe-core, and the shared H-CAM packages. P5.4 should reuse those dependencies
for queues, detail views, spatial projections, accessibility, validation,
icons, and event-driven invalidation.

No additional dependency is required for the evidence tables, review desk,
chronology, rule trace, candidate matrix, or state handling.

## Relationship Graph Candidates

| Candidate | Strengths | Risks | Planned role |
| --- | --- | --- | --- |
| Native table plus simple deterministic SVG | No new dependency; complete semantic control | Layout and interaction logic would become custom domain code; poor scaling | Authoritative table is mandatory; custom SVG is not preferred for the enhanced graph |
| `@xyflow/react` / React Flow | DOM-based nodes, React integration, keyboard focus and selection support, configurable ARIA text, bounded graph suitable for analyst drill-down | Primarily a node-workflow library; must disable editing, dragging, delete semantics, and misleading defaults; exact version/security review needed | Recommended bounded enhanced relationship renderer behind an H-CAM adapter |
| Cytoscape.js | Mature graph model, layout extensions, events, headless layouts, graph algorithms | Canvas rendering needs a separate accessible authority; algorithms could invite unauthorized client inference; additional adapter/testing cost | Strong fallback if future graph-analysis needs are explicitly authorized |
| Sigma.js plus Graphology | WebGL rendering for very large graphs and MapLibre integration options | Higher complexity, weaker semantic accessibility at the canvas, excessive for a deliberately bounded initial graph | Future high-capability profile evaluation only; not baseline |

## Recommendation

Adopt an internal `RelationshipGraphRenderer` contract first. Under a later
exact P5.4 start authorization, resolve one pinned React Flow version for the
bounded enhanced projection while retaining the authoritative table as the
complete workflow. Configure the graph as read-only:

- no node creation, deletion, reconnection, or arbitrary dragging;
- no graph-computed identity, risk, confidence, centrality, or relationship;
- server-provided typed nodes and edges only;
- hard caps on nodes, edges, depth, labels, and layout time;
- deterministic stable layout or server-provided positions;
- localized ARIA labels and visible keyboard focus;
- synchronized selection with node and edge tables;
- complete teardown and no protected browser persistence;
- low-resource table-first fallback;
- dependency kill switch and renderer-independent domain tests.

Do not install React Flow during planning. The start package must bind its
exact package name, version, integrity, license, transitive dependency set,
vulnerability snapshot, bundle impact, and approved paths.

## Spatial Rendering

P5.4 should add no spatial dependency. Reuse the P5.2 GIS domain with MapLibre
for the base 2D map and deck.gl only for accepted bounded overlays. The map is
an enhancement; synchronized tables remain authoritative. No tile or provider
network is authorized by this plan.

## Rule Graphs

The rule evaluation view is not a rule editor. It should use existing UI
primitives for a deterministic, bounded node trace and table. If the selected
relationship renderer can represent the typed rule trace without weakening
semantics or increasing bundle cost, it may be reused through a separate
adapter. P5.4 must not add a second graph dependency solely for rule display.

## Chronology And Tables

Use semantic HTML and React Aria Components where they fit existing patterns.
Virtualization is not recommended initially because P5.4 queues are
server-paginated and bounded; virtualization can complicate focus, screen
reader position, and deterministic screenshots. A future measured case may
authorize a pinned virtualization dependency without changing the table API.

## Client-State Policy

Use TanStack Query for server projections and invalidation. Keep review drafts,
stale conflict copies, and selected comparison state in memory. Do not add a
global state library or browser persistence dependency for P5.4. URL state may
contain only allowlisted non-sensitive queue filters and opaque refs; no
reasons, evidence, scores, provider values, or command tokens.

## Explanation And Text Generation

P5.4 requires no LLM or text-generation dependency. Explanations are
deterministic projections of exact rule revisions, typed evaluation traces,
evidence roles, and limitations. Any future generated narrative must remain
secondary, attributable, testable against the exact trace, and separately
authorized.

## Rejected Planning Shortcuts

- One large graph library as the source of truth.
- A client-side graph database or identity-resolution engine.
- Automatic layout-derived risk or relationship metrics.
- Storing reviewer drafts in local storage or IndexedDB.
- Query-string bearer tokens or protected route state.
- General workflow automation or notification dependencies.
- Unbounded table virtualization before measured need.
- A second map stack separate from the accepted P5.2 GIS domain.

## Start-Package Supply-Chain Gate

Any new dependency must have exact version and integrity pinning, official
source and release provenance, license compatibility, bounded transitive tree,
offline lockfile evidence after resolution, vulnerability scan result or
explicit refresh limitation, bundle-size budget, CSP compatibility, teardown
test, and rollback path. A failed or unavailable check stops dependency
adoption without blocking the authoritative table implementation.
