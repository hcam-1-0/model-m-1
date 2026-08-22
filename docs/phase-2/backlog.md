# Phase 2 Build And Review Backlog

Status: accepted core; authenticated capability management and controlled
ONVIF operations are implemented locally and pending publication review.

## Delivered Core

- P2-01 stream endpoint control plane and migrations;
- P2-02 metadata-only health worker and bounded FFprobe;
- P2-03 exact ONVIF egress and authenticated capability inventory;
- P2-04 transactional outbox and health/capability events;
- P2-05 short-lived authorized HLS playback with recording disabled;
- P2-06 deterministic 50-stream synthetic lab and outage recovery;
- P2-07 capability jobs, cache/history, metrics, alerts, and private-lab harness.

## Active Publication Review

- P2-R1 review migration, secret provider, authentication, and egress changes;
- P2-R2 review jobs, leases, retries, history, APIs, audit, and event contracts;
- P2-R3 rerun full Python, PostgreSQL, Docker, C50, outage, security, package,
  dependency-lock, and vulnerability evidence;
- P2-R4 publish through a reviewable PR and require green remote CI;
- P2-R5 synchronize accepted documentation with the merged commit.

The exact completion conditions for P2-R3 through P2-R5 are recorded in
`extension-publication-checklist.md`. The earlier closure of issue #27 applies
to the merged core and is not evidence that this extension was published.

The CI implementation for P2-R3 is prepared locally: PostgreSQL and Compose
jobs call the guarded evidence runner, bind pull-request evidence to the PR
head, upload commit-specific JSON for seven days, and fail on a missing report.
The jobs use the reviewed universal `uv.lock`; runtime evidence records its
SHA-256 so dependency drift invalidates an artifact.
This automation does not complete P2-R3 until it is committed and a remote run
passes for the reviewed source.

Remote P2-G1/P2-G2 review is now fail-closed through `verify-run`: reviewers
must validate run, job, artifact, and payload identity from a clean checkout of
the reviewed commit before linking an Actions run. The verifier is read-only,
does not fetch logs, and does not replace P2-R4 pull-request or P2-R5 owner
acceptance evidence.

## Delivered Controlled ONVIF Operations

- P2-08 enumerate media profiles and advertised service capabilities;
- P2-09 inspect imaging settings without changing them;
- P2-10 pull a bounded set of ONVIF events and immediately unsubscribe;
- P2-11 provide PTZ stop and bounded moves behind global and per-camera opt-in,
  dedicated RBAC, reason, audit, leases, velocity/duration limits, and auto-stop;
- P2-12 provide bounded WS-Discovery only in development/test on one exact
  configured private interface and approved private networks;
- P2-13 expand the synthetic simulator and security tests for every operation;

## Deferred Authorization Gate

- P2-14 validate physical-camera control behavior only after a new written
  authorization explicitly covers PTZ movement. The current private-lab path
  remains metadata-only and does not satisfy this gate.

## Still Prohibited

Recording, snapshots, image capture, firmware, provisioning, arbitrary device
configuration, public/LAN-wide discovery, real-person video analytics,
Government integrations, biometrics, and watchlists remain blocked. H-CAM does
not claim ONVIF conformance without the formal test process for an exact
release.
