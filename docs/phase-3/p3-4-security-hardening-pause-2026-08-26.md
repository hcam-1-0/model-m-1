# P3.4 Security Hardening Pause - 2026-08-26

Status: resumed and technically completed locally after the recorded pause.

Branch: `codex/phase3-geometry-events`

Starting commit: `be709f3ded407f4d892db391543ab54c8141fb20`

The working tree was intentionally uncommitted at pause time and was preserved
through the resumed validation. No remote branch, pull request, merge,
deployment, camera, media, external data, Government data, or private data
action was performed.

## Completed In This Continuation

- Re-audited the local branch, GitHub issues, pull requests, and scanner
  availability.
- Confirmed no open GitHub issues. Dependabot PRs `#33` and `#34` remain open
  and failing on their original isolated branches.
- Confirmed GitHub Dependabot vulnerability alerts, secret scanning, and code
  scanning are disabled for this private repository. The current token cannot
  enable those repository settings.
- Freshly scanned the exact pinned
  `postgis/postgis:18-3.6-alpine@sha256:eb2e8b8afd9b0ecee83bc20fd01aca62a5071bada2c0f38763174b653f8eed42`
  image with Docker Scout 1.24.0. It still has 54 findings: 2 critical, 21
  high, 22 medium, 6 low, and 3 unspecified.
- Scanned the official Debian/Trixie `postgis/postgis:18-3.6` alternative. It
  was worse: 215 SARIF results, including 4 critical and 23 high. The Alpine
  pin was therefore retained.
- Redirected scan caches to `E:` after `C:` ran out of temporary space. Docker
  Scout temporary data and unused Docker build cache were pruned; project
  images, active containers, and user data were not pruned.
- Ran Bandit against application code. Initial high findings identified
  untrusted XML parsing and a dynamic `shell` parameter.
- Added explicit `defusedxml>=0.7.1,<1.0` runtime protection and changed all
  untrusted ONVIF, WS-Discovery, and authenticated simulator XML parsing to
  defused parsers.
- Removed the ffprobe wrapper's `shell` parameter and hard-coded shell-free
  process creation.
- Marked ONVIF UsernameToken Profile 1.0 SHA-1 use as protocol-mandated legacy
  interoperability with `usedforsecurity=False`; no selectable weak algorithm
  was introduced.
- Added malicious external-entity tests for HTTPX ONVIF responses, legacy
  resolver responses, WS-Discovery datagrams, and simulator WSSE bodies.
- Bandit's high/medium application gate passed with zero findings after the
  fixes. The synthetic publisher's fixed `/tmp` path remains an explicitly
  documented, tmpfs-only Bandit exception.
- The raw offline secret scan produced only unverified hashes, synthetic
  fixtures, redaction tests, and placeholders. A production-source profile
  retaining credential/provider/private-key detectors passed with zero
  candidates.
- Verified the signed `astral-sh/setup-uv` `v10.0.1` tag and updated all six CI
  action pins plus Phase 1/2 governance checks to commit
  `20cfd1bf945f4377ade1205e4dbc17946fc9a30d`.
- Expanded the reviewed setuptools range from `<84` to `<85`; the lock still
  resolves setuptools `83.0.0`.
- Regenerated deterministic P3.4 dependency/SBOM evidence. The Python audit
  reports no known vulnerabilities.
- Focused validation passed: 116 tests, Ruff, strict Phase 1 readiness, and
  strict Phase 2 readiness.

## Interrupted Work

The complete branch-coverage suite was running when the user requested the
pause. It was terminated intentionally before producing a result. Do not claim
a new full-suite pass or reuse the earlier 711-pass result for this modified
tree.

## Resume Checklist Used

1. Inspect `git status --short` and preserve every listed modification plus
   this note.
2. Keep `UV_CACHE_DIR=E:\hcam-uv-cache` and `TEMP`/`TMP=E:\hcam-scan-temp`
   because `C:` had approximately 0.41 GiB free at pause time.
3. Rerun Ruff and the Bandit high/medium application gate.
4. Rerun the production-source offline secret profile and confirm zero
   candidates.
5. Rerun the complete pytest branch-coverage suite and record the new exact
   pass/skip/coverage counts.
6. Run fresh SQLite migration upgrade/downgrade/drift validation.
7. Build the disposable loopback PostGIS stack, run all eight PostgreSQL tests,
   validate health/readiness and Alembic drift, then remove the stack and
   volume.
8. Build and inspect wheel/sdist artifacts, perform an isolated install, and
   rerun both CI-equivalent `pip-audit --skip-editable` profiles.
9. Update `p3-4-validation-evidence.json`, P3.4 validation documentation, and
   checker expectations with only newly observed results.
10. Run every Phase 0 through P3.4 readiness/contract checker and
    `phase34_implementation_readiness.py --require-clean-source --json` after a
    local commit.
11. Commit the validated local checkpoint. Do not push or open/merge a PR
    without explicit remote-action authorization.

## Gates That Remain Unchanged

- `D-P3.4-ACCEPTANCE` is still pending and must bind a newly computed final
  clean-source digest. The previous digest is superseded by this uncommitted
  hardening work and must not be accepted.
- Pilot/production deployment remains blocked by the unresolved PostGIS image
  findings.
- P3.5, physical cameras, media, model/dataset changes, external or Government
  data, identity/cross-camera linkage, alerting, and deployment remain outside
  this authorization.

## Resume Completion

- The complete repository suite passed 715 tests and 119 subtests, with 8
  expected PostgreSQL skips, one pre-existing Starlette warning, and 90.24%
  branch coverage.
- A fresh SQLite database passed `0011 -> 0010 -> 0011` and clean Alembic drift
  checks.
- A fresh loopback-only Compose stack reached migration head, liveness,
  readiness, and protected metrics. All 8 PostgreSQL/PostGIS tests passed after
  `0011 -> check -> 0010 -> 0011 -> check`; the stack and volume were removed.
- Fresh wheel and source archives contained 99 and 473 members respectively,
  with zero prohibited model, media, key, or credential paths. A hash-locked
  isolated install passed application, CLI, and dependency compatibility checks.
- Ruff, Bandit, the production-source secret profile, both CI-equivalent Python
  vulnerability audits, and the P3.4 supply-chain evidence checks pass.
- The Phase 1 strict checker no longer crashes after a stale 180-second pytest
  timeout. It uses a 600-second command bound, reports timeout/runtime failures
  explicitly, and completed its full validation with zero failures.
- The exact pinned PostGIS image still has 54 unresolved findings, including 2
  critical and 21 high. An official Debian/Trixie alternative was worse, so no
  deployment waiver was added.
- GitHub-native Dependabot vulnerability alerts, secret scanning, and code
  scanning remain disabled at repository level; the current token could not
  enable them. Local equivalent scans were completed without changing remote
  settings.
- The local checkpoint commit and final clean-source digest are generated only
  after this tracked evidence is finalized. They do not grant owner acceptance.
