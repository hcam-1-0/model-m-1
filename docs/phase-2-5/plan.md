# Phase 2.5 Plan: Controlled Sentinel-Compatible Camera Lab

<!-- markdownlint-disable MD013 -->

Status: generated compatibility lab plus public Sentinel catalogue/one-camera
preview implemented; product integration and external multi-camera scale remain
closed.

Phase 3 remains paused. The owner's later correction authorized implementation
of the exact public Sentinel sandbox connection and bounded live test preview.
Credentials, private hosts, Government data, recording, downloads, analytics,
multi-camera external scale, and deployment remain unauthorized.

## Purpose

Phase 2 proved the H-CAM stream control plane, health workers, protected HLS,
ONVIF capability management, and 50-stream scale with one generated H.264
source. Phase 2.5 closes a different gap: compatibility with the official
Sentinel sandbox's catalogue-driven and heterogeneous live-stream behavior.

The target result is a safe adapter and test environment that supports offline
generated validation and one selected public sandbox stream without becoming a
dependency of the main platform.

## Relationship To Other Phases

| Area | Existing owner | Phase 2.5 responsibility |
| --- | --- | --- |
| Camera registry and departments | Phase 1 | Map external catalogue identities without replacing registry rules |
| Stream endpoints, health, playback | Phase 2 | Extend through a catalogue adapter and realistic generated feeds |
| ONVIF management | Phase 2 | Preserve unchanged; Sentinel catalogue ingestion is separate |
| Detection and tracking | Phase 3 | Not implemented here; receive a verified media/timestamp contract later |
| Intelligence and alerts | Phase 4 | Not implemented here |
| Operator applications | Phase 5 | Only define preview transport requirements here |
| Production deployment | Phase 6 | Not authorized by lab or sandbox evidence |
| Hackathon demonstration | Phase 7 | Receive reproducible connection evidence and runbooks later |

Phase 2.5 must not reopen or weaken accepted Phase 2 safety decisions. Per
D-P2.5-001, it extends the Phase 2 lab directly. The original one-source,
50-path behavior remains available as a named `baseline` profile with the same
acceptance assertions, while Sentinel-compatible behavior is added through
explicit profiles and scenarios in the same lab lifecycle.

## Confirmed Inputs

- The official guide requires catalogue-first consumption from `/api/ingest`.
- The catalogue returns exact RTSP, WHEP, and HLS transport locations.
- RTSP/TCP is the intended AI-inference transport.
- PTS/RTP timestamps, not advertised FPS or frame-arrival time, drive
  time-derived processing.
- Sources can mix H.264, H.265/HEVC, geometry, frame rate, and bitrate.
- Clients must tolerate startup GOP bursts, keyframe wait, variable frame
  intervals, disconnects, and hard loop discontinuities.
- The official environment has no footage-download workflow.
- The observed public reference exposes 30 catalogue records, including 19
  with unknown technical metadata.
- The technical round is expected to use approximately 50 synchronized
  simulated-live camera feeds rather than static downloaded files.
- Current live-environment evidence suggests 30 cameras may be the practical
  event set. Phase 2.5 therefore defaults to 30 active generated cameras while
  preserving tested capacity for 50.

## Outcomes

Phase 2.5 should produce:

1. a versioned generated `/api/ingest` catalogue simulator;
2. a resource-bounded heterogeneous stream lab;
3. a separately versioned `sentinel_sandbox_catalog_v1` adapter;
4. normalized source, camera, transport, health, and timestamp contracts;
5. catalogue refresh and reconciliation with explicit review/apply behavior;
6. generated fault scenarios for reconnect, keyframe wait, PTS variation, and
   loop discontinuity;
7. metrics, audit events, and zero-retention evidence;
8. offline, generated-live, metadata-only, and controlled-live gates; and
9. a handoff contract for Phase 3 inference and Phase 7 demonstration work.

## Non-Goals

Phase 2.5 does not include:

- video download or fixture creation from Sentinel footage;
- production CCTV or Government database access;
- face recognition, ANPR, detection, tracking, or alert generation;
- evidence storage, recording, screenshots, thumbnails, or frame export;
- camera discovery, provisioning, PTZ, firmware, or gateway control;
- a replacement VMS or a production multi-region deployment;
- a claim of ONVIF, Sentinel, or Government deployment conformance; or
- automatic connection to every catalogue entry after refresh.

## Architecture Direction

```text
public Sentinel /api/ingest ---- same normalized catalogue
        |                                  |
        |                      +-----------+-----------+
        |                      |                       |
        |              lab1highadapter          lab2lowadapter
        |              30 conn / 4 preview      4 conn / 1 preview
        |                      |                       |
        +----------------------+-----------------------+
                               |
                     one selected exact HLS source
                               |
                     ephemeral stream-copy relay
                               |
                     isolated loopback WHEP gateway
                               |
                         test dashboard only

generated simulator + 50 fixtures + faults
        |
        +---- explicit offline `generated-fallback` profile
        |
        +---- isolated lab state and test dashboard
```

The catalogue adapter is a control-plane component. It discovers advertised
metadata and transport choices. It does not decode media, run AI, or own the
MediaMTX gateway; the lab relay is a separate bounded data-plane helper.

## Work Packages

### P2.5-W1: Source Contract Freeze

- preserve official-guide and public-environment evidence;
- define supported and optional `/api/ingest` fields;
- define unknown-value normalization;
- define catalogue limits, provenance, and versioning; and
- record organizer questions that block live testing.

Exit: accepted adapter input contract and test fixture schema.

### P2.5-W2: Generated Catalogue Simulator

- generate no-data camera records and exact local transport URLs;
- support 12-camera compatibility, 30-camera default, and 50-camera capacity
  modes;
