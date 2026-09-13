# Phase 5 Portal And Workflow Catalogue

Status: proposed, non-effective, planning only

## Shared Operator Model

Every portal uses the same identity, department, contract, freshness,
correction, degradation, and safe-problem semantics. Portal boundaries improve
focus and ownership; they never create a separate authorization domain or a
different meaning for the same record.

## Global Navigation

The planned global shell provides:

- portal switcher filtered by server-returned capability;
- active department and time-zone context;
- bounded global search entry that exposes only accepted search domains;
- recent safe navigation history without record payload persistence;
- application/degradation/session status;
- notification inbox for UI workflow status, not dispatch or enforcement;
- language, density, contrast, motion, and capability-profile preferences;
- help, policy, version, compatibility, and limitation views;
- keyboard command palette for navigation and permitted read-only commands.

## H-CAM Command

### Audience

Commanders, duty officers, and control-room supervisors.

### Planned Views

| View | Purpose | Initial contract status |
| --- | --- | --- |
| Situation overview | Summarize proposed alerts, reviews, investigations, camera coverage, and degradation | Partial; domain lists exist, aggregate contract missing |
| Operational map | Show bounded camera, alert, hypothesis, incident, and resource layers | Partial; coordinates exist, viewport/tile API missing |
| Review backlog | Prioritize pending mandatory reviews by safe severity and age | Partial; alert/review data exists, aggregate/sort policy needs freezing |
| Coverage and health | Show camera/stream coverage, stale health, and blind spots | Partial; camera/stream APIs exist, aggregate semantics missing |
| Platform degradation | Show affected services, current state, loss accounting, and recovery | Supported by operations summary/views within generated-only limits |
| Shift handoff | Produce a bounded view of unresolved records and changes | Missing typed handoff contract |

### Command Workflow

1. Load operations summary and current completeness.
2. Load bounded alert, timeline, camera, and stream aggregates.
3. Display time window, department, freshness, and degraded sources.
4. Select an aggregate to navigate to its authoritative list.
5. Preserve filters and map extent without placing sensitive data in the URL.
6. Do not perform review or lifecycle mutations in the overview.

### Required States

Loading, empty, partial, stale, degraded, denied, failure, recovery, and
unsupported aggregate. A healthy green summary is prohibited when any required
source is unknown.

## H-CAM Operations

### Audience

Control-room operators and camera technicians.

### Planned Views

| View | Purpose | Initial contract status |
| --- | --- | --- |
| Camera catalogue | Search and filter cameras by source, department, type, ownership, and state | Supported for bounded list/detail |
| Camera map | Select cameras spatially with list alternative | Partial; coordinates exist, viewport contract missing |
| Camera detail | Metadata, provenance, location, streams, health, and recent changes | Supported across camera and stream APIs |
| Stream health | State, reason, last observation, success/failure streak, and probe history | Supported |
| Capability inventory | Latest capability, freshness, completeness, profile, and history | Supported for ONVIF stream endpoints under existing gates |
| Live workspace | One or more authorized playback sessions in a stable grid | Partial; single-session issuer exists, browser media contract missing |
| Workspace layouts | Named layouts, tile positions, and safe display preferences | Missing persistence contract |
| Probe/refresh queue | Submit bounded metadata probes and inspect status | Supported by existing routes, subject to role/reason/cooldown behavior |

### Camera-To-Live Workflow

1. Query bounded camera catalogue.
2. Select a camera from table or map.
3. Load stream endpoints and health without rendering raw locators.
4. Check capability freshness and codec/transport support.
5. Request one short-lived playback session.
6. Start the selected browser transport within the effective profile budget.
7. Show connecting, playing, buffering, stalled, expired, denied, unsupported,
   failed, and closed state.
8. Tear down the session on close, expiry, logout, department change, or
   policy reduction.

No recording, download, screenshot, image capture, PTZ, ONVIF discovery, or
camera configuration action is implied by this workflow.

### Multi-View Rules

- Stable tile dimensions prevent layout shift.
- One tile is active for audio; all others are muted.
- Simultaneous stream ceiling comes from the effective capability profile.
- Operators can lower quality or tile count; they cannot exceed server policy.
- Failure in one tile does not hide the health of others.
- Fullscreen preserves accessible exit, status, and source context.
- No tile restarts indefinitely; reconnect is bounded and visible.

