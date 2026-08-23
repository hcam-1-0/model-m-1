# Controlled ONVIF Extension Publication Checklist

Status: `pending`

Phase 2 core was accepted and merged before the authenticated capability
management and controlled ONVIF operations extension was implemented. This
checklist prevents that earlier decision from being treated as acceptance of
the unpublished extension.

## Local Implementation Evidence

- [x] Authenticated capability jobs, cache/history, controlled operations,
  migration `0006`/`0007`, observability, and documentation are implemented.
- [x] Offline tests, branch coverage, static checks, SQLite migration checks,
  readiness validation, and package builds pass.
- [x] Exact DNS answers are validated and the selected address is pinned while
  preserving Host/TLS SNI; a real private-CA TLS test passes.
- [x] Controlled operations and synchronous discovery persist pending audit
  intent before network activity, correlate it by operation ID, and retain a
  pending lifecycle row without a snapshot if completion fails.
- [x] Reviewed deterministic OpenAPI and migrated-database snapshots fail CI
  and readiness validation when an unacknowledged release contract drifts.
- [x] The reviewed universal `uv.lock` governs local, CI, package, and container
  installs; publication evidence fails verification after dependency drift.
- [x] Scheduled capability queues and expired-lease recovery create durable,
  transactional audit evidence; recent recovery remains visible in protected
  low-cardinality metrics, alerts, and the Phase 2 dashboard.
- [x] Manual refresh admission recovers active-job uniqueness races by returning
  the winning job, and the 60-second cooldown begins at terminal completion.
- [x] Terminal refresh processing prunes expired capability history while
  preserving the newest inventory snapshot for every stream.
- [x] Disabled or missing streams terminalize queued work with lease cleanup,
  failure audit, retention, and no camera contact or false idle result.
- [x] Physical-camera control remains prohibited; synthetic PTZ evidence does
  not authorize movement of an owned or third-party camera.

## Publication Gates

- [ ] `P2-G1` Migration `0007` passes the current PostgreSQL 18 upgrade, drift,
  downgrade, concurrent-worker, and concurrent queue-admission gates.
  Evidence: `pending`
- [ ] `P2-G2` The current Phase 2 Compose stack passes C50 health, playback isolation,
  outage recovery, protected metrics, and zero-outbox-backlog checks.
  Evidence: `pending`
- [ ] `P2-G3` A reviewable pull request for the extension completes with green required
  remote CI checks.
  Evidence: `pending`
- [ ] `P2-G4` The repository owner explicitly accepts the controlled ONVIF extension
  under its default-off safety boundaries.
  Evidence: `pending`

## Evidence Rules

Every checked gate must replace `pending` with at least one Markdown link to
its exact evidence. Runtime gates should link the current GitHub Actions run or
a repository evidence artifact tied to the reviewed commit. The PR gate should
link the reviewed pull request with green required checks. Owner acceptance
should link the signed-off decision in `owner-review.md` or the accepted PR.
CI publishes seven-day `phase2-p2-g1-<source-sha>` and
`phase2-p2-g2-<source-sha>` artifacts from PR-head-bound jobs. The reviewer must
run `verify-run` from a clean checkout of the reviewed source SHA and retain its
valid JSON report before linking the run; artifact presence or URL shape alone
does not satisfy a gate.

The readiness verifier fails closed when a gate is missing, duplicated,
reordered, checked without linked evidence, linked through an unsafe path, or
points at a missing repository file. Runtime and PR URLs must belong to
`mayankthakor227/h-cam-2.0`. Linked local runtime JSON is validated for source
commit, age, current contract and dependency-lock hashes, complete approved checks, safety
declarations, and credential leakage. `Status` must remain `pending` while any
gate is open and must change to `accepted` only when all four gates pass.

Use `tools/phase2_publication_evidence.py` to preflight the environment and to
generate sanitized, clean-commit-bound `P2-G1` or `P2-G2` JSON evidence. The
runner does not update this checklist; a reviewer must inspect and link the
result before checking a gate. Use its `verify` command before attaching or
promoting a local artifact, or its `verify-run` command before linking a remote
Actions run. The default maximum age is seven days.

Until all publication gates are checked with linked evidence, the machine
status is `accepted_core_extension_pending`. Phase 2 core acceptance and Phase
3 planning authorization remain valid, but the extension is not accepted or
published.
