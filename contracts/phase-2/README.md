# Phase 0-2 Release Contracts

These immutable historical snapshots record the accepted public HTTP API and
Alembic-migrated database schema through Phase 2.

- `openapi.json` is generated from the actual FastAPI application.
- `database.json` was inspected from a disposable SQLite database at the
  accepted Phase 2 Alembic head.

The active release-contract verifier now targets the additive Phase 3 baseline
under `contracts/phase-3/`. Do not regenerate these Phase 2 files with that
tool. Their continued presence permits historical review and publication-
evidence verification.

Verify the current baseline with:

```powershell
python tools/release_contracts.py check
```

Current contract changes require review of authentication, authorization,
scope, request/response compatibility, migration safety, indexes, foreign keys,
constraints, and downgrade implications. After that review, update the Phase 3
baseline deterministically with:

```powershell
python tools/release_contracts.py write --acknowledge-reviewed-change
```

The acknowledgment only prevents accidental local rewrites. Pull-request
review and CI remain the approval boundary. Snapshots contain metadata only;
they contain no camera locators, credentials, footage, or Government data.
