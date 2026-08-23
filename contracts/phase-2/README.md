# Phase 0-2 Release Contracts

These reviewed snapshots protect the public HTTP API and the Alembic-migrated
database schema from accidental drift across Phase 0, Phase 1, and Phase 2.

- `openapi.json` is generated from the actual FastAPI application.
- `database.json` is inspected from a disposable SQLite database upgraded to
  the current Alembic head.

Verify them with:

```powershell
python tools/release_contracts.py check
```

Contract changes require review of authentication, authorization, scope,
request/response compatibility, migration safety, indexes, foreign keys,
constraints, and downgrade implications. After that review, update both
deterministically with:

```powershell
python tools/release_contracts.py write --acknowledge-reviewed-change
```

The acknowledgment only prevents accidental local rewrites. Pull-request
review and CI remain the approval boundary. Snapshots contain metadata only;
they contain no camera locators, credentials, footage, or Government data.
