# P5.3 Start Authorization Proposal

Status: non-effective; exact owner start authorization pending

Package: `P5.3-START-R0`

Package SHA-256:
`03D87FD50A6A54619F2A7065809A88DA04BED95B2159B7EE178C41A03A1BDCCA`

Bound-input digest:
`8B6A77A935B30751B851F04FB4B5A8273CC1D01A7333F1A33A54E8FF6BDC80FB`

Planning-preparation component digest:
`F13D61CF09630010007424DC85137A428D072EE6DF1FCA4A5CDE1162B810E1E9`

Prepared: 2026-09-08

Expires if not accepted: 2026-10-08

## Purpose

This package is the bounded implementation gate for P5.3 Camera And Live
Monitoring Workspace. It converts the accepted R1 architecture into an exact
local generated-only delivery scope. Preparing this package does not activate
that scope and awards no product points.

The product hierarchy and trust boundary are fixed:

1. Command Center remains the primary dashboard.
2. Operations owns Camera Catalogue, Camera Detail, and Stream Diagnostics.
3. Live Workspace and Monitor Wall are connected specialist surfaces.
4. Browser playback uses a same-origin media edge and opaque, short-lived,
   one-stream grants.
5. Browsers never receive RTSP, ONVIF, internal gateway, secret-reference, or
   reusable bearer-bearing locators.
6. HLS is the baseline transport through typed hls.js/MSE, with native HLS
   permitted only through the same safe same-origin authorization boundary.
7. WHEP remains optional, default-off, pinned to
   `draft-ietf-wish-whep-04`, kill-switch controlled, and backed by HLS
   fallback.
8. All twenty producer gaps and thirty threats remain explicit and fail
   closed.

The older `hcam-1-0/final-ui` and isolated Phase 2.5 Sentinel lab remain
references only. This package does not authorize source import or connect the
P5.3 product to Sentinel or any camera environment.

## Proposed Effect

Exact owner acceptance would authorize only:

- recording the exact `D-P5.3-START` statement;
- one local checkpoint containing the pending P5.3 planning and start records
  before product work, with no push;
- guarded resolution and installation of exact `hls.js` `1.7.2` from the
  official npm registry under the package's supply-chain controls;
- implementation of eight frozen workstreams in 24 named existing files, 86
  named additive implementation paths, 14 named phase/evidence records, and
  four bounded navigation/status transitions;
- deterministic generated camera metadata and synthetic HLS media for C1,
  C4, and C10 validation;
- local loopback-only frontend, generated-media, HLS, and default-off WHEP
  simulator validation;
- bounded build, browser, visual, accessibility, security, recovery, teardown,
  and resource-profile validation;
- up to twelve in-scope remediation, validation, and reseal cycles;
- up to three local checkpoint commits without push; and
- preparation of one non-effective exact P5.3 exit-acceptance proposal.

Acceptance would not authorize source import, backend producers or routes,
real playback-control or media-edge services, real cameras or media, Sentinel,
provider access, operational actions, deployment, or remote Git.

## Frozen Workstreams

| Workstream | Points | Delivery boundary |
| --- | ---: | --- |
| `P5.3-W1` | 2.0 | Typed camera/live contracts, strict projection rules, generated fixtures, and producer-gap states |
| `P5.3-W2` | 2.0 | Operations-owned Camera Catalogue, Camera Detail, Stream Diagnostics, freshness, capability, and probe views |
| `P5.3-W3` | 2.5 | Playback-control and same-origin media-edge contracts, opaque grants, authorization, scope, expiry, and revocation |
| `P5.3-W4` | 2.5 | HLS baseline, browser/codec capability selection, rendition policy, backpressure, stalls, and teardown |
| `P5.3-W5` | 1.5 | Optional default-off WHEP adapter, pinned draft behavior, kill switch, and deterministic HLS fallback |
| `P5.3-W6` | 2.5 | Single/multi-camera Live Workspace, bounded Monitor Wall, layouts, admission, handoff, and multi-window behavior |
| `P5.3-W7` | 1.5 | Accessibility equivalence, localization, dynamic profiles, security controls, and low-cardinality signals |
| `P5.3-W8` | 1.5 | Complete validation, evidence, limitations, clean-source reproduction, and exact owner exit acceptance |

No partial product credit is awarded within a workstream. The final 1.5 points
for W8 remain withheld until exact owner exit acceptance.

## Application Scope

### Operations

Operations receives authoritative catalogue, detail, and diagnostics pages.
These pages expose only typed, department-scoped, sanitized projections:

