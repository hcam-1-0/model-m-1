# Phase 2 Build And Review Backlog

Status: complete. Phase 2 core and the separately reviewed controlled ONVIF
extension are accepted and merged under their documented safety boundaries.

## Delivered Core

- P2-01 stream endpoint control plane and migrations;
- P2-02 metadata-only health worker and bounded FFprobe;
- P2-03 exact ONVIF egress and authenticated capability inventory;
- P2-04 transactional outbox and health/capability events;
- P2-05 short-lived authorized HLS playback with recording disabled;
- P2-06 deterministic 50-stream synthetic lab and outage recovery;
- P2-07 capability jobs, cache/history, metrics, alerts, and private-lab harness.

## Completed Publication Review

- [x] P2-R1 reviewed migration, secret provider, authentication, egress, TLS,
  DNS pinning, and redaction changes with no blocking finding.
- [x] P2-R2 reviewed jobs, leases, retries, history, APIs, audit, controlled
  operation lifecycles, events, and metrics with no blocking finding.
- [x] P2-R3 reran full Python, PostgreSQL 18, Docker, C50, outage, security,
  package, dependency-lock, contract, and vulnerability evidence.
- [x] P2-R4 published [pull request #31](https://github.com/mayankthakor227/h-cam-2.0/pull/31) with eight successful repository checks.
- [x] P2-R5 synchronized accepted documentation with implementation merge
  commit `cc0d247e80e4eb9c9f320160028e3c9104770fa9`.

The exact completion evidence for P2-R3 through P2-R5 is recorded in
`extension-publication-checklist.md`. The extension source commit was
`dd58590877957d4d07c1acc0b4a24ce206731c42`; the PostgreSQL 18 and synthetic
50-stream jobs passed in Actions run `32551095462`, their commit-named artifacts
were independently verified, and the owner recorded scoped acceptance before
the merge.

Remote P2-G1/P2-G2 review remains fail-closed through `verify-run`: reviewers
validate run, job, artifact, and payload identity from a clean checkout of the
reviewed commit. The verifier is read-only, does not fetch logs, and does not
replace pull-request review or owner acceptance evidence.

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
