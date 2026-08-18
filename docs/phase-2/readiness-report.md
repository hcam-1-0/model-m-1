# Phase 2 Readiness Report

Status: `ready_for_owner_review`

The implementation and automated evidence are complete. The only remaining
gate is explicit owner acceptance.

## Evidence Summary

| Area | Evidence |
|---|---|
| Schema | Alembic `0004` and `0005`, drift and round-trip tests |
| API | Stream management, health/history, queued probes, playback sessions |
| Adapters | RTSP/HLS/HTTP, legacy, synthetic, controlled ONVIF |
| Health | FFprobe worker, leases, hysteresis, backoff, history, retention |
| Events | Transactional outbox, at-least-once dispatcher, validation sink |
| Playback | ES256, JWKS, 60-second exact-path permission, no token storage |
| Scale | 50 synthetic streams, two workers, on-demand fMP4 HLS |
| Security | RBAC, department scope, audit reasons, loopback exposure, allowlist |
| Operations | protected bounded metrics, Grafana dashboard, Prometheus alert rules |
| Governance | synthetic-only, no recording, no real CCTV or Government data |

Run `python tools/phase2_readiness.py --run-validation` for the machine-readable
audit. Runtime lab evidence is produced by `tools/phase2_lab.py verify` and the
failure drill.

## Local Validation Evidence

Validated on 2026-08-18:

- 242 tests passed, 1 local PostgreSQL-URL test skipped, 90.15% branch coverage;
- PostgreSQL 18 lab reached 50 healthy streams with two worker replicas;
- path-scoped JWT playback passed while anonymous and cross-stream reads failed;
- the ONVIF outage completed `healthy -> degraded -> offline` and recovered via
  `offline -> degraded -> healthy`;
- two fresh recovery rounds completed for all 50 streams;
- protected metrics returned `401` anonymously and `200` with the lab token;
- all unhealthy state gauges and unpublished outbox backlog returned zero;
- no recording, real video, Government data, or media segment download was used.

This status is not production approval and makes no claim about 80,000-camera
capacity, real-network latency, evidentiary admissibility, or police deployment.
