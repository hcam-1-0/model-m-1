# Phase 2.5 observability

`/health/live` measures process liveness only; `/health/ready` measures database/auth readiness. Catalogue, provider, relay, gateway, and browser-media are independent dependency states. Provider loss must not change liveness.

| Metric | Type | Labels | Unit | Retention |
|---|---|---|---|---|
| `hcam_phase2_5_component_state` | gauge | component, state | boolean | scrape policy |
| `hcam_phase2_5_failures_total` | counter | component, error_code | events | scrape policy |
| `hcam_phase2_5_operation_duration_seconds` | histogram | component, outcome | seconds | scrape policy |
| `hcam_phase2_5_operational_signal` | gauge | signal, state | boolean | scrape policy |

Lab targets: dashboard 99%/30d, catalogue success 95%/24h, p95 refresh <20s, recovery <10m, preview setup <15s, cleanup <60s, and zero retained media. Pilot and production targets require SRE owner approval. Owner and escalation owner: H-CAM platform operations; routing is the operations runbook until an alert integration is approved.

Alerts: stale catalogue, repeated schema rejection, relay leakage, cleanup failures, capacity exhaustion, and retained-media detection use the bounded failure/state metrics and route to H-CAM platform operations. Support bundles contain version, checksum, safe health summary, and a 50-event sanitized ring; the privacy scanner rejects locators, credentials, tokens, SDP, camera identifiers, and raw payloads.

`GET /api/status` returns a fixed operational contract: liveness, readiness,
provider, catalogue, relay, gateway, preview, cleanup, and browser-media checks;
fixed component/error-code pairs; and the fixed operational signals below. It
never includes a provider or media locator, a credential, a token, SDP, a raw
payload, an exception string, or a camera/session identifier. WHEP signalling
and decoded browser media remain separate: browser media stays `not_started`
until a browser supplies independent decode evidence.

## Bounded alert signals

The dashboard exports signals only; it does not claim an external alert-delivery
integration. H-CAM platform operations owns the operations-runbook route and
records acknowledgement/escalation there until an approved notifier exists.

| Alert | Signal / threshold | Evaluation | Severity / owner / routing | Recovery |
|---|---|---|---|---|
| Stale catalogue | `catalogue_freshness=stale` after `max(60s, 2x refresh interval)` | current catalogue age | warning / H-CAM platform operations / operations runbook | valid refresh makes it `fresh` |
| Repeated schema rejection | `schema_rejection_threshold=active` at 3 consecutive rejected refreshes | consecutive current refresh results | warning / H-CAM platform operations / operations runbook | valid catalogue refresh resets it |
| Relay leakage | `relay_leakage=active` after cleanup reports an external cleanup failure | current cleanup result | critical / H-CAM platform operations / operations runbook | later successful cleanup clears it |
| Cleanup failures | `cleanup_failure=active` with `cleanup_failed` | current cleanup result | warning / H-CAM platform operations / operations runbook | later successful cleanup clears it |
| Capacity exhaustion | `capacity_exhaustion=active` when the bounded preview/relay limit rejects a request | current admission result | warning / H-CAM platform operations / operations runbook | next successful admission clears it |
| Retained-media detection | `retained_media=active` when the metadata-only retention inspector reports a non-zero artifact count | each status/support-bundle check; no media is read | critical / H-CAM platform operations / operations runbook | a later zero count makes it inactive |

These signals have only fixed `signal` and `state` labels. They contain no
camera, stream, session, user, correlation, provider-locator, or exception-text
labels. Capacity exhaustion is an admission condition, not `mediamtx_unavailable`.

## Zero-retention check and support bundle

The Phase 2.5 lab has no recording sink and keeps no media payload, SDP, media
locator, or filesystem artifact in the diagnostic path. `/api/status` and the
support bundle run the same metadata-only retention inspector. Its result is
`pass` for zero reported artifacts, `fail` for a non-zero count, and
`not_checked` when the safe aggregate is unavailable; it never reads media or
exposes an artifact path. The zero-retention target is zero detected artifacts
in every status/support-bundle evaluation over the current operational window;
any `fail` consumes the lab's zero-retention error budget and is owned by
H-CAM platform operations through the operations runbook.

