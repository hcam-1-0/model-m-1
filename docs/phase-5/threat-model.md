# Phase 5 Operator Application Threat Model

Status: proposed, non-effective, planning only

## Protected Assets

- authenticated operator session and current principal;
- department, role, purpose, and action capabilities;
- camera and stream metadata;
- short-lived playback-session material;
- hypotheses, alerts, reviews, timelines, evidence references, corrections,
  and operational state;
- ETags, idempotency identities, reasons, and command outcomes;
- audit, security, and evidence-record separation;
- UI contract, build, dependency, and release integrity;
- operator attention, workflow context, and decision quality.

No real protected data is authorized in P5.0 planning.

## Trust Boundaries

1. Operator and managed browser.
2. Portal JavaScript and third-party dependencies.
3. Same-origin web/BFF boundary.
4. H-CAM HTTP service APIs.
5. Browser event-delivery adapter.
6. Playback-session issuer and media delivery boundary.
7. GIS feature/tile providers.
8. Client observability boundary.
9. Build, package, and release pipeline.
10. Cross-window and multi-monitor workspace communication.

The browser is not trusted to enforce authorization or protect a bearer token
against malicious JavaScript. Hidden buttons, route guards, client role state,
and disabled controls are usability mechanisms, not security controls.

## Threat Catalogue

| ID | Threat | Impact | Required planning control |
| --- | --- | --- | --- |
| P5-T01 | Stolen browser token or session | Unauthorized access and commands | Prefer BFF/server session, HttpOnly cookie, bounded expiry, revocation, no token persistence |
| P5-T02 | Cross-site scripting or dependency compromise | Session and displayed-data compromise | Strict CSP, no uncontrolled remote scripts, output encoding, dependency policy, Trusted Types evaluation |
| P5-T03 | CSRF against state-changing command | Unauthorized review, lifecycle, or configuration action | SameSite policy plus explicit CSRF defense; reason, ETag, idempotency, and server authorization remain required |
| P5-T04 | Client-side role or department tampering | Cross-scope disclosure or action | Server-derived principal and row scope; every query/command reauthorized; negative tests |
| P5-T05 | URL or history leakage | Protected identifiers, filters, or tokens exposed | Typed safe URL state; prohibit tokens, locators, evidence, reasons, and sensitive terms in URLs |
| P5-T06 | Persistent browser-cache leakage | Data remains after logout or device reuse | No persistent protected response/media cache by default; no-store; logout cleanup; managed-browser validation |
| P5-T07 | Raw API/exception leakage | Internal data and security details disclosed | Typed safe problem mapping; bounded errors; zero raw body/stack in UI telemetry |
| P5-T08 | Stale ETag command | Operator overwrites newer review or lifecycle state | Mandatory `If-Match`; conflict view; reload and explicit reconsideration; no silent replay |
| P5-T09 | Duplicate mutation | Duplicate review, entry, or transition | Idempotency identity, bounded retry policy, server outcome verification |
| P5-T10 | Event spoofing, replay, or gap | UI shows incorrect current state | Authenticated event channel, schema/version/scope checks, sequence/gap detection, HTTP refetch |
| P5-T11 | Unknown event version | Unsafe interpretation | Quarantine and visible compatibility degradation; never permissive fallback |
| P5-T12 | Direct broker access | Expanded credential and data exposure | Server-mediated event adapter only |
| P5-T13 | Direct camera/ONVIF/RTSP access | Credential, network, camera-control, and privacy exposure | Playback-session boundary; never send management locator or secret reference to browser |
| P5-T14 | Playback token leakage | Unauthorized live viewing | Short lifetime, audience/scope binding, no URL/log/storage leakage, explicit teardown |
| P5-T15 | Unbounded multi-stream fan-out | Camera, server, network, GPU, or browser exhaustion | Profile and server admission ceilings, one active audio source, bounded reconnect, visible degradation |
| P5-T16 | Media persists unexpectedly | Unauthorized recording or evidence creation | No recording/download/snapshot/cache API; teardown and zero-retention evidence |
| P5-T17 | WebRTC IP/local-network exposure | Operator/network privacy leakage | Explicit ICE/candidate policy, managed media server, no browser-to-camera peers, WHEP version pin |
| P5-T18 | Malicious or untrusted map/tile source | Tracking, injection, availability, or attribution failure | Exact destination policy, private-source option, CSP, attribution, integrity and fallback |
| P5-T19 | Unbounded GIS/graph/timeline response | Browser freeze and denial of service | Viewport/time/count/byte/depth bounds, clustering/tiling, virtualization, cancellation |
| P5-T20 | Coordinate or time-zone error | Wrong location or chronology | Explicit CRS/order/time zone, canonical timestamps, conversion tests, visible source time |
| P5-T21 | Confidence or candidate misrepresentation | False identity or operational conclusion | Separate observation/hypothesis/candidate/review states; abstention and contradiction visible |
| P5-T22 | Alert fatigue or interruptive updates | Missed critical state and poor decisions | Bounded prioritization, no routine modal/ARIA alerts, status batching, operator-controlled filters |
| P5-T23 | Color-only severity or map-only result | Inaccessible or misunderstood state | Text/icons plus color, table/list alternatives, measured contrast |
| P5-T24 | Keyboard trap in grid, map, graph, or video | Operator cannot complete workflow | Native semantics first, documented composite keyboard model, escape and focus restoration |
| P5-T25 | Focus loss during live updates | Wrong action or unusable screen reader flow | Preserve focused identity, do not reorder focused row, polite status announcements |
| P5-T26 | Client optimistic state shown as accepted | False belief that action succeeded | Pending is distinct; only server response/event-refetch can confirm completion |
| P5-T27 | Hidden partial/stale/degraded source | Incorrect command decision | Per-source freshness and completeness; aggregate cannot be healthy while required source unknown |
| P5-T28 | Sensitive client telemetry | Operator, subject, or investigation leakage | Low-cardinality allowlist; no IDs, terms, routes values, reasons, payloads, media, or raw exceptions |
| P5-T29 | Cross-window data leak | Protected record visible in unintended window | Minimal message protocol, same-origin validation, no payload persistence, session/scope broadcast closure |
| P5-T30 | Clickjacking | Tricked privileged action | Frame restrictions, CSP `frame-ancestors`, confirmation for consequential commands |
| P5-T31 | Tabnabbing or unsafe external navigation | Session/phishing compromise | Bounded external links, safe rel behavior, no provider URL rendering from data |
| P5-T32 | Supply-chain compromise | Malicious UI code or build | Lockfile, provenance/SBOM, dependency allowlist, review, reproducible build evidence |
| P5-T33 | Service worker retains old or sensitive data | Stale vulnerable bundle or data persistence | Static-assets-only policy, versioned activation, explicit purge, no API/media caching |
| P5-T34 | Draft loss or disclosure | Operator reason lost or persisted insecurely | Memory-only bounded drafts, clear expiry/logout behavior, explicit conflict preservation |
| P5-T35 | Unavailable action appears enabled | Unsafe expectation or bypass attempt | Server capability projection, disabled reason, command reauthorization, negative tests |
| P5-T36 | Frontend obscures correction/retraction | Superseded information used | Append-only visual history, current/prior links, correction event refetch, no destructive replacement |
| P5-T37 | Admin portal becomes universal privilege surface | High-impact compromise | Separate roles, least privilege, read-only default, sensitive-command separation and audit |
| P5-T38 | Unified search collapses audit/evidence boundaries | Policy and retention violation | Search only derived minimized projections; independent source stores remain authoritative |
| P5-T39 | Capability auto-detection fingerprints device | Privacy and inventory leakage | Coarse classes, local evaluation, no raw hardware identifiers or telemetry labels |
| P5-T40 | High-capability profile weakens safeguards | Different safety behavior by machine | Profile changes rendering/resource ceilings only; semantic and security invariants are fixed |

