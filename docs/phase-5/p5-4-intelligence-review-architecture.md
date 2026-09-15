# P5.4 Intelligence, Alerts, And Human Review Architecture

Status: planning baseline; owner decisions and separate start authorization required

## Purpose

P5.4 plans the analyst and reviewer experience that consumes accepted Phase 3
anonymous analytic events and accepted Phase 4 intelligence contracts. It
does not run models, infer identity, connect to providers, or perform an
operational action. Its purpose is to help authorized people inspect evidence,
understand uncertainty, challenge hypotheses, review proposed alerts, and
record accountable decisions without turning machine output into fact.

Command Center remains the primary H-CAM dashboard. Intelligence Center is a
connected specialist portal. It owns analytical queues, relationship
exploration, rule explanations, proposed-alert review, and correction review.
Command Center may show safe aggregates and opaque references, but it may not
duplicate reviewer controls or collapse the intelligence evidence ladder.

## Non-Negotiable Truth Model

The browser renders each concept with a distinct type, label, icon, chronology,
provenance treatment, and allowed action set.

| Concept | Meaning | Must never imply |
| --- | --- | --- |
| Source observation | A bounded fact reported by an accepted source contract | Identity, intent, guilt, or correctness beyond its source |
| Inference | A derived statement with method, inputs, revision, and limitations | A direct observation or final truth |
| Hypothesis | A falsifiable, revisioned explanation supported or contradicted by evidence | Confirmed identity, criminality, or prediction |
| Candidate | A possible reference result with field-level evidence and uncertainty | Identity established or database truth copied into H-CAM |
| Proposed alert | A review-required semantic occurrence | An operational alert, dispatch request, or enforcement command |
| Review | An attributable human decision under a server-provided policy | External authorization or automatic action |
| Correction | An append-only statement that revises or retracts earlier meaning | Deletion or silent rewriting of history |
| Lifecycle state | A procedural state of an aggregate | Evidence strength, guilt, severity truth, or identity confidence |

Every detail view includes a persistent semantic banner naming the current
concept, its source class, freshness, completeness, revision, and authority
limit. Terms such as `confirmed match`, `suspect`, `criminal`, `guilty`, and
`verified identity` are prohibited unless a future legally governed producer
defines and authorizes that exact fact. This phase defines no such producer.

## Portal Topology

```text
H-CAM Command Center (primary)
  |-- safe intelligence workload summary
  |-- proposed-alert aggregate counts
  |-- health and degraded-state indicators
  `-- opaque handoffs
       |
       v
H-CAM Intelligence Center (specialist)
  |-- Intelligence Overview
  |-- Hypothesis Queue
  |-- Correlation Run Queue
  |-- Relationship Explorer
  |-- Spatial Intelligence
  |-- Rule And Evaluation Explorer
  |-- Candidate Evidence Workspace
  |-- Proposed Alert Queue
  |-- Mandatory Review Desk
  |-- Corrections And Reconsideration
  `-- Intelligence Health
```

The specialist portal reuses the P5.1 shell, authorization, API, invalidation,
query policy, observability, internationalization, accessibility, and design
packages. GIS views reuse the one P5.2 GIS domain and renderer boundary.
Camera handoffs use P5.3 opaque references and never expose media or camera
locators to intelligence contracts.

## Page Families

### Intelligence Overview

Shows department-scoped workload, freshness, incomplete-data counts,
contradiction and abstention counts, proposed-alert lifecycle distribution,
review backlog, conflict rate, correction impact, and producer health. Every
aggregate links to an authoritative queue with the exact filter encoded as
non-sensitive typed state. It does not rank people or infer threat level.

### Hypothesis Queue

Provides paginated, server-filtered hypotheses with type, revision, state,
observed window, evidence counts by role, freshness, completeness, and
correlation-run reference. Default ordering is deterministic and operationally
neutral: oldest actionable review need first, then stable identifier. Scores
never become the primary sort without an explicit, visible operator choice.

### Correlation Run Queue

Separates queued, running, succeeded, partial, failed, superseded, and
cancelled runs. Detail shows accepted input manifest, rule/configuration
revision, deterministic mode, started/completed times, partial-result reason,
output references, and retry lineage. The UI does not rerun correlation in
P5.4.

### Relationship Explorer

Consumes a server-bounded subgraph. It provides an enhanced graph projection
and a synchronized authoritative node/edge table. Nodes and edges retain typed
provenance, direction, temporal bounds, evidence role, revision, and
truncation state. Visual distance, size, color, centrality, and layout are not
evidence and are never described as such.

The proposed baseline uses a renderer facade. A bounded DOM-based graph
candidate may be added under a later exact dependency authorization. The
client never performs identity resolution, relationship inference, hidden
expansion, or unbounded layout computation. Low-resource mode can default to
the table while remaining functionally complete.

### Spatial Intelligence

Reuses P5.2 MapLibre and optional deck.gl projections for bounded GeoJSON
features in WGS 84 longitude/latitude. It includes list/table equivalence,
time window, freshness, completeness, location precision, truncation, and
source controls. Spatial proximity is shown as proximity, never association,
identity, causation, or guilt. Exact sensitive coordinates require server-side
authorization and minimization; generated planning fixtures contain none.

### Rule And Evaluation Explorer

