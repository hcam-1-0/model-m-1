# P5.5 Owner Decision Packet

Status date: 2026-09-09

Status: twelve owner decisions pending; no option authorizes implementation

Selections must be recorded as `D-P5.5-001:A` through `D-P5.5-012:A` or with
another explicit option. Recommended options preserve the strongest accepted
architecture and the current generated-only boundary.

## D-P5.5-001: Product And Portal Topology

### A. Connected Investigation Center with separately authorized Evidence Desk, recommended

Command Center remains primary. Investigation Center owns timeline,
reconstruction, corrections, and relationships. Evidence Desk is a connected
route/domain with an independent authorization check. This supports rich
enterprise pages without making evidence access implicit.

### B. Put investigations and evidence inside Intelligence Center

Fewer portals, but analytical hypotheses and investigation records become too
easy to confuse and Intelligence Center becomes overloaded.

### C. Separate Investigation and Evidence applications

Strong isolation, but duplicates shell, navigation, handoffs, state, and testing
for the first implementation.

### D. One universal case canvas

Flexible but weakens typed workflows and encourages client-side composition of
unbounded or differently authorized data.

## D-P5.5-002: Investigation Work Organization

### A. Bounded typed views with server aggregates and saved filters, recommended

Use recent changes, correction pending, reconstruction incomplete, evidence
unavailable, review required, and policy-preview states. Counts and sorts remain
server authoritative.

### B. One chronological list of all investigations

Simple but poor for triage and hides freshness, gaps, and workload types.

### C. Client-side joined universal queue

Feature-rich appearance but incomplete, resource-heavy, and unsafe across
different authorization domains.

### D. Search-only workspace

Reduces UI surface but prevents proactive handling of corrections and stale
investigations.

## D-P5.5-003: Chronology Authority

### A. Record-sequence authority plus qualified event-time view, recommended

Monotonic record sequence determines append history. Event time is an asserted
view with source, range/precision, clock state, ties, and unknown values.

### B. Event time as the only order

Looks natural but permits backdating, clock disagreement, and unknown time to
misrepresent the historical record.

### C. Record time only

Safe for history but removes useful event-context analysis.

### D. User-selectable order without authority label

Flexible but invites screenshots and interpretations without knowing which
chronology is shown.

## D-P5.5-004: Large Timeline Rendering

### A. Server-paginated semantic table plus optional bounded visual lane, recommended

Native table/list is authoritative. Stable anchors preserve focus and reading
order. A visual lane may window the current page. No new dependency is required.

### B. Add TanStack Virtual immediately

Can render more client rows efficiently but still needs server pagination and
adds dependency, accessibility, measurement, and browser-test obligations.

### C. Infinite scroll only

Fluid for mouse use but weak for deterministic page references, keyboard
navigation, reconstruction evidence, and returning to an exact entry.

### D. Render the full timeline

Straightforward but unsafe at the accepted 10,000-entry bound.

## D-P5.5-005: Reconstruction And Comparison

### A. Exact-revision reconstruction with typed field comparison and late-change warnings, recommended

The server/contract supplies the exact revision and digest. Users compare two
revisioned projections while later corrections, missing components, and
limitations remain visible.

### B. Client replay from cached events

Fast but cannot be authoritative after missed events, pagination, schema drift,
or corrections.

### C. Current-state snapshot only

Simpler but fails the core reconstruction objective.

### D. AI-generated historical narrative

Readable but non-deterministic and capable of inventing chronology or omitting
contradictions.

## D-P5.5-006: Correction, Retraction, And Impact Presentation

### A. Append-only predecessor/successor view with per-target impact closure, recommended

Show original and correction/retraction together, exact fields, authority,
reason, revision, and pending/applied/blocked/failed/superseded impacts. Stale
downstream views remain locked or visibly incomplete.

### B. Replace corrected values in the timeline

Cleaner appearance but erases what was previously known or relied upon.

### C. Corrections on a separate hidden history page

Preserves data but lets current views conceal important changes.

### D. Automatically reverse reviews and relationships

Reduces manual work but creates unauthorized conclusions and side effects.

## D-P5.5-007: Evidence State Presentation

### A. Orthogonal state matrix, recommended

Display reference identity, availability, digest observation, provenance
closure, custody history, signature/timestamp observation, access, and legal
assessment separately with source, time, method, freshness, and limitations.

