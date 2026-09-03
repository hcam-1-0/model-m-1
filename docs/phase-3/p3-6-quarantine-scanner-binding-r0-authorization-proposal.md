# P3.6 F: Quarantine And Scanner Binding R0 Authorization Proposal

Status: sealed planning proposal pending exact owner authorization. No `F:`
query, directory creation, write probe, scanner query, scanner execution,
installation, download, model operation, or runtime action is authorized by
this document.

Decision ID: `D-P3.6-U3E-BINDING-R0-AUTH`.

## Owner Input And Interpretation

The owner reported that `F:` was cleaned and has approximately 50 GB free, and
authorized using that drive as needed. This proposal interprets that message as
permission to prepare a bounded authorization package for `F:`. It does not
treat the reported capacity as measured evidence or as authority to query or
modify the drive.

The proposed exact quarantine root is:

```text
F:\HCAM-Quarantine
```

This new top-level root is intentionally outside the existing `F:\h cam`
project tree. `B:` remains prohibited. No other `F:` path or volume is included.

## Why Another Authorization Is Required

Accepted U3D policy requires both an owner-supplied exact root and a separate,
digest-bound, one-attempt storage and scanner binding authorization. The broad
instruction to use `F:` is not converted into unrestricted filesystem or
scanner authority.

The package therefore binds every permitted action, field, path, timeout,
output, failure rule, and continuing prohibition before an attempt can occur.

## Exact One-Attempt Scope

If the owner later accepts the exact package digest, one attempt within 24
hours may:

1. verify the accepted package and all core hashes;
2. query `F:` readiness, drive type, filesystem, total bytes, and free bytes;
3. require a fixed local NTFS/ReFS volume with at least 5 GiB and 15 percent
   free;
4. canonicalize only `F:\HCAM-Quarantine`, reject reparse components, and prove
   it is outside `F:\h cam` and every repository;
5. create only that exact directory if it does not exist;
6. inspect its ACL only long enough to project owner-write and broad-write
   booleans without persisting users, names, or SIDs;
7. create, flush, read back, hash, atomically rename, read back, hash, and delete
   one deterministic 4096-byte probe file;
8. query bounded Microsoft Defender product, engine, signature, enabled-state,
   and one local `MpCmdRun.exe` candidate's version and SHA-256 without scanning
   or updating;
9. query only installed ModelScan distribution version metadata without import,
   execution, installation, download, package-file enumeration, or path
   discovery; and
10. write only the exact sanitized authorization, result, and evidence records.

The root may remain as an empty quarantine directory after a successful probe.
Probe data has zero retention. If the attempt created the root and a failure
occurs, it may remove that root only when it is still empty. Any cleanup failure
leaves the root ineligible and requires separate review.

## Expected Result Boundaries

The attempt can establish a storage-readiness observation valid for at most 60
minutes. It cannot make the full scanner chain ready:

- Defender remains a candidate until exact offline signature verification
  policy is bound;
- ModelScan remains incomplete until exact distribution and executable digests
  and supported JSON-report behavior are validated; and
- the H-CAM framework-free passive inspector remains unimplemented and unbound.

Partial or unavailable scanner metadata is recorded without override,
installation, retry, or execution. This attempt alone cannot authorize model
artifact acquisition or pass `P36-G4`.

## Privacy And Minimization

The result may persist the exact approved operational locators
`F:\HCAM-Quarantine` and one selected system `MpCmdRun.exe` candidate path.
It must not persist:

- hostname, user identity, volume label or serial, device identifier, MAC/IP, or
  personal path;
- environment or `PATH` dumps, raw ACL users/SIDs, raw command output, stack
  traces, or exceptions;
- Defender threat history, preferences, exclusions, quarantine, or events; or
- credentials, secrets, camera/media/data facts, or unrelated software state.

## Continuing Prohibitions

Even after exact acceptance, the attempt does not authorize:

- access to or modification of `B:`, `F:\h cam`, any other `F:` path, or any
  other volume;
- scanner execution, remediation, signature/platform/security-intelligence
  updates, ModelScan installation, or passive-inspector implementation;
- artifact, model, dataset, dependency, driver, source, or container download;
- checkpoint loading, unpickling, framework import, conversion, export,
  inference, calibration, validation, benchmark, or hardware test;
- profile admission, activation, placement, promotion, or capacity claim;
- cameras, streams, media, private/Government data, Docker, Kubernetes,
  deployment, product implementation, or remote Git.

## Exact Acceptance Template

```text
D-P3.6-U3E-BINDING-R0-AUTH: I, mayank-admin, authorize one local binding attempt against package digest <PACKAGE_DIGEST_SHA256> within 24 hours for exact candidate root F:\HCAM-Quarantine. The attempt may query only F: readiness, fixed-drive type, NTFS/ReFS filesystem, total and free capacity, exact canonical/reparse/ACL properties; create only F:\HCAM-Quarantine if absent; perform and clean one 4096-byte atomic create/flush/readback/rename probe; query only bounded Microsoft Defender and ModelScan metadata without scanner execution or updates; and write only the exact sanitized authorization, result, and evidence records. Failure consumes the authorization and requires a new digest-bound authorization. This does not authorize any other path or volume, B:, F:\h cam, scanner execution, installation, update, download, artifact acquisition, checkpoint loading, inference, validation, hardware testing, media/data, containers/Kubernetes, implementation, deployment, or remote Git.
```

The final package digest must replace `<PACKAGE_DIGEST_SHA256>`. A generic
`continue`, the earlier permission to use `F:`, or any prior acceptance does not
accept the package or authorize the attempt.
