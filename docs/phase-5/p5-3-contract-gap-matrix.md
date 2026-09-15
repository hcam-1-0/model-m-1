# P5.3 Contract Gap Matrix

Status: planning inventory; no backend or frontend contract is implemented by this document

## Existing Contract Assessment

| Existing capability | Current owner | Reuse status | P5.3 constraint |
| --- | --- | --- | --- |
| Camera catalogue and detail | Phase 2 camera API | Partial | Existing stream projections contain fields that must not reach a general browser DTO. |
| Stream list and detail | Phase 2 stream API | Partial | Browser-safe projection must exclude locator, management locator, internal destination, and secret references. |
| Health and probe history | Phase 2 health/probe APIs | Partial | Normalize to bounded safe reason bands; do not expose raw probe bodies or exception details. |
| ONVIF capability latest/history | Phase 2 capability APIs | Partial | Expose only safe media capability summaries. ONVIF service URLs and device-management details remain server-only. |
| Playback-session issue | Phase 2 playback API | Contract mismatch | Current response contains playback URL and token; P5.1 expects opaque session state with `locatorExposed: false`. |
| Playback proposal adapter | P5.1 playback contracts | Foundation only | Needs a real producer projection, renewal/revocation/close lifecycle, transport choice, and media-edge binding. |
| Dynamic capability profiles | Phase 3.6 and P5.1 | Partial | Infrastructure and UI profile names require an explicit mapping; authority must remain invariant. |
| Command/GIS navigation | P5.2 | Reusable | P5.3 must define camera-focused inbound/outbound handoff with opaque references and safe return state. |
| Phase 2.5 Sentinel lab | Isolated lab branch/repository | No production reuse | A later adapter validation may target it under separate lab authority; P5.3 cannot depend on it. |

## Producer Gaps

| ID | Missing or incomplete producer contract | Required behavior | Failure if unresolved | Intended workstream |
| --- | --- | --- | --- | --- |
| P5.3-G01 | Browser-safe camera summary DTO | Opaque refs, safe labels, lifecycle, health, freshness, completeness, capability summary, revision | Raw server fields may leak to the browser or catalogue remains generated-only | W1/W2 |
| P5.3-G02 | Combined paginated camera/stream query | Stable sort, bounded filters, cursor, revision, partial-source state | Client joins create inconsistent pages and freshness | W1/W2 |
| P5.3-G03 | Sanitized diagnostics projection | Safe probe/capability chronology, reason taxonomy, staleness, no raw responses | Operators cannot diagnose safely; backend detail leaks | W2 |
| P5.3-G04 | Opaque playback proposal response | Session ref, expiry, allowed transport order, profile ceiling, `locatorExposed: false` | Existing raw URL/token response conflicts with P5.1 browser contract | W3 |
| P5.3-G05 | Same-origin media-edge exchange | Convert opaque grant into media access without browser-visible internal locator or URL token | Native and MSE media cannot authenticate safely and consistently | W3 |
| P5.3-G06 | Playback renewal/revocation/close | Bounded renewal, idempotent close, immediate revocation, typed terminal reasons | Expired sessions loop or continue after logout/scope change | W3 |
| P5.3-G07 | Server-side active-session admission | Per operator/department/profile ceilings, idempotency, cooldown, lease and abandoned-session recovery | Browser-only limits are bypassable and inconsistent | W3/W6 |
| P5.3-G08 | HLS rendition and codec summary | Bounded variants, codec strings, resolution, frame-rate band, bitrate band, segment profile | Client guesses quality or contacts arbitrary playlist data | W4 |
| P5.3-G09 | HLS media-edge origin contract | Exact origins, redirect rules, cache/no-store policy, header/cookie mechanism | CSP or authorization becomes overbroad; tokens leak in URLs | W3/W4 |
| P5.3-G10 | WHEP session contract | Draft version, endpoint class, POST/PATCH/DELETE lifecycle, auth, redirect, timeout, ICE/TURN bounds | Optional low-latency path is ambiguous and unsafe | W5 |
| P5.3-G11 | Browser capability report | Versioned allowlisted codec/MSE/WebRTC/Media Capabilities projection with anti-fingerprinting minimization | Profile selection trusts unbounded client claims | W4/W7 |
| P5.3-G12 | Profile mapping contract | Map Phase 3 infrastructure classes to P5 UI profiles and media budgets | Laptop, GPU lab, server, and cluster semantics drift | W6/W7 |
| P5.3-G13 | Playback invalidation event | Opaque session/stream ref, reason, revision, observed time; event only invalidates query | Logout, revocation, health, and permission changes do not converge | W3/W6 |
| P5.3-G14 | Minimized client media signal contract | Low-cardinality aggregate state, transport, profile, quality band, safe reason, duration bucket | Diagnostics become blind or telemetry leaks protected identifiers | W7 |
| P5.3-G15 | Server-side workspace layout API | Department/user scope, opaque refs, ETag, conflict/deleted state, no token/locator/media | Layouts become unsafe browser persistence or last-write-wins | W6 |
| P5.3-G16 | Cross-portal live handoff | Camera ref, bounded UTC context, source/return route, optional authorized case ref | Command/GIS navigation leaks state or loses context | W1/W6 |
| P5.3-G17 | Monitor-wall lease and window policy | Independent window revalidation, active owner, bounded lease, release on close | Multiple windows exceed budgets or preserve stale authority | W6/W7 |
| P5.3-G18 | Generated media and scenario manifest | Unique C1/C4/C10 assets, hashes, codecs, playlists, deterministic faults, zero protected data | Tests are not reproducible or accidentally rely on external media | W1/W8 |
| P5.3-G19 | Capacity evidence schema | Declared machine/browser, active/deferred counts, latency buckets, dropped-frame bands, limitations | C1/C4/C10 results become misleading production claims | W7/W8 |
| P5.3-G20 | Accessibility-equivalent status projection | Same camera, health, freshness, lifecycle, and controls as each tile | Video becomes the sole information channel | W2/W6/W7 |

