# P5.3 Camera And Live Monitoring Architecture

Status: planning baseline; owner decisions pending; no implementation authority

Authority: `D-P5.3-PLAN-AUTH`

## Purpose

P5.3 defines the operator-facing camera and live-monitoring workspace. It does
not replace Phase 2 camera management, perform analytics, or turn the Phase 2.5
Sentinel lab into a production dependency. It gives an authorized operator a
safe, accessible way to inspect catalogue data, understand stream condition,
request short-lived live viewing, arrange bounded multi-camera workspaces, and
handoff an opaque camera reference to Command, GIS, Alerts, or Investigations.

## Non-Negotiable Architecture Rules

1. Command Center remains the primary situational dashboard. P5.3 is a
   connected specialist workspace under Operations.
2. The server is authoritative for department scope, permission, stream
   eligibility, profile ceiling, freshness, and session lifecycle.
3. Browsers never receive RTSP, ONVIF, management, secret, internal media
   gateway, or credential-bearing locators through catalogue APIs or route
   state.
4. Media is view-only. Recording, snapshot, download, export, print, PTZ, and
   other operational control are outside P5.3.
5. HLS is the dependable baseline. WHEP is an optional, draft-pinned
   low-latency enhancement with automatic HLS fallback.
6. Low-resource mode contains every authorized workflow. Stronger hardware may
   increase admitted streams, rendition quality, frame rate, and rendering
   detail, but cannot add authority or remove safeguards.
7. Generated synthetic media is the only implementation-time media source
   until a later, explicit owned-lab authorization.

## Logical Topology

```text
Command Center / GIS Center / Alerts / Investigation
                    |
          opaque cameraRef + return context
                    |
     Operations: Camera And Live Workspace
                    |
       P5 typed client and session policy
          |                         |
          v                         v
browser-safe camera API      playback control API
          |                         |
   Phase 2 camera data       opaque short-lived grant
                                    |
                         same-origin media edge
                                    |
                     internal authorized media gateway
                                    |
                         Phase 2 stream endpoint
```

The media edge is a future producer capability, not a P5.3 planning-time
implementation. It must validate the normal H-CAM session, department scope,
camera/stream grant, expiry, profile ceiling, and revocation state before
serving HLS or negotiating WHEP. The edge may know the internal media endpoint;
the browser-facing catalogue and route contracts may not.

## Ownership Boundaries

| Concern | Authoritative owner | Browser projection |
| --- | --- | --- |
| Camera identity, department, lifecycle | Phase 2 camera service | Opaque camera reference, display name, safe location label, state, revision |
| Stream endpoint and credentials | Phase 2 stream service and secret provider | Never exposed |
| Health, probes, capabilities | Phase 2 stream services | Sanitized status, reason band, freshness, completeness, safe codec/rendition summary |
| Playback authorization | Future playback control producer | Opaque session reference, expiry, state, allowed transports, profile ceiling |
| HLS/WHEP transport | Internal media gateway behind media edge | Same-origin or exact allowlisted session path; no camera locator |
| Resource profile | Server ceiling plus P5 capability projection | Effective profile and safe downgrade reason |
| Workspace layout | Future server-side workspace producer | Revisioned layout without tokens, locators, media, or protected payloads |
| Analytics and incidents | Phase 3/4 producers | Read-only references and handoff context; video does not create event truth |

## Browser-Safe Read Models

### Camera summary

Required safe fields:

- `cameraRef`, display name, safe location label, department scope state;
- lifecycle and operational availability bands;
- aggregate stream-health band, freshness, completeness, last observation time;
- safe capability summary such as supported live viewing, accepted codec family,
  and available rendition bands;
- revision/ETag and typed partial/degraded reasons;
- permission projection for view and diagnostics.

Explicitly excluded fields:

- raw stream or management locator;
- username, password, secret reference, token, certificate material;
- internal address, host, port, filesystem path, provider response, probe body;
- unrestricted coordinates or other fields not permitted for the current
  department and purpose.

### Playback grant

The browser-safe grant contains only:

- opaque `sessionRef` and opaque `cameraRef`/`streamRef`;
- `issuedAt`, `expiresAt`, renewable/closeable flags, current lifecycle state;
- allowed transport order such as `hls` then `whep`, or `whep` then `hls`;
- profile/rendition ceiling and safe denial/degradation reason;
- `locatorExposed: false` as a contract invariant.

Authentication material must not enter URLs, client logs, telemetry, browser
storage, route state, error text, clipboard features, or exported diagnostics.

## Playback State Machine

```text
idle
  -> admission_pending
  -> reason_required
  -> session_requesting
  -> negotiating | loading
  -> playing

playing
  -> quality_changing
  -> profile_downgraded
  -> stalled
  -> reconnect_wait
  -> loading
  -> playing

any active state
  -> expiring
  -> expired | revoked | denied | unsupported | failed
  -> releasing
  -> released
```

Required properties:

- transitions are typed and deterministic;
- every transition has an allowlisted safe reason code;
- the UI cannot skip admission, reason, or authorization states;
- expiry, logout, department change, permission change, route disposal, and
  workspace close trigger immediate local teardown plus best-effort server
  close;
- teardown clears media element sources, source buffers, peer connections,
  timers, retries, object URLs, and in-memory grant material;
