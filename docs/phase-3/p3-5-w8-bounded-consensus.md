# P3.5 W8 Bounded Synthetic Track-Local Consensus

Status: `validated_generated_contract_fixture`.

Work package: `P35-W8_bounded_synthetic_track_local_consensus`.

Authorization: final digest-bound `D-P3.5-START`, specifically its generated-only
normalization/consensus semantics and zero-retention evidence boundaries. The
implementation remains local, default-off, production-forbidden, network-denied,
and disconnected from APIs, workers, databases, cameras, and deployment.

## Purpose

W8 proves the deterministic state and lifecycle contracts for optional temporal
consensus over typed W7 normalization results. It is not an operational plate
decision system. The owner has not approved numeric minimum-support or margin
thresholds, so the implementation computes vote evidence but every closed result
is a mandatory abstention.

## Grouping Boundary

One state is keyed by exactly:

```text
(stream_id, tracker_epoch, track_id)
```

These identifiers reuse the accepted P3.3 anonymous stream-local contracts.
Plate text is never a state key. Matching text cannot join streams, tracker
epochs, or tracks, and no camera, assignment, department, person, vehicle,
registration, owner, watchlist, or cross-camera identifier is accepted.

Only a typed, valid, generated Latin W7 normalization can enter the state
machine. Devanagari and Gujarati auxiliary observations, unrecognized format
hypotheses, arbitrary text, file/URL/upload input, media, and real registration
marks are rejected before state allocation.

## Resource And Lifecycle Bounds

- maximum five observations per state;
- maximum two seconds of event time per state;
- maximum 256 active states per stream;
- deterministic close on count limit, event-time limit, track end, or epoch reset;
- a 257th concurrent state closes as an overload abstention without evicting or
  merging any active state;
- duplicate sequence numbers and decreasing sequence/event time fail closed;
- no fallback, unbounded queue, cross-stream state, or background cleanup path.

The state machine is process-local and in memory. Track end and epoch reset are
explicit controls; event-time expiry is deterministic and independent of wall
clock time. Restart persistence and recovery are intentionally absent.

## Voting And Abstention

Observations are grouped by the exact W7 `normalized_display_candidate` only
after the anonymous track key has selected the state. Candidate scores are the
sum of identity-calibrated confidence values. Ranking is deterministic by:

1. descending confidence weight;
2. descending observation support;
3. ascending exact candidate value as a stable tie break.

The in-memory result records ranked votes, winning support, winning confidence
weight, and margin. These values and the candidate strings are ephemeral and
are rejected by the canonical evidence boundary.

`minimum_support` and `minimum_margin` are both unset. `thresholds_approved` is
false, `accepted_value_emitted` is false, and every non-overload close uses
`consensus_thresholds_unapproved`. Overload uses `overload_fail_closed`. No W8
result can create an alert, lookup, identity, event, enforcement action, or
persistent plate observation.

## Aggregate Evidence

Canonical evidence:
`contracts/phase-3/p3-5-consensus-evaluation.json`.

SHA-256:
`58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124`.

The evidence covers nine deterministic generated contract scenarios:

| Scenario | Operations | Closed | Abstained | Violations |
| --- | ---: | ---: | ---: | ---: |
| Agreement | 5 | 1 | 1 | 0 |
| Disagreement | 5 | 1 | 1 | 0 |
| Cross-boundary isolation | 4 | 4 | 4 | 0 |
| Duplicate rejection | 2 | 1 | 1 | 1 |
| Out-of-order rejection | 2 | 1 | 1 | 1 |
| Event-time window | 2 | 1 | 1 | 0 |
| Epoch reset | 2 | 2 | 2 | 0 |
| Track end | 2 | 1 | 1 | 0 |
| Overload and cleanup | 257 | 257 | 257 | 0 |

Totals are 281 bounded operations and 269 closed results, all 269 abstained.
Replay is deterministic for 20/20 runs. Maximum observed active state count is
256. Cross-stream/epoch/track merge count, accepted value count, operational
event count, model execution, downloads, media input, external text input, real
registration input, and network access are all zero.

Tracked evidence contains no plate or normalized text, ranked votes, stream ID,
tracker epoch, track ID, sample/region/result ID, or text-derived commitment.
No W8 path uses `B:`; that RaiDrive-backed location remains outside the workflow.
Plate-text retention remains zero hours.

## Validation

- focused W8, contract, and readiness tests: `61 passed`;
- canonical contract and W8 evidence drift checks: passed;
- complete repository suite: `946 passed`, eight expected PostgreSQL skips, and
  one existing Starlette/httpx deprecation warning;
- legacy unittest discovery: `40 passed`;
- total branch coverage: `90.77%`, above the required `90%` floor;
- consensus module statement and branch coverage: `100%`;
- repository-wide Ruff, compileall, release/analytics/P3.5 contract drift, and
  strict P3.5 readiness: passed;
- `uv pip check`: all `76` installed packages compatible;
- sdist and wheel source build with no isolation: passed;
- built wheel: `108` entries, consensus module present, direct wheel import
  passed, and zero enumerated model-weight, trained-data, image, or video files;
- wheel SHA-256:
  `AAE7843B3CB66D833D4A41F18D74C3C3F671DBF4FB3E622A7DCF5215E53EA1DD`;
- sdist SHA-256:
  `29F30A47A3EDA276909A818025BA5CF24C9DFE41CB2175BD28A4933C2C5594EE`.

## Continuing Blocks

W8 does not approve minimum-support or margin thresholds, model quality,
promotion, real-world accuracy, persistence, API/worker integration, alerts,
lookups, camera/media access, real/public/private/Government/police data,
training, Tesseract, `PLATE-D0`, P3.6, deployment, or remote Git operations.

`P35-W9` is not started. Its broader aggregate evidence, security, resource,
packaging, and rollback scope remains a separate package and cannot be inferred
from W8 completion.
