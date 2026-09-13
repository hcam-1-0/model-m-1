# P5.5 Dependency Evaluation

Status date: 2026-09-09

Status: planning complete; no dependency change authorized

## Existing Foundation

The locked frontend already includes React, React Router, TanStack Query,
React Aria Components, React Intl, Lucide, AJV, OpenAPI tooling, the shared H-CAM
shell/contracts/query/event/observability packages, and the internal bounded
graph approach used by P5.4. These are sufficient for an initial generated-only
P5.5 implementation.

## Timeline Rendering

### Baseline Recommendation

Use server-bounded pagination with a native semantic table/list. An optional
visual timeline lane may window only the rows already fetched for the current
page. Record sequence, page anchors, selection, focus, result count, and
reading order remain authoritative.

Advantages:

- no dependency or lockfile change;
- bounded browser memory and DOM size;
- predictable focus and screen-reader behavior;
- no false assumption that virtualization replaces server pagination;
- functionally complete low-resource mode.

### TanStack Virtual

The official [TanStack Virtual documentation](https://tanstack.com/virtual/latest/docs/api/virtualizer)
supports stable item keys, anchored scrolling, measurement, and bounded visible
items. The official [virtualization guide](https://tanstack.com/table/latest/docs/framework/react/guide/virtualization)
also states that virtualization is not a substitute for server-side pagination,
filtering, or sorting.

Evaluation: useful as a later optional enhancement after producer pagination
exists and keyboard/screen-reader behavior passes explicit browser testing. It
is not installed and is not required for P5.5 start.

### React Spectrum TableView

Adobe's official [TableView documentation](https://react-spectrum.adobe.com/react-spectrum/TableView.html)
includes accessibility and automatic virtualization, but adopting it would add
a second component-system layer and additional packages beyond the existing
React Aria Components baseline.

Evaluation: reject for P5.5. The benefit does not justify design-system,
dependency, bundle, testing, and migration cost.

## Graph And Provenance Rendering

Reuse the P5.4 internal bounded read-only graph adapter with authoritative node
and edge tables. Provenance adds typed entity/activity/agent nodes and edge
families but does not require new layout or graph dependencies.

The graph is optional in low-resource mode. It has no source resolution,
mutation, export, or truth authority.

## Query And Event State

The installed [TanStack Query](https://tanstack.com/query/latest/docs/reference/QueryClient)
supports scoped query keys, invalidation, refetch, cancellation, and clearing.
P5.5 should use:

- department, purpose, contract version, resource, filters, page, order, and
  through-revision in query keys;
- scoped event invalidation followed by HTTP confirmation;
- cancellation and cache removal on session/scope/capability change;
- no persistence plugin and no sensitive browser storage;
- immutable cache updates only for local presentation state, never server
  authority.

## Comparison And Diff Rendering

Use typed field-change contracts and ordinary tables. A generic text-diff or
JSON-tree dependency would blur semantic field types, risk rendering sensitive
unknown fields, and encourage raw-payload display.

Recommendation: no diff dependency. Render only an allowlisted typed projection
with added/changed/inactive/unknown labels.

## Cryptography And Canonicalization

Do not add browser cryptography, signature, timestamp, hashing, or JSON
canonicalization packages. P5.5 consumes named algorithm/profile/result fields
from accepted contracts. The browser is not an integrity authority and cannot
access source bytes.

## PROV Interchange

Do not add RDF, JSON-LD, ontology, graph database, or PROV parser dependencies.
The accepted Phase 4.5 projection is generated, lossy, export-only in concept,
and import-disabled. P5.5 displays its status and typed rows only.

## Document And Media Rendering

PDF, image, video, audio, office-document, archive, and text-preview libraries
are prohibited because P5.5 does not resolve or render source evidence. The
existing HLS/media stack remains isolated to P5.3 and receives only an opaque
handoff when separately authorized.

## Recommended Dependency Decision

1. Use the existing locked dependency baseline for initial implementation.
2. Require server pagination before any large-timeline performance claim.
3. Keep an adapter boundary for optional TanStack Virtual evaluation later.
4. Add no graph, diff, crypto, PROV, media, document, storage, or export
   dependency.
5. Any future dependency requires an exact start-package amendment, registry
   metadata, integrity, license, SBOM, vulnerability, build, bundle, and
   accessibility evidence.

## Rejected Planning Shortcuts

- loading all 10,000 possible timeline entries into the browser;
- using client-side sorting to represent the entire investigation;
- raw JSON viewers for unknown producer fields;
- browser-generated hashes or legal certificates;
- iframe/object/embed source previews;
- graph-only provenance;
- localStorage/sessionStorage persistence of investigation data or drafts;
- an export/download library for preview-only manifests.
