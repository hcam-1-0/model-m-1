# P3.3 Entry Decision Packet

Status: owner decisions pending; implementation not authorized.

Planning authority: `D-P3.3-PLAN-AUTH`.

Accountable owner: `mayank-admin`.

## Decision Rule

Each decision is independent. Accepting the plan does not authorize downloads
or implementation. Accepting an artifact does not authorize a dataset, media,
camera, deployment, or the next milestone. `D-P3.3-START` is valid only after
the prerequisite records bind exact hashes and all required evidence is green.

`DR-0026` permits accountable-owner self-review. A separate reviewer is
optional and cannot block the owner decision, but technical evidence is not
waived.

## Fixed Invariants

- Tracking is anonymous, per-camera, per-stream, and per-epoch.
- No appearance embedding, ReID, biometrics, identity, or cross-camera linkage.
- Input is generated structured observations or the accepted normalized P3.2
  observation contract; no media input path exists.
- Every discontinuity that could make association ambiguous starts a new epoch.
- Every queue, memory, track, time, and retention boundary is explicit and
  testable.
- Generated metrics do not support real-world performance claims.
- Runtime is default-off and forbidden in production for this milestone.

## D-P3.3-001: Plan And Safety Contract

Decision: accept, revise, or reject the P3.3 plan, including:

- the two evidence lanes;
- exact-class Tier A association partitions;
- stream/epoch isolation and reset semantics;
- no state restoration after worker restart;
- generated-only APIs and data;
- persistence, outbox, retention, RBAC, audit, observability, and exit evidence;
- continued prohibitions.

Recommended: accept. This provides a complete implementation boundary without
granting implementation authority.

Exact acceptance form:

> I, mayank-admin, accept D-P3.3-001 and the P3.3 stream-local tracking plan under its documented generated-only, anonymous, default-off boundaries. This does not authorize source, package, model, or dataset downloads, implementation, cameras or media, public/private/Government data, cross-camera linkage, deployment, P3.4, or remote Git actions.

## D-P3.3-002: Exact Tracker Source And Adaptation

Decision: approve the acquisition plan for a pinned FoundationVision ByteTrack
commit and only the minimal source files needed for association, matching, base
track, and Kalman behavior.

Recommended implementation approach:

- preserve the MIT license and attribution;
- do not import the full YOLOX project into the H-CAM runtime;
- adapt only the pinned algorithmic source behind `StreamLocalTracker`;
- remove image, detector, Torch, training, visualization, and deployment paths;
- permit only NumPy and a reviewed linear-assignment dependency already frozen
  in an exact lock;
- validate deterministic behavior against a separately isolated pinned upstream
  oracle before promotion;
- record commit, file list, before/after hashes, patch, license, SBOM, and parity
  evidence.

This decision cannot be finally accepted until the exact commit, file hashes,
dependency versions, and license review are recorded. The present planning
packet authorizes none of those downloads.

Later exact acceptance form:

> I, mayank-admin, accept D-P3.3-002 for the exact ByteTrack source manifest and digest presented with the decision record. I authorize only the recorded source acquisition and H-CAM adaptation path; no dataset, media, camera, ReID, cross-camera tracking, deployment, or redistribution is authorized.

## D-P3.3-003: Generated Suite And Evaluation Oracle

Decision: approve `DATA-TRK-GEN-R0` and a pinned TrackEval commit as a
development-only metric oracle.

Recommended boundary:

- generated normalized boxes, classes, confidence, sequence, timestamps, and
  generated ground truth only;
- all Tier A classes and every scenario listed in the plan;
- no images, video, external data, local paths, URLs, or user-submitted boxes;
- canonical MOT-format export created only in a temporary controlled directory;
- exact TrackEval source commit, license, hash, dependency lock, and SBOM;
- network-free evaluation after acquisition;
- HOTA, DetA, AssA, LocA, IDF1, IDP/IDR, MOTA, switches, and fragments;
- reports labeled generated-only and non-representative.

This decision cannot be finally accepted until exact generated-suite and
TrackEval manifests are available. No MOTChallenge or other external dataset is
included.

Later exact acceptance form:

> I, mayank-admin, accept D-P3.3-003 for the exact DATA-TRK-GEN-R0 and TrackEval manifests and digest presented with the decision record. I authorize only generated structured tracking evaluation; no external dataset, image, video, camera, Government/private data, or real-world performance claim is authorized.

## D-P3.3-004: Lifecycle, Resource, And Metric Policy

Decision: accept or revise the proposed operational contract before code binds
it.

Recommended policy:

- exact-class association for all seven Tier A classes;
- two-observation confirmation;
- 0.10 low-confidence floor;
- 3-second and 30-sampled-frame lost-state ceiling;
- 300 observations per frame;
- 512 active plus lost tracks per stream;
- 32 generated stream lanes per worker;
- 64 queued batches per stream and 1,000 ms maximum queue age;
- 250 ms generated-batch association budget and 256 MiB incremental worker
  memory budget on the approved reference profile;
- reset on restart, reconnect, source/config/version change, unsafe ordering,
  or overload;
- no interpolation, appearance features, checkpoint restore, or track rebirth
  after epoch end;
- golden HOTA and IDF1 of 1.00, challenge HOTA at least 0.85 and IDF1 at least
  0.90, per-class HOTA at least 0.80 and IDF1 at least 0.85, zero isolation
  violations, and no regression greater than 0.02.

Recommended: provisionally accept for implementation, with measured resource
results and metric outcomes required again at exit. If the approved tracker
cannot satisfy a proposed quality threshold, the implementation must stop and
return a new decision packet rather than lower the gate silently.

Exact acceptance form:

> I, mayank-admin, accept D-P3.3-004 with the lifecycle, resource, isolation, and generated-metric policy stated in the P3.3 decision packet. Any threshold or boundary change requires a new owner decision. This does not authorize implementation, real media, cross-camera tracking, deployment, or operational claims.

## D-P3.3-START: Explicit Implementation Start

This decision is unavailable until:

- `D-P3.3-001` and `D-P3.3-004` are accepted;
- exact `D-P3.3-002` and `D-P3.3-003` manifests are complete and accepted;
- artifact hashes, licenses, dependency lock, SBOM, and vulnerability review pass;
- current P3.2 acceptance remains valid and its package digest is unchanged;
- a machine verifier reports zero failed and zero unresolved manual entry gates;
- the implementation file boundary and authorization expiry are explicit.

The later start statement must bind the exact entry-package SHA-256 digest. A
generic "continue" is not sufficient.

## Decisions Required Now

Only `D-P3.3-001` and `D-P3.3-004` are ready for owner decision from this
planning package. `D-P3.3-002`, `D-P3.3-003`, and `D-P3.3-START` require future
exact manifests and are not ready for acceptance.

The owner may accept the two ready decisions together with:

> I, mayank-admin, accept D-P3.3-001 and D-P3.3-004 exactly as proposed. This is planning and policy acceptance only and does not authorize downloads, implementation, cameras or media, external data, cross-camera tracking, deployment, P3.4, or remote Git actions.
