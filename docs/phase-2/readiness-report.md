# Phase 2 Readiness Report

Status: `accepted_core_extension_pending`

The repository owner accepted the merged Phase 2 core on 2026-08-21 and
authorized Phase 3 AI analytics planning. The later authenticated capability
management and controlled ONVIF operations extension has complete local
offline evidence, but is not yet published or owner-accepted.

## Evidence Summary

| Area | Evidence |
|---|---|
| Schema | Alembic `0004` through `0007`, drift and round-trip tests |
| Contracts | Reviewed deterministic OpenAPI and Alembic-upgraded database snapshots |
| Dependencies | Universal `uv.lock`, pinned uv/action versions, hashed runtime export |
| API | Stream, health, capability cache/history, ONVIF operations, playback |
| Adapters | RTSP/HLS/HTTP, legacy, synthetic, authenticated read-only ONVIF |
| Secrets | Fail-closed provider contract, rotation-safe private-lab files |
| Health | FFprobe worker, leases, hysteresis, backoff, history, retention |
| Events | Transactional outbox, at-least-once dispatcher, validation sink |
| Playback | ES256, JWKS, 60-second exact-path permission, no token storage |
| Scale | 50 synthetic streams, two workers, on-demand fMP4 HLS |
| Security | RBAC, scope, pre-action audit, pinned exact egress, verified TLS/SNI, redaction, no redirects/proxies |
| Operations | jobs, scheduler, retry, leases, retention, bounded metrics and alerts |
| Governance | default-off control/discovery, no recording or Government data |

Run `python tools/phase2_readiness.py --run-validation` for the machine-readable
audit. Runtime lab evidence is produced by `tools/phase2_lab.py verify` and the
failure drill.

## Local Validation Evidence

Latest offline validation on 2026-08-21:

- 413 tests passed, 4 PostgreSQL-URL tests skipped, and branch coverage passed
  at 90.42%;
- Phase 2 readiness reported `accepted_core_extension_pending` with zero
automated failures and one grouped publication gate;
- publication completion is fail-closed behind named `P2-G1` through `P2-G4`
  gates, each requiring a validated Markdown evidence reference;
- compile, Ruff, Phase 1 regressions, SQLite upgrade/drift, lab preparation,
  lab configuration, and `git diff --check` passed;
- dependency locking is enforced in readiness, CI, source distributions, and
  the runtime image; publication artifacts include the current lock hash;
- synthetic Media, Imaging, Events, and PTZ operations passed, including
  pull-point cleanup, every bounded PTZ action, controller-role separation,
  movement leases, automatic stop, audit records, and safe metrics;
- manual capability refresh admission passed completion-anchored cooldown and
  active-job race recovery tests; the PostgreSQL two-request race test is
  present but awaits the current PostgreSQL publication gate;
- terminal refresh processing passed 90-day job/history pruning while retaining
  the newest stale inventory snapshot for each stream;
- WS-Discovery fixtures passed exact-interface/CIDR filtering, unsafe-XAddr
  rejection, result bounds, role enforcement, and success/failure audit.

Historic container evidence from 2026-08-19:

- a separate PostgreSQL 18 run passed both integration tests, concurrent worker
  claims, schema drift check, and full downgrade/upgrade round trip;
- scheduled ONVIF device/media discovery cached one fresh stable snapshot with
  two normalized profiles, without network discovery or raw XML persistence;
- PostgreSQL 18 lab reached 50 healthy streams with two worker replicas;
- path-scoped JWT playback passed while anonymous and cross-stream reads failed;
- the ONVIF outage completed `healthy -> degraded -> offline` and recovered via
  `offline -> degraded -> healthy`;
- two fresh recovery rounds completed for all 50 streams;
- protected metrics returned `401` anonymously and `200` with the lab token;
- all unhealthy state gauges and unpublished outbox backlog returned zero;
- no recording, real video, Government data, or media segment download was used.

Current PostgreSQL/Compose revalidation is pending. Docker Desktop 28.5.2 and
Compose 2.40.3 are installed, but the Linux engine returned HTTP 500 with no
server version, and both its WSL distribution and service were stopped. No
process was force-killed and no system service was changed. A normal background
launch created Desktop processes, but the service, WSL distribution, and server
remained unavailable after the three-minute readiness window. Migration `0007`
therefore still needs the current PostgreSQL and Compose gates after Docker is
repaired.
Rechecking with Docker API 1.47 and 1.45 produced the same HTTP 500, ruling out
API negotiation as the cause. The laptop also had no local PostgreSQL service,
`psql` executable, port 5432 listener, or configured PostgreSQL test URL. GitHub
CLI authentication for the repository was valid, but no pull request exists
for `codex/phase2-onvif-capability-management`, so no unpublished-extension CI
result can be treated as current evidence.

`tools/phase2_publication_evidence.py` now provides a read-only preflight and
guarded `P2-G1`/`P2-G2` evidence runs. It rejects dirty source, validates
structured Docker server data even when the Docker command returns zero,
redacts PostgreSQL credentials, restores migration head after a downgrade
attempt, and removes the synthetic stack after every start attempt. A blocked
preflight is diagnostic evidence only and cannot satisfy a publication gate.
The read-only verifier rejects stale, oversized, failed, wrong-gate,
wrong-commit, contract/lock-drifted, command-tampered, safety-weakened, or
credential-bearing artifacts. Readiness also restricts remote evidence to this
repository's Actions runs and pull requests and validates linked local runtime
JSON against the current commit.

Remote runtime evidence can additionally be verified with `verify-run`. The
command requires a clean checkout of the expected commit, validates the exact
workflow run and expected job through read-only GitHub APIs, downloads only the
commit-named artifact into temporary storage, applies the full local payload
verifier, and deletes the download. Failed, stale, expired, wrong-commit,
extra-file, authentication-blocked, or token-bearing error cases are covered by
synthetic tests. A valid verifier report is required before a remote P2-G1 or
P2-G2 run is linked.

The local CI workflow now routes its PostgreSQL 18 and 50-stream jobs through
the guarded runner and uploads seven-day, PR-head-bound `phase2-p2-g1-*` and
`phase2-p2-g2-*` artifacts using an immutable action commit. Workflow structure
tests protect the source checkout, confirmation flags, output paths, retention,
read-only permissions, locked installs, hashed artifact installation, and
defensive cleanup. This branch still has no pull
request or remote run, so the configuration is readiness evidence rather than
completed P2-G1/P2-G2 runtime evidence.

The remaining extension publication conditions are authoritative in
`extension-publication-checklist.md`: current PostgreSQL validation, current
Compose validation, green remote PR checks, and explicit owner acceptance.

The private-camera harness is implemented and synthetically tested, but no
physical-camera run was performed because no owned/authorized camera, exact
egress rule, or local credential reference was supplied. Production
authenticated use remains gated on an approved external secret provider.
Physical-camera PTZ was also not attempted; the current private-camera
authorization and harness are metadata-only.

This status is not production approval and makes no claim about 80,000-camera
capacity, real-network latency, evidentiary admissibility, or police deployment.