- reconnect uses bounded exponential backoff with jitter and a circuit-open
  terminal state; it never refreshes indefinitely in the background;
- HLS fallback after WHEP failure requires the original grant to allow HLS and
  the remaining lifetime to exceed a minimum safe window.

## Admission And Quality Policy

Admission is an intersection, not a benchmark-generated entitlement:

```text
effective budget = minimum(
  server profile ceiling,
  operator role/session ceiling,
  workspace policy ceiling,
  browser codec support,
  advisory Media Capabilities result,
  stream capability and health,
  measured decode/network pressure
)
```

Streams are prioritized in this order:

1. explicitly opened single-camera view;
2. operator-pinned or incident-linked tile;
3. focused/selected visible tile;
4. other visible tiles;
5. near-viewport tiles awaiting admission;
6. off-screen or hidden tiles, which remain released.

The scheduler may reduce rendition, frame rate, tile animation, and the number
of concurrently playing non-pinned streams. It may not silently remove a
selected stream, change department scope, elevate permission, or classify an
event. All denial and degradation is visible in both the video tile and the
authoritative status table.

## Dynamic Profiles

| Profile | Functional scope | Initial validation target | Capacity behavior |
| --- | --- | --- | --- |
| Low resource | Complete catalogue, detail, diagnostics, single live view, saved-layout projection, handoffs, accessible alternatives | C1 mandatory; C4 layout may be present with one active and deferred tiles | Conservative rendition and decode budget; no feature removal |
| Enhanced workstation | Same workflows | C1 and C4 | More simultaneous streams and higher rendition where measured conditions permit |
| Control room | Same workflows with monitor-wall composition | C1, C4, and C10 | Larger active budget, multi-monitor layout, bounded wake-lock option |
| Owned GPU lab | Same workflows; laboratory evidence only | C1, C4, and C10 on declared owned hardware | Hardware decode/acceleration may raise quality; no claim until measured |
| Future server | Same operator contract with server-side media capacity | C1/C4/C10 contract projection only in P5.3 | Server admission remains bounded and does not imply browser decode capacity |

The Phase 3 infrastructure classes (`portable_cpu`, `owned_gpu_lab`,
`standalone_server`, `kubernetes_cluster`) and P5 UI profiles (`low_resource`,
`enhanced`, `control_room`, `future_server`) require an explicit mapping
contract. No client string alone activates a server or GPU capability.

## Transport Policy

### HLS baseline

- Use an internal rendition manifest with bounded variants and safe codec
  metadata.
- Prefer hls.js/MSE where request headers are required and supported.
- Allow native HLS only behind a same-origin authentication mechanism that does
  not put bearer material in a URL.
- Treat `MediaSource.isTypeSupported()` and Media Capabilities as advisory.
- Enforce buffer, retry, segment, response-size, origin, and redirect bounds.

### WHEP enhancement

- Pin the exact IETF draft and record it in evidence.
- Require HTTPS, exact destination validation, DTLS-SRTP, bounded ICE/TURN
  policy, zero arbitrary redirects, and explicit DELETE teardown.
- Treat negotiation, SDP, and ICE material as sensitive transient state.
- Maintain an HLS fallback and a feature kill switch.
- Make no WHEP conformance or latency claim before exact implementation and
  owned-lab evidence.

## Workspace Persistence

Saved layouts are future server-side records with:

- opaque workspace and camera references;
- owner/department scope and purpose;
- named layout, tile order, tile size, selected quality preference, and revision;
- optimistic concurrency through ETag/`If-Match`;
- explicit conflict, stale, deleted, and inaccessible states;
- no session grant, token, locator, media buffer, captured frame, analytics
  payload, or protected display text.

Until the producer exists, layouts are generated fixtures or memory-only for
the current browser session. `localStorage`, IndexedDB, Cache Storage, service
workers, and URL serialization are prohibited for protected workspace state.

## Cross-Portal Handoffs

Command and GIS may open P5.3 with only:

- opaque `cameraRef`;
- bounded UTC time context;
- source portal and allowlisted return route;
- optional opaque incident/investigation reference already authorized for the
  current operator.

P5.3 may return the same opaque references and a safe playback-state reason.
It does not return a URL, token, frame, recording, or inferred incident.

## Accessibility And Authoritative Alternatives

- Every tile is paired with camera name, health, freshness, capability,
  playback state, and safe failure reason in semantic text.
- Catalogue, diagnostics, and monitor-wall contents remain available through
  an authoritative list/table, independent of canvas or video rendering.
- All commands are keyboard reachable with visible focus and no keyboard trap.
- Status changes use bounded live announcements; frequent frame/bitrate updates
  are not announced.
- State never depends on color, motion, or the video image alone.
- Stable aspect ratios prevent controls and text from shifting when media loads.
- Operators can pause or release playback. Reduced-motion preferences are
  honored for transitions and status visualization.

## Observability Boundary

Permitted dimensions are low-cardinality values such as portal, view type,
transport, effective profile, lifecycle state, rendition band, and safe reason
code. Camera references, stream references, departments, users, locations,
coordinates, locators, SDP, ICE candidates, tokens, playlist paths, free text,
and provider details are prohibited as labels or client logs.

## Planning Outcome

This architecture is non-effective until the owner selects the P5.3 decisions,
accepts the reconciled planning package, and separately authorizes an exact
start package. Planning completion adds zero Phase 5 product points.