## Browser-Safe Projection Rules

### Allowed

- opaque references;
- display-safe camera name and approved location label;
- lifecycle and health bands;
- freshness, completeness, revision, and safe timestamps;
- safe codec family and rendition bands;
- permission and feature capability flags;
- typed safe reason codes and retry/cooldown state.

### Denied

- RTSP, ONVIF, HLS-origin, WHEP-origin, internal gateway, management, or secret
  locator;
- username, password, secret reference, bearer token, cookie value,
  certificate/private-key material;
- raw IP, host, port, SDP, ICE candidate, playlist, probe response, exception,
  provider payload, filesystem path, or database detail;
- camera image, snapshot, recorded segment, downloadable object, model output,
  or Government/private record.

## Contract Design Requirements

1. All list operations use bounded server pagination and stable sort keys.
2. Detail and layout mutations use revisions/ETags; no last-write-wins.
3. Events invalidate authoritative queries and never become direct client truth.
4. Every response exposes freshness, completeness, and partial/degraded state.
5. Error responses use the accepted safe problem mapping and allowlisted reason
   codes without backend, media, provider, or security detail.
6. Session creation requires normal authorization plus explicit purpose/reason;
   client route visibility is not permission.
7. Profile changes affect capacity and quality only, not fields, workflows,
   permissions, retention, or security policy.
8. No gap is considered closed by this planning package. A later start package
   must classify each as implemented, simulated, bridged, or still blocked.

## Gap Priority

| Priority | Gaps | Reason |
| --- | --- | --- |
| Blocker | G01, G03, G04, G05, G06, G07, G09 | Required to prevent locator/token leakage and uncontrolled playback |
| Required for baseline | G02, G08, G11, G12, G13, G16, G18, G20 | Required for usable HLS C1/C4 and safe cross-portal operation |
| Required for full P5.3 | G14, G15, G17, G19 | Required for monitor wall, saved layouts, observability, and C10 evidence |
| Optional enhancement | G10 | WHEP remains default-off and cannot block HLS acceptance |

## Closeout Rule

P5.3 cannot be accepted if any blocker gap is silently bypassed. Optional WHEP
may remain disabled with a documented gap, but HLS, teardown, accessibility,
and browser-safe projection cannot.
