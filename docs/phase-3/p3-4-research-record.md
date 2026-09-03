# P3.4 Research Record

Status: primary-source planning research complete on 2026-08-25. No package,
dataset, model, or runtime dependency was downloaded.

Decision overlay: `D-P3.4-001` selects a hybrid PostGIS authority and Shapely
worker path. `D-P3.4-002` selects a visual typed rule graph with constrained CEL.
These selections add no dependency or implementation authorization.

## Existing H-CAM Baseline

H-CAM already provides normalized line and simple-polygon contracts, IANA time
zone schedule fields, versioned geometry references, an analytic-event envelope,
anonymous epoch-scoped track lifecycle v2, deterministic generated tracking,
transactional outbox, RBAC, audit, and short metadata retention. P3.4 should
extend these contracts rather than create a separate GIS or event platform.

## Primary Sources

| Source | Planning finding |
| --- | --- |
| [Shapely 2.1.2 predicates](https://shapely.readthedocs.io/en/2.1.2/predicates.html) | `covers`, `contains`, `crosses`, `touches`, and DE-9IM-backed predicates provide explicit boundary semantics. |
| [Shapely user manual](https://shapely.readthedocs.io/en/2.1.2/manual.html) | Prepared geometries accelerate repeated predicates; predicates distinguish interior, boundary, and exterior. |
| [Shapely STRtree](https://shapely.readthedocs.io/en/2.1.2/strtree.html) | Immutable two-dimensional bounding-box indexing can preselect active rule candidates, followed by exact predicates. |
| [Shapely precision model](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.set_precision.html) | Precision reduction can remove duplicate vertices or collapse narrow geometry; validation must detect and reject collapse. |
| [Shapely requirements and license](https://shapely.readthedocs.io/en/2.1.2/index.html) | Shapely 2.1 requires Python 3.10+, GEOS 3.9+, and NumPy; Shapely is BSD-3-Clause and GEOS is LGPL-2.1. |
| [Shapely 2.1.2 release](https://shapely.readthedocs.io/en/2.1.2/release/2.x.html#version-2-1-2-2025-09-24) | Version 2.1.2 provides Python 3.14 wheels with GEOS 3.13.1, matching the current developer interpreter. |
| [OGC GeoSPARQL 1.1 Simple Features relations](https://docs.ogc.org/is/22-047r1/22-047r1.html#_simple_features_relation_family) | OGC relations bind `equals`, `disjoint`, `intersects`, `touches`, `crosses`, `within`, `contains`, and `overlaps` to DE-9IM patterns. |
| [Apache Beam model](https://beam.apache.org/documentation/basics/) | Event time and processing time are distinct; watermarks and explicit late-data policy are required when order is uncertain. |
| [Python `zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) | IANA zones and the `fold` attribute provide deterministic handling of daylight-saving transitions. |
| [PostgreSQL 18 `INSERT`](https://www.postgresql.org/docs/18/sql-insert.html) | Unique constraints plus `ON CONFLICT` provide an atomic deduplication primitive for deterministic event IDs. |
| [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html) | Rule-based state machines generate action sequences and check invariants after each transition, fitting entry/exit/dwell/replay testing. |

## Conclusions

1. Use a proven two-dimensional topology engine. Exact Shapely 2.1.2 is the
   selected worker candidate, while PostGIS is the authoritative geometry,
   validation, indexing, history, and administrative-query layer. Both paths
   require exact version, license, hash, SBOM, compatibility, and parity evidence
   before addition.
2. Keep H-CAM coordinates normalized and image-space only. P3.4 must make no
   geospatial distance, speed, map, or real-world location claim.
3. Use a versioned anchor policy and state machine around predicates. A raw
   `intersects` result is insufficient because camera jitter can repeatedly
   touch a boundary.
4. Process track event time and source sequence, not wall-clock arrival order.
   Late, duplicate, replayed, and schedule-boundary behavior must be explicit.
5. Persist deterministic state and events transactionally. Event publication
   remains an outbox concern; event creation is not operational alerting.
6. Use hand-computable goldens plus property/state-machine tests. Shapely cannot
   serve as both implementation and sole correctness oracle.

## Rejected Or Deferred Options

- Extending the current hand-written segment helper into a full topology engine
  is rejected because robustness, boundary semantics, and maintenance burden
  exceed the helper's validation-only purpose.
- PostGIS-only per-transition evaluation is rejected. P3.4 state is stream-local
  and latency-sensitive; PostGIS is authoritative storage and administration,
  while the worker evaluates locally cached immutable geometry.
- GeoPandas is not needed for bounded per-stream rule evaluation.
- Perspective calibration, homography, world coordinates, GIS layers, speed,
  route inference, and cross-camera geometry are deferred to separately
  authorized work.