- camera identity and location label suitable for the active department;
- configured state, source status, freshness, completeness, and degradation;
- stream endpoint health without exposing internal locators or credentials;
- ONVIF capability-snapshot status from the accepted Phase 2 boundary;
- probe and refresh history through safe reason codes;
- available transport/rendition projections and browser compatibility;
- blocked, unsupported, stale, denied, conflict, and unavailable states; and
- explicit handoff into Live Workspace when viewing is authorized.

P5.3 does not add the missing backend producers. Generated fixtures must keep
the corresponding information marked generated-only, unavailable, or blocked.

### Live Workspace

The connected Live Workspace provides single-camera focus, bounded multi-feed
viewing, camera context, source/freshness state, transport state, admission
state, recovery state, and an investigation handoff contract. It is view-only.

The UI must not expose recording, snapshot, download, export, print, PTZ,
analytics activation, or camera-configuration controls. Browser playback must
be torn down on route exit, logout, department change, authorization change,
grant expiry, revocation, window close, or unrecoverable failure.

### Monitor Wall

Monitor Wall provides stable, bounded layouts suitable for low-resource,
enhanced-workstation, control-room, owned-GPU-lab, and future-server profiles.
The same authorization and safety policy applies to every profile. Higher
profiles may increase admitted streams, rendition, frame rate, and rendering
quality but cannot increase operator authority or bypass review, scope,
teardown, security, or accessibility requirements.

Layouts use server-side ETags, revisions, and optimistic concurrency in the
contract. Until a producer exists, P5.3 uses generated fixtures and a
memory-only fallback; it must not imply durable server persistence.

## Media Boundary

The browser requests a playback session through a typed control-plane
contract. A successful response contains only an opaque short-lived grant and
safe same-origin playback locator. The media edge validates stream,
department, user/session, purpose, expiry, transport, rendition, and revocation
before translating the grant internally. The browser cannot choose or recover
an upstream locator.

HLS is mandatory and is the fallback for every provisional WHEP path. WHEP is
implemented without a third-party client dependency, using browser `fetch`
and `RTCPeerConnection` behind capability, policy, kill-switch, and generated
simulator gates. No WHEP conformance claim is authorized.

## Dependency Gate

Dependency work is prohibited until exact start acceptance. If accepted, the
only new direct runtime dependency is:

- `hls.js` exact candidate version `1.7.2`, expected Apache-2.0 license, from
  `https://registry.npmjs.org/` only.

Resolution must capture exact direct/transitive versions, integrity, engine
compatibility, license, advisory, provenance, lifecycle-script, bundle, and
SBOM evidence before installation. Installation must use the accepted
hash-bound Node `24.18.0` and pnpm `11.21.0` direct invocation, frozen lockfile,
ignored lifecycle scripts, and disabled browser downloads.

No Shaka Player, Video.js, dash.js, general media player, WHEP client, WebRTC
library, RTSP/ONVIF client, native addon, recording client, provider client, or
backend SDK is authorized. Any need for another dependency stops the work.

## Generated Media

Only deterministic, non-issuable generated media may be used. The bounded
generator uses already installed `ffmpeg` and `ffprobe` only after their exact
path, type, version, size, SHA-256, and available trust metadata pass the
package checks. Missing or unacceptable tools stop the work; they may not be
downloaded or installed.

The generator uses `testsrc2`, `smptebars`, solid colors, and generated-only
labels, with no audio and no copied imagery. Each fixture is 30 seconds with
two-second HLS segments. Rendition targets are:

| Band | Resolution | Frame rate | Target bitrate |
| --- | --- | ---: | ---: |
| Low | 640 x 360 | 10 fps | 500 kbps |
| Medium | 1280 x 720 | 20 fps | 1,500 kbps |
| High | 1920 x 1080 | 25 fps | 4,000 kbps |

`C1`, `C4`, and `C10` use one, four, and ten unique generated streams. The
maximum generated-media output is 2 GiB, with at most four generator processes
and a 300-second timeout per process. Binary media remains untracked and is
deleted after hashes and bounded aggregate evidence are recorded.

## Runtime Boundary

If authorized, runtime validation is limited to:

- application origin `http://127.0.0.1:4173`;
- generated-media origin `http://127.0.0.1:8093`;
- one already installed compatible Microsoft Edge through the Playwright
  channel, with no browser download;
- generated HLS only; and
- an optional default-off generated WHEP simulator only.

If either port is occupied, the run stops; it may not scan for or choose
another port. External network access is forbidden after the dependency gate.
No backend, real playback-control service, real media edge, camera, Sentinel,
provider, model, operational service, container, or Kubernetes workload may
run.

## Recovery And Accessibility

