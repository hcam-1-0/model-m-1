# P5.3 Reconciled Planning R1

Status: owner selections reconciled; exact planning acceptance pending

Selected profile: `D/A/A/A/A/A/A/A/A/A/A/A`

Base package: `P5.3-PLANNING-R0`, SHA-256
`5EF0C24479157668C2236603B2177A5F38001BDF927EA249A1623D0EEB4D281B`

## Reconciled Product Shape

Command Center remains the primary dashboard. The Operations portal owns the
camera catalogue, camera detail, and stream diagnostics. A connected Live
Workspace supports focused single-camera and bounded multi-camera viewing. A
connected Monitor Wall supports C1, C4, and C10 layouts without becoming a
separate source of camera, event, or authorization truth.

The surfaces share one typed camera/live domain and one server-authoritative
session model. Navigation carries only opaque camera, incident, investigation,
and return-context references. It never carries a camera locator, media URL,
token, SDP, ICE candidate, frame, recording, or protected free text.

## Reconciled Browser And Media Boundary

The selected boundary is a same-origin H-CAM media edge with opaque short-lived
grants. The browser-safe camera API returns only allowlisted metadata. The
playback-control producer validates user, role, department, purpose, stream,
health, profile, capacity, expiry, and revocation. The media edge is the only
browser-adjacent component allowed to resolve an approved internal media
gateway destination.

The browser never receives or stores:

- RTSP or ONVIF locators;
- device-service or management locators;
- MediaMTX internal addresses;
- usernames, passwords, secret references, or certificate material;
- reusable or long-lived bearer credentials;
- token-bearing query strings or route state.

The grant is one-stream scoped, short-lived, renewable only within policy,
immediately revocable, and idempotently closeable. Server lease expiry recovers
capacity when a browser cannot close cleanly.

## Reconciled Transport Stack

### HLS baseline

- A typed `HlsPlaybackAdapter` is the mandatory baseline.
- hls.js/MSE is the preferred narrow implementation candidate, but an exact
  package version is deferred to a later start package.
- Native HLS is allowed only when a same-origin authentication mechanism avoids
  bearer material in the media URL.
- Codec and Media Capabilities signals are advisory inputs to admission, not
  authorization or performance evidence.
- Variants, redirects, buffers, retries, segment sizes, timeouts, and origins
  are bounded.

### WHEP enhancement

- A typed `WhepPlaybackAdapter` is optional and default-off.
- The planning baseline pins semantics to `draft-ietf-wish-whep-04`, which is
  not an RFC.
- HTTPS, exact destination validation, bounded redirects, SDP, ICE/TURN,
  output, timeout, and teardown policies are mandatory.
- HLS fallback and a feature kill switch are mandatory.
- No WHEP conformance or operational latency claim is allowed.

## Reconciled Admission Model

The effective media profile is the minimum of:

1. server profile ceiling;
2. operator role and session ceiling;
3. workspace and department policy;
4. stream capability, health, freshness, and completeness;
5. browser codec and transport support;
6. minimized advisory Media Capabilities result;
7. measured current workspace decode and network pressure.

The weighted scheduler prioritizes explicit single-view intent, pinned tiles,
focused and selected tiles, visible tiles, near-viewport tiles, then deferred
off-screen tiles. It admits incrementally and never autoplays every saved tile.
It may reduce non-pinned quality or release hidden/off-screen non-pinned
sessions. It cannot elevate permission, remove an explicit selected workflow,
change event truth, or hide degradation.

## Reconciled Profiles

| Profile | Required product capability | Capacity behavior |
| --- | --- | --- |
| Low resource | Complete catalogue/detail/diagnostics, C1 live view, multi-tile layout with deferred tiles, all handoffs and alternatives | Conservative active count and rendition; no feature removal |
| Enhanced workstation | Same workflows | C4 target and higher rendition when measured state permits |
| Control room | Same workflows plus bounded monitor-wall composition | C10 target, multi-monitor composition, optional explicit wake lock |
| Owned GPU lab | Same workflows and authority | C1/C4/C10 generated and later separately authorized owned-lab evidence |
| Future server | Same operator contract | Higher server-side capacity may be projected, but browser admission remains independent and bounded |

Phase 3 infrastructure profile names and P5 UI profile names require an
explicit mapping contract. A browser profile name cannot activate a GPU,
server, container, or Kubernetes capability.

## Reconciled Recovery Model

The selected typed state machine provides:

