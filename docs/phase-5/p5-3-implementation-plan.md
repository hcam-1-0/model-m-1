# P5.3 Bounded Implementation Plan

Status: non-effective planning baseline; owner decisions and separate start authorization required

## Objective

Implement a production-shaped but generated-only Camera And Live Monitoring
Workspace that remains safe and functionally complete on a low-resource laptop,
scales its admitted stream count and quality on stronger owned hardware, and
preserves identical operator authority, security, and workflow semantics across
profiles.

## Frozen Product Weight

P5.3 carries 16 of 100 Phase 5 points. Planning work earns no product points.

| Workstream | Points | Exit outcome |
| --- | ---: | --- |
| W1. Contracts and generated fixtures | 2.0 | Browser-safe schemas, generated metadata/media manifests, handoff and reason taxonomies |
| W2. Catalogue, detail, and diagnostics | 2.0 | Complete camera catalogue/detail/health/probe/capability UX using generated producers |
| W3. Playback control and media-edge contracts | 2.5 | Opaque grant lifecycle, admission, renewal, revocation, close, and safe edge boundary |
| W4. HLS baseline and capability selection | 2.5 | Typed hls.js/native adapter, codec checks, quality policy, stalls, teardown |
| W5. Provisional WHEP and HLS fallback | 1.5 | Draft-pinned optional adapter, security bounds, typed negotiation, fallback and kill switch |
| W6. Live workspace, monitor wall, and layouts | 2.5 | C1/C4/C10 scheduling, focus/pin/defer, revisioned layout projection, portal handoffs |
| W7. Accessibility, security, profiles, and signals | 1.5 | Authoritative alternative, invariant authority, CSP/storage/telemetry controls |
| W8. Validation, evidence, and acceptance | 1.5 | Deterministic generated evidence, clean replays, declared limitations, sealed package |
| **Total** | **16.0** | **P5.3 complete only after exact owner acceptance** |

## Delivery Sequence

### W1: Contracts And Generated Fixtures

1. Extend P5 playback contracts additively with typed lifecycle, transport,
   admission, quality, session expiry, teardown, and safe reason states.
2. Define browser-safe camera summary/detail/diagnostic DTOs with recursive
   forbidden-field rules.
3. Define cross-portal handoff, client media signal, profile mapping, generated
   media manifest, and capacity-evidence schemas.
4. Build generated camera/stream fixtures and unique synthetic C1/C4/C10 media
   descriptions with exact hashes and deterministic fault schedules.

Stop conditions: any proposed DTO includes a locator, secret, token, SDP, ICE,
raw provider/probe payload, media copy, or protected data.

### W2: Catalogue, Detail, And Diagnostics

1. Add grouped Operations routes for catalogue, camera detail, and stream
   diagnostics using the P5.1 shell and generated mock producer only.
2. Implement bounded pagination/filter/sort, detail drill-down, health,
   capability, probe, freshness, completeness, and revision states.
3. Add authoritative semantic list/table alternatives and all loading, empty,
   partial, stale, degraded, denied, conflict, and failure states.
4. Preserve stable responsive dimensions and low-resource completeness.

Stop conditions: any direct Phase 2 raw DTO is bound to the browser, any
management/control action appears, or any real endpoint is contacted.

### W3: Playback Control And Media-Edge Contracts

1. Implement a generated-only playback-control simulator conforming to opaque
   grant, expiry, renewal, revocation, idempotent close, lease, cooldown, and
   admission contracts.
2. Define but do not operationally connect the future same-origin media-edge
   adapter contract.
3. Implement browser in-memory grant handling and complete cleanup on logout,
   scope/permission change, expiry, route disposal, and window close.
4. Validate no locator/token material reaches URL, route, log, telemetry,
   storage, error, or exported diagnostics.

Stop conditions: a raw playback URL/token is persisted or placed in a query
parameter, or a browser can bypass server admission.

### W4: HLS Baseline

1. Under the later exact start package, resolve one pinned hls.js version and
   record integrity, license, dependency, vulnerability, and bundle evidence.
2. Implement `HlsPlaybackAdapter` against generated same-origin media only.
3. Implement native HLS capability as a guarded path requiring safe same-origin
   authentication; never use a URL bearer token.
4. Add codec/MSE/Media Capabilities advisory checks, bounded variant selection,
   buffers, retries, redirects, timeouts, and teardown.
5. Validate supported, unsupported, malformed, oversized, stalled, expired,
   revoked, hidden, and profile-downgrade scenarios.

Stop conditions: dependency scope exceeds the accepted package, MSE/native HLS
requires permissive CSP or query tokens, or generated media provenance fails.

### W5: Optional WHEP

1. Freeze the exact WHEP Internet-Draft version and implementation subset.
2. Implement a replaceable default-off adapter using browser standards or one
   separately approved narrow dependency.
3. Enforce HTTPS, destination, redirect, SDP, ICE/TURN, timeout, output,
   telemetry, and teardown bounds.
4. Implement deterministic HLS fallback and feature kill switch.
5. Validate only against a generated local WHEP simulator.

