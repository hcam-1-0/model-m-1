# Phase 2 Acceptance Checklist

## Automated Evidence

- [x] Stream endpoint schema, migration, legacy backfill, and constraints
- [x] Department-scoped read/write API, reasons, audit, and ETags
- [x] Credential-free locator validation and exact network allowlist
- [x] DNS-rebinding, environment-proxy, and ONVIF redirect denial controls
- [x] Metadata-only FFprobe runner with bounded execution
- [x] Execution-time stdout/stderr ceilings that terminate output floods
- [x] Controlled ONVIF simulator with Media, Imaging, Events, and PTZ services
- [x] Scoped, audited, bounded ONVIF media capability discovery
- [x] Explicit device-service configuration and four ONVIF authentication modes
- [x] Per-attempt secret resolution, rotation, confinement, and redaction tests
- [x] Verified TLS/private CA support and exact scheme/host/port/address egress
- [x] Background refresh API, priority, deduplication, cooldown, and safe status
- [x] 24-hour jittered schedule, 36-hour freshness, and 90-day history retention
- [x] Stable fingerprint deduplication and capability-change outbox event
- [x] Transient retries, 90-second lease recovery, and disabled-stream denial
- [x] Partial-result normalization and hostile service-URL rejection
- [x] Deprecated synchronous compatibility and media-only snapshot behavior
- [x] Low-cardinality capability metrics and operational alerts
- [x] Controlled private-camera metadata harness disabled by default
- [x] Read-only imaging inspection and bounded pull-point event lifecycle
- [x] Dedicated controller role plus global and administrator-set stream gates
- [x] PTZ velocity/duration limits, per-stream leases, and continuous auto-stop
- [x] Admin-only WS-Discovery bound to an exact interface and private CIDRs
- [x] Discovery fixtures prove unsafe XAddrs are filtered and never contacted
- [x] Safe ONVIF operation records, audit events, and low-cardinality metrics
- [x] PostgreSQL leases and SQLite single-worker boundary
- [x] Two-worker PostgreSQL claim test and 50-stream scheduled-load test
- [x] Health hysteresis, backoff, projection, history, and outbox events
- [x] At-least-once outbox dispatcher and explicit production sink boundary
- [x] ES256 JWKS and 60-second path-scoped HLS authorization
- [x] MediaMTX recording disabled and non-media ports private
- [x] Deterministic synthetic 50-stream stack
- [x] Anonymous and cross-stream HLS denial checks
- [x] Full 50-stream recovery after controlled ONVIF outage
- [x] Protected metrics and zero unpublished outbox backlog after validation
- [x] Phase 0 and Phase 1 regression suite preserved
- [x] Readiness verifier and CI phase gate

## Core Owner Gate

- [x] Owner reviewed the Phase 2 evidence and explicitly accepted it on
  2026-08-21

Phase 2 core status is `accepted`. Phase 3 planning is authorized. This
acceptance does not authorize real CCTV, Government data, biometrics,
watchlists, or production deployment.

## Controlled Extension Owner Gate

- [x] Owner separately accepted the authenticated capability-management and
  controlled ONVIF operations extension on 2026-08-23.
- [x] The exact reviewed source was merged through
  [pull request #31](https://github.com/mayankthakor227/h-cam-2.0/pull/31).

The extension publication evidence and exact acceptance boundary are recorded
in [extension-publication-checklist.md](extension-publication-checklist.md) and
[owner-review.md](owner-review.md). This acceptance does not authorize
physical-camera control, recording, Government data, analytics, or deployment.
