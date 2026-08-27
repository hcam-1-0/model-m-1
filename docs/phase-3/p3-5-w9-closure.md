# P3.5 W9 Narrow Generated-Only Closure

Status: validated generated-only closure; awaiting separate W10 clean-source
acceptance.

Authorization:
[P3.5 W9 narrow closure authorization](p3-5-w9-start-authorization.md).

Canonical evidence:
[`p3-5-w9-closure-evidence.json`](../../contracts/phase-3/p3-5-w9-closure-evidence.json).

Verifier: `tools/phase35_w9_closure.py`.

## Implemented Scope

W9 adds no product runtime behavior. It consolidates W1-W8 evidence and adds a
stdlib-only local verifier that:

- validates the exact Option A authorization, proposal hash, baseline commit,
  planning digest, actions, prohibitions, and changed-file allowlist;
- hashes seven canonical W1-W8 evidence groups without retaining generated
  values;
- runs two deterministic 10,000-observation generated-contract replays through
  the existing bounded consensus engine;
- proves default-off rejection, the 256-state ceiling, fail-closed overload,
  mandatory abstention, a 30-second ceiling, and a 128 MiB traced-memory ceiling;
- blocks an intentional socket attempt and permits no successful network access;
- builds a wheel and sdist from an isolated source copy with no package index,
  no environment proxies, fixed timestamps, no build isolation, and a temporary
  Python `sitecustomize` socket-denial guard verified before the build;
- rejects unsafe archive entries and model, weight, trained-data, font, image,
  or video payloads;
- stores only aggregate archive counts, canonical byte counts, and SHA-256
  digests.

The sdist canonical-content digest replaces the content of its own W9 evidence
entry with a fixed marker. This prevents a circular self-hash while still
binding the entry name and every other packaged byte. The raw sdist digest and
size are intentionally not retained. The wheel contains no W9 evidence and is
therefore bound by both raw-archive and canonical-content SHA-256 values.

## Deterministic Resource Result

Each replay processes exactly 10,000 ephemeral observations. It closes 2,208
results, all abstaining; observes at most 256 active states; and produces four
fail-closed overload results. The default-off engine rejects execution before
the enabled generated-test policy is supplied. No minimum-support, margin,
quality, or promotion threshold is introduced.

Only pass/fail values for the generous elapsed and memory ceilings are retained;
variable timing and memory measurements are not committed. This keeps the
canonical evidence deterministic across machines while still failing a run that
exceeds either bound.

## Zero-Retention And Security Result

Tracked W9 evidence contains no generated token, raw or normalized OCR value,
ranked vote, stream/epoch/track identifier value, pixels, media, owner record,
vehicle record, Government record, or external path. It records zero model/font
execution, zero artifact downloads, zero external-runtime access, zero final-test
opens, zero camera/external inputs, zero accepted values, and zero operational
events.

No W9 path accesses `B:` RaiDrive or the external `E:` runtime. Static denial
assertions are documentation and tests only. The package build runs from a
temporary local source copy and its archives remain untracked.

## Rollback

W9 changes only its exact tool, test, evidence, authorization and documentation
files plus existing readiness/index/CI files. It changes no application,
migration, dependency, lockfile, container, API, worker, database, or persistent
storage path.

Local rollback is therefore source-only: revert the exact W9 closure commit and
rerun the P3.5 readiness and W1-W8 evidence checks. No database downgrade,
artifact cleanup, media deletion, model rollback, or service restart is needed.
Remote push, pull request, merge, and deployment remain unauthorized.

## Verification

```powershell
uv run --locked --extra dev python tools/phase35_w9_closure.py check-evidence
uv run --locked --extra dev python tools/phase35_readiness.py --strict
uv run --locked --extra dev python -m pytest tests/test_phase35_w9_closure.py tests/test_phase35_readiness.py
```

Evidence rewriting is explicit:

```powershell
uv run --locked --extra dev python tools/phase35_w9_closure.py write --acknowledge-generated-only-closure
```

## Remaining Gate

W9 does not accept P3.5. W10 must regenerate the complete clean-source validation
package, publish its exact digest and repository head, preserve every continuing
prohibition, and receive a separate explicit owner acceptance decision.
