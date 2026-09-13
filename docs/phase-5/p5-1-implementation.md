# P5.1 Shared Application Foundation Implementation

Status date: 2026-09-07

## Scope

P5.1 implements the generated-only frontend foundation authorized by exact
package `P5.1-START-R0`. It does not implement operational workflows, map or
media runtimes, backend routes, Government or private data access, models,
deployment, or remote Git activity.

## Delivered Topology

The `frontend/` workspace contains seven independently buildable portals:

- Command Center;
- Operations Center;
- Intelligence Center;
- Investigation Center;
- Evidence Center;
- Admin Center;
- Security Center.

They share sixteen bounded packages through workspace contracts. No portal
imports another portal and runtime federation is absent. One lockfile governs
the complete workspace.

## Workstream Results

| Workstream | Technical result | Evidence |
| --- | --- | --- |
| P5.1-W1 Workspace, build, and dependency policy | Complete | Seven independent builds, one lockfile, exact dependency evidence, CycloneDX 1.6 SBOM, zero unresolved audit findings |
| P5.1-W2 Shell, navigation, and routing | Complete | Shared semantic shell, capability-filtered navigation, route validation, command dialog, responsive mobile navigation |
| P5.1-W3 Design system and accessibility | Complete | Tokens, accessible primitives, focus handling, forced-colors and reduced-motion behavior, Storybook and axe evidence |
| P5.1-W4 Typed contracts, API, and errors | Complete | Typed client, same-origin boundary, runtime payload validation, bounded problem mapping, concurrency and freshness contracts |
| P5.1-W5 Session, authorization, and context | Complete | Fail-closed session states, department and capability context, CSRF and reauthentication contracts, denied-state handling |
| P5.1-W6 Server state, concurrency, and events | Complete | Operation-specific query policy, stale-state handling, conflict projection, event invalidation without authority claims |
| P5.1-W7 Localization, profiles, and windows | Complete | English, Gujarati, Hindi, and pseudo-locale catalogues; low-resource, enhanced, control-room, and future-server profiles |
| P5.1-W8 Observability, adoption, validation, and acceptance | Technically complete; owner acceptance pending | Low-cardinality observability, generated fixtures, reference-only UI adoption record, validation and evidence package |

## Security Boundaries

- All fetch calls are confined to the typed API client.
- Same-origin requests are the only implemented transport policy.
- Tokens, credentials, media locators, personal identifiers, free text, and
  high-cardinality values are prohibited from telemetry fixtures.
- Browser persistent-storage APIs are not used for protected state.
- Server responses remain authoritative after event invalidation.
- Capabilities fail closed and cannot be elevated by local profile selection.
- The playback package contains contracts only and no camera, media, HLS,
  WebRTC, recording, or snapshot implementation.
- Existing `hcam-1-0/final-ui` material was assessed as a reference only; no
  source path was copied or included in a build.

## Resource Profiles

The safe low-resource profile is functionally complete. Enhanced workstation,
control-room, and future-server profiles may adjust density, visual quality,
and bounded concurrency, but cannot grant authority or expose a feature that
is absent from the low-resource workflow. Hardware selection remains a future
runtime responsibility.

## Storage Note

During validation the `C:` volume exhausted its free space. Generated
dependency trees, build output, coverage output, browser reports, and an
incomplete worktree virtual environment were preserved under
`F:/HCAM-Task-Storage`. They are not source, are excluded from Git and the
evidence component digest, and are not required to understand the contracts.
No repository source was relocated.

## Progress

Workstreams W1 through W7 earn **10.5/12 P5.1 points (87.5000%)**. W8 is
technically complete but its 1.5 points remain gated by separate exact owner
acceptance. Phase 5 therefore reaches **18.5/100 (18.5000%)**, change
**+10.5000 percentage points** from the accepted P5.0 baseline. Exact P5.1
acceptance would make P5.1 **12/12 (100.0000%)** and Phase 5
**20/100 (20.0000%)**.
