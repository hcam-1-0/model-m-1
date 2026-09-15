# P5.3 Camera And Live Monitoring Threat Model

Status: planning baseline; generated-only validation proposed

## Assets

- department-scoped camera and stream metadata;
- playback authority, opaque session references, and transient credentials;
- internal media destinations and camera locators;
- operator identity, role, department, purpose, and audit context;
- live media confidentiality and availability;
- workspace layouts and cross-portal handoff context;
- browser, network, decoder, GPU, CPU, and session capacity;
- security, audit, and operational-signal integrity.

## Trust Boundaries

1. Browser and application shell.
2. H-CAM API and authorization boundary.
3. Playback control and same-origin media edge.
4. Internal media gateway.
5. Camera/stream endpoint and secret-provider boundary.
6. Optional WHEP peer, ICE, and TURN boundary.
7. Generated lab environment, isolated from real providers and production data.

## Threat Register

| ID | Threat | Required control | Generated validation |
| --- | --- | --- | --- |
| T01 | Raw camera or management locator reaches the browser | Dedicated allowlist DTO and recursive forbidden-key/value checks | Seed locator-like values in every nested source field and require absence |
| T02 | Bearer token appears in URL, history, referrer, log, error, or telemetry | Opaque grant, Authorization header or protected same-origin mechanism, no query token | Inspect route, request, console, telemetry, and error projections |
| T03 | Grant persists in local/browser cache | Memory-only transient holder, no localStorage/IndexedDB/Cache API/service worker | Reload/logout test and storage API instrumentation |
| T04 | Grant replay against another stream, operator, department, or origin | Audience, subject, stream, department, origin, nonce, expiry, and revision binding | Cross-binding and replay vectors fail closed |
| T05 | XSS steals grant or redirects media | Strict CSP, Trusted Types plan, no unsafe script/eval, short lifetime, minimized JS exposure | Static CSP and injected markup/URL vectors |
| T06 | Clickjacking or deceptive fullscreen hides context | `frame-ancestors`, visible camera identity/state, explicit fullscreen transition | Framing denial and fullscreen state tests |
| T07 | Mixed content or invalid TLS weakens signaling/media | Secure context, verified HTTPS/WSS, no verification disable | HTTP and invalid-certificate projections denied |
| T08 | CORS policy allows arbitrary origins | Same-origin default, exact allowlist, credentials policy, preflight tests | Unknown/null/wildcard origin vectors denied |
| T09 | Malicious playlist or redirect contacts an arbitrary destination | Media edge owns destination, exact origin and redirect policy, response bounds | Cross-origin and redirect-chain fixtures denied |
| T10 | HLS manifest or segment creates memory/network exhaustion | Manifest/variant/segment/response/buffer/time bounds and cancellation | Oversized, recursive, high-variant, slow, and endless fixtures |
| T11 | WHEP redirect changes POST semantics or leaves allowlist | Draft-pinned 307 policy, exact location validation, no arbitrary redirect | 301/302/303/cross-origin/credential-bearing redirect vectors |
| T12 | SDP/ICE exposes addresses or reaches restricted networks | Bound ICE/TURN policy, no raw retention, exact peer consent/destination controls | Hostile candidate, oversized SDP, and disallowed TURN fixtures |
| T13 | WebRTC diagnostics fingerprint browser or operator network | Minimized capability report and low-cardinality aggregate stats | Forbidden field and cardinality checks |
| T14 | Auto-opening many streams exhausts bandwidth, decoder, GPU, or server | Server admission, client scheduler, C1/C4/C10 ceilings, visibility/focus priority | Over-admission and concurrent-window tests |
| T15 | Hidden page continues unnecessary playback | Visibility-aware bounded grace and release; pinned exception must be explicit | Hide/show sequence and release verification |
| T16 | Retry storm amplifies outage | Bounded exponential backoff, jitter, cooldown, circuit breaker, cancellation | Deterministic stall/outage fleet simulation |
| T17 | Stale health is displayed as live truth | Freshness, completeness, observed time, stale/degraded state | Clock and delayed-event scenarios |
| T18 | Client event mutates truth directly | Event invalidates authoritative query only | Forged, duplicate, old, and out-of-order event tests |
| T19 | Role or department changes while media remains active | Server revocation plus immediate client teardown and revalidation | Logout, switch, privilege-loss, and cross-window tests |
| T20 | Browser close or crash leaves a server session consuming capacity | Short lease/expiry, idempotent close, abandoned-session recovery | Missing-close and lease-expiry simulation |
| T21 | Layout stores protected identifiers, token, locator, or media | Server-side allowlist schema; opaque refs only; recursive rejection | Malicious layout payload vectors |
| T22 | Concurrent layout edits overwrite one another | ETag/If-Match and explicit conflict resolution | Two-revision deterministic conflict test |
| T23 | Video becomes the sole source of operational state | Authoritative synchronized list/table and text reason/state | Disable video/MSE/WebRTC and verify complete workflow |
| T24 | Frequent status updates overwhelm assistive technology | Bounded announcements and separate silent high-rate metrics | Announcement rate and focus stability test |
| T25 | Hardware profile changes operator authority | Profile intersection with invariant authorization and feature contracts | Same permission matrix across all profiles |
| T26 | Compromised/generated lab input is mistaken for operational evidence | Generated provenance, visible environment classification, no production claim | Manifest/hash/label/claim checks |
| T27 | Decoder or browser media bug processes hostile content | Generated bounded media, current supported browsers, sandboxed origins, prompt patching | Malformed synthetic segments and clean failure state |
| T28 | Recording/snapshot/download feature is accidentally exposed | Capability denylist, no command, no route, no browser persistence, no export handler | DOM/route/contract forbidden-action scans |
| T29 | PTZ or camera-control authority leaks into live UI | Separate control contract and explicit P5.3 deny | Control field/action fixture must remain unavailable |
| T30 | Telemetry leaks camera, location, operator, token, or raw error | Low-cardinality schema, client/server redaction, bounded reason taxonomy | Recursive forbidden-key/value and cardinality tests |

