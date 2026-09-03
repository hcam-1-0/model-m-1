# P3.6 Quarantine Remediation R1 Consumed Attempt

Decision: `D-P3.6-U3G-BINDING-R1-AUTH`

Status: the exact one-attempt authorization was accepted against package digest
`C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
The attempt is consumed, failed closed, and grants no retry or continuing
machine authority.

## Immutable Evidence

| Record | SHA-256 |
| --- | --- |
| Authorization | `12DBCEA9BB4C7AECDED5A42CCE2962CFBB689488F1B713990687DE876AC01070` |
| Result | `417AB2F17C42FD6313CC2798AC055EEF75AB16F0431BE6486619C762FA253226` |
| Evidence | `B1D454E1F1390C0FB7D594D80197BA87DA75B5D4216CBF9177F8883E46268B4D` |

Machine-readable records:

- [authorization](../../contracts/phase-3/p3-6-quarantine-remediation-r1-authorization.json);
- [result](../../contracts/phase-3/p3-6-quarantine-remediation-r1-result.json); and
- [bounded evidence](../../contracts/phase-3/p3-6-quarantine-remediation-r1-evidence.json).

## Storage Outcome

The volume and exact absent-path prerequisites passed. The root was created
with the protected security descriptor at creation, but post-create semantic
verification did not find the current-process `Modify` rule in the exact form
required by the package. The DACL gate therefore failed closed.

The atomic probe was not executed. The attempt-created empty root was removed,
no probe bytes were retained, and no passing storage attestation was issued.
Raw ACLs, identities, SIDs, security descriptors, and exception text were not
persisted.

## Defender Outcome

The bounded Defender status operation did not yield a usable normalized
product version. Candidate resolution, binary hashing, and cache-only
WinVerifyTrust were therefore skipped. `MpCmdRun.exe` was not executed, no scan
or update occurred, and no certificate or chain data was persisted.

## Gate Effect

`P36-G1`, `P36-G2`, `P36-G4`, and `P36-G5` remain blocked. ModelScan remains
deferred, the passive inspector remains unimplemented, and the scanner chain
is not ready. Artifact acquisition, model loading, runtime execution,
validation, hardware testing, containers/Kubernetes, cameras or media,
implementation, deployment, and remote Git remain unauthorized.

Any future retry requires new failure analysis, a new immutable action and
authorization package, a new digest, and a new exact owner authorization. The
consumed U3G statement cannot be reused.
