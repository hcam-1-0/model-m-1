# P5.3 Owner Decision Packet

Status: owner decisions pending; every option below is non-effective

Select one letter for each decision. The recommended profile is:

`D / A / A / A / A / A / A / A / A / A / A / A`

## D-P5.3-001: Workspace Topology

**A. One page inside Command Center.** Keeps navigation short, but overloads the
primary situational surface and weakens detailed camera workflows.

**B. One standalone Live Center.** Gives media maximum space, but separates
catalogue, diagnostics, and Operations ownership too strongly.

**C. Camera pages only inside Operations.** Clear ownership, but multi-camera
and monitor-wall work become cramped and hard to preserve across navigation.

**D. Operations owns Catalogue, Camera Detail, and Diagnostics; connected Live
Workspace and Monitor Wall handle media. Recommended.** Command remains primary,
Operations remains authoritative for cameras, and media gets a focused surface
without becoming a separate product.

## D-P5.3-002: Browser And Media Security Boundary

**A. Same-origin H-CAM media edge with opaque short-lived grants; internal
MediaMTX and camera locators remain server-only. Recommended.** Supports header
or protected same-origin authentication, central revocation, exact destination
policy, and browser-safe DTOs.

**B. Browser receives the internal MediaMTX URL and short token.** Simpler, but
exposes infrastructure and creates URL, CORS, CSP, logging, and rotation risks.

**C. Browser connects directly to cameras.** Avoids the gateway but violates
network, credential, codec, audit, and policy boundaries.

**D. Public reverse proxy with query-string token.** Easy to demonstrate, but
bearer material can leak through logs, history, referrers, and copied URLs.

## D-P5.3-003: HLS Playback Engine

**A. hls.js/MSE baseline behind a typed adapter, with native HLS only through a
safe same-origin auth path. Recommended.** Provides controlled request handling
and broad browser coverage without hand-writing HLS logic.

**B. Native `<video>` HLS only.** Minimal code but incomplete cross-browser
support and weak header-based authentication control.

**C. Shaka Player.** Mature and broad, but introduces DASH, DRM, and offline
surface that P5.3 does not need.

**D. Custom HLS/MSE implementation.** Maximum control with excessive protocol,
security, and compatibility risk.

## D-P5.3-004: WHEP Role

**A. Optional, default-off, draft-pinned WHEP adapter with HLS fallback and kill
switch. Recommended.** Enables lower-latency research without making an
Internet-Draft or WebRTC availability a baseline dependency.

**B. WHEP-first and mandatory.** Prioritizes latency, but blocks browsers and
networks where WebRTC negotiation is unavailable and increases privacy risk.

**C. HLS only, no WHEP contract.** Safest initial delivery, but discards a
valuable future low-latency lane.

**D. Separate HLS and WHEP user experiences.** Exposes protocol complexity to
operators and creates divergent workflows.

## D-P5.3-005: Effective Media Profile

**A. Intersection of server ceiling, role/session ceiling, workspace policy,
stream health/capability, browser support, advisory Media Capabilities, and
measured pressure. Recommended.** Fails closed and adapts without trusting one
client or hardware signal.

**B. Browser benchmark chooses profile automatically.** Adaptive but outside
current hardware-testing authority and vulnerable to drift or manipulation.

**C. Operator selects unrestricted quality.** Simple but can exceed server,
network, decoder, and security policy.

**D. Fixed global profile.** Predictable but wastes capable hardware and can
overload low-resource systems.

## D-P5.3-006: Multi-Stream Admission And Scheduling

**A. Weighted deterministic scheduler using explicit intent, pin/focus,
visibility tier, health, and bounded stream/decode/network budgets.
Recommended.** Admits incrementally, protects selected work, and explains
defer/downgrade decisions.

**B. Auto-play every tile in the saved layout.** Visually immediate but creates
unbounded load and hidden background traffic.

**C. First-come, first-served only.** Deterministic but ignores operational
focus and can block a selected camera.

**D. AI-selected stream priority.** Outside current model and authority scope
and difficult to explain or reproduce.

## D-P5.3-007: Recovery And Fallback