## Fail-Closed Conditions

Playback does not begin when any of the following is unknown, stale beyond its
policy, or invalid:

- operator session, department, permission, purpose, or stream eligibility;
- opaque grant signature/binding, expiry, revocation, audience, or profile;
- browser-supported codec/transport;
- media-edge origin, TLS, CSP, redirect, or destination policy;
- workspace/session capacity;
- safe teardown registration;
- synchronized non-video status availability.

Failure does not fall back to a raw stream URL, direct camera connection,
query-string token, public proxy, external player, permissive CSP, or disabled
certificate verification.

## Privacy And Retention

- No media is recorded, captured, downloaded, exported, printed, or cached as a
  P5.3 feature.
- No analytics, biometric, owner, registration, watchlist, Government, or
  private-data processing is introduced.
- Playback grants and negotiation data exist only as transient in-memory state.
- Client diagnostic records contain only bounded reason/state/profile/transport
  fields and duration/count buckets.
- Generated fixtures contain no copied Sentinel, camera, private, or Government
  media.

## Residual Risks

- A compromised browser or operating system can observe displayed media; the
  web application cannot eliminate screen recording outside its control.
- Codec support and hardware acceleration vary by browser, operating system,
  driver, and policy. Capability APIs are advisory and require runtime evidence.
- WHEP remains an Internet-Draft and may change. The optional adapter must be
  version-pinned and replaceable.
- Browser crash or network partition can delay explicit close, so short server
  leases and abandoned-session recovery remain mandatory.
- Accessibility conformance needs later manual assistive-technology review in
  addition to generated/static checks.

## Threat Acceptance Rule

No threat is accepted by this planning document. A later start package must map
every threat to exact source, tests, evidence, and a residual-risk owner. Any
unmapped T01-T08, T14, T19, T23, T25, T28, or T30 blocks P5.3 acceptance.
