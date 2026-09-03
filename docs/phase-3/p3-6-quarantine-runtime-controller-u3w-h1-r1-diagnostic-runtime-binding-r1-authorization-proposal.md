# P3.6 U3W H1 R1 Diagnostic Runtime-Binding Authorization Proposal

## State

- Preparation authority:
  `D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-ACCEPTANCE`
- Accepted implementation package SHA-256:
  `AB6861A7A3074BD12B36AFE7B8B88BE58EB0A643583D577E586BE1B785E6F0BD`
- Acceptance record SHA-256:
  `5B8847FF5E484C40D0630C2E9B91D41D877662D27648BCB951962117C25B7DD5`
- Future decision:
  `D-P3.6-U3W-H1-R1-DIAGNOSTIC-RUNTIME-BINDING-R1-AUTH`
- Current attempts authorized: zero
- PowerShell execution currently authorized: no

## Proposed attempt

U3W proposes one single-use diagnostic attempt on `LAB-LAPTOP-01` within a
24-hour authorization window. A failed, incomplete, or timed-out attempt would
consume the authorization. There is no automatic retry or parallel attempt.

The future attempt would bind only
`C:\Program Files\PowerShell\7\pwsh.exe`, its three fixed parent components,
the authorization-bound checkout, and five exact accepted source files. It
would then launch one process with `-NoLogo`, `-NoProfile`, `-NonInteractive`,
and the exact accepted U3V diagnostic harness.

The process would have a 30-second timeout, 4 KiB stdout limit, zero stderr,
and a 16 KiB result limit. The exact harness may dot-source only the accepted
controller whose SHA-256 is
`78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB`.

## Success and failure

Success requires `controller_projection_valid`, controller family
`policy_valid`, eight checked diagnostic groups, zero retained raw controller
bytes, stable runtime and source identities, and every machine, fallback,
retry, U3K, and deployment authority flag remaining false.

A non-success result may retain only one of the eleven allowlisted diagnostic
reason codes and one of three reason families. It must not retain candidate
values, type names, keys, raw projection, exception, stdout, stderr,
environment, identity, or security material. Diagnostic failure is not success
evidence and cannot authorize U3K.

## Explicit exclusions

The proposal contains no authority for an attempt. Until the exact future
package digest is accepted, it authorizes no PowerShell parsing, import,
dot-sourcing, or execution and no runtime or parent observation.

The future proposed scope excludes alternate runtime or hardware discovery,
Utility-manifest or module-closure work, environment or registry inventory,
Python execution, machine or storage actions, `F:`, `B:`, ACLs, probes,
cleanup, Defender or scanners, network or trust retrieval, downloads,
artifacts, models, inference, cameras, media, private or Government data,
containers, Kubernetes, profile activation, deployment, U3K, and remote Git.

## Gate sequence

1. Seal this non-effective proposal and authorization package.
2. Obtain exact digest-bound owner authorization for one U3W attempt.
3. Perform at most one exact authorized attempt.
4. Seal bounded sanitized result and evidence.
5. Obtain separate owner acceptance of U3W evidence.
6. Keep U3K and every deployment gate closed unless separately authorized.

Proposal preparation, static validation, `continue`, or silence cannot be
treated as runtime authorization.