- support deterministic add, update, remove, offline, and malformed cases;
- expose ETag or deterministic body fingerprint behavior; and
- provide no control or media-upload endpoint.

Exit: fully offline schema and reconciliation tests pass.

### P2.5-W3: Heterogeneous Media Lab

- add generated H.264 and HEVC profiles;
- generate unique per-camera codec, geometry, frame-rate, quality/bitrate, and
  transport-role combinations;
- model keyframe wait, PTS variation, restart, and loop discontinuity;
- preserve RTSP/TCP, protected HLS, and bounded WHEP roles; and
- implement selected D-P2.5-003 using 50 unique high-quality generated fixtures
  with 30 active by default and parallel real-time remux.

Exit: deterministic compatibility scenarios pass without retained media.

### P2.5-W4: Catalogue Adapter And Reconciliation

- add `sentinel_sandbox_catalog_v1` without changing legacy adapters;
- implement bounded refresh jobs and sanitized snapshots;
- map source identities to H-CAM camera records;
- expose catalogue diffs while durably auto-applying every accepted snapshot
  through candidate promotion and rollback; and
- preserve optimistic locking, department scope, RBAC, reason, and audit.

Exit: generated catalogue changes reconcile deterministically and safely.

### P2.5-W5: Timestamp And Recovery Contract

- expose media PTS and connection/discontinuity epochs to future consumers;
- distinguish advertised live state from observed health;
- validate bounded exponential reconnect with jitter;
- prevent track or dwell state from crossing discontinuity epochs; and
- document the Phase 3 decoder/inference handoff.

Exit: fault scenarios have machine-readable evidence and no tight retry loops.

### P2.5-W6: Security, Load, And Observability

- enforce exact scheme/host/port/address egress rules;
- resolve credentials through a typed provider when official auth is known;
- add catalogue and transport connection ceilings;
- add low-cardinality metrics, audit actions, and safe error codes; and
- add a local kill switch and unconditional cleanup.

Exit: security and load tests pass in generated-only mode.

### P2.5-W7: Controlled-Live Validation

- keep all external access closed until D-P2.5-007 and an exact authorization
  manifest are accepted;
- begin every permitted progression with metadata and one bounded RTSP/TCP
  stream;
- decode to memory/null with zero retained frames; and
- continue only through the camera-count ladder authorized in that manifest;
- preserve an exact evidence manifest for every authorized run.

Exit: owner accepts the exact evidence package and documented limitations.

### P2.5-W8: Handoff And Closure

- publish connection and timestamp contracts for Phase 3;
- publish operator-preview requirements for Phase 5;
- publish technical-round runbook inputs for Phase 7;
- document residual risks and organizer dependencies; and
- obtain explicit owner acceptance.

Exit: Phase 2.5 acceptance is recorded without implying deployment authority.

## Delivery Order

1. accept this plan and owner decisions;
2. freeze the generated catalogue contract;
3. implement offline catalogue fixtures and parser tests;
4. implement the separate catalogue adapter and reconciliation preview;
5. extend the Phase 2 lab directly with explicit baseline, compatibility, and
   full-fidelity profiles;
6. add timing, fault, security, load, and observability tests;
7. produce generated-only evidence;
8. review official access terms and authentication;
9. authorize metadata-only live validation separately;
10. authorize one-camera media validation separately; and
11. close Phase 2.5 only after owner acceptance.

## Planning Acceptance Criteria

Planning is ready for owner acceptance when:

- topology and module ownership are explicit;
- generated scenarios cover official stream behavior;
- the adapter's input, normalized output, and reconciliation behavior are
  explicit;
- all network, credential, load, retention, and cleanup rules are explicit;
- implementation backlog items have testable completion evidence;
- live access has independent gates and exact ceilings;
- unresolved owner decisions are listed with recommendations; and
- no planning statement silently grants implementation or live-access scope.

## Implementation Acceptance Criteria

Implementation will require evidence that:

- existing Phase 0, Phase 1, Phase 2, and paused Phase 3 tests remain green;
- the accepted Phase 2 baseline behavior remains reproducible through its named
  regression profile;
- the new generated compatibility lab is deterministic and disposable;
- catalogue reconciliation is idempotent and department-safe;
- unknown metadata, mixed codecs, PTS variation, and discontinuities pass;
- credentials and exact stream URLs do not leak into logs, metrics, fixtures,
  audit records, or evidence;
- no media artifact remains after validation;
- retries, concurrency, bandwidth, and response sizes remain bounded; and
- controlled-live evidence, if authorized, stays within its exact manifest.

## Current Planning Status

Official-source intake, public environment mapping, adapter identity, topology,
work packages, safety boundary, validation strategy, and D-P2.5-001 through
D-P2.5-008 are selected. Generated G1-G5 are implemented. The current public
catalogue contains 30 advertised-live cameras within the retained 50-slot
holder. G6 metadata and a one-camera G7 browser smoke were executed after the
owner corrected the lab to use the Sentinel online environment. G8 remains
closed. Regression, packaging, Docker/browser evidence, exact digest, and final
owner acceptance remain the closure sequence.

## Implemented Online Lab Resource Profiles

Two switchable lab profiles share one test dashboard and the same Sentinel
catalogue:

- `lab1highadapter` is the default high-resource profile with the current 30
  records, 50-slot capacity, 30 connection ceiling, four previews, and native
  media quality.
- `lab2lowadapter` shows the same 30 records and native media metadata with a
  four-connection ceiling and one preview.

The switch is durable and readiness-gated, with rollback to the prior profile
when catalogue health cannot be proven. Generated fallback retains its original
50/30 and 12/4 catalogue/publisher profiles. The future product adapter remains
independent and is not implemented by Phase 2.5.
