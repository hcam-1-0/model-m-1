# Taxonomy, Geometry, And Runtime Contracts

Status: model-independent P3.0 contract structures are implemented. Every
tracked taxonomy and geometry fixture is `draft`; the runtime adapter fixture is
unconfigured and cannot perform inference.

## Taxonomy Manifest

`TaxonomyManifestV1` defines:

- immutable taxonomy version and artifact digest;
- a unique, acyclic class hierarchy;
- an intended-use statement and unknown-class policy;
- mandatory prohibitions on biometric identification, person re-identification,
  cross-camera identity, sensitive-trait inference, and autonomous enforcement;
- rejection of prohibited attribute/purpose terms in class definitions; and
- owner, optional reviewer, approval record, and lifecycle state.

`approved` and `retired` manifests require an owner-controlled approval record.
The optional legacy `independent_reviewer_id` field may be omitted or may equal
the owner. The generated `hcam.objects.synthetic.v1` fixture is draft-only test
metadata. It is not the approved Tier A taxonomy.

## Geometry And Time

All coordinates use `normalized_top_left`: `(0,0)` is the top-left of the source
frame and `(1,1)` is the bottom-right. Source dimensions remain in observation
metadata for deterministic conversion.

Line definitions require two distinct bounded points and an explicit crossing
direction. Zone definitions use an implicitly closed polygon with 3-128 unique
vertices. Validation rejects out-of-frame points, zero-area polygons, duplicate
vertices, and self-intersections.

Schedules are either always active or contain weekly windows in an explicit IANA
timezone/UTC. Windows are minute-based half-open intervals, cannot wrap midnight,
and cannot overlap on the same day. Overnight periods must be represented as two
windows split at midnight.

Approved or retired geometry requires an owner-controlled approval record.
Separate-person review is disabled; the optional reviewer field may be omitted
or identify the owner. The tracked line and zone fixtures are draft and
synthetic.

## Runtime Boundary

`AnalyticsRuntimeAdapter` is a protocol, not an inference implementation. Its
metadata contracts use:

- opaque, short-lived input lease IDs rather than paths, URLs, credentials, or
  frame bytes;
- stream/camera scoped batches of at most 16 inputs;
- deadlines that cannot outlive input leases;
- normalized candidates that reference only inputs from the request;
- low-cardinality safe failure codes; and
- descriptors fixed to denied network access and verified artifact handles.

`GuardedAnalyticsRuntimeAdapter` enforces configured state, supported capability,
adapter batch limits, request/result matching, candidate input scope, and
exception sanitization. `UnavailableAnalyticsRuntimeAdapter` always returns
`runtime_unconfigured` and never opens an input lease.

No model format, model artifact, runtime provider, decoder, lease store, camera,
or media backend is implemented or selected by this boundary.

## Verification

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py check
uv run --locked --extra dev pytest tests/test_analytics_contracts.py tests/test_analytics_taxonomy.py tests/test_analytics_geometry.py tests/test_analytics_runtime.py --cov=hcam.analytics --cov-branch --cov-report=term-missing --cov-fail-under=90
```

Schema and fixture rewrites require the explicit
`--acknowledge-reviewed-change` flag and a reviewed diff.
