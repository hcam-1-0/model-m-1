# Phase 2.5 observability

`/health/live` measures process liveness only; `/health/ready` measures database/auth readiness. Catalogue, provider, relay, gateway, and browser-media are independent dependency states. Provider loss must not change liveness.

| Metric | Type | Labels | Unit | Retention |
|---|---|---|---|---|
| `hcam_phase2_5_component_state` | gauge | component, state | boolean | scrape policy |
| `hcam_phase2_5_failures_total` | counter | component, error_code | events | scrape policy |
| `hcam_phase2_5_operation_duration_seconds` | histogram | component, outcome | seconds | scrape policy |

Lab targets: dashboard 99%/30d, catalogue success 95%/24h, p95 refresh <20s, recovery <10m, preview setup <15s, cleanup <60s, and zero retained media. Pilot and production targets require SRE owner approval. Owner and escalation owner: H-CAM platform operations; routing is the operations runbook until an alert integration is approved.

Alerts: stale catalogue, repeated schema rejection, relay leakage, cleanup failures, capacity exhaustion, and retained-media detection use the bounded failure/state metrics and route to H-CAM platform operations. Support bundles contain version, checksum, safe health summary, and a 50-event sanitized ring; the privacy scanner rejects locators, credentials, tokens, SDP, camera identifiers, and raw payloads.

| Fault | Local health | Stable UI/backend code | Metric/event | Recovery |
|---|---|---|---|---|
| Provider 502 | live/ready unchanged; provider degraded | `catalog_upstream_failed` | provider failure counter/event | next bounded refresh |
| Empty catalogue | live/ready unchanged; catalogue degraded | `catalog_empty` | catalogue failure counter/event | valid refresh retains prior registry |
| Schema drift | live/ready unchanged; catalogue failed | `catalog_schema_rejected` | catalogue failure counter/event | corrected bounded document |
| MediaMTX unavailable | live/ready unchanged; relay degraded | `mediamtx_unavailable` | relay failure counter/event | relay retry |
| Preview timeout | live/ready unchanged; preview failed | `preview_timeout` | preview failure counter/event | explicit retry |
| Cleanup failure | live/ready unchanged; cleanup failed | `cleanup_failed` | cleanup failure counter/event | bounded cleanup retry |

Frontend status consumes only these stable codes; it must keep configuration, provider/relay availability, WHEP signaling, and decoded browser media as separate states. Correlation IDs are random 32-hex values, retained only in the bounded sanitized ring, and are never derived from camera, user, session, or locator values.