Stop conditions: the draft changes without review, an arbitrary destination or
candidate is allowed, negotiation material is retained, or HLS fallback breaks.

### W6: Live Workspace And Monitor Wall

1. Implement single-camera, multi-camera, and monitor-wall views behind the
   accepted Operations navigation.
2. Implement weighted admission using intent, pin/focus, visibility, health,
   effective profile, and bounded budgets.
3. Support C1/C4/C10 templates, stable tiles, defer/release, quality downgrade,
   independent window revalidation, and optional explicit wake lock.
4. Implement generated server-side layout projections with ETag conflicts and
   memory-only fallback; no browser persistence.
5. Connect Command/GIS/Alert/Investigation handoffs through opaque refs only.

Stop conditions: every saved tile auto-plays, stream count is unbounded,
multiple windows bypass admission, or layout state contains protected values.

### W7: Accessibility, Security, Profiles, And Signals

1. Complete keyboard, focus, no-trap, semantic status, bounded announcement,
   contrast, reflow, reduced-motion, and pause/release behavior.
2. Prove every media workflow has an authoritative non-video status/list path.
3. Map Phase 3 and P5 resource profiles and verify identical permissions,
   actions, errors, and safeguards across all profiles.
4. Apply exact CSP, origin, storage, token, telemetry, and frame-ancestor rules.
5. Emit low-cardinality generated signals without identifiers or security
   material.

Stop conditions: a profile changes authority, video is the only status source,
or any sensitive/unbounded value reaches client telemetry.

### W8: Validation And Acceptance

1. Run focused contract, unit, component, story, browser, visual, accessibility,
   security, deterministic replay, dependency, and complete repository tests.
2. Run generated C1/C4/C10 matrices for every declared profile without claiming
   production capacity.
3. Execute two clean generated replays and compare canonical outputs.
4. Generate evidence index, source/dependency hashes, environment declaration,
   known limitations, gap closure, and prohibited-claim checks.
5. Seal an exact evidence package, technical commit, and separate owner
   acceptance proposal.

Stop conditions: non-determinism, unavailable vulnerability refresh without a
visible limitation, incomplete cleanup, failed security/accessibility gate,
unmapped blocker gap, or any real media/network/data activity.

## Start-Package Requirements

A future `P5.3-START-R0` package must bind:

- exact base commit, branch, authorized paths, and immutable accepted inputs;
- selected owner decisions and reconciled planning-package digest;
- exact direct dependency/version/integrity/license allowlist;
- generated media generator or checked-in fixture strategy and maximum sizes;
- exact loopback origins, ports, media formats, codec/rendition matrix, and
  network prohibition;
- exact C1/C4/C10 process, browser, timeout, output, and retention bounds;
- test/build/browser commands and declared toolchain;
- source, generated evidence, screenshot, report, and package output paths;
- recursive forbidden-value checks and security stop conditions;
- local commit allowance and continuing remote-Git prohibition.

## Proposed Implementation Path Classes

The start package should permit only additive or bounded Phase 5 paths:

- `frontend/apps/operations-center/**`;
- new or existing Phase 5 camera/live feature packages;
- additive shared contracts in `frontend/packages/**`;
- generated-only frontend fixtures and media under an exact bounded directory;
- P5.3-specific frontend tests and Playwright stories;
- P5.3 contracts, docs, evidence, validation, and status records;
- dependency manifests/lockfile only for exact approved packages.

Backend routes, migrations, real media adapters, Phase 2 product source, Phase
2.5 lab source, Phase 3 accepted artifacts, and Phase 4 accepted artifacts
remain outside the initial P5.3 frontend implementation package unless a later
authorization explicitly adds a bounded producer slice.

## Validation Matrix

| Dimension | Required cases |
| --- | --- |
| Capacity | C1, C4, C10; active/deferred/released; profile upgrade/downgrade |
| Transport | HLS MSE, guarded native HLS, WHEP optional, WHEP-to-HLS fallback, unsupported |
| Codec/media | supported, unsupported, mixed renditions, malformed, oversized, stalled, ended |
| Session | approval, denial, expiry, bounded renewal, revocation, replay rejection, idempotent close |
| Scope | login, logout, department switch, role loss, independent window, stale grant |
| Recovery | transient stall, outage, backoff, cooldown, circuit-open, manual retry, hidden page |
| Security | locators/tokens/storage/URL/log/telemetry/CSP/CORS/redirect/SDP/ICE negative cases |
| Accessibility | keyboard, focus, table/list equivalence, announcements, contrast, zoom/reflow, reduced motion |
| Persistence | memory-only fallback, server projection, ETag conflict, deleted/inaccessible layout |
| Evidence | deterministic hashes, two clean replays, declared environment, limitation and non-claim checks |

## Acceptance Criteria

P5.3 is complete only when all 16 points are earned under sealed evidence and
exact owner acceptance. At that point Phase 5 advances from 32/100 to 48/100.
Planning completion leaves P5.3 at 0/16 and Phase 5 at 32/100.
