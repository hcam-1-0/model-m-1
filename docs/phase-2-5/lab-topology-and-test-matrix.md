# Phase 2.5 Lab Topology And Test Matrix

<!-- markdownlint-disable MD013 -->

Status: online Sentinel topology and generated fallback implemented; final
clean-source evidence and exact-package owner acceptance remain pending.

## Current Online Topology

The default dashboard consumes one shared 30-camera Sentinel catalogue through
two resource profiles. High permits 30 managed connections/four preview relays;
low permits four connections/one relay. Both preserve native source properties.
A selected HLS feed is stream-copied into a separate no-recording MediaMTX and
served to the loopback dashboard through WHEP. The relay is ephemeral,
short-leased, locator-redacted, and stores no media.

The generated topology below remains the offline fault, diversity, GPU, and
50-slot fallback. It is no longer the default source for the running dashboard.

## Design Principle

The existing Phase 2 lab proves 50 stream sessions by remuxing one generated
H.264 source to 50 paths. Phase 2.5 must preserve that scale test and add a
separate compatibility lab. It should not run 50 expensive encoders merely to
prove diversity.

The new lab prepares 50 unique generated fixtures, publishes 30 deterministic
camera paths by default, retains capacity for 50 paths, and runs expensive
fault cases against a bounded scenario subset. Publication is stream-copy, so
fixture diversity does not require 30 steady-state encoders.

## In-Place Phase 2 Deployment Shape

Per D-P2.5-001, the existing Phase 2 deployment is extended through additive
Phase 2.5 overlays and a separate lab package:

```text
deploy/compose.phase2-5.yaml       generated catalogue, publishers, faults, dashboard
deploy/compose.phase2-5.*.yaml     optional NVIDIA and Linux VAAPI overlays
deploy/mediamtx.phase2-5.yml       private RTSP and loopback HLS/WHEP relay
app/hcam/labs/sentinel/            isolated lab adapter, state, media, UI, and policies
tools/phase2_5_lab.py              guarded lifecycle and fault runner
tools/phase2_5_evidence.py         offline-verifiable evidence package
```

The protected Phase 2 Compose file remains unchanged. The Phase 2.5 overlay is
explicit and default-off, while the isolated lab package is not imported by
the product runtime. Historical Phase 2 evidence remains historical.

## Components

| Component | Responsibility | Explicit limit |
| --- | --- | --- |
| PostgreSQL | Existing registry, stream, refresh, health, audit, and outbox state | Disposable volume |
| H-CAM API | Existing control plane plus future catalogue APIs | Loopback published only |
| Catalogue simulator | Generated `/api/ingest` responses and deterministic mutations | No upload/control route |
| MediaMTX | Private RTSP relay, protected HLS, optional WHEP preview | Recording disabled |
| Profile publishers | Generated H.264/HEVC fixtures via stream-copy | 30 active by default, 50 capacity |
| Fault controller | Stops/restarts selected generated paths and changes catalogue state | Exact scenario allowlist |
| Catalogue worker | Fetches, validates, snapshots, and diffs the generated catalogue | One active refresh per source |
| Stream workers | Existing metadata-only FFprobe health | Two workers in PostgreSQL mode |
| Evidence runner | Executes gates and writes sanitized JSON | No media bodies or frames |

## Network Shape

```text
host loopback
  |
  +-- H-CAM API
  +-- protected HLS preview
  +-- optional WHEP preview during its dedicated gate
  |
private Compose networks
  +-- control: API, PostgreSQL, workers, catalogue simulator
  +-- media: publishers, MediaMTX, fault controller
```

Rules:

- PostgreSQL, RTSP publish, MediaMTX API/metrics, and simulator internals remain
  private to Compose.
- HLS and WHEP, when enabled, bind only to loopback.
- MediaMTX recording remains disabled globally and per path.
- The catalogue returns only exact service names and ports available inside the
  lab network.
- No host route, DNS name, or IP from a Sentinel environment appears in the
  generated stack.

## Validation Tiers

| Tier | Scope | Cameras | Media | Primary purpose |
| --- | --- | ---: | --- | --- |
| T0 | Static fixtures | 0/12/30/50 records | none | Schema, bounds, normalization, malformed input |
| T1 | Catalogue lifecycle | 12 records | none | Refresh, diff, apply, identity, stale/removal behavior |
| T2 | Compatibility smoke | 12 paths | generated | Mixed codec/geometry and transport behavior |
| T3 | Operational/capacity projection | 30 then 50 paths | generated remux | Default event set and safety capacity |
| T4 | Fault scenarios | 1-4 paths at a time | generated | PTS, keyframe, restart, loop boundary, fallback |
| T5 | Public metadata | published catalogue only | none | Separately authorized schema compatibility |
| T6 | Controlled live smoke | exactly 1 camera | zero-retention decode | Separately authorized transport validation |
| T7 | Controlled subset | maximum 4 cameras | zero-retention decode | Only after T6 owner acceptance |

