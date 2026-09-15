# Sentinel catalogue v1 compatibility contract

## Identity and compatibility

Canonical name: `sentinel_sandbox_catalog_v1`. Current schema version: **1**.
Only version 1 is supported. A document must carry `contract` equal to that
name and integer `schema_version` 1. The existing generated-lab `schema` field
is accepted as the version during the migration window. Other names, absent or
non-integral versions, and unsupported versions fail closed with
`schema_drift` or `schema_version_unsupported`.

Forward compatible changes are additive fields that do not alter a defined
field's type or meaning. They are ignored, counted as bounded warnings, and
never copied to persistence, DTOs, logs, metrics, or evidence. Removal,
renaming, changed meaning/type, a second transport representation, or changed
identity/geometry semantics are breaking. There is no runtime downgrade or
content negotiation: a new version needs a reviewed parser and fixture update.

## Versioned field matrix

| Field | Requirement and normalization | Browser / GIS / diagnostics |
| --- | --- | --- |
| `contract`, `schema_version` | required root, exact v1 | no / no / safe code only |
| `cameras` | required array, 0..configured capacity | count / count / count |
| `id` | required 1..160 bounded text; source-scoped unique | ID / ID / never metric label |
| `name`, `location` | optional bounded display text | name / location is not geometry / no |
| `source_provider`, `department`, `camera_type` | optional bounded text | no / department and type / no |
| `number`, `lab_profile`, `capacity_holder` | optional metadata; invalid optional numbers are unknown | profile / no / no |
| `live` | required boolean advertised state | advertised / advertised / bounded state |
| observed health, registry state | derived only by H-CAM worker/store | derived / derived / bounded state |
| preview compatible, approved live | derived from approved endpoint/policy | derived / derived / bounded state |
| codec, dimensions, FPS, bitrate, BPP | optional advertised metadata; normalized or unknown | codec/profile / no / no |
| `longitude`, `latitude` | both absent or finite; longitude -180..180, latitude -90..90 | no / display-safe geometry / no |
| `updated_at` | optional ISO-8601 UTC; no naive, malformed, or far-future time | no / no / safe code |
| legacy URL fields | RTSP inference, WHEP preview, HLS fallback | never / never / locator hash only |
| `transports` | typed replacement with unique rtsp/whep/hls kinds | never / never / no raw value |
| unknown fields | tolerated only as safe additive fields | never / never / warning count |

Ordering never selects a record: semantic records are sorted by ID. Identity is
not inferred from array position, display name, or `number`. A provider-side
identity mutation is an addition/removal and must pass the same safety checks.

## Transport, geometry, and timestamp policy

Only RTSP/TCP (`inference`), WHEP/WebRTC (`preview`), and HLS (`fallback`) are
valid roles, at most once each. Legacy URL fields and `transports` cannot be
combined. Validation rejects malformed objects/URLs, redirects, credentials,
query strings, fragments, unsupported schemes, disallowed hosts/ports/paths,
relative non-HLS values, and ambiguous payloads. The exact network policy is
the authority; raw locators never leave the internal endpoint model.

Geometry accepts only a complete longitude/latitude pair. Non-numeric,
NaN/infinite, incomplete, out-of-range, and detectable swapped coordinates
fail closed. Geometry changes are semantic changes. Timestamps are metadata:
malformed/future values fail closed; an anomalous or old snapshot never silently
replaces the newer accepted snapshot.

## State separation and last-known-good policy

`advertised_live` is provider metadata. `observed_health` is a bounded worker
observation. `registry_state` is the store lifecycle. `preview_compatible`
means an approved preview endpoint exists; it is not WHEP signaling or decoded
browser media. The values are never collapsed.

A valid non-empty catalogue is staged and atomically applied. Invalid,
unsupported, over-capacity, ambiguous, or unsafe catalogues are rejected before
persistence and retain the prior accepted state. Valid empty catalogues are
observable but do not delete last-known-good. Missing records become durable
missing/tombstoned identities after the existing grace policy and recover only
after safe reappearance. Candidate semantic/transport changes preserve the
prior healthy endpoint until health-gated promotion; failure rolls back.

## Stable codes and DTO allowlist review

The v1 codes are `schema_version_unsupported`, `schema_drift`,
`required_field_missing`, `invalid_field_type`, `invalid_identifier`,
`duplicate_identifier`, `unsafe_locator`, `invalid_transport`,
`transport_missing`, `invalid_geometry`, `invalid_timestamp`,
`stale_catalogue`, `out_of_order_record`, `over_capacity`, and
`ambiguous_payload`. Diagnostics contain only codes/counts; never ID, locator,
payload, credential, token, Authorization header, SDP, or exception text.

`CatalogCamera.browser_safe()` is the explicit browser allowlist. The GIS
allowlist, `CatalogCamera.gis_safe()`, additionally permits display-safe
department/type/geometry. The internal endpoint model is not a DTO. Logs,
metrics, evidence, and support bundles use bounded codes/counts/component state
or locator hashes; camera IDs, correlation IDs, and locators are not labels.

## Fixtures, snapshots, and offline evidence

The deterministic redacted corpus is
`tests/fixtures/sentinel_contract_v1/catalogues.json`; it covers valid,
additive, multi-transport, missing/malformed transport, identity, URL,
geometry, timestamp, partial, tombstone, capacity, version, and schema drift.
It uses `.invalid` placeholders only.

Run `python tools/sentinel_contract_v1.py check` to verify the canonical valid
fixture snapshot. Normal tests never regenerate snapshots. A reviewed change
requires `python tools/sentinel_contract_v1.py update --acknowledge`, whose
diff is the required explicit acknowledgement. Offline verification uses the
fixture bytes, injected `httpx.MockTransport`, and no DNS/provider/camera/auth:

```text
python -m uv run --locked --extra dev --extra analytics pytest tests/test_issue10_sentinel_contract_v1.py -q
python -m uv run --locked --extra dev --extra analytics python tools/sentinel_contract_v1.py check
```

The test suite proves schema-drift rejection, sanitized DTOs, last-known-good
retention, tombstones, and recovery through the real adapter/store path.