**A. Typed deterministic state machine with bounded in-transport recovery,
jittered reconnect, cooldown, circuit breaker, WHEP-to-HLS fallback, and manual
terminal recovery. Recommended.** Avoids retry storms and preserves visible
state.

**B. Retry forever.** Maximizes automatic recovery but consumes resources and
hides persistent failure.

**C. Fail once and require reload.** Simple, but poor for intermittent networks
and monitor-wall operation.

**D. Let each player library decide.** Reduces local code but creates
inconsistent semantics, telemetry, and teardown.

## D-P5.3-008: Playback Session Lifecycle

**A. One opaque grant per stream with short expiry, bounded renewal, immediate
revocation, idempotent close, and abandoned-session lease recovery.
Recommended.** Limits replay and keeps server capacity authoritative.

**B. One long-lived workspace token.** Reduces requests but enlarges the blast
radius and complicates per-stream revocation.

**C. Reuse normal login token at the media gateway.** Couples broad application
authority to media delivery and exposes a more valuable credential.

**D. Anonymous internal playback.** Depends on network trust and removes
operator-level authorization and auditability.

## D-P5.3-009: Layout And Preference Persistence

**A. Revisioned server-side department/user layouts with opaque camera refs and
ETags; memory-only fallback until the producer exists. Recommended.** Supports
shared workstations, conflict handling, revocation, and safe cleanup.

**B. LocalStorage or IndexedDB.** Convenient, but retains protected workspace
context across logout and users.

**C. Encode the full layout in the URL.** Shareable, but leaks identifiers and
operational context through history and logs.

**D. No saved layouts.** Safest persistence posture but inefficient for
control-room use.

## D-P5.3-010: Authorized Media Controls

**A. View-only live controls: open, pause/resume, mute, allowed quality band,
pin/focus/reorder/release, fullscreen, diagnostics, and reference-only handoff.
Recording, snapshot, download, export, print, PTZ, and analytics remain absent.
Recommended.** Delivers complete monitoring without widening operational or
evidence authority.

**B. Add snapshots and downloads.** Useful to investigations, but creates new
evidence, retention, privacy, integrity, and export obligations outside P5.3.

**C. Add recording.** Operationally valuable but requires storage, retention,
legal, access, chain-of-custody, and deployment decisions not authorized here.

**D. Add PTZ and camera configuration.** Uses Phase 2 control capabilities but
would introduce sensitive operational actions and collision/interlock risks.

## D-P5.3-011: Accessibility Equivalence

**A. Video plus synchronized authoritative list/table/status, keyboard and
focus completeness, non-color state, bounded announcements, pause/stop, stable
dimensions, and reduced motion. Recommended.** Preserves the same safe camera
and playback information when video is not perceivable or available.

**B. Accessible labels on video controls only.** Helps control operation but
does not provide equivalent camera health or playback state.

**C. Screen-reader summary page.** Creates a second, easily drifting product
path without record-level parity.

**D. Exempt monitor walls from accessibility.** Conflicts with the accepted P5
accessibility architecture and leaves core workflows unequal.

## D-P5.3-012: Validation And Evidence Standard

**A. Deterministic generated C1/C4/C10 media and metadata, contract/state/
security/accessibility/browser/profile/recovery/teardown tests, two clean
replays, exact hashes, declared environment, and separate later owned-lab gate.
Recommended.** Produces reproducible evidence without using real cameras or
claiming production capacity.

**B. One manual browser demo.** Fast but not deterministic and weak on failure,
security, cleanup, and accessibility.

**C. Real Sentinel or camera testing immediately.** More realistic but outside
current authorization and risks coupling the product to the lab.

**D. Unit tests only.** Useful for logic but insufficient for browser media,
resource pressure, CSP, teardown, and visual/accessibility behavior.

## Effect Of Selection

Selections define a reconciled P5.3 planning profile only. They do not authorize
implementation, dependencies, routes, migrations, media runtime, playback
session issuance, cameras, Sentinel, network, recording, snapshots, data,
models, operational actions, deployment, P5.4, or remote Git. The next sequence
is:

1. record the selected profile in a reconciled planning package;
2. obtain exact owner acceptance of that package;
3. prepare one non-effective start package with exact paths, dependencies,
   fixtures, commands, bounds, evidence, and stop conditions;
4. obtain exact start authorization before implementation.
