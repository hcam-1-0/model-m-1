# P5.3 Dependency And Transport Evaluation

Status: planning evaluation only; no dependency resolution, install, import, build, or runtime authorized

## Selection Principles

1. Prefer browser standards and existing P5 packages before adding a library.
2. Add one narrowly scoped media dependency only when it removes material
   protocol and compatibility risk.
3. Keep every transport behind an H-CAM adapter so protocol or library changes
   do not alter operator workflows or authority.
4. Pin exact versions and integrity in a later start package after license,
   provenance, vulnerability, bundle, browser, and maintenance review.
5. Never choose a library because it offers prohibited recording, offline,
   download, DRM, analytics, or direct-camera features.

## HLS Options

| Option | Strengths | Costs/risks | Planning result |
| --- | --- | --- | --- |
| Native `<video>` HLS only | Minimal JavaScript and strong Safari support | Inconsistent non-Safari support; cannot generally attach an Authorization header to native media requests; unsafe if solved with URL tokens | Insufficient as the universal baseline |
| hls.js behind P5 adapter | Narrow HLS/MSE focus, active official project, Apache-2.0, custom request handling, broad desktop browser support | New dependency, MSE/codec variation, bundle/runtime surface, Safari native fallback still needs safe authentication | Preferred baseline candidate |
| Shaka Player | Mature HLS/DASH player, Apache-2.0, broad streaming feature set | Larger surface; DRM/offline/download-adjacent capabilities exceed P5.3 needs and complicate policy | Defer unless later requirements justify it |
| Hand-written HLS/MSE parser | Maximum control | High protocol, buffering, discontinuity, rendition, retry, security, and browser-compatibility risk | Reject |

Recommendation: use a pinned hls.js release behind `HlsPlaybackAdapter` for the
initial generated-only implementation. Use native HLS only when a same-origin
media-edge authentication design works without URL bearer material. Exact
version selection belongs to the start package, not this plan.

## WHEP Options

| Option | Strengths | Costs/risks | Planning result |
| --- | --- | --- | --- |
| No WHEP | Smallest surface and stable HLS baseline | Cannot evaluate lower-latency operation | Acceptable fallback but does not meet the selected innovation direction |
| Small internal adapter using `fetch` and `RTCPeerConnection` | Exact bounded implementation of required POST/PATCH/DELETE lifecycle; no broad dependency | Must track changing Internet-Draft and implement redirect/auth/ICE/teardown carefully | Preferred provisional approach after exact start review |
| Third-party WHEP client library | Potentially faster integration | Maturity, version drift, maintenance, transitive dependency, and contract-fit uncertainty | Evaluate only if an exact maintained candidate passes later review |
| Direct MediaMTX-specific browser logic throughout UI | Fast initial demo | Couples product state to one gateway and makes future protocol replacement difficult | Reject; MediaMTX belongs behind adapter and media edge |

Recommendation: keep WHEP default-off behind `WhepPlaybackAdapter`, bind it to
`draft-ietf-wish-whep-04` for the current planning package, and require HLS
fallback. A standards change triggers adapter compatibility review, not UI
rewrites.

## Browser APIs

| API | Role | Authority level |
| --- | --- | --- |
| `MediaSource.isTypeSupported()` | Coarse codec/container preflight | Advisory only |
| Media Capabilities `decodingInfo()` | Supported/smooth/power-efficient hint | Advisory only; minimized to prevent fingerprint expansion |
| HTML media events/state | Playback lifecycle input | One input to typed state machine, never sole truth |
| WebRTC `getStats()` | Optional WHEP health input | Locally aggregated and minimized |
| Page Visibility | Hidden-page admission/release signal | Cannot grant or preserve authority by itself |
| Intersection Observer | Visible/near/off-screen tile priority | Approximate scheduling input only |
| Screen Wake Lock | Explicit control-room convenience | Optional, user-controlled, never required |

## Existing Dependency Reuse

- Reuse P5.1 React, TypeScript, Vite, Vitest, Playwright, Zod, query, routing,
  localization, capability, observability, and application-shell foundations.
- Reuse P5.1 `playback-contracts` as the starting browser-safe boundary, but
  extend it additively for lifecycle, transport, admission, and teardown.
- Reuse accepted P5.2 Command/GIS routes and opaque handoff conventions.
- Reuse internal MediaMTX only through the future media-edge contract.
- Do not import the isolated Phase 2.5 Sentinel lab UI or adapter source into
  the main product.

## Start-Package Review Required

Before any dependency change, the exact start package must freeze:

- package name, version, registry source, integrity, license, maintainers, and
  release date;
- direct and transitive dependency graph;
- vulnerability database refresh time and any unavailable refresh limitation;
- production/browser bundle entry points and tree-shaking behavior;
- browser/codec support matrix and fallback behavior;
- CSP, worker, request-header, credential, redirect, logging, and telemetry
  implications;
- size budget and low-resource mode impact;
- SBOM/provenance records and rollback plan;
- explicit exclusion of offline storage, recording, capture, download, DRM,
  analytics upload, or arbitrary provider connectivity.

## Non-Decision

This evaluation recommends architecture and candidate classes only. It does not
authorize an exact dependency, version, lockfile update, source import, network
request, browser execution, or media playback.
