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
These choices freeze the recommended technical baseline. They do not authorize
runtime implementation, model execution, synthetic generation, dependency
changes, camera/media access, real registration marks, deployment, or remote
Git operations.

`D-P3.5-START` remains a separate digest-bound implementation gate.