## Abuse Cases

### Cross-Department Enumeration

An authenticated user modifies a route parameter, cursor, map extent, event
subscription, or cached query key to request another department's records.
Every backend operation and event subscription must enforce current department
scope. The response must not reveal whether a protected record exists.

### Stale Review Resubmission

An operator leaves an alert open while another reviewer changes it. The first
operator submits the old form. The server returns conflict. The client keeps a
memory-only draft, loads the new state, highlights material changes, and
requires a new explicit decision.

### Event-Injection UI Escalation

A forged or replayed `alert.changed` event claims an alert is approved. The
client validates channel/session/schema/scope/sequence, treats the event only
as an invalidation hint, and fetches the authoritative alert before rendering
the current lifecycle or enabling an action.

### Live-Grid Resource Exhaustion

An operator or script opens many streams. The client and server enforce an
admission budget based on policy and effective profile. Excess requests remain
queued or denied visibly. Existing sessions do not reconnect forever.

### Candidate Identity Overclaim

A generated candidate has a high score. The UI labels it as candidate evidence
with calibration, contradiction, source, and abstention context. It never
changes the label to identified, wanted, guilty, or confirmed without a later
accepted domain contract and human authority.

### Compromised Tile Or Script Origin

An external origin attempts to serve changed JavaScript or track map requests.
The baseline uses self-hosted application assets, strict destination and CSP
policies, and an approved tile source. A failed base map leaves authoritative
lists usable.

## Required Security Evidence For Future Implementation

- server/client authorization and department-isolation parity;
- CSRF, session fixation, expiry, logout, revocation, and reauthentication;
- XSS, CSP, dependency, source-map, and external-origin checks;
- ETag conflict and idempotency mutation tests;
- event spoof, replay, gap, unknown version, reconnect, and scope tests;
- no-store, local/session/IndexedDB/cache storage, history, clipboard, print,
  and download inspection;
- playback token, expiry, teardown, fan-out, reconnect, and zero-retention
  tests using generated media only if separately authorized;
- map/graph/timeline bounds and adversarial geometry tests;
- keyboard, focus, status, zoom, target, contrast, reduced-motion, and screen-
  reader workflow evidence;
- telemetry field and cardinality allowlist tests;
- dependency lock, SBOM, license, provenance, vulnerability, and build-output
  evidence;
- all blocked capabilities absent from routes, bundles, controls, and network
  traces.

## Residual Risks

- Browser code cannot fully defend tokens or displayed data from arbitrary
  malicious script in the same origin; dependency and CSP controls reduce but
  do not eliminate that risk.
- Maps, video, graphs, and dense updating grids require manual usability and
  assistive-technology evaluation; static contracts are insufficient.
- WHEP is still an Internet-Draft and can change incompatibly.
- Exact identity provider, managed-browser policy, tile/media topology, and
  deployment environment are unknown.
- No real operational workflow, user study, threat exercise, penetration test,
  accessibility audit, capacity test, or deployment evidence exists.

These risks remain open and block production or compliance claims.
