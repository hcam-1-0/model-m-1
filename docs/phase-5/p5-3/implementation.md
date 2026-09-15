# P5.3 Camera And Live Monitoring Workspace Implementation

Status date: 2026-09-08

## Scope

P5.3 implements the generated-only camera catalogue, detail, diagnostics, live
workspace, monitor wall, browser-safe playback contracts, media adapters, and
dynamic stream admission authorized by exact package `P5.3-START-R0`.
Operations owns the camera surfaces; Command Center remains primary, and GIS
and investigation handoffs carry only opaque generated references.

No source was imported. No backend route, migration, real playback service,
provider, Sentinel connection, camera, real media, Government/private data,
model, inference, operational action, container, Kubernetes resource,
deployment, or remote Git operation was added or used.

## Delivered Topology

- eight independently buildable portals and twenty-two shared packages;
- Operations camera catalogue, camera detail, and stream diagnostics pages;
- connected single-camera live workspace, multi-camera workspace, monitor
  wall, and workspace manager;
- browser-safe opaque grant and same-origin media-edge contracts;
- native HLS and pinned `hls.js` `1.7.2` adapters with a no-media fallback;
- optional default-off WHEP contract adapter with deterministic HLS fallback;
- deterministic C1, C4, and C10 admission profiles with admitted and held
  tiles, stable scheduling, pause, resume, release, and complete teardown;
- generated layout revision and conflict behavior without browser persistence;
- authoritative semantic status, list, table, and detail alternatives;
- low-resource, enhanced-workstation, control-room, GPU-lab, and future-server
  resource projections that never change operator authority.

## Workstream Results

| Workstream | Weight | Result |
| --- | ---: | --- |
| P5.3-W1 Contracts and generated fixtures | 2.0 | Complete: eight strict contracts, eight generated fixtures, safe reasons, profile, layout, handoff, and media manifests |
| P5.3-W2 Catalogue, detail, and diagnostics | 2.0 | Complete: generated inventory, detail, health, capability, probe, freshness, completeness, and degraded-state surfaces |
| P5.3-W3 Playback control and media-edge contracts | 2.5 | Complete: opaque grant lifecycle, admission, renewal, revocation, close, cooldown, and same-origin boundary |
| P5.3-W4 HLS baseline and capability selection | 2.5 | Complete: native HLS, lazy `hls.js`, capability selection, bounded recovery, quality policy, and teardown |
| P5.3-W5 Provisional WHEP and HLS fallback | 1.5 | Complete: draft-pinned, replaceable, default-off WHEP adapter and deterministic HLS fallback |
| P5.3-W6 Live workspace, monitor wall, and layouts | 2.5 | Complete: C1/C4/C10 scheduling, focus, pin, defer, release, revisioned layouts, and specialist handoffs |
| P5.3-W7 Accessibility, security, profiles, and signals | 1.5 | Complete: keyboard/focus behavior, authoritative non-video equivalence, safe signals, and profile-invariant authority |
| P5.3-W8 Validation, evidence, and acceptance | 1.5 | Complete: sealed evidence package exactly owner accepted under `D-P5.3-ACCEPTANCE` |

## Security And Authority

- The browser sees generated opaque grants and same-origin media paths only.
- Grant material remains memory-only and is removed on close, revocation,
  expiry, logout, scope change, route disposal, and window teardown.
- No recording, snapshot, download, export, print, PTZ, camera management, or
  operational action is implemented.
- Dynamic profiles alter admitted count, rendition, and presentation quality
  only; authorization, safeguards, and operator actions stay identical.
- WHEP is disabled by default and cannot remove the mandatory HLS fallback.
- Client signals use bounded reason classes and exclude identifiers, locators,
  grants, SDP, ICE, raw errors, and security material.

## Progress

W1 through W8 earn **16/16 P5.3 points (100.0000%)**, change **+9.3750
percentage points** from the 90.6250% technical-cap state. Phase 5 reaches
**48/100 (48.0000%)**, change **+1.5000 percentage points** from 46.5000%.
Exact `D-P5.3-ACCEPTANCE` is effective; P5.4 remains unauthorized.
