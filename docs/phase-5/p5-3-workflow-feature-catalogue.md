# P5.3 Workflow And Feature Catalogue

Status: proposed planning inventory; owner decisions pending

## Product Position

The P5.3 experience is a connected specialist area under the Operations portal.
Command Center remains the primary dashboard and GIS Center remains the spatial
specialist. P5.3 supplies detailed camera and live-workspace tools without
turning the product into one overloaded page.

## Planned Pages

| Page | Primary purpose | Required content | Explicit exclusions |
| --- | --- | --- | --- |
| Camera Catalogue | Find and compare cameras across the authorized department scope | Dense table/list, bounded filters, health, freshness, capability, stream count, selected profile support, saved views projection | Raw locators, credentials, unbounded map, live autoplay |
| Camera Detail | Inspect one camera and its streams | Identity, safe location context, lifecycle, stream summary, health history, probes, capabilities, configuration revision, related opaque references | Management locator, secret reference, PTZ/action controls, snapshots |
| Stream Diagnostics | Understand why live viewing is unavailable or degraded | Sanitized probe timeline, capability freshness/completeness, codec/rendition support, playback eligibility, safe reason codes | Raw probe bodies, exception text, internal addresses, secret state beyond configured/not configured |
| Live Workspace | Operate one or several admitted live streams | Stable video tiles, authoritative status panel, focus/pin, quality band, transport state, bounded retry, incident/investigation handoff | Recording, snapshot, download, export, print, detection overlays not yet authorized |
| Monitor Wall | Arrange a larger bounded set for control-room use | Named revisioned layout projection, C1/C4/C10 admission, tile priority, health/status strip, full-screen and multi-monitor composition | Background autoplay of every tile, unlimited streams, browser-stored protected state |
| Workspace Manager | View and reconcile saved layout projections | Owner/scope, revision, tile references, created/updated timestamps, conflict/deleted/inaccessible states | Playback grants, tokens, media data, hidden cross-department references |

## Catalogue Workflows

### Find a camera

1. Enter the Operations Camera Catalogue.
2. Apply bounded server-side filters such as safe location label, lifecycle,
   health band, capability, and freshness.
3. Review the authoritative list with loading, partial, stale, degraded, empty,
   denied, and failure states.
4. Open Camera Detail using an opaque camera reference.
5. Preserve only safe bounded filters in route state; keep protected filters and
   selection in memory or a future server-owned workspace.

### Diagnose unavailable live viewing

1. Open Camera Detail or Stream Diagnostics.
2. Compare stream lifecycle, health, latest probe, capability snapshot,
   completeness, staleness, and playback eligibility.
3. Present one safe primary reason plus contributing reason bands.
4. Offer only actions already authorized for the role, such as refresh view,
   retry a playback proposal after cooldown, or open the support workflow.
5. Never reveal internal locators, credentials, probe payloads, or stack traces.

## Live Workflows

### Open one live stream

1. Operator selects `Open live` from an authorized camera context.
2. Client evaluates local compatibility and requests server admission with an
   explicit purpose/reason.
3. Server returns denied, approval-required, or an opaque short-lived grant.
4. Adapter starts the allowed transport and reports typed loading state.
5. Video and synchronized non-video status become ready together.
6. Expiry, revocation, logout, scope change, route close, or operator stop
   releases all media resources and grant material.

### Add a stream to a workspace

1. Operator selects an available tile position.
2. Admission policy compares pinned/selected/visible priority against the
   effective stream and decode budgets.
3. If capacity exists, the client requests a separate scoped grant.
4. If capacity does not exist, the tile remains queued/deferred with a clear
   explanation and an option to release a lower-priority tile.
5. The scheduler may lower quality before releasing a selected tile.

### Recover from a stall

1. Detect a stall from multiple bounded media signals and a timer, not one event.
2. Mark the tile degraded while preserving the last trusted non-video status.
3. Attempt bounded in-transport recovery.
4. Recreate the transport only if the grant remains valid and the retry budget
   is open.
5. Use HLS fallback after WHEP failure only when authorized.
6. Stop in a visible terminal state after retry exhaustion; require operator
   action after cooldown.

### Handle profile pressure

1. Measure only current workspace decode/network pressure and supported
   browser signals.
