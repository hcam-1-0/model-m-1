# Phase 2 Publication Evidence

`tools/phase2_publication_evidence.py` generates bounded, machine-readable
evidence for the controlled ONVIF extension publication gates. It does not
change checklist state, accept the extension, publish code, contact a physical
camera, capture images, or record video.

## Evidence Identity

Every runtime report contains:

- schema `hcam.phase2.publication-evidence.v2`;
- the exact Git commit and branch;
- whether the worktree was clean;
- SHA-256 hashes of the reviewed OpenAPI and database contracts;
- the SHA-256 hash of the reviewed `uv.lock` dependency graph;
- UTC generation time, bounded command outcomes, and safety declarations.

Text identities use LF-canonicalized bytes so the same committed contracts and
lock file produce identical evidence on Windows and Linux checkouts. Any other
content change still changes the recorded SHA-256.

`P2-G1` and `P2-G2` refuse to run unless the worktree is clean and committed.
This prevents evidence from being attached to a commit that does not contain
the tested source. Generated files default to `var/evidence/`, which is ignored
by Git until a reviewer intentionally promotes an approved artifact into a
review packet.

## Read-Only Preflight

```powershell
python tools/phase2_publication_evidence.py preflight
python tools/phase2_publication_evidence.py preflight --strict
```

Preflight checks source identity, `HCAM_POSTGRES_TEST_URL`, structured Docker
server data, Docker Compose, GitHub authentication, and a pull request for the
current branch. It performs no migrations and starts no containers. Normal
preflight returns zero so its blocked JSON can be inspected; `--strict`
returns `2` when prerequisites are blocked.

Docker process exit code alone is not accepted. The probe requires a non-empty
JSON server object with a server version. This catches Docker Desktop states
that return exit code zero while reporting an engine HTTP 500 on stderr. The
server must also report Linux as its operating system; Windows-container mode
does not satisfy the Compose gate.

## PostgreSQL Gate

Use only an isolated, disposable PostgreSQL 18 database:

```powershell
$env:HCAM_POSTGRES_TEST_URL = "postgresql+psycopg://.../hcam_test"
python tools/phase2_publication_evidence.py postgres `
  --confirm-disposable-database
```

The gate uses only an official `postgresql+psycopg://` test URL and queries
`server_version_num` to prove the server major version is exactly 18. It then
upgrades to head, checks drift, runs all marked PostgreSQL tests, downgrades to
base, restores head, and checks drift again. Restoration is attempted even if
downgrade fails. The URL and its password are never written to the evidence
report.

The confirmation is an operational assertion that destroying and recreating
the supplied database schema is authorized. Never point it at a production,
shared, evidentiary, or Government database.

## Compose Gate

Run only the repository's generated 50-stream lab:

```powershell
python tools/phase2_publication_evidence.py compose `
  --confirm-synthetic-lab
```

The gate prepares generated secrets, validates the Compose model, starts the
synthetic stack, verifies C50 health and playback isolation, runs outage
recovery, and removes the stack after every start attempt. It fails before
startup when a structured Docker Linux server is unavailable.

This command does not use the Sentinel reference environment or the private
camera harness. It must not be modified to add real camera locators or footage.

## Artifact Verification

Validate a downloaded or promoted runtime report without rerunning its gate:

```powershell
python tools/phase2_publication_evidence.py verify `
  var/evidence/phase2_p2_g1_YYYYMMDDTHHMMSSZ.json `
  --gate P2-G1 `
  --expected-commit <40-character-commit-sha>
```

Verification is read-only. It accepts only a regular UTF-8 JSON file no larger
than 1 MiB and, by default, no older than seven days. It verifies the schema,
gate identity, `passed` status, clean source commit and branch, current contract
and dependency-lock hashes, exact check order and approved command shapes,
successful exit codes,
required safety declarations, and absence of credential-like values. `P2-G2`
also requires structured proof of a ready Docker Linux server and Compose.

