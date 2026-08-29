## Summary

Explain the user-visible outcome and the problem being solved.

## Scope

- [ ] The change is limited to the stated issue or project item.
- [ ] No unrelated generated files, runtime data, recordings, or local secrets are included.
- [ ] A linked issue, architecture decision, or risk item exists when the change affects a public contract.

## Safety And Data Handling

- [ ] No CCTV video is committed or attached.
- [ ] No credentials, tokens, cookies, private URLs, or local configuration are committed.
- [ ] No government data, police records, or personally sensitive data are included.
- [ ] Camera sources are allow-listed and fail closed; no domain crawling or broad probing was added.
- [ ] Recording, analytics, camera control, and retention behavior remain disabled unless explicitly reviewed in scope.

## Validation

- [ ] `uv run --locked --extra dev --extra postgres --extra cam-adapter ruff check app tests tools migrations`
- [ ] `uv run --locked --extra dev --extra postgres --extra cam-adapter pytest`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `git diff --check`
- [ ] Dashboard/API changes include focused smoke tests and an accurate live-media verification note.

## Operational Evidence

List relevant Actions runs, screenshots with sensitive data removed, migration evidence, or manual gates. Do not claim decoded live video solely from an HTTP `200` response.

## Review Notes

Call out migrations, API compatibility, security boundaries, rollback steps, and any follow-up Project items.
