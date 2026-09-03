# P3.6 Quarantine Storage R2 Authorization Proposal

Planning acceptance: `D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE`

Future execution authority: `D-P3.6-U3K-STORAGE-R2-AUTH`

Status: non-effective planning proposal. The U3K execution package cannot be
issued yet because the transaction runner is not implemented, tested, bound,
or accepted. This document does not authorize `F:` access, ACL work, a probe,
runner implementation or execution, Defender, scanners, runtime queries,
downloads, deployment, or remote Git.

## Relationship To U3H And U3I

The owner selected U3H `A/A/A/A/A/A`, including storage-first decomposition,
exact `Modify | Synchronize` normalization, independent ACL tuple checks, and a
content-hashed runner proposal. The U3H acceptance SHA-256 is
`802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`.

The non-executable runner implementation-authorization proposal is separately
sealed under digest
`712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`.
It is still pending owner authorization, contains no handlers, and cannot touch
a machine. Storage R2 cannot become executable until that runner is separately
authorized, implemented, tested against twenty generated vectors, sealed, and
accepted with an exact runtime binding.

## Exact Storage Scope

| Boundary | Exact value |
| --- | --- |
| Logical node | `LAB-LAPTOP-01` |
| Candidate volume | `F:` only |
| Candidate root | `F:\HCAM-Quarantine` only |
| Excluded project path | `F:\h cam` |
| Prohibited volume | `B:` |
| Initial state | Absent; existing file, directory, or reparse object fails without modification |
| Volume | Ready, fixed, NTFS/ReFS |
| Free-space floor | At least 5 GiB and at least 15% |
| Future attempts | One, under a later U3K package and statement |
| Future use window | 24 hours |
| Per-action timeout | 30 seconds |
| Total transaction timeout | 120 seconds |
| Probe | One generated 4096-byte atomic probe with zero content retention |
| Network | Disabled |
| Defender/scanner actions | None |
| Automatic retry | None |

## Corrected DACL Semantics

The future descriptor remains protected and contains only three explicit,
inheritable allow rules:

| Principal | Requested rights | Required returned semantic rights |
| --- | --- | --- |
| Ephemeral current-process SID | `Modify` | Exactly `Modify` plus automatic `Synchronize` |
| LocalSystem (`S-1-5-18`) | `FullControl` | Exactly `FullControl` |
| Built-in Administrators (`S-1-5-32-544`) | `FullControl` | Exactly `FullControl` |

The current-process rule must not contain `ChangePermissions`, `TakeOwnership`,
`FullControl`, generic-all, or unknown bits. Subset matching is prohibited.

Each rule is classified independently by in-memory SID, normalized rights,
inheritance, propagation, and access type. Rule count, inherited-rule absence,
deny-rule absence, and unauthorized-principal absence are separate booleans.
This prevents a rights-normalization failure from being mislabeled as an
unauthorized principal. Only bounded booleans may be retained; raw ACL, SDDL,
security descriptor, SID, and account names are prohibited.

## Reserved Future Sequence

The final U3K package, when all prerequisites exist, may bind only:

1. `U3K-A01`: bind UTC start time.
2. `U3K-A02`: verify package, owner statement, runner/runtime, target, window,
   attempt state, limits, and exact static action sequence.
3. `U3K-A03`: persist sanitized authorization before machine access.
4. `U3K-A04`: read only allowlisted `F:` drive properties.
5. `U3K-A05`: verify canonical, isolated, non-reparse, absent root.
6. `U3K-A06`: construct the exact protected descriptor in memory.
7. `U3K-A07`: create the exact absent root with security at creation.
8. `U3K-A08`: verify normalized ACL tuples and independent policy booleans.
9. `U3K-A09`: perform and clean one generated atomic probe.
10. `U3K-A10`: write only sanitized result and evidence records.

Unknown, missing, duplicate, reordered, disabled, or changed actions fail before
machine access. No Defender operation is present in the allowlist.

## Future Outputs

A later exactly authorized attempt may write only:

- `contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json` before
  machine access;
- `contracts/phase-3/p3-6-quarantine-storage-r2-result.json`; and
- `contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json`.

The result can contain allowlisted capacity buckets, storage state, reason code,
root lifecycle booleans, DACL policy booleans, probe policy booleans, and a
bounded freshness timestamp. It cannot contain identities, raw ACLs, device
identifiers, raw errors, command output, probe bytes, secrets, or personal
paths.

## Required Sequence Before Execution

1. Exact U3I runner-proposal implementation authorization.
2. Reviewable runner and generated contract-harness implementation.
3. All twenty generated vectors passing without machine or network access.
4. Exact implemented runner digest and runtime path/version/hash/trust binding.
5. Sealed implementation evidence and explicit owner acceptance.
6. Exact U3J storage-proposal planning acceptance.
7. A new final U3K package binding every exact artifact and limit.
8. Separate exact U3K owner execution authorization within its use window.

U3J acceptance alone cannot skip any step.

## U3J Planning Acceptance Template

The final proposal-package digest replaces
`<STORAGE_R2_PROPOSAL_PACKAGE_DIGEST_SHA256>`:

```text
D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE: I, mayank-admin, accept the non-effective storage-only R2 action and authorization proposal against package digest <STORAGE_R2_PROPOSAL_PACKAGE_DIGEST_SHA256>. I accept exact F:\HCAM-Quarantine absent-root targeting, security-at-create, current-process Modify plus automatic Synchronize normalization, independent exact three-tuple DACL checks, one generated 4096-byte zero-retention atomic probe, bounded sanitized outputs, no Defender or scanner work, and no automatic retry. This acceptance authorizes preparation only of a later final execution package after the separately authorized runner is implemented, tested, sealed, and accepted. It does not authorize runner implementation or execution, F: or ACL access, a storage attempt, hardware or runtime queries, Defender/scanners, downloads, models, inference, media/data, containers/Kubernetes, deployment, or remote Git.
```

The future `D-P3.6-U3K-STORAGE-R2-AUTH` template in the machine-readable
proposal is deliberately unusable now because the implemented runner, runtime
binding, implementation evidence, and final U3K package digests do not exist.
