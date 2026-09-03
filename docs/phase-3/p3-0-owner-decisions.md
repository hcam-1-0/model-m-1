# P3.0 Owner Decisions And Acceptance Record

Status: P3-G1 through P3-G4 accepted on 2026-08-24. P3.0 is accepted.

Machine-readable record:
[`p3-0-owner-decisions.json`](../../contracts/phase-3/p3-0-owner-decisions.json).

## P3-G1

Accountable owner `mayank-admin` approved the complete class list proposed in
the immediately preceding P3-G1 recommendation:

- `object.person`;
- `vehicle.bicycle`;
- `vehicle.motorcycle`;
- `vehicle.car`;
- `vehicle.bus`;
- `vehicle.truck`; and
- `object.unknown`.

`object.entity` and `object.vehicle` are supporting hierarchy classes and are
not emitted leaf observations. Unknown model labels are explicitly emitted as
`object.unknown`; they are not silently mapped to another class.

Approved intended use: anonymous situational metadata from synthetic or
explicitly authorized video for operator-reviewed testing of object detection,
stream-local tracking, line crossing, zone entry/exit, occupancy, and dwell
duration.

Approved geometry semantics use normalized top-left coordinates, directional
two-point lines, valid simple polygons, and always-active or explicit IANA-
timezone weekly schedules. This approves the geometry contract, not any
site-specific coordinates. Every operational line, zone, schedule, and purpose
still requires a versioned configuration and accountable-owner approval.

"All classes" means every emitted class listed above. It does not include
synthetic ANPR, Tier B/C analytics, identity, watchlists, sensitive traits,
Government matching, or autonomous enforcement. Those exclusions remain
separately gated.

The existing generated taxonomy fixture remains `draft`. Owner approval of the
scope does not approve a model/dataset label mapping.

## P3-G2

Accountable owner `mayank-admin` approved the improved synthetic-lab metadata
policy below.

| Classification | Data | Maximum retention | Access |
| --- | --- | ---: | --- |
| `derived.analytics.standard` | Anonymous aggregates and non-sensitive event metadata | 7 days | Department-scoped viewer/editor/admin |
| `derived.analytics.restricted` | Event-level observations and stream-local tracks | 24 hours | `platform.admin`, reason and audit required |
| `control.analytics.configuration` | Assignments, taxonomy, geometry, policy, revisions | 90 days | Editor/admin, reason and audit required |
| `audit.analytics` | Security, access, mutation, denial, deletion metadata | 90 days | `platform.admin`, reason required |
| `telemetry.analytics.aggregate` | Identifier-free operational metrics | 30 days | Protected metrics reader |
| `derived.analytics.plate_text` | Plate text or alternatives | Disabled, zero retention | No access |
| `media.analytics.raw` | Frames, crops, images, clips, video | Forbidden, zero retention | No access |

Additional controls:

- policy scope is synthetic lab only;
- raw-media persistence and data export are denied;
- training reuse requires a new purpose approval;
- deletion runs at least every 24 hours with no more than 24 hours of lag;
- deletion proof stores audited metadata, never deleted content;
- encrypted backup retention is at most 7 days;
- restores delete expired records before access is restored; and
- legal hold is unavailable until separately designed and approved.

This is the approved policy baseline. Data-plane persistence cannot start until
the retention/deletion/access controls have executable tests. Existing P3.0
blocked assignment metadata does not activate analytics processing.

## P3-G3

Accountable owner: `mayank-admin`.

Optional reviewer: `mahin-eleveted`, role `member`.

The reviewer identifier is recorded exactly as supplied by the owner. Naming the
reviewer completes the historical P3-G3 record, but reviewer participation is
optional and non-blocking.

## P3-G4

The accountable owner stated that the named reviewer was unavailable and, as
main developer and team lead, explicitly reviewed and accepted P3.0. The
acceptance is recorded under `mayank-admin` in the capacities `main_developer`,
`team_lead`, and `accountable_owner`.

The owner then removed the P3-G4 policy that prevented the team lead from
reviewing their own work. For this bounded milestone,
`accountable_owner_self_review_permitted` makes the acceptance effective. The
named reviewer remains available for an optional later review but does not block
P3.0.

## Later-Gate Review Policy

P3-G4 is complete and P3.0 is accepted. The owner has disabled mandatory
separate-person review for model promotion, dataset approval, operational site
geometry, and deployment. Accountable-owner review is sufficient. All evidence,
license, provenance, security, validation, rollback, audit, and explicit
authorization requirements remain mandatory.

P3-G4 does not authorize P3.1/P3.2 model, dataset, runtime, inference, media,
camera, Government-data, alert, pilot, or deployment work.
