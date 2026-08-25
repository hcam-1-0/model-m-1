# P3.4 Owner Technical Decisions

Status: `D-P3.4-001` through `D-P3.4-004` accepted by `mayank-admin` on
2026-08-25. `D-P3.4-START` remains pending.

Machine-readable record:
[`p3-4-owner-decisions.json`](../../contracts/phase-3/p3-4-owner-decisions.json).

## D-P3.4-001: Hybrid Geometry Engine

Selected option: **C. Hybrid Shapely plus PostGIS**.

- exact Shapely 2.1.2 is the real-time worker predicate candidate;
- PostgreSQL/PostGIS is the authoritative approved-geometry, validation,
  indexing, version-history, and administrative-query layer;
- normalized image coordinates remain non-geographic and make no GIS, distance,
  speed, or physical-location claim;
- canonical normalized JSON, WKB, precision policy, and SHA-256 bind the same
  immutable geometry version across database and worker boundaries;
- invalid geometry is rejected rather than silently repaired;
- generated parity evidence must cover boundary, crossing, containment,
  precision, collapse, and version-drift cases across both engines;
- exact PostGIS, GEOS, CEL, and Python artifacts, licenses, hashes, lock entries,
  SBOM records, and compatibility evidence remain implementation evidence, not
  an implicit download authorization.

PostGIS is not the per-track network hot path. Shapely evaluates immutable local
copies; PostGIS remains the durable authority and investigation/query surface.

## D-P3.4-002: Visual Rules, Typed Temporal Nodes, And CEL

Selected option: **C. Visual rule graph plus typed temporal nodes plus
constrained CEL**.

- the visual builder compiles to an immutable, versioned, typed H-CAM AST;
- H-CAM-owned typed nodes implement line, zone, entry, exit, presence, dwell,
  occupancy, sequence, time-window, cooldown, and repeat-limit state;
- constrained CEL evaluates stateless Boolean conditions over an approved typed
  context, such as class, confidence, direction, schedule, count, and prior
  typed-node result;
- CEL cannot directly access coordinates, SQL, files, network, secrets, models,
  camera controls, external lookups, or alert/enforcement actions;
- no loops, recursion, mutation, user extensions, arbitrary functions, or
  dynamically loaded code are permitted;
- the control plane performs parsing, type checking, function allowlisting,
  static cost estimation, canonical AST serialization, and digest generation
  before a rule can be approved;
- workers execute only the approved compiled representation under node, depth,
  candidate, state, time, and memory ceilings;
- all execution remains deterministic, event-time-based, stream-local, and
  default-off.

The DSL composes safe primitives; it does not replace geometry predicates or
temporal state machines with arbitrary scripts.

## D-P3.4-003: Balanced Deterministic Time Policy

Selected option: **A. Balanced deterministic default**.

- maximum 64 buffered lifecycle inputs per stream lane;
- maximum two seconds of event-time lateness;
- ordering by tracker epoch, source sequence, UTC event time, and lifecycle ID;
- committed watermark prevents late input from rewriting closed state;
- deterministic IANA time-zone and daylight-saving behavior;
- deterministic event IDs, database uniqueness, and transactional outbox;
- exact duplicates are ignored and conflicting duplicates fail closed.

## D-P3.4-004: Bounded PostgreSQL/PostGIS Persistence

Selected option: **A. Bounded PostgreSQL/PostGIS state plus transactional
outbox**.

- 64 active rule versions per assignment;
- 16 candidate rules per track transition;
- 16,384 live track-rule states per stream;
- existing P3.3 lane, queue, observation, and track ceilings remain inherited;
- standard derived metadata retention remains at most 168 hours and restricted
  metadata at most 24 hours;
- immutable geometry/rule versions, evaluator runs, bounded current state, typed
  events, and outbox records are persisted transactionally;
- no media, full trajectory, identity, embedding, plate text, owner data,
  watchlist result, or cross-camera key is stored;
- C10 goldens, property/state-machine tests, PostgreSQL concurrency, replay,
  retention, overload, and clean-source evidence remain mandatory.

## Remaining Gate

These four selections freeze the technical baseline but do not authorize any
implementation. `D-P3.4-START` must separately authorize dependency acquisition,
contracts, migration, evaluator, API, generated execution, tests, evidence, and
local checkpoint work under the continuing exclusions.
