# Phase 2 Acceptance Checklist

## Automated Evidence

- [x] Stream endpoint schema, migration, legacy backfill, and constraints
- [x] Department-scoped read/write API, reasons, audit, and ETags
- [x] Credential-free locator validation and exact network allowlist
- [x] Metadata-only FFprobe runner with bounded execution
- [x] Controlled ONVIF simulator without discovery
- [x] PostgreSQL leases and SQLite single-worker boundary
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

## Owner Gate

- [ ] Owner reviews the Phase 2 evidence and explicitly accepts or rejects it

Until the final owner checkbox is accepted, Phase 2 status is
`ready_for_owner_review`. Phase 3 remains blocked.