- bounded in-transport recovery;
- jittered exponential reconnect;
- per-session retry and workspace reconnect budgets;
- cooldown and circuit-open terminal states;
- WHEP-to-HLS fallback only when the grant allows HLS and remains valid;
- manual retry after cooldown;
- immediate local teardown on expiry, revocation, denial, logout, department
  switch, permission loss, route disposal, window close, or explicit release;
- best-effort idempotent server close and server-side lease recovery.

No retry runs forever or continues invisibly after the workspace is hidden or
closed.

## Reconciled Persistence And Controls

Layouts are revisioned server-side records scoped to an operator and/or
department, use opaque camera references and ETags, and expose explicit
conflict, stale, deleted, and inaccessible states. Until that producer exists,
state is generated or memory-only. Protected workspace state is prohibited
from localStorage, IndexedDB, Cache Storage, service workers, and URLs.

Authorized live controls are limited to open, pause/resume, mute, allowed
quality band, pin, focus, reorder, release, fullscreen, diagnostics, and
reference-only handoff. Recording, snapshot, download, export, print, PTZ,
camera configuration, model inference, analytics activation, dispatch, and
enforcement remain absent.

## Reconciled Accessibility Contract

Every media tile has synchronized authoritative text for camera identity,
health, freshness, completeness, playback lifecycle, transport, profile,
quality band, safe reason, retry/cooldown, and expiry. Catalogue, diagnostics,
workspace, and monitor wall remain fully operable through semantic lists and
tables when video, MSE, WebRTC, WebGL, hardware acceleration, or multiple
monitors are unavailable.

Keyboard access, visible focus, no trap, non-color state, bounded status
announcements, stable media dimensions, pause/release, zoom/reflow of surrounding
content, and reduced motion are mandatory acceptance gates.

## Reconciled Validation Contract

The generated-only validation matrix includes:

- unique C1, C4, and C10 media and metadata fixtures with exact provenance and
  hashes;
- supported, unsupported, malformed, oversized, stalled, expired, revoked,
  fallback, and teardown cases;
- admission, profile upgrade/downgrade, hidden-page, multi-window, logout,
  department-switch, and permission-loss cases;
- recursive locator, token, secret, route, storage, log, telemetry, CSP, CORS,
  redirect, SDP, and ICE negative tests;
- contract, state, unit, component, story, browser, visual, accessibility,
  security, deterministic replay, dependency, SBOM, and limitation evidence;
- two clean deterministic replays and declared test environment;
- a later separate owned-lab gate, not activated by this package.

## Preserved Gaps And Workstreams

All twenty `P5.3-G01` through `P5.3-G20` producer gaps remain open until an
authorized implementation proves each one implemented, simulated, bridged, or
explicitly blocked. The eight workstreams remain frozen at 16 product points:

| Workstream | Weight |
| --- | ---: |
| P5.3-W1 Contracts and generated fixtures | 2.0 |
| P5.3-W2 Catalogue, detail, and diagnostics | 2.0 |
| P5.3-W3 Playback control and media-edge contracts | 2.5 |
| P5.3-W4 HLS baseline and capability selection | 2.5 |
| P5.3-W5 Provisional WHEP and HLS fallback | 1.5 |
| P5.3-W6 Live workspace, monitor wall, and layouts | 2.5 |
| P5.3-W7 Accessibility, security, profiles, and signals | 1.5 |
| P5.3-W8 Validation, evidence, and acceptance | 1.5 |
| **Total** | **16.0** |

No weight or acceptance criterion was rebaselined.

## Exact Progress

- P5.3 owner decisions: **12/12 (100.0000%)**, change **+100.0000 percentage points**.
- P5.3 planning: **8/8 (100.0000%)**, change **+0.0000 percentage points**.
- P5.3 product: **0/16 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **32/100 (32.0000%)**, change **+0.0000 percentage points**.

## Next Gate

Exact owner acceptance of the sealed `P5.3-PLANNING-R1` package is required.
That acceptance may authorize preparation only of a separate non-effective
start package. It does not authorize implementation.

The original one-commit allowance in `D-P5.3-PLAN-AUTH` was consumed by commit
`392a52ce982dd90b5a30de44843a5dfa552956c1`. This reconciliation is not
committed and cannot be committed without new authority.

## Continuing Prohibitions

Product/test implementation, dependency resolution/install/lockfile changes,
source import, backend routes/migrations, frontend/browser/media runtime,
playback-session issuance, providers/network/Sentinel/cameras/media, recording,
snapshot, download, export, print, PTZ, Government/private data, models,
datasets, artifacts, inference, operational actions, containers, Kubernetes,
deployment, P5.4, commit, push, and remote Git remain closed.
