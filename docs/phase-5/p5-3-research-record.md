# P5.3 Camera And Live Monitoring Research Record

Status date: 2026-09-08

Status: official primary-source research complete; no product, dependency, media, network, or runtime action performed

Authority: `D-P5.3-PLAN-AUTH`

## Research Questions

1. Which browser transport should be the dependable baseline and which should remain optional?
2. How can the browser play live video without receiving camera locators, reusable credentials, or long-lived tokens?
3. Which browser signals are useful for admission and quality selection without becoming hardware or performance claims?
4. How must a multi-camera workspace recover from stalls, expiry, revocation, logout, and scope change?
5. How can low-resource mode remain functionally complete while stronger hardware increases only capacity and quality?
6. Which accessible non-video representations are authoritative when video is unavailable or unusable?

## Official Sources And Findings

| Source | Planning finding | P5.3 application |
| --- | --- | --- |
| [RFC 8216: HTTP Live Streaming](https://www.rfc-editor.org/rfc/rfc8216.html) | HLS defines media playlists, master playlists, variant streams, target duration, and client reload behavior for unbounded media. It supports adaptation among declared renditions. | HLS is the baseline transport. The server advertises a bounded rendition set; the client chooses only within the authorized profile and may downgrade on measured pressure. |
| [Apple HLS Authoring Specification](https://developer.apple.com/documentation/http-live-streaming/hls-authoring-specification-for-apple-devices/) | Apple's authoring guidance defines interoperability constraints for HLS assets and low-latency parts. | Generated fixtures need an explicit codec, container, segment, keyframe, and playlist profile. No real-camera compatibility claim follows from synthetic validation. |
| [W3C Media Source Extensions](https://www.w3.org/TR/media-source-2/) | MSE lets JavaScript append media segments to an `HTMLMediaElement`; `isTypeSupported()` is a coarse capability check. MSE 2 remains a Working Draft and warns implementers about instability. | Use stable MSE behavior through a pinned HLS adapter. Treat worker construction and `ManagedMediaSource` as progressive enhancements, not baseline requirements. |
| [W3C Media Capabilities](https://www.w3.org/TR/media-capabilities/) | `decodingInfo()` reports `supported`, `smooth`, and `powerEfficient` for a declared configuration. | Use the result as advisory input to quality admission. It cannot grant authority or prove sustained performance on a specific device. |
| [WHATWG HTML media element](https://html.spec.whatwg.org/multipage/media.html) | Media elements expose network state, ready state, errors, buffering, waiting, stalled, and playback events; user agents may suspend activity. | Build a typed state machine with explicit timeouts and multiple signals. No single media event is accepted as stream truth. |
| [W3C WebRTC](https://www.w3.org/TR/webrtc/) | `RTCPeerConnection` supplies standardized negotiation and inbound RTP statistics. | A WHEP adapter may derive bounded local health signals such as packet loss, jitter, decoded frames, and dropped frames. Raw candidate, SDP, address, and per-camera data are not telemetry labels. |
| [W3C WebRTC Statistics](https://www.w3.org/TR/webrtc-stats/) | The statistics model includes inbound packets, loss, jitter-buffer, frames, freezes, and decode data. | Only minimized aggregates and allowlisted reason codes may leave the browser. Stats remain diagnostic input, not evidence of event truth or operator authority. |
| [IETF WHEP Internet-Draft](https://datatracker.ietf.org/doc/draft-ietf-wish-whep/) | As of 2026-09-08 the active document is `draft-ietf-wish-whep-04`, an Internet-Draft in working-group last call, not an RFC. It defines HTTP session creation, redirection, authorization, trickle ICE, and DELETE teardown. | WHEP remains provisional, version-pinned, optional, and default-off. HLS fallback is mandatory and no WHEP conformance claim is allowed. |
| [RFC 8826: WebRTC Security Considerations](https://www.rfc-editor.org/rfc/rfc8826.html) | WebRTC can reveal network information, consume significant bandwidth, and create a browser-mediated attack surface toward otherwise restricted destinations. | Permit only a same-origin or exact allowlisted media edge, bound ICE/TURN policy, bounded sessions, teardown, and minimized diagnostics. Arbitrary candidates or destinations are denied. |
| [RFC 8827: WebRTC Security Architecture](https://www.rfc-editor.org/rfc/rfc8827.html) | WebRTC depends on authenticated origins, HTTPS signaling, DTLS-SRTP, and browser enforcement. | Require secure contexts and verified transport. Mixed content, insecure signaling, and unapproved peer destinations fail closed. |
| [RFC 6750: OAuth 2.0 Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html) | Bearer tokens in URI query parameters are discouraged because URLs are commonly logged and otherwise exposed. TLS and protected token handling are required. | Never place a playback bearer token in a query string, URL, route state, log, metric, browser storage, or error. Prefer a same-origin opaque grant and an Authorization header where the client can set one. |
| [W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/) | CSP separates destinations for media, connections, workers, scripts, and frames; its WebRTC restriction is still evolving. | Freeze exact `media-src`, `connect-src`, `worker-src`, `script-src`, and `frame-ancestors` policy. A draft `webrtc` directive is defense in depth, not the only control. |
| [W3C Page Visibility](https://www.w3.org/TR/page-visibility-2/) | A document exposes visibility changes and may become hidden without closing. | Hidden workspaces release or reduce non-pinned sessions after a bounded grace period. Visibility does not override explicit operator intent or accessibility needs. |
| [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/) | Intersection observations are asynchronous and intentionally not pixel-perfect. | Use visibility tiers to defer off-screen tiles; do not use them as an authorization decision or exact workload measurement. |
| [W3C Screen Wake Lock](https://www.w3.org/TR/screen-wake-lock/) | Wake locks require a secure, visible document and can be denied or released by the user agent. | Offer wake lock only as an explicit control-room convenience. Playback and incident handling must remain complete without it. |
| [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Keyboard operation, focus visibility, status messages, reflow, labels, contrast, and alternatives remain testable requirements. | Every live view has an authoritative table/list/status alternative, stable focus, non-color state, pause/stop, and bounded announcements. Video is never the only carrier of health or incident information. |

## Evaluated Implementation References

| Candidate | Evidence | Planning result |
| --- | --- | --- |
| [hls.js](https://github.com/video-dev/hls.js/) | Official Apache-2.0 project for HLS playback through MSE, with native HLS fallback guidance. | Preferred narrow HLS dependency candidate. Pin and review an exact release only in a later authorized start package. |
| [Shaka Player](https://github.com/shaka-project/shaka-player) | Official Apache-2.0 player covering DASH, HLS, DRM, and offline features. | Not preferred for the first P5.3 slice. Its larger feature surface includes capabilities that are prohibited or unnecessary here, especially offline storage. |
| [MediaMTX browser guidance](https://github.com/bluenviron/mediamtx/blob/main/docs/4-read/07-web-browsers.md) | Official project guidance documents HLS and WHEP browser paths and Authorization-header use. | Reuse the accepted internal MediaMTX role, but keep it behind a browser-safe H-CAM media edge. Direct browser-to-camera and query-token patterns remain prohibited. |

## Repository Evidence Considered

- Phase 2 owns camera, stream, health, probe, ONVIF capability, control, and playback-session operations under department-scoped RBAC and audit controls.
- The Phase 2 stream DTO includes raw locator and management-locator fields. It therefore cannot be reused as a general browser DTO.
- The Phase 2 playback response returns a short-lived playback URL and access token. P5.1 instead exposes an opaque playback-session projection with `locatorExposed: false`; a producer contract is missing between them.
- P5.1 already supplies the application shell, typed client, authorization projection, capability profiles, safe query policy, observability boundary, and provisional playback adapter.
- P5.2 establishes Command Center as primary and GIS Center as a connected specialist. P5.3 must accept and return opaque camera references without exposing media destinations.
- Phase 3.6 allows hardware to change admitted load and optimization only. Model, event, authority, security, and operator semantics remain constant.
- The Phase 2.5 Sentinel lab is isolated. It may later validate an adapter through a separately authorized lab path, but it is not a production dependency or source of P5.3 truth.

## Conclusions

1. HLS is the baseline transport. A pinned hls.js adapter provides MSE playback where needed; native HLS is allowed only through an authentication design that does not put bearer material in a URL.
2. WHEP is an optional low-latency enhancement pinned to the exact active draft, protected by HTTPS, exact destination policy, bounded ICE/TURN behavior, explicit teardown, and HLS fallback.
3. Add a same-origin media-edge contract that turns an opaque, short-lived browser grant into media access without exposing internal camera locators or reusable credentials.
4. Use browser codec and Media Capabilities results as advisory inputs. The server profile ceiling, current session health, operator intent, and bounded workspace budgets remain authoritative.
5. Admit streams incrementally. C1 is mandatory everywhere; C4 and C10 are profile-dependent capacity levels, not different product editions.
6. Use generated synthetic media only during implementation until a separate owned-lab authorization exists. No real camera, Sentinel, or operational claim is permitted.

## Non-Claims

- No HLS, MSE, WebRTC, WHEP, MediaMTX, WCAG, CSP, or dependency conformance is claimed.
- No dependency was downloaded, installed, imported, built, or executed.
- No media playlist, segment, SDP, ICE candidate, camera, provider, Sentinel, or other network destination was contacted.
- No browser, codec, GPU, CPU, playback, latency, capacity, accessibility-technology, or monitor-wall runtime test was performed.
- No recording, snapshot, download, export, model, inference, Government data, private data, operational action, or deployment occurred.