Use `--max-age-days` only when the owner has documented a different review
window. A local artifact linked by the publication checklist must match the
repository's current `HEAD`; moving `HEAD` invalidates that local link. For the
final review commit, prefer the exact GitHub Actions run URL and retain its JSON
artifact with the run.

## CI Publication Artifacts

The `postgres-integration` and `phase2-synthetic-lab` jobs use the same guarded
runner instead of reimplementing gate commands in YAML. On pull requests, both
jobs explicitly check out the contributing repository and PR head SHA rather
than GitHub's synthetic merge commit. The report records that source SHA and
uses `GITHUB_HEAD_REF` as its branch identity when checkout is detached.

Each job uploads one commit-specific artifact for seven days:

- `phase2-p2-g1-<source-sha>` containing `p2-g1.json`;
- `phase2-p2-g2-<source-sha>` containing `p2-g2.json`.

The upload step uses immutable, verified `actions/upload-artifact` v7.0.1
commit `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`. Upload runs even after a
failed gate so reviewers can inspect the sanitized failure report, while a
missing report fails the job. Only a report whose status is `passed` satisfies
a publication gate. The Compose job also performs an unconditional defensive
stack stop after the runner's recorded cleanup.

After a green run, use the remote verifier from a clean checkout of the
reviewed commit, then link the exact Actions run in the publication checklist:

```powershell
python tools/phase2_publication_evidence.py verify-run `
  https://github.com/mayankthakor227/h-cam-2.0/actions/runs/<run-id> `
  --gate P2-G1 --expected-commit <source-sha> `
  --output var/evidence/p2-g1-run-verification.json
```

The existing local-file verifier remains available for a separately downloaded
artifact:

```powershell
python tools/phase2_publication_evidence.py verify p2-g1.json `
  --gate P2-G1 --expected-commit <source-sha>
```

The workflow configuration is not runtime evidence by itself. P2-G1 and P2-G2
remain open until these jobs execute successfully for the reviewed commit.

## Remote Run Verification

`verify-run` accepts only an exact Actions run URL in this repository. It uses
read-only GitHub run, job, and artifact metadata plus an exact-name artifact
download. It does not request workflow logs, mutate GitHub state, contact a
camera, or retain the downloaded artifact after verification.

The command fails closed unless all of the following are true:

- the local worktree is clean and its HEAD equals `--expected-commit`;
- the completed `Python CI` run used `.github/workflows/python-ci.yml`, has a
  successful conclusion, and is bound to the expected commit;
- the expected PostgreSQL or Compose job completed successfully;
- exactly one unexpired, at-most-1-MiB, commit-named artifact belongs to that
  run and reports a SHA-256 digest;
- the downloaded archive contains only the expected `p2-g1.json` or
  `p2-g2.json` payload; and
- the payload passes the existing gate, age, commit, contract, dependency-lock,
  command, safety, Docker, and credential-leak checks.

The default evidence age is seven days. Exit `1` means the remote evidence is
invalid. Exit `2` means verification is blocked by local source state, GitHub
authentication, network access, or artifact download. Reports use schema
`hcam.phase2.github-run-verification.v1`; credential-like GitHub CLI errors are
bounded and redacted.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | The requested gate passed, or informational preflight completed. |
| `1` | A gate command failed, or an evidence artifact is invalid. |
| `2` | Required confirmation or environment evidence is missing. |

## Review And Linking

A reviewer must verify that the evidence status is `passed`, the commit equals
the reviewed PR head, contract and `uv.lock` hashes match the PR, and the corresponding
GitHub Actions checks are green. Then replace the gate's `pending` marker in
`extension-publication-checklist.md` with a Markdown link to that exact run or
approved repository artifact. Local blocked reports and historic successful
runs do not satisfy current publication gates.

The readiness checker only accepts runtime URLs under
`mayankthakor227/h-cam-2.0/actions/runs/`, PR URLs under this repository's
`pull/` path, and the local `owner-review.md` decision. It fully validates a
linked local runtime JSON artifact. Before checking a remotely linked runtime
gate, the reviewer must retain the valid `verify-run` report in the review
record. Required-check and branch-protection status remain separate P2-G3
review evidence.
