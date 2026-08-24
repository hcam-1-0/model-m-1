# Analytics Capability Catalog

Each capability is independently assignable, versioned, observable, and
reversible. A capability cannot inherit approval from a less risky capability.

## Tier A: Foundation

| Capability | Output | Minimum entry evidence | Main limitations |
| --- | --- | --- | --- |
| Person detection | Anonymous bounding-box observation | Approved labels, frozen test set, class metrics, slice analysis | Occlusion, scale, crowding, lighting |
| Vehicle detection | Vehicle-class bounding-box observation | Approved class taxonomy and per-class metrics | Camera angle, partial vehicles, class ambiguity |
| Selected object detection | Approved neutral class observation | Documented purpose and license-reviewed data | Must not become unrestricted object search |
| Per-camera tracking | Ephemeral local tracks | Sequence annotations and HOTA/IDF1 evidence | Restarts, occlusion, no cross-camera identity |
| Line crossing | Directional event from local tracks | Versioned geometry and scenario tests | Perspective and tracker errors |
| Zone entry/exit | Entry, exit, and occupancy transitions | Geometry validation and boundary tests | Edge jitter and partial objects |
| Dwell time | Duration derived from a local track in a zone | Clock and discontinuity tests | Not intent or loitering by itself |
| Synthetic ANPR | Plate region and OCR alternatives | Synthetic/authorized plates, exact/character metrics | Not ownership or enforcement evidence |

Tier A is the Phase 3 acceptance scope. "Selected object" starts empty; every
class needs a documented purpose and data approval.

## Tier B: Scenario Analytics

| Capability | Prerequisites | Required additional review |
| --- | --- | --- |
| Crowd density | Calibrated region and density/count evidence | Crowd definition, threshold, privacy, venue slices |
| Loitering hypothesis | Stable local tracks, dwell and zone semantics | Scenario-specific duration, false-positive and response review |
| Restricted-zone intrusion | Zone, schedule, direction, authorization | Site policy and operator escalation design |
| Wrong-way movement | Calibrated direction and vehicle tracks | Road layout, exceptions, minimum track quality |

Tier B output remains a hypothesis requiring review. It must not infer motive.

## Tier C: High-Consequence Analytics

| Capability | Why separately gated | Required evidence before implementation |
| --- | --- | --- |
| Abandoned-object hypothesis | Requires object-owner temporal reasoning | Scenario definition, sequence data, false-alert workload study |
| Accident hypothesis | Rare, diverse, safety-critical event | Authorized incident data, expert labels, recall and false-alert analysis |
| Fire/smoke hypothesis | Environment-sensitive and safety-critical | Dedicated datasets, environmental slices, response integration review |
| Weapon-like-object hypothesis | Severe consequence of false positives | Legal/policy approval, dedicated data, expert validation, mandatory human review |

Tier C is not authorized by approval of the Phase 3 baseline. Each item needs a
separate decision record and acceptance plan.

## Common Output Requirements

Every model-generated observation includes:

- camera and stream identifiers;
- source, processing, and receipt times;
- pipeline, model, postprocessor, and runtime versions;
- class taxonomy version and machine-readable class ID;
- confidence and calibrated-confidence method when available;
- normalized geometry with source-frame dimensions;
- processing node, frame sequence, and quality indicators;
- privacy classification and retention class;
- review state and a statement that the output is probabilistic.

Runtime-specific labels are mapped to the H-CAM taxonomy before publication.
Unknown classes are rejected or explicitly emitted as `unknown`; they are not
silently remapped.

## Capability Lifecycle

```text
proposed -> data_review -> offline_evaluation -> lab_shadow
         -> owner_approved -> active -> suspended -> retired
```

- Promotion is per model version, pipeline version, capability, dataset suite,
  hardware profile, and policy version.
- Any material change returns the combination to offline evaluation.
- A capability can be suspended immediately without deleting evidence.
- Rollback points to a previously approved immutable version; it does not edit
  the failed version in place.

## Prohibited Attribute Inference

Phase 3 must not infer or store face identity, ethnicity, religion, caste,
health, disability, emotion, sexual orientation, political affiliation,
criminality, or other sensitive personal traits. Generic clothing/color
attributes are also deferred because they can enable person search and
cross-camera profiling; they require a later privacy decision.
