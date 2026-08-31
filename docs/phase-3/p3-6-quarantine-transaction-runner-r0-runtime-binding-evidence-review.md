# P3.6 U3I Runtime Binding R0 Evidence Review

Status: exact generated evidence sealed; owner acceptance pending.

## Binding

- Authorization decision: `D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH`
- Authorization package SHA-256:
  `37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`
- Authorization-record SHA-256:
  `1C3144D82EA1B41B3FBBE7E70F5BF74ED5EE5ACC709CAB272E2CBD287253648F`
- Result-record SHA-256:
  `643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7`
- Evidence-record SHA-256:
  `4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`
- Logical node: `LAB-LAPTOP-01`
- Attempt: one of one, consumed
- Started: `2026-08-31T19:36:05.800Z`
- Completed: `2026-08-31T19:36:06.820Z`
- Binding valid through: `2026-09-01T19:36:06.820Z`

## Result

The binding state is `bound_until_observed_at_plus_86400_seconds`. All eight
allowlisted actions succeeded. The exact fixed path was canonical, every fixed
component was non-reparse, and the target was a regular online file. Observed
metadata was:

- file size: `301368` bytes;
- file version: `7.6.5.500`;
- product version:
  `7.6.5 SHA: ea554a8f9c6085f54fb2828f7ea286c65c35599f+ea554a8f9c6085f54fb2828f7ea286c65c35599f`;
- PowerShell product classification: passed;
- PowerShell major version 7: passed;
- runtime SHA-256:
  `362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139`;
- cache-only whole-chain-excluding-root WinVerifyTrust: trusted;
- provider state close: passed; and
- accepted runner-source SHA-256:
  `C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.

Neither `pwsh.exe` nor the runner was executed. There was no alternate runtime
discovery, network access, `F:` or `B:` access, storage or ACL access,
Defender/scanner action, model/inference/media/data access, container or
Kubernetes action, deployment, or remote Git action. Raw output was not
persisted.

## Acceptance Effect

Exact evidence acceptance authorizes preparation only of a new, separate final
U3K storage package while this binding remains valid. It does not authorize
runner or runtime execution, implementation of machine handlers, a storage
attempt, `F:` or ACL access, Defender/scanners, downloads, artifact
acquisition, model loading or inference, media/data access, containers,
Kubernetes, deployment, or remote Git. The later U3K package would still need
its own exact digest-bound `D-P3.6-U3K-STORAGE-R2-AUTH` before any attempt.

## Exact Owner Decision

```text
D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE: I, mayank-admin, accept runtime-binding evidence SHA-256 4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C and result SHA-256 643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7, produced under authorization-package digest 37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9 for runtime SHA-256 362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139 and runner-source SHA-256 C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15, valid through 2026-09-01T19:36:06.820Z. This authorizes preparation only of a separate final U3K storage package. It does not authorize runtime or runner execution, machine handlers, storage or ACL access, Defender/scanners, acquisition, models, inference, media/data, containers/Kubernetes, deployment, or remote Git.
```