T0-T4 are required before any external metadata or media test. T5-T7 are
independent owner gates, not automatic progression.

## Generated Source Profiles

The compatibility set should use these canonical profiles. Exact encoder
availability must be checked during implementation before selecting FFmpeg
arguments.

| Profile | Codec | Geometry | Nominal FPS | Purpose |
| --- | --- | --- | ---: | --- |
| P1 | H.264 | 1280x720 | 25 | Common 720p baseline |
| P2 | H.264 | 1280x960 | 24.8 | Non-16:9 and fractional-rate handling |
| P3 | H.264 | 1920x1080 | 12.5 | Low-rate full-HD source |
| P4 | H.264 | 1920x1080 | 25 | Common full-HD source; actual codec may intentionally differ by camera |
| P5 | HEVC | 1920x1080 | 25 | HEVC decoder path |
| P6 | HEVC | 2560x1440 | 13.35 | Higher geometry and fractional rate |
| P7 | H.264 actual, unknown advertised | 1280x720 | 15 | Catalogue zeros resolved after probe |
| P8 | HEVC actual, unknown advertised | 1920x1080 | 15 | Unknown codec until probe |

The generated images should include a visible synthetic source ID, profile ID,
UTC-like generated clock, frame sequence, moving object, and color bars. These
markers are for test diagnostics only and contain no real person or location.

## Twelve-Camera Compatibility Set

| Camera | Profile | Advertised state | Scenario |
| --- | --- | --- | --- |
| C01 | P1 | live and complete | RTSP/TCP baseline |
| C02 | P2 | live and complete | Fractional FPS and non-16:9 |
| C03 | P3 | live and complete | Low-rate 1080p |
| C04 | P4 | live and complete | HLS preview fallback |
| C05 | P5 | live and complete | HEVC 1080p |
| C06 | P6 | live and complete | HEVC 1440p |
| C07 | P7 | live, technical zeros | Probe-derived H.264 metadata |
| C08 | P8 | live, technical zeros | Probe-derived HEVC metadata |
| C09 | P1 | live but unreachable | Advertised/observed health separation |
| C10 | P4 | initially offline | Catalogue state transition |
| C11 | P1 | live and complete | Restart and reconnect target |
| C12 | P3 | live and complete | Loop discontinuity target |

## Thirty-Camera Default And Fifty-Camera Capacity

The full-fidelity profile prepares 50 unique generated fixtures. Normal
Sentinel-compatible runs activate cameras C01-C30. C31-C50 remain deterministic
capacity holders and are activated only by the 50-camera capacity gate.

Across the complete 50-camera holder, the fixtures should include:

- 20 H.264 advertised records;
- 10 HEVC advertised records;
- 15 records with one or more unknown technical properties;
- 3 advertised-live but temporarily unreachable records; and
- 2 catalogue-membership mutation records.

Every fixture should have its own synthetic camera label, visible frame counter,
quality setting, codec/profile, geometry, nominal rate, bitrate band, GOP, and
transport availability. Exact combinations come from a deterministic manifest
so failures are reproducible.

All generated H.264 fixtures disable B-frames and are rejected by preparation
unless FFprobe reports `has_b_frames=0`. This is a WHEP compatibility contract,
not a reduction in the RTSP codec matrix. HEVC fixtures remain available for
RTSP, catalogue mismatch, and dynamic-adapter validation; the basic browser UI
enables Preview only from observed generated H.264 evidence.

This distribution is a generated stress profile, not a copy of current public
camera locations or an assertion about the final technical-round dataset. The
adapter must accept the catalogue's actual count and properties dynamically;
30 and 50 are validation profiles, not hardcoded runtime assumptions.

## Catalogue Mutation Scenarios

| Scenario | Mutation | Expected reconciliation behavior |
| --- | --- | --- |
| M1 | identical response | Reuse fingerprint; no change event |
| M2 | new camera | Stage candidate; auto-promote only after accepted apply and health |
| M3 | location/name change | Update source metadata; preserve H-CAM identity |
| M4 | codec/geometry change | New snapshot and capability-change indication |
| M5 | URL change | Revalidate; require reviewed endpoint update |
| M6 | camera absent once | Mark missing; retain inactive last-known state |
| M7 | camera absent past grace | Durable tombstone; keep retrying catalogue recovery |
| M8 | live to offline | Update advertised state; health remains independent |
| M9 | reordered records | Fingerprint remains semantically stable |
| M10 | duplicate external ID | Reject snapshot as ambiguous |
| M11 | oversized/too many records | Reject before persistence or reconciliation |
| M12 | malformed or hostile URL | Reject record/snapshot according to atomicity policy |

