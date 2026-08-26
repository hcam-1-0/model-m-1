# P3.5 Owner Decisions

Status: `owner_approved`.

On 2026-08-26, `mayank-admin` approved the recommended option `A` for all four
P3.5 technical decisions:

| Decision | Approved baseline |
| --- | --- |
| `D-P3.5-001` | Strict procedural, non-issuable synthetic corpus |
| `D-P3.5-002` | Staged plate detector, Latin-primary OCR, and auxiliary-script portfolio |
| `D-P3.5-003` | Raw-preserving, NFC, grapheme-aware, abstaining temporal consensus |
| `D-P3.5-004` | Ephemeral plate text, aggregate evidence, and zero retention |

The canonical record is
[`p3-5-owner-decisions.json`](../../contracts/phase-3/p3-5-owner-decisions.json).
These choices froze the recommended technical baseline but did not by
themselves authorize implementation. The separate digest-bound
`D-P3.5-START` gate was subsequently completed after exact artifact and runtime
review. Its authority is limited to the generated-only scope documented in
[P3.5 generated-only start authorization](p3-5-start-authorization.md).

Camera/media access, real registration marks, training, deployment, P3.6, and
remote Git operations remain prohibited.
