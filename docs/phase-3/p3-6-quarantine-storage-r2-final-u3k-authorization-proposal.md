# P3.6 U3K Storage R2 Final Package Preparation

Status: final U3K preparation artifact produced; execution authorization is not
requestable because the accepted runner has no implemented machine handlers.

## Preparation Authority

`D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` accepts evidence SHA-256
`4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`
and authorizes preparation only of this separate final U3K storage package.
The acceptance-record SHA-256 is
`F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E`.

The accepted runtime binding is for exact
`C:\Program Files\PowerShell\7\pwsh.exe`, runtime SHA-256
`362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139`,
and is valid through `2026-09-01T19:36:06.820Z`.

## Bound Storage Design

The package preserves the accepted U3J storage-only design:

- logical node `LAB-LAPTOP-01`;
- exact initially absent root `F:\HCAM-Quarantine`;
- one future attempt only;
- actions `U3K-A01` through `U3K-A10` in exact order;
- protected security-at-create DACL with the accepted normalized tuple policy;
- one generated 4096-byte zero-retention atomic probe;
- bounded sanitized authorization, result, and evidence records;
- no network, Defender, ModelScan, scanner, download, model, media, or data
  action; and
- no retry after a consumed attempt.

U3J proposal-package SHA-256 is
`8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`;
its acceptance-record SHA-256 is
`6F68EB164DC662086F7444D49638FFAB95F7FF1586469BB5E5E2DC876185AAA5`.

## Execution Blocker

The exact accepted runner source SHA-256 is
`C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15`.
It is parser-valid and passes twenty generated contract vectors, but all ten
machine-action handlers deliberately throw `P36_MACHINE_HANDLER_NOT_IMPLEMENTED`.
Its accepted implementation package and acceptance-record SHA-256 values are
respectively
`71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`
and `70F2EE1133648F16CA6298C25FB6C46F56AA7C88FBA97553BDD0A2F55D90C63A`.

Therefore this package must not be described as executable, and
`D-P3.6-U3K-STORAGE-R2-AUTH` is not currently requestable. That decision
cannot be used against this package. Doing so would authorize a runner that
cannot perform the sealed transaction and has no accepted machine-handler
evidence.

## Required Next Work

Before an executable U3K package can be regenerated:

1. Prepare and explicitly authorize a digest-bound machine-handler
   implementation package.
2. Implement only the ten accepted U3K actions with fail-closed boundaries.
3. Add generated, static, failure, cleanup, redaction, and authorization tests.
4. Seal and separately accept exact source and evidence.
5. Refresh the runtime binding if it has expired.
6. Regenerate a new final executable U3K package against those exact hashes.
7. Obtain separate `D-P3.6-U3K-STORAGE-R2-AUTH` before any `F:` access.

This preparation authorizes none of those steps. It also authorizes no runner
or runtime execution, `F:` or `B:` access, ACL operation, probe, scanner,
download, model, inference, media/data, container/Kubernetes, deployment, or
remote Git action.