2. Lower non-pinned rendition bands deterministically.
3. Release off-screen or hidden non-pinned sessions after a grace period.
4. Preserve the selected stream and all non-video workflows.
5. Explain profile downgrade with a safe reason and allow later recovery within
   the server ceiling.

### Cross-portal handoff

1. Command/GIS/Alert/Investigation passes opaque references and bounded time
   context.
2. P5.3 revalidates route, department, role, and camera access.
3. The operator opens live viewing only through a new playback proposal.
4. Return navigation preserves only allowlisted opaque context.

## Monitor-Wall Features

- fixed, predictable C1, C4, and C10 templates;
- custom layout projection only within the same bounded tile maximum;
- pin, focus, reorder, swap, pause, release, mute, quality-band preference,
  fullscreen, and safe diagnostics;
- clear active/deferred/stalled/expired/denied/unsupported state per tile;
- workspace-level stream budget, active count, deferred count, degradation,
  and connection state;
- independent window support with fresh session and department validation;
- optional screen wake lock after explicit operator action, with visible state
  and normal operation when denied or released;
- no automatic startup of all saved tiles.

## Operator Controls

| Control | P5.3 state |
| --- | --- |
| Open live | Planned and authorization-gated |
| Pause/resume local playback | Planned |
| Mute/unmute | Planned; default mute for multi-camera safety |
| Select allowed quality band | Planned within server ceiling |
| Pin/focus/reorder/release tile | Planned |
| Fullscreen and multi-monitor composition | Planned with revalidation |
| Retry after bounded cooldown | Planned |
| Open diagnostics | Planned |
| Create incident/investigation handoff | Reference-only handoff; authoritative workflow remains external |
| Record video | Prohibited |
| Capture snapshot | Prohibited |
| Download/export/print media | Prohibited |
| PTZ or camera configuration | Prohibited in P5.3 |
| Run analytics or model inference | Prohibited |

## Complete State Inventory

Every page or tile must account for:

- initial, loading, empty, ready, partial, stale, degraded, denied, forbidden;
- approval-required, reason-required, requesting, queued, deferred, admitted;
- negotiating, loading-media, playing, paused, muted, quality-changing;
- stalled, reconnect-wait, reconnecting, fallback-in-progress, circuit-open;
- expiring, expired, revoked, unsupported, failed, releasing, released;
- profile-downgraded, offline, service-unavailable, conflict, deleted;
- logout, department-switch, permission-change, hidden-document, route-disposed;
- correction/retraction context from connected Phase 4 views where applicable.

## Authoritative Non-Video Alternative

For every camera tile, the alternative must expose the same operationally safe
identity and status fields in text:

- display name and safe location;
- lifecycle, health, freshness, and completeness;
- current playback state and transport class;
- effective profile and rendition band;
- safe reason, retry/cooldown state, and expiry;
- authorized navigation and release controls.

The table/list remains usable when video, WebGL, MSE, WebRTC, acceleration, or
multiple monitors are unavailable. It must not contain a captured frame.

## Generated Validation Catalogue

### C1

- one synthetic HLS stream;
- open, play, pause, expiry, renewal proposal, release, logout, and denial;
- supported and unsupported codec paths;
- keyboard and non-video equivalence;
- zero persisted token/locator/media state.

### C4

- four unique synthetic streams with mixed safe codec/rendition metadata;
- admission priority, focus/pin, off-screen deferral, quality downgrade;
- one stall, one expiry, one fallback, and one scope-change teardown;
- deterministic layout conflict and recovery.

### C10

- ten unique synthetic streams with bounded HLS and optional WHEP simulator
  paths;
- profile ceilings, backpressure, retry storms, hidden-page behavior, teardown,
  and monitor-wall status equivalence;
- declared machine/browser profile and no production capacity claim.

## Acceptance Evidence Required Later

- typed contract and state-machine tests;
- deterministic generated fixture and media manifests;
- browser-safe projection and secret/locator redaction tests;
- HLS adapter tests and provisional WHEP fallback tests;
- C1/C4/C10 admission, degradation, teardown, and replay evidence;
- keyboard, focus, status, reflow, reduced-motion, and authoritative-alternative
  validation;
- CSP, origin, redirect, token, storage, telemetry, and logout threat tests;
- clean build, dependency, license, SBOM, vulnerability-refresh, and limitation
  records;
- separate owned-lab evidence only if later explicitly authorized.