## H-CAM Intelligence

### Audience

Intelligence analysts and mandatory reviewers.

### Planned Views

| View | Purpose | Initial contract status |
| --- | --- | --- |
| Hypothesis queue | Review current hypotheses, uncertainty, chronology, and revision | Supported by list and revisions; filtering gaps remain |
| Correlation run | Inspect deterministic run status, inputs, outputs, and failures | Supported |
| Relationship graph | Explore bounded nodes/edges with list alternative | Supported by graph projection; client bounds/layout policy needed |
| Spatial projection | Review location relationships on map and timeline | Partial; projection exists, map query/render contract needs freezing |
| Proposed alerts | Filter, inspect, and compare alert aggregates | Supported by P4.7 handoff |
| Review workspace | Record approve/reject/abstain/request-information decisions | Supported generated-only; exact forms and consequences need design |
| Lifecycle history | Inspect state transitions, denials, timers, and corrections | Supported |
| Reference query | Inspect provider state, query progress, candidates, contradiction, and abstention | Supported generated-only; no real provider use |
| Rule explanation | Show exact rule revision, nodes, predicate, geometry, and evaluation | Supported across rule APIs; consumer contract needs consolidation |

### Alert Review Workflow

1. Load alert list with freshness, completeness, and safe priority inputs.
2. Open alert detail and capture current ETag.
3. Load hypothesis, rule revision, source chronology, reference-query state,
   candidate uncertainty, contradictions, existing reviews, quorum, and
   lifecycle.
4. Present source facts separately from inference and candidate material.
5. Require an explicit decision and bounded reason.
6. Submit idempotency identity and `If-Match` to the accepted review command.
7. On conflict, preserve the draft reason locally in memory, load current
   state, and require reconsideration before resubmission.
8. Confirm only the server-returned aggregate and review record.
9. Navigate to timeline/reconstruction when permitted.

The UI never turns a proposed alert into a confirmed identity, operational
dispatch, notification, or enforcement action.

### Graph Accessibility

Every graph has:

- a bounded node and relationship table;
- keyboard selection independent of pointer drag;
- path and neighbor summaries;
- visible edge direction and relationship type beyond color;
- zoom controls with text labels and reset;
- reduced-motion layout behavior;
- no force-layout movement while a node has keyboard focus unless requested.

## H-CAM Investigations

### Audience

Investigators and authorized reviewers.

### Planned Views

| View | Purpose | Initial contract status |
| --- | --- | --- |
| Timeline list | Find bounded generated investigations by status and time | Supported, search gaps remain |
| Timeline detail | Show append-only record chronology and current revision | Supported |
| Event-time view | Show source chronology without replacing durable record order | Supported through reconstruction view |
| Reconstruction | Rebuild state through a selected revision | Supported |
| Corrections | Show original, corrected, affected, and propagated records | Supported |
| Relationships | Link timelines or records with typed revision history | Supported for creation; query projection gap exists |
| Reviews | Show attributable review and disposition chronology | Supported for creation; consolidated query gap exists |

### Investigation Workflow

1. Load the current timeline and ETag.
2. Display durable record order by default with event-time alternative.
3. Distinguish event, hypothesis, alert, review, action, correction,
   retraction, and evidence-reference entries.
4. Add a typed entry only through the accepted command and reason contract.
5. Record a correction as a new append-only revision, never overwrite history.
6. Load reconstruction through a selected revision and show gaps explicitly.
7. Link to evidence-reference state without resolving or copying source data.

### Timeline Interaction

The timeline uses a virtualized list only if focus, reading order, item count,
and off-screen content remain understandable. Users can switch to a compact
table. Infinite scroll is not the only navigation mechanism; bounded pages or
explicit load-more controls remain available.

## H-CAM Evidence

### Audience

Evidence officers, investigators with evidence scope, and auditors.

### Planned Views

| View | Purpose | Initial contract status |
| --- | --- | --- |
| Evidence references | List references without copying source content | Supported per timeline; global query missing |
| Integrity state | Show assessment algorithm, observation, result, and limitations | Supported |
| Provenance graph | Show entity/activity/agent derivation in H-CAM semantics | Supported |
| Hold overlay | Show separately controlled generated hold state | Supported generated-only; no legal policy |
| Retention evaluation | Show policy availability and generated decision | Supported generated-only |
| Deletion simulation | Preview affected references and blockers | Supported generated-only; no deletion execution |
| Export preview | Show purpose-bound manifest and unresolved references | Supported generated-only; no export execution |