Recommended disappearance grace is three successful catalogue observations
over at least five minutes. Generated tests should use a compressed clock while
preserving the same state transitions.

## Media Fault Scenarios

### F1: Startup GOP Burst

- start a client after the publisher has been running;
- deliver initialization/keyframe data without using arrival rate as time;
- verify downstream elapsed time is based on PTS; and
- do not classify a short startup burst as accelerated motion.

### F2: Delayed Keyframe

- join between keyframes;
- permit bounded decoder warnings or no decoded frame until IDR;
- keep health in connecting/degraded during the grace window; and
- avoid an immediate reconnect loop.

### F3: Variable PTS Intervals

- alternate short and long inter-frame deltas around a stable timeline;
- verify monotonic PTS and positive deltas;
- ensure no division by advertised FPS; and
- expose gaps without silently rewriting timestamps.

### F4: Supervised Restart

- stop one generated source;
- observe degraded then offline according to the current health state machine;
- reconnect with bounded exponential backoff and jitter; and
- recover without restarting unrelated streams.

### F5: Hard Loop Discontinuity

- introduce an explicit PTS reset or hard generated scene cut;
- increment the discontinuity epoch;
- invalidate cross-boundary transient processing state; and
- preserve camera and stream identity.

### F6: RTSP Failure With HLS Fallback

- advertise both exact URLs;
- make RTSP unavailable for one generated camera;
- allow preview fallback only under policy; and
- keep inference transport failure visible rather than reporting the camera as
  fully healthy because HLS preview works.

### F7: Catalogue Live/Transport Offline

- keep `live=true` in the generated catalogue;
- stop the transport;
- show advertised state and observed health separately; and
- avoid modifying the source catalogue claim.

## Timing Evidence

Each compatibility run should produce metadata-only evidence containing:

- scenario and generated profile IDs;
- source PTS start/end and monotonicity result;
- minimum, maximum, median, and p95 PTS delta;
- connection and discontinuity epoch counts;
- reconnect attempt count and bounded delay buckets;
- first packet and first decoded-frame latency when decoding is in scope;
- advertised versus observed codec/geometry/rate; and
- a zero-retained-media assertion.

Do not include frame payloads, exact external URLs, credentials, camera location
labels, or high-cardinality identifiers in long-lived metrics.

## Resource Strategy

### Switchable Lab Adapters

| Lab adapter | Catalogue records | Active publishers | Fixture quality | Claim |
| --- | ---: | ---: | --- | --- |
| `lab1highadapter` | 50 | 30 | Original generated fixture codec, geometry, FPS, GOP, timing, and quality | Full-fidelity acceptance baseline |
| `lab2lowadapter` | 12 | 4 | Same files through stream copy; no transcode or downscale | Resource-reduced development only |

Switch validation must cover high to low, low to high, exact publisher counts,
catalogue counts, persisted selection after restart, and rollback when runtime
readiness fails. The final generated-only acceptance package must be captured
in the high profile.

- Keep the accepted Phase 2 50-stream remux test as the primary scale proof.
- Prepare 50 unique high-quality synthetic fixtures once, then parallel-remux
  them without quality loss.
- Activate 30 paths by default and all 50 only for the capacity gate.
- Use dedicated live-generated publishers only for dynamic timing/fault cases
  that cannot be represented by deterministic fixture playback.
- Require parallel execution for the declared full-fidelity 30/50 gate. A
  resource-limited serial run may validate compatibility but cannot claim the
  operational or capacity result.
- Measure CPU, memory, open connections, startup time, and cleanup time.
- Fail fast if free disk, memory, Docker engine, FFmpeg codec support, or port
  availability does not meet the lab preflight.
- Never reduce codec, timing, or fault assertions merely to make a weak run
  report green; select a smaller declared tier instead.

## Lab Commands And Evidence Shape

The extended guarded runner should expose:

```text
prepare
doctor
config
start --profile <baseline|sentinel-compatibility|full-fidelity> --tier <T1|T2|T3|T4>
verify --profile <baseline|sentinel-compatibility|full-fidelity> --tier <T1|T2|T3|T4>
fault --scenario <F1..F7>
stop
```

Every command must require an explicit generated-lab confirmation, validate
that no external hosts are configured, and perform cleanup after success,
failure, timeout, or interruption.

## Lab Acceptance

The generated lab is acceptable only when:

- T0-T4 pass from a clean checkout;
- the named Phase 2 baseline profile reproduces the existing 50-stream
  assertions;
- all generated endpoints remain private or loopback;
- no media artifact remains after cleanup;
- all declared profile, catalogue, timing, and fault assertions are measured;
- repeated runs are deterministic within documented timing tolerances; and
- the evidence bundle can be independently verified without network access.
