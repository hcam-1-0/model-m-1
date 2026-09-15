# P5.5 Security, Privacy, Evidence, And Human-Factors Threat Model

Status date: 2026-09-09

Status: planning complete; owner decisions and implementation remain pending

## Protected Properties

- immutable entry and aggregate revision history;
- deterministic record sequence and qualified event-time assertions;
- evidence-reference identity and source-version assertions;
- separation of availability, integrity, provenance, custody, access, and legal
  assessment;
- append-only corrections, retractions, reviews, and impacts;
- bounded relationship and provenance projections;
- department, role, purpose, capability, and current-session isolation;
- source confidentiality and the reference-without-copying default;
- non-operative retention, hold, deletion, disposition, and export previews;
- attributable but content-minimized audit and client signals.

## Threat Catalogue

| ID | Threat | Consequence | Required planning control |
| --- | --- | --- | --- |
| T01 | Resource existence leaks through different denial responses | Cross-scope intelligence disclosure | Same bounded not-found/denied presentation |
| T02 | Timeline IDOR | Unauthorized investigation access | Department, role, purpose, capability check on every read |
| T03 | Evidence access inherited from timeline access | Privilege escalation | Independent Evidence Desk authorization |
| T04 | Cross-department relationship edge | Scope disclosure | Server validation, scoped identifiers, closed edge |
| T05 | Purpose changes but cached records remain | Secondary use | Purpose-bound cache key and immediate purge |
| T06 | Logout or role loss leaves sensitive tabs populated | Residual disclosure | Broadcast teardown and memory/cache clearing |
| T07 | Cursor or sort tampering widens a list | Enumeration | Opaque signed/bound cursor and allowlisted sort |
| T08 | Client joins unbounded lists | Resource exhaustion and hidden omissions | Producer aggregates and bounded server pagination |
| T09 | Event-time order is shown as causal order | False reconstruction | Record sequence default; qualified asserted-time view |
| T10 | Backdated assertion changes prior history | Misleading chronology | Immutable sequence and separate record/event clocks |
| T11 | Unknown precision displayed as exact timestamp | False certainty | Precision/range/clock state beside event time |
| T12 | Concurrent mutation overwrites correction | Lost update | Strong ETag, expected revision, idempotency receipt |
| T13 | Retry duplicates an entry | False chronology | Semantic command and delivery identities |
| T14 | Correction replaces original text | Historical erasure | Append-only correction entry and immutable predecessor |
| T15 | Retraction is presented as deletion | Hidden prior reliance | Original plus retraction remain visible |
| T16 | Correction impact is incomplete | Stale review or export projection | Per-target impact state and completeness warning |
| T17 | Client replay differs from server reconstruction | False historical state | Authoritative exact-revision reconstruction endpoint |
| T18 | Reconstruction omits later correction warning | Misinterpretation | Explicit excluded-later-change section |
| T19 | Comparison calls inactive records deleted | False deletion claim | `not active in projection` typed label |
| T20 | Relationship graph visual proximity implies association strength | Analytical overclaim | Typed edges and authoritative tables |
| T21 | Graph cycle/depth/fanout bomb | Browser denial of service | Server and client node/edge/depth/time bounds |
| T22 | Graph hides inaccessible nodes but implies closure | False completeness | Partial/denied closure state and no inferred edge |
| T23 | Evidence locator appears in URL or DOM | Source disclosure | Opaque IDs and field-minimized contracts |
| T24 | Reference registration triggers source fetch | Unauthorized collection | No resolver in P5.5 and explicit capability denial |
| T25 | Media preview auto-loads | Unauthorized media access | No media renderer, thumbnail, preload, or URL |
| T26 | Mutable source at stable locator is treated as same evidence | Substitution | Immutable version assertion and observation history |
| T27 | Digest match becomes `authentic` | False evidentiary claim | Separate digest observation and authenticity state |
| T28 | Unsupported algorithm silently falls back | Invalid integrity result | Named profile, fail closed, no client verification |
| T29 | Unavailable source appears verified from old result | Stale assurance | Freshness and availability shown independently |
| T30 | Provenance consistency becomes factual truth | Overclaim | `structurally consistent` label and limitation |
| T31 | External PROV graph imports hostile statements | Injection and false lineage | Import absent and disabled contract |
| T32 | Custody gap is hidden by H-CAM access logs | False complete custody | Separate custody and audit record classes |
| T33 | User-supplied label injects script or markup | XSS | Text rendering, schema bounds, CSP baseline |
| T34 | Oversized narrative or metadata freezes UI | Availability loss | String/document/page bounds and truncation with detail |
| T35 | Search index contains secret locator or identity | Persistent disclosure | Minimized allowlist and generated-only fixtures |
| T36 | Telemetry includes timeline/evidence IDs or reasons | Sensitive metadata leak | Low-cardinality labels and prohibited payload scan |
| T37 | Browser cache/history retains evidence response | Residual disclosure | `no-store`, no sensitive query strings, cache purge |
| T38 | Hold preview appears to grant access | Policy confusion | Hold affects deletion eligibility only |
| T39 | Wildcard hold preview normalizes broad target | Indefinite over-retention | Exact bounded target/query snapshot only |
| T40 | Client hardcodes a retention period | Invented legal policy | Opaque external policy reference and unknown state |
| T41 | Deletion simulation looks executed | False destruction belief | Persistent preview-only banner and no command |
| T42 | Receipt says all copies deleted | False assurance | Per-target outcomes, residuals, never universal claim |
| T43 | Export preview omits contradictions/corrections | Biased package | Deterministic closure and inclusion/exclusion ledger |
| T44 | Export preview exposes source content | Exfiltration | Reference-only fields and no payload/render/download |
| T45 | Preview is reused for another recipient or purpose | Secondary-use error | Bind purpose, recipient class, scope, revision, expiry |
| T46 | Disabled case bridge is accidentally callable | External side effect | No adapter, destination, credential, or command |
| T47 | Event payload directly mutates current state | Stale or forged UI state | Invalidation only, authoritative HTTP confirmation |
| T48 | Dynamic profile omits contradictions or limitations | Hardware-dependent truth | Authority and semantic completeness invariant |
| T49 | Virtualized timeline drops focused or unread rows | Accessibility failure | Server pages, stable anchors, semantic fallback |
| T50 | Color alone distinguishes correction/retraction | Misread state | Text, icon, structure, and accessible description |
| T51 | Conflict refresh destroys a drafted reason | Unsafe re-entry or lost work | Bounded memory-only draft and reconsideration flow |
| T52 | Admin role bypasses evidence purpose | Privileged misuse | Resource-specific role plus purpose, no admin shortcut |
| T53 | Localization changes a canonical reason or digest | Contract mismatch | Localize labels only; preserve canonical values |
| T54 | Generated fixture resembles a real identifier | Accidental real-data handling | Non-issuable tokens and recursive prohibited-data guard |
| T55 | Integrity or custody badge implies legal admissibility | Legal overclaim | Legal state fixed to `not_performed` in baseline |
| T56 | Audit records are copied into investigation evidence | Record-class confusion | Typed cross-reference only; separate retention/access |

