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

These signals have only fixed `signal` and `state` labels. They contain no
camera, stream, session, user, correlation, provider-locator, or exception-text
labels. Capacity exhaustion is an admission condition, not `mediamtx_unavailable`.

| Fault | Local health | Stable UI/backend code | Metric/event | Recovery |
|---|---|---|---|---|
| Provider 502 | live/ready unchanged; provider degraded | `catalog_upstream_failed` | provider failure counter/event | next bounded refresh |
| Empty catalogue | live/ready unchanged; catalogue degraded | `catalog_empty` | catalogue failure counter/event | valid refresh retains prior registry |
| Schema drift | live/ready unchanged; catalogue failed | `catalog_schema_rejected` | catalogue failure counter/event | corrected bounded document |
| MediaMTX unavailable | live/ready unchanged; relay degraded | `mediamtx_unavailable` | relay failure counter/event | relay retry |
| Preview timeout | live/ready unchanged; preview failed | `preview_timeout` | preview failure counter/event | explicit retry |
| Cleanup failure | live/ready unchanged; cleanup failed | `cleanup_failed` | cleanup failure counter/event | bounded cleanup retry |

Frontend status consumes only these stable codes; it must keep configuration, provider/relay availability, WHEP signaling, and decoded browser media as separate states. Correlation IDs are random 32-hex values, retained only in the bounded sanitized ring, and are never derived from camera, user, session, or locator values.
