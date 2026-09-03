# Summary

Explain what changed and why it belongs in this phase.

## Scope

- Phase / backlog item:
- Main files changed:
- Out of scope:

## Safety And Data Handling

- [ ] This PR does not commit CCTV video, credentials, secrets, government data, police records, or personally sensitive data.
- [ ] Any Sentinel fixture output remains under ignored local paths such as `fixtures/sentinel/`.
- [ ] Any sample data is clearly synthetic, public, or metadata-only.
- [ ] Any new external endpoint, data source, or integration is documented before use.

## Validation

List the commands run and the result.

```powershell
python -m py_compile tools/sentinel_cctv_probe.py
python -m unittest discover -s tests -v
git diff --check
```

## Documentation And Backlog Impact

- [ ] Related Phase 0 docs are updated, or this PR does not require doc changes.
- [ ] Related backlog, review question, or decision record is updated when scope changes.
- [ ] Phase movement is not implied unless the Phase 0 acceptance checklist is reviewed.

## Reviewer Notes

Call out risks, assumptions, follow-up issues, or decisions needed from the project owner.