### B. One `verified` badge

Compact but dangerously collapses different technical and legal meanings.

### C. Raw integrity and provenance JSON

Exact but inaccessible, easy to misread, and may expose unknown sensitive
fields.

### D. Evidence confidence score

Convenient for ranking but has no accepted semantics and would create a false
evidentiary conclusion.

## D-P5.5-008: Provenance And Custody Visualization

### A. Bounded typed graph plus authoritative node/edge/custody tables, recommended

Reuse the internal graph adapter. Preserve entity/activity/agent and typed
relations. Show custody as a separate timeline with gaps. Generated PROV is a
lossy projection; import and conformance claims remain disabled.

### B. Tables only

Strong accessibility and lower cost but makes complex derivation paths harder
to scan.

### C. Graph only

Visually rich but inaccessible and prone to relationship overclaim.

### D. External graph database/browser

Powerful but adds infrastructure, data replication, authorization, and
deployment scope not justified in P5.5.

## D-P5.5-009: Source And Media Boundary

### A. Opaque reference only with no resolution or rendering, recommended

Evidence Desk displays minimized metadata and explicit source-not-resolved and
media-not-rendered states. A future source resolver or media handoff requires a
separate producer contract and authorization.

### B. Resolve metadata headers only

Could improve freshness but still creates network, credential, source-policy,
SSRF, and access risks outside this phase.

### C. Inline media and document preview

Useful to investigators but directly violates the accepted no-copy/no-render
boundary.

### D. Download source to a local evidence cache

Potentially performant but creates an unapproved evidence store, custody,
retention, deletion, and security system.

## D-P5.5-010: Retention, Hold, Deletion, And Export Experience

### A. Generated non-operative Policy Preview Studio, recommended

Show policy references, exact targets, conflicts, per-target simulated outcomes,
residuals, inclusion/exclusion reasons, and completeness. Keep execution,
approval, signing, delivery, download, and print absent.

### B. Hide all policy-related views

Lowest risk but prevents testing the accepted Phase 4.5 contracts and operator
understanding of lifecycle state.

### C. Enable hold and deletion actions for administrators

Operationally useful but requires legal policy, separation of duties, storage
adapters, audit, recovery, and deployment authority not present here.

### D. Create downloadable reference-only export files

Still creates a derivative and recipient/purpose security boundary; it is not
authorized by a preview contract.

## D-P5.5-011: Concurrency, Events, And Draft Recovery

### A. Strong ETag plus revision plus idempotency receipt; events invalidate only, recommended

Bound drafts to exact state, refetch on conflict, show differences, and require
reconsideration. Events mark scoped queries stale and HTTP confirms authority.

### B. Optimistic client cache is authoritative

Responsive but unsafe for append-only evidence history and concurrent review.

### C. Polling only

Reliable and simple but slower and more expensive; retain only as event-gap
fallback.

### D. Last write wins with toast notification

Simple but can erase or misattribute consequential changes.

## D-P5.5-012: Dependency, Accessibility, Security, And Validation Baseline

### A. Existing locked dependencies plus deterministic generated-only layered validation, recommended

Use semantic pages, table/graph equivalence, C1/C10/C50 generated workloads,
contract tests, component tests, browser keyboard/accessibility tests, scope and
cache teardown tests, threat coverage, all-portal builds, and full regression.
Reserve one P5.5 point for exact owner acceptance.

### B. Add virtualization, graph, diff, crypto, and document libraries up front

Enables more features but expands supply-chain and browser risk before producer
contracts exist.

### C. Unit tests and manual visual review only

Too narrow for chronology, focus, scope isolation, concurrency, and overclaim
risks.

### D. Validate with real investigations and evidence

Would provide realism but is prohibited and unnecessary for initial contract/UI
validation.

## Recommended Selection Statement

```text
D-P5.5-001: A
D-P5.5-002: A
D-P5.5-003: A
D-P5.5-004: A
D-P5.5-005: A
D-P5.5-006: A
D-P5.5-007: A
D-P5.5-008: A
D-P5.5-009: A
D-P5.5-010: A
D-P5.5-011: A
D-P5.5-012: A
```

This selection records architecture preferences only. It does not authorize a
dependency, route, migration, source resolution, runtime, evidence operation,
policy action, implementation, deployment, or remote Git action.
