# Phase 2 Readiness Report

Status: `complete`

The repository owner accepted the merged Phase 2 core on 2026-08-21 and
authorized Phase 3 AI analytics planning. The later authenticated capability
management and controlled ONVIF operations extension passed its separate
publication gates, was explicitly accepted on 2026-08-23, and was merged
through pull request #31.

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

Latest clean-commit validation on 2026-08-23:

- 415 tests passed, 4 PostgreSQL-URL tests were skipped only in the general
  suite because its default PostgreSQL URL was intentionally absent, and branch
  coverage passed at 90.41%;
- Phase 2 readiness reports `complete` with zero automated failures and zero
  manual gates after the linked `P2-G1` through `P2-G4` records were accepted;
- compile, Ruff, Phase 1 regressions, SQLite upgrade/drift, lab preparation,
  lab configuration, and `git diff --check` passed;
- the dependency audit reported no known vulnerabilities;
- dependency locking is enforced in readiness, CI, source distributions, and
  the runtime image; publication artifacts include the current lock hash;
- synthetic Media, Imaging, Events, and PTZ operations passed, including
  pull-point cleanup, every bounded PTZ action, controller-role separation,
  movement leases, automatic stop, audit records, and safe metrics;
- manual capability refresh admission passed completion-anchored cooldown and
  active-job race recovery tests, including the PostgreSQL publication gate;
- terminal refresh processing passed 90-day job/history pruning while retaining
  the newest stale inventory snapshot for each stream;
- WS-Discovery fixtures passed exact-interface/CIDR filtering, unsafe-XAddr
  rejection, result bounds, role enforcement, and success/failure audit.

Current publication validation on 2026-08-23:

- `P2-G1` passed all seven PostgreSQL 18 checks: server version, migration
  upgrade, schema drift, four PostgreSQL integration tests, downgrade, restored
  upgrade, and final drift;
- `P2-G2` passed all six guarded synthetic checks: preparation, Compose
  validation/start, 50-stream health and security, outage recovery, and cleanup;
- 50 of 50 streams were healthy, playback remained path-isolated, capability
  history was present, protected metrics passed, and the unpublished outbox
  backlog was zero;
- the outage drill completed `healthy -> degraded -> offline -> degraded ->
  healthy`, and all 50 streams recovered;
- local `P2-G1` and `P2-G2` artifacts and the two remote commit-named artifacts
  were independently verified as `valid`;
- Docker Desktop 4.51.0, Docker Engine 28.5.2, and Compose 2.40.3 were healthy;
- no camera, image, recording, Government data, external dataset, real video,
  or physical PTZ action was used.

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

An earlier 2026-08-21 revalidation attempt was blocked when Docker Desktop's
Linux engine returned HTTP 500 and its WSL distribution and service were
stopped. API 1.47 and 1.45 checks ruled out negotiation, and no local PostgreSQL
fallback was available. This remains useful environment history, but it was
superseded by the successful 2026-08-23 PostgreSQL and Compose publication
validation above.

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

The CI workflow routes its PostgreSQL 18 and 50-stream jobs through
the guarded runner and uploads seven-day, PR-head-bound `phase2-p2-g1-*` and
`phase2-p2-g2-*` artifacts using an immutable action commit. Workflow structure
tests protect the source checkout, confirmation flags, output paths, retention,
read-only permissions, locked installs, hashed artifact installation, and
defensive cleanup. [Actions run 32551095462](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/32551095462)
passed all eight repository checks for reviewed source
`dd58590877957d4d07c1acc0b4a24ce206731c42`; its P2-G1/P2-G2 artifacts were
verified from a clean checkout and remained unexpired at owner acceptance.

The completed extension publication record is authoritative in
`extension-publication-checklist.md`. Pull request #31 merged the exact reviewed
source as `cc0d247e80e4eb9c9f320160028e3c9104770fa9` after green remote checks and
explicit scoped owner acceptance.

The private-camera harness is implemented and synthetically tested, but no
physical-camera run was performed because no owned/authorized camera, exact
egress rule, or local credential reference was supplied. Production
authenticated use remains gated on an approved external secret provider.
Physical-camera PTZ was also not attempted; the current private-camera
authorization and harness are metadata-only.

This status is not production approval and makes no claim about 80,000-camera
capacity, real-network latency, evidentiary admissibility, or police deployment.