### Evidence Workflow

1. Enter from an authorized timeline or evidence-reference query.
2. Load reference metadata, integrity state, provenance, review, correction,
   hold, and retention projections separately.
3. Display unresolved, missing, stale, mismatched, contradicted, and unknown as
   distinct non-success states.
4. Generate only a preview where an accepted generated-only command exists.
5. Never fetch, render, copy, export, delete, or change source evidence under
   the current boundaries.

Integrity verifies a reference or observed bytes under a stated process. It
does not prove truth, legality, identity, admissibility, or chain of custody.

## H-CAM Admin

### Audience

Platform, department, camera, policy, and integration administrators.

### Planned Domains

- camera registry and normalized imports;
- stream endpoints, health, probe, capabilities, and playback policy;
- analytics assignments and revisions;
- geometry and intelligence rule catalogues;
- review policy, provider catalogue, and kill-switch visibility;
- department, role, user, identity provider, feature flag, saved view, and UI
  capability profile management;
- compatibility, deprecation, and release-manifest status.

Only the first six have partial accepted backend surfaces. Identity,
department, user, saved-view, UI-profile, and release management APIs are
contract gaps. The portal must render them as unavailable rather than
implement client-only authority.

## H-CAM Security

### Audience

Security operators, auditors, and authorized administrators.

### Planned Views

- current security and degradation posture;
- denied request counts and safe reason classes;
- privileged-action audit references;
- role/scope and row-security parity evidence;
- stale control, kill-switch, and feature-gate state;
- dependency, license, SBOM, vulnerability, and provenance status;
- session and authentication health without exposing tokens or user detail;
- incident links to external security systems only after a future integration
  contract exists.

Security signals, operational logs, audit records, and evidence records remain
separate. A unified search is a disabled derived projection, never an
authoritative merged store.

## Shared UI State Matrix

Every data view implements these states where applicable:

| State | Meaning | Required response |
| --- | --- | --- |
| Loading | Initial bounded request is pending | Stable skeleton/placeholder, cancel where useful, no false empty state |
| Empty | Successful complete query returned no items | Explain active filters and safe reset action |
| Partial | Some required sources or pages are unavailable | Show included and missing sources; no aggregate success claim |
| Stale | Last accepted state exceeded its freshness bound | Keep visible with timestamp and refresh action |
| Degraded | Supporting service is impaired | Show affected capability and permitted fallback |
| Denied | Server rejected current principal/scope/action | No protected detail; preserve focus and safe navigation |
| Conflict | ETag or lifecycle changed | Show current revision and require reconsideration |
| Failure | Request failed with safe classified reason | Recovery action only when safe; no raw detail |
| Recovery | A previously degraded source recovered | Announce politely and allow refresh |
| Correction | Append-only correction affected visible state | Show prior/current relationship and chronology |
| Success | Accepted operation completed | Confirm server result, not optimistic assumption |
| Unsupported | Browser or capability cannot execute the view | Provide equivalent list/detail or lower profile |
| Session expired | Authentication is no longer valid | Preserve no sensitive drafts; return focus after reauthentication |

## Accessibility Matrix

Each workflow requires evidence for:

- complete keyboard operation and logical focus order;
- focus not obscured and focus restoration after overlays;
- visible labels and matching accessible names;
- status announcements that do not steal focus;
- assertive announcements only for immediate application failure;
- field and operation error association;
- state and severity conveyed through text/icon plus color;
- target size and spacing;
- contrast in normal, dark, high-contrast, and forced-color modes as selected;
- 200% and 400% zoom/reflow where applicable;
- reduced-motion alternatives;
- alternatives for map, graph, timeline, drag, hover, and gesture interactions;
- localized English, Gujarati, and Hindi labels and long text;
- screen-reader testing for the selected managed browser matrix.

## Workflow Stop Conditions

No workflow may be planned as available when it depends on:

- a missing accepted producer contract;
- a direct camera, media, provider, model, database, broker, or evidence-source
  connection;
- real data or operational action;
- a client-created authorization or lifecycle decision;
- unbounded search, graph, map, timeline, or live-stream fan-out;
- persistent sensitive browser storage;
- automatic retry of a denied, invalid, conflicting, or non-idempotent action.