## Trust Boundaries

1. **External sources:** media stores, camera systems, provider records, case
   systems, and physical custody remain outside P5.5 authority.
2. **Phase 4 investigation service:** authoritative producer of timeline,
   evidence, reconstruction, correction, policy-preview, audit, and event
   contracts; several UI consumer reads remain gaps.
3. **API client:** validates schema/version, department, freshness, ETag, bounds,
   and sanitized errors; does not infer missing fields.
4. **Investigation Center:** presents scoped timeline and reconstruction state;
   it does not grant Evidence Desk access.
5. **Evidence Desk:** presents references and supplied observations; it has no
   resolver, media renderer, cryptographic authority, or legal authority.
6. **Browser memory/cache:** transient and scope-bound; sensitive responses are
   not persisted to local or session storage.
7. **Event channel:** invalidation hint only; HTTP remains authoritative.
8. **Policy preview:** generated and non-operative; policy authority and actual
   execution remain external.

## Abuse Cases

### Manufacture A Clean Timeline By Hiding Retractions

An operator filters out retractions and exports a visual impression of only
supporting entries. The default timeline retains correction/retraction markers,
active filters are always visible, and reconstruction reports later excluded
changes. A future export preview computes deterministic closure and records
included and excluded references with reasons.

### Treat A Digest Match As Identity Proof

An operator sees `match` and assumes the referenced media proves a person's
identity. The Evidence Desk labels the state `digest observation: match`, names
the algorithm/profile and observation time, keeps identity/legal assessment at
`not established`/`not performed`, and links to explicit limitations.

### Probe Another Department Through Relationships

A relationship points to an opaque timeline in another scope. The current view
may show a redacted inaccessible endpoint only when the server contract allows
it; opening it performs independent authorization. Differences between denied
and nonexistent resources do not confirm existence.

### Make A Simulation Look Like A Real Deletion

A user captures a screenshot of a green simulated deletion result. The preview
uses persistent text `generated simulation, no action executed`, names residual
and unknown states, and offers no execute control. Visual success colors alone
are prohibited.

### Recover Sensitive Data From Browser State

After logout, another user returns to a prior tab. Session invalidation clears
query caches, selected records, comparison state, graphs, drafts, and event
subscriptions. Responses use no-store and URLs contain only opaque IDs.

## Failure Taxonomy

| Family | Example typed states | Retry policy in UI |
| --- | --- | --- |
| Authorization | denied, purpose_invalid, capability_revoked | no automatic retry |
| Scope | department_mismatch, inaccessible_reference | no automatic retry |
| Concurrency | stale_revision, etag_failed, command_conflict | refetch and reconsider |
| Contract | unsupported_version, invalid_shape, bound_exceeded | fail closed |
| Chronology | unknown_time, inconsistent_order, incomplete_revision | display qualified state |
| Integrity | mismatch, unsupported_profile, unavailable | no success promotion |
| Provenance | cycle, orphan, partial, depth_exceeded | bounded table/error |
| Policy | policy_missing, hold_conflict, authority_missing | preview blocked |
| Transient | timeout, service_unavailable | bounded manual/automatic retry |
| Client | render_failed, stale_cache, event_gap | clear/refetch authoritative state |

Raw exceptions, source locators, IDs, user reasons, payloads, digests, security
material, and response bodies are not telemetry labels or user-facing debug
output.

## Validation Boundary

Planning proposes generated tests for all 56 threats, including cross-scope
denials, pagination tampering, dual-clock order, exact revision reconstruction,
late corrections, retraction visibility, graph bounds, reference non-resolution,
integrity-state separation, unavailable sources, custody gaps, policy-preview
inertness, residual deletion results, export closure, ETag/idempotency conflict,
event gaps, cache purge, dynamic-profile equivalence, focus retention, keyboard
navigation, localization invariance, telemetry redaction, and prohibited data.

No threat is considered closed by planning. Real source preservation, physical
custody, legal authority, cryptographic operations, storage administration,
external systems, operator training, and deployment configuration require
future separately authorized validation.