Support bundles are deterministic canonical JSON with a checksum over only
allowlisted diagnostics: format/version, safe settings, logical listener
states, bounded health/status signals, zero-retention state, and at most 50
sanitized error records. The privacy scanner rejects actual locators,
credentials, bearer values, identifiers, SDP-like content, and provider payload
values, while allowing safe fixed terms such as WHEP, HLS, MediaMTX, provider,
camera, and tokenization.

## Executable fault evidence

Each row below names a test that crosses the real application/service boundary;
the observability helper is not the sole source of evidence. Events contain only
a random operation correlation, bounded component, stable code, and outcome.

| Fault | Injected boundary and path | Status/health/metric/recovery evidence | Test |
|---|---|---|---|
| Provider 502 | mocked HTTP response through `SentinelCatalogAdapter.refresh` and `/api/refresh` | provider degraded with `catalog_upstream_failed`; live/ready unchanged; valid adapter response recovers | `test_real_catalogue_http_faults_have_distinct_status_metrics_and_recovery` |
| Valid empty catalogue | mocked valid empty HTTP document through the same adapter | provider remains healthy; catalogue reports `catalog_empty`; last known-good snapshot remains | `test_real_catalogue_http_faults_have_distinct_status_metrics_and_recovery` |
| Schema rejection | malformed HTTP document through parser and `/api/refresh` | catalogue reports `catalog_schema_rejected`; bounded counter/event; valid refresh resets state | `test_real_catalogue_http_faults_have_distinct_status_metrics_and_recovery`, `test_schema_rejection_threshold_and_recovery_use_refresh_runtime` |
| MediaMTX unavailable | connection refusal at the WHEP upstream transport | relay reports `mediamtx_unavailable`; no client/validation error is reclassified | `test_whep_transport_failure_is_relay_unavailable_but_rejection_is_not` |
| Preview timeout | timeout at WHEP offer transport | preview reports `preview_timeout`, increments bounded failure metric, then a successful offer recovers preview only | `test_whep_preview_timeout_is_observed_through_runtime_route` |
| Cleanup failure | connection refusal at external WHEP resource deletion | cleanup reports `cleanup_failed` and leak signal; later successful cleanup clears current state | `test_whep_cleanup_failure_is_observed_through_runtime_route` |

`hcam_phase2_5_operation_duration_seconds` receives refresh observations from
the application refresh path. Preview success is signaling-only and does not
change `browser_media`, which remains `not_started` without browser decode
evidence.

| Fault | Local health | Stable UI/backend code | Metric/event | Recovery |
|---|---|---|---|---|
| Provider 502 | live/ready unchanged; provider degraded | `catalog_upstream_failed` | provider failure counter/event | next bounded refresh |
| Empty catalogue | live/ready unchanged; catalogue degraded | `catalog_empty` | catalogue failure counter/event | valid refresh retains prior registry |
| Schema drift | live/ready unchanged; catalogue failed | `catalog_schema_rejected` | catalogue failure counter/event | corrected bounded document |
| MediaMTX unavailable | live/ready unchanged; relay degraded | `mediamtx_unavailable` | relay failure counter/event | relay retry |
| Preview timeout | live/ready unchanged; preview failed | `preview_timeout` | preview failure counter/event | explicit retry |
| Cleanup failure | live/ready unchanged; cleanup failed | `cleanup_failed` | cleanup failure counter/event | bounded cleanup retry |

Frontend status consumes only these stable codes; it must keep configuration, provider/relay availability, WHEP signaling, and decoded browser media as separate states. Correlation IDs are random 32-hex values, retained only in the bounded sanitized ring, and are never derived from camera, user, session, or locator values.