Admission is deterministic and server-authoritative in the contract. The
client may request but cannot invent profile, priority, stream count,
rendition, transport, or bypass decisions. Retry, cooldown, circuit breaking,
stall detection, HLS fallback, session expiry, revocation, teardown, and
abandoned-work behavior are bounded and testable.

Every video state has an authoritative non-video equivalent containing camera
identity, current status, freshness, transport/admission state, safe failure
reason, and available operator action. Keyboard operation, focus, status
announcements, contrast, 200% zoom, reduced motion, long text, and English,
Gujarati, and Hindi projections remain required.

## Validation

After exact start authorization, all 25 validation gates in the machine-
readable package must pass. The suite covers:

- exact toolchain, workspace, lint, formatting, and strict TypeScript checks;
- unit, component, story, contract, and branch-coverage thresholds;
- Operations, Live Workspace, and Monitor Wall builds and bundle checks;
- C1, C4, and C10 generated playback and deterministic admission;
- browser/codec selection, HLS behavior, optional WHEP negotiation, HLS
  fallback, stalls, retry, cooldown, circuit, revocation, and teardown;
- department/role denial, scope change, hostile locators, grant leakage,
  storage leakage, malformed manifests, and safe telemetry;
- authoritative accessibility equivalence and localization;
- dependency integrity, advisory, license, provenance, lock, and SBOM checks;
- two byte-deterministic generated replays;
- focused P5.3 validation, complete frontend and repository regression, Ruff,
  and `git diff --check`; and
- clean-source reproduction with no tracked generated media, build, cache,
  coverage, screenshot, browser, or secret-bearing output.

These are generated local validation claims only. They do not establish real
camera compatibility, production capacity, latency, availability, WHEP
conformance, hardware performance, or deployment readiness.

## Progress Boundary

- Current P5.3 product: **0/16 (0.0000%)**.
- Current Phase 5 product: **32/100 (32.0000%)**.
- Maximum before exact P5.3 exit acceptance: **14.5/16 (90.6250%)** and Phase
  5 **46.5/100 (46.5000%)**.
- After exact exit acceptance: **16/16 (100.0000%)** and Phase 5 **48/100
  (48.0000%)**.

Preparing or accepting this start package awards no product points by itself.

## Stop Conditions

Work stops closed on any bound-input or immutable-history mismatch, path
escape, toolchain mismatch, dependency or supply-chain failure, lifecycle
script, browser download, unapproved network requirement, unavailable or
untrusted ffmpeg/ffprobe, real or issuable data need, backend/service change,
grant or locator leakage, missing HLS fallback, WHEP conformance claim,
forbidden operator control, incomplete teardown, inaccessible video-only
state, failed validation, or twelve-cycle exhaustion.

## Owner Authorization Statement

Normalized owner-statement SHA-256 if accepted exactly:
`117A5D77E8ACFFD03B963AFA1BDD08F744200726C00CFCA00C9375986AD8A8A5`

```text
D-P5.3-START: I, mayank-admin, accept P5.3 start package P5.3-START-R0 with SHA-256 03D87FD50A6A54619F2A7065809A88DA04BED95B2159B7EE178C41A03A1BDCCA and bound-input digest 8B6A77A935B30751B851F04FB4B5A8273CC1D01A7333F1A33A54E8FF6BDC80FB and authorize its exact bounded local generated-only Camera And Live Monitoring Workspace implementation scope, exact hls.js 1.7.2 dependency resolution under the documented supply-chain policy, deterministic C1/C4/C10 synthetic-media generation, source and test implementation, loopback-only build and browser validation, evidence generation, and up to three local checkpoint commits without push. Command Center remains primary; Operations owns Camera Catalogue, Camera Detail, and Stream Diagnostics; Live Workspace and Monitor Wall remain connected specialist surfaces; the same-origin opaque-grant media-edge boundary, HLS baseline, optional default-off draft-ietf-wish-whep-04 WHEP with HLS fallback, dynamic profiles, deterministic admission, bounded recovery and teardown, view-only controls, authoritative accessibility equivalence, twenty producer gaps, thirty threats, and all stop conditions remain mandatory. This does not authorize source import, unapproved dependencies or network access, backend routes or migrations, real playback-session or media-edge services, providers, Sentinel, cameras or real media, recording, snapshots, downloads, exports, print or PTZ, Government or private data, models, datasets, artifacts or inference, operational actions, hardware or production claims, containers, Kubernetes, deployment, P5.4, or remote Git.
```

The statement must be accepted exactly. A shortened acknowledgement,
`continue`, the planning acceptance, or approval of another package does not
activate this package.
