# Sentinel catalogue v1 compatibility and rejection report

This report maps the offline corpus to executable Issue #10 evidence. It is
safe to publish: fixture identifiers are synthetic and no locator is copied to
diagnostics, DTOs, metrics, or support evidence.

| Fixture category | Runtime boundary | Expected stable result | Executable evidence |
| --- | --- | --- | --- |
| valid, multi-transport | `normalize_catalog_document` | accepted, deterministic fingerprint | `test_versioned_valid_fixture_has_strict_safe_projections` |
| additive field | same parser | accepted; bounded warning only | `test_additive_fields_are_ignored_without_becoming_a_dto_or_diagnostic` |
| missing/malformed/duplicate transport | parser and exact policy | `transport_missing`, `invalid_transport`, or `ambiguous_payload` | parametrized rejection test |
| credentials, query, fragment, host, port, path | exact policy | `unsafe_locator` | parametrized rejection test |
| empty/oversized/malformed ID | parser | `invalid_identifier`, `duplicate_identifier`, `over_capacity` | parametrized rejection test |
| malformed/ranged coordinates | parser | `invalid_geometry` | parametrized rejection test |
| malformed/future timestamp | parser | `invalid_timestamp` | parametrized rejection test |
| unsupported version/schema name | version gate | `schema_version_unsupported` or `schema_drift` | parametrized rejection test |
| invalid snapshot after valid state | adapter -> store | reject and preserve LKG | `test_real_adapter_preserves_last_known_good_on_schema_rejection_and_recovers` |
| empty/tombstone response | store reconciliation | retain durable membership | `test_missing_and_tombstone_catalogues_never_delete_last_known_good_identity` |
| valid recovery | adapter -> store | same accepted snapshot/membership restored | LKG recovery test |
| snapshot drift | checked fixture digest | test fails until reviewed acknowledgement | `test_snapshot_requires_explicit_reviewed_update_path` |
| offline boundary | fixture bytes and injected mock transport | no public fetch | `test_contract_fixtures_are_offline_and_redacted` |

The source's pre-existing change-anomaly guard remains the policy for partial
or large rollback payloads. It is intentionally stricter than field parsing:
a syntactically valid but anomalous snapshot is not automatically applied.
