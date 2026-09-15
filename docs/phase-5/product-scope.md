# Phase 5 Product Scope

Status: proposed, non-effective, planning only

## Product Statement

H-CAM Operator Application is the human decision and investigation layer over
the accepted H-CAM platform. It should help an authorized user understand what
the system knows, what it does not know, why a record exists, how fresh and
complete it is, which action is permitted, and what happened after an action.

It must not present an AI score, reference candidate, camera observation, or
system alert as confirmed identity or operational truth. Uncertainty,
contradiction, correction, degradation, authorization, and review state are
first-class information.

## Intended Users

| Persona | Primary goals | Required protections |
| --- | --- | --- |
| Command supervisor | Understand critical workload, coverage, service degradation, and review backlog | Aggregated data, drill-down by authority, no accidental action, clear freshness |
| Control-room operator | Find cameras, assess health, prepare a live view, inspect alerts, and hand work to an analyst | Fast keyboard operation, bounded stream count, no raw locators, visible failures |
| Intelligence analyst | Review hypotheses, graph relationships, candidate uncertainty, and rule provenance | No identity overclaim, contradiction visibility, source chronology, purpose binding |
| Alert reviewer | Accept, reject, abstain, or request more information under quorum and lifecycle rules | Reason and ETag enforcement, explicit consequences, immutable review history |
| Investigator | Build and reconstruct timelines, add references, and propagate corrections | Append-only chronology, provenance, correction visibility, no source copying by default |
| Evidence officer | Inspect evidence references, integrity, provenance, holds, retention state, and export previews | Strong separation of reference from content, purpose and policy visibility, no silent export |
| Camera technician | Inspect camera metadata, stream health, capabilities, and probe history | Department scope, secret redaction, explicit control gates, no browser-to-camera access |
| Platform administrator | Manage configuration, roles, departments, policies, and feature visibility | Least privilege, attributable changes, second-person gates where required |
| Security auditor | Inspect access, denied actions, security signals, control revisions, and supply-chain posture | Read-only-by-default access, immutable audit references, separation from evidence records |

The same person may hold several roles, but the application must render each
capability from server-provided authorization and scope. The UI cannot infer a
role from a job title or make a denied action available because another portal
normally exposes it.

## Product Goals

1. Provide a calm, dense, repeatable operational workspace optimized for
   scanning, comparison, and keyboard-driven action.
2. Separate command, operations, intelligence, investigation, evidence,
   administration, and security concerns while preserving linked navigation.
3. Consume accepted versioned HTTP and event contracts without direct data-
   store, broker, camera, provider, or model access.
4. Preserve server authority for authentication, department scope, purpose,
   reason, ETag concurrency, idempotency, audit, and lifecycle transitions.
5. Make loading, empty, partial, stale, degraded, denied, conflict, failure,
   recovery, correction, and success states explicit on every data surface.
6. Support responsive laptop use, higher-density workstations, and future
   multi-monitor control-room layouts through bounded capability profiles.
7. Keep low-capability mode functionally complete. Higher-capability modes may
   improve density, simultaneous decoding, map detail, animation, and local
   rendering, but cannot remove safeguards or change semantic results.
8. Meet an implementation target based on WCAG 2.2 Level AA, with manual and
   automated evidence required before any conformance claim.
9. Preserve safe, generated-only demonstrations until later authority opens
   real media, data, providers, models, or operational actions.
10. Produce versioned UI contracts and evidence so future desktop, mobile, or
    field clients can reuse semantics without copying screen logic.

## Non-Goals For P5.0 Planning

- Building a landing page, marketing site, or decorative dashboard.
- Implementing frontend source, dependencies, routes, components, tests, or
  build configuration.
- Creating a new backend API merely to simplify a mockup.
- Connecting to Sentinel, cameras, ONVIF, media, providers, brokers, or models.
- Displaying real Government, police, private, personal, vehicle, owner,
  watchlist, case, investigation, evidence, or biometric information.
- Enabling PTZ, recording, image capture, export, deletion, retention, hold,
  alert notification, dispatch, enforcement, or autonomous action.
- Treating a UI action as authorization or a hidden control as access control.
- Claiming production readiness, legal admissibility, accessibility
  conformance, real-time capacity, security compliance, or operational value.

## Logical Portal Model

### H-CAM Command

