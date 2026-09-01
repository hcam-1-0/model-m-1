# P3.6 U3L Machine-Handler Implementation Evidence Review

Status: implemented and statically validated; non-executable; exact owner
implementation acceptance pending.

## Authorization

`mayank-admin` authorized only the source, generated Python tests, evidence,
package, compatible ledgers, and Phase 3.6 documentation bound to proposal
package SHA-256
`EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311`.
The exact statement and its SHA-256 are recorded in the allowlisted evidence
file. The sealed proposal package was not changed.

## Implemented Source

| Artifact | SHA-256 | Role |
|---|---|---|
| `tools/phase36_quarantine_transaction_runner.ps1` | `22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A` | Preserves `Contract` mode and adds default-off static `Storage` orchestration |
| `tools/phase36_quarantine_machine_handlers.psm1` | `41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721` | Pure ten-action state machine, deadlines, stable reasons, ownership, and terminal authority |
| `tools/phase36_quarantine_windows_storage_adapter.psm1` | `232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9` | Sole direct Windows and .NET machine API boundary |
| `tests/test_phase36_quarantine_machine_handlers_generated.py` | `F36D9194A981ADE7F7C99948F4841DED680B06AE4C3A71404EFE7A752EA7D1A2` | Generated reference, static boundary, package, and ledger checks |

The runner uses a case-sensitive static map for exactly `U3K-A01` through
`U3K-A10`. It checks the exact owner receipt and the two module hashes before
import, then recomputes package, source, runtime, action, target, limit, and
output bindings in A02. Unknown, missing, duplicate, reordered, repeated, or
timed-out actions terminate without retry.

The handler module performs only pure classification and state transitions.
It contains no direct filesystem, identity, ACL, network, process, registry,
service, scanner, environment, or download operation.

The adapter contains the direct operations. Root creation uses
`CreateDirectoryW` with a non-null `SECURITY_ATTRIBUTES` descriptor. An
`ERROR_ALREADY_EXISTS` result is terminal and never grants attempt ownership.
There is no plain-create or post-create ACL rewrite fallback. Cleanup is
limited to exact attempt-created probe paths and the exact attempt-created,
empty, non-reparse root; recursive deletion is absent.

## Generated Evidence

- All 64 generated vectors passed.
- Eight generated static source-boundary checks passed.
- The generated verifier reported 72 pre-seal checks passed.
- The explicit Phase 3.6 suite reported 275 Phase 3.6 tests passed before the
  four final package and ledger integrity assertions were added.
- The original `Contract` behavior and its twenty generated vectors remain
  represented by compatibility tests.
- Ruff passed for every changed Python test path.
- Strict JSON and duplicate-key checks are required again after final sealing.

The first test command used the incomplete disposable worktree environment and
stopped during test collection because `numpy` was absent. It ran no vector and
provides no evidence. All reported passing results use the already provisioned
repository Python environment.

PowerShell was not parsed, imported, or executed. The runner, pure handler,
and Windows adapter were inspected only as source text by Python. No machine,
runtime, hardware, storage, `F:`, ACL, probe, cleanup, Defender, ModelScan,
network, model, media, data, container, Kubernetes, deployment, or remote Git
action occurred.

## Historical Packages

The prior U3I implementation package and final U3K preparation package remain
immutable. They bind the historical placeholder runner SHA-256
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.
They are retained as historical governance evidence and are not executable
against the new source.

The previously accepted runtime binding is expired and cannot be reused. A
fresh runtime binding and a newly sealed U3K package must bind the current
runner, handler, adapter, generated tests, accepted evidence, action spec, and
runtime before execution can be considered.

## Next Gate

The next decision is
`D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE` against the SHA-256
of the separate implementation package manifest. Acceptance covers only this
source and generated/static evidence.

`D-P3.6-U3K-STORAGE-R2-AUTH is not requestable` at this point. Acceptance does
not authorize PowerShell parsing, importing, or execution; runtime or hardware
observation; machine handlers; storage, `F:`, ACL, probe, cleanup;
Defender/scanners; downloads or artifacts; models or inference; camera, media,
private or Government data; containers or Kubernetes; deployment; or remote
Git.
