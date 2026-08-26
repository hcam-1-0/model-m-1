# P3.5 Planning Readiness Report

Status: `ready_for_owner_decisions` under `D-P3.5-PLAN-AUTH`.

Scope: `phase3.p3_5.synthetic_anpr.planning_only`.

## Technical Readiness

- accepted P3.4 dependency is bound to immutable digest
  `11CCD757E2308F56EE5912B70861B8A977DBD8B7CEE8DBD434265A28988EF8AF`;
- the owner statement is recorded as planning-only authorization;
- all six existing plate/OCR candidate manifests remain pending, blocked, and
  artifact-unresolved;
- ten current primary sources are recorded with limitations and no artifact,
  dataset, or model download;
- non-issuable synthetic source, localization, OCR, Unicode normalization,
  grapheme metrics, abstention, consensus, privacy, resources, and generated
  evidence are specified;
- the accepted zero-retention/no-access-role plate-text policy is preserved;
- the planning package includes no P3.5 application, migration, deployment,
  model, font, dictionary, generated image, media, or dataset file;
- an eight-slot metadata-only artifact proposal records immutable sources and
  bounds where available while all SHA-256, download, and execution authority
  remains blocked;
- the early exact `D-P3.5-START` statement is preserved as non-effective intent;
- root, contract/phase indexes, backlog, decision register, checklist, and CI
  contain the same planning-only status.

The exact live package digest is emitted by `tools/phase35_readiness.py`. It
must be regenerated from clean committed source before owner decisions are
bound to a planning checkpoint.

## Manual Owner Gates

Five explicit gates remain:

1. `D-P3.5-001`: synthetic corpus, token grammar, and source policy;
2. `D-P3.5-002`: detector and OCR portfolio;
3. `D-P3.5-003`: normalization, confidence, abstention, and consensus;
4. `D-P3.5-004`: privacy, persistence, resources, and evaluation;
5. `D-P3.5-START`: final digest-bound implementation authorization after
   `D-P3.5-ARTIFACT-RESEARCH` and exact artifact review.

The first four decisions freeze technical planning only. They do not authorize
implementation. The early exact `D-P3.5-START` statement does not bind
undisclosed artifacts or network actions and remains non-effective. After the
first four choices, `D-P3.5-ARTIFACT-RESEARCH` must separately authorize only
the exact quarantine proposal. Final start confirmation must bind the completed
review packet digest.

## Verification

```powershell
uv run --locked --extra dev python tools/phase35_readiness.py --strict
uv run --locked --extra dev python tools/phase35_readiness.py --json
```

After a local planning commit, add `--require-clean-source` to verify the exact
tracked package. Add `--require-decisions` only after the owner has made and
recorded all five explicit decisions.

## Continuing Boundaries

No model, weight, font, dictionary, dataset, source archive, dependency,
container, generated image, training run, inference run, product module,
migration, API, worker, database, camera, media, Sentinel stream, real
registration mark, vehicle/owner record, Government database, identity,
cross-camera link, watchlist, alert, enforcement action, pilot, production
deployment, P3.6 work, push, pull request, or merge is authorized.