Shows exact rule identifier and revision, lifecycle state, approved/shadow
status, typed visual graph, constrained expression fragments, normalized
inputs, node-by-node outcome, timer/window behavior, evidence references,
result, abstention, and limitations. Natural-language explanation is a
secondary summary and may never replace the exact trace.

### Candidate Evidence Workspace

Presents candidate sets as field-level evidence matrices. Each row carries
source class, field category, comparison result, calibration class,
contradiction state, ambiguity, missingness, provenance, freshness, and an
explicit `identity_not_established` boundary. Raw provider responses,
credentials, exact provider destinations, and unnecessary fields remain
server-side. The workspace supports abstention and `insufficient evidence` as
first-class outcomes.

### Proposed Alert Queue And Detail

Separates semantic occurrence identity from delivery/idempotency identity.
List and detail show alert class, procedural priority, lifecycle, evidence
freshness, completeness, contradiction, review policy, quorum state,
chronology, corrections, and safe source references. `Proposed alert` remains
the visible noun until the accepted server lifecycle says otherwise; it is
never labeled as dispatch, incident fact, or enforcement instruction.

### Mandatory Review Desk

The review desk is a deliberate decision surface, not a rapid-approval feed.
It provides evidence before decision controls, contradiction and abstention
prominently, server-authoritative policy, remaining independent reviewer slots,
bounded reason codes, optional field-minimized rationale, draft state,
confirmation, ETag, expected revision, idempotency key, command receipt, and
conflict recovery. Drafts are memory-only by default.

No button performs notification, dispatch, enforcement, provider update, case
mutation, or another external action. A successful review only records the
accepted Phase 4 review command and refreshes the authoritative alert state.

### Corrections And Reconsideration

Shows append-only correction, retraction, supersession, and reconsideration
lineage. Impacted hypotheses, candidates, proposed alerts, reviews, and future
P5.5 investigation references receive visible stale/corrected markers. Old
records remain available according to authorization and retention contracts;
the UI never rewrites history or hides a correction.

### Intelligence Health

Shows low-cardinality producer availability, queue freshness, stale inventory,
event lag, API degradation, circuit state, and generated test status. It does
not expose identifiers, provider destinations, raw errors, payloads, secrets,
or protected data.

## Server Authority And Client State

The server remains authoritative for department scope, roles, capabilities,
field minimization, list filters, pagination, graph bounds, current revision,
review policy, quorum, lifecycle transitions, allowed actions, and command
acceptance. The browser may cache only field-minimized projections under P5.1
query policy and must purge them on logout, department change, permission loss,
or session expiry.

Mutation sequence:

1. Fetch authoritative detail and strong ETag.
2. Build a memory-only draft against that exact revision.
3. Revalidate capability and review policy before confirmation.
4. Present an explicit confirmation summary with consequences and limitations.
5. Submit `If-Match`, expected revision, bounded reason, and idempotency key.
6. Treat `412 Precondition Failed` or typed conflict as a stop, not a retry.
7. Fetch current authority and display a semantic comparison.
8. Require deliberate reconsideration and a new confirmation.
9. Store only the server command receipt and refreshed authoritative state.

Event messages invalidate bounded query keys. They never patch a review,
quorum, lifecycle, identity, or authorization result into truth. Unknown event
versions are quarantined; polling or manual refresh provides the fallback.

## Dynamic Resource Profiles

| Profile | Enhanced behavior | Invariant behavior |
| --- | --- | --- |
| Low-resource | Table-first graph, limited visible nodes, no animated layout, single spatial panel | Complete workflows, evidence, contradiction, review, correction, security, and accessibility |
| Enhanced workstation | Bounded interactive graph, synchronized map, more retained non-sensitive view state | Same server authority and limits |
| Control room | Multi-monitor queue/detail separation and shared selected-reference context | Independent session and permission revalidation per window |
| GPU lab | Optional accelerated rendering only after evidence and explicit enablement | No model execution and no change to meaning or authority |
| Future server | Server-precomputed layouts and larger bounded projections | Browser still receives minimized projections and never performs inference |

Profile changes may affect only rendering density, visible result cap, layout
quality, prefetch budget, and animation. They may not change permissions,
quorum, evidence visibility policy, allowed transitions, review safeguards,
retention, correction handling, or external-action prohibitions.

## Accessibility And Human Factors

- Every graph and map has a synchronized authoritative list or table.
- Keyboard order follows task order, not visual layout coordinates.
- Focus remains visible and returns predictably after dialogs and conflicts.
- Status changes use bounded polite announcements; urgent assertive messages
  are reserved for destructive loss of a draft or expiring decision authority.
- Color is never the only marker for state, evidence role, contradiction,
  freshness, priority, or correction.
- Review controls remain disabled until required evidence is inspected and the
  current server policy is loaded.
- Queue designs expose workload and age without encouraging speed-only review.
- Confirmation copy states what will be recorded and what will not happen.
- Reduced motion, zoom/reflow, target size, contrast, and stable dimensions are
  acceptance gates, not optional polish.

## Boundary Summary

P5.4 planning defines a production-shaped consumer architecture, but no source
or test implementation is authorized. No model, provider, camera, media,
identity, private or Government record, real investigation, operational alert,
notification, dispatch, enforcement, autonomous action, container,
Kubernetes, deployment, or remote Git action is part of this plan.