The first view for supervisors. It summarizes active proposed alerts, review
backlog, investigation workload, service degradation, camera coverage, and
freshness. It offers drill-down, not inline high-risk mutation. Aggregates must
link to their definitions, time windows, completeness, and underlying lists.

### H-CAM Operations

The camera and control-room workspace. It covers camera search, map selection,
stream health, probe history, capability snapshots, bounded live-view
preparation, workspace layouts, and escalation to intelligence or
investigation. It must distinguish metadata availability from actual media
reachability.

### H-CAM Intelligence

The analyst workspace for hypotheses, correlation runs, graph and map
projections, proposed alerts, reference-query state, candidate uncertainty,
contradictions, abstentions, mandatory review, quorum, and lifecycle history.

### H-CAM Investigations

The chronology workspace. It provides timelines, event-time and record-order
views, reconstruction, relationships, reviews, corrections, and retractions.
The application must preserve prior states and make corrected facts visibly
different from removed or hidden content.

### H-CAM Evidence

The evidence-reference workspace. It shows reference identity, source class,
integrity state, provenance graph, policy/hold/retention evaluation state, and
export preview. Source evidence remains unresolved and uncopied by default.

### H-CAM Admin

The configuration workspace. Planned domains include users, roles,
departments, camera registry, stream endpoints, feature gates, rule/provider
catalogues, review policies, capability profiles, and compatibility status.
Only domains with accepted backend commands may progress beyond read-only
planning.

### H-CAM Security

The security and audit workspace. It separates operational logs, security
signals, audit records, and evidence records. It shows denied actions,
privileged operations, stale controls, dependency and supply-chain state,
degradation, and unresolved security findings without becoming an
authoritative SIEM.

## Shared Experience Principles

### Dense, Not Crowded

The application should prioritize tables, timelines, maps, compact detail
panes, command bars, saved views, and side-by-side comparison. Cards are for
repeated entities, not page-section decoration. Hero layouts and marketing
composition are out of scope.

### Context Survives Navigation

Selected department, bounded time window, filter set, map extent, selected
entity, and source view should be represented in typed route/search state when
safe. Secrets, tokens, raw evidence, camera locators, and personal data must
never enter URLs.

### State Before Action

Every command displays current revision, freshness, review requirement,
required reason, expected consequence, and safe failure behavior. Conflicts
reload current server state without silently resubmitting a mutation.

### Uncertainty Is Visible

Confidence is not a decorative percentage. Each view must distinguish
observation, hypothesis, candidate, reviewed conclusion, contradiction,
abstention, correction, and unknown. Color is supplemental only.

### Event Updates Do Not Grant Authority

Events invalidate or refresh cached queries. They do not directly mutate
authoritative browser state, unlock actions, or confirm a workflow. The client
must read the current resource after an event and obey the returned ETag and
capability state.

## Capability Profiles

The proposed UI capability system has four bounded profiles:

| Profile | Intended environment | Functional rule |
| --- | --- | --- |
| `safe_minimum` | Low-resource laptop or degraded browser | All required workflows remain available; one active live tile; simplified map styling; reduced animation |
| `balanced` | Typical development or operator laptop | Moderate density, bounded parallel queries, small live grid, standard map layers |
| `enhanced` | GPU-capable analyst workstation | Higher live-tile ceiling, richer map layers, local visual acceleration, larger comparison workspace |
| `control_room` | Future managed multi-monitor workstation | Coordinated workspaces, high information density, server-approved media and map budgets |

Profile selection must combine:

1. server policy ceiling;
2. accepted deployment profile;
3. browser capability observation;
4. current degradation and network state;
5. operator preference within the allowed ceiling.

The lowest result wins. Hardware detection is advisory and sanitized. A
profile cannot enable a server-disabled feature, change an authorization
decision, increase data scope, bypass review, or lower evidence visibility.

## Language And Localization

The information architecture must support English, Gujarati, and Hindi without
embedding policy in presentation strings. Layouts must tolerate long labels,
localized dates, local time zones, and future right-to-left testing even if an
RTL language is not selected initially. Canonical timestamps remain available
alongside localized display values.

## Product Acceptance Principle

A visually complete screen is not a completed capability. Each weighted item
requires contract coverage, all required UI states, accessibility evidence,
security and authorization behavior, deterministic generated fixtures,
responsive validation, and explicit owner acceptance where defined.
