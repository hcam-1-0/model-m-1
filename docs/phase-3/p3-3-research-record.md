# P3.3 Tracking Research Record

Status: planning research complete; implementation artifacts remain
unselected and unauthorized.

Research date: 2026-08-25.

Scope: primary sources for anonymous, per-camera multi-object tracking and its
evaluation. No repository, package, model, or dataset was downloaded.

## Sources

1. [ByteTrack ECCV 2022 paper](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820001.pdf)
   and [arXiv record](https://arxiv.org/abs/2110.06864).
2. [FoundationVision ByteTrack repository](https://github.com/FoundationVision/ByteTrack)
   and its [MIT license](https://raw.githubusercontent.com/FoundationVision/ByteTrack/main/LICENSE).
3. [HOTA paper](https://arxiv.org/abs/2009.07736).
4. [TrackEval official repository](https://github.com/JonathonLuiten/TrackEval)
   and its [MIT license](https://raw.githubusercontent.com/JonathonLuiten/TrackEval/master/LICENSE).

These links identify projects, not approved artifacts. Exact commits, files,
hashes, dependency trees, and licenses must be frozen before implementation.

## Findings

### Association Method

ByteTrack is a tracking-by-detection method. It first associates high-confidence
detections with predicted track locations, then gives unmatched tracks a second
association opportunity against low-confidence detections. The paper reports
that the second association can recover partially occluded objects that would
otherwise fragment into multiple tracks.

The selected H-CAM use is narrower than the paper's general definition of
identity. H-CAM track identifiers are anonymous, temporary technical handles
inside one stream and one tracker epoch. They are not person identities,
vehicle identities, biometric identifiers, or cross-camera join keys.

### Integration Risk

The upstream tracker is coupled to its YOLOX repository structure and imports
framework and numerical dependencies that H-CAM does not need for a normalized
box association component. Importing the full upstream project would expand the
runtime and supply-chain surface unnecessarily.

The recommended implementation path is therefore a small, attributed
adaptation of the pinned upstream association, base-track, Kalman-filter, and
matching logic behind an H-CAM-owned contract. The adaptation must preserve the
upstream MIT notice, remove detector and image dependencies, and prove behavior
parity against a separately pinned upstream oracle on deterministic generated
sequences. This is a proposal, not permission to download or adapt source.

### Evaluation

HOTA explicitly combines detection and association quality and exposes
decomposed results such as `DetA`, `AssA`, and `LocA`. IDF1 complements it by
measuring identity-consistent detections across a sequence. The official
TrackEval project implements HOTA, IDF1, CLEAR MOT, and related metrics.

P3.3 should use a pinned TrackEval artifact as a development-only evaluation
oracle. Runtime code must not depend on TrackEval. H-CAM may maintain small
hand-computable invariant tests, but it must not label a simplified local score
as official HOTA or IDF1.

### Dataset Boundary

MOT17, MOT20, HiEve, BDD100K, CrowdHuman, and other datasets mentioned by the
paper are research references only. None is authorized for download or use.
P3.3 planning uses deterministic generated structured observations and generated
ground truth only. It makes no real-scene accuracy, fairness, representativeness,
or operational performance claim.

## Planning Consequences

- Keep association state strictly partitioned by department, assignment,
  camera, stream, and epoch.
- Partition association by exact H-CAM Tier A class; never use appearance or
  biometric features.
- Use monotonic sequence and UTC time checks, with a new epoch after any unsafe
  discontinuity, restart, reconfiguration, or source change.
- Bound detections, active tracks, lost tracks, queue depth, and processing time.
- Evaluate generated sequences with exact fixture digests and a pinned TrackEval
  oracle.
- Require separate approval for exact source artifacts, generated suite,
  tracker policy, implementation start, and final evidence acceptance.
